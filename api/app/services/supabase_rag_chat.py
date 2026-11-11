"""
FitBreak Stage 2: Retrieval & Chat Flow (RAG Vector Search + Gemini 3.1 Flash-Lite)
Pipeline:
1. User hỏi: Tiếp nhận câu hỏi triệu chứng/y khoa từ người dùng.
2. Vector hóa câu hỏi: Gọi Gemini text-embedding-004 với task_type="RETRIEVAL_QUERY" tạo vector 768 chiều.
3. Truy vấn ngữ nghĩa: Gọi RPC match_medical_chunks trên Supabase pgvector lấy top 3-5 chunks liên quan nhất.
4. Sinh câu trả lời: Tổng hợp bằng Gemini 3.1 Flash-Lite kèm trích dẫn tài liệu nguồn chính xác.
"""

from __future__ import annotations

import os
import sys
import time
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

# Load env paths
env_paths = [
    Path(__file__).resolve().parents[1] / ".env",          # api/app/.env
    Path(__file__).resolve().parents[2] / ".env",          # api/.env
    Path(__file__).resolve().parents[3] / ".env",          # root/.env
]
for ep in env_paths:
    if ep.exists():
        load_dotenv(ep)
        break
else:
    load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("FitBreak.RAGChat")

# CONFIG
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
EMBEDDING_MODELS = ["gemini-embedding-2", "gemini-embedding-001"]
PRIMARY_EMBEDDING_MODEL = "gemini-embedding-2"

# 1. Khởi tạo Supabase Client
try:
    from supabase import create_client, Client
    supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as exc:
    logger.error(f"Lỗi khởi tạo Supabase Client: {exc}")
    supabase_client = None

# 2. Khởi tạo Google GenAI Client
try:
    from google import genai
    from google.genai import types
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as exc:
    logger.error(f"Lỗi khởi tạo Google GenAI Client: {exc}")
    ai_client = None


# ==============================================================================
# BƯỚC 1 & 2: VECTOR HÓA CÂU HỎI (EMBED QUERY VỚI TASK_TYPE='RETRIEVAL_QUERY')
# ==============================================================================
def embed_query_vector(query_text: str) -> Optional[List[float]]:
    """
    Biến câu hỏi người dùng thành vector 768 chiều sử dụng mô hình Gemini Embedding
    (gemini-embedding-001 / text-embedding-004) với task_type="RETRIEVAL_QUERY"
    và output_dimensionality=768 để khớp chuẩn xác với cột vector(768) trên Supabase pgvector.
    """
    if not ai_client:
        logger.error("Chưa khởi tạo được Google GenAI Client. Kiểm tra GEMINI_API_KEY!")
        return None

    clean_query = query_text.strip()
    if not clean_query:
        return None

    config = types.EmbedContentConfig(
        task_type="RETRIEVAL_QUERY",
        output_dimensionality=768,
        title="Medical Telehealth User Query",
    )

    # Thử lần lượt các model embedding được hỗ trợ
    for model_name in EMBEDDING_MODELS:
        try:
            response = ai_client.models.embed_content(
                model=model_name,
                contents=clean_query,
                config=config,
            )
            if response and response.embeddings:
                values = response.embeddings[0].values
                # Đảm bảo đúng 768 chiều cho pgvector
                if len(values) > 768:
                    values = values[:768]
                return values
        except Exception as exc:
            logger.debug(f"Thử model {model_name} không thành công: {exc}")
            continue

    logger.error("Tất cả các model embedding (gemini-embedding-2, gemini-embedding-001) đều không khả dụng!")
    return None


