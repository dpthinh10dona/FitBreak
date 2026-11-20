import { useState, useEffect } from 'react';
import { API_BASE_URL } from './config';
import PatientHeader from './components/patientHeader';
import ProfileBanner from './components/profileBanner';
import LogIn from "./components/logIn";
import SignUp from "./components/signUp";
import UpdateProfile from './components/updateProfile';
import CreateProfile from "./components/createProfile";
import ClinicalNutritionModule from "./components/clinicalNutritionModule";
import ClinicalRehabSchedule from "./components/clinicalRehabSchedule";
import JoinTeam from "./components/joinTeam";
import TaskBoard from "./components/taskBoard";
import Shop from './components/shop';
import TelehealthDoctorChatbot from './components/telehealthDoctorChatbot';
import OnboardingTour from './components/onboardingTour';
import './App.css';

const getScheduleKey = (u) => (u?.email ? `workoutSchedule_${u.email}` : null);

const loadScheduleForUser = (u) => {
  const key = getScheduleKey(u);
  if (!key) return null;
  try {
    const saved = localStorage.getItem(key);
    return saved ? JSON.parse(saved) : null;
  } catch (e) {
    console.error("Lỗi parse lịch tập:", e);
    return null;
  }
};

const loadLegacySelectedSlots = () => {
  try {
    return JSON.parse(localStorage.getItem('selectedTimeSlots') || '[]');
  } catch {
    return [];
  }
};

