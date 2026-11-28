import { API_BASE_URL } from '../config';
import { useState, useEffect } from 'react';
import "../style/joinTeam.css";

const JoinTeam = () => {
  const [teamMembers, setTeamMembers] = useState([]);
  const [teamInput, setTeamInput] = useState('');
  const [myTeamCode, setMyTeamCode] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);

  const fetchTeamMembers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      const response = await fetch(`${API_BASE_URL}/get-team`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        let errorMessage = `Lỗi ${response.status}: Không thể lấy dữ liệu`;
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
          errorMessage = errorData.detail[0].msg || JSON.stringify(errorData.detail);
        } else if (typeof errorData.detail === 'object' && errorData.detail !== null) {
          errorMessage = errorData.detail.message || JSON.stringify(errorData.detail);
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setTeamMembers(Array.isArray(data) ? data : [data]);
      const codeResponse = await fetch(`${API_BASE_URL}/my-team-code`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (codeResponse.ok) setMyTeamCode((await codeResponse.json()).invite_code);
      setError(null);
    } catch (err) {
      setError(err.message || "Đã xảy ra lỗi khi lấy dữ liệu.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTeamMembers();
  }, []);

  const handleJoinTeam = async (e) => {
    e.preventDefault();
    if (!teamInput.trim()) {
      alert("Vui lòng nhập mã đội!");
      return;
    }

    try {
      setJoining(true);
      const token = localStorage.getItem('token');

      const response = await fetch(`${API_BASE_URL}/join-team`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ invite_code: teamInput.trim() }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Không thể gia nhập team!");
      }

      alert("Tham gia team thành công!");
      setTeamInput('');
      fetchTeamMembers();
    } catch (err) {
      alert(`Lỗi: ${err.message}`);
    } finally {
      setJoining(false);
    }
  };

  return (
    <div className="join-team-wrapper">
      <div className="join-team-header-section">
        <div className="join-title-group">
          <h2>Đội Ngũ Luyện Tập (Team Roster)</h2>
          <p>Mời đồng đội cùng tham gia Guild để cùng hợp sức đánh Boss và tăng sức mạnh!</p>
          {myTeamCode != null && <p>Mã mời đội của bạn: <strong>{myTeamCode}</strong></p>}
        </div>

        <form className="join-form" onSubmit={handleJoinTeam}>
          <div className="join-input-box">
            <span className="join-input-icon">#</span>
            <input
              type="text"
              className="join-input"
              placeholder="Nhập mã mời đội để gia nhập..."
              value={teamInput}
              onChange={(e) => setTeamInput(e.target.value)}
            />
          </div>
          <button type="submit" className="join-btn" disabled={joining}>
            {joining ? "Đang xử lý..." : "Gia nhập Team"}
          </button>
        </form>
      </div>

      {loading ? (
        <div className="team-loading-state">
          <div className="team-spinner"></div>
          <span>Đang tải thông tin đội ngũ...</span>
        </div>
      ) : error ? (
        <div className="team-error-state">
          <span>⚠️ {error}</span>
        </div>
      ) : teamMembers.length === 0 ? (
        <div className="team-empty-state">
          <div className="team-empty-icon">👥</div>
          <h3>Chưa có thành viên nào trong team</h3>
          <p>Nhập mã đội ở trên để xây dựng Guild ngay!</p>
        </div>
      ) : (
        <div className="team-container">
          {teamMembers.map((member, index) => (
            <div key={member.id || index} className="profile-card">
              <div className="profile-index-badge">
                #{String(index + 1).padStart(2, '0')}
              </div>
              
              <div className="profile-info">
                <div className="profile-header-meta">
                  <h4 className="member-name">{member.nickname || 'Chiến Binh'}</h4>
                  <span className="member-goal-tag">🎯 {member.goal || 'Tập luyện'}</span>
                </div>

              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default JoinTeam;
