import {
  AlertTriangle,
  ShieldAlert,
  Database,
  RefreshCw,
  Info,
  CheckCircle2,
  Stethoscope,
  SlidersHorizontal,
} from 'lucide-react';
import '../style/safetyGuardrail.css';

/**
 * SafetyGuardrailAlert Component
 * Hiển thị thông báo chặn an toàn y tế và dữ liệu từ hệ thống Guardrail của FitBreak.
 *
 * @param {Object} props.data Dữ liệu kết quả Guardrail nhận từ FastAPI
 * @param {Function} props.onReset Hàm callback khi người dùng bấm nút thiết lập lại form
 */
const SafetyGuardrailAlert = ({ data, onReset }) => {
  if (!data || data.allow_ai_generation) {
    return null;
  }

  const {
    status = 'MEDICAL_WARNING',
    bmi = null,
    bmi_category = '',
    reasons = [],
    suggestion = '',
    disclaimer = 'FitBreak chỉ cung cấp thông tin tham khảo cho người khỏe mạnh 12–24 tuổi, không thay thế chẩn đoán y khoa.',
  } = data;

  const isMedicalWarning = status === 'MEDICAL_WARNING';

  // Cấu hình nội dung theo trạng thái
  const config = isMedicalWarning
    ? {
        containerClass: 'safety-alert-medical',
        title: 'Cảnh Báo An Toàn Y Tế (Chặn Kê Đơn Tự Động)',
        subtitle: 'Hệ thống đã tạm dừng tạo thực đơn / lịch tập AI do phát hiện yếu tố nguy cơ sức khỏe.',
        badgeText: 'Medical Warning',
        badgeClass: 'badge-medical',
        iconBg: 'safety-icon-medical',
        titleClass: 'safety-title-medical',
        icon: <ShieldAlert className="safety-icon" />,
        actionBtnText: 'Cập nhật lại thông tin sức khỏe',
        actionBtnClass: 'btn-medical',
        actionIcon: <Stethoscope className="safety-action-icon" />,
        suggestionBg: 'suggestion-medical',
      }
    : {
        containerClass: 'safety-alert-insufficient',
        title: 'Chưa Đủ Căn Cứ Dữ Liệu An Toàn',
        subtitle: 'Dữ liệu thực phẩm hoặc bài tập sau bộ lọc chưa đủ tiêu chuẩn tối thiểu để sinh kế hoạch.',
        badgeText: 'Insufficient Data',
        badgeClass: 'badge-insufficient',
        iconBg: 'safety-icon-insufficient',
        titleClass: 'safety-title-insufficient',
        icon: <Database className="safety-icon" />,
        actionBtnText: 'Điều chỉnh tiêu chí & Ngân sách',
        actionBtnClass: 'btn-insufficient',
        actionIcon: <SlidersHorizontal className="safety-action-icon" />,
        suggestionBg: 'suggestion-insufficient',
      };

  return (
    <div
      role="alert"
      className={`safety-alert-container ${config.containerClass}`}
    >
      {/* 1. Header Row */}
      <div className="safety-alert-header">
        <div className="safety-alert-title-group">
          <div className={`safety-icon-wrapper ${config.iconBg}`}>
            {config.icon}
          </div>
          <div className="safety-title-text">
            <h3 className={config.titleClass}>
              {config.title}
            </h3>
            <p>{config.subtitle}</p>
          </div>
        </div>
        <span className={`safety-status-badge ${config.badgeClass}`}>
          {config.badgeText}
        </span>
      </div>

      {/* 2. Chỉ số BMI (nếu có) */}
      {typeof bmi === 'number' && bmi > 0 && (
        <div className="safety-bmi-ribbon">
          <div className="safety-bmi-left">
            <span className="safety-bmi-label">
              Chỉ số khối cơ thể (BMI):
            </span>
            <span className="safety-bmi-val">
              {bmi.toFixed(1)}
            </span>
          </div>
          {bmi_category && (
            <span className="safety-bmi-cat">
              Thể trạng: {bmi_category}
            </span>
          )}
        </div>
      )}

      {/* 3. Danh sách lý do bị chặn (Reasons List) */}
      {reasons && reasons.length > 0 && (
        <div className="safety-reasons-card">
          <div className="safety-reasons-heading">
            <AlertTriangle className="safety-heading-icon" />
            Lý do hệ thống kích hoạt cơ chế bảo vệ:
          </div>
          <ul className="safety-reasons-list">
            {reasons.map((reason, idx) => (
              <li key={idx} className="safety-reason-item">
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 4. Khuyến nghị khắc phục (Suggestion Box) */}
      {suggestion && (
        <div className={`safety-suggestion-card ${config.suggestionBg}`}>
          <CheckCircle2 className="safety-suggestion-icon" />
          <div className="safety-suggestion-text">
            <strong>Hướng xử lý đề xuất: </strong>
            {suggestion}
          </div>
        </div>
      )}

      {/* 5. Cảnh báo y tế luật pháp mặc định (Medical Disclaimer) */}
      {disclaimer && (
        <div className="safety-disclaimer-box">
          <Info className="safety-disclaimer-icon" />
          <p className="safety-disclaimer-text">
            {disclaimer}
          </p>
        </div>
      )}

      {/* 6. Nút Thao tác quay lại (Action Button) */}
      <div className="safety-alert-actions">
        <button
          type="button"
          onClick={onReset}
          className={`btn-safety-reset ${config.actionBtnClass}`}
        >
          {config.actionIcon}
          <span>{config.actionBtnText}</span>
          <RefreshCw className="safety-refresh-icon" />
        </button>
      </div>
    </div>
  );
};

export default SafetyGuardrailAlert;
