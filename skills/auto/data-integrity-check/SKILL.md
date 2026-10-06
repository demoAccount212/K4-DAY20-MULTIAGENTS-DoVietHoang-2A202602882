---
name: data-integrity-check
description: DÙNG KHI xử lý dữ liệu thô để đảm bảo tính nhất quán và đúng đắn của kết quả.
---
- Kiểm tra số lượng dòng dữ liệu đầu vào và đầu ra (rows_in vs rows_used) để ghi vào block `meta`.
- Xác nhận logic xử lý trùng lặp (duplicate removal) khớp chính xác với mô tả trong README.
- Kiểm tra các giá trị đặc biệt (ví dụ: -999, null) và xử lý chúng theo quy tắc nghiệp vụ trước khi tính toán.
- Đối chiếu kết quả tính toán cuối cùng với các yêu cầu về định dạng (ví dụ: canonical spelling cho vùng miền).
- Đảm bảo tệp `clean.csv` (nếu có) tuân thủ đúng header và định dạng cột đã quy định.