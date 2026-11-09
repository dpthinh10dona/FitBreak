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

---

## 3. NHẬT KÝ THỰC HIỆN CHI TIẾT (ACTION LOGS)

### [2026-11-08] - Khởi tạo Kiến trúc & Tài liệu Thiết kế
* **Người thực hiện**: Senior Frontend Developer & UI/UX Designer.
* **Hành động**:
  - Tạo tài liệu quản lý tiến độ `Frontend_Log.md` tại thư mục gốc của dự án.
  - Chuẩn hóa thông số kỹ thuật (Tokens, Palette, A11y rules) cho toàn bộ hệ sinh thái MedTech Web App.
* **Bước tiếp theo**: Khởi tạo file style `frontend/src/style/medtech-theme.css` và bắt đầu code Component **Patient Dashboard Header & Medical Summary Cards**.

### [2026-11-08] - Hoàn thành Giai đoạn 1 & 2 (P1 & P2): Design Tokens & Patient Dashboard Header
* **Files tạo mới / chỉnh sửa**:
  - `frontend/src/style/medtech-theme.css`: Định nghĩa hệ thống biến màu lâm sàng (Medical Blue `#0284C7`, Deep Navy `#0F172A`, Surface White `#FFFFFF`, Canvas `#F8FAFC`, Emerald `#10B981`, Rose `#EF4444`).
  - `frontend/src/style/patientHeader.css`: Styling chi tiết cho Header bệnh nhân và Grid thẻ sinh tồn Vitals.
  - `frontend/src/components/patientHeader.jsx`: Component Header y tế đạt chuẩn WCAG AA, hiển thị thể trạng BMI, TDEE, Cường độ vận động y tế (`light`/`medium`/`heavy`) và Hộp cảnh báo dinh dưỡng lâm sàng.
  - `frontend/src/App.jsx`: Tích hợp thay thế Header & Summary Cards cũ.
  - `frontend/src/main.jsx`: Nạp Design System Tokens vào toàn bộ ứng dụng.
* **Kiểm tra**: `vite build` thành công 100% trong 997ms.
* **Giai đoạn tiếp theo**: **P3 - Health Metrics & Vital Signs Cards** (Trực quan hóa bảng nhập và đo chỉ số sinh tồn: Huyết áp, SpO2, Đường huyết).

### [2026-11-08] - Hoàn thành Giai đoạn 3 (P3): Health Metrics & Vital Signs Cards
* **Files tạo mới / chỉnh sửa**:
  - `frontend/src/style/clinicalCheckup.css`: Styling thẻ lâm sàng vô trùng (Sterile White Card `#FFFFFF`), thanh chỉ số cảnh báo có viền màu sắc động (`border-left` theo mức `normal`, `warning`, `danger`), bố cục input trực quan kèm hậu tố đơn vị y tế (`mmHg`, `mg/dL`, `%`).
  - `frontend/src/components/clinicalVitalCheckup.jsx`: Tách module nhập liệu sinh tồn đạt chuẩn y tế MedTech, chip chọn thời điểm đo đường huyết (`Lúc đói ≥ 8h`, `Trước bữa ăn`, `Ngẫu nhiên`), trực quan hóa kết quả phân tích nguy cơ lâm sàng và đồng bộ với Supabase.
  - `frontend/src/components/updateProfile.jsx`: Tái cấu trúc, nhúng sạch sẽ `ClinicalVitalCheckup` vào trang Hồ sơ y tế của bệnh nhân.
* **Kiểm tra**: `vite build` vượt qua thành công 100% trong 372ms.
* **Giai đoạn tiếp theo**: **P4 - Personalized Clinical Diet & Food Module** (Tái thiết kế giao diện gợi ý thực đơn dinh dưỡng lâm sàng, phân tách khẩu phần và giải thích y khoa).

