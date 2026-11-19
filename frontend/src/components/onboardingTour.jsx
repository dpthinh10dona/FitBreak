import React, { useState, useEffect } from 'react';
import { 
  UserCheck, 
  Calendar, 
  Utensils, 
  Users, 
  ShoppingBag, 
  ArrowRight, 
  ArrowLeft, 
  CheckCircle2, 
  X, 
  Sparkles,
  HelpCircle,
  Activity,
  Flame,
  Award
} from 'lucide-react';
import '../style/onboardingTour.css';

const STEPS = [
  {
    step: 0,
    tab: 'tasks',
    title: 'Chào mừng đến với FitBreak!',
    subtitle: 'Nền tảng Quản lý Sức khỏe & Luyện tập Gamification',
    badge: 'Tổng quan trang bìa',
    icon: Sparkles,
    content: (
      <div className="tour-step-content">
        <p className="tour-lead-text">
          FitBreak kết hợp giữa <strong>phục hồi thể chất y khoa</strong> và <strong>gamification chiến đấu Raid Boss</strong>. Dưới đây là cách bạn làm quen với trang bìa:
        </p>
        <div className="tour-grid-cards">
          <div className="tour-info-card">
            <div className="tour-card-icon"><Activity size={20} /></div>
            <div>
              <div className="tour-card-title">Thanh Header & Chỉ số Vitals</div>
              <div className="tour-card-desc">Quan sát BMI, thể trạng, phân loại hoạt động và lượng Coins đã tích lũy ở trên cùng.</div>
            </div>
          </div>
          <div className="tour-info-card">
            <div className="tour-card-icon"><Flame size={20} /></div>
            <div>
              <div className="tour-card-title">Banner Nhân vật & Boss Raid</div>
              <div className="tour-card-desc">Hiển thị máu Boss, cấp độ nhân vật và sát thương. Hoàn thành bài tập để gây damage và nhận thưởng coin!</div>
            </div>
          </div>
          <div className="tour-info-card">
            <div className="tour-card-icon"><Award size={20} /></div>
            <div>
              <div className="tour-card-title">Bảng Vận Động & Pomodoro</div>
              <div className="tour-card-desc">Đồng hồ đếm giờ làm việc - nghỉ ngơi kèm danh sách bài tập vận động giãn cơ hôm nay.</div>
            </div>
          </div>
        </div>
      </div>
    ),
    instruction: 'Hãy cùng xem quy trình 5 bước để bắt đầu lộ trình của bạn nhé!'
  },
  {
    step: 1,
    tab: 'profile',
    title: 'Bước 1: Thiết lập Hồ sơ Sức khỏe',
    subtitle: 'Cung cấp chỉ số sinh trắc học để cá nhân hóa',
    badge: 'Bước 1 / 5',
    icon: UserCheck,
    content: (
      <div className="tour-step-content">
        <p className="tour-lead-text">
          Để hệ thống và AI tính toán chính xác nhu cầu năng lượng (TDEE, Calo, Protein) cũng như lọc bài tập an toàn:
        </p>
        <ul className="tour-checklist">
          <li><strong>Chiều cao & Cân nặng:</strong> Hệ thống tự động tính chỉ số BMI theo chuẩn WHO.</li>
          <li><strong>Mục tiêu:</strong> Chọn Giảm cân, Tăng cơ hoặc Duy trì sức khỏe.</li>
          <li><strong>Tình trạng sức khỏe / Bệnh lý nền:</strong> Tick chọn các vấn đề như tim mạch, dạ dày, đau khớp gối để AI lọc bài tập và thực đơn phù hợp.</li>
        </ul>
      </div>
    ),
    instruction: 'Bấm "Chuyển đến Hồ sơ" để đi đến màn hình nhập thông tin cá nhân.'
  },
  {
    step: 2,
    tab: 'schedule',
    title: 'Bước 2: Lập Lịch Trình Vận Động',
    subtitle: 'Sắp xếp thời gian biểu tập luyện trong tuần',
    badge: 'Bước 2 / 5',
    icon: Calendar,
    content: (
      <div className="tour-step-content">
        <p className="tour-lead-text">
          Phần <strong>Lịch Trình Vận Động</strong> giúp bạn phân bổ thời gian rảnh để tập luyện mà không ảnh hưởng học tập/công việc:
        </p>
        <ul className="tour-checklist">
          <li><strong>Chọn khung giờ rảnh:</strong> Chọn các khung 30 phút trong tuần bạn có thể vận động.</li>
          <li><strong>Sinh lịch tập AI:</strong> Hệ thống phân bổ các bài tập trị liệu, cardio hoặc giãn cơ phù hợp với mức thể lực.</li>
          <li><strong>Lưu ý y tế (Limitation):</strong> Xem các chống chỉ định cho từng bài tập ở cột bên phải.</li>
        </ul>
      </div>
    ),
    instruction: 'Bấm "Tiếp tục" để xem trang Lập Lịch Trình Vận Động.'
  },
  {
    step: 3,
    tab: 'food',
    title: 'Bước 3: Gợi Ý Thực Đơn Dinh Dưỡng',
    subtitle: 'Thực đơn chuẩn lâm sàng, vừa ngân sách & calo',
    badge: 'Bước 3 / 5',
    icon: Utensils,
    content: (
      <div className="tour-step-content">
        <p className="tour-lead-text">
          Phần <strong>Dinh Dưỡng Lâm Sàng</strong> thiết lập thực đơn 3 bữa ăn mỗi ngày cho bạn:
        </p>
        <ul className="tour-checklist">
          <li><strong>Ngân sách & Dị ứng:</strong> Nhập số tiền chi cho ăn uống mỗi ngày và tick chọn các thực phẩm gây dị ứng.</li>
          <li><strong>Phân tích Y khoa:</strong> AI diễn giải lý do phối hợp món ăn, calo và protein.</li>
          <li><strong>Trích dẫn nguồn & Hạn chế:</strong> Xem nguồn tài liệu dinh dưỡng và các lưu ý món ăn ngay dưới từng món.</li>
        </ul>
      </div>
    ),
    instruction: 'Bấm "Tiếp tục" để chuyển sang phần Đội nhóm rèn luyện.'
  },
  {
    step: 4,
    tab: 'team',
    title: 'Bước 4: Tham Gia Nhóm Rèn Luyện',
    subtitle: 'Sát cánh cùng đồng đội đánh Boss Raid',
    badge: 'Bước 4 / 5',
    icon: Users,
    content: (
      <div className="tour-step-content">
        <p className="tour-lead-text">
          Tập luyện một mình dễ nản? Hãy gia nhập biệt đội:
        </p>
        <ul className="tour-checklist">
          <li><strong>Tham gia hoặc tạo Team:</strong> Kết nối cùng bạn bè và đồng nghiệp qua mã nhóm.</li>
          <li><strong>Đánh Boss chung:</strong> Mỗi bài tập bạn hoàn thành sẽ trừ máu trực tiếp của Raid Boss cho cả đội.</li>
          <li><strong>Bảng xếp hạng:</strong> Vinh danh những thành viên chăm chỉ và cống hiến nhiều nhất.</li>
        </ul>
      </div>
    ),
    instruction: 'Bấm "Tiếp tục" để khám phá Cửa hàng vật phẩm.'
  },
  {
    step: 5,
    tab: 'shop',
    title: 'Bước 5: Cửa Hàng Vật Phẩm & Phần Thưởng',
    subtitle: 'Đổi coin lấy trang bị và phụ kiện Avatar',
    badge: 'Bước 5 / 5',
    icon: ShoppingBag,
    content: (
      <div className="tour-step-content">
        <p className="tour-lead-text">
          Mỗi khi hoàn thành nhiệm vụ Pomodoro, bài tập hoặc hạ Boss, bạn nhận được <strong>Coins</strong>:
        </p>
        <ul className="tour-checklist">
          <li><strong>Trang bị độc quyền:</strong> Mũ, giáp, vũ khí giúp tăng chỉ số sức mạnh (STR / Damage).</li>
          <li><strong>Tùy biến Avatar:</strong> Nâng cấp ngoại hình nhân vật chiến binh của bạn.</li>
          <li><strong>Động lực duy trì:</strong> Biến việc rèn luyện sức khỏe mỗi ngày thành trò chơi nhập vai thú vị.</li>
        </ul>
      </div>
    ),
    instruction: 'Tuyệt vời! Bạn đã nắm rõ toàn bộ lộ trình FitBreak. Bấm "Hoàn tất" để bắt đầu trải nghiệm!'
  }
];

