import { API_BASE_URL } from '../config';
import { useState, useEffect, Fragment } from 'react';
import '../style/clinicalSchedule.css';

const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const hours = Array.from({ length: 15 }, (_, i) => i + 6); // 6:00 -> 20:00

const dayNamesVi = {
  Mon: 'Thứ Hai',
  Tue: 'Thứ Ba',
  Wed: 'Thứ Tư',
  Thu: 'Thứ Năm',
  Fri: 'Thứ Sáu',
  Sat: 'Thứ Bảy',
  Sun: 'Chủ Nhật'
};

const dayTypeClinicalLabels = {
  resistance_training: { label: 'Tập Kháng Lực / Cơ', className: 'badge-clinical-resistance' },
  cardio: { label: 'Cardio / Tim Mạch', className: 'badge-clinical-cardio' },
  hiit: { label: 'HIIT Cường Độ Cao', className: 'badge-clinical-hiit' },
  Rest: { label: 'Nghỉ Phục Hồi Thể Lực', className: 'badge-clinical-rest' }
};

const formatDayTimeRanges = (slotsArray, day) => {
  if (!slotsArray || slotsArray.length === 0) return '';
  const dayPrefix = `${day}-`;
  const daySlots = slotsArray.filter(s => s.startsWith(dayPrefix));
  if (daySlots.length === 0) return '';

  const minutesList = daySlots.map(s => {
    const parts = s.split('-');
    const h = parseInt(parts[1], 10);
    const m = parseInt(parts[2], 10);
    return h * 60 + m;
  });

  const sortedMinutes = Array.from(new Set(minutesList)).sort((a, b) => a - b);
  if (sortedMinutes.length === 0) return '';

  const intervals = [];
  let start = sortedMinutes[0];
  let prev = start;

  for (let i = 1; i < sortedMinutes.length; i++) {
    const current = sortedMinutes[i];
    if (current === prev + 30) {
      prev = current;
    } else {
      intervals.push([start, prev + 30]);
      start = current;
      prev = current;
    }
  }
  intervals.push([start, prev + 30]);

  const fmt = (min) => {
    const h = Math.floor(min / 60);
    const m = min % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
  };

  return intervals.map(([s, e]) => `${fmt(s)} - ${fmt(e)}`).join(', ');
};

/**
 * ClinicalRehabSchedule Component (MedTech Standard)
 * Lịch trình vận động, bài tập trị liệu & phục hồi thể lực cá nhân hóa theo mức:
 * 'light' (nhẹ nhàng, phục hồi), 'medium' (vừa phải), 'heavy' (chuyên sâu).
 */