# ==============================================================================
# BƯỚC 3: TRUY VẤN NGỮ NGHĨA COSINE SIMILARITY TRÊN SUPABASE PGVECTOR
# ==============================================================================
def search_medical_knowledge_pgvector(
    query_text: str,
    top_k: int = 4,
    match_threshold: float = 0.50,
) -> List[Dict[str, Any]]:
    """
    Thực thi tìm kiếm tương đồng ngữ nghĩa trên Supabase pgvector qua RPC match_medical_chunks.
    Trả về top 3 - 5 chunks liên quan nhất kèm điểm similarity và nguồn văn bản.
    """
    if not supabase_client:
        logger.error("Supabase client chưa sẵn sàng!")
        return []

    # 1. Sinh vector câu hỏi
    query_vector = embed_query_vector(query_text)
    if not query_vector:
        logger.warning("Không tạo được embedding vector cho câu hỏi.")
        return []

    # 2. Gọi hàm RPC trên Supabase
    try:
        res = supabase_client.rpc(
            "match_medical_chunks",
            {
                "query_embedding": query_vector,
                "match_threshold": match_threshold,
                "match_count": top_k,
            },
        ).execute()

        chunks = res.data or []
        logger.info(f"Đã tìm thấy {len(chunks)} chunks liên quan nhất từ Supabase pgvector (threshold >= {match_threshold}).")
        return chunks
    except Exception as exc:
        logger.error(f"Lỗi khi truy vấn vector match_medical_chunks trên Supabase: {exc}")
        return []


# ==============================================================================
# BƯỚC 4: SINH CÂU TRẢ LỜI BẰNG GEMINI 3.1 FLASH-LITE (PROMPT KÈM NGUỒN)
# ==============================================================================
RAG_TELEHEALTH_SYSTEM_PROMPT = """Bạn là Bác sĩ Trợ lý Ảo FitBreak Telehealth. 
Nhiệm vụ của bạn là trả lời câu hỏi của người bệnh/bác sĩ một cách CHÍNH XÁC, AN TOÀN, KHOA HỌC và DỄ HIỂU.

--- NGUYÊN TẮC RAG BẮT BUỘC (CRITICAL GUIDELINES) ---
1. TỔNG HỢP THEO TÀI LIỆU ĐƯỢC TRÍCH XUẤT:
   - Dùng các đoạn tài liệu y khoa chính thống được cung cấp làm căn cứ xác thực duy nhất.
   - Tuyệt đối giữ nguyên các số liệu định lượng, công thức tính và đơn vị y tế (ví dụ: mg/kg/lần, ml, calo, mmHg, g/ngày, mmol/L).

2. TRÍCH DẪN NGUỒN TÀI LIỆU (CITATIONS):
   - Cuối câu trả lời, luôn có mục "📚 Nguồn tài liệu tham khảo:" ghi rõ tên văn bản hoặc số Quyết định của Bộ Y Tế / Viện Dinh Dưỡng được trích xuất.

3. ĐẢM BẢO AN TOÀN Y TẾ:
   - Nếu phát hiện dấu hiệu nguy hiểm (sốt li bì, co giật, đau thắt ngực, khó thở cấp), lập tức đưa ra cảnh báo Cờ Đỏ (Red Flags) yêu cầu tới cơ sở y tế gần nhất.
   - Đưa ra lời nhắc nhở miễn trừ trách nhiệm y tế: Thông tin mang tính tham khảo lâm sàng, cần tuân thủ chỉ định trực tiếp từ bác sĩ điều trị.
"""

