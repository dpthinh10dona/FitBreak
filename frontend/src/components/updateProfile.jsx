import { API_BASE_URL } from '../config';
import { useState, useEffect } from 'react';
import ClinicalVitalCheckup from './clinicalVitalCheckup';
import "../style/updateProfile.css";

const UpdateProfile = ({ user, onUpdateProfileSuccess }) => {
  const [formData, setFormData] = useState({
    name: user?.name || '',
    age: user?.age ? String(user.age) : '',
    gender: user?.gender !== undefined ? String(user.gender) : '',
    height: user?.height ? String(user.height) : '',
    weight: user?.weight ? String(user.weight) : '',
    goal: user?.goal || '',
    activity_frequency: user?.activity_frequency ? String(user.activity_frequency) : '',
  });

  useEffect(() => {
    if (user) {
      // Đồng bộ form khi parent nhận snapshot profile mới từ Supabase.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setFormData({
        name: user.name || '',
        age: user.age ? String(user.age) : '',
        gender: user.gender !== undefined ? String(user.gender) : '',
        height: user.height ? String(user.height) : '',
        weight: user.weight ? String(user.weight) : '',
        goal: user.goal || '',
        activity_frequency: user.activity_frequency ? String(user.activity_frequency) : '',
      });
    }
  }, [user]);

  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const validateProfile = () => {
    const age = Number(formData.age);
    const height = Number(formData.height);
    const weight = Number(formData.weight);
    const activityFrequency = Number(formData.activity_frequency);

    if (!formData.name.trim()) return 'Tên hiển thị không được để trống.';
    if (!Number.isFinite(age) || age < 12 || age > 65) {
      return 'Tuổi phải nằm trong khoảng 12 đến 65.';
    }
    if (!Number.isFinite(height) || height < 100 || height > 230) {
      return 'Chiều cao phải nằm trong khoảng 100 đến 230 cm.';
    }
    if (!Number.isFinite(weight) || weight < 30 || weight > 200) {
      return 'Cân nặng phải nằm trong khoảng 30 đến 200 kg.';
    }
    if (![1, 2, 3].includes(activityFrequency)) {
      return 'Vui lòng chọn tần suất vận động hợp lệ.';
    }

    const bmi = weight / ((height / 100) ** 2);
    if (bmi < 16) {
      return `BMI ${bmi.toFixed(1)} quá thấp (dưới 16). Vui lòng kiểm tra lại số liệu hoặc tham khảo nhân viên y tế.`;
    }
    if (bmi >= 35) {
      return `BMI ${bmi.toFixed(1)} quá cao (từ 35 trở lên). Vui lòng kiểm tra lại số liệu hoặc tham khảo nhân viên y tế.`;
    }
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    const validationError = validateProfile();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);

    const payload = {
      ...formData,
      gender: formData.gender === 'true',
      age: Number(formData.age),
      height: Number(formData.height),
      weight: Number(formData.weight),
      activity_frequency: Number(formData.activity_frequency),
    };

    try {
      const response = await fetch(`${API_BASE_URL}/profiles/update-profile`, { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!response.ok) {
        if (Array.isArray(data.detail)) {
          const messages = data.detail.map((item) => item.msg).filter(Boolean);
          throw new Error(messages.join(' ') || 'Dữ liệu nhập vào không hợp lệ!');
        }
        throw new Error(data.detail || data.message || 'Cập nhật thông tin thất bại!');
      }

      setSuccessMsg('Cập nhật hồ sơ thành công!');
      if (onUpdateProfileSuccess) {
        await onUpdateProfileSuccess(data.profile || payload);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="update-profile-profile-form-container">
      <div className="update-profile-header">
        <span className="update-profile-badge">PROFILE SETTINGS</span>
        <h2>Cập Nhật Hồ Sơ & Thể Trạng</h2>
        <p>Cập nhật số đo và tần suất hoạt động để hệ thống điều chỉnh độ khó và bài tập phù hợp</p>
      </div>

      <form onSubmit={handleSubmit} className="update-profile-profile-form">
        {error && (
          <div className="update-profile-error-box">
            <span>⚠️ {error}</span>
          </div>
        )}
        {successMsg && (
          <div className="update-profile-success-box">
            <span>✅ {successMsg}</span>
          </div>
        )}
        
        <div className="update-profile-card">
          <div className="update-profile-form-content">
            <div className="update-profile-form-column">
              <div className="update-profile-form-group">
                <label>Tên hiển thị (Display Name)</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="Nhập tên hiển thị"
                  required
                />
              </div>

              <div className="update-profile-form-group">
                <label>Tuổi (Age)</label>
                <input
                  type="number"
                  name="age"
                  value={formData.age}
                  onChange={handleInputChange}
                  placeholder="Tuổi của bạn"
                  min="12"
                  max="65"
                  required
                />
              </div>

              <div className="update-profile-form-group">
                <label>Giới tính (Gender)</label>
                <select
                  name="gender"
                  value={formData.gender}
                  onChange={handleInputChange}
                  required
                >
                  <option value="">-- Chọn giới tính --</option>
                  <option value="true">Nam</option>
                  <option value="false">Nữ</option>
                </select>
              </div>

              <div className="update-profile-form-group">
                <label>Chiều cao (cm)</label>
                <input
                  type="number"
                  name="height"
                  value={formData.height}
                  onChange={handleInputChange}
                  placeholder="Ví dụ: 175"
                  min="100"
                  max="230"
                  required
                />
              </div>
            </div>

            <div className="update-profile-form-column">
              <div className="update-profile-form-group">
                <label>Cân nặng (kg)</label>
                <input
                  type="number"
                  name="weight"
                  value={formData.weight}
                  onChange={handleInputChange}
                  placeholder="Ví dụ: 68"
                  min="30"
                  max="200"
                  step="0.1"
                  required
                />
              </div>

              <div className="update-profile-form-group">
                <label>Mục tiêu rèn luyện (Goal)</label>
                <select
                  name="goal"
                  value={formData.goal}
                  onChange={handleInputChange}
                  required
                >
                  <option value="">-- Chọn mục tiêu --</option>
                  <option value="giảm cân">Giảm cân</option>
                  <option value="cân bằng">Cân bằng</option>
                  <option value="tăng cơ">Tăng cơ</option>
                </select>
              </div>

              <div className="update-profile-form-group">
                <label>Tần suất vận động (Activity Frequency)</label>
                <select
                  name="activity_frequency"
                  value={formData.activity_frequency}
                  onChange={handleInputChange}
                  required
                >
                  <option value="">-- Chọn tần suất --</option>
                  <option value="1">Ít vận động / Lâu lâu mới vận động</option>
                  <option value="2">Vận động từ 1-4 buổi / tuần</option>
                  <option value="3">Vận động từ 5-7 buổi / tuần</option>
                </select>
              </div>
            </div>
          </div>

          <div className="update-profile-actions">
            <button type="submit" className="update-profile-save-button" disabled={loading}>
              {loading ? 'Đang lưu...' : 'Lưu Thay Đổi'}
            </button>
          </div>
        </div>
      </form>

      {/* MEDICAL CHECKUP SECTION (CLINICAL MEDTECH INTEGRATION) */}
      <ClinicalVitalCheckup 
        user={user} 
        onCheckupSuccess={() => {
          if (onUpdateProfileSuccess) {
            onUpdateProfileSuccess();
          }
        }} 
      />
    </div>
  );
};

export default UpdateProfile;
