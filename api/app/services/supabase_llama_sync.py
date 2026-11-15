"""
Supabase & LlamaParse Automated Knowledge Pipeline for FitBreak Telehealth.
Orchestrates:
1. Uploading medical documents to Supabase Storage ("FitBreak Medical Knowledge" bucket).
2. Advanced parsing to clean Markdown via LlamaParse Cloud API (vietnamese language support).
3. Semantic hierarchical chunking via MarkdownNodeParser.
4. Automatic persistence to Supabase Database table ("medical_chunks").
"""

from __future__ import annotations

import os
import sys
import time
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Load environment variables
from dotenv import load_dotenv

# Tìm và nạp file .env từ api/app/.env hoặc từ thư mục gốc
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

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("FitBreak.LlamaParserSync")

# ==========================================
# CẤU HÌNH BIẾN MÔI TRƯỜNG (ENVIRONMENT KEYS)
# ==========================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
# Ưu tiên Service Role Key (để bypass RLS khi ghi Storage & DB lớn), fallback sang SUPABASE_KEY
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

LLAMA_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY") or os.getenv("LLAMA_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_MEDICAL_BUCKET", "FitBreak Medical Knowledge")
MEDICAL_CHUNKS_TABLE = os.getenv("MEDICAL_CHUNKS_TABLE", "medical_chunks")

# Kiểm tra thư viện Supabase
try:
    from supabase import create_client, Client
except ImportError:
    logger.error("Thư viện 'supabase' chưa được cài đặt. Vui lòng chạy: pip install supabase")
    sys.exit(1)

# Kiểm tra thư viện google.genai (cho text-embedding-004)
_HAS_GENAI = False
_genai_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        _genai_client = genai.Client(api_key=GEMINI_API_KEY)
        _HAS_GENAI = True
    except Exception as e:
        logger.debug(f"Không thể khởi tạo google.genai: {e}")

# Kiểm tra thư viện LlamaParse / LlamaCloud v2 & LlamaIndex
_HAS_LLAMA_CLOUD = False
_HAS_LLAMA_PARSE = False
try:
    from llama_cloud.client import LlamaCloud
    _HAS_LLAMA_CLOUD = True
except ImportError:
    pass

try:
    from llama_parse import LlamaParse
    _HAS_LLAMA_PARSE = True
except ImportError:
    pass

_HAS_LLAMA_INDEX = False
try:
    from llama_index.core.node_parser import MarkdownNodeParser
    from llama_index.core.schema import Document
    _HAS_LLAMA_INDEX = True
except ImportError:
    logger.warning("Thư viện 'llama-index-core' chưa được cài đặt. Vui lòng chạy: pip install llama-index-core")


