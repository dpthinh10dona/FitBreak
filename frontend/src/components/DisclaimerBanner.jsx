import React from 'react';
import { AlertTriangle } from 'lucide-react';
import '../style/medicalDisclaimer.css';

const DisclaimerBanner = ({
  sticky = true,
  text = 'Thông tin chỉ mang tính tham khảo do AI hỗ trợ, không thay thế chẩn đoán hay tư vấn y tế chuyên nghiệp.',
  className = '',
}) => {
  return (
    <div
      className={`med-disclaimer-banner ${sticky ? 'is-sticky' : ''} ${className}`.trim()}
      role="note"
      aria-label="Cảnh báo tham khảo"
    >
      <AlertTriangle size={16} className="med-disclaimer-banner-icon" />
      <p className="med-disclaimer-banner-text">{text}</p>
    </div>
  );
};

export default DisclaimerBanner;
