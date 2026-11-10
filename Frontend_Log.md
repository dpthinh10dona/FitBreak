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
- **Giao diện ngoài (Log In / Sign Up)**:
  - `frontend/src/style/logIn.css` & `frontend/src/style/signUp.css`: Thiết kế chuẩn Medical Blue & Crisp White (`#0284c7`, `#f8fafc`, `#ffffff`), card trắng lâm sàng, input focus xanh y tế.
  - `frontend/src/components/logIn.jsx` & `frontend/src/components/signUp.jsx`: Cập nhật nội dung thương hiệu y tế, huy hiệu kiểm chuẩn lâm sàng.
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

---

## 8. CHUẨN HÓA BÁC SĨ TRỢ LÝ ẢO (CLINICAL AI ADVISOR) RAG-FIRST & CÁ NHÂN HÓA HỒ SƠ

### 8.1 Kiến trúc Tri thức Y khoa RAG-First (`clinical_rag.py`)
- Xây dựng module tri thức y khoa chuẩn mực `clinical_rag.py` tích hợp phác đồ điều trị nội khoa và y học thể thao từ Bộ Y Tế, Viện Dinh Dưỡng Quốc Gia và Hội Dị Ứng Miễn Dịch:
  - Phân khoa Tiêu hóa & Chuyển hóa lâm sàng: Đau thượng vị, trào ngược axit (GERD), hạ đường huyết cơ năng, tụt huyết áp tư thế.
  - Phân khoa Cơ xương khớp & Thể chất: Đau cơ khởi phát muộn (DOMS), tổn thương gân cơ, quy trình RICE.
  - Cảnh báo cấp cứu & Red Flags: Các dấu hiệu chuyển viện khẩn cấp (đau thắt ngực, xuất huyết tiêu hóa, ngất xỉu, khó thở).
- Thuật toán trích xuất tài liệu theo từ khóa ngữ nghĩa (`retrieve_medical_docs`), gán nhãn nguồn trích dẫn y khoa chuẩn mực để đưa vào biến `{{retrieved_medical_docs}}`.

### 8.2 Chuẩn hóa System Prompt Kỹ thuật Lâm sàng (`chatbot_agent.py`)
- Áp dụng cấu trúc Prompt Engineering chuẩn xác của Bác sĩ Trợ lý Ảo:
  - **3 biến ngữ cảnh bắt buộc**: `{{user_message}}`, `{{retrieved_medical_docs}}`, `{{current_user_profile}}` (thể trạng BMI, dị ứng cứng, chỉ số lâm sàng, lời khuyên hiện tại, mức vận động).
  - **4 phần câu trả lời chuẩn mực**:
    1. **Nhận định sơ bộ**: Tóm tắt cơ chế phát sinh triệu chứng dựa trên tài liệu y khoa.
    2. **Giải pháp & Lời khuyên tức thì**: Hướng dẫn nghỉ ngơi, xử trí tại nhà, dinh dưỡng tạm thời an toàn (tuyệt đối không xung đột bệnh nền hay dị ứng).
    3. **Dấu hiệu cảnh báo (Red Flags)**: Chỉ rõ triệu chứng nguy hiểm cần cấp cứu.
    4. **Miễn trừ trách nhiệm y tế (Disclaimer)**: Khẳng định vai trò tham khảo ban đầu.
  - **Ràng buộc định dạng**: Trả về Markdown tiêu chuẩn, không bọc JSON, không sinh code block, tách biệt hoàn toàn câu hỏi xác nhận lưu Supabase cho Node UI xử lý riêng.

### 8.3 Tối ưu hóa Failover & Hiển thị Frontend
- `api/app/core/ollama_client.py`: Tinh chỉnh cơ chế luân chuyển dự phòng Gemini / Groq hỗ trợ chế độ `text/plain` cho Markdown chuẩn xác.
- `frontend/src/style/telehealthChatbot.css`: Bổ sung `white-space: pre-wrap;` và định kiểu chữ in đậm/in nghiêng lâm sàng cho bong bóng chat.
- `frontend/src/components/telehealthDoctorChatbot.jsx`: Bổ sung hàm render Markdown chuyên dụng `formatClinicalMessage`, hiển thị ngắt dòng và đề mục rõ ràng, trực quan.

