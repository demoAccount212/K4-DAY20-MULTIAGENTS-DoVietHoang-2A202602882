"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import re
import json
from pathlib import Path

from .model import make_model
from .tasks import ROOT, eval_markers, list_tasks   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    if out_dir is None:
        out_dir = ROOT / "skills" / "auto"
    else:
        out_dir = Path(out_dir)

    results_path = Path(results_dir) / source_condition
    if not results_path.exists():
        return []

    runs = []
    for run_json_path in results_path.glob("*/run.json"):
        try:
            r = json.loads(run_json_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        if r.get("role") != "learn":
            continue

        # Read trace.md
        trace_path = run_json_path.parent / "trace.md"
        trace = ""
        if trace_path.exists():
            trace = trace_path.read_text(encoding="utf-8")
            # Take last ~6000 characters
            if len(trace) > 6000:
                trace = trace[-6000:]

        failed_checks = []
        for check in r.get("checks", []):
            if not check.get("passed", True):
                failed_checks.append({"name": check.get("name", ""), "detail": check.get("detail", "")})

        if failed_checks:
            runs.append({
                "task": r.get("task", ""),
                "failed": failed_checks,
                "trace": trace
            })

    if not runs:
        print("không có check thất bại ở tác vụ học")
        return []

    if model is None:
        model = make_model()

    # Build prompt
    prompt = "Bạn viết SKILL cho một tác tử lập trình và phân tích dữ liệu.\n"
    prompt += "Dưới đây là các check thất bại (tên và nhận xét của bot đánh giá) và vết của các lần chạy.\n"
    prompt += f"Hãy tìm các lỗi QUY TRÌNH chung (không phải đáp án cụ thể) và viết tối đa {max_skills} skill ngắn\n"
    prompt += "giúp tránh các lỗi đó trên tác vụ MỚI cùng loại.\n\n"
    prompt += "Quy tắc:\n"
    prompt += "- Skill phải tổng quát: không nêu id tác vụ, không nêu tên tệp riêng của một tác vụ, không nêu đáp án hay con số.\n"
    prompt += "- Mỗi skill có frontmatter YAML gồm `name` (chữ thường, gạch ngang) và `description` (một câu: DÙNG KHI NÀO),\n"
    prompt += "  sau đó tối đa 40 dòng chỉ dẫn mệnh lệnh (danh sách kiểm tra - checklist - hoạt động tốt).\n"
    prompt += "- Định dạng đầu ra, đúng từng ký tự:\n"
    prompt += "=== SKILL: <name> ===\n"
    prompt += "---\n"
    prompt += "name: <name>\n"
    prompt += "description: <khi nào dùng>\n"
    prompt += "---\n"
    prompt += "<nội dung>\n"
    prompt += "=== END ===\n\n"

    for run in runs:
        prompt += f"## Task: {run['task']}\n"
        for fc in run["failed"]:
            prompt += f"- Check failed: {fc['name']}\n"
            prompt += f"  Detail: {fc['detail']}\n"
        if run["trace"]:
            prompt += f"Trace (last 6000 chars):\n{run['trace']}\n"
        prompt += "\n"

    # Invoke model
    from langchain_core.messages import HumanMessage
    response = model.invoke([HumanMessage(content=prompt)])
    content = response.content if hasattr(response, 'content') else str(response)
    # Handle both string and list of content objects (e.g., from google_genai)
    if isinstance(content, list):
        reply = "".join(c.get("text", "") for c in content if isinstance(c, dict))
    else:
        reply = str(content)

    # Parse and validate skills
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in parse_skill_blocks(reply):
        if len(written) >= max_skills:
            break
        problems = validate_skill(text, expected_name=name)
        if problems:
            continue
        skill_dir = out_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(text, encoding="utf-8")
        written.append(skill_file)

    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
