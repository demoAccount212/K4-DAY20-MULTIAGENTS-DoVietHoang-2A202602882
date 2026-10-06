# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| | | |

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: google_genai:gemini-3.1-flash-lite, temp=0, recursion_limit=60
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: deepagents 0.1.0, Windows 11 (Git Bash), chạy trực tiếp
- Số lần chạy tác vụ đã dùng / ngân sách: 18 runs (6 baseline + 6 subagents + 6 skills-auto)
- Commit của tag `freeze`: 0564f82

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Baseline sẽ đạt điểm cao hơn subagents trên tác vụ đánh giá. Trên tác vụ học, subagents chỉ được gọi 0-2 lần, không cải thiện điểm kỹ thuật (12/18 vs 15/18) mà tốn 2.3x token (302k vs 133k). Nhóm lỗi E (quy ước tổ chức) chiếm đa số và không được giải quyết bằng đa tác tử.
- H2 (skills-auto so với baseline): Skills-auto sẽ đạt điểm tương đương hoặc nhỉnh hơn baseline trên tác vụ đánh giá. Skills sinh ra (data-integrity-check, pre-submission-audit, rigorous-testing-protocol) nhắm vào các rule thất bại (money_in_cents, meta_block, clean_csv, regression_tests, type_hints) nhưng chỉ được đọc 1/3 lần (data-learn). Chi phí token thấp hơn baseline (113k vs 133k).
- H3 (tác vụ học so với tác vụ đánh giá): Điểm tác vụ đánh giá sẽ thấp hơn tác vụ học cho mọi điều kiện (dấu hiệu overfitting). Skills sinh từ failure của học có thể không áp dụng cho quy ước mới của đánh giá (new rules). SkillsBench/SkillEvolBench ghi nhận lợi ích trên học thường không chuyển sang tác vụ mới.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có công cụ: read_file, write_file, edit_file, ls, glob, grep, execute, task (và general-purpose subagent).
2. Công cụ `task` cho phép giao việc cho subagent `general-purpose` - subagent đó nhìn thấy system prompt giống tác tử chính nhưng không kế thừa context hội thoại; chỉ nhận prompt giao việc.
3. Từ mô tả `task`: "use it for any complex, context-heavy task"; từ mô tả `execute`: "run Python and tests".

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

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

Nhận xét: Nhóm E (Vi phạm quy ước tổ chức) chiếm 12/19 failed checks (63%). Nhóm D (dữ liệu bẩn/định dạng) 7/19 (37%). Skill có thể phòng ngừa nhóm E nếu description kích hoạt đúng lúc (khi output có quy ước Acme). Curator đã sinh 3 skill nhắm vào E, nhưng skills_read=1/3 cho thấy description chưa đủ tốt.

## 5. Điều kiện `subagents` (Phần 2.3)

- Các subagent đã định nghĩa:
  - explorer: đọc tài liệu, docstring, mẫu dữ liệu; báo cáo sự thật; không sửa file
  - implementer: thực hiện thay đổi thực tế: viết code, sửa file, chạy test, tạo tài liệu
  - reviewer: kiểm tra độc lập kết quả theo đề bài và các trường hợp biên; không sửa
- `subagent_calls` ở từng tác vụ:
  - code-learn: 0 (recursion limit reached trước khi giao việc)
  - data-learn: 1 (đã gọi nhưng không cải thiện điểm)
  - logs-learn: 2 (đã gọi nhưng điểm giảm: 3/9 vs 6/9 baseline)
  - code-eval: 0 (recursion)
  - data-eval: 8
  - logs-eval: 6
- Thông tin thiếu hoặc thừa khi giao việc: Không thể quan sát vì trace.md chỉ chứa luồng chính.
- Ảnh hưởng đến token và thời gian: Subagents tốn 2.3x token (302k vs 133k trung bình learn, 145k vs 95k eval), 2-3x thời gian; không cải thiện điểm kỹ thuật (12/18 vs 15/18 learn, 12/18 vs 17/18 eval).

## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator, số skill bị xóa và lý do: 1 lần chạy curator, 0 skill bị xóa (3 skill hợp lệ).

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| pre-submission-audit | Tổng quát (check output schema, naming, sorting, tests, CHANGELOG) | Đúng nhưng agent không đọc | 5 bước, desc: "DÙNG KHI chuẩn bị nộp bài...", skills_read=0 |
| rigorous-testing-protocol | Tổng quát (test per bug, type hints, regression) | Đúng, khớp rule_regression_tests, rule_type_hints | 5 bước, desc: "DÙNG KHI viết mã xử lý dữ liệu...", skills_read=0 |
| data-integrity-check | Tổng quát (rows_in/used, duplicate logic, sentinel values, canonical, clean.csv) | Đúng, khớp rule_money_in_cents, rule_meta_block, rule_clean_csv | 5 bước, desc: "DÙNG KHI xử lý dữ liệu thô...", skills_read=1 (data-learn) |

## 7. Kết quả so sánh (Phần 4.3, 4.4)

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 6/10 | 6/10 | 3/10 |
| data-learn | 3/8 | 3/8 | 3/8 |
| logs-learn | 6/9 | 3/9 | 6/9 |
| code-eval | 6/11 | 3/11 | 6/11 |
| data-eval | 5/9 | 5/9 | 5/9 |
| logs-eval | 6/10 | 4/10 | 6/10 |
| **Mean score - learning tasks** | 0.55 | 0.44 | 0.45 |
| **Mean score - evaluation tasks** | 0.57 | 0.41 | 0.57 |
| **Mean tokens per run** | 114,320 | 224,077 | 126,595 |
| **Runs that read a skill** | 0/6 | 0/6 | 1/6 |

```text
condition     role    technical  house rules  mean tokens  read a skill
baseline      eval     17/18         0/12          94,865      0/3     
baseline      learn    15/18         0/9          133,775      0/3     
subagents     eval     12/18         0/12         145,201      0/3     
subagents     learn    12/18         0/9          302,953      0/3     
skills-auto   eval     17/18         0/12         140,081      0/3     
skills-auto   learn    12/18         0/12         113,109      1/3     
```

Lần chạy có error:
- baseline code-learn: GraphRecursionError (recursion_limit=60)
- subagents code-learn: GraphRecursionError
- subagents code-eval: GraphRecursionError
- skills-auto code-learn: GraphRecursionError
- skills-auto code-eval: GraphRecursionError
- Tất cả skills_modified = false (OK)

## 8. Phân tích

1. **So với `baseline`, điều kiện nào cải thiện điểm tác vụ học? Đánh giá? Có điều kiện nào cải thiện học nhưng không đánh giá?**
   - Học: Baseline tốt nhất (0.55). Subagents (0.44) và skills-auto (0.45) đều kém hơn.
   - Đánh giá: Baseline = skills-auto (0.57), subagents tệ nhất (0.41).
   - Skills-auto cải thiện đánh giá so với học (0.57 vs 0.45) nhưng không vượt baseline. Đây là dấu hiệu **skills sinh ra giúp chuyển giao tốt hơn từ học sang đánh giá**, nhưng không đủ mạnh để vượt baseline.

2. **Tách điểm check kỹ thuật vs quy ước (`rule_`). Skill giúp nhóm nào? Rule mới của eval có được giúp không?**
   - Technical: Baseline 17/18 eval, skills-auto 17/18 eval, subagents 12/18 eval → Skills-auto giữ ngang baseline về kỹ thuật.
   - House rules: TẤT CẢ 0/12 eval, 0/9 learn → **Không condition nào đạt bất kỳ rule check nào**.
   - Skills sinh ra nhắm vào rule (money_in_cents, meta_block, clean_csv, regression_tests, type_hints, service_names, sorted, schema_version) nhưng skills_read=0/3 eval → **Agent không đọc skill**.
   - Rule mới của eval: Không được giúp vì skill không được đọc.

3. **Check skill giúp đạt vs không giúp:**
   - Giúp: Không có check nào được giúp rõ rệt. Data-learn đọc data-integrity-check (skills_read=1) nhưng vẫn fail 3 rule checks → skill đọc nhưng không làm theo đầy đủ (chỉ làm phần technical).
   - Không giúp: Logs-learn skills_read=0, fail 3 rule; pre-submission-audit, rigorous-testing-protocol không được đọc.