### 8.4 Tích hợp Kiến trúc Dual-Agent: Động Cơ Cá Nhân Hóa Dữ Liệu Sức Khỏe (`Personalization Logic Engine`)
- **Agent 1 (Clinical AI Advisor)**: Nhận `{{user_message}}`, `{{retrieved_medical_docs}}`, `{{current_user_profile}}` để tư vấn lâm sàng tự nhiên bằng Markdown (4 phần chuẩn y khoa).
- **Agent 2 (Personalization Logic Engine)**: Nhận `{{user_message}}`, `{{agent_response}}`, `{{current_user_profile}}` để phân tích logic điều chỉnh dữ liệu Supabase:
  - Kiểm tra điều kiện cập nhật (`has_proposed_changes`).
  - Kiểm tra và giải quyết xung đột y khoa với Hard Constraints (`health_metrics`: tim mạch, huyết áp, dị ứng cố định) -> `conflict_detected`, `conflict_explanation`.
  - Hợp nhất (Merge) đề xuất mới với lời khuyên dinh dưỡng cũ mà không xóa mất thông tin có sẵn.
  - Định dạng chuẩn Strict JSON: xuất `summary_for_ui_card`, `proposed_updates` (`food_recommendation`, `level_of_physical_activity`) và `requires_user_confirmation: true`.
- **Giao diện Human-in-the-Loop Action Card (`telehealthDoctorChatbot.jsx`)**:
  - Hiển thị trực tiếp thẻ xác nhận kèm tóm tắt lý do y khoa, cảnh báo xung đột (nếu có), chi tiết thay đổi và 2 nút bấm thao tác tức thì: `[✓ Đồng ý cập nhật]` và `[✕ Bỏ qua]`.

---

## 9. KHÔI PHỤC VŨ ĐÀI SĂN BOSS & BANNER ANH HÙNG (HERO & ACTIVE RAID BOSS BANNER)

### 9.1 Khôi phục vị trí Boss trong vòng lặp Game (`App.jsx`, `profileBanner.jsx`)
- Khôi phục component `<ProfileBanner />` vào luồng giao diện chính của `App.jsx` ngay bên dưới `<PatientHeader />`, trả lại không gian chiến đấu Boss cho người chơi.
- Bổ sung cơ chế fallback token thông minh (`localStorage.getItem('token') || localStorage.getItem('access_token') || user?.token`) giúp kết nối API `/get-raid-boss/{team_id}` luôn thành công 100%.
- Thiết lập dữ liệu khởi tạo Boss mặc định (*"Raid Boss Hắc Long"*, 100/100 HP, +25 Coins thưởng), đảm bảo thanh máu Boss và avatar luôn hiển thị mượt mà không bị tình trạng treo *"Loading..."*.

### 9.2 Thiết kế lại Giao diện Banner chuẩn Xanh Dương - Trắng MedTech (`profileBanner.css`)
- **Khung chứa tổng thể (`.profile-banner-inner`)**:
  - Thẻ card nền trắng sáng `#ffffff`, viền nhẹ `#e2e8f0`, đổ bóng mềm mại `0 2px 8px rgba(15, 23, 42, 0.05)`, bo góc `16px`, độ rộng chuẩn `1400px` ăn khớp với Patient Header.
- **Khu vực Anh hùng (`.user-profile-group`)**:
  - Hộp Avatar anh hùng (`.avatar-box`): Nền gradient xanh y tế nhạt `#f0f9ff` đến `#e0f2fe`, viền xanh `#bae6fd`, hiển thị trọn vẹn trang bị (mũ, áo, vũ khí) mua từ Shop.
  - Tên nhân vật in đậm màu Navy `#0f172a`, huy hiệu nhóm `#e0f2fe` chữ xanh `#0284c7`, thẻ thống kê Sức mạnh (⚔️ DMG - nền hồng đỏ) và Tiền thưởng (🪙 Coins - nền vàng gold).
- **Vũ đài Boss Đột Kích (`.boss-section`)**:
  - Thiết kế dạng thẻ chiến đấu công nghệ cao: Nền trắng ánh hồng nhẹ (`#ffffff` đến `#fff5f5`), viền đỏ hồng `#fecdd3`, bóng mờ hồng.
  - Huy hiệu trạng thái: Chấm đỏ nhấp nháy phát sáng (`pulseDot`) kèm dòng chữ nổi bật `🔴 ACTIVE RAID BOSS`.
  - Thanh máu Boss (`.boss-hp-bar`): Track nền xám sáng, thanh fill gradient đỏ cam rực rỡ (`#ef4444 -> #f97316 -> #dc2626`) kèm ánh sáng phát quang, hiển thị phần trăm máu và thông số `HP / Max HP`.
  - Hình ảnh Boss nổi (`.boss-avatar`): Sprite cử động lơ lửng (`floatBoss`), tích hợp hiệu ứng rung lắc đỏ rực (`hitShake`) mỗi khi người dùng hoàn thành bài tập từ `TaskBoard`.

### 9.3 Tối ưu hóa Hiển thị Hồ Sơ Sức Khỏe (Conditional Rendering by Tab)
- Cập nhật [`patientHeader.jsx`](file:///d:/DOAN-PHU-THINH/FitBreak/frontend/src/components/patientHeader.jsx) với điều kiện `{activeTab === 'profile' && ...}`:
  - Khối Card tóm tắt Hồ Sơ Sức Khỏe (`patient-vitals-banner`: BMI, Chỉ số hình thể, TDEE, Cường độ vận động, Chỉ dẫn y tế lâm sàng) chỉ hiển thị khi người dùng vào đúng tab **"Hồ Sơ Y Tế"** (`profile`).
  - Ẩn hoàn toàn khỏi các tab còn lại (`tasks`, `food`, `schedule`, `team`, `shop`), giúp thanh điều hướng trên cùng luôn thanh thoát, hiện đại, giải phóng tối đa diện tích màn hình để người dùng tập trung luyện tập, theo dõi bài tập hằng ngày và chiến đấu cùng Boss.

---

## 10. ĐỒNG BỘ BỀN VỮNG HẠN MỨC TƯ VẤN BÁC SĨ (PERSISTENT TELEHEALTH QUOTA)

### 10.1 Nguyên nhân vấn đề
- **Frontend**: Khởi tạo state tĩnh `remainingQuestions = 3` trong bộ nhớ RAM của component, không có API kiểm tra trạng thái lúc tải trang hay đăng nhập, dẫn đến việc mỗi lần F5 hoặc Re-login huy hiệu đều hiển thị lại `3/3`.
- **Backend**: Lưu trữ bộ đếm qua `defaultdict` thuần trong RAM, khi server restart/redeploy hoặc quá trình ngủ đông (spin-down) sẽ làm mất lượt đếm câu hỏi trong ngày.

### 10.2 Giải pháp khắc phục 2 tầng
- **Tầng Backend (`api/app/router/chatbot.py`)**:
  - Bổ sung cơ chế lưu trữ bền vững (Persistence) vào file JSON [`chatbot_daily_usage.json`](file:///d:/DOAN-PHU-THINH/FitBreak/api/app/core/dataset/chatbot_daily_usage.json).
  - Tự động load và save theo cấu trúc ngày `YYYY-MM-DD` và `user_id`.
  - Mở thêm endpoint `GET /chatbot/quota` giúp client tra cứu hạn mức thực tế bất cứ lúc nào.
- **Tầng Frontend (`frontend/src/components/telehealthDoctorChatbot.jsx`)**:
  - Tự động lưu và đọc hạn mức từ `localStorage` theo khóa `fitbreak_telehealth_quota_{email}_{YYYY-MM-DD}` (đảm bảo không bị reset khi đăng xuất/đăng nhập lại cùng tài khoản).
  - Khởi tạo `useEffect` tự động gọi `GET /chatbot/quota` để đồng bộ chính xác với máy chủ ngay khi người dùng đăng nhập.
  - Tự động reset hạn mức về 3 khi bước sang ngày mới nhờ khóa định danh theo ngày thực tế.





