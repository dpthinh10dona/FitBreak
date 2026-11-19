import { API_BASE_URL } from '../config';
import { useState } from 'react';
import "../style/logOut.css";

const LogOut = ({ onLogoutSuccess }) => {
  const [loading, setLoading] = useState(false);

  const handleLogout = async () => {
    setLoading(true);
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 5000);
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');

    try {
      const response = await fetch(`${API_BASE_URL}/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: "include",
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error("Đăng xuất thất bại");
      }
    } catch (err) {
      // Thu hồi phiên phía máy chủ là best-effort. Người dùng vẫn phải có thể
      // đăng xuất khỏi thiết bị khi backend chậm, mất mạng hoặc lỗi CORS.
      console.warn('Không thể thu hồi phiên phía máy chủ:', err);
    } finally {
      window.clearTimeout(timeoutId);
      if (onLogoutSuccess) {
        onLogoutSuccess();
      }
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      className="log-out-btn"
      onClick={handleLogout}
      disabled={loading}
      title="Log out of your session"
    >
      <span className="log-out-icon">🚪</span>
      <span>{loading ? '...' : 'Log Out'}</span>
    </button>
  );
};

export default LogOut;
