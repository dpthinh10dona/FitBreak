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

  const [medicalData, setMedicalData] = useState({
    sys: '',
    dia: '',
    glycemic_index: '',
    time: 0, // 0: Lúc đói, 1: Trước bữa ăn, 2: Ngẫu nhiên
    spo2_index: '',
  });

  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [loading, setLoading] = useState(false);

  const [medicalResult, setMedicalResult] = useState(null);
  const [medicalLoading, setMedicalLoading] = useState(false);
  const [medicalError, setMedicalError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleMedicalInputChange = (e) => {
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
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
          throw new Error(data.detail[0].msg || 'Dữ liệu nhập vào không hợp lệ!');
        }
        throw new Error(data.detail || data.message || 'Cập nhật thông tin thất bại!');
      }

      setSuccessMsg('Cập nhật hồ sơ thành công!');
      onUpdateProfileSuccess(payload);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMedicalCheckup = async () => {
    setMedicalError(null);
    setMedicalLoading(true);

    const payload = {
      weight: formData.weight ? Number(formData.weight) : null,
      height: formData.height ? Number(formData.height) : null,
      sys: medicalData.sys ? Number(medicalData.sys) : null,
      dia: medicalData.dia ? Number(medicalData.dia) : null,
      time: medicalData.glycemic_index ? Number(medicalData.time) : null,
      glycemic_index: medicalData.glycemic_index ? Number(medicalData.glycemic_index) : null,
      spo2_index: medicalData.spo2_index ? Number(medicalData.spo2_index) : null,
    };

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
        throw new Error(data.detail || 'Không thể phân tích chỉ số y tế');
      }

      setMedicalResult(data.result);
    } catch (err) {
      setMedicalError(err.message);
    } finally {
      setMedicalLoading(false);
    }
  };

  const getBadgeClass = (level) => {
    switch (level) {
      case 'good': return 'med-badge-good';
      case 'warning': return 'med-badge-warning';
      case 'danger': return 'med-badge-danger';
      case 'critical': return 'med-badge-critical';
      default: return '';
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
        onCheckupSuccess={(result) => {
          if (onUpdateProfileSuccess) {
            onUpdateProfileSuccess();
          }
        }} 
      />
    </div>
  );
};

export default UpdateProfile;
