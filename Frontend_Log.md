# FRONTEND_LOG: HỆ THỐNG GIAO DIỆN Y TẾ & MEDTECH (FITBREAK HEALTHCARE PLATFORM)

> **Role**: Senior Frontend Developer & UI/UX Designer specializing in Healthcare & MedTech Applications.  
> **Target Standards**: WCAG 2.1 AA/AAA Accessibility, Mobile-First Responsiveness, Clinical-Grade Usability, Low Cognitive Load.

---

## 1. TỔNG QUAN HỆ THỐNG THIẾT KẾ (MEDTECH DESIGN SYSTEM SPECIFICATIONS)

### 1.1 Bảng màu Y tế Chuẩn mực (Clinical Color Palette)
* **Primary / Trust Blue (`--med-primary`)**: `#0284C7` (Sky 600) / `#0369A1` (Sky 700) - Tượng trưng cho sự tin cậy, y khoa chuẩn mực, an tâm cho bệnh nhân.
* **Secondary / Deep Navy (`--med-navy`)**: `#0F172A` (Slate 900) - Màu chữ tiêu đề, mang tính vững chắc, chuyên nghiệp.
* **Clinical Surface (`--med-bg-surface`)**: `#FFFFFF` (Pure White) - Bề mặt thẻ trắng sáng, vô trùng, thanh lịch.
* **Background Canvas (`--med-bg-base`)**: `#F8FAFC` (Slate 50) - Nền tổng thể mềm mại, triệt tiêu cảm giác chói mắt.
* **Border & Dividers (`--med-border`)**: `#E2E8F0` (Slate 200) - Đường nét sắc sảo, tối giản, ngăn nắp.
* **Semantic Status Indicators**:
  * **Success / Normal Vitals (`--med-success`)**: `#10B981` (Emerald 500) - Chỉ số cơ thể đạt mức an toàn.
  * **Warning / Moderate Risk (`--med-warning`)**: `#F59E0B` (Amber 500) - Chỉ số cần lưu ý (tiền béo phì, tiền tiểu đường).
  * **Danger / Critical Alert (`--med-danger`)**: `#EF4444` (Rose 500) - Chỉ số báo động (huyết áp cao, hạ SpO2).

### 1.2 Kiểu chữ & Thị giác (Typography & Hierarchy)
* **Font Family**: `Inter`, `-apple-system`, `BlinkMacSystemFont`, `'Segoe UI'`, `Roboto`, sans-serif.
* **Đặc tính**: Kích thước chữ tối thiểu cho nội dung đọc là 15px - 16px, độ tương phản màu (Contrast Ratio) ≥ 4.5:1 đạt chuẩn WCAG AA cho người thị lực kém.

---

## 2. KẾ HOẠCH LỘ TRÌNH TRIỂN KHAI (ROADMAP & IMPLEMENTATION STATUS)

| Giai đoạn | Hạng mục / Module | Mô tả chi tiết | Trạng thái |
| :---: | :--- | :--- | :---: |
| **P1** | **MedTech Design Tokens & Foundations** | Xây dựng biến CSS chuẩn (`medtech-theme.css`), typography, reset và spacing chuẩn mực y tế. | 🟢 Hoàn thành |
| **P2** | **Patient Dashboard Header & Medical Summary Banner** | Header tinh giản cho bệnh nhân, thanh trạng thái, Avatar/Bệnh án, và các thẻ sinh tồn tóm tắt (Vitals Quickview). | 🟢 Hoàn thành |
| **P3** | **Health Metrics & Vital Signs Cards** | Trực quan hóa kết quả kiểm tra sức khỏe (BMI, Huyết áp, SpO2, Đường huyết) với thanh đo ngưỡng an toàn lâm sàng. | 🟢 Hoàn thành |
| **P4** | **Personalized Clinical Diet & Food Module** | Giao diện tư vấn dinh dưỡng y khoa, hiển thị rõ giải thích lâm sàng, lọc dị ứng, khẩu phần rõ ràng. | 🟢 Hoàn thành |
| **P5** | **Physical Activity & Rehabilitation Schedule** | Lịch tập phục hồi chức năng và thể dục theo phân loại `light` / `medium` / `heavy` dễ nhìn, lịch hẹn rõ ràng. | 🟢 Hoàn thành |
| **P6** | **Telehealth AI Doctor ChatBot** | Cửa sổ hội chẩn trực tuyến chuyên nghiệp, hiển thị thẻ đề xuất cập nhật thông tin sức khỏe an toàn. | 🟢 Hoàn thành |
| **P7** | **Theme Harmonization & MedTech Auth Overhaul** | Đồng bộ màu sắc giữa các module y tế và ứng dụng nền tối; thiết kế lại toàn bộ màn hình Log In / Sign Up theo phong cách Medical Blue & Clean White. | 🟢 Hoàn thành |

---

## 3. NHẬT KÝ THỰC HIỆN CHI TIẾT (ACTION LOGS)

### [2026-11-08] - Khởi tạo Kiến trúc & Tài liệu Thiết kế
* **Người thực hiện**: Senior Frontend Developer & UI/UX Designer.
* **Hành động**:
  - Tạo tài liệu quản lý tiến độ `Frontend_Log.md` tại thư mục gốc của dự án.
  - Chuẩn hóa thông số kỹ thuật (Tokens, Palette, A11y rules) cho toàn bộ hệ sinh thái MedTech Web App.

