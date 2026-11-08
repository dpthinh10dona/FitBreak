import React, { useState } from 'react';
import { API_BASE_URL } from '../config';
import '../style/clinicalCheckup.css';

/**
 * ClinicalVitalCheckup Component (MedTech Standard)
 * Bảng nhập liệu và đánh giá chỉ số sinh tồn (Vital Signs Form): Huyết áp, Đường huyết, SpO2.
 * Trực quan hóa kết quả phân tích y khoa, ngưỡng rủi ro, và cá nhân hóa cấp độ vận động/dinh dưỡng.
 */
const ClinicalVitalCheckup = ({ user, onCheckupSuccess }) => {
  const [medicalData, setMedicalData] = useState({
    sys: '',
    dia: '',
    glycemic_index: '',
    time: 0, // 0: Lúc đói, 1: Trước bữa ăn, 2: Ngẫu nhiên
    spo2_index: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [medicalResult, setMedicalResult] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setMedicalData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleTimeSelect = (val) => {
    setMedicalData((prev) => ({
      ...prev,
      time: val,
    }));
  };

  const handleAnalyze = async () => {
    setError(null);

    const hasBp = medicalData.sys !== '' || medicalData.dia !== '';
    const hasGlucose = medicalData.glycemic_index !== '';
    const hasSpo2 = medicalData.spo2_index !== '';

    if (!hasBp && !hasGlucose && !hasSpo2) {
      setError('Vui lòng nhập ít nhất 1 chỉ số y tế (Huyết áp, Đường huyết, hoặc SpO2) để tiến hành phân tích lâm sàng.');
      return;
    }

    setLoading(true);

    const payload = {};
    if (medicalData.sys !== '') payload.sys = Number(medicalData.sys);
    if (medicalData.dia !== '') payload.dia = Number(medicalData.dia);
    if (medicalData.glycemic_index !== '') payload.glycemic_index = Number(medicalData.glycemic_index);
    if (hasGlucose) payload.time = Number(medicalData.time);
    if (medicalData.spo2_index !== '') payload.spo2_index = Number(medicalData.spo2_index);

    try {
      const response = await fetch(`${API_BASE_URL}/profiles/medical-checkup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Phân tích y tế thất bại!');
      }

      setMedicalResult(data);
      if (onCheckupSuccess) {
        onCheckupSuccess(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getMetricClass = (level) => {
    if (level === 0 || level === 'normal') return { box: 'level-normal', badge: 'badge-normal' };
    if (level === 1 || level === 'warning') return { box: 'level-warning', badge: 'badge-warning' };
    return { box: 'level-danger', badge: 'badge-danger' };
  };

  return (
    <div className="clinical-checkup-container">
      {/* 1. INPUT FORM CARD */}
      <div className="clinical-checkup-card">
        <div className="clinical-card-header">
          <h3>
            <span role="img" aria-label="medical checkup">🩺</span>
            Kiểm Tra Sức Khỏe & Đo Lường Chỉ Số Sinh Tồn (Vital Signs)
          </h3>
          <p>
            Nhập các chỉ số đo đạc từ thiết bị y tế cá nhân tại nhà để hệ thống Bác sĩ AI phân loại thể trạng, đánh giá rủi ro và tự động cá nhân hóa lộ trình tập luyện & dinh dưỡng.
          </p>
        </div>

        {error && (
          <div style={{
            backgroundColor: 'var(--med-danger-bg)',
            border: '1px solid var(--med-danger-border)',
            color: 'var(--med-danger)',
            padding: '12px 16px',
            borderRadius: 'var(--med-radius-sm)',
            fontSize: '0.88rem',
            marginBottom: '20px',
            fontWeight: 600
          }}>
            ⚠️ {error}
          </div>
        )}

        <div className="clinical-devices-stack">
          {/* DEVICE 1: BLOOD PRESSURE */}
          <div className="clinical-device-block">
            <div className="device-intro">
              <div className="device-icon-clinical">💓</div>
              <div className="device-text-meta">
                <h4>Máy đo Huyết áp Điện tử</h4>
                <span>Đo huyết áp tâm thu (SYS) và tâm trương (DIA) (Đơn vị: mmHg)</span>
              </div>
            </div>
            <div className="clinical-grid-inputs">
              <div className="clinical-field-group">
                <label htmlFor="sys-input">Huyết áp tâm thu (SYS - Chỉ số tối đa)</label>
                <div className="clinical-input-wrapper">
                  <input
                    id="sys-input"
                    type="number"
                    name="sys"
                    value={medicalData.sys}
                    onChange={handleInputChange}
                    placeholder="120"
                    className="clinical-input"
                  />
                  <span className="input-suffix">mmHg</span>
                </div>
              </div>
              <div className="clinical-field-group">
                <label htmlFor="dia-input">Huyết áp tâm trương (DIA - Chỉ số tối thiểu)</label>
                <div className="clinical-input-wrapper">
                  <input
                    id="dia-input"
                    type="number"
                    name="dia"
                    value={medicalData.dia}
                    onChange={handleInputChange}
                    placeholder="80"
                    className="clinical-input"
                  />
                  <span className="input-suffix">mmHg</span>
                </div>
              </div>
            </div>
          </div>

          {/* DEVICE 2: GLUCOSE */}
          <div className="clinical-device-block">
            <div className="device-intro">
              <div className="device-icon-clinical">🩸</div>
              <div className="device-text-meta">
                <h4>Máy đo Nồng độ Đường huyết</h4>
                <span>Kiểm tra glucose máu mao mạch kèm thời điểm đo đạc (Đơn vị: mg/dL)</span>
              </div>
            </div>
            <div className="clinical-grid-inputs">
              <div className="clinical-field-group">
                <label htmlFor="glucose-input">Nồng độ Glucose trong máu</label>
                <div className="clinical-input-wrapper">
                  <input
                    id="glucose-input"
                    type="number"
                    name="glycemic_index"
                    value={medicalData.glycemic_index}
                    onChange={handleInputChange}
                    placeholder="95"
                    className="clinical-input"
                  />
                  <span className="input-suffix">mg/dL</span>
                </div>
              </div>
              <div className="clinical-field-group">
                <label>Thời điểm tiến hành đo</label>
                <div className="timing-chips-grid">
                  {[
                    { val: 0, label: "Lúc đói (≥ 8h)" },
                    { val: 1, label: "Trước bữa ăn" },
                    { val: 2, label: "Ngẫu nhiên" },
                  ].map((item) => (
                    <button
                      key={item.val}
                      type="button"
                      className={`timing-chip ${medicalData.time === item.val ? 'active' : ''}`}
                      onClick={() => handleTimeSelect(item.val)}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* DEVICE 3: SpO2 */}
          <div className="clinical-device-block">
            <div className="device-intro">
              <div className="device-icon-clinical">💨</div>
              <div className="device-text-meta">
                <h4>Máy đo Nồng độ Oxy trong máu (SpO2)</h4>
                <span>Đo độ bão hòa oxy trong máu qua đầu ngón tay (Đơn vị: %)</span>
              </div>
            </div>
            <div className="clinical-grid-inputs" style={{ gridTemplateColumns: 'minmax(240px, 360px)' }}>
              <div className="clinical-field-group">
                <label htmlFor="spo2-input">Chỉ số bão hòa SpO2 (%)</label>
                <div className="clinical-input-wrapper">
                  <input
                    id="spo2-input"
                    type="number"
                    name="spo2_index"
                    value={medicalData.spo2_index}
                    onChange={handleInputChange}
                    placeholder="98"
                    className="clinical-input"
                  />
                  <span className="input-suffix">%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="clinical-action-bar">
          <button
            type="button"
            className="btn-clinical-analyze"
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? 'Đang phân tích dữ liệu lâm sàng...' : '⚕️ Phân Tích & Đánh Giá Y Tế Lâm Sàng'}
          </button>
        </div>
      </div>

      {/* 2. RESULTS & DIAGNOSTIC CARD */}
      {medicalResult && (
        <div className="clinical-results-panel" aria-live="polite">
          <div className="results-header-clinical">
            <h4>
              <span>📊</span>
              Báo Cáo Phân Tích Rủi Ro Lâm Sàng & Đề Xuất Phục Hồi
            </h4>
            <p>Hệ thống tự động đồng bộ kết quả này vào hồ sơ cá nhân của bạn trên Supabase.</p>
          </div>

          <div className="clinical-status-grid">
            {/* BMI Card */}
            {medicalResult.details?.bmi && (
              <div className={`metric-status-box ${getMetricClass(medicalResult.details.bmi.level).box}`}>
                <div className="metric-top-row">
                  <span className="metric-name">Thể trạng (BMI)</span>
                  <span className={`metric-badge-clinical ${getMetricClass(medicalResult.details.bmi.level).badge}`}>
                    {medicalResult.details.bmi.status}
                  </span>
                </div>
                <div className="metric-value-huge">{medicalResult.details.bmi.value} <span style={{ fontSize: '0.9rem', color: '#64748b' }}>kg/m²</span></div>
                <p className="metric-risk-comment">{medicalResult.details.bmi.risk}</p>
              </div>
            )}

            {/* Blood Pressure Card */}
            {medicalResult.details?.blood_pressure && (
              <div className={`metric-status-box ${getMetricClass(medicalResult.details.blood_pressure.level).box}`}>
                <div className="metric-top-row">
                  <span className="metric-name">Huyết áp</span>
                  <span className={`metric-badge-clinical ${getMetricClass(medicalResult.details.blood_pressure.level).badge}`}>
                    {medicalResult.details.blood_pressure.status}
                  </span>
                </div>
                <div className="metric-value-huge">
                  {medicalResult.details.blood_pressure.sys} / {medicalResult.details.blood_pressure.dia}
                  <span style={{ fontSize: '0.9rem', color: '#64748b' }}> mmHg</span>
                </div>
                <p className="metric-risk-comment">{medicalResult.details.blood_pressure.risk}</p>
              </div>
            )}

            {/* Diabetes Card */}
            {medicalResult.details?.diabete && (
              <div className={`metric-status-box ${getMetricClass(medicalResult.details.diabete.level).box}`}>
                <div className="metric-top-row">
                  <span className="metric-name">Đường huyết</span>
                  <span className={`metric-badge-clinical ${getMetricClass(medicalResult.details.diabete.level).badge}`}>
                    {medicalResult.details.diabete.status}
                  </span>
                </div>
                <div className="metric-value-huge">
                  {medicalResult.details.diabete.value}
                  <span style={{ fontSize: '0.9rem', color: '#64748b' }}> mg/dL</span>
                </div>
                <p className="metric-risk-comment">{medicalResult.details.diabete.risk}</p>
              </div>
            )}

            {/* SpO2 Card */}
            {medicalResult.details?.spo2 && (
              <div className={`metric-status-box ${getMetricClass(medicalResult.details.spo2.level).box}`}>
                <div className="metric-top-row">
                  <span className="metric-name">Nồng độ SpO2</span>
                  <span className={`metric-badge-clinical ${getMetricClass(medicalResult.details.spo2.level).badge}`}>
                    {medicalResult.details.spo2.status}
                  </span>
                </div>
                <div className="metric-value-huge">
                  {medicalResult.details.spo2.value}
                  <span style={{ fontSize: '0.9rem', color: '#64748b' }}> %</span>
                </div>
                <p className="metric-risk-comment">{medicalResult.details.spo2.risk}</p>
              </div>
            )}
          </div>

          {/* Advice Section */}
          <div className="clinical-advice-columns">
            {medicalResult.recommendations?.workout_advice?.length > 0 && (
              <div className="clinical-advice-card workout">
                <h5>🏋️ Chỉ dẫn Vận động & Phục hồi Thể lực</h5>
                <ul>
                  {medicalResult.recommendations.workout_advice.map((adv, idx) => (
                    <li key={idx}>{adv}</li>
                  ))}
                </ul>
              </div>
            )}

            {medicalResult.recommendations?.diet_advice?.length > 0 && (
              <div className="clinical-advice-card diet">
                <h5>🥗 Chỉ dẫn Dinh dưỡng Lâm sàng</h5>
                <ul>
                  {medicalResult.recommendations.diet_advice.map((adv, idx) => (
                    <li key={idx}>{adv}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ClinicalVitalCheckup;
