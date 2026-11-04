// Cấu hình URL backend tập trung
// Khi chạy production trên Vercel: lấy từ biến môi trường VITE_API_URL
// Khi chạy dev trên máy: tự fallback về http://localhost:8000
export const API_BASE_URL = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

export default API_BASE_URL;

