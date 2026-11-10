"""
Chunking Configuration for Document Ingestion Pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ChunkConfig:
    """Settings controlling how Markdown documents are partitioned into semantic chunks."""

    max_chunk_size: int = 800  # Kích thước ký tự tối đa cho mỗi chunk
    min_chunk_size: int = 120  # Kích thước ký tự tối thiểu để không tạo chunk vụn
    chunk_overlap: int = 150   # Độ chồng lấn giữa các chunk liên tiếp
    preserve_headings: bool = True  # Luôn giữ ngữ cảnh tiêu đề (Heading Path)
    preserve_tables: bool = True    # Giữ nguyên vẹn bảng biểu trong 1 chunk
    split_long_paragraphs: bool = True
    stop_words_separator: str = "\n\n"
