import { API_BASE_URL } from '../config';
import { useState, useEffect } from 'react';
import '../style/clinicalDiet.css';

/**
 * ClinicalNutritionModule Component (MedTech Standards)
 * Thiết kế giao diện tư vấn dinh dưỡng y khoa chuyên sâu:
 * - Đồng bộ với hồ sơ sinh tồn (TDEE, Protein, Lời khuyên bệnh lý).
 * - Kiểm soát ngân sách, lọc kiêng cữ dị ứng y khoa nghiêm ngặt.
 * - Trực quan hóa 3 bữa ăn (Sáng, Trưa, Tối) với thanh Macro vi chất, hệ số khẩu phần và phân tích lâm sàng từ AI.
 */
const ClinicalNutritionModule = () => {
  const [formData, setFormData] = useState({
    calories_need: '',
    protein_need: '',
    daily_budget: '120000',
    aim: 'Duy trì',
    diet_type: 'Không kiêng',
    allergen: ''
  });

  const [profile, setProfile] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        const userObj = JSON.parse(localStorage.getItem('user') || '{}');
        const email = userObj?.email;

        let data = null;
        if (email) {
          const res = await fetch(`${API_BASE_URL}/profiles/get-profile-by-email/${email}`, {
            headers: { 'Authorization': `Bearer ${token}` },
          });
          if (res.ok) {
            data = await res.json();
          }
        }

        if (data) {
          setProfile(data);
          let mappedGoal = 'Duy trì';
          if (data.goal) {
            const goalLower = data.goal.toLowerCase();
            if (goalLower.includes('tăng cơ')) mappedGoal = 'Tăng cơ';
            else if (goalLower.includes('giảm cân')) mappedGoal = 'Giảm cân';
            else if (goalLower.includes('duy trì') || goalLower.includes('cân bằng')) mappedGoal = 'Duy trì';
          }

          setFormData((prev) => ({
            ...prev,
            calories_need: String(data.tdee || data.calories_need || 2000),
            protein_need: String(data.protein || data.protein_need || 75),
            aim: mappedGoal
          }));
        }
      } catch (err) {
        console.error("Lỗi khi tải profile:", err);
      }
    };

    fetchUserProfile();
  }, []);

  const allergenOptions = [
    { id: 'đậu', label: 'Đậu (Đậu nành, Đậu phộng)', icon: '🥜' },
    { id: 'hải sản', label: 'Hải sản (Tôm, Cua, Cá)', icon: '🦐' },
    { id: 'lactose', label: 'Lactose (Sữa bò, Phô mai)', icon: '🥛' },
  ];

  const handleAllergenToggle = (id) => {
    const current = formData.allergen ? formData.allergen.split(';') : [];
    let updated;
    if (current.includes(id)) {
      updated = current.filter(item => item !== id);
    } else {
      updated = [...current, id];
    }
    setFormData(prev => ({ ...prev, allergen: updated.join(';') }));
  };

  const handleBudgetPreset = (amount) => {
    setFormData(prev => ({ ...prev, daily_budget: amount }));
  };

  const handleSubmit = async (e, isRefresh = false) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);

    const budgetNum = Number(formData.daily_budget);
    if (!budgetNum || budgetNum <= 0) {
      setError('Vui lòng cung cấp ngân sách dinh dưỡng hợp lệ mỗi ngày.');
      setLoading(false);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const payload = {
        calories_need: Number(formData.calories_need || profile?.tdee || 2000),
        protein_need: Number(formData.protein_need || profile?.protein || 75),
        daily_budget: budgetNum,
        aim: formData.aim || 'Duy trì',
        diet_type: formData.diet_type || 'Không kiêng',
        allergen: formData.allergen || null,
        food_recommendation: profile?.food_recommendation || null,
      };

      if (isRefresh && resultData?.meals) {
        payload.exclude_dishes = resultData.meals.map(m => {
          let name = m.name || m.dish_name || '';
          return name.replace(/\s*\(x[\d\.]+\s*phần\)/i, '').trim();
        });
      }

      const response = await fetch(`${API_BASE_URL}/food-suggest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Lỗi phân tích thực đơn y khoa!');
      }

      setResultData(data.result || data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResultData(null);
    setError(null);
  };

  return (
    <div className="clinical-diet-container">
      {/* 1. MODULE BANNER */}
      <header className="clinical-diet-header">
        <div className="clinical-diet-icon">🥗</div>
        <div className="clinical-diet-title-group">
          <h2>Tư Vấn Dinh Dưỡng Lâm Sàng & Thực Đơn AI</h2>
          <p>Thiết lập chế độ ăn chuẩn y khoa, đo lường năng lượng TDEE và vi chất cá nhân hóa theo tình trạng sức khỏe.</p>
        </div>
      </header>

      {/* 2. PATIENT VITALS SYNC BAR */}
      {profile && (
        <div className="clinical-patient-sync">
          <div className="clinical-sync-metrics">
            <span>⚕️ Chỉ số sinh tồn đồng bộ:</span>
            <span>TDEE: <strong>{profile.tdee || 2000} kcal/ngày</strong></span>
            <span>•</span>
            <span>Protein mục tiêu: <strong>{profile.protein || 75}g/ngày</strong></span>
          </div>
          {profile.food_recommendation && (
            <div className="clinical-medical-alert-pill">
              <span>🩺 Lưu ý y tế:</span>
              <strong>{profile.food_recommendation}</strong>
            </div>
          )}
        </div>
      )}

      {/* 3. QUESTIONNAIRE FORM (Khi chưa có kết quả) */}
      {!loading && !resultData && (
        <form className="clinical-form-card" onSubmit={handleSubmit}>
          {error && (
            <div style={{
              backgroundColor: 'var(--med-danger-bg)',
              border: '1px solid var(--med-danger-border)',
              color: 'var(--med-danger)',
              padding: '12px 16px',
              borderRadius: 'var(--med-radius-sm)',
              fontSize: '0.88rem',
              fontWeight: 600
            }}>
              ⚠️ {error}
            </div>
          )}

          {/* Ngân sách */}
          <div>
            <div className="clinical-form-section-title">
              <span>💵</span> 1. Ngân sách phân bổ bữa ăn (VNĐ / Ngày)
            </div>
            <div className="clinical-budget-row">
              <div className="clinical-budget-input-box">
                <input
                  type="number"
                  value={formData.daily_budget}
                  onChange={(e) => setFormData({ ...formData, daily_budget: e.target.value })}
                  placeholder="80000"
                  step="5000"
                  required
                />
                <span className="clinical-currency-tag">VNĐ / ngày</span>
              </div>
              <div className="clinical-budget-pills">
                {['50000', '80000', '120000', '180000', '250000'].map((amt) => (
                  <button
                    key={amt}
                    type="button"
                    className={`clinical-budget-btn ${formData.daily_budget === amt ? 'active' : ''}`}
                    onClick={() => handleBudgetPreset(amt)}
                  >
                    {Number(amt) / 1000}k
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Mục tiêu thể trạng */}
          <div>
            <div className="clinical-form-section-title">
              <span>🎯</span> 2. Mục tiêu thể hình & Sức khỏe
            </div>
            <div className="clinical-cards-selector">
              {[
                { id: 'Giảm cân', title: 'Giảm cân', subtitle: 'Giảm tinh bột', icon: '🏃' },
                { id: 'Tăng cơ', title: 'Tăng cơ', subtitle: 'Tăng Protein', icon: '💪' },
                { id: 'Duy trì', title: 'Duy trì', subtitle: 'Cân bằng', icon: '⚖️' },
              ].map((aimItem) => (
                <div
                  key={aimItem.id}
                  className={`clinical-radio-card ${formData.aim === aimItem.id ? 'selected' : ''}`}
                  onClick={() => setFormData({ ...formData, aim: aimItem.id })}
                >
                  <span className="clinical-radio-icon">{aimItem.icon}</span>
                  <div className="clinical-radio-content">
                    <span className="clinical-radio-title">{aimItem.title}</span>
                    <span className="clinical-radio-sub">{aimItem.subtitle}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Hình thức bữa ăn (Chế độ ăn) */}
          <div>
            <div className="clinical-form-section-title">
              <span>🍳</span> 3. Chế độ ăn uống
            </div>
            <div className="clinical-cards-selector">
              {[
                { id: 'Ăn chay', title: 'Ăn chay', subtitle: 'Thuần thực vật', icon: '🌱' },
                { id: 'Không kiêng', title: 'Không kiêng', subtitle: 'Đa dạng thực phẩm', icon: '🍽️' },
                { id: 'Eat clean', title: 'Eat clean', subtitle: 'Tự nhiên & Tươi sạch', icon: '🥦' },
              ].map((dietItem) => (
                <div
                  key={dietItem.id}
                  className={`clinical-radio-card ${formData.diet_type === dietItem.id ? 'selected' : ''}`}
                  onClick={() => setFormData({ ...formData, diet_type: dietItem.id })}
                >
                  <span className="clinical-radio-icon">{dietItem.icon}</span>
                  <div className="clinical-radio-content">
                    <span className="clinical-radio-title">{dietItem.title}</span>
                    <span className="clinical-radio-sub">{dietItem.subtitle}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Dị ứng y khoa */}
          <div>
            <div className="clinical-form-section-title">
              <span>🚫</span> 4. Thực phẩm kiêng cữ / Dị ứng y khoa
            </div>
            <div className="clinical-allergen-tags">
              {allergenOptions.map((opt) => {
                const isSelected = formData.allergen.split(';').includes(opt.id);
                return (
                  <button
                    key={opt.id}
                    type="button"
                    className={`clinical-allergen-chip ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleAllergenToggle(opt.id)}
                  >
                    <span>{opt.icon}</span>
                    <span>{opt.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="clinical-diet-submit-row">
            <button type="submit" className="btn-generate-diet">
              ⚕️ Phân Tích & Xuất Thực Đơn Y Khoa
            </button>
          </div>
        </form>
      )}

      {/* 4. LOADING STATE */}
      {loading && (
        <div className="clinical-form-card" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '16px' }}>⏳</div>
          <h3 style={{ color: 'var(--med-navy)', margin: '0 0 8px 0' }}>Bác sĩ AI đang hội chẩn & cân đối vi chất...</h3>
          <p style={{ color: 'var(--med-muted)', margin: 0 }}>Đang tính toán TDEE, lượng Protein và rà soát các thực phẩm kiêng cữ.</p>
        </div>
      )}

      {/* 5. RESULTS DISPLAY */}
      {!loading && resultData && (
        <div className="clinical-diet-results">
          {/* Doctor Nutrition Rationale */}
          {resultData.nutrition_note && (
            <div className="clinical-rationale-card">
              <span className="clinical-rationale-icon">💡</span>
              <div className="clinical-rationale-body">
                <h4>Phân tích Y khoa & Lý do chỉ định thực đơn:</h4>
                <p>{resultData.nutrition_note}</p>
              </div>
            </div>
          )}

          {/* Daily Macros Overview */}
          <div className="clinical-macro-overview">
            <div className="clinical-macro-box">
              <div className="macro-box-number">{(resultData.total_calories || 0).toLocaleString()}</div>
              <div className="macro-box-label">Tổng Calo (Kcal/Ngày)</div>
            </div>
            <div className="clinical-macro-box">
              <div className="macro-box-number" style={{ color: '#0284c7' }}>{resultData.total_protein || 0}g</div>
              <div className="macro-box-label">Protein Cung Cấp</div>
            </div>
            <div className="clinical-macro-box">
              <div className="macro-box-number" style={{ color: '#10b981' }}>{(resultData.total_cost || 0).toLocaleString()}đ</div>
              <div className="macro-box-label">Tổng Chi Phí Thực Tế</div>
            </div>
          </div>

          {/* Three Meals Breakdown */}
          <div className="clinical-meals-grid">
            {(resultData.meals || []).map((meal, index) => (
              <div className="clinical-meal-card" key={meal.id || index}>
                <div className="clinical-meal-header">
                  <div className="meal-type-badge">
                    <span>{meal.type === 'Bữa sáng' ? '🌅' : meal.type === 'Bữa trưa' ? '🌞' : '🌙'}</span>
                    <span>{meal.type}</span>
                  </div>
                  <span className="meal-time-tag">{meal.time}</span>
                </div>

                <div className="clinical-meal-body">
                  <div className="meal-dish-name">{meal.name}</div>

                  <div className="meal-cost-calories-row">
                    <span className="meal-calories">🔥 {meal.kcal || 0} kcal</span>
                    <span className="meal-cost">💵 {(meal.cost || 0).toLocaleString()}đ</span>
                  </div>

                  {/* Nutrients Macro Bars */}
                  <div className="meal-nutrients-list">
                    <div className="nutrient-bar-row">
                      <span className="nutrient-name">Đạm</span>
                      <div className="nutrient-track">
                        <div className="nutrient-fill fill-protein" style={{ width: `${Math.min(100, ((meal.protein || 0) / 45) * 100)}%` }}></div>
                      </div>
                      <span className="nutrient-grams">{meal.protein || 0}g</span>
                    </div>

                    <div className="nutrient-bar-row">
                      <span className="nutrient-name">Carb</span>
                      <div className="nutrient-track">
                        <div className="nutrient-fill fill-carbs" style={{ width: `${Math.min(100, ((meal.carbs || 0) / 60) * 100)}%` }}></div>
                      </div>
                      <span className="nutrient-grams">{meal.carbs || 0}g</span>
                    </div>

                    <div className="nutrient-bar-row">
                      <span className="nutrient-name">Béo</span>
                      <div className="nutrient-track">
                        <div className="nutrient-fill fill-fat" style={{ width: `${Math.min(100, ((meal.fat || 0) / 30) * 100)}%` }}></div>
                      </div>
                      <span className="nutrient-grams">{meal.fat || 0}g</span>
                    </div>
                  </div>

                  {meal.ingredients && (
                    <div className="meal-ingredients-box">
                      <strong>Thành phần:</strong> {meal.ingredients}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Action Row */}
          <div className="clinical-diet-actions">
            <button className="btn-clinical-secondary" onClick={handleReset}>
              ↩️ Thiết lập lại mục tiêu
            </button>
            <button className="btn-clinical-primary" onClick={(e) => handleSubmit(e, true)}>
              🔄 Bác sĩ đề xuất thực đơn khác
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClinicalNutritionModule;
