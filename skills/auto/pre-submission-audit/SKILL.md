---
name: pre-submission-audit
description: DÙNG KHI chuẩn bị nộp bài để đảm bảo tuân thủ mọi quy tắc định dạng và cấu trúc dữ liệu.
---
- Đọc kỹ tệp yêu cầu (README/Prompt) để liệt kê danh sách các "RULE" bắt buộc.
- Kiểm tra tệp đầu ra (JSON/CSV) so với schema mẫu:
    - Xác nhận các trường bắt buộc (ví dụ: `meta`, `schema_version`).
    - Kiểm tra định dạng dữ liệu (ví dụ: tiền tệ phải là số nguyên cents, định dạng thời gian ISO-8601 UTC).
    - Kiểm tra quy tắc đặt tên (ví dụ: thay thế dấu gạch ngang bằng dấu gạch dưới trong tên dịch vụ).
- Xác nhận tệp đầu ra đã được sắp xếp đúng thứ tự (nếu có yêu cầu).
- Kiểm tra các tệp thay đổi: đảm bảo không sửa đổi tệp gốc trong thư mục `tests/` và đã cập nhật `CHANGELOG.md` theo đúng định dạng.