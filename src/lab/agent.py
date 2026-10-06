"""GUIDE Phần 1 - Dựng tác tử (agent) bằng Deep Agents.   >>> SINH VIÊN CÀI ĐẶC <<<

Pseudo-code: guides/pseudocode/01_agent.md
Kiểm tra:    pytest tests/test_02_agent.py
"""
from pathlib import Path
import sys
import subprocess
import platform

from deepagents.backends import LocalShellBackend
from deepagents.backends.local_shell import ExecuteResponse


class GitBashShellBackend(LocalShellBackend):
    """Custom backend that uses Git Bash on Windows to execute Unix commands."""

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """Execute a shell command using Git Bash on Windows."""
        if not command or not isinstance(command, str):
            return ExecuteResponse(
                output="Error: Command must be a non-empty string.",
                exit_code=1,
                truncated=False,
            )

        effective_timeout = timeout if timeout is not None else self._default_timeout
        if effective_timeout <= 0:
            msg = f"timeout must be positive, got {effective_timeout}"
            raise ValueError(msg)

        # On Windows, wrap the command with Git Bash to run Unix commands
        if platform.system() == "Windows":
            # Convert Windows path to Git Bash path (e.g., D:\path\to\dir -> /d/path/to/dir)
            gitbash_root = self._windows_to_gitbash_path(str(self.cwd))
            # Use full path to bash.exe from Git for Windows
            bash_path = r"C:\Program Files\Git\bin\bash.exe"
            # Use bash with the working directory set to the Git Bash path
            bash_command = f'cd "{gitbash_root}" && {command}'
            # Use shell=False and pass command as list to avoid cmd.exe
            shell = False
            cmd = [bash_path, "-c", bash_command]
        else:
            shell = True
            cmd = command

        try:
            result = subprocess.run(  # noqa: S602
                cmd,
                check=False,
                shell=shell,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                text=True,
                timeout=effective_timeout,
                env=self._env,
                cwd=str(self.cwd) if platform.system() != "Windows" else None,
            )

            # Combine stdout and stderr
            output_parts = []
            if result.stdout:
                output_parts.append(result.stdout)
            if result.stderr:
                stderr_lines = result.stderr.strip().split("\n")
                output_parts.extend(f"[stderr] {line}" for line in stderr_lines)

            output = "\n".join(output_parts) if output_parts else "<no output>"

            # Check for truncation
            truncated = False
            if len(output) > self._max_output_bytes:
                output = output[: self._max_output_bytes]
                output += f"\n\n... Output truncated at {self._max_output_bytes} bytes."
                truncated = True

            # Add exit code info if non-zero
            if result.returncode != 0:
                output = f"{output.rstrip()}\n\nExit code: {result.returncode}"

            return ExecuteResponse(
                output=output,
                exit_code=result.returncode,
                truncated=truncated,
            )

        except subprocess.TimeoutExpired:
            if timeout is not None:
                msg = f"Error: Command timed out after {effective_timeout} seconds (custom timeout). The command may be stuck or require more time."
            else:
                msg = f"Error: Command timed out after {effective_timeout} seconds. For long-running commands, re-run using the timeout parameter."
            return ExecuteResponse(
                output=msg,
                exit_code=124,
                truncated=False,
            )
        except Exception as e:  # noqa: BLE001
            return ExecuteResponse(
                output=f"Error executing command ({type(e).__name__}): {e}",
                exit_code=1,
                truncated=False,
            )

    def _windows_to_gitbash_path(self, windows_path: str) -> str:
        """Convert Windows path to Git Bash path (e.g., D:\\path\\to\\dir -> /d/path/to/dir)."""
        if len(windows_path) >= 2 and windows_path[1] == ":":
            drive = windows_path[0].lower()
            path = windows_path[2:].replace("\\", "/")
            return f"/{drive}{path}"
        return windows_path