### [2026-11-08] - Hoàn thành Giai đoạn 4 (P4): Personalized Clinical Diet & Food Module
* **Files tạo mới / chỉnh sửa**:
  - `frontend/src/style/clinicalDiet.css`: Styling chuyên biệt cho Module Dinh Dưỡng Lâm Sàng MedTech. Nền thẻ trắng tinh khiết `#FFFFFF`, thanh đồng bộ chỉ số sinh tồn (TDEE, Protein, Lời khuyên y khoa), các thẻ chọn mục tiêu thể trạng/hình thức nấu/dị ứng y khoa sắc nét. Thiết kế 3 thẻ bữa ăn (Sáng, Trưa, Tối) trực quan với thanh tiến trình đo Macro (Đạm, Carb, Béo).
  - `frontend/src/components/clinicalNutritionModule.jsx`: Component tư vấn dinh dưỡng y khoa, kết nối API AI RAG `/food-suggest`, tự động loại trừ món ăn khi bấm "Đổi thực đơn khác", và hiển thị rõ ràng Hộp phân tích lâm sàng của Bác sĩ (`clinical-rationale-card`).
  - `frontend/src/App.jsx`: Tích hợp thay thế tab `food` sang `ClinicalNutritionModule`.
* **Kiểm tra**: `vite build` thành công 100% trong 371ms.
* **Giai đoạn tiếp theo**: **P5 - Physical Activity & Rehabilitation Schedule** (Lịch trình vận động & bài tập phục hồi chức năng cá nhân hóa theo mức `light`, `medium`, `heavy`).

### [2026-11-08] - Hoàn thành Giai đoạn 5 (P5): Physical Activity & Rehabilitation Schedule
* **Files tạo mới / chỉnh sửa**:
  - `frontend/src/style/clinicalSchedule.css`: Thiết kế thời khóa biểu y tế 7 ngày phong cách tối giản lâm sàng (Sterile Timetable). Thẻ phân loại bài tập y tế rõ ràng (`badge-clinical-resistance`, `badge-clinical-cardio`, `badge-clinical-hiit`, `badge-clinical-rest`). Khối đơn thuốc vận động y khoa có viền màu `border-left` theo cường độ `light`, `medium`, `heavy`.
  - `frontend/src/components/clinicalRehabSchedule.jsx`: Component quản lý lộ trình tập phục hồi và vận động thể lực, tích hợp chỉ dẫn đơn thuốc y khoa từ bác sĩ theo tình trạng sức khỏe thực tế của bệnh nhân. Hỗ trợ xem thời khóa biểu 7 ngày và kéo chọn khung giờ rảnh để tạo giáo án phục hồi tự động qua API backend.
  - `frontend/src/App.jsx`: Tích hợp thay thế tab `schedule` sang `ClinicalRehabSchedule`.
* **Kiểm tra**: `vite build` vượt qua thành công 100% trong 322ms.
* **Giai đoạn tiếp theo**: **P6 - Telehealth AI Doctor ChatBot** (Nâng cấp giao diện ChatBot bác sĩ tư vấn trực tuyến phong cách Telemedicine, tối giản, thanh lịch, tin cậy).

### [2026-11-08] - Hoàn thành Giai đoạn 6 (P6): Telehealth AI Doctor ChatBot
* **Files tạo mới / chỉnh sửa**:
  - `frontend/src/style/telehealthChatbot.css`: Thiết kế cửa sổ trò chuyện tư vấn từ xa (Telemedicine Virtual Clinic). Nền trắng lâm sàng thanh thoát, bong bóng chat Medical Blue sắc sảo, avatar bác sĩ `👨‍⚕️`, nhãn trạng thái trực tuyến an tâm. Thẻ đề xuất cập nhật hồ sơ y tế (`clinical-proposal-card`) có viền phân loại mâu thuẫn (`has-conflict`) bằng màu đỏ cảnh báo hoặc xanh ngọc đồng thuận.
  - `frontend/src/components/telehealthDoctorChatbot.jsx`: Component Bác sĩ Trợ lý Y khoa FitBreak. Ràng buộc chuẩn y tế nghiêm ngặt (< 100 từ/câu, tối đa 3 lượt/ngày), kết nối Failover Gemini / Groq API, hiển thị card xác nhận thông tin bệnh án và tự động reload hồ sơ sau khi cập nhật thành công lên Supabase.
  - `frontend/src/App.jsx`: Tích hợp thay thế sang `TelehealthDoctorChatbot`.