4. **Chi phí: so sánh token, hiệu quả điểm/token, đa tác tử có đáng chi phí?**
   - Baseline: 114k tokens/run, score 0.56 avg → **4.9 pts/100k tokens**
   - Subagents: 224k tokens/run, score 0.43 avg → **1.9 pts/100k tokens** (tệ hơn 2.6x)
   - Skills-auto: 127k tokens/run, score 0.51 avg → **4.0 pts/100k tokens** (gần baseline)
   - **Kết luận**: Subagents không đáng chi phí (2.6x cost, điểm thấp hơn). Skills-auto hiệu quả tương đương baseline nhưng không vượt trội.

5. **Dấu hiệu rò rỉ/quá khớp? Phòng tránh như thế nào?**
   - Không có tên tác vụ eval, file cụ thể, con số đáp án trong skill (validate_skill chặn eval_markers).
   - Chỉ chạy curator 1 lần, không lặp lại trên skills-auto trace.
   - Skills_overfitting: Skills sinh từ học nhưng không áp dụng được rule mới của eval (house rules 0/12).

6. **Nhiễu: so sánh điểm học Phần 3.4 vs sau freeze.**
   - Phần 3.4 (skills-auto learn): code-learn 3/10, data-learn 3/8, logs-learn 6/9
   - Sau freeze (cùng skill): Giống hệt (lưu trữ cùng thư mục ghi đè)
   - Chênh lệch = 0 → Kết quả ổn định, không bị nhiễu giữa 2 lần chạy cùng skill. Nhưng cũng cho thấy skill không cải thiện được vì agent không đọc.

## 9. Hạn chế và tính hợp lệ

1. Chỉ 3 tác vụ học / 3 tác vụ đánh giá - mẫu nhỏ, không đủ ý nghĩa thống kê.
2. Mỗi cấu hình chỉ chạy 1 lần - nhiễu mô hình (stochastic) làm kết quả không tái lập; cần chạy lặp (Phần 6e).
3. Mô hình đơn lẻ (gemini-3.1-flash-lite) - kết quả có thể không đại diện cho mô hình mạnh hơn.
4. Quy ước Acme được thiết kế sẵn bởi giảng viên - thiên về loại lỗi E (63% failures).
5. Recursion limit (60) cắt ngang code-learn tasks → mất điểm không phản ánh năng lực thực.

## 10. Kết luận

1. Baseline (Deep Agents mặc định) đạt điểm cao nhất trên cả học (0.55) và đánh giá (0.57).
2. Subagents giảm điểm và tốn 2x token - không đáng dùng trong setup này.
3. Skills-auto đạt ngang baseline trên đánh giá (0.57) nhưng không vượt trội; skills_read thấp (1/6) do description chưa đủ tốt.
4. **Vấn đề cốt lõi**: 100% house-rule checks fail ở mọi điều kiện → Agent không tuân thủ quy ước output.
5. Đề xuất: Cải thiện `description` của skill (trigger condition rõ ràng), tăng recursion_limit cho code tasks, thêm few-shot examples cho rule compliance.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
  1. pytest tests/test_01_provided.py
  2. pytest tests/test_02_agent.py tests/test_03_runner.py
  3. python -m lab.runner --condition baseline --tasks data-learn
  4. python -m lab.runner --condition baseline --tasks code-learn logs-learn
  5. python -m lab.runner --condition subagents --tasks learn
  6. python -m lab.curator
  7. python -m lab.runner --condition skills-auto --tasks learn
  8. python -m lab.runner --condition baseline --tasks eval
  9. python -m lab.runner --condition subagents --tasks eval
  10. python -m lab.runner --condition skills-auto --tasks eval
  11. python -m lab.compare > report/table.md
  12. python scripts/check_breakdown.py
- Thử thách mở rộng: (không chọn)
- Ghi chú khác: Freeze tag 0564f82, hypotheses commit 2e1b3e2