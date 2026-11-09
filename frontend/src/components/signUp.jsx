import { API_BASE_URL } from '../config';
import { useState } from 'react';
import "../style/signUp.css";

const SignUp = ({ onSignUpSuccess, onGoToLogIn }) => {
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
      const response = await fetch(`${API_BASE_URL}/register`, { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        if (Array.isArray(data.detail)) {
          throw new Error(data.detail[0].msg || 'Dữ liệu nhập vào không hợp lệ!');
        }
        throw new Error(data.detail || data.message || 'Đăng ký thất bại!');
      }

      onSignUpSuccess(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="signup-fitbreak-signup-page">
      <div className="signup-fitbreak-content-wrapper">
        <div className="signup-fitbreak-logo-section">
          <div className="signup-badge-hero">
            <span>🩺</span>
            <span>KHỞI TẠO HỒ SƠ Y TẾ FITBREAK</span>
          </div>
          <h1 className="signup-fitbreak-logo">
            FitBreak <span className="signup-logo-accent">MedTech</span>
          </h1>
          <p className="signup-hero-tagline">
            Đăng ký để xây dựng lộ trình phục hồi thể chất, giám sát chỉ số sinh hiệu và nhận chế độ dinh dưỡng tối ưu từ chuyên gia y tế.
          </p>
          <div className="signup-features-list">
            <div className="signup-feature-item">
              <span className="signup-feature-icon">📊</span>
              <span>Đo lường tự động chỉ số BMI & TDEE khoa học</span>
            </div>
            <div className="signup-feature-item">
              <span className="signup-feature-icon">📅</span>
              <span>Lịch trình vận động phục hồi 7 ngày thông minh</span>
            </div>
            <div className="signup-feature-item">
              <span className="signup-feature-icon">🔒</span>
              <span>Bảo mật dữ liệu sức khỏe chuẩn tiêu chuẩn lâm sàng</span>
            </div>
          </div>
        </div>

        <div className="signup-form-container">
          <div className="signup-form-header">
            <h2>Tạo Tài Khoản Mới</h2>
            <p>Bắt đầu hành trình nâng cao và bảo vệ sức khỏe toàn diện ngay hôm nay</p>
          </div>

          <form className="signup-form" onSubmit={handleSubmit}>
            {error && <div className="signup-error-alert">⚠️ {error}</div>}
            
            <div className="signup-form-group">
              <label htmlFor="email" className="signup-form-label">Email đăng ký</label>
              <input 
                type="email" 
                id="email" 
                className="signup-form-input" 
                placeholder="tennguoidung@example.com"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>

            <div className="signup-form-group">
              <label htmlFor="password" className="signup-form-label">Mật khẩu (Tối thiểu 6 ký tự)</label>
              <input 
                type="password" 
                id="password" 
                className="signup-form-input" 
                placeholder="••••••••"
                value={formData.password}
                onChange={handleChange}
                required
              />
            </div>
            
            <div className="signup-form-actions">
              <button type="submit" className="signup-submit-btn" disabled={loading}>
                {loading ? 'Đang tạo hồ sơ...' : 'Đăng Ký Tài Khoản'}
              </button>
              
              <div className="signup-divider-row">
                <span className="divider-line"></span>
                <span className="divider-text">Đã có tài khoản?</span>
                <span className="divider-line"></span>
              </div>

              <button type="button" className="signup-switch-btn" onClick={onGoToLogIn}>
                Đăng nhập ngay
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default SignUp;
