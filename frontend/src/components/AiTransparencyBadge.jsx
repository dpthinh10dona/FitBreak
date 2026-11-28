import React from 'react';
import { Sparkles, Calculator } from 'lucide-react';
import '../style/medicalDisclaimer.css';

export const AiTransparencyBadge = ({ className = '' }) => {
  return (
    <span className={`ai-transparency-badge ${className}`.trim()}>
      <Sparkles size={12} />
      <span>[Do AI tổng hợp - Chỉ mang tính tham khảo]</span>
    </span>
  );
};

export const DeterministicBadge = ({
  label = 'Tính toán theo công thức chuẩn / Bộ lọc dữ liệu',
  className = '',
}) => {
  return (
    <span className={`deterministic-source-badge ${className}`.trim()}>
      <Calculator size={12} />
      <span>{label}</span>
    </span>
  );
};

export default AiTransparencyBadge;
