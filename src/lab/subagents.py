"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶC <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": "Dùng khi cần đọc tài liệu, docstring, mẫu dữ liệu hoặc tìm hiểu về vấn đề trước khi làm",
            "system_prompt": "Bạn là explorer. Nhiệm vụ là đọc tài liệu, xem nhanh các file liên quan và báo cáo lại faits saillants. Không sửa file nào."
        },
        {
            "name": "implementer",
            "description": "Dùng khi cần thực hiện thay đổi thực tế: viết code, sửa file, chạy test, hoặc tạo tài liệu mới",
            "system_prompt": "Bạn là implementer. Nhiệm vụ là thực hiện các thay đổi được yêu cầu một cách chính xác và đầy đủ. Báo cáo kết quả sau khi làm xong."
        },
        {
            "name": "reviewer",
            "description": "Dùng khi cần kiểm tra độc lập kết quả: kiểm tra code có tuân thủ convention không, xem xét các trường hợp biên, xác nhận tính đúng đắn",
            "system_prompt": "Bạn là reviewer. Nhiệm vụ là kiểm tra kết quả một cách khách đối và lập luận, không thực hiện thay đổi nào."
        }
    ]