* **Kiểm tra**: `vite build` thành công 100% trong 366ms.
* **Tổng kết lộ trình**: Toàn bộ 6 giai đoạn chuẩn hóa giao diện y tế **Healthcare & MedTech Web Platform** đã hoàn tất 100%. Mọi tiêu chuẩn WCAG 2.1 AA, Mobile-First, Low Cognitive Load và thiết kế lâm sàng đã được áp dụng đồng bộ.

---

## 7. ĐỒNG BỘ TOÀN DIỆN HỆ THỐNG GIAO DIỆN XANH TRẮNG & CHUẨN HÓA DATASET DINH DƯỠNG

### 7.1 Chuẩn hóa Form Dinh Dưỡng & Dataset (`clinicalNutritionModule.jsx`, `rag_service.py`)
- **Mục tiêu thể hình & Sức khỏe (`aim`)**:
  - `Giảm cân`: Giảm tinh bột (🏃)
  - `Tăng cơ`: Tăng Protein (💪)
  - `Duy trì`: Cân bằng (⚖️)
- **Chế độ ăn (`diet_type`)**:
  - `Ăn chay`: Thuần thực vật (🌱) -> lọc món `vegetarian` trong dataset.
  - `Không kiêng`: Đa dạng thực phẩm (🍽️) -> cho phép toàn bộ món ăn trong dataset.
  - `Eat clean`: Tự nhiên & Tươi sạch (🥦) -> lọc món `eat_clean` trong dataset.
- **Thực phẩm kiêng cữ / Dị ứng y khoa (`allergens`)**: Chuẩn hóa chính xác 3 loại dị ứng theo quy ước:
  - `Đậu`: Đậu nành, Đậu phộng (`soy`, `peanut`).
  - `Hải sản`: Tôm cua cá (`seafood`).
  - `Lactose`: Sữa bò & chế phẩm (`lactose`).

### 7.2 Đồng bộ toàn bộ Frontend sang Xanh Dương + Trắng (Medical Blue & Crisp White)
- **Toàn cục (`index.css` & `App.css`)**:
  - Chuyển toàn bộ nền `#root` và `body` từ nền tối sang nền trắng y tế `#f8fafc` cùng hiệu ứng gradient vòm xanh nhạt thanh lịch (`rgba(2, 132, 199, 0.08)`, `rgba(56, 189, 248, 0.06)`).
  - Khử bỏ hoàn toàn sự đứt gãy giao diện giữa Patient Header và TaskBoard/Pomodoro.
- **Bảng bài tập & Đồng hồ Pomodoro (`taskBoard.css`)**:
  - `.pomodoro-sidebar`: Card trắng sáng `#ffffff`, viền nhẹ `#e2e8f0`, đổ bóng mềm mại, tiêu đề chữ đậm `#0f172a`.
  - `.timer-display-wrapper`: Nền xanh nhạt `#f0f9ff`, viền `#bae6fd`, chữ số Pomodoro xanh y tế `#0284c7`.
  - `.workout-block`, `.exercise-card`: Nền trắng sáng, hiệu ứng hover xanh sky `#f0f9ff` kèm viền `#bae6fd`.
- **Cửa hàng & Trang bị (`shop.css`)**:
  - Khung xem trước Avatar và các thẻ vật phẩm chuyển sang phong cách trắng xanh đồng bộ, chữ rõ nét `#0f172a`.
- **Đội nhóm & Khám sức khỏe (`joinTeam.css`, `updateProfile.css`, `createProfile.css`)**:
  - Input form nền sáng `#f8fafc`, focus viền xanh `#0284c7`, thẻ thành viên và modal sạch sẽ, hiện đại.