def generate_rag_response(
    user_query: str,
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    user_profile_context: Optional[str] = None,
    top_k: int = 4,
) -> Dict[str, Any]:
    """
    Tổng hợp câu trả lời hoàn chỉnh dựa trên câu hỏi và các chunks y khoa được trích xuất.
    """
    start_time = time.time()

    # Nếu chưa truyền chunks vào, tự động tìm kiếm từ pgvector
    if retrieved_chunks is None:
        retrieved_chunks = search_medical_knowledge_pgvector(user_query, top_k=top_k)

    # Định dạng các chunks thành ngữ cảnh bằng chứng y khoa
    context_blocks = []
    sources_cited = set()

    for idx, c in enumerate(retrieved_chunks, 1):
        source = c.get("source_name", "Tài liệu Y tế Bộ Y Tế")
        heading = c.get("heading_path") or "Thông tin lâm sàng"
        content = c.get("content", "").strip()
        sim = c.get("similarity", 0)
        sources_cited.add(source)

        context_blocks.append(
            f"[TRÍCH ĐOẠN {idx}] (Độ liên quan: {sim:.1%})\n"
            f"• Nguồn tài liệu: {source}\n"
            f"• Đề mục: {heading}\n"
            f"• Nội dung: {content}"
        )

    evidence_text = "\n\n".join(context_blocks) if context_blocks else "Không tìm thấy tài liệu liên quan trực tiếp trong kho tri thức."

    # Xây dựng Prompt hoàn chỉnh
    prompt = f"""{RAG_TELEHEALTH_SYSTEM_PROMPT}

=== BẰNG CHỨNG TÀI LIỆU Y KHOA ĐƯỢC TRÍCH XUẤT TỪ SUPABASE PGVECTOR ===
{evidence_text}

=== HỒ SƠ THỂ TRẠNG NGƯỜI BỆNH (NẾU CÓ) ===
{user_profile_context or "Chưa có thông tin hồ sơ cụ thể."}

=== CÂU HỎI CỦA NGƯỜI DÙNG ===
{user_query}

=== YÊU CẦU ĐẦU RA ===
Hãy trả lời câu hỏi trên theo định dạng Markdown chuẩn, rõ ràng, chính xác về liều lượng/đơn vị và trích dẫn rõ nguồn ở cuối câu trả lời.
"""

    if not ai_client:
        return {
            "answer": "Hệ thống AI hiện chưa được kết nối API Key. Vui lòng kiểm tra GEMINI_API_KEY.",
            "sources": list(sources_cited),
            "chunks_used": len(retrieved_chunks),
            "latency": 0,
        }

    try:
        config = types.GenerateContentConfig(
            temperature=0.3,  # Nhiệt độ thấp để đảm bảo độ chuẩn xác y khoa
            response_mime_type="text/plain",
        )
        response = ai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
        answer = response.text.strip() if response and response.text else "Không nhận được phản hồi từ AI."
    except Exception as exc:
        logger.error(f"Lỗi khi gọi Gemini {GEMINI_MODEL}: {exc}")
        answer = f"Đã xảy ra lỗi khi tạo câu trả lời y khoa: {exc}"

    elapsed = time.time() - start_time
    logger.info(f"[+] Hoàn tất RAG Chat trong {elapsed:.2f}s. Số nguồn trích dẫn: {len(sources_cited)}")

    return {
        "query": user_query,
        "answer": answer,
        "sources": list(sources_cited),
        "chunks_used": len(retrieved_chunks),
        "latency_seconds": round(elapsed, 2),
    }


# ==============================================================================
# CLI TEST TRỰC TIẾP
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FitBreak - Kiểm thử Giai đoạn 2: Retrieval & Chat Flow")
    parser.add_argument(
        "--query",
        type=str,
        default="Liều dùng Paracetamol cho trẻ 15kg sốt bao nhiêu?",
        help="Câu hỏi kiểm thử của người dùng",
    )
    parser.add_argument("--top_k", type=int, default=4, help="Số lượng chunks cần trích xuất (mặc định: 4)")
    args = parser.parse_args()

    print("=" * 70)
    print("FITBREAK TELEHEALTH RAG - STAGE 2: RETRIEVAL & CHAT FLOW")
    print("=" * 70)
    print(f"Câu hỏi: {args.query}\n")

    result = generate_rag_response(args.query, top_k=args.top_k)

    print("\n--- CÂU TRẢ LỜI CỦA BÁC SĨ AI (GEMINI 3.1 FLASH-LITE) ---")
    print(result["answer"])
    print("\n" + "=" * 70)
    print(f"Nguồn trích dẫn: {', '.join(result['sources']) if result['sources'] else 'Tri thức lâm sàng chuẩn'}")
    print(f"Số chunks đã dùng: {result['chunks_used']} | Thời gian phản hồi: {result['latency_seconds']}s")
    print("=" * 70)
