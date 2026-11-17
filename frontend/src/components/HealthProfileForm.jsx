import React, { useState, useMemo } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Stethoscope,
  Activity,
  X,
  Sparkles,
  Info,
} from 'lucide-react';

// Danh sách các tùy chọn bệnh lý nền
const MEDICAL_CONDITION_OPTIONS = [
  { id: 'normal', label: 'Bình thường (Không có bệnh lý)' },
  { id: 'diabetes', label: 'Tiểu đường / Tiền tiểu đường' },
  { id: 'hypertension', label: 'Cao huyết áp / Tim mạch' },
  { id: 'joint_injury', label: 'Chấn thương xương khớp / Cột sống' },
  { id: 'stomach', label: 'Bệnh lý dạ dày / Tiêu hóa' },
  { id: 'other', label: 'Khác (ghi rõ bên dưới)' },
];

/**
 * Hàm phân loại thể trạng theo tiêu chuẩn WHO / IDP cho người châu Á
 */
const getBmiCategory = (bmi) => {
  if (!bmi || bmi <= 0) return { label: '--', color: 'text-slate-400', bg: 'bg-slate-100' };
  if (bmi < 16.0) return { label: 'Gầy độ III (Suy dinh dưỡng nặng)', color: 'text-rose-700', bg: 'bg-rose-100' };
  if (bmi < 17.0) return { label: 'Gầy độ II (Thiếu cân vừa)', color: 'text-amber-700', bg: 'bg-amber-100' };
  if (bmi < 18.5) return { label: 'Gầy độ I (Thiếu cân nhẹ)', color: 'text-yellow-700', bg: 'bg-yellow-100' };
  if (bmi < 23.0) return { label: 'Bình thường (Lý tưởng)', color: 'text-emerald-700', bg: 'bg-emerald-100' };
  if (bmi < 25.0) return { label: 'Tiền béo phì / Thừa cân nhẹ', color: 'text-orange-700', bg: 'bg-orange-100' };
  if (bmi < 30.0) return { label: 'Béo phì độ I', color: 'text-rose-600', bg: 'bg-rose-100' };
  if (bmi < 35.0) return { label: 'Béo phì độ II', color: 'text-rose-700', bg: 'bg-rose-100' };
  return { label: 'Béo phì độ III (Bệnh lý nguy hiểm)', color: 'text-rose-900', bg: 'bg-rose-200' };
};

/**
 * Client-side fallback validator (tương đồng 100% logic với backend safety_guardrail.py)
 * Cho phép test nhanh ngay cả khi backend chưa bật hoặc API gặp sự cố mạng.
 */
