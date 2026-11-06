import { useState } from 'react';
import { API_BASE_URL } from '../config';
import '../style/healthChatbot.css';

const HealthChatbot = ({ user, onProfileUpdated }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Xin chào! Tôi là Trợ lý Bác sĩ FitBreak. Tôi có thể giải đáp các thắc mắc về sức khỏe, triệu chứng hay bệnh lý của bạn và giúp bạn cá nhân hóa chế độ ăn, lịch tập phù hợp nhất.',
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [remainingQuestions, setRemainingQuestions] = useState(3);
  const [activeProposal, setActiveProposal] = useState(null);

  const getWordCount = (str) => {
    return str.trim() ? str.trim().split(/\s+/).length : 0;
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    const trimmed = inputMessage.trim();
    if (!trimmed || loading) return;

    const wordCount = getWordCount(trimmed);
    if (wordCount > 100) {
      alert(`Câu hỏi của bạn có ${wordCount} từ. Giới hạn tối đa dưới 100 từ mỗi câu!`);
      return;
    }

    if (remainingQuestions <= 0) {
      alert('Bạn đã dùng hết 3 câu hỏi tư vấn trong ngày hôm nay!');
      return;
    }

    const token = localStorage.getItem('token');
    if (!token) {
      alert('Vui lòng đăng nhập để sử dụng tính năng ChatBot Bác sĩ.');
      return;
    }

    const newMessages = [...messages, { role: 'user', content: trimmed }];
    setMessages(newMessages);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chatbot/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: trimmed,
          history: newMessages.slice(-5)
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Không thể kết nối đến Trợ lý Bác sĩ.');
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
          content: `⚠️ Lỗi: ${err.message}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmProposal = async (proposal) => {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      const res = await fetch(`${API_BASE_URL}/chatbot/confirm-update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          food_recommendation: proposal.food_recommendation,
          level_of_physical_activity: proposal.level_of_physical_activity
        })
      });

      const data = await res.json();
      if (data.success) {
        alert('🎉 Đã cập nhật hồ sơ cá nhân hóa của bạn lên Supabase thành công!');
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
    <div className="health-chatbot-widget">
      {!isOpen && (
        <button className="chatbot-toggle-btn" onClick={() => setIsOpen(true)}>
          <span>🩺</span>
          <span>Bác Sĩ AI</span>
          <span className="chatbot-badge">{remainingQuestions}/3</span>
        </button>
      )}

      {isOpen && (
        <div className="chatbot-window">
          <div className="chatbot-header">
            <div className="chatbot-header-title">
              <span className="chatbot-avatar-icon">👨‍⚕️</span>
              <div>
                <h4>FitBreak Health Doctor</h4>
                <span className="chatbot-status">Sẵn sàng chẩn đoán & tư vấn</span>
              </div>
            </div>
            <button className="chatbot-close-btn" onClick={() => setIsOpen(false)}>✕</button>
          </div>

          <div className="chatbot-messages">
            {messages.map((m, idx) => (
              <div key={idx} className={`chat-bubble ${m.role}`}>
                <div>{m.content}</div>

                {/* Nếu tin nhắn có đề xuất cập nhật */}
                {m.proposal && m.proposal.has_update && (
                  <div className={`proposal-card ${m.proposal.conflict_detected ? 'conflict' : ''}`}>
                    <span className="proposal-title">
                      {m.proposal.conflict_detected ? '⚠️ Cảnh Báo Mâu Thuẫn Sức Khỏe' : '💡 Đề Xuất Cá Nhân Hóa Hồ Sơ'}
                    </span>
                    {m.proposal.conflict_message && (
                      <p className="proposal-detail" style={{ color: '#fca5a5' }}>
                        {m.proposal.conflict_message}
                      </p>
                    )}
                    {m.proposal.food_recommendation && (
                      <p className="proposal-detail">
                        🥗 <strong>Dinh dưỡng:</strong> {m.proposal.food_recommendation}
                      </p>
                    )}
                    {m.proposal.level_of_physical_activity && (
                      <p className="proposal-detail">
                        🏋️ <strong>Cường độ:</strong> {m.proposal.level_of_physical_activity}
                      </p>
                    )}
                    <p className="proposal-detail" style={{ fontStyle: 'italic', marginTop: '6px' }}>
                      ❓ {m.proposal.verification_question}
                    </p>

                    {activeProposal === m.proposal && (
                      <div className="proposal-actions">
                        <button 
                          className="btn-confirm-proposal"
                          onClick={() => handleConfirmProposal(m.proposal)}
                        >
                          ✓ Đồng ý cập nhật
                        </button>
                        <button 
                          className="btn-dismiss-proposal"
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
            {loading && <div className="chatbot-typing">Bác sĩ đang chẩn đoán và suy nghĩ...</div>}
          </div>

          <form className="chatbot-footer" onSubmit={handleSendMessage}>
            <div className="chatbot-limit-info">
              <span>Còn lại: <strong>{remainingQuestions}/3</strong> câu hỏi hôm nay</span>
              <span className={currentWords > 100 ? 'warning' : ''}>
                {currentWords}/100 từ
              </span>
            </div>
            <div className="chatbot-input-row">
              <input
                type="text"
                className="chatbot-input"
                placeholder="Nhập triệu chứng, bệnh lý..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                disabled={loading || remainingQuestions <= 0}
              />
              <button 
                type="submit" 
                className="chatbot-send-btn"
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

export default HealthChatbot;

