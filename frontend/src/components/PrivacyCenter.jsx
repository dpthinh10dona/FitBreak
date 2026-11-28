import React, { useState } from 'react';
import {
  ShieldCheck,
  Download,
  Eye,
  Code2,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { API_BASE_URL } from '../config';
import '../style/privacyCenter.css';

const PrivacyCenter = ({ onAccountDeleted }) => {
  const [exportData, setExportData] = useState(null);
  const [viewMode, setViewMode] = useState('table'); // 'table' | 'json'
  const [loadingExport, setLoadingExport] = useState(false);
  const [loadingClear, setLoadingClear] = useState(false);
  const [loadingDelete, setLoadingDelete] = useState(false);

  const [statusMessage, setStatusMessage] = useState(null); // { type: 'success' | 'error', text: string }
  const [showClearModal, setShowClearModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [confirmText, setConfirmText] = useState('');

  const getAuthHeaders = () => {
    const token =
      localStorage.getItem('access_token') ||
      localStorage.getItem('token') ||
      sessionStorage.getItem('access_token') ||
      '';
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  };

  // Chức năng 1: Xem & Tải xuống dữ liệu (Export JSON)
  const handleFetchExport = async () => {
    setLoadingExport(true);
    setStatusMessage(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/privacy/export`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Không thể tải dữ liệu cá nhân.');
      }
      const data = await res.json();
      setExportData(data);
      setStatusMessage({
        type: 'success',
        text: 'Đã tải dữ liệu cá nhân thành công.',
      });
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message });
    } finally {
      setLoadingExport(false);
    }
  };

  const handleDownloadJson = () => {
    if (!exportData) return;
    const dateStr = new Date().toISOString().split('T')[0];
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `my_health_data_${dateStr}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Chức năng 2: Xóa dữ liệu sức khỏe (Clear Health Logs)
  const handleClearHealthLogs = async () => {
    setLoadingClear(true);
    setStatusMessage(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/privacy/health-logs`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Không thể xóa nhật ký sức khỏe.');
      }
      const result = await res.json();
      setShowClearModal(false);

      // Cập nhật lại state UI ngay lập tức
      if (exportData) {
        setExportData((prev) => ({
          ...prev,
          data: {
            ...prev.data,
            vitals: [],
            health_states: [],
          },
        }));
      }

      setStatusMessage({
        type: 'success',
        text:
          result.message ||
          'Đã xóa nhật ký sinh hiệu và trạng thái sức khỏe. Tài khoản & XP được giữ nguyên.',
      });
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message });
    } finally {
      setLoadingClear(false);
    }
  };

  // Chức năng 3: Xóa vĩnh viễn tài khoản (Hard Delete)
  const handleDeleteAccount = async () => {
    if (confirmText !== 'XOA') return;
    setLoadingDelete(true);
    setStatusMessage(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/privacy/account`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Không thể xóa vĩnh viễn tài khoản.');
      }

      localStorage.clear();
      sessionStorage.clear();
      setShowDeleteModal(false);

      if (onAccountDeleted) {
        onAccountDeleted();
      } else {
        window.location.href = '/';
      }
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.message });
      setLoadingDelete(false);
    }
  };

  return (
    <div className="privacy-center-container">
      <div className="privacy-header">
        <div className="privacy-header-icon">
          <ShieldCheck size={24} />
        </div>
        <div>
          <h2>Quyền riêng tư &amp; Dữ liệu của tôi</h2>
          <p>
            Xem, tải xuống hoặc xóa dữ liệu cá nhân của bạn theo chuẩn minh bạch dữ liệu.
          </p>
        </div>
      </div>

      {statusMessage && (
        <div className={`privacy-alert ${statusMessage.type}`}>
          {statusMessage.type === 'success' ? (
            <CheckCircle2 size={18} />
          ) : (
            <XCircle size={18} />
          )}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* 1. Xem & Tải xuống dữ liệu */}
      <section className="privacy-card">
        <div className="privacy-card-header">
          <h3 className="privacy-card-title">
            <Eye size={18} />
            1. Xem &amp; Tải xuống dữ liệu (Export JSON)
          </h3>
          {exportData && (
            <div className="privacy-actions-row">
              <button
                type="button"
                className="privacy-btn privacy-btn-secondary"
                onClick={() =>
                  setViewMode((m) => (m === 'table' ? 'json' : 'table'))
                }
              >
                <Code2 size={15} />
                {viewMode === 'table' ? 'Xem JSON thô' : 'Xem bảng tóm tắt'}
              </button>
              <button
                type="button"
                className="privacy-btn privacy-btn-primary"
                onClick={handleDownloadJson}
              >
                <Download size={15} />
                Tải xuống tệp .JSON
              </button>
            </div>
          )}
        </div>

        <p className="privacy-card-desc">
          Kiểm tra toàn bộ dữ liệu hệ thống đang lưu trữ cho tài khoản của bạn (hồ sơ chỉ số, lịch tập, ghi chú sinh hiệu, trạng thái sức khỏe).
        </p>

        <button
          type="button"
          className="privacy-btn privacy-btn-primary"
          onClick={handleFetchExport}
          disabled={loadingExport}
        >
          <Eye size={15} />
          {loadingExport ? 'Đang tải dữ liệu...' : 'Xem dữ liệu của tôi'}
        </button>

        {exportData && viewMode === 'table' && (
          <div className="privacy-summary-grid">
            <div className="privacy-summary-item">
              <div className="privacy-summary-label">Email tài khoản</div>
              <div className="privacy-summary-value" style={{ fontSize: '0.9rem' }}>
                {exportData.email || '—'}
              </div>
            </div>
            <div className="privacy-summary-item">
              <div className="privacy-summary-label">Hồ sơ cá nhân</div>
              <div className="privacy-summary-value">
                {exportData.data?.profile?.length || 0} bản ghi
              </div>
            </div>
            <div className="privacy-summary-item">
              <div className="privacy-summary-label">Ghi chú sinh hiệu</div>
              <div className="privacy-summary-value">
                {exportData.data?.vitals?.length || 0} bản ghi
              </div>
            </div>
            <div className="privacy-summary-item">
              <div className="privacy-summary-label">Lịch tập luyện</div>
              <div className="privacy-summary-value">
                {exportData.data?.workouts?.length || 0} bản ghi
              </div>
            </div>
            <div className="privacy-summary-item">
              <div className="privacy-summary-label">Trạng thái sức khỏe</div>
              <div className="privacy-summary-value">
                {exportData.data?.health_states?.length || 0} bản ghi
              </div>
            </div>
          </div>
        )}

        {exportData && viewMode === 'json' && (
          <pre className="privacy-json-viewer">
            {JSON.stringify(exportData, null, 2)}
          </pre>
        )}
      </section>

      {/* 2. Xóa dữ liệu sức khỏe */}
      <section className="privacy-card">
        <div className="privacy-card-header">
          <h3 className="privacy-card-title">
            <Trash2 size={18} />
            2. Xóa dữ liệu sức khỏe (Clear Health Logs)
          </h3>
        </div>
        <p className="privacy-card-desc">
          Xóa sạch lịch sử sinh hiệu, ghi chú chỉ số cá nhân và trạng thái cảnh báo sức khỏe. Tài khoản đăng nhập, Nickname, Avatar và điểm thưởng XP vẫn được giữ nguyên.
        </p>
        <button
          type="button"
          className="privacy-btn privacy-btn-warning"
          onClick={() => setShowClearModal(true)}
          disabled={loadingClear}
        >
          <Trash2 size={15} />
          Xóa dữ liệu sức khỏe
        </button>
      </section>

      {/* 3. Xóa vĩnh viễn tài khoản */}
      <section className="privacy-card danger-zone">
        <div className="privacy-card-header">
          <h3 className="privacy-card-title" style={{ color: 'var(--med-danger, #be123c)' }}>
            <AlertTriangle size={18} />
            3. Xóa vĩnh viễn tài khoản &amp; toàn bộ dữ liệu
          </h3>
        </div>
        <p className="privacy-card-desc">
          Hành động này sẽ xóa đồng bộ toàn bộ dữ liệu của bạn khỏi PostgreSQL và xóa vĩnh viễn tài khoản khỏi hệ thống xác thực. Không thể hoàn tác.
        </p>
        <button
          type="button"
          className="privacy-btn privacy-btn-danger"
          onClick={() => {
            setConfirmText('');
            setShowDeleteModal(true);
          }}
        >
          <AlertTriangle size={15} />
          Xóa vĩnh viễn tài khoản
        </button>
      </section>

      {/* Modal xác nhận xóa dữ liệu sức khỏe */}
      {showClearModal && (
        <div className="privacy-modal-overlay" role="dialog" aria-modal="true">
          <div className="privacy-modal">
            <h3 style={{ color: 'var(--med-warning, #b45309)' }}>
              <AlertTriangle size={20} />
              Xác nhận xóa nhật ký sức khỏe
            </h3>
            <p>
              Bạn có chắc chắn muốn xóa toàn bộ lịch sử sinh hiệu và trạng thái sức khỏe? Nickname, Avatar và điểm XP của bạn sẽ được giữ nguyên.
            </p>
            <div className="privacy-modal-actions">
              <button
                type="button"
                className="privacy-btn privacy-btn-secondary"
                onClick={() => setShowClearModal(false)}
                disabled={loadingClear}
              >
                Hủy
              </button>
              <button
                type="button"
                className="privacy-btn privacy-btn-warning"
                onClick={handleClearHealthLogs}
                disabled={loadingClear}
              >
                {loadingClear ? 'Đang xóa...' : 'Xác nhận xóa'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Danger Modal xóa vĩnh viễn tài khoản */}
      {showDeleteModal && (
        <div className="privacy-modal-overlay" role="dialog" aria-modal="true">
          <div className="privacy-modal">
            <h3>
              <AlertTriangle size={20} />
              Cảnh báo: Xóa vĩnh viễn tài khoản
            </h3>
            <p>
              Hành động này <strong>không thể hoàn tác</strong>. Toàn bộ hồ sơ, lịch sử sinh hiệu, lịch tập luyện và tài khoản đăng nhập sẽ bị xóa vĩnh viễn.
            </p>
            <p>
              Vui lòng nhập chính xác <strong>XOA</strong> vào ô bên dưới để xác nhận:
            </p>
            <input
              type="text"
              className="privacy-modal-input"
              placeholder='Nhập "XOA" để xác nhận'
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
            />
            <div className="privacy-modal-actions">
              <button
                type="button"
                className="privacy-btn privacy-btn-secondary"
                onClick={() => setShowDeleteModal(false)}
                disabled={loadingDelete}
              >
                Hủy
              </button>
              <button
                type="button"
                className="privacy-btn privacy-btn-danger"
                disabled={confirmText !== 'XOA' || loadingDelete}
                onClick={handleDeleteAccount}
              >
                {loadingDelete ? 'Đang xóa...' : 'Xóa vĩnh viễn tài khoản'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PrivacyCenter;
