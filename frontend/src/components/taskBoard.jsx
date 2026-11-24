import { API_BASE_URL } from '../config';
import { useState, useEffect } from 'react';
import '../style/taskBoard.css';

const daysOfWeekMap = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const MINI_TASKS = [
  "Hít đất 10 cái",
  "Đi uống 1 cốc nước đầy",
  "Vươn vai và nhắm mắt thư giãn 2 phút",
  "Squat 15 cái",
  "Đi bộ quanh phòng 2 phút",
  "Giãn cơ vai và lưng 5 phút"
];


const getTodayDateKey = () => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const getCompletedExercisesToday = () => {
  try {
    const key = `completed_exercises_${getTodayDateKey()}`;
    return JSON.parse(localStorage.getItem(key) || '[]');
  } catch (e) {
    return [];
  }
};

const markExerciseCompletedToday = (exerciseId) => {
  try {
    const key = `completed_exercises_${getTodayDateKey()}`;
    const list = getCompletedExercisesToday();
    if (!list.includes(exerciseId)) {
      list.push(exerciseId);
      localStorage.setItem(key, JSON.stringify(list));
    }
  } catch (e) {}
};


const formatDayTimeRanges = (day, selectedTimeSlots = []) => {
  try {
    const slotsArray = selectedTimeSlots;
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
  } catch (e) {
    return '';
  }
};

