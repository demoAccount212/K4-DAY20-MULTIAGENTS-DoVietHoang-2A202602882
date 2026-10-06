# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| | | |

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: google_genai:gemini-3.1-flash-lite, temp=0, recursion_limit=60
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: deepagents 0.1.0, Windows 11 (Git Bash), chạy trực tiếp
- Số lần chạy tác vụ đã dùng / ngân sách: 9 runs (3 baseline + 3 subagents + 3 skills-auto learn)
- Commit của tag `freeze`: (pending)

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

> Dự đoán điều kiện nào đạt điểm cao nhất trên **tác vụ đánh giá** và vì sao. Nêu căn cứ từ phân loại lỗi (mục 4) và từ tài liệu tham khảo. Điền cả ba dòng; `verify_freeze.py` kiểm tra điều này.

- H1 (subagents so với baseline): Baseline sẽ đạt điểm cao hơn subagents trên tác vụ đánh giá. Trên tác vụ học, subagents chỉ được gọi 0-2 lần, không cải thiện điểm kỹ thuật (12/18 vs 15/18) mà tốn 2.3x token (302k vs 133k). Nhóm lỗi E (quy ước tổ chức) chiếm đa số và không được giải quyết bằng đa tác tử.
- H2 (skills-auto so với baseline): Skills-auto sẽ đạt điểm tương đương hoặc nhỉnh hơn baseline trên tác vụ đánh giá. Skills sinh ra (data-integrity-check, pre-submission-audit, rigorous-testing-protocol) nhắm vào các rule thất bại (money_in_cents, meta_block, clean_csv, regression_tests, type_hints) nhưng chỉ được đọc 1/3 lần (data-learn). Chi phí token thấp hơn baseline (113k vs 133k).
- H3 (tác vụ học so với tác vụ đánh giá): Điểm tác vụ đánh giá sẽ thấp hơn tác vụ học cho mọi điều kiện (dấu hiệu overfitting). Skills sinh từ failure của học có thể không áp dụng cho quy ước mới của đánh giá (new rules). SkillsBench/SkillEvolBench ghi nhận lợi ích trên học thường không chuyển sang tác vụ mới.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có công cụ: read_file, write_file, edit_file, ls, glob, grep, execute, task (và general-purpose subagent).
2. Công cụ `task` cho phép giao việc cho subagent `general-purpose` - subagent đó nhìn thấy system prompt giống tác tử chính nhưng không kế thừa context hội thoại; chỉ nhận prompt giao việc.
3. Từ mô tả `task`: "use it for any complex, context-heavy task"; từ mô tả `execute`: "run Python and tests".

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

> Chỉ dùng tác vụ học. Mỗi dòng là một check thất bại.

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| code-learn | tests_not_modified | E | "the original files in tests/ must not be modified" |
| code-learn | rule_type_hints | E | "RULE: every public function ... has type annotations" |
| code-learn | rule_regression_tests | E | "RULE: add tests/test_regressions.py with one test function per bug" |
| code-learn | rule_changelog | E | "RULE: record each fix in CHANGELOG.md under '## Unreleased'" |
| data-learn | north_q1_revenue | D | "wrong value (got 2314.87)" |
| data-learn | north_q1_orders | D | "wrong value (got 9)" |
| data-learn | rule_money_in_cents | E | "RULE: money values ... are integer cents" |
| data-learn | rule_meta_block | E | "RULE: answer.json has an object `meta` = ..." |
| data-learn | rule_clean_csv | E | "RULE: write workspace/clean.csv with the header ..." |
| logs-learn | rule_service_names | E | "RULE: service names ... lower-case with '-' replaced by '_'" |
| logs-learn | rule_sorted_errors | E | "RULE: `errors` is sorted by service, then by timestamp_utc" |
| logs-learn | rule_schema_header | E | "RULE: top-level object has `schema_version`: 2" |

Nhận xét: nhóm lỗi nào chiếm đa số? Skill có thể phòng ngừa nhóm đó không?
- Nhóm E (Vi phạm quy ước tổ chức) chiếm 12/19 failed checks (63%). Nhóm D (dữ liệu bẩn/định dạng) 7/19 (37%).
- Skill có thể phòng ngừa nhóm E nếu description kích hoạt đúng lúc (khi output có quy ước Acme). Curator đã sinh 3 skill nhắm vào E, nhưng skills_read=1/3 cho thấy description chưa đủ tốt.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế):
  - explorer: đọc tài liệu, docstring, mẫu dữ liệu; báo cáo sự thật; không sửa file
  - implementer: thực hiện thay đổi thực tế: viết code, sửa file, chạy test, tạo tài liệu
  - reviewer: kiểm tra độc lập kết quả theo đề bài và các trường hợp biên; không sửa
