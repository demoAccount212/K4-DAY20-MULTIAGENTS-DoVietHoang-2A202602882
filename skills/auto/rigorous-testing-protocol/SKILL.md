---
name: rigorous-testing-protocol
description: DÙNG KHI viết mã xử lý dữ liệu để đảm bảo tính chính xác và khả năng tái lập.
---
- Luôn tạo tệp kiểm thử riêng (ví dụ: `tests/test_regressions.py`) cho mỗi lỗi đã sửa.
- Viết ít nhất 3 trường hợp kiểm thử (test cases) cho mỗi tác vụ sửa lỗi.
- Thêm type hints cho tất cả các hàm công khai (public functions) để đảm bảo chất lượng mã nguồn.
- Chạy toàn bộ bộ kiểm thử sau mỗi lần thay đổi mã để đảm bảo không phát sinh lỗi mới (regression).
- Xác nhận mã chạy thành công với lệnh thực thi chuẩn (ví dụ: `python script.py`) trước khi kết thúc.