PATHS_NOTE = (
    "PATHS: every path is relative to the sandbox root and never starts with '/'. "
    "The task files are in the folder workspace/ (for example workspace/app.log). "
    "Use exactly this relative form both in the file tools and in the shell (execute); "
    "the shell starts in the sandbox root. "
)
BASE_PROMPT = (
    "You are an engineering assistant working in a sandbox. "
    + PATHS_NOTE
    + "Use the shell to run Python and tests. "
    "When you are done, reply with a short summary that mentions only files you really created or changed."
)
SKILLS_NOTE = (
    " Skills are in the folder skills/ (one sub-folder per skill with a SKILL.md). "
    "As your FIRST action, read the SKILL.md of every skill whose description could apply to the task, "
    "then follow them. Never modify skills/."
)
SUBAGENTS_NOTE = (
    " You have specialised subagents (see the description of the task tool). "
    "For anything beyond a trivial step, delegate to a suitable subagent and put ALL the task rules and file paths "
    "in the delegation message, because a subagent sees only what you send. "
    "Check what a subagent returns before you rely on it."
)

# ---- CÀI ĐẶT make_backend ----
def make_backend(sandbox: Path):
    """Tạo backend (môi trường thực thi) cho tác tử.

    Yêu cầu:
      - Thư mục gốc (root_dir) là `sandbox`; đường dẫn tương đối `workspace/...` và `skills/...`
        phải dùng được ở CẢ công cụ tệp lẫn shell (shell chạy với thư mục làm việc = `sandbox`).
      - Tác tử chạy được lệnh shell và gọi được `python` (cần đặt PATH).
      - KHÔNG chuyển biến môi trường của bạn vào shell của tác tử (khóa API không được lộ).
    """
    # Use Git Bash path for Python on Windows
    python_path = Path(sys.executable).parent.as_posix() + ":/usr/local/bin:/usr/bin:/bin"
    env = {
        "PATH": python_path,
        "HOME": str(sandbox),
        "PYTHONDONTWRITEBYTECODE": "1",
    }

    return GitBashShellBackend(
        root_dir=sandbox,
        virtual_mode=True,
        inherit_env=False,
        env=env,
        timeout=120,
    )


# ---- CÀI ĐẶT build_agent ----
def build_agent(sandbox: Path, mode: str = "single", use_skills: bool = False, model=None):
    """Tạo tác tử Deep Agents.

    Tham số:
      sandbox:    thư mục chứa `workspace/` (và `skills/` nếu có).
      mode:       "single"    -> tác tử mặc định (có subagent `general-purpose` sẵn của Deep Agents)
                  "subagents" -> thêm các subagent từ `get_subagents()` (nối PATHS_NOTE vào `system_prompt` của MỖI subagent,
                                  vì subagent không nhận BASE_PROMPT) và thêm SUBAGENTS_NOTE vào prompt chính
      use_skills: True -> nạp thư mục "/skills/" qua tham số `skills=` của create_deep_agent
                  và thêm SKILLS_NOTE vào prompt.
      model:      mô hình ngôn ngữ; None -> dùng `make_model()`.
    mode không hợp lệ -> ném ValueError.
    Trả về: đồ thị (graph) đã biên dịch, gọi bằng `.invoke({"messages": [...]})`.
    """
    from deepagents import create_deep_agent
    from .model import make_model
    from .subagents import get_subagents

    if mode not in ("single", "subagents"):
        raise ValueError(f"Invalid mode: {mode}. Must be 'single' or 'subagents'.")

    kwargs = {}
    prompt = BASE_PROMPT

    if mode == "subagents":
        # subagent KHÔNH nhận BASE_PROMPT, nên nối PATHS_NOTE vào system_prompt của từng subagent;
        # nếu không, subagent trộn lẫn "/workspace/x" và "workspace/x" và báo "không tìm thấy tệp"
        subs = get_subagents()
        kwargs["subagents"] = [
            {**sub, "system_prompt": sub["system_prompt"] + " " + PATHS_NOTE} for sub in subs
        ]
        prompt = prompt + SUBAGENTS_NOTE

    if use_skills:
        kwargs["skills"] = ["/skills/"]
        prompt = prompt + SKILLS_NOTE

    if model is None:
        model = make_model()

    return create_deep_agent(
        model=model,
        system_prompt=prompt,
        backend=make_backend(sandbox),
        **kwargs,
    )