### [2026-11-08] - Hoàn thành Giai đoạn 1 & 2 (P1 & P2): Design Tokens & Patient Dashboard Header
* **Files tạo mới / chỉnh sửa**:
  - `frontend/src/style/medtech-theme.css`: Định nghĩa hệ thống biến màu lâm sàng.
  - `frontend/src/style/patientHeader.css`: Styling chi tiết cho Header bệnh nhân và Grid thẻ sinh tồn Vitals.
  - `frontend/src/components/patientHeader.jsx`: Component Header y tế đạt chuẩn WCAG AA.
  - `frontend/src/App.jsx`: Tích hợp thay thế Header & Summary Cards cũ.
  - `frontend/src/main.jsx`: Nạp Design System Tokens vào toàn bộ ứng dụng.

### [2026-11-08] - Hoàn thành Giai đoạn 3 (P3): Health Metrics & Vital Signs Cards
* **Files tạo mới / chỉnh sửa**:
  - `frontend/src/style/clinicalCheckup.css`: Styling thẻ lâm sàng vô trùng, thanh chỉ số cảnh báo có viền màu sắc động.
  - `frontend/src/components/clinicalVitalCheckup.jsx`: Tách module nhập liệu sinh tồn đạt chuẩn y tế MedTech.
  - `frontend/src/components/updateProfile.jsx`: Tái cấu trúc, nhúng sạch sẽ `ClinicalVitalCheckup` vào trang Hồ sơ y tế của bệnh nhân.

### [2026-11-08] - Hoàn thành Giai đoạn 4 (P4): Personalized Clinical Diet & Food Module
* **Files tạo mới / chỉnh sửa**:
  - `frontend/src/style/clinicalDiet.css`: Styling chuyên biệt cho Module Dinh Dưỡng Lâm Sàng MedTech.
  - `frontend/src/components/clinicalNutritionModule.jsx`: Component tư vấn dinh dưỡng y khoa kết nối AI.
  - `frontend/src/App.jsx`: Tích hợp thay thế tab `food` sang `ClinicalNutritionModule`.

### [2026-11-08] - Hoàn thành Giai đoạn 5 (P5): Physical Activity & Rehabilitation Schedule
* **Files tạo mới / chỉnh sửa**:
  - `frontend/src/style/clinicalSchedule.css`: Thời khóa biểu y tế 7 ngày phong cách tối giản lâm sàng.
  - `frontend/src/components/clinicalRehabSchedule.jsx`: Quản lý lộ trình tập phục hồi và vận động thể lực.
  - `frontend/src/App.jsx`: Tích hợp thay thế tab `schedule` sang `ClinicalRehabSchedule`.

### [2026-11-08] - Hoàn thành Giai đoạn 6 (P6): Telehealth AI Doctor ChatBot
* **Files tạo mới / chỉnh sửa**:
  - `frontend/src/style/telehealthChatbot.css`: Cửa sổ trò chuyện tư vấn y tế từ xa.
  - `frontend/src/components/telehealthDoctorChatbot.jsx`: Bác sĩ AI FitBreak với failover Gemini -> Groq.
  - `frontend/src/App.jsx`: Tích hợp vào ứng dụng.

### [2026-11-08] - Hoàn thành Giai đoạn 7 (P7): Đồng bộ Giao diện & Tái thiết kế Log In / Sign Up
* **Files tạo mới / chỉnh sửa**:
  - `frontend/src/style/medtech-theme.css`: Cập nhật bảng màu giao diện bên trong sang tone Deep Medical Slate đồng bộ hoàn hảo với nền tối tổng thể của ứng dụng (`#080a12`, `#101424`), viền Medical Sky (`rgba(56, 189, 248, 0.2)`), loại bỏ hiện tượng các khối trắng tinh bị đối chọi gay gắt với TaskBoard, Pomodoro và Shop.
  - `frontend/src/style/patientHeader.css`: Đồng bộ Header và Vitals Banner theo phong cách Medical Slate & Glass, văn bản trắng sắc nét, viền xanh y khoa hiện đại.
  - `frontend/src/style/clinicalDiet.css`, `frontend/src/style/clinicalSchedule.css`, `frontend/src/style/telehealthChatbot.css`: Thay thế các mã màu nền trắng cứng `#ffffff` bằng các biến thẻ nền y tế đồng bộ.
  - `frontend/src/style/logIn.css` & `frontend/src/style/signUp.css`: Thiết kế lại hoàn toàn giao diện ngoài (Log In / Sign Up) theo đúng tinh thần **Medical Blue & Crisp White** (#0284c7, #f8fafc, #ffffff), thẻ trắng lâm sàng vô trùng, input focus xanh y tế, hiệu ứng thanh lịch và chuyên nghiệp.
  - `frontend/src/components/logIn.jsx` & `frontend/src/components/signUp.jsx`: Cập nhật nội dung thương hiệu y tế, huy hiệu kiểm chuẩn lâm sàng, tính năng theo dõi sinh hiệu và bác sĩ AI.
* **Kiểm tra**: `vite build` thành công 100% trong 591ms.