const ClinicalRehabSchedule = ({ scheduleData, onScheduleGenerated }) => {
  const [selectedSlots, setSelectedSlots] = useState(() => {
    try {
      const saved = localStorage.getItem('selectedTimeSlots');
      return saved ? new Set(JSON.parse(saved)) : new Set();
    } catch (e) {
      return new Set();
    }
  });

  const [isMouseDown, setIsMouseDown] = useState(false);
  const [isSelecting, setIsSelecting] = useState(true);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [userProfile, setUserProfile] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        const userObj = JSON.parse(localStorage.getItem('user') || '{}');
        const email = userObj?.email;
        if (!email || !token) return;

        const res = await fetch(`${API_BASE_URL}/profiles/get-profile-by-email/${email}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setUserProfile(data);
        }
      } catch (err) {
        console.error("Lỗi khi nạp profile cho lịch tập:", err);
      }
    };
    fetchProfile();
  }, []);

  const getSlotKey = (day, hour, isHalf) => `${day}-${hour}-${isHalf ? '30' : '00'}`;

  const handleMouseDown = (key) => {
    setIsMouseDown(true);
    const newSelected = new Set(selectedSlots);
    if (newSelected.has(key)) {
      newSelected.delete(key);
      setIsSelecting(false);
    } else {
      newSelected.add(key);
      setIsSelecting(true);
    }
    setSelectedSlots(newSelected);
  };

  const handleMouseEnter = (key) => {
    if (!isMouseDown) return;
    const newSelected = new Set(selectedSlots);
    if (isSelecting) {
      newSelected.add(key);
    } else {
      newSelected.delete(key);
    }
    setSelectedSlots(newSelected);
  };

  const handleMouseUp = () => {
    setIsMouseDown(false);
  };

  const handleGenerateSchedule = async () => {
    setErrorMsg('');
    const slotsByDay = {};
    days.forEach((day) => {
      slotsByDay[day] = [];
    });

    selectedSlots.forEach((slotKey) => {
      const [day, hour, min] = slotKey.split('-');
      const h = parseInt(hour, 10);
      const m = parseInt(min, 10);
      slotsByDay[day].push(h * 60 + m);
    });

    const timetable = {};
    let activeDaysCount = 0;

    days.forEach((day) => {
      const minutesList = slotsByDay[day].sort((a, b) => a - b);
      if (minutesList.length > 0) {
        let totalContinuousMinutes = 0;
        let maxSessionMinutes = 0;
        let currentRun = 30;

        for (let i = 1; i < minutesList.length; i++) {
          if (minutesList[i] === minutesList[i - 1] + 30) {
            currentRun += 30;
          } else {
            maxSessionMinutes = Math.max(maxSessionMinutes, currentRun);
            currentRun = 30;
          }
        }
        maxSessionMinutes = Math.max(maxSessionMinutes, currentRun);
        totalContinuousMinutes = minutesList.length * 30;

        timetable[day] = {
          available_minutes: totalContinuousMinutes,
          max_session_minutes: maxSessionMinutes,
        };
        activeDaysCount++;
      } else {
        timetable[day] = {
          available_minutes: 0,
          max_session_minutes: 0,
        };
      }
    });

    if (activeDaysCount < 3) {
      setErrorMsg('Vui lòng chọn thời gian rảnh ít nhất 3 ngày trong tuần để đảm bảo hiệu quả phục hồi thể lực!');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setErrorMsg('Vui lòng đăng nhập để thiết lập lịch phục hồi thể lực!');
        setLoading(false);
        return;
      }

      let response;
      try {
        response = await fetch(`${API_BASE_URL}/schedule/generate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            timetable,
            level: userProfile?.level_of_physical_activity || 'medium',
          }),
        });
      } catch (netErr) {
        console.warn('Endpoint /schedule/generate không phản hồi, thử /schedule-maker:', netErr);
      }

      if (!response || response.status === 404) {
        response = await fetch(`${API_BASE_URL}/schedule-maker`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            timetable,
            level: userProfile?.level_of_physical_activity || 'medium',
          }),
        });
      }

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Không thể tạo thời khóa biểu phục hồi!');
      }

      const scheduleToStore = data.schedule || data;
      localStorage.setItem('workoutSchedule', JSON.stringify(scheduleToStore));
      localStorage.setItem('selectedTimeSlots', JSON.stringify(Array.from(selectedSlots)));
      if (onScheduleGenerated) {
        onScheduleGenerated(scheduleToStore);
      }
      setIsEditing(false);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const selectedSlotsArray = Array.from(selectedSlots);
  const selectedCount = selectedSlots.size;
  const totalHours = (selectedCount * 0.5).toFixed(1);

  const levelStr = (userProfile?.level_of_physical_activity || 'medium').toLowerCase();
  const getPrescriptionMeta = (lvl) => {
    switch (lvl) {
      case 'heavy':
        return {
          title: 'Chỉ định: Luyện tập Tăng cường & Kháng lực Thể hình (Heavy)',
          pillClass: 'level-pill-heavy',
          desc: 'Thể trạng tốt, không có hạn chế bệnh lý cấp tính. Giáo án tập trung kích thích sợi cơ, tăng cường sức bền tim mạch và nâng cao giới hạn thể lực.'
        };
      case 'medium':
        return {
          title: 'Chỉ định: Vận động Thể chất Cân bằng & Kiểm soát Chỉ số (Medium)',
          pillClass: 'level-pill-medium',
          desc: 'Phù hợp người có thể trạng tiền béo phì hoặc đang ổn định đường huyết/huyết áp. Giáo án cân đối giữa bài tập kháng lực vừa phải và cardio đốt mỡ an toàn.'
        };
      case 'light':
      default:
        return {
          title: 'Chỉ định: Vận động Trị liệu & Phục hồi Chức năng (Light)',
          pillClass: 'level-pill-light',
          desc: 'Dành cho người có bệnh lý mạn tính, nguy cơ tim mạch hoặc thừa cân nhiều. Ưu tiên bài tập cường độ thấp, tập trung giãn cơ, bảo vệ sụn khớp và điều hòa nhịp thở.'
        };
    }
  };

  const prescription = getPrescriptionMeta(levelStr);

  // VIEW 1: TIMETABLE BOARD
  if (scheduleData && !isEditing) {
    const weeklySchedule = scheduleData.schedule || scheduleData;

    return (
      <div className="clinical-schedule-container">
        {/* Header */}
        <div className="clinical-schedule-header-card">
          <div className="clinical-schedule-title-area">
            <div className="clinical-schedule-icon">🗓️</div>
            <div className="clinical-schedule-titles">
              <h2>Thời Khóa Biểu Vận Động & Trị Liệu Cá Nhân Hóa</h2>
              <p>Lộ trình tập luyện tuần được thiết kế đồng bộ theo kết quả kiểm tra sinh tồn y tế</p>
            </div>
          </div>
          <div className="clinical-schedule-actions">
            <button className="btn-clinical-reschedule" onClick={() => setIsEditing(true)}>
              ⚙️ Chọn lại giờ & Tinh chỉnh
            </button>
          </div>
        </div>

        {/* Prescription Card */}
        <div className="clinical-prescription-card">
          <span className="prescription-icon">🩺</span>
          <div className="prescription-content">
            <div className="prescription-header-row">
              <h4>{prescription.title}</h4>
              <span className={`prescription-level-pill ${prescription.pillClass}`}>{levelStr}</span>
            </div>
            <p>{prescription.desc}</p>
          </div>
        </div>

        {/* 7 Days Grid */}
        <div className="clinical-board-grid">
          {days.map((day) => {
            const rawDayData = weeklySchedule[day];
            const slots = Array.isArray(rawDayData) ? rawDayData : (rawDayData ? [rawDayData] : []);
            const activeSlot = slots.find(s => (s.day_type || s.type) !== 'Rest' && s.exercises && s.exercises.length > 0) || slots[0];
            const dayType = activeSlot?.day_type || activeSlot?.type || 'Rest';
            const exercises = slots.flatMap(s => s.exercises || []);
            const isRest = !exercises || exercises.length === 0 || dayType === 'Rest';
            const categoryInfo = dayTypeClinicalLabels[dayType] || dayTypeClinicalLabels.Rest;
            const timeRangeText = formatDayTimeRanges(selectedSlotsArray, day);

            return (
              <div key={day} className={`clinical-day-column ${isRest ? 'is-rest' : ''}`}>
                <div className="clinical-day-header">
                  <div className="clinical-day-title">{dayNamesVi[day]}</div>
                  {timeRangeText ? (
                    <div className="clinical-day-time-tag">🕒 {timeRangeText}</div>
                  ) : (
                    <div className="clinical-day-time-tag" style={{ color: '#94a3b8', backgroundColor: '#f1f5f9' }}>
                      Theo lịch rảnh
                    </div>
                  )}
                  <div>
                    <span className={`clinical-category-badge ${categoryInfo.className}`}>
                      {categoryInfo.label}
                    </span>
                  </div>
                </div>

                <div className="clinical-exercises-stack">
                  {isRest ? (
                    <div className="rest-day-clinical-card">
                      <div className="rest-icon-large">🌿</div>
                      <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#475569' }}>Ngày Nghỉ Phục Hồi</div>
                      <div style={{ fontSize: '0.75rem', marginTop: '4px' }}>Nghỉ ngơi, ngủ đủ giấc & giãn cơ nhẹ</div>
                    </div>
                  ) : (
                    exercises.map((ex, idx) => {
                      const exName = ex.exercise || ex.name || ex.exercise_name || "Bài tập";
                      const bodyPart = ex.body_part ? ex.body_part.replace('_', ' ') : "Toàn thân";
                      const duration = ex.time_need || ex.duration || 15;
                      const setsReps = ex.sets 
                        ? `${ex.sets} hiệp ${ex.reps ? `× ${ex.reps}` : ''}`
                        : `${duration} phút`;

                      return (
                        <div key={ex.id || idx} className="clinical-task-card">
                          <div className="task-name-clinical">{exName}</div>
                          <div className="task-meta-clinical">
                            <span style={{ textTransform: 'capitalize' }}>🎯 {bodyPart}</span>
                            <span className="task-sets-clinical">⏱ {setsReps}</span>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // VIEW 2: TIME GRID SELECTOR
  return (
    <div className="clinical-schedule-container" onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp}>
      <div className="clinical-schedule-header-card">
        <div className="clinical-schedule-title-area">
          <div className="clinical-schedule-icon">⏰</div>
          <div className="clinical-schedule-titles">
            {scheduleData && (
              <button 
                onClick={() => setIsEditing(false)}
                style={{
                  background: 'none', border: 'none', color: 'var(--med-primary)', 
                  fontWeight: 700, fontSize: '0.82rem', cursor: 'pointer', padding: 0, marginBottom: '6px'
                }}
              >
                ← Quay lại xem thời khóa biểu hiện tại
              </button>
            )}
            <h2>Đăng Ký Khung Giờ Rảnh Trong Tuần</h2>
            <p>Nhấp hoặc kéo thả chuột trên bảng để đánh dấu các khung giờ bạn có thể vận động (mỗi ô là 30 phút)</p>
          </div>
        </div>

        <div className="clinical-schedule-actions">
          <div style={{ fontSize: '0.88rem', color: 'var(--med-slate)', fontWeight: 600 }}>
            Đã chọn: <strong style={{ color: 'var(--med-primary-dark)' }}>{selectedCount} ô ({totalHours} giờ)</strong>
          </div>
          <button 
            className="btn-clinical-save-schedule"
            onClick={handleGenerateSchedule}
            disabled={loading || selectedCount === 0}
          >
            {loading ? 'Đang phân bổ bài tập...' : '⚕️ Thiết Lập Lịch Phục Hồi AI'}
          </button>
        </div>
      </div>

      {errorMsg && (
        <div style={{
          backgroundColor: 'var(--med-danger-bg)', border: '1px solid var(--med-danger-border)',
          color: 'var(--med-danger)', padding: '12px 18px', borderRadius: 'var(--med-radius-md)',
          marginBottom: '20px', fontWeight: 600, fontSize: '0.88rem'
        }}>
          ⚠️ {errorMsg}
        </div>
      )}

      {/* Grid Selector */}
      <div className="clinical-time-grid-wrapper">
        <div className="clinical-grid-table">
          <div style={{ padding: '8px', fontWeight: 800, fontSize: '0.78rem', color: '#64748b', textAlign: 'center' }}>
            GIỜ
          </div>
          {days.map(d => (
            <div key={d} style={{ padding: '8px', fontWeight: 800, fontSize: '0.82rem', color: 'var(--med-navy)', textAlign: 'center' }}>
              {dayNamesVi[d]}
            </div>
          ))}

          {hours.map((hour) => (
            <Fragment key={`hour-row-${hour}`}>
              <div style={{ padding: '6px 4px', fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textAlign: 'center' }}>
                {hour}:00
              </div>
              {days.map(day => {
                const k1 = getSlotKey(day, hour, false);
                const isSelected = selectedSlots.has(k1);
                return (
                  <div
                    key={k1}
                    className={`time-slot-cell ${isSelected ? 'selected' : ''}`}
                    onMouseDown={() => handleMouseDown(k1)}
                    onMouseEnter={() => handleMouseEnter(k1)}
                    title={`${dayNamesVi[day]} ${hour}:00 - ${hour}:30`}
                  />
                );
              })}
            </Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ClinicalRehabSchedule;
