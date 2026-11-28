import { useState } from 'react';
import { API_BASE_URL } from '../config';
import MedicalDisclaimerModal, { AI_HEALTH_CONSENT_KEY } from './MedicalDisclaimerModal';
import DisclaimerBanner from './DisclaimerBanner';
import AiTransparencyBadge from './AiTransparencyBadge';
import '../style/healthChatbot.css';

const HealthChatbot = ({ user, onProfileUpdated }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [hasConsent, setHasConsent] = useState(() => {
    try {
      return localStorage.getItem(AI_HEALTH_CONSENT_KEY) === 'true';
    } catch {
      return false;
    }
  });
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Xin chào! Tôi là Trợ lý tra cứu thông tin sức khỏe FitBreak. Tôi có thể hỗ trợ tra cứu thông tin tham khảo về sức khỏe, dinh dưỡng và lịch tập phù hợp với bạn.',
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [remainingQuestions, setRemainingQuestions] = useState(3);
  const [activeProposal, setActiveProposal] = useState(null);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    const trimmed = inputMessage.trim();
    if (!trimmed || loading) return;

    const characterCount = trimmed.length;
    if (characterCount > 99) {
      alert(`Câu hỏi của bạn có ${characterCount} ký tự. Giới hạn tối đa là 99 ký tự mỗi câu!`);
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
          status_flag: proposal.level_of_physical_activity === 'light'
            ? 'restrict_heavy_exercise'
            : proposal.level_of_physical_activity
              ? 'maintain_activity'
              : 'nutrition_review'
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

  const currentCharacters = inputMessage.length;

  return (
    <div className="health-chatbot-widget">
      {!isOpen && (
        <button className="chatbot-toggle-btn" onClick={() => setIsOpen(true)}>
          <span>🩺</span>
          <span>Trợ Lý Sức Khỏe</span>
          <span className="chatbot-badge">{remainingQuestions}/3</span>
        </button>
      )}

      {isOpen && (
        <div className="chatbot-window">
          <MedicalDisclaimerModal
            isOpen={!hasConsent}
            onAccept={() => setHasConsent(true)}
          />
          <div className="chatbot-header">
            <div className="chatbot-header-title">
              <span className="chatbot-avatar-icon">👨‍⚕️</span>
              <div>
                <h4>Trợ Lý Tra Cứu Thông Tin Sức Khỏe</h4>
                <span className="chatbot-status">Sẵn sàng hỗ trợ tra cứu thông tin</span>
              </div>
            </div>
            <button className="chatbot-close-btn" onClick={() => setIsOpen(false)}>✕</button>
          </div>

          <div className="chatbot-messages">
            <DisclaimerBanner sticky={true} />
            {messages.map((m, idx) => (
              <div key={idx} className={`chat-bubble ${m.role}`}>
                <div>{m.content}</div>
                {m.role !== 'user' && <AiTransparencyBadge />}

                {/* Nếu tin nhắn có đề xuất cập nhật */}
                {m.proposal && m.proposal.has_update && (
                  <div className={`proposal-card ${m.proposal.conflict_detected ? 'conflict' : ''}`}>
                    <span className="proposal-title">
                      {m.proposal.conflict_detected ? 'Cảnh Báo Mâu Thuẫn Sức Khỏe' : 'Đề Xuất Cá Nhân Hóa Hồ Sơ'}
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
            {loading && <div className="chatbot-typing">Trợ lý AI đang tổng hợp thông tin...</div>}
          </div>

          <form className="chatbot-footer" onSubmit={handleSendMessage}>
            <div className="chatbot-limit-info">
              <span>Còn lại: <strong>{remainingQuestions}/3</strong> câu hỏi hôm nay</span>
              <span className={currentCharacters > 99 ? 'warning' : ''}>
                {currentCharacters}/99 ký tự
              </span>
            </div>
            <div className="chatbot-input-row">
              <input
                type="text"
                className="chatbot-input"
                placeholder="Nhập triệu chứng, bệnh lý..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                maxLength={99}
                disabled={loading || remainingQuestions <= 0}
              />
              <button 
                type="submit" 
                className="chatbot-send-btn"
                disabled={loading || !inputMessage.trim() || currentCharacters > 99 || remainingQuestions <= 0}
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

