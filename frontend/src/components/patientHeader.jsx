import React from 'react';
import LogOut from './logOut';
import CoinIcon from './CoinIcon';
import '../style/patientHeader.css';

/**
 * PatientHeader Component
 * Giao diện Header & Vitals Summary y khoa chuẩn mực (Clinical & MedTech Web Platform).
 * Đáp ứng chuẩn WCAG 2.1 AA, Mobile-First, hạn chế tải nhận thức (low cognitive load).
 */
const PatientHeader = ({
  user,
  activeTab,
  onSelectTab,
  onLogout
}) => {
  const name = user?.name || "Bệnh nhân / Người dùng";
  const email = user?.email || "Chưa cập nhật email";
  const height = user?.height || 0;
  const weight = user?.weight || 0;
  const bmi = height > 0 ? (weight / ((height / 100) ** 2)).toFixed(1) : user?.bmi || "--";
  const levelOfActivity = user?.level_of_physical_activity || "medium";
  const foodRecommendation = user?.food_recommendation;
  const coins = user?.coins || 0;

  // Đánh giá thể trạng BMI theo chuẩn WHO / Y tế Châu Á
  const getBmiStatus = (bmiVal) => {
    const val = parseFloat(bmiVal);
    if (isNaN(val)) return { text: "Chưa đo đạc", badge: "badge-primary" };
    if (val < 18.5) return { text: "Nhẹ cân (CED)", badge: "badge-warning" };
    if (val < 23.0) return { text: "Thể trạng chuẩn", badge: "badge-success" };
    if (val < 25.0) return { text: "Tiền béo phì", badge: "badge-warning" };
    return { text: "Béo phì / Cần điều chỉnh", badge: "badge-danger" };
  };

  // Cường độ vận động y tế
  const getActivityLevelLabel = (lvl) => {
    switch (lvl) {
      case 'heavy':
        return { text: 'Cường độ cao (Heavy)', badge: 'badge-primary' };
      case 'medium':
        return { text: 'Cường độ vừa (Medium)', badge: 'badge-success' };
      case 'light':
      default:
        return { text: 'Vận động nhẹ / Phục hồi (Light)', badge: 'badge-warning' };
    }
  };

  const bmiMeta = getBmiStatus(bmi);
  const activityMeta = getActivityLevelLabel(levelOfActivity);

  const navItems = [
    { id: 'tasks', label: 'Bài Tập Hằng Ngày', icon: '📋' },
    { id: 'profile', label: 'Hồ Sơ Y Tế', icon: '🩺' },
    { id: 'food', label: 'Dinh Dưỡng Lâm Sàng', icon: '🥗' },
    { id: 'schedule', label: 'Lịch Trình Vận Động', icon: '🗓️' },
    { id: 'team', label: 'Nhóm Sức Khỏe', icon: '👥' },
    { id: 'shop', label: 'Trang Bị Hỗ Trợ', icon: '🛡️' },
  ];

  return (
    <div className="patient-header-container" role="banner">
      {/* 1. TOPBAR NAVIGATION */}
      <div className="patient-header-topbar">
        <div 
          className="patient-brand" 
          onClick={() => onSelectTab('tasks')}
          role="button"
          tabIndex={0}
          aria-label="Về trang chủ FitBreak Health"
        >
          <div className="patient-brand-logo" aria-hidden="true">
            ⚕️
          </div>
          <div className="patient-brand-text">
            <h1>FitBreak</h1>
            <span>MEDTECH PLATFORM</span>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="patient-nav" aria-label="Điều hướng hệ thống">
          {navItems.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              className={`patient-nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                onSelectTab(item.id);
              }}
              aria-current={activeTab === item.id ? 'page' : undefined}
            >
              <span aria-hidden="true">{item.icon}</span>
              <span>{item.label}</span>
            </a>
          ))}
        </nav>

        {/* User Status & Log Out */}
        <div className="patient-actions">
          <div className="patient-profile-pill" title={`Điểm thưởng sức khỏe: ${coins}`}>
            <CoinIcon size={16} />
            <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#b45309' }}>
              {coins.toLocaleString()}
            </span>
          </div>

          <div className="patient-profile-pill">
            <div className="patient-avatar-circle" aria-hidden="true">
              {name.charAt(0).toUpperCase()}
            </div>
            <div className="patient-profile-info">
              <p className="patient-name">{name}</p>
              <p className="patient-status-indicator">Đã đồng bộ</p>
            </div>
          </div>

          <LogOut onLogoutSuccess={onLogout} />
        </div>
      </div>

      {/* 2. PATIENT SUMMARY & CLINICAL VITALS BANNER (Chỉ hiển thị tại tab Hồ Sơ Y Tế) */}
      {activeTab === 'profile' && (
      <div className="patient-vitals-banner">
        <div className="patient-banner-card">
          {/* Header Row of Banner */}
          <div className="patient-banner-header">
            <div className="patient-meta-group">
              <div className="patient-big-avatar" aria-hidden="true">
                🧑‍⚕️
              </div>
              <div className="patient-meta-text">
                <h2>Hồ Sơ Sức Khỏe: {name}</h2>
                <p>Mã tài khoản: {email} | Phân loại thể trạng: <strong>{bmiMeta.text}</strong></p>
              </div>
            </div>

            <div className="patient-badge-row">
              <span className={`clinical-badge ${bmiMeta.badge}`}>
                BMI: {bmi} kg/m²
              </span>
              <span className={`clinical-badge ${activityMeta.badge}`}>
                {activityMeta.text}
              </span>
            </div>
          </div>

          {/* Vitals Quick Cards Grid */}
          <div className="patient-vitals-grid">
            {/* Card 1: BMI */}
            <div className="vital-card">
              <div className="vital-card-top">
                <span className="vital-title">Thể trạng (BMI)</span>
                <span className="vital-icon" style={{ backgroundColor: '#e0f2fe', color: '#0369a1' }}>⚖️</span>
              </div>
              <div className="vital-value-row">
                <span className="vital-value">{bmi}</span>
                <span className="vital-unit">kg/m²</span>
              </div>
              <div className="vital-evaluation" style={{ color: bmiMeta.badge === 'badge-success' ? '#10b981' : '#f59e0b' }}>
                ● {bmiMeta.text}
              </div>
            </div>

            {/* Card 2: Cân nặng & Chiều cao */}
            <div className="vital-card">
              <div className="vital-card-top">
                <span className="vital-title">Chỉ số hình thể</span>
                <span className="vital-icon" style={{ backgroundColor: '#f0fdf4', color: '#15803d' }}>📏</span>
              </div>
              <div className="vital-value-row">
                <span className="vital-value">{weight || '--'}</span>
                <span className="vital-unit">kg / {height || '--'} cm</span>
              </div>
              <div className="vital-evaluation" style={{ color: '#64748b' }}>
                Đo đạc kiểm tra định kỳ
              </div>
            </div>

            {/* Card 3: Nhu cầu Năng Lượng / TDEE */}
            <div className="vital-card">
              <div className="vital-card-top">
                <span className="vital-title">Năng lượng mục tiêu (TDEE)</span>
                <span className="vital-icon" style={{ backgroundColor: '#fff7ed', color: '#c2410c' }}>🔥</span>
              </div>
              <div className="vital-value-row">
                <span className="vital-value">{user?.calories_need || user?.tdee || '2,000'}</span>
                <span className="vital-unit">kcal/ngày</span>
              </div>
              <div className="vital-evaluation" style={{ color: '#0284c7' }}>
                Protein: <strong>{user?.protein_need || user?.protein || '75'}g</strong>
              </div>
            </div>

            {/* Card 4: Chế độ Vận động */}
            <div className="vital-card">
              <div className="vital-card-top">
                <span className="vital-title">Cường độ khuyến nghị</span>
                <span className="vital-icon" style={{ backgroundColor: '#fdf2f8', color: '#be185d' }}>🏋️</span>
              </div>
              <div className="vital-value-row">
                <span className="vital-value" style={{ textTransform: 'capitalize' }}>
                  {levelOfActivity}
                </span>
              </div>
              <div className="vital-evaluation" style={{ color: '#64748b' }}>
                Đồng bộ cùng lịch tập AI
              </div>
            </div>
          </div>

          {/* Card 5: Lời khuyên y khoa cá nhân hóa (nếu có từ medical_checkup hoặc chatbot) */}
          {foodRecommendation && (
            <div className="patient-diet-notice">
              <span className="diet-notice-icon">🩺</span>
              <div className="diet-notice-content">
                <h4>Chỉ dẫn y tế & Lời khuyên dinh dưỡng lâm sàng:</h4>
                <p>{foodRecommendation}</p>
              </div>
            </div>
          )}
        </div>
      </div>
      )}
    </div>
  );
};

export default PatientHeader;
