# Kết quả kiểm chứng FitBreak

## Nguồn dữ liệu

| Chỉ số | Kết quả |
|---|---:|
| PDF trong `medical_knowledge` được chủ dự án duyệt | 16/16 |
| PDF có chunk trong cache RAG | 16/16 |
| Số chunk RAG | 4.077 |
| PDF chưa xác định được ngày áp dụng từ bản hiện có | 1 |
| Món ăn chưa đối chiếu giá trị theo từng công thức | 91/91 |
| Bài tập chưa đối chiếu hướng dẫn theo từng dòng | 36/36 |

Chi tiết từng PDF, gồm tên, ngày áp dụng, giới hạn và đường dẫn nguồn, nằm trong `source_inventory.json` và `approved_source_catalog.json`. Khi chưa có URL công khai, trích dẫn mở chính PDF qua `/chatbot/sources/{source_id}`.

## Kiểm thử

| Nhóm | Ca giả lập đạt/tổng | Ca trực tiếp đạt/tổng |
|---|---:|---:|
| TYPICAL | 20/20 | 1/1 |
| INSUFFICIENT_DATA | 20/20 | 1/1 |
| AI_ERROR | 20/20 | 1/1 |
| WARNING | 20/20 | 1/1 |

17 ca unit test trước đó đã được mở rộng lên **19/19**. Trong 20 đáp án sai giả lập, bộ chấm nhận diện 20; backend trực tiếp từ chối **11**. Các kết quả giả lập đo hợp đồng và guardrail. Bốn ca trực tiếp đo ranh giới kỹ thuật; `clinical_accuracy_score` vẫn là `null` vì chưa có chấm điểm lâm sàng độc lập.

Chủ dự án chấp nhận bộ ca để đưa vào báo cáo (`OWNER_APPROVED_FOR_REPORT`). Trạng thái này không được diễn giải thành thẩm định lâm sàng của chuyên gia y tế.

## Tệp kết quả

- `clinical_evaluation_report.md`, `.csv`, `.json`: bảng 80 ca, đầu vào, mong đợi, thực tế, lỗi và cách sửa.
- `live_clinical_sample.md`, `.csv`, `.json`: bốn phản hồi trực tiếp của nhà cung cấp AI.
- `source_inventory.json`: kiểm kê 16 PDF và trạng thái nguồn.
- `approved_source_catalog.json`: bản chụp danh mục nguồn được chủ dự án duyệt.
- `dataset_provenance.json`: kiểm kê dữ liệu món ăn và bài tập, gồm một ca đối chiếu công thức phở bò.
