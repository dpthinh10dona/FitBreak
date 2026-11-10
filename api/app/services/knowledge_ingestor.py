"""
Knowledge Ingestor Pipeline for FitBreak Telehealth RAG.
Orchestrates document parsing, semantic chunking, metadata extraction,
and caching for medical knowledge bases.
"""

from __future__ import annotations

import os
import re
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from app.services.document_parser import convert_document, is_supported
from app.services.chunking import chunk_document, ChunkConfig

logger = logging.getLogger("knowledge_ingestor")

DEFAULT_KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "core" / "dataset" / "medical_knowledge"
CACHE_FILE_NAME = "chunks_cache.json"


class KnowledgeIngestor:
    """
    Manages ingesting, indexing, and retrieving medical knowledge chunks.
    Supports .docx, .pdf, .md, .txt.
    """

    def __init__(self, knowledge_dir: Optional[Union[str, Path]] = None, config: Optional[ChunkConfig] = None):
        self.knowledge_dir = Path(knowledge_dir or DEFAULT_KNOWLEDGE_DIR)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.knowledge_dir / CACHE_FILE_NAME
        self.config = config or ChunkConfig(max_chunk_size=750, min_chunk_size=100, chunk_overlap=120)
        self._chunks: List[Dict[str, Any]] = []
        self._loaded = False

    def ingest_file(self, file_path: Union[str, Path], save_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Parses a single document (.docx, .pdf, .md, .txt) and partitions it into RAG chunks.
        """
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Tệp tài liệu không tồn tại: {file_path}")

        if not is_supported(p):
            raise ValueError(f"Định dạng tệp '{p.suffix}' chưa được hỗ trợ bởi document parser.")

        logger.info(f"[Ingestor] Đang phân tích cú pháp tài liệu: {p.name}")
        markdown_text = convert_document(p)

        logger.info(f"[Ingestor] Đang phân mảnh (chunking) tài liệu: {p.name}")
        raw_chunks = chunk_document(markdown_text, source=str(p), config=self.config)

        # Xác định chuyên mục (category) từ thư mục con nếu có
        category = "chung"
        try:
            rel = p.resolve().relative_to(self.knowledge_dir.resolve())
            if len(rel.parts) > 1:
                category = rel.parts[0]
        except Exception:
            pass

        processed_chunks: List[Dict[str, Any]] = []
        for idx, chunk in enumerate(raw_chunks, 1):
            content = chunk.get("content", "").strip()
            if not content:
                continue

            metadata = chunk.get("metadata", {})
            metadata.setdefault("source_file", p.name)
            metadata.setdefault("file_type", p.suffix.lstrip(".").lower())
            metadata.setdefault("category", category)
            metadata.setdefault("ingested_at", time.strftime("%Y-%m-%d %H:%M:%S"))

            # Extract auto-keywords from content and headings
            keywords = self._extract_keywords(content, metadata.get("heading_path", ""))
            if category != "chung":
                cat_clean = category.replace("_", " ").replace("-", " ")
                if cat_clean not in keywords:
                    keywords.append(cat_clean)

            chunk_obj = {
                "id": f"{p.stem}_{idx}",
                "title": metadata.get("section_title") or metadata.get("heading_path") or p.stem,
                "source": p.name,
                "category": category,
                "heading_path": metadata.get("heading_path", ""),
                "content": content,
                "keywords": keywords,
                "metadata": metadata,
            }
            processed_chunks.append(chunk_obj)

        if save_cache:
            # Update cache with new chunks (replacing old chunks from same source file)
            self.load_chunks(force_reload=False)
            filtered = [c for c in self._chunks if c.get("source") != p.name]
            filtered.extend(processed_chunks)
            self._chunks = filtered
            self._save_cache()

        logger.info(f"[Ingestor] Hoàn tất nạp tệp {p.name}: tạo thành công {len(processed_chunks)} chunks.")
        return processed_chunks

    def ingest_directory(self, dir_path: Optional[Union[str, Path]] = None, force_rebuild: bool = False) -> List[Dict[str, Any]]:
        """
        Scans a directory for all supported documents (.docx, .pdf, .md, .txt) and ingests them.
        Hỗ trợ quét đệ quy qua TẤT CẢ thư mục con (Subfolders) để người dùng tự do phân loại.
        """
        target_dir = Path(dir_path or self.knowledge_dir)
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)

        supported_files: List[Path] = []
        for ext in [".docx", ".pdf", ".md", ".txt"]:
            # Dùng rglob để tự động quét xuyên qua mọi thư mục con
            supported_files.extend(list(target_dir.rglob(f"*{ext}")))
            supported_files.extend(list(target_dir.rglob(f"*{ext.upper()}")))

        # Deduplicate files, bỏ qua file tạm Word (~$) và chỉ lấy file thực sự
        unique_files = sorted(list({
            f.resolve() for f in supported_files
            if not f.name.startswith("~$") and f.is_file()
        }))

        if not unique_files:
            logger.warning(f"[Ingestor] Không tìm thấy tài liệu nào trong thư mục: {target_dir}")
            return []

        all_chunks: List[Dict[str, Any]] = []
        for file_p in unique_files:
            try:
                chunks = self.ingest_file(file_p, save_cache=False)
                all_chunks.extend(chunks)
            except Exception as exc:
                logger.error(f"[Ingestor] Lỗi khi xử lý tệp {file_p.name}: {exc}", exc_info=True)

        self._chunks = all_chunks
        self._save_cache()
        self._loaded = True
        logger.info(f"[Ingestor] Đã nạp toàn bộ thư mục: tổng cộng {len(self._chunks)} chunks từ {len(unique_files)} tài liệu.")
        return self._chunks

    def load_chunks(self, force_reload: bool = False) -> List[Dict[str, Any]]:
        """
        Loads pre-indexed chunks from cache if available; otherwise builds from directory.
        """
        if self._loaded and not force_reload:
            return self._chunks

        if self.cache_file.exists() and not force_reload:
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._chunks = json.load(f)
                self._loaded = True
                logger.info(f"[Ingestor] Đã tải {len(self._chunks)} chunks từ cache {self.cache_file.name}")
                return self._chunks
            except Exception as exc:
                logger.warning(f"[Ingestor] Lỗi đọc cache ({exc}), đang tiến hành quét lại thư mục...")

        return self.ingest_directory()

    def search_chunks(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Hybrid keyword & semantic overlap search over all indexed knowledge chunks.
        """
        chunks = self.load_chunks()
        if not chunks or not query:
            return []

        query_clean = query.lower()
        query_words = set(re.findall(r"\w+", query_clean))

        scored: List[tuple[float, Dict[str, Any]]] = []

        for chunk in chunks:
            score = 0.0
            content = chunk.get("content", "").lower()
            title = chunk.get("title", "").lower()
            heading_path = chunk.get("heading_path", "").lower()
            category = chunk.get("category", "").lower()
            keywords = [k.lower() for k in chunk.get("keywords", [])]

            # 0. Category match
            if category and category != "chung" and category in query_clean:
                score += 5.0

            # 1. Exact phrase matches in title or heading
            if query_clean in title or query_clean in heading_path:
                score += 8.0

            # 2. Keyword exact matches
            for kw in keywords:
                if kw in query_clean:
                    score += 4.0

            # 3. Heading words matching
            for qw in query_words:
                if len(qw) >= 2:
                    if qw in title:
                        score += 3.0
                    if qw in heading_path:
                        score += 2.0
                    # Content frequency bonus
                    count = content.count(qw)
                    if count > 0:
                        score += min(count * 0.5, 4.0)

            # 4. Critical clinical keyword weighting
            clinical_boosts = [
                "đau", "sốt", "dạ dày", "tiêu chảy", "cổ vai gáy", "lưng", "huyết áp",
                "tim mạch", "chóng mặt", "mỏi mắt", "dị ứng", "hạ đường huyết", "chuột rút"
            ]
            for cb in clinical_boosts:
                if cb in query_clean and cb in content:
                    score += 3.0

            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for score, c in scored[:top_k]]

    def _extract_keywords(self, content: str, heading_path: str) -> List[str]:
        """Extracts medical and health domain keywords from text."""
        combined = (heading_path + " " + content).lower()
        potential_terms = [
            "đau cổ", "đau vai", "cổ vai gáy", "đau thắt lưng", "đau lưng", "thoát vị đĩa đệm",
            "ống cổ tay", "chuột rút", "căng cơ", "đau cơ", "doms", "công thái học", "tư thế ngồi",
            "trào ngược dạ dày", "gerd", "ợ chua", "viêm dạ dày", "đau thượng vị", "tiêu hóa",
            "tiêu chảy", "mất nước", "điện giải", "chế độ brat", "hạ đường huyết", "tụt huyết áp",
            "tăng huyết áp", "tim mạch", "nhịp tim", "mỏi mắt", "thị giác màn hình", "20-20-20",
            "mất ngủ", "căng thẳng", "stress", "tdee", "calo", "protein", "béo phì", "dị ứng"
        ]
        found = [term for term in potential_terms if term in combined]
        return list(dict.fromkeys(found))

    def _save_cache(self) -> None:
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._chunks, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.error(f"[Ingestor] Không thể ghi file cache: {exc}")


# Singleton instance
default_ingestor = KnowledgeIngestor()


if __name__ == "__main__":
    import sys
    ingestor = KnowledgeIngestor()
    if len(sys.argv) > 1 and sys.argv[1] == "--rebuild":
        print("Đang quét và xây dựng lại cơ sở tri thức...")
        chunks = ingestor.ingest_directory(force_rebuild=True)
        print(f"Hoàn tất! Tổng cộng {len(chunks)} chunks.")
    elif len(sys.argv) > 2 and sys.argv[1] == "--ingest":
        target_file = sys.argv[2]
        print(f"Đang nạp tệp: {target_file}")
        chunks = ingestor.ingest_file(target_file)
        print(f"Nạp thành công {len(chunks)} chunks từ tệp.")
    else:
        print("Sử dụng:")
        print("  python -m app.services.knowledge_ingestor --rebuild")
        print("  python -m app.services.knowledge_ingestor --ingest <đường_dẫn_tệp>")