function App() {
  const [currentScreen, setCurrentScreen] = useState('login');
  const [activeTab, setActiveTab] = useState('tasks');
  const [user, setUser] = useState(null);
  const [showCreateProfileModal, setShowCreateProfileModal] = useState(false);
  const [showOnboardingTour, setShowOnboardingTour] = useState(false);
  const [workoutSchedule, setWorkoutSchedule] = useState(null);
  const [selectedTimeSlots, setSelectedTimeSlots] = useState([]);
  const [authNotice, setAuthNotice] = useState('');
  const [avatarVersion, setAvatarVersion] = useState(0);

  const handleAvatarUpdated = () => {
    setAvatarVersion((prev) => prev + 1);
  };
  const fetchUserProfileByEmail = async (email, token) => {
    if (!email || !token) return null;
    try {
      const response = await fetch(`${API_BASE_URL}/profiles/get-profile-by-email/${email}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        setUser(null);
        setCurrentScreen('login');
        return undefined;
      }

      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error("Lá»—i khi láº¥y thÃ´ng tin profile:", error);
      return null;
    }
  };

  const fetchUserStats = async (token) => {
    if (!token) return null;
    try {
      const response = await fetch(`${API_BASE_URL}/get-stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        return await response.json();
      }
      return null;
    } catch (error) {
      console.error("Lá»—i khi láº¥y thÃ´ng tin stats:", error);
      return null;
    }
  };

  const saveScheduleToServer = async (schedule, slots, tokenOverride) => {
    const token = tokenOverride || localStorage.getItem('token') || localStorage.getItem('access_token');
    if (!token) return false;
    const response = await fetch(`${API_BASE_URL}/user-schedules/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        workout_schedule: schedule || {},
        selected_time_slots: Array.isArray(slots) ? slots : [],
      }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Không thể lưu lịch tập');
    }
    return true;
  };

  const loadScheduleFromServer = async (token, userObj) => {
    if (!token) return { schedule: null, slots: [] };
    try {
      const response = await fetch(`${API_BASE_URL}/user-schedules/me`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Không thể tải lịch tập');
      const data = await response.json();
      let schedule = data.workout_schedule;
      let slots = data.selected_time_slots || [];

      if (!schedule || Object.keys(schedule).length === 0) {
        const legacySchedule = loadScheduleForUser(userObj);
        const legacySlots = loadLegacySelectedSlots();
        if (legacySchedule) {
          schedule = legacySchedule;
          slots = legacySlots;
          await saveScheduleToServer(schedule, slots, token);
          const legacyKey = getScheduleKey(userObj);
          if (legacyKey) localStorage.removeItem(legacyKey);
          localStorage.removeItem('workoutSchedule');
          localStorage.removeItem('selectedTimeSlots');
        }
      }
      return {
        schedule: schedule && Object.keys(schedule).length > 0 ? schedule : null,
        slots,
      };
    } catch (error) {
      console.error('Lỗi đồng bộ lịch tập:', error);
      return {
        schedule: loadScheduleForUser(userObj),
        slots: loadLegacySelectedSlots(),
      };
    }
  };

  useEffect(() => {
    const checkUserStatus = async () => {
      localStorage.removeItem('workoutSchedule');

      const savedUser = localStorage.getItem('user');
      const storedToken = localStorage.getItem('token') || localStorage.getItem('access_token');

      if (savedUser) {
        let parsedUser = null;
        try {
          parsedUser = JSON.parse(savedUser);
        } catch (e) {
          console.error("Lỗi parse user từ localStorage:", e);
        }

        const token = storedToken || parsedUser?.token || parsedUser?.access_token;

        if (token && parsedUser) {
          if (!localStorage.getItem('token')) {
            localStorage.setItem('token', token);
          }
          if (!localStorage.getItem('access_token')) {
            localStorage.setItem('access_token', token);
          }

          const [profile, stats, savedSchedule] = await Promise.all([
            fetchUserProfileByEmail(parsedUser.email, token),
            fetchUserStats(token),
            loadScheduleFromServer(token, parsedUser),
          ]);
          if (profile === undefined) return;

          // Nếu token đã hết hạn hoặc không hợp lệ -> đưa về trang đăng nhập
          setWorkoutSchedule(savedSchedule.schedule);
          setSelectedTimeSlots(savedSchedule.slots);

          const fullUserData = { 
            ...parsedUser, 
            ...profile, 
            ...stats, 
            token,
            access_token: token,
            hasProfile: !!profile 
          };

          setUser(fullUserData);
          localStorage.setItem('user', JSON.stringify(fullUserData));
          setCurrentScreen('main');
          setShowCreateProfileModal(!profile);

          const hasCompletedTour = localStorage.getItem('fitbreak_tour_completed');
          if (profile && !hasCompletedTour) {
            setShowOnboardingTour(true);
          }
        }
      }
    };

    checkUserStatus();
  // Khởi tạo phiên một lần; các hàm đồng bộ chỉ dùng token/user đã đọc tại thời điểm mount.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleAuthSuccess = async (data, isSignUp = false) => {
    const token = data?.access_token || data?.token;
    const userObj = data?.user;

    if (token) {
      localStorage.setItem('token', token);
      localStorage.setItem('access_token', token);
    }

    if (isSignUp) {
      if (!token) {
        setAuthNotice(data?.message || 'Đăng ký thành công. Vui lòng xác nhận email rồi đăng nhập.');
        setCurrentScreen('login');
        return;
      }
      const signedUpUser = { ...userObj, token, access_token: token, hasProfile: false };
      setUser(signedUpUser);
      localStorage.setItem('user', JSON.stringify(signedUpUser));
      setWorkoutSchedule(null);
      setSelectedTimeSlots([]);
      setCurrentScreen('main');
      setShowCreateProfileModal(true);
      return;
    }

    const [profile, stats] = await Promise.all([
      fetchUserProfileByEmail(userObj?.email, token),
      fetchUserStats(token)
    ]);
    if (profile === undefined) return;
    const savedSchedule = await loadScheduleFromServer(token, userObj);

    const fullUserData = {
      ...userObj,
      ...profile,
      ...stats,
      token,
      access_token: token,
      hasProfile: !!profile
    };

    setUser(fullUserData);
    localStorage.setItem('user', JSON.stringify(fullUserData));
    setWorkoutSchedule(savedSchedule.schedule);
    setSelectedTimeSlots(savedSchedule.slots);
    setCurrentScreen('main');
    setShowCreateProfileModal(!profile);

    const hasCompletedTour = localStorage.getItem('fitbreak_tour_completed');
    if (profile && !hasCompletedTour) {
      setShowOnboardingTour(true);
    }
  };

  const handleUpdateProfileSuccess = async (updatedData) => {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    const email = user?.email || updatedData?.email;
    const refreshedProfile = await fetchUserProfileByEmail(email, token);
    const newProfileInfo = refreshedProfile || updatedData?.profile || updatedData?.user || updatedData || {};

    setUser((prevUser) => {
      const newUserState = { ...prevUser, ...newProfileInfo };
      localStorage.setItem('user', JSON.stringify(newUserState));
      return newUserState;
    });
  };

  const handleCreateProfileSuccess = async (data) => {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    const [profile, stats] = await Promise.all([
      fetchUserProfileByEmail(user?.email, token),
      fetchUserStats(token),
    ]);
    const updatedUser = { ...user, ...(data?.user || {}), ...profile, ...stats, hasProfile: true };
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
    setShowCreateProfileModal(false);
    if (!localStorage.getItem('fitbreak_tour_completed')) setShowOnboardingTour(true);
  };

  const handleUpdateCoins = (newCoins) => {
    setUser((prevUser) => {
      const updatedUser = { ...prevUser, coins: newCoins };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      return updatedUser;
    });
  };

  const handleRefreshStats = async () => {
    const token = localStorage.getItem('token');
    const stats = await fetchUserStats(token);
    if (!stats) return;

    setUser((prevUser) => {
      const updatedUser = { ...prevUser, ...stats };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      return updatedUser;
    });
  };

  const handleUpdateSchedule = async (newSchedule) => {
    setWorkoutSchedule(newSchedule);
    try {
      await saveScheduleToServer(newSchedule, selectedTimeSlots);
    } catch (error) {
      console.error('Lỗi lưu thay đổi lịch:', error);
    }
  };

  const handleScheduleGenerated = async (newSchedule, slots = selectedTimeSlots) => {
    setWorkoutSchedule(newSchedule);
    setSelectedTimeSlots(slots);
    await saveScheduleToServer(newSchedule, slots);
    setActiveTab('schedule');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setWorkoutSchedule(null);
    setSelectedTimeSlots([]);
    setUser(null);
    setCurrentScreen('login');
  };

  if (currentScreen === 'main') {
    return (
      <div className="app-container">
        <PatientHeader 
          user={user} 
          onLogout={handleLogout} 
          activeTab={activeTab} 
          onSelectTab={setActiveTab} 
          onOpenTour={() => setShowOnboardingTour(true)}
        />
        
        <ProfileBanner 
          user={user} 
          teamName={user?.team || 1}
          token={localStorage.getItem('token') || localStorage.getItem('access_token')}
          avatarVersion={avatarVersion}
        />
        
        <div className="main-content">
          {activeTab === 'tasks' && (
            <TaskBoard 
              user={user} 
              scheduleData={workoutSchedule} 
              onUpdateCoins={handleUpdateCoins}
              onUpdateSchedule={handleUpdateSchedule}
              selectedTimeSlots={selectedTimeSlots}
            />
          )}
          {activeTab === 'profile' && (
            <UpdateProfile user={user} onUpdateProfileSuccess={handleUpdateProfileSuccess} />
          )}
          {activeTab === 'food' && <ClinicalNutritionModule user={user} />}
          {activeTab === 'schedule' && (
            <ClinicalRehabSchedule 
              scheduleData={workoutSchedule} 
              onScheduleGenerated={handleScheduleGenerated} 
              initialSelectedTimeSlots={selectedTimeSlots}
            />
          )}
          {activeTab === 'team' && <JoinTeam />}
          {activeTab === 'shop' && (
            <Shop 
              user={user} 
              onUpdateCoins={handleUpdateCoins} 
              onAvatarUpdated={handleAvatarUpdated}
              onStatsUpdated={handleRefreshStats}
            />
          )}
        </div>

        {showCreateProfileModal && (
          <CreateProfile 
            user={user}
            onCreateProfileSuccess={handleCreateProfileSuccess}
          />
        )}

        <OnboardingTour
          isOpen={showOnboardingTour}
          onClose={() => setShowOnboardingTour(false)}
          onNavigateTab={(tabId) => setActiveTab(tabId)}
          activeTab={activeTab}
        />

        <TelehealthDoctorChatbot 
          user={user} 
          onProfileUpdated={async () => {
            const token = localStorage.getItem('token');
            if (user?.email && token) {
              const updatedProfile = await fetchUserProfileByEmail(user.email, token);
              if (updatedProfile) {
                const newFull = { ...user, ...updatedProfile };
                setUser(newFull);
                localStorage.setItem('user', JSON.stringify(newFull));
              }
            }
          }} 
        />
      </div>
    );
  }

  if (currentScreen === 'signup') {
    return (
      <SignUp 
        onSignUpSuccess={(data) => handleAuthSuccess(data, true)}
        onGoToLogIn={() => setCurrentScreen('login')} 
      />
    );
  }

  return (
    <LogIn 
      onLoginSuccess={handleAuthSuccess} 
      onGoToSignUp={() => setCurrentScreen('signup')} 
      notice={authNotice}
    />
  );
}

export default App;
