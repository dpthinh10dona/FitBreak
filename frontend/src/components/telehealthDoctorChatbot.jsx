import { useState } from 'react';
import { API_BASE_URL } from '../config';
import '../style/telehealthChatbot.css';

/**
 * TelehealthDoctorChatbot Component (MedTech Standard)
 * Cửa sổ Bác sĩ Trực tuyến phong cách Telemedicine:
 * - Giao diện nền trắng lâm sàng, tông Medical Blue tạo sự tin cậy và thư thái.
 * - Hạn chế tối đa dưới 100 từ / câu và tối đa 3 câu hỏi / ngày.
 * - Hiển thị Card xác nhận đề xuất y khoa (Verification Proposal) trước khi lưu vào Supabase.
 * - Tự động reload lại Header khi người dùng xác nhận cập nhật thông tin sức khỏe.
 */
const TelehealthDoctorChatbot = ({ user, onProfileUpdated }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Kính chào bạn! Tôi là Bác sĩ Trợ lý Y khoa FitBreak. Bạn đang gặp phải triệu chứng, vấn đề tiêu hóa, xương khớp hay cần tư vấn điều chỉnh chế độ sinh hoạt như thế nào?',
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [remainingQuestions, setRemainingQuestions] = useState(3);
  const [activeProposal, setActiveProposal] = useState(null);

  const getWordCount = (str) => {
    return str.trim() ? str.trim().split(/\s+/).length : 0;
  };

  const getAuthToken = () => {
    let t = localStorage.getItem('token') || localStorage.getItem('access_token');
    if (!t && user) {
      t = user.token || user.access_token;
    }
    if (!t) {
      try {
        const u = JSON.parse(localStorage.getItem('user') || '{}');
        t = u?.token || u?.access_token;
      } catch (e) {}
    }
    if (t && !localStorage.getItem('token')) {
      localStorage.setItem('token', t);
    }
    return t;
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    const trimmed = inputMessage.trim();
    if (!trimmed || loading) return;

    const wordCount = getWordCount(trimmed);
    if (wordCount > 100) {
      alert(`Câu hỏi của bạn hiện có ${wordCount} từ. Để đảm bảo tính chính xác và súc tích trong y khoa, vui lòng rút gọn dưới 100 từ!`);
      return;
    }

    if (remainingQuestions <= 0) {
      alert('Bạn đã sử dụng hết 3 lượt tư vấn y tế miễn phí hôm nay. Vui lòng quay lại vào ngày mai!');
      return;
    }

    const token = getAuthToken();
    if (!token && !user?.email) {
      alert('Vui lòng đăng nhập để kết nối với Bác sĩ Trợ lý.');
      return;
    }

    const newMessages = [...messages, { role: 'user', content: trimmed }];
    setMessages(newMessages);
    setInputMessage('');
    setLoading(true);

    try {
      const headers = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE_URL}/chatbot/ask`, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({
          message: trimmed,
          history: newMessages.slice(-5)
        })
      });

      const data = await response.json();
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại để tiếp tục tư vấn với Bác sĩ.');
        }
        throw new Error(data.detail || 'Không thể kết nối đến hệ thống Bác sĩ AI.');
      }

      setRemainingQuestions(data.remaining_questions_today);

      const botMsg = {
        role: 'assistant',
        content: data.reply,
        proposal: data.proposal
      };

      setMessages((prev) => [...prev, botMsg]);
      if (data.proposal && data.proposal.has_update) {
        setActiveProposal(data.proposal);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Thông báo y tế: ${err.message}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmProposal = async (proposal) => {
    const token = getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/chatbot/confirm-update`, {
        method: 'POST',
        headers,
        credentials: 'include',
        body: JSON.stringify({
          food_recommendation: proposal.food_recommendation,
          level_of_physical_activity: proposal.level_of_physical_activity
        })
      });

      const data = await res.json();
      if (data.success) {
        alert('✅ Đã cập nhật chỉ số sức khỏe của bạn vào hồ sơ cá nhân thành công!');
        setActiveProposal(null);
        if (onProfileUpdated) {
          onProfileUpdated();
        }
      } else {
        alert(data.message || 'Cập nhật thất bại.');
      }
    } catch (e) {
      alert('Lỗi cập nhật: ' + e.message);
    }
  };

  const handleDismissProposal = () => {
    setActiveProposal(null);
  };

  const currentWords = getWordCount(inputMessage);

  return (
    <div className="telehealth-widget" role="complementary" aria-label="Bác sĩ Trợ lý FitBreak">
      {!isOpen && (
        <button 
          className="telehealth-launcher-btn" 
          onClick={() => setIsOpen(true)}
          aria-label="Mở cửa sổ tư vấn bác sĩ trực tuyến"
        >
          <span aria-hidden="true">🩺</span>
          <span>Bác Sĩ Trực Tuyến</span>
          <span className="telehealth-badge-counter">{remainingQuestions}/3</span>
        </button>
      )}

      {isOpen && (
        <div className="telehealth-window" role="dialog" aria-modal="true">
          {/* Header */}
          <div className="telehealth-header">
            <div className="doctor-identity-meta">
              <div className="doctor-avatar-circle" aria-hidden="true">
                👨‍⚕️
              </div>
              <div className="doctor-text-info">
                <h4>FitBreak Health Doctor</h4>
                <span className="doctor-availability">Chuyên gia Y học Thể thao & Dinh dưỡng</span>
              </div>
            </div>
            <button 
              className="telehealth-close-btn" 
              onClick={() => setIsOpen(false)}
              aria-label="Đóng cửa sổ bác sĩ"
            >
              ✕
            </button>
          </div>

          {/* Message Thread */}
          <div className="telehealth-thread">
            {messages.map((m, idx) => (
              <div key={idx} className={`chat-bubble-clinical ${m.role}`}>
                <div>{m.content}</div>

                {/* Proposal Verification Card */}
                {m.proposal && m.proposal.has_update && (
                  <div className={`clinical-proposal-card ${m.proposal.conflict_detected ? 'has-conflict' : ''}`}>
                    <span className="proposal-heading">
                      {m.proposal.conflict_detected ? '⚠️ Cảnh Báo Xung Đột Dữ Liệu Y Tế' : '📋 Đề Xuất Cập Nhật Hồ Sơ Bệnh Án'}
                    </span>
                    {m.proposal.conflict_message && (
                      <p className="proposal-item" style={{ color: 'var(--med-danger)', fontWeight: 600 }}>
                        {m.proposal.conflict_message}
                      </p>
                    )}
                    {m.proposal.food_recommendation && (
                      <p className="proposal-item">
                        🥗 <strong>Chế độ ăn:</strong> {m.proposal.food_recommendation}
                      </p>
                    )}
                    {m.proposal.level_of_physical_activity && (
                      <p className="proposal-item">
                        🏋️ <strong>Cường độ vận động:</strong> {m.proposal.level_of_physical_activity}
                      </p>
                    )}
                    <p className="proposal-verification-question">
                      ❓ {m.proposal.verification_question}
                    </p>

                    {activeProposal === m.proposal && (
                      <div className="proposal-action-buttons">
                        <button 
                          className="btn-accept-proposal"
                          onClick={() => handleConfirmProposal(m.proposal)}
                        >
                          ✓ Xác nhận cập nhật
                        </button>
                        <button 
                          className="btn-decline-proposal"
                          onClick={handleDismissProposal}
                        >
                          ✕ Bỏ qua
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="doctor-thinking-indicator">
                <span>⚕️ Bác sĩ đang kiểm tra chỉ số và chẩn đoán...</span>
              </div>
            )}
          </div>

          {/* Footer Input */}
          <form className="telehealth-footer" onSubmit={handleSendMessage}>
            <div className="telehealth-quota-bar">
              <span>Hạn mức: <strong>{remainingQuestions}/3</strong> câu hỏi hôm nay</span>
              <span className={currentWords > 100 ? 'limit-warning' : ''}>
                {currentWords}/100 từ
              </span>
            </div>
            <div className="telehealth-input-group">
              <input
                type="text"
                className="telehealth-input-field"
                placeholder="Nhập triệu chứng, thuốc, thắc mắc y khoa..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                disabled={loading || remainingQuestions <= 0}
              />
              <button 
                type="submit" 
                className="telehealth-send-btn"
                disabled={loading || !inputMessage.trim() || currentWords > 100 || remainingQuestions <= 0}
              >
                Gửi
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default TelehealthDoctorChatbot;
