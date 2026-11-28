import React, { useState, useEffect } from 'react';
import { ShieldAlert } from 'lucide-react';
import '../style/medicalDisclaimer.css';

export const AI_HEALTH_CONSENT_KEY = 'ai_health_consent_v1';

const MedicalDisclaimerModal = ({ isOpen = true, onAccept }) => {
  const [checked, setChecked] = useState(false);

  // Chặn phím ESC để người dùng không thể bỏ qua bước xác nhận
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
      }
    };
    window.addEventListener('keydown', handleKeyDown, true);
    return () => window.removeEventListener('keydown', handleKeyDown, true);
  }, [isOpen]);

  if (!isOpen) return null;

  const handleConfirm = () => {
    if (!checked) return;
    try {
      localStorage.setItem(AI_HEALTH_CONSENT_KEY, 'true');
    } catch {
      // Ignore storage errors in restricted environments
    }
    if (onAccept) {
      onAccept();
    }
  };

  return (
    <div
      className="med-consent-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="med-consent-title"
      onClick={(e) => e.stopPropagation()}
    >
      <div className="med-consent-modal" onClick={(e) => e.stopPropagation()}>
        <div className="med-consent-header">
          <div className="med-consent-icon">
            <ShieldAlert size={22} />
          </div>
          <h3 id="med-consent-title" className="med-consent-title">
            Lưu ý về giới hạn hỗ trợ của AI
          </h3>
        </div>

        <div className="med-consent-body">
          <p>
            Các thông tin, gợi ý thực đơn và phân tích chỉ số trong mục này được hỗ trợ bởi trí tuệ nhân tạo (AI) và công thức tham khảo.
          </p>
          <p>
            Công cụ <strong>không</strong> cung cấp dịch vụ khám chữa bệnh, chẩn đoán y khoa hay thay thế cho bác sĩ hoặc chuyên gia y tế.
          </p>
        </div>

        <label className="med-consent-checkbox-label">
          <input
            type="checkbox"
            checked={checked}
            onChange={(e) => setChecked(e.target.checked)}
          />
          <span>
            Tôi hiểu đây là công cụ hỗ trợ tham khảo bằng AI, không thay thế chẩn đoán hay chỉ định của bác sĩ
          </span>
        </label>

        <div className="med-consent-actions">
          <button
            type="button"
            className="med-consent-btn"
            disabled={!checked}
            onClick={handleConfirm}
          >
            Tôi đã hiểu và tiếp tục
          </button>
        </div>
      </div>
    </div>
  );
};

export default MedicalDisclaimerModal;
