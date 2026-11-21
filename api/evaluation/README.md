# FitBreak Clinical Evaluation

Bộ đánh giá này tách khỏi `test_suite.py` và không gọi Gemini, Groq, Supabase hay mạng.

## Phạm vi

- `TYPICAL`: câu trả lời điển hình phải trích đúng và đủ tập nguồn đã truy xuất.
- `INSUFFICIENT_DATA`: thiếu bằng chứng hoặc provider lỗi phải fail-closed, không sinh tư vấn.
- `AI_ERROR`: câu trả lời sai có gold standard và phải bị bộ chấm từ chối.
- `WARNING`: ca cảnh báo phải hướng người dùng đến cấp cứu/cơ sở y tế và trích đúng nguồn.

## Chạy

```powershell
python api/evaluation/run_clinical_evaluation.py
```

Lệnh sinh ba báo cáo bền vững trong `api/evaluation/reports/`: JSON để tích hợp CI,
CSV để lọc/phân tích và Markdown để nộp minh chứng.

## Duyệt chuyên gia

Các gold standard hiện mang trạng thái `PENDING_CLINICAL_REVIEW`. Người có thẩm quyền cần
đối chiếu từng ca `AI_ERROR`, ghi nhận danh tính/phạm vi duyệt theo quy trình của dự án rồi
mới đổi `review_policy.review_status` thành `APPROVED`. Không được coi PASS kỹ thuật là xác
nhận đúng về lâm sàng.
