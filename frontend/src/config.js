// Cấu hình URL backend tập trung
// Ưu tiên:
// 1. Biến môi trường VITE_API_URL (khi cấu hình trên Vercel / Render / Netlify)
// 2. Tự động nhận diện nếu đang chạy trên cloud (domain khác localhost) -> trỏ về Render backend
// 3. Chạy localhost dev máy -> trỏ về http://localhost:8000
const isBrowser = typeof window !== "undefined";
const isLocalhost = isBrowser && (
  window.location.hostname === "localhost" || 
  window.location.hostname === "127.0.0.1" ||
  window.location.hostname.endsWith(".local")
);

export const API_BASE_URL = (
  import.meta.env.VITE_API_URL || 
  (isBrowser && !isLocalhost ? "https://fitbreak.onrender.com" : "http://localhost:8000")
).replace(/\/+$/, "");

export default API_BASE_URL;