const mockClientSideValidate = (profile) => {
  const heightM = parseFloat(profile.height_cm) / 100.0;
  const weightKg = parseFloat(profile.weight_kg);
  const bmi = heightM > 0 ? parseFloat((weightKg / (heightM * heightM)).toFixed(2)) : 0;
  const age = parseInt(profile.age, 10) || 0;
  const targetCal = profile.target_calories ? parseFloat(profile.target_calories) : null;
  const budget = parseFloat(profile.budget_vnd) || 0;
  const freeMins = parseInt(profile.free_minutes_per_week, 10) || 0;

  const medicalWarnings = [];
  const insufficientReasons = [];

  // 1. Kiểm tra BMI & Tuổi
  if (bmi < 16.0) {
    medicalWarnings.push(`Chỉ số BMI (${bmi}) dưới 16.0 (Suy dinh dưỡng nặng). Cần tham vấn bác sĩ dinh dưỡng trước khi tập.`);
  } else if (bmi >= 35.0) {
    medicalWarnings.push(`Chỉ số BMI (${bmi}) từ 35.0 trở lên (Béo phì độ II trở lên), tiềm ẩn nguy cơ tim mạch và khớp.`);
  }

  if (age < 12 || age > 65) {
    medicalWarnings.push(`Độ tuổi ${age} nằm ngoài nhóm đối tượng học sinh - sinh viên (12–24 tuổi) đã kiểm định của FitBreak.`);
  }

  // 2. Kiểm tra bệnh lý đã chọn
  const hasMedicalCondition = profile.medical_conditions.some((c) => c !== 'normal');
  if (hasMedicalCondition) {
    medicalWarnings.push('Phát hiện có bệnh lý nền được tích chọn (Tiểu đường, huyết áp hoặc xương khớp/dạ dày).');
  }

  // 3. Quét từ khóa trong ghi chú
  const notes = (profile.user_notes || '').toLowerCase();
  const dangerKeywords = ['khó thở', 'đau ngực', 'thoát vị', 'gãy xương', 'chấn thương', 'tim mạch', 'tiểu đường'];
  const matched = dangerKeywords.filter((kw) => notes.includes(kw));
  if (matched.length > 0) {
    medicalWarnings.push(`Ghi chú chứa từ khóa cảnh báo sức khỏe: ${matched.map((m) => `"${m}"`).join(', ')}.`);
  }

  // 4. Kiểm tra calo mục tiêu
  if (targetCal) {
    if (targetCal < 1000) medicalWarnings.push(`Calo mục tiêu (${targetCal} kcal) quá thấp (< 1000 kcal), nguy cơ hạ đường huyết.`);
    if (targetCal > 4500) medicalWarnings.push(`Calo mục tiêu (${targetCal} kcal) quá cao (> 4500 kcal).`);
    if (bmi < 18.5 && profile.goal === 'giam_can') {
      medicalWarnings.push(`Thể trạng đang thiếu cân (BMI ${bmi}) nhưng lại đặt mục tiêu 'Giảm cân' là phản khoa học.`);
    }
  }

  if (medicalWarnings.length > 0) {
    return {
      status: 'MEDICAL_WARNING',
      bmi,
      bmi_category: getBmiCategory(bmi).label,
      reasons: medicalWarnings,
      suggestion: 'Vui lòng tham khảo ý kiến bác sĩ hoặc chuyên viên y tế trước khi thực hiện chế độ ăn kiêng hay vận động mạnh.',
      disclaimer: 'FitBreak là công cụ hỗ trợ lối sống, không thay thế chẩn đoán hoặc phác đồ điều trị y tế chuyên khoa.',
      allow_ai_generation: false,
    };
  }

  // 5. Kiểm tra dữ liệu khả dụng
  if (budget > 0 && budget < 25000) {
    insufficientReasons.push(`Ngân sách ăn uống (${budget.toLocaleString()}đ/ngày) dưới mức tối thiểu 25,000đ/ngày.`);
  }
  if (freeMins > 0 && freeMins < 30) {
    insufficientReasons.push(`Thời gian rảnh (${freeMins} phút/tuần) chưa đạt tối thiểu 30 phút/tuần để xếp lịch.`);
  }

  if (insufficientReasons.length > 0) {
    return {
      status: 'INSUFFICIENT_DATA',
      bmi,
      bmi_category: getBmiCategory(bmi).label,
      reasons: insufficientReasons,
      suggestion: 'Vui lòng tăng ngân sách ăn uống hoặc đăng ký thêm khung giờ rảnh trong tuần.',
      disclaimer: 'Hệ thống cần tối thiểu ngân sách và quỹ thời gian để xây dựng phương án khả thi.',
      allow_ai_generation: false,
    };
  }

  return {
    status: 'PASS',
    bmi,
    bmi_category: getBmiCategory(bmi).label,
    reasons: ['Tất cả chỉ số sức khỏe đều đạt chuẩn an toàn.'],
    allow_ai_generation: true,
  };
};

/**
 * HealthProfileForm Component
 */