class SupabaseLlamaSync:
    """
    Quản lý quy trình đồng bộ tự động giữa Supabase Storage, LlamaParse và Supabase Database.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        llama_api_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        table_name: Optional[str] = None,
        parser_engine: Optional[str] = None,
    ):
        self.supabase_url = supabase_url or SUPABASE_URL
        self.supabase_key = supabase_key or SUPABASE_KEY
        self.llama_api_key = llama_api_key or LLAMA_API_KEY
        self.bucket_name = bucket_name or SUPABASE_BUCKET
        self.table_name = table_name or MEDICAL_CHUNKS_TABLE
        self.parser_engine = (parser_engine or os.getenv("PARSER_ENGINE", "local")).lower()

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Thiếu SUPABASE_URL hoặc SUPABASE_KEY / SUPABASE_SERVICE_ROLE_KEY trong file .env!"
            )

        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self._ensure_bucket_exists()

    def is_document_processed(self, document_id: str) -> bool:
        """
        Cơ chế kiểm tra trùng lặp (Deduplication Check):
        Kiểm tra xem tệp tài liệu này đã từng được phân tích và lưu trong database Supabase hay chưa.
        Giúp tiết kiệm 100% quota lượt gọi LlamaParse và Embedding API khi chạy lại.
        """
        try:
            res = (
                self.client.table(self.table_name)
                .select("id")
                .eq("document_id", document_id)
                .limit(1)
                .execute()
            )
            return bool(res.data and len(res.data) > 0)
        except Exception as e:
            logger.debug(f"Không thể kiểm tra trạng thái tài liệu cũ ({e}).")
            return False

    def generate_embeddings(self, texts: List[str], batch_size: int = 20) -> List[Optional[List[float]]]:
        """
        Sinh vector 768 chiều bằng mô hình Google text-embedding-004.
        """
        if not _HAS_GENAI or not _genai_client:
            return [None] * len(texts)

        embeddings: List[Optional[List[float]]] = []
        logger.info(f"Đang tạo vector embedding (gemini-embedding-001, 768 chiều) cho {len(texts)} chunks...")

        # Cấu hình embedding chuyên biệt cho tài liệu (RETRIEVAL_DOCUMENT) và định dạng chuẩn 768 chiều
        from google.genai import types
        embed_config = types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=768,
        )

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            for text in batch_texts:
                vec = None
                for model_name in ["gemini-embedding-2", "gemini-embedding-001"]:
                    try:
                        res = _genai_client.models.embed_content(
                            model=model_name,
                            contents=text[:8000],  # Giới hạn an toàn context window
                            config=embed_config,
                        )
                        if res and res.embeddings:
                            raw_vals = res.embeddings[0].values
                            vec = raw_vals[:768] if len(raw_vals) > 768 else raw_vals
                            break
                    except Exception as e:
                        logger.debug(f"Thử model {model_name} không thành công: {e}")
                        continue
                embeddings.append(vec)

        return embeddings

    def _ensure_bucket_exists(self) -> None:
        """Kiểm tra và tạo bucket nếu chưa tồn tại trên Supabase Storage."""
        try:
            buckets = self.client.storage.list_buckets()
            bucket_names = [b.name for b in buckets] if buckets else []
            if self.bucket_name not in bucket_names:
                logger.info(f"Bucket '{self.bucket_name}' chưa tồn tại. Đang tạo bucket mới...")
                self.client.storage.create_bucket(self.bucket_name, options={"public": True})
                logger.info(f"Đã tạo bucket '{self.bucket_name}' thành công.")
        except Exception as e:
            logger.warning(f"Không thể kiểm tra/tạo bucket tự động ({e}). Sử dụng bucket mặc định: '{self.bucket_name}'.")

    def upload_file_to_storage(self, local_path: Path, remote_filename: Optional[str] = None) -> str:
        """
        Upload tệp tài liệu lên Supabase Storage bucket.
        Trả về URL công khai (Public URL) hoặc Signed URL của tệp.
        """
        p = Path(local_path)
        if not p.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {local_path}")

        file_name = remote_filename or p.name
        logger.info(f"Đang tải file '{file_name}' lên Supabase Storage bucket: [{self.bucket_name}]...")

        with open(p, "rb") as f:
            file_bytes = f.read()

        # Upload với cơ chế ghi đè (upsert)
        response = self.client.storage.from_(self.bucket_name).upload(
            path=file_name,
            file=file_bytes,
            file_options={"x-upsert": "true"},
        )

        # Lấy Public URL của tệp
        try:
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_name)
        except Exception:
            # Fallback nếu bucket là private: tạo signed URL có hạn 24 giờ
            public_url = self.client.storage.from_(self.bucket_name).create_signed_url(file_name, expires_in=86400).get("signedURL", "")

        logger.info(f"[+] Tải lên thành công! URL: {public_url}")
        return public_url

    def _extract_local_fallback(self, local_path: Path) -> str:
        """Trích xuất văn bản dự phòng nếu LlamaParse gặp sự cố hoặc trả về rỗng."""
        ext = local_path.suffix.lower()
        if ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(str(local_path))
                pages_text = []
                for idx, page in enumerate(reader.pages, 1):
                    t = page.extract_text() or ""
                    if t.strip():
                        pages_text.append(f"## Trang {idx}\n\n{t.strip()}")
                return "\n\n".join(pages_text)
            except Exception as e:
                logger.warning(f"Lỗi khi đọc PDF bằng pypdf: {e}")
        elif ext in [".txt", ".md"]:
            try:
                with open(local_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return ""

    def _extract_with_gemini(self, local_path: Path) -> str:
        """Trích xuất tài liệu sử dụng mô hình Google Gemini AI Vision mới nhất."""
        if not _HAS_GENAI or not _genai_client:
            logger.warning("Google GenAI client chưa khả dụng, chuyển sang local parser...")
            return self._extract_local_fallback(local_path)

        ext = local_path.suffix.lower()
        mime_map = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/markdown",
        }
        mime_type = mime_map.get(ext)
        if not mime_type:
            return self._extract_local_fallback(local_path)

        try:
            from google.genai import types
            with open(local_path, "rb") as f:
                file_bytes = f.read()

            gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
            logger.info(f"Đang gọi Google Gemini ({gemini_model}) phân tích nội dung tài liệu...")
            resp = _genai_client.models.generate_content(
                model=gemini_model,
                contents=[
                    types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                    "Bạn là chuyên gia y khoa số hóa tài liệu. Hãy trích xuất toàn bộ nội dung tài liệu sau thành Markdown tiếng Việt hoàn chỉnh, giữ nguyên cấu trúc tiêu đề (#, ##), danh sách và bảng biểu phác đồ."
                ]
            )
            return resp.text or ""
        except Exception as e:
            logger.warning(f"Lỗi khi gọi Gemini parsing ({e}), tự động chuyển sang local parser...")
            return self._extract_local_fallback(local_path)

    def parse_document(self, local_path: Path, public_url: Optional[str] = None) -> str:
        """
        Phân tích cú pháp tài liệu theo engine được chọn:
        - 'llama' hoặc 'v2' (mặc định cho Llama): LlamaParse v2 Parse API (llama_cloud client).
        - 'gemini': Google Gemini 3.1 Flash-Lite AI Vision hiện đại.
        - 'local': pypdf siêu tốc, chính xác, không phụ thuộc internet.
        """
        engine = self.parser_engine
        logger.info(f"Đang phân tích tài liệu '{local_path.name}' bằng engine [{engine.upper()}]...")

        if engine == "gemini":
            full_text = self._extract_with_gemini(local_path)
        elif engine in ("llama", "v2"):
            full_text = self.parse_document_with_llama_v2(local_path, public_url=public_url)
        else:  # 'local'
            full_text = self._extract_local_fallback(local_path)

        if not full_text.strip():
            logger.info("Dùng fallback trích xuất nội bộ để đảm bảo văn bản không bị rỗng...")
            full_text = self._extract_local_fallback(local_path)

        logger.info(f"[+] Trích xuất hoàn tất! Độ dài văn bản: {len(full_text):,} ký tự.")
        return full_text

    def parse_document_with_llama_v2(self, local_path: Path, public_url: Optional[str] = None) -> str:
        """
        Gọi LlamaParse v2 Parse API (thông qua llama_cloud.client.LlamaCloud).
        1. Tải file lên LlamaCloud qua files.upload_file().
        2. Tạo tác vụ phân tích v2 qua v_2.parse_file(tier='cost_effective', version='latest').
        3. Poll v_2.get_parse_job(expand='markdown') để nhận toàn bộ nội dung Markdown các trang.
        Tự động fallback về pypdf nếu token không hợp lệ hoặc gặp sự cố mạng.
        """
        full_text = ""
        if self.llama_api_key and _HAS_LLAMA_CLOUD:
            try:
                logger.info("Đang gửi tài liệu sang LlamaParse v2 API (LlamaCloud v2, tier: cost_effective)...")
                client = LlamaCloud(token=self.llama_api_key)
                
                with open(local_path, "rb") as f:
                    uploaded_file = client.files.upload_file(upload_file=f)
                
                logger.info(f"LlamaCloud File ID: {uploaded_file.id}. Đang khởi tạo v2 Parse Job...")
                job = client.v_2.parse_file(
                    file_id=uploaded_file.id,
                    tier="cost_effective",
                    version="latest",
                    output_options={"markdown": {}}
                )
                
                # Poll kết quả với timeout 120s
                max_polls = 60
                for poll_idx in range(max_polls):
                    res = client.v_2.get_parse_job(job_id=job.id, expand="markdown")
                    status_str = str(res.job.status).upper()
                    if "COMPLETED" in status_str or "SUCCESS" in status_str:
                        if hasattr(res, "markdown") and res.markdown and hasattr(res.markdown, "pages"):
                            pages = [p.markdown for p in res.markdown.pages if hasattr(p, "markdown") and p.markdown]
                            full_text = "\n\n".join(pages)
                        elif hasattr(res, "markdown") and isinstance(res.markdown, str):
                            full_text = res.markdown
                        logger.info(f"[+] LlamaParse v2 hoàn thành! Trích xuất được {len(full_text):,} ký tự.")
                        break
                    elif "FAIL" in status_str or "ERROR" in status_str:
                        logger.warning(f"LlamaParse v2 job báo lỗi: {res.job.error_message}")
                        break
                    
                    time.sleep(2)
            except Exception as e:
                logger.warning(f"LlamaParse v2 API gặp sự cố ({e}). Tự động chuyển sang fallback...")

        # Nếu LlamaParse v2 không trả về nội dung
        if not full_text.strip():
            logger.info("Kích hoạt bộ trích xuất nội bộ pypdf dự phòng...")
            full_text = self._extract_local_fallback(local_path)

        return full_text

    def chunk_markdown(self, full_markdown: str, source_name: str) -> List[Dict[str, Any]]:
        """
        Phân mảnh cấu trúc Markdown theo phân cấp đề mục (#, ##, ###) và đoạn văn.
        """
        chunks_data: List[Dict[str, Any]] = []

        if _HAS_LLAMA_INDEX:
            chunker = MarkdownNodeParser()
            nodes = chunker.get_nodes_from_documents([Document(text=full_markdown)])
            
            for idx, node in enumerate(nodes):
                content = node.text.strip()
                if not content:
                    continue

                heading_path = ""
                if hasattr(node, "metadata") and isinstance(node.metadata, dict):
                    heading_path = node.metadata.get("header_path") or node.metadata.get("heading") or ""

                chunks_data.append({
                    "id": f"{source_name}_chunk_{idx}",
                    "document_id": source_name,
                    "source_name": source_name,
                    "content": content,
                    "chunk_index": idx,
                    "heading_path": heading_path,
                    "char_count": len(content),
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                })
        else:
            # Fallback chunking theo đề mục regex nếu chưa cài llama-index-core
            logger.info("Sử dụng fallback markdown chunker...")
            sections = full_markdown.split("\n## ")
            for idx, sec in enumerate(sections):
                content = ("## " + sec if idx > 0 else sec).strip()
                if not content:
                    continue
                chunks_data.append({
                    "id": f"{source_name}_chunk_{idx}",
                    "document_id": source_name,
                    "source_name": source_name,
                    "content": content,
                    "chunk_index": idx,
                    "heading_path": content.split("\n")[0][:80],
                    "char_count": len(content),
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                })

        logger.info(f"[+] Đã chia thành {len(chunks_data)} semantic chunks.")
        return chunks_data

    def save_chunks_to_database(self, chunks: List[Dict[str, Any]], batch_size: int = 50) -> int:
        """
        Lưu các chunks vào bảng Database Supabase theo từng đợt (batch) an toàn.
        """
        if not chunks:
            logger.warning("Không có chunk nào để lưu.")
            return 0

        total_saved = 0
        total_chunks = len(chunks)

        logger.info(f"Đang lưu {total_chunks} chunks vào bảng '{self.table_name}' trên Supabase...")

        for i in range(0, total_chunks, batch_size):
            batch = chunks[i : i + batch_size]
            try:
                self.client.table(self.table_name).upsert(batch).execute()
                total_saved += len(batch)
                logger.info(f"  -> Đã lưu {total_saved}/{total_chunks} chunks...")
            except Exception as e:
                err_str = str(e)
                if "Could not find the 'embedding' column" in err_str or "PGRST204" in err_str:
                    logger.warning("Bảng 'medical_chunks' trên Supabase chưa có cột 'embedding' (vector). Đang lưu các trường văn bản (không kèm vector)...")
                    clean_batch = [{k: v for k, v in row.items() if k != "embedding"} for row in batch]
                    try:
                        self.client.table(self.table_name).upsert(clean_batch).execute()
                        total_saved += len(clean_batch)
                        logger.info(f"  -> Đã lưu {total_saved}/{total_chunks} chunks (dạng văn bản)...")
                        continue
                    except Exception as inner_err:
                        logger.error(f"Lỗi khi lưu batch text: {inner_err}")
                else:
                    logger.error(f"Lỗi khi lưu batch chunks {i} - {i+len(batch)}: {e}")

                # Thử lại từng record để không mất toàn bộ batch
                for row in batch:
                    try:
                        self.client.table(self.table_name).upsert(row).execute()
                        total_saved += 1
                    except Exception as row_err:
                        if "embedding" in str(row_err):
                            try:
                                clean_row = {k: v for k, v in row.items() if k != "embedding"}
                                self.client.table(self.table_name).upsert(clean_row).execute()
                                total_saved += 1
                                continue
                            except Exception:
                                pass
                        logger.error(f"  -> Lỗi lưu chunk [{row.get('id')}]: {row_err}")

        logger.info(f"[+] Hoàn tất lưu {total_saved}/{total_chunks} chunks vào Supabase Database!")
        return total_saved

    def process_and_save(self, file_path: str, remote_filename: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """
        Xử lý toàn diện một tệp:
        Kiểm tra trùng -> Upload Supabase Storage -> LlamaParse Markdown -> Markdown Chunker -> Embedding (text-embedding-004) -> Supabase DB.
        """
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

        file_name = remote_filename or path_obj.name

        # 0. CƠ CHẾ CHỐNG TRÙNG LẶP (DEDUPLICATION CHECK)
        if not force and self.is_document_processed(file_name):
            logger.info(f"[*] BỎ QUA: Tệp '{file_name}' ĐÃ ĐƯỢC XỬ LÝ & LƯU TRÊN SUPABASE TỪ TRƯỚC!")
            logger.info(f"    (Bỏ qua để tiết kiệm quota LlamaParse. Dùng cờ --force nếu muốn ép buộc xử lý lại).\n")
            return {
                "file_name": file_name,
                "status": "skipped",
                "reason": "already_processed",
            }

        start_time = time.time()
        logger.info(f"============================================================")
        logger.info(f"BẮT ĐẦU XỬ LÝ: {file_name}")
        logger.info(f"============================================================")

        # 1. Upload lên Supabase Storage
        public_url = self.upload_file_to_storage(path_obj, remote_filename=file_name)

        # 2. Phân tích văn bản qua Parser Engine được chọn (local / gemini / llama)
        markdown_text = self.parse_document(path_obj, public_url=public_url)

        # 3. Phân mảnh Markdown thành các node ngữ nghĩa
        chunks = self.chunk_markdown(markdown_text, source_name=file_name)
        for c in chunks:
            c["source_url"] = public_url

        # 4. Sinh vector ngữ nghĩa text-embedding-004 (nếu có Gemini API Key)
        if _HAS_GENAI and _genai_client:
            chunk_texts = [c["content"] for c in chunks]
            vectors = self.generate_embeddings(chunk_texts)
            for c, vec in zip(chunks, vectors):
                c["embedding"] = vec

        # 5. Lưu vào Supabase Database table
        saved_count = self.save_chunks_to_database(chunks)

        elapsed = time.time() - start_time
        logger.info(f"[SUCCESS] Hoàn tất xử lý tệp '{file_name}' trong {elapsed:.2f}s ({saved_count} chunks đã lưu)!\n")

        return {
            "file_name": file_name,
            "public_url": public_url,
            "chunks_count": saved_count,
            "elapsed_seconds": round(elapsed, 2),
            "status": "success",
        }

    def process_directory(self, dir_path: str, extensions: tuple = (".pdf", ".docx", ".md", ".txt"), force: bool = False) -> List[Dict[str, Any]]:
        """
        Quét và tự động đồng bộ toàn bộ tài liệu trong một thư mục lên Supabase.
        Tự động bỏ qua các file đã xử lý trước đó.
        """
        folder = Path(dir_path)
        if not folder.exists():
            raise FileNotFoundError(f"Thư mục không tồn tại: {dir_path}")

        files = [p for p in folder.iterdir() if p.suffix.lower() in extensions]
        logger.info(f"Tìm thấy {len(files)} tệp tài liệu hợp lệ trong '{dir_path}'.")

        results = []
        skipped_count = 0
        success_count = 0

        for f in files:
            try:
                res = self.process_and_save(str(f), force=force)
                results.append(res)
                if res.get("status") == "skipped":
                    skipped_count += 1
                else:
                    success_count += 1
            except Exception as e:
                logger.error(f"[FAILED] Không thể xử lý '{f.name}': {e}")

        logger.info(f"TỔNG KẾT: Đã xử lý mới: {success_count} | Bỏ qua (đã có từ trước): {skipped_count} / {len(files)} tệp.")
        return results


# ==========================================
# CLI EXECUTION ENTRYPOINT
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FitBreak - Đồng bộ tài liệu y khoa lên Supabase Storage và phân tích qua LlamaParse."
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Đường dẫn đến 1 tệp tài liệu cụ thể cần đồng bộ (.pdf, .docx, .md, .txt)",
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=str(Path(__file__).resolve().parents[1] / "core" / "dataset" / "medical_knowledge"),
        help="Thư mục chứa các tài liệu cần đồng bộ hàng loạt (mặc định: medical_knowledge)",
    )
    parser.add_argument(
        "--parser",
        type=str,
        choices=["v2", "llama", "local", "gemini"],
        default=os.getenv("PARSER_ENGINE", "v2"),
        help="Chọn công nghệ phân tích tài liệu: 'v2' / 'llama' (LlamaParse v2 Parse API mới nhất), 'local' (pypdf nội bộ siêu tốc), 'gemini' (Google Gemini AI Vision)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ép buộc xử lý và upload lại ngay cả khi file đã tồn tại trên Supabase Database.",
    )

    args = parser.parse_args()

    # In thông tin các key môi trường
    engine_desc = (
        "LlamaParse v2 Parse API (LlamaCloud v2)"
        if args.parser in ("v2", "llama")
        else ("Google Gemini 3.1 Flash-Lite AI Vision" if args.parser == "gemini" else "pypdf nội bộ siêu tốc (Không phụ thuộc API bên ngoài)")
    )
    print("=" * 65)
    print("FITBREAK SUPABASE DOCUMENT INGESTION PIPELINE")
    print("=" * 65)
    print(f"Parser Engine:   {args.parser.upper()} [{engine_desc}]")
    print(f"Supabase URL:    {SUPABASE_URL or '[Chưa cấu hình trong .env]'}")
    print(f"Supabase Key:    {'[Đã cấu hình]' if SUPABASE_KEY else '[CHƯA CÓ TRONG .ENV]'}")
    if args.parser in ("v2", "llama"):
        print(f"Llama Cloud Key: {'[Đã cấu hình]' if LLAMA_API_KEY else '[CHƯA CÓ TRONG .ENV]'}")
    print(f"Gemini Key:      {'[Đã cấu hình]' if GEMINI_API_KEY else '[Tùy chọn - Chưa có]'}")
    print(f"Target Bucket:   {SUPABASE_BUCKET}")
    print(f"Database Table:  {MEDICAL_CHUNKS_TABLE}")
    print(f"Chế độ Force:    {'BẬT (Ghi đè tất cả)' if args.force else 'TẮT (Tự động bỏ qua file đã có)'}")
    print("=" * 65)

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\n[!] LỖI: Vui lòng cấu hình SUPABASE_URL và SUPABASE_KEY / SUPABASE_SERVICE_ROLE_KEY trong file api/app/.env!")
        sys.exit(1)

    if args.parser in ("v2", "llama") and not LLAMA_API_KEY:
        print("\n[!] LỖI: Vui lòng cấu hình LLAMA_CLOUD_API_KEY (hoặc LLAMA_API_KEY) trong file .env khi dùng parser LlamaParse v2!")
        print("    Đăng ký lấy key miễn phí tại: https://cloud.llamaindex.ai\n")
        sys.exit(1)

    sync_service = SupabaseLlamaSync(parser_engine=args.parser)

    if args.file:
        sync_service.process_and_save(args.file, force=args.force)
    else:
        sync_service.process_directory(args.dir, force=args.force)
