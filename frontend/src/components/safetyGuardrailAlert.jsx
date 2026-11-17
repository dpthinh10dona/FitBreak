import React from 'react';
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
        containerClass: 'safety-alert-medical border border-rose-200 bg-rose-50/70',
        title: 'Cảnh Báo An Toàn Y Tế (Chặn Kê Đơn Tự Động)',
        subtitle: 'Hệ thống đã tạm dừng tạo thực đơn / lịch tập AI do phát hiện yếu tố nguy cơ sức khỏe.',
        badgeText: 'Medical Warning',
        badgeClass: 'badge-medical bg-rose-100 text-rose-700 border-rose-200',
        iconBg: 'safety-icon-medical bg-rose-100 text-rose-600',
        titleClass: 'safety-title-medical text-rose-900',
        icon: <ShieldAlert className="w-6 h-6 text-rose-600" />,
        actionBtnText: 'Cập nhật lại thông tin sức khỏe',
        actionBtnClass: 'btn-medical bg-rose-600 hover:bg-rose-700 text-white',
        actionIcon: <Stethoscope className="w-4 h-4" />,
        suggestionBg: 'suggestion-medical bg-pink-50 border-pink-200 text-pink-900',
      }
    : {
        containerClass: 'safety-alert-insufficient border border-amber-200 bg-amber-50/70',
        title: 'Chưa Đủ Căn Cứ Dữ Liệu An Toàn',
        subtitle: 'Dữ liệu thực phẩm hoặc bài tập sau bộ lọc chưa đủ tiêu chuẩn tối thiểu để sinh kế hoạch.',
        badgeText: 'Insufficient Data',
        badgeClass: 'badge-insufficient bg-amber-100 text-amber-800 border-amber-200',
        iconBg: 'safety-icon-insufficient bg-amber-100 text-amber-700',
        titleClass: 'safety-title-insufficient text-amber-950',
        icon: <Database className="w-6 h-6 text-amber-600" />,
        actionBtnText: 'Điều chỉnh tiêu chí & Ngân sách',
        actionBtnClass: 'btn-insufficient bg-amber-600 hover:bg-amber-700 text-white',
        actionIcon: <SlidersHorizontal className="w-4 h-4" />,
        suggestionBg: 'suggestion-insufficient bg-orange-50 border-orange-200 text-orange-950',
      };

  return (
    <div
      role="alert"
      className={`safety-alert-container ${config.containerClass} transition-all duration-200`}
    >
      {/* 1. Header Row */}
      <div className="safety-alert-header flex items-start justify-between gap-4 mb-4">
        <div className="safety-alert-title-group flex items-center gap-3">
          <div className={`safety-icon-wrapper ${config.iconBg} p-2 rounded-xl`}>
            {config.icon}
          </div>
          <div className="safety-title-text">
            <h3 className={`text-lg font-bold tracking-tight ${config.titleClass}`}>
              {config.title}
            </h3>
            <p className="text-sm text-slate-500 mt-0.5">{config.subtitle}</p>
          </div>
        </div>
        <span className={`safety-status-badge text-xs font-bold px-2.5 py-1 rounded-full border ${config.badgeClass}`}>
          {config.badgeText}
        </span>
      </div>

      {/* 2. Chỉ số BMI (nếu có) */}
      {typeof bmi === 'number' && bmi > 0 && (
        <div className="safety-bmi-ribbon flex items-center justify-between bg-white border border-slate-100 rounded-lg px-4 py-2.5 mb-4">
          <div className="safety-bmi-left flex items-baseline gap-2">
            <span className="safety-bmi-label text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Chỉ số khối cơ thể (BMI):
            </span>
            <span className="safety-bmi-val text-xl font-extrabold text-slate-900">
              {bmi.toFixed(1)}
            </span>
          </div>
          {bmi_category && (
            <span className="safety-bmi-cat text-xs font-bold px-2.5 py-1 rounded-md bg-slate-100 text-slate-700">
              Thể trạng: {bmi_category}
            </span>
          )}
        </div>
      )}

      {/* 3. Danh sách lý do bị chặn (Reasons List) */}
      {reasons && reasons.length > 0 && (
        <div className="safety-reasons-card bg-white border border-slate-100 rounded-lg p-4 mb-4 shadow-sm">
          <div className="safety-reasons-heading flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            Lý do hệ thống kích hoạt cơ chế bảo vệ:
          </div>
          <ul className="safety-reasons-list list-disc list-inside space-y-1.5 pl-1 m-0 text-slate-800 text-sm">
            {reasons.map((reason, idx) => (
              <li key={idx} className="safety-reason-item leading-relaxed">
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 4. Khuyến nghị khắc phục (Suggestion Box) */}
      {suggestion && (
        <div className={`safety-suggestion-card flex items-start gap-3 rounded-lg p-3.5 mb-4 border ${config.suggestionBg}`}>
          <CheckCircle2 className="w-5 h-5 mt-0.5 shrink-0 opacity-80" />
          <div className="safety-suggestion-text text-sm leading-relaxed">
            <strong className="font-bold">Hướng xử lý đề xuất: </strong>
            {suggestion}
          </div>
        </div>
      )}

      {/* 5. Cảnh báo y tế luật pháp mặc định (Medical Disclaimer) */}
      {disclaimer && (
        <div className="safety-disclaimer-box flex items-start gap-2.5 p-3 rounded-lg bg-slate-100/70 border border-slate-200 mb-5">
          <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
          <p className="safety-disclaimer-text text-xs text-slate-500 leading-normal m-0">
            {disclaimer}
          </p>
        </div>
      )}

      {/* 6. Nút Thao tác quay lại (Action Button) */}
      <div className="safety-alert-actions flex justify-end">
        <button
          type="button"
          onClick={onReset}
          className={`btn-safety-reset inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold shadow-sm transition-all duration-150 cursor-pointer ${config.actionBtnClass}`}
        >
          {config.actionIcon}
          <span>{config.actionBtnText}</span>
          <RefreshCw className="w-3.5 h-3.5 opacity-70 ml-1" />
        </button>
      </div>
    </div>
  );
};

export default SafetyGuardrailAlert;