const TaskBoard = ({ scheduleData, onUpdateCoins, onUpdateSchedule, selectedTimeSlots = [] }) => {
  const [todaySchedule, setTodaySchedule] = useState([]);
  const [todayName, setTodayName] = useState('');
  const [removingTasks, setRemovingTasks] = useState({});

  const POMODORO_TIME = 25 * 60;
  const [timeLeft, setTimeLeft] = useState(POMODORO_TIME);
  const [isRunning, setIsRunning] = useState(false);
  const [isBreak, setIsBreak] = useState(false);
  const [currentMiniTask, setCurrentMiniTask] = useState("");
  const [isCompletingMini, setIsCompletingMini] = useState(false);

  useEffect(() => {
    if ("Notification" in window && Notification.permission !== "granted") {
      Notification.requestPermission();
    }
  }, []);

  useEffect(() => {
    const currentDayKey = daysOfWeekMap[new Date().getDay()];
    setTodayName(currentDayKey);

    if (scheduleData && scheduleData[currentDayKey]) {
      setTodaySchedule(JSON.parse(JSON.stringify(scheduleData[currentDayKey])));
    } else {
      setTodaySchedule([]);
    }
  }, [scheduleData]);

  useEffect(() => {
    let interval = null;
    if (isRunning && timeLeft > 0) {
      interval = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    } else if (isRunning && timeLeft === 0) {
      setIsRunning(false);
      setIsBreak(true);
      
      const randomTask = MINI_TASKS[Math.floor(Math.random() * MINI_TASKS.length)];
      setCurrentMiniTask(randomTask);
      
      if ("Notification" in window && Notification.permission === "granted") {
        new Notification("Hết 25 phút rồi! 🔥", {
          body: `Tới lúc nghỉ ngơi. Hãy đứng lên và: ${randomTask}`,
          icon: "/favicon.ico"
        });
      }
    }
    return () => clearInterval(interval);
  }, [isRunning, timeLeft]);

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleMiniTaskComplete = async () => {
    setIsCompletingMini(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/exercises-log`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          exercise_id: "mini_break_task",
          completed_at: new Date().toISOString(),
          reward_coins: 2
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (onUpdateCoins) {
          onUpdateCoins(data.new_coins);
        }
        setIsBreak(false);
        setTimeLeft(POMODORO_TIME);

        window.dispatchEvent(new CustomEvent('raid:boss-updated', { detail: data.boss }));
      } else {
        console.error("Lỗi server khi hoàn thành mini task");
      }
    } catch (error) {
      console.error("Lỗi kết nối:", error);
    } finally {
      setIsCompletingMini(false);
    }
  };

  const handleTaskComplete = async (slotIndex, exIndex, exerciseItem) => {
    const taskId = `${slotIndex}-${exIndex}`;
    setRemovingTasks((prev) => ({ ...prev, [taskId]: true }));

    const safeExerciseId = String(exerciseItem.id || exerciseItem.exercise || exerciseItem.name || '0');
    const alreadyRewardedToday = getCompletedExercisesToday().includes(safeExerciseId);
    const rewardCoins = alreadyRewardedToday ? 0 : (exerciseItem.reward_coins || 10);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/exercises-log`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          exercise_id: safeExerciseId,
          completed_at: new Date().toISOString(),
          reward_coins: rewardCoins
        })
      });

      if (response.ok) {
        const data = await response.json();
        markExerciseCompletedToday(safeExerciseId);

        if (rewardCoins > 0 && onUpdateCoins) {
          onUpdateCoins(data.new_coins);
        }

        setTimeout(() => {
          let fullSchedule = scheduleData ? JSON.parse(JSON.stringify(scheduleData)) : {};
          const currentDayKey = daysOfWeekMap[new Date().getDay()];
          
          if (fullSchedule[currentDayKey] && fullSchedule[currentDayKey][slotIndex]) {
            fullSchedule[currentDayKey][slotIndex].exercises = fullSchedule[currentDayKey][slotIndex].exercises.filter((_, idx) => idx !== exIndex);
          }

          if (onUpdateSchedule) {
            onUpdateSchedule(fullSchedule);
          }
          
          setTodaySchedule(fullSchedule[currentDayKey] || []);

          if (data.boss) {
            window.dispatchEvent(new CustomEvent('raid:boss-updated', { detail: data.boss }));
          }
        }, 300);
      } else {
        setRemovingTasks((prev) => ({ ...prev, [taskId]: false }));
      }
    } catch (error) {
      console.error('Lỗi khi gửi dữ liệu hoàn thành:', error);
      setRemovingTasks((prev) => ({ ...prev, [taskId]: false }));
    }
  };

  return (
    <div className="taskboard-page-wrapper">
      <div className="pomodoro-sidebar">
        <div className="pomodoro-header-row">
          <span className="pomodoro-badge">NHỊP ĐỘ LÀM VIỆC</span>
          <h3>Pomodoro Phục Hồi</h3>
        </div>

        {!isBreak ? (
          <div className="timer-section">
            <div className="timer-display-wrapper">
              <div className={`timer-display ${isRunning ? 'timer-running' : ''}`}>
                {formatTime(timeLeft)}
              </div>
              <div className="timer-mode-tag">
                {isRunning ? 'Đang chạy' : 'Tạm dừng'}
              </div>
            </div>

            <p className="timer-desc">Tập trung làm việc. Nghỉ ngơi giải lao và vận động sau mỗi 25 phút.</p>

            <div className="timer-controls">
              <button 
                className={`btn-timer ${isRunning ? 'btn-pause' : 'btn-start'}`}
                onClick={() => {
                  if ("Notification" in window && Notification.permission !== "granted") {
                    Notification.requestPermission();
                  }
                  setIsRunning(!isRunning);
                }}
              >
                {isRunning ? 'Tạm dừng' : 'Bắt đầu'}
              </button>
              <button 
                className="btn-timer btn-reset"
                onClick={() => {
                  setIsRunning(false);
                  setTimeLeft(POMODORO_TIME);
                }}
              >
                Đặt lại
              </button>
            </div>
          </div>
        ) : (
          <div className="break-section fade-in">
            <div className="break-badge-alert">THỜI GIAN NGHỈ</div>
            <h4 className="break-title">Hết 25 phút làm việc</h4>
            <p className="break-task-text">Đứng lên và thực hiện vận động nhẹ:</p>
            <div className="highlight-task">{currentMiniTask}</div>
            <button 
              className="btn-complete-mini"
              disabled={isCompletingMini}
              onClick={handleMiniTaskComplete}
            >
              {isCompletingMini ? 'Đang ghi nhận...' : 'Đã hoàn thành (+2 Coins)'}
            </button>
            <button 
              className="btn-skip-mini"
              onClick={() => {
                setIsBreak(false);
                setTimeLeft(POMODORO_TIME);
              }}
            >
              Bỏ qua lần này
            </button>
          </div>
        )}
      </div>

      <div className="taskboard-container">
        <div className="taskboard-header">
          <div className="taskboard-header-content">
            <h2>Kế hoạch vận động trong ngày</h2>
            <span className="taskboard-day-chip">{todayName}</span>
          </div>
        </div>

        {todaySchedule.length === 0 ? (
          <div className="empty-schedule-card">
            <h3>Chưa có lịch vận động hôm nay</h3>
            <p>Vui lòng chuyển sang mục Lịch Trình Vận Động để đăng ký khung giờ rảnh và tạo lịch phục hồi.</p>
          </div>
        ) : (
          todaySchedule.map((slot, slotIndex) => {
            const hasExercises = slot.exercises && slot.exercises.length > 0;

            if (slot.day_type === 'Rest') {
              return (
                <div key={slotIndex} className="rest-day-card">
                  <h3>Hôm nay là ngày nghỉ phục hồi</h3>
                  <p>Dành thời gian nghỉ ngơi để cơ bắp tái tạo và thư giãn cột sống.</p>
                </div>
              );
            }

            if (!hasExercises) {
              return (
                <div key={slotIndex} className="completed-block">
                  <h3>Đã hoàn tất toàn bộ bài tập trong mục này</h3>
                  <p>Bạn đã duy trì thói quen vận động rất tốt hôm nay.</p>
                </div>
              );
            }

            return (
              <div key={slotIndex} className="workout-block">
                <div className="block-title">
                  <div className="block-title-main">
                    <h3>Phân nhóm: <span className="highlight-type">{(slot.day_type || '').replace('_', ' ').toUpperCase()}</span></h3>
                  </div>
                  {(() => {
                    const timeRange = formatDayTimeRanges(todayName, selectedTimeSlots);
                    return timeRange ? (
                      <span className="block-time-badge">{timeRange}</span>
                    ) : (
                      <span className="block-time-badge">{slot.total_time} / {slot.slot_budget} phút</span>
                    );
                  })()}
                </div>

                <div className="exercise-list">
                  {slot.exercises.map((item, exIndex) => {
                    const taskId = `${slotIndex}-${exIndex}`;
                    const isRemoving = !!removingTasks[taskId];

                    const exerciseTitle = item.exercise || item.name || item.exercise_name || "Bài tập";
                    const bodyPart = item.body_part || "Toàn thân";
                    const duration = item.time_need || 0;
                    const level = item["level of physical activity"] || item.level || "Vừa";

                    return (
                      <div key={taskId} className={`exercise-card ${isRemoving ? 'fade-out' : ''}`}>
                        <div className="exercise-checkbox-wrapper">
                          <input
                            type="checkbox"
                            id={`chk-${taskId}`}
                            className="exercise-checkbox"
                            checked={false}
                            onChange={() => handleTaskComplete(slotIndex, exIndex, item)}
                          />
                        </div>
                        <div className="exercise-info">
                          <div className="exercise-header-row">
                            <h4>{exerciseTitle}</h4>
                            <span className="body-part-badge">{bodyPart}</span>
                          </div>
                          <div className="exercise-meta-row">
                            <span className="exercise-duration">Thời lượng: <b>{duration} phút</b></span>
                            <span className="exercise-meta-separator">•</span>
                            <span className="exercise-level">Cường độ: <span className="level-text">{level}</span></span>
                            <span className="exercise-meta-separator">•</span>
                            {(() => {
                                const safeExId = String(item.id || item.exercise || item.name || '0');
                                const isDoneToday = getCompletedExercisesToday().includes(safeExId);
                                return isDoneToday ? (
                                  <span className="exercise-reward-tag exercise-reward-claimed" title="Đã nhận thưởng hôm nay">Đã nhận thưởng</span>
                                ) : (
                                  <span className="exercise-reward-tag">+{item.reward_coins || 10} Coins</span>
                                );
                              })()}
                          </div>
                          {item.source_citation && (
                            <div className="exercise-source-citation">
                              Nguồn dữ liệu: {item.source_citation}.
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default TaskBoard;
