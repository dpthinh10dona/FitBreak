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
            <span>🛡️</span>
            <span>NỀN TẢNG Y TẾ & PHỤC HỒI THỂ LỰC</span>
          </div>
          <h1 className="signup-fitbreak-logo">
            FitBreak <span className="signup-logo-accent">Health</span>
          </h1>
          <p className="signup-hero-tagline">
            Giải pháp theo dõi chỉ số sinh hiệu, lịch trình vận động thể chất khoa học và hỗ trợ dinh dưỡng chuẩn y khoa được cá nhân hóa bởi AI.
          </p>
          <div className="signup-features-list">
            <div className="signup-feature-item">
              <span className="signup-feature-icon">🩺</span>
              <span>Theo dõi chỉ số sinh hiệu (BMI, Huyết áp, SpO2, Đường huyết)</span>
            </div>
            <div className="signup-feature-item">
              <span className="signup-feature-icon">🥗</span>
              <span>Gợi ý thực đơn tham khảo theo mục tiêu cá nhân</span>
            </div>
            <div className="signup-feature-item">
              <span className="signup-feature-icon">🤖</span>
              <span>Trợ lý tra cứu thông tin sức khỏe hỗ trợ 24/7</span>
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
              <label htmlFor="password" className="signup-form-label">Mật khẩu (ít nhất 8 ký tự)</label>
              <input 
                type="password" 
                id="password" 
                className="signup-form-input" 
                placeholder="••••••••"
                value={formData.password}
                onChange={handleChange}
                minLength="8"
                maxLength="256"
                autoComplete="new-password"
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