const HealthProfileForm = ({ onProfileSaved, apiBaseUrl = '' }) => {
  // Form State
  const [formData, setFormData] = useState({
    height_cm: '170',
    weight_kg: '62',
    age: '19',
    goal: 'tang_co',
    target_calories: '2200',
    budget_vnd: '80000',
    free_minutes_per_week: '180',
    allergies: '',
    medical_conditions: ['normal'],
    user_notes: '',
  });

  const [loading, setLoading] = useState(false);
  const [guardrailModalData, setGuardrailModalData] = useState(null); // Dữ liệu khi bị chặn
  const [isAiUnlocked, setIsAiUnlocked] = useState(false); // Trạng thái mở khóa AI
  const [saveSuccessMsg, setSaveSuccessMsg] = useState('');

  // 1. Tự động tính chỉ số BMI khi nhập chiều cao và cân nặng
  const calculatedBmi = useMemo(() => {
    const h = parseFloat(formData.height_cm) / 100.0;
    const w = parseFloat(formData.weight_kg);
    if (h > 0 && w > 0) {
      return parseFloat((w / (h * h)).toFixed(1));
    }
    return null;
  }, [formData.height_cm, formData.weight_kg]);

  const bmiMeta = useMemo(() => getBmiCategory(calculatedBmi), [calculatedBmi]);

  // Xử lý thay đổi input
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setSaveSuccessMsg('');
  };

  // Xử lý toggle checkbox bệnh lý
  const handleCheckboxChange = (conditionId) => {
    setFormData((prev) => {
      let updated;
      if (conditionId === 'normal') {
        updated = ['normal'];
      } else {
        const withoutNormal = prev.medical_conditions.filter((c) => c !== 'normal');
        if (withoutNormal.includes(conditionId)) {
          updated = withoutNormal.filter((c) => c !== conditionId);
          if (updated.length === 0) updated = ['normal'];
        } else {
          updated = [...withoutNormal, conditionId];
        }
      }
      return { ...prev, medical_conditions: updated };
    });
    setSaveSuccessMsg('');
  };

  // 3. Xử lý khi bấm nút "Lưu thông tin"
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSaveSuccessMsg('');

    try {
      let result = null;

      // Thử gọi API POST /api/validate-profile nếu có apiBaseUrl
      if (apiBaseUrl) {
        try {
          const res = await fetch(`${apiBaseUrl}/api/validate-profile`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              ...formData,
              height_cm: parseFloat(formData.height_cm),
              weight_kg: parseFloat(formData.weight_kg),
              age: parseInt(formData.age, 10),
              target_calories: formData.target_calories ? parseFloat(formData.target_calories) : null,
              budget_vnd: parseFloat(formData.budget_vnd),
              free_minutes_per_week: parseInt(formData.free_minutes_per_week, 10),
              allergies: formData.allergies ? formData.allergies.split(',').map((a) => a.trim()) : [],
            }),
          });
          if (res.ok) {
            result = await res.json();
          }
        } catch (netErr) {
          console.warn('Backend API không phản hồi, chuyển sang fallback mock client:', netErr);
        }
      }

      // Nếu không có API hoặc API lỗi -> Chạy client validator giả lập để test nhanh
      if (!result) {
        result = mockClientSideValidate(formData);
      }

      // Kiểm tra kết quả Guardrail
      if (result.status === 'MEDICAL_WARNING' || result.status === 'INSUFFICIENT_DATA') {
        setGuardrailModalData(result);
        setIsAiUnlocked(false);
      } else {
        // PASS an toàn
        setIsAiUnlocked(true);
        setSaveSuccessMsg('Hồ sơ đạt chuẩn an toàn y tế. Các tính năng AI đã được mở khóa hoàn toàn!');
        if (onProfileSaved) onProfileSaved(formData, true);
      }
    } catch (err) {
      console.error('Lỗi thẩm định hồ sơ:', err);
    } finally {
      setLoading(false);
    }
  };

  // Hành động: Vẫn lưu hồ sơ nhưng Khóa tính năng AI
  const handleForceSaveWithAiLocked = () => {
    setGuardrailModalData(null);
    setIsAiUnlocked(false);
    setSaveSuccessMsg('Đã lưu hồ sơ thành công. Lưu ý: Tính năng tạo thực đơn & bài tập AI đã bị khóa để bảo đảm an toàn sức khỏe.');
    if (onProfileSaved) onProfileSaved(formData, false);
  };

  return (
    <div className="max-w-3xl mx-auto p-4 sm:p-6 bg-slate-50 min-h-screen">
      {/* Card Form */}
      <div className="bg-white border border-slate-200/90 rounded-2xl shadow-sm overflow-hidden">
        {/* Header */}
        <div className="border-b border-slate-100 p-6 bg-gradient-to-r from-sky-50/50 via-white to-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold">
              <Activity className="w-5 h-5 text-sky-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">Hồ Sơ Sức Khỏe & Thể Trạng</h2>
              <p className="text-xs text-slate-500 mt-0.5">Thiết lập dữ liệu ban đầu để hệ thống rà soát an toàn y học</p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* PHẦN 1: THÔNG SỐ CƠ THỂ & TỰ ĐỘNG TÍNH BMI */}
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 mb-3 flex items-center gap-2">
              <span>1. Chỉ Số Nhân Trắc Học</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Chiều cao (cm) *</label>
                <input
                  type="number"
                  name="height_cm"
                  required
                  min="100"
                  max="230"
                  value={formData.height_cm}
                  onChange={handleChange}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm font-medium"
                  placeholder="170"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Cân nặng (kg) *</label>
                <input
                  type="number"
                  name="weight_kg"
                  required
                  min="30"
                  max="200"
                  step="0.5"
                  value={formData.weight_kg}
                  onChange={handleChange}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm font-medium"
                  placeholder="65"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Độ tuổi (12–24) *</label>
                <input
                  type="number"
                  name="age"
                  required
                  min="10"
                  max="80"
                  value={formData.age}
                  onChange={handleChange}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm font-medium"
                  placeholder="19"
                />
              </div>
            </div>

            {/* DÒNG HIỂN THỊ BMI TỰ ĐỘNG */}
            <div className="mt-4 p-3.5 bg-slate-50 border border-slate-200/80 rounded-xl flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">Chỉ số BMI tự động:</span>
                <span className="text-2xl font-black text-slate-800 tracking-tight">
                  {calculatedBmi !== null ? calculatedBmi : '--'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">Phân loại:</span>
                <span className={`text-xs font-bold px-3 py-1 rounded-full ${bmiMeta.bg} ${bmiMeta.color}`}>
                  {bmiMeta.label}
                </span>
              </div>
            </div>
          </div>

          {/* PHẦN 2: BỆNH LÝ NỀN & GHI CHÚ TỰ DO */}
          <div className="pt-2 border-t border-slate-100">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 mb-2 flex items-center gap-2">
              <Stethoscope className="w-4 h-4 text-sky-600" />
              <span>2. Tình Trạng Sức Khỏe & Bệnh Lý Nền</span>
            </h3>
            <p className="text-xs text-slate-500 mb-3">
              Tích chọn trung thực để hệ thống kích hoạt cơ chế bảo vệ sức khỏe và chống chỉ định vận động:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {MEDICAL_CONDITION_OPTIONS.map((opt) => {
                const isChecked = formData.medical_conditions.includes(opt.id);
                return (
                  <label
                    key={opt.id}
                    className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer text-xs font-medium transition-all ${
                      isChecked
                        ? opt.id === 'normal'
                          ? 'border-emerald-300 bg-emerald-50/70 text-emerald-900'
                          : 'border-rose-300 bg-rose-50/70 text-rose-900'
                        : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-700'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => handleCheckboxChange(opt.id)}
                      className="rounded border-slate-300 text-sky-600 focus:ring-sky-500 w-4 h-4"
                    />
                    <span>{opt.label}</span>
                  </label>
                );
              })}
            </div>

            {/* Ô ghi chú ngắn */}
            <div className="mt-3">
              <label className="block text-xs font-semibold text-slate-600 mb-1">
                Ghi chú thêm về sức khỏe / chấn thương / dị ứng đặc biệt:
              </label>
              <textarea
                name="user_notes"
                rows={2}
                value={formData.user_notes}
                onChange={handleChange}
                placeholder="Ví dụ: Em hay bị khó thở khi vận động gắng sức, từng đau lưng dưới nhẹ..."
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm font-normal"
              />
            </div>
          </div>

          {/* PHẦN 3: MỤC TIÊU & TÀI CHÍNH */}
          <div className="pt-2 border-t border-slate-100">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 mb-3">
              <span>3. Kế Hoạch & Ngân Sách Sinh Viên</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Mục tiêu thể hình</label>
                <select
                  name="goal"
                  value={formData.goal}
                  onChange={handleChange}
                  className="w-full px-3 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm font-medium bg-white"
                >
                  <option value="giam_can">Giảm cân / Thon gọn</option>
                  <option value="tang_co">Tăng cơ / Phát triển thể hình</option>
                  <option value="duy_tri">Duy trì / Phục hồi sức khỏe</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Ngân sách ăn (VNĐ/ngày) *</label>
                <input
                  type="number"
                  name="budget_vnd"
                  required
                  step="5000"
                  value={formData.budget_vnd}
                  onChange={handleChange}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm font-medium"
                  placeholder="80000"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1.5">Thời gian rảnh (phút/tuần) *</label>
                <input
                  type="number"
                  name="free_minutes_per_week"
                  required
                  step="15"
                  value={formData.free_minutes_per_week}
                  onChange={handleChange}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500 text-sm font-medium"
                  placeholder="180"
                />
              </div>
            </div>
          </div>

          {/* THÔNG BÁO THÀNH CÔNG NẾU ĐÃ PASS */}
          {saveSuccessMsg && (
            <div
              className={`p-4 rounded-xl text-sm flex items-start gap-3 border ${
                isAiUnlocked ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-amber-50 border-amber-200 text-amber-900'
              }`}
            >
              {isAiUnlocked ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              ) : (
                <Lock className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              )}
              <div className="font-medium leading-relaxed">{saveSuccessMsg}</div>
            </div>
          )}

          {/* FOOTER ACTIONS */}
          <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <ShieldAlert className="w-4 h-4 text-slate-400" />
              <span>Hệ thống bảo vệ Safety Guardrail tự động kích hoạt khi lưu</span>
            </div>

            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2.5 bg-sky-600 hover:bg-sky-700 active:bg-sky-800 text-white font-bold text-sm rounded-xl shadow-sm transition-all duration-150 cursor-pointer disabled:opacity-50"
              >
                {loading ? 'Đang thẩm định...' : '💾 Lưu thông tin'}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* KHỐI NÚT TẠO THỰC ĐƠN / LỊCH TẬP (MỞ KHÓA HOẶC BỊ KHÓA) */}
      <div className="mt-6 p-5 bg-white border border-slate-200 rounded-2xl flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="font-bold text-slate-900 text-sm">Trạng thái tính năng AI</h4>
            {isAiUnlocked ? (
              <span className="text-[11px] font-extrabold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                SẴN SÀNG
              </span>
            ) : (
              <span className="text-[11px] font-extrabold px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800">
                BỊ KHÓA
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {isAiUnlocked
              ? 'Hồ sơ đã đạt chuẩn an toàn y tế. Bạn có thể sử dụng AI để tạo thực đơn và giáo án tuần.'
              : 'Tính năng AI sẽ bị tạm khóa khi hồ sơ chưa qua kiểm duyệt hoặc có cảnh báo y tế nguy hiểm.'}
          </p>
        </div>

        <button
          type="button"
          disabled={!isAiUnlocked}
          onClick={() => alert('Chuyển sang module Tạo Thực đơn & Lịch tập AI!')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all shadow-sm ${
            isAiUnlocked
              ? 'bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer'
              : 'bg-slate-100 text-slate-400 border border-slate-200 cursor-not-allowed'
          }`}
        >
          {isAiUnlocked ? <Sparkles className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
          <span>Tạo Thực Đơn & Lịch Tập AI</span>
        </button>
      </div>

      {/* =========================================================================
          POPUP MODAL CẢNH BÁO Y TẾ & THIẾU DỮ LIỆU Ở GIỮA MÀN HÌNH
          ========================================================================= */}
      {guardrailModalData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs transition-opacity animate-in fade-in duration-200">
          <div
            className="w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden transform transition-all animate-in zoom-in-95 duration-200"
            role="dialog"
            aria-modal="true"
          >
            {/* Modal Header */}
            <div
              className={`p-5 border-b flex items-start justify-between gap-3 ${
                guardrailModalData.status === 'MEDICAL_WARNING'
                  ? 'bg-rose-50/80 border-rose-100 text-rose-900'
                  : 'bg-amber-50/80 border-amber-100 text-amber-950'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                    guardrailModalData.status === 'MEDICAL_WARNING'
                      ? 'bg-rose-100 text-rose-600'
                      : 'bg-amber-100 text-amber-700'
                  }`}
                >
                  {guardrailModalData.status === 'MEDICAL_WARNING' ? (
                    <ShieldAlert className="w-6 h-6" />
                  ) : (
                    <AlertTriangle className="w-6 h-6" />
                  )}
                </div>
                <div>
                  <h3 className="font-black text-base leading-tight">
                    {guardrailModalData.status === 'MEDICAL_WARNING'
                      ? 'Cảnh Báo An Toàn Y Tế'
                      : 'Chưa Đủ Căn Cứ Dữ Liệu'}
                  </h3>
                  <span
                    className={`inline-block text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full mt-1 border ${
                      guardrailModalData.status === 'MEDICAL_WARNING'
                        ? 'bg-rose-100 border-rose-300 text-rose-800'
                        : 'bg-amber-100 border-amber-300 text-amber-900'
                    }`}
                  >
                    {guardrailModalData.status}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setGuardrailModalData(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-black/5"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
              {/* BMI Pill nếu có */}
              {guardrailModalData.bmi > 0 && (
                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-200/80 text-xs">
                  <span className="font-semibold text-slate-500 uppercase">Chỉ số BMI ghi nhận:</span>
                  <span className="font-extrabold text-slate-900 text-sm">
                    {guardrailModalData.bmi} ({guardrailModalData.bmi_category})
                  </span>
                </div>
              )}

              {/* Danh sách lý do cảnh báo */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Lý do hệ thống tạm dừng tự động kê đơn:
                </h4>
                <ul className="space-y-2 pl-0 list-none m-0">
                  {guardrailModalData.reasons.map((reason, idx) => (
                    <li
                      key={idx}
                      className="text-xs sm:text-sm text-slate-800 bg-slate-50 border border-slate-200/60 rounded-lg p-2.5 leading-relaxed flex items-start gap-2"
                    >
                      <span className="text-rose-500 font-bold shrink-0">•</span>
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Lời khuyên gặp bác sĩ */}
              {guardrailModalData.suggestion && (
                <div className="p-3.5 bg-rose-50/50 border border-rose-200/70 rounded-xl text-xs text-rose-900 leading-relaxed flex items-start gap-2.5">
                  <Stethoscope className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <div>
                    <strong className="font-bold">Khuyến cáo: </strong>
                    {guardrailModalData.suggestion}
                  </div>
                </div>
              )}

              {/* Disclaimer */}
              <div className="flex items-start gap-2 text-[11px] text-slate-400 leading-normal p-2 bg-slate-50 rounded-lg border border-slate-100">
                <Info className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                <span>{guardrailModalData.disclaimer}</span>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="p-4 bg-slate-50 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-end gap-2.5">
              <button
                type="button"
                onClick={() => setGuardrailModalData(null)}
                className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-slate-300 bg-white hover:bg-slate-100 text-slate-700 font-bold text-xs transition-colors cursor-pointer"
              >
                ✏️ Sửa lại thông tin
              </button>
              <button
                type="button"
                onClick={handleForceSaveWithAiLocked}
                className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs transition-colors cursor-pointer flex items-center justify-center gap-1.5"
              >
                <Lock className="w-3.5 h-3.5" />
                <span>Vẫn lưu hồ sơ (Khóa tính năng AI)</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HealthProfileForm;
