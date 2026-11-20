# FITBREAK FRONTEND REDESIGN & INTERACTIVE ONBOARDING TOUR LOG
Date: 2026-11-19
Status: COMPLETED (First Draft Released & Verified)
Author: Senior Frontend Developer

---

## 1. MỤC TIÊU & THAY ĐỔI TRỌNG TÂM (CORE REQUIREMENTS)
- **Loại bỏ form popup gò bó khi vừa đăng nhập/đăng ký**: Thay vì ép người dùng điền thông tin ngay từ đầu một cách đột ngột, hệ thống chuyển sang quy trình **Interactive Onboarding Tour (Website Guided Tour)** dẫn dắt người dùng qua từng trang một cách trực quan, rõ ràng và mượt mà.
- **Tự động kích hoạt khi mới vào**: Nếu người dùng lần đầu vào app (hoặc vừa đăng ký), hệ thống sẽ bật modal Tour dẫn dắt từ trang này sang trang khác.
- **Có nút mở lại bất cứ lúc nào**: Bổ sung nút **"Hướng dẫn"** (`.patient-tour-pill-btn`) ngay cạnh avatar trên Header để người dùng có thể xem lại lộ trình bất cứ khi nào cần.
- **Thay đổi Tab theo từng bước (Interactive Tour Navigation)**: Khi người dùng bấm "Tiếp tục" qua từng bước, ứng dụng tự động switch tab tương ứng dưới nền để người dùng nhìn thấy trực tiếp giao diện thực tế.

---

## 2. CHI TIẾT CÁC BƯỚC HƯỚNG DẪN (5-STEP TOUR WORKFLOW)

### Tổng quan trang bìa (Bước 0 - Overview)
- **Mục tiêu**: Giới thiệu giao diện FitBreak kết hợp giữa **phục hồi thể chất y khoa** và **gamification chiến đấu Raid Boss**.
- **Cách xem**:
  1. **Thanh Header & Vitals**: Hiển thị chỉ số thể trạng BMI, cấp độ hoạt động và số dư Coins tích lũy.
  2. **Banner Nhân vật & Boss Raid**: Trực quan hóa thanh máu Boss (Raid Boss Hắc Long), cấp độ và sát thương chiến đấu của nhân vật.
  3. **Bảng Vận Động & Pomodoro**: Đồng hồ đếm giờ làm việc - nghỉ giải lao cùng danh sách bài tập giãn cơ hôm nay.

### Bước 1: Thiết lập Hồ sơ Sức khỏe (`tab: profile`)
- **Tự động chuyển tab**: Hệ thống chuyển người dùng sang tab **"Hồ Sơ Y Tế"** (`activeTab: profile`).
- **Nội dung hướng dẫn**:
  - Hướng dẫn nhập chiều cao, cân nặng để tính BMI chuẩn WHO.
  - Chọn mục tiêu: Giảm cân, Tăng cơ hoặc Duy trì sức khỏe.
  - Tick chọn tình trạng sức khỏe / bệnh lý nền để AI tự động lọc thực đơn và bài tập an toàn.

### Bước 2: Lập Lịch Trình Vận Động (`tab: schedule`)
- **Tự động chuyển tab**: Hệ thống chuyển người dùng sang tab **"Lịch Trình Vận Động"** (`activeTab: schedule`).
- **Nội dung hướng dẫn**:
  - Hướng dẫn chọn các khung giờ rảnh 30 phút trong tuần.
  - Bấm sinh lịch tập AI để sắp xếp các bài tập phục hồi chức năng và cardio.
  - Quan sát cột **Chú ý Y tế & Hạn chế vận động (Limitation Type)** ở ô bên phải để nắm rõ chống chỉ định.

### Bước 3: Gợi Ý Thực Đơn Dinh Dưỡng (`tab: food`)
- **Tự động chuyển tab**: Chuyển sang tab **"Dinh Dưỡng Lâm Sàng"** (`activeTab: food`).
- **Nội dung hướng dẫn**:
  - Nhập ngân sách ăn uống trong ngày và chọn dị ứng thực phẩm.
  - Nhận thực đơn 3 bữa sáng - trưa - tối tính toán calo và protein chi tiết.
  - Đọc phần Phân tích Y khoa và nguồn trích dẫn dữ liệu ở dưới mỗi món.

### Bước 4: Tham Gia Nhóm Rèn Luyện (`tab: team`)
- **Tự động chuyển tab**: Chuyển sang tab **"Nhóm Rèn Luyện"** (`activeTab: team`).
- **Nội dung hướng dẫn**:
  - Hướng dẫn tạo hoặc nhập mã tham gia nhóm cùng bạn bè.
  - Đánh Boss tập thể: Mỗi lần tập xong trừ máu trực tiếp cho Boss của cả đội.
  - Theo dõi bảng xếp hạng cống hiến.

### Bước 5: Cửa Hàng Vật Phẩm & Phần Thưởng (`tab: shop`)
- **Tự động chuyển tab**: Chuyển sang tab **"Vật Phẩm Hỗ Trợ"** (`activeTab: shop`).
- **Nội dung hướng dẫn**:
  - Dùng Coins nhận được từ việc tập luyện và đánh Boss để mua trang phục, vũ khí.
  - Tăng chỉ số sức mạnh nhân vật (Damage/STR) và thay đổi ngoại hình Avatar.

---

## 3. CÁC FILE ĐƯỢC TẠO VÀ CẬP NHẬT

1. **`frontend/src/components/onboardingTour.jsx` (MỚI)**:
   - Quản lý state 6 bước (0 -> 5).
   - Sync realtime với `activeTab` thông qua prop `onNavigateTab(tabId)`.
   - Có thanh tiến trình (progress bar + step dots) cho phép click nhảy trực tiếp tới bước bất kỳ.
   - Lưu trạng thái hoàn tất vào `localStorage.setItem('fitbreak_tour_completed', 'true')`.

2. **`frontend/src/style/onboardingTour.css` (MỚI)**:
   - Thiết kế theo chuẩn **MedTech Clinical Theme (Anti-AI Slop)**.
   - Nền backdrop blur mờ ảo nhẹ (`rgba(15, 23, 42, 0.65)`), hairline borders `1px solid #e2e8f0`, màu nhấn `Clinical Blue #0284c7`.
   - Nút điều hướng rõ ràng: Quay lại, Tiếp theo, Bỏ qua, Hoàn tất & Bắt đầu.

3. **`frontend/src/components/patientHeader.jsx` & `frontend/src/style/patientHeader.css`**:
   - Thêm nút **"Hướng dẫn"** (`.patient-tour-pill-btn`) kèm icon `HelpCircle` để người dùng có thể mở lại tour bất cứ khi nào muốn.

4. **`frontend/src/components/signUp.jsx` & `frontend/src/style/signUp.css`**:
   - Đồng bộ hoàn toàn 100% giao diện và nội dung cột trái (Hero Banner, Badge `🛡️ NỀN TẢNG Y TẾ & PHỤC HỒI THỂ LỰC`, Logo `FitBreak Health`, Tagline, 3 thẻ tính năng nổi bật) với trang Đăng nhập (`logIn.jsx`).
   - Chuẩn hóa layout container `max-width: 1080px`, khoảng cách `gap: 64px`, font typography, card form 440px và hairline borders đồng nhất.

5. **`frontend/src/App.jsx`**:
   - Thay thế việc ép bật popup tạo profile ngay khi vào bằng việc kích hoạt `OnboardingTour` nếu người dùng chưa hoàn thành tour.
   - Tích hợp state `showOnboardingTour` và hàm điều hướng tab.

---

## 4. KIỂM THỬ XUẤT CODE (BUILD VERIFICATION)
- Đã chạy lệnh build:
  ```bash
  cd frontend && npx vite build --emptyOutDir=false
  ```
- Kết quả: **Thành công 100% (0 errors, 0 warnings)**, Vite đóng gói sạch sẽ toàn bộ modules và assets (`dist/assets/index-DuNIYiXQ.css` và `dist/assets/index-D4BRes6h.js`).