export default function OnboardingTour({ isOpen, onClose, onNavigateTab, activeTab }) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    if (isOpen) {
      // Khi mở tour, chuyển về step tương ứng
      const stepData = STEPS[currentStepIndex];
      if (stepData && onNavigateTab) {
        onNavigateTab(stepData.tab);
      }
    }
  }, [currentStepIndex, isOpen]);

  if (!isOpen) return null;

  const currentStep = STEPS[currentStepIndex];
  const StepIcon = currentStep.icon;
  const isFirst = currentStepIndex === 0;
  const isLast = currentStepIndex === STEPS.length - 1;

  const handleNext = () => {
    if (!isLast) {
      const nextIndex = currentStepIndex + 1;
      setCurrentStepIndex(nextIndex);
      if (onNavigateTab) {
        onNavigateTab(STEPS[nextIndex].tab);
      }
    } else {
      handleFinish();
    }
  };

  const handlePrev = () => {
    if (!isFirst) {
      const prevIndex = currentStepIndex - 1;
      setCurrentStepIndex(prevIndex);
      if (onNavigateTab) {
        onNavigateTab(STEPS[prevIndex].tab);
      }
    }
  };

  const handleJumpToStep = (index) => {
    setCurrentStepIndex(index);
    if (onNavigateTab) {
      onNavigateTab(STEPS[index].tab);
    }
  };

  const handleFinish = () => {
    localStorage.setItem('fitbreak_tour_completed', 'true');
    if (onClose) onClose();
  };

  return (
    <div className="onboarding-tour-overlay" role="dialog" aria-modal="true">
      <div className="onboarding-tour-card">
        {/* Header */}
        <div className="onboarding-tour-header">
          <div className="tour-badge-wrapper">
            <span className="tour-step-pill">{currentStep.badge}</span>
            <span className="tour-tab-indicator">Tab đang xem: <strong>{currentStep.tab.toUpperCase()}</strong></span>
          </div>
          <button 
            type="button" 
            className="tour-close-btn" 
            onClick={handleFinish}
            aria-label="Đóng hướng dẫn"
          >
            <X size={18} />
          </button>
        </div>

        {/* Title area */}
        <div className="onboarding-tour-title-area">
          <div className="tour-icon-box">
            <StepIcon size={26} />
          </div>
          <div>
            <h2 className="tour-main-title">{currentStep.title}</h2>
            <p className="tour-subtitle">{currentStep.subtitle}</p>
          </div>
        </div>

        {/* Step Indicator Progress Bar */}
        <div className="tour-progress-bar-container">
          <div className="tour-steps-dots">
            {STEPS.map((s, idx) => (
              <button
                key={s.step}
                type="button"
                className={`tour-dot-btn ${idx === currentStepIndex ? 'active' : ''} ${idx < currentStepIndex ? 'completed' : ''}`}
                onClick={() => handleJumpToStep(idx)}
                title={s.title}
              >
                {idx < currentStepIndex ? <CheckCircle2 size={12} /> : idx}
              </button>
            ))}
          </div>
          <div className="tour-progress-line">
            <div 
              className="tour-progress-fill" 
              style={{ width: `${(currentStepIndex / (STEPS.length - 1)) * 100}%` }}
            />
          </div>
        </div>

        {/* Body content */}
        <div className="onboarding-tour-body">
          {currentStep.content}
          
          <div className="tour-instruction-alert">
            <div className="tour-alert-icon"><HelpCircle size={18} /></div>
            <div className="tour-alert-text">{currentStep.instruction}</div>
          </div>
        </div>

        {/* Footer actions */}
        <div className="onboarding-tour-footer">
          <button 
            type="button" 
            className="tour-btn tour-btn-secondary" 
            onClick={handlePrev}
            disabled={isFirst}
          >
            <ArrowLeft size={16} /> Quay lại
          </button>

          <div className="tour-footer-right">
            <button 
              type="button" 
              className="tour-btn tour-btn-ghost" 
              onClick={handleFinish}
            >
              Bỏ qua hướng dẫn
            </button>
            <button 
              type="button" 
              className="tour-btn tour-btn-primary" 
              onClick={handleNext}
            >
              {isLast ? (
                <>Hoàn tất & Bắt đầu <CheckCircle2 size={16} /></>
              ) : (
                <>Tiếp theo <ArrowRight size={16} /></>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
