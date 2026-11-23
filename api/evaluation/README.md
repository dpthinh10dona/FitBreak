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

## Trạng thái duyệt của chủ dự án

Chủ dự án chấp nhận bộ ca để nộp báo cáo với trạng thái `OWNER_APPROVED_FOR_REPORT`.
Trạng thái này không phải là thẩm định lâm sàng độc lập. PASS kỹ thuật không xác nhận
đáp án đúng về lâm sàng.

Toàn bộ 16 PDF trong `api/app/core/dataset/medical_knowledge/source_catalog.json` đã
được đánh dấu `APPROVED` theo xác nhận của chủ dự án. Khi bản PDF không cung cấp ngày
áp dụng có thể đọc được, catalog ghi `null` và câu trả lời hiện “chưa xác định thời điểm áp dụng”.
RAG dùng chính PDF trong repository làm đường dẫn nguồn khi chưa có URL công khai.
Báo cáo 80/80 là kiểm thử hợp
đồng bằng mock, không phải điểm chất lượng của provider thật.

`python api/evaluation/build_source_inventory.py` lập danh mục kiểm kê toàn bộ PDF,
gồm hash, số trang, metadata trích từ trang đầu và trạng thái xác minh.
`python api/evaluation/build_dataset_provenance.py` kiểm kê 91 món ăn và 36 bài tập,
đánh dấu các dòng chưa đối chiếu với tài liệu gốc. Trích dẫn chung không xác nhận số liệu từng dòng.
`python api/evaluation/run_live_clinical_sample.py`
ghi phản hồi của provider vào báo cáo JSON, CSV và Markdown riêng. Trường `clinical_accuracy_score` để trống
cho tới khi chuyên gia đánh giá nội dung; lỗi kết nối không được tính thành câu trả lời sai.

Trong nhóm `AI_ERROR`, số đạt của bộ chấm chỉ cho thấy bộ chấm nhận ra đáp án giả lập sai.
Báo cáo ghi thêm `ai_error_enforcement.backend_rejected` để phân biệt số câu backend thực sự chặn.
Không dùng tỷ lệ 80/80 hoặc kết quả ca trực tiếp để kết luận AI đúng về lâm sàng.