- `subagent_calls` ở từng tác vụ và nhận xét:
  - code-learn: 0 (recursion limit reached trước khi giao việc)
  - data-learn: 1 (đã gọi nhưng không cải thiện điểm)
  - logs-learn: 2 (đã gọi nhưng điểm giảm: 3/9 vs 6/9 baseline)
- Thông tin thiếu hoặc thừa khi giao việc: Không thể quan sát vì trace.md chỉ chứa luồng chính; subagent_calls > 0 nhưng không thấy nội dung delegation.
- Ảnh hưởng đến token và thời gian: Subagents tốn 2.3x token (302k vs 133k trung bình), 2-3x thời gian; không cải thiện điểm kỹ thuật (12/18 vs 15/18).

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator, số skill bị xóa và lý do: 1 lần chạy curator, 0 skill bị xóa (3 skill hợp lệ).

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| pre-submission-audit | Tổng quát (check output schema, naming, sorting, tests, CHANGELOG) | Đúng nhưng agent không đọc (skills_read=0) | 5 bước, description: "DÙNG KHI chuẩn bị nộp bài...", skills_read=0 |
| rigorous-testing-protocol | Tổng quát (test per bug, type hints, regression) | Đúng, khớp rule_regression_tests, rule_type_hints | 5 bước, description: "DÙNG KHI viết mã xử lý dữ liệu...", skills_read=0 |
| data-integrity-check | Tổng quát (rows_in/used, duplicate logic, sentinel values, canonical, clean.csv) | Đúng, khớp rule_money_in_cents, rule_meta_block, rule_clean_csv | 5 bước, description: "DÙNG KHI xử lý dữ liệu thô...", skills_read=1 (data-learn) |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây sau khi chạy Phần 4)
```

Lần chạy có error:
- baseline code-learn: GraphRecursionError (recursion_limit=60)
- subagents code-learn: GraphRecursionError
- skills-auto code-learn: GraphRecursionError
- Tất cả skills_modified = false (OK)

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
   - (sẽ điền sau khi chạy eval)

2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
   - (sẽ điền sau khi chạy eval)

3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp.
   - Giúp: data-learn đọc data-integrity-check (skills_read=1) nhưng vẫn fail rule_money_in_cents, rule_meta_block, rule_clean_csv → skill đọc nhưng không làm theo đầy đủ.
   - Không giúp: logs-learn skills_read=0, fail 3 rule checks; pre-submission-audit, rigorous-testing-protocol không được đọc.

4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
   - Baseline: 133,775 tokens, 15/18 technical
   - Subagents: 302,953 tokens, 12/18 technical (tệ hơn)
   - Skills-auto: 113,109 tokens, 12/18 technical (tốt hơn về cost)
   - Subagents không đáng chi phí trong thí nghiệm này.

5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
   - Không có tên tác vụ đánh giá, tên file cụ thể, con số đáp án trong skill (validate_skill chặn eval_markers).
   - Chỉ chạy curator 1 lần, không lặp lại trên skills-auto trace.

6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?
   - (sẽ điền sau khi chạy eval và freeze)

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1. Chỉ 3 tác vụ học / 3 tác vụ đánh giá - mẫu nhỏ, không đủ ý nghĩa thống kê.
2. Mỗi cấu hình chỉ chạy 1 lần - nhiễu mô hình (stochastic) làm kết quả không tái lập; cần chạy lặp (Phần 6e).
3. Mô hình đơn lẻ (gemini-3.1-flash-lite) - kết quả có thể không đại diện cho mô hình mạnh hơn.
4. Quy ước Acme được thiết kế sẵn bởi giảng viên - có thể thiên về loại lỗi E.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

(sẽ điền sau khi hoàn tất Phần 4)

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
  1. pytest tests/test_01_provided.py
  2. pytest tests/test_02_agent.py tests/test_03_runner.py
  3. python -m lab.runner --condition baseline --tasks data-learn
  4. python -m lab.runner --condition baseline --tasks code-learn logs-learn
  5. python -m lab.runner --condition subagents --tasks learn
  6. python -m lab.curator
  7. python -m lab.runner --condition skills-auto --tasks learn
- Thử thách mở rộng (nếu có): (chưa chọn)
- Ghi chú khác: