import { API_BASE_URL } from '../config';
import { useState } from 'react';
import "../style/logIn.css";

const LogIn = ({ onLoginSuccess, onGoToSignUp }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { id, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [id]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/login`, { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        if (Array.isArray(data.detail)) {
          throw new Error(data.detail[0].msg || 'Dữ liệu nhập vào không hợp lệ!');
        }
        throw new Error(data.detail || data.message || 'Đăng nhập thất bại!');
      }

      onLoginSuccess(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-fitbreak-login-page">
      <div className="login-fitbreak-content-wrapper">
        <div className="login-fitbreak-logo-section">
          <div className="login-badge-hero">
            <span>🛡️</span>
            <span>NỀN TẢNG Y TẾ & PHỤC HỒI THỂ LỰC</span>
          </div>
          <h1 className="login-fitbreak-logo">
            FitBreak <span className="login-logo-accent">Health</span>
          </h1>
          <p className="login-hero-tagline">
            Giải pháp theo dõi chỉ số sinh hiệu, lịch trình vận động thể chất khoa học và hỗ trợ dinh dưỡng chuẩn y khoa được cá nhân hóa bởi AI.
          </p>
          <div className="login-features-list">
            <div className="feature-item">
              <span className="feature-icon">🩺</span>
              <span>Theo dõi chỉ số sinh hiệu (BMI, Huyết áp, SpO2, Đường huyết)</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🥗</span>
              <span>Đề xuất thực đơn dinh dưỡng lâm sàng theo bệnh lý</span>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🤖</span>
              <span>Bác sĩ AI Telehealth tư vấn trực tuyến 24/7</span>
            </div>
          </div>
        </div>

        <div className="login-form-container">
          <div className="login-form-header">
            <h2>Đăng Nhập Hệ Thống</h2>
            <p>Truy cập hồ sơ y tế và tiếp tục lộ trình chăm sóc sức khỏe của bạn</p>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            {error && <div className="login-error-alert">⚠️ {error}</div>}
            
            <div className="login-form-group">
              <label htmlFor="email" className="login-form-label">Email tài khoản</label>
              <input 
                type="email" 
                id="email" 
                className="login-form-input" 
                placeholder="bacsi_hoac_benhnhan@example.com"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>

            <div className="login-form-group">
              <label htmlFor="password" className="login-form-label">Mật khẩu</label>
              <input 
                type="password" 
                id="password" 
                className="login-form-input" 
                placeholder="••••••••"
                value={formData.password}
                onChange={handleChange}
                required
              />
            </div>
            
            <div className="login-form-actions">
              <button type="submit" className="login-submit-btn" disabled={loading}>
                {loading ? 'Đang xác thực bảo mật...' : 'Đăng Nhập'}
              </button>
              
              <div className="login-divider-row">
                <span className="divider-line"></span>
                <span className="divider-text">Chưa có hồ sơ?</span>
                <span className="divider-line"></span>
              </div>

              <button type="button" className="login-switch-btn" onClick={onGoToSignUp}>
                Đăng ký tài khoản mới
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default LogIn;
