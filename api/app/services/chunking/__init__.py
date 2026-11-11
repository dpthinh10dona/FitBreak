"""
Document Chunking Module for FitBreak RAG.
Exports ChunkConfig, chunker registry, and registered chunkers for PDF, DOCX, and Text.
"""

from app.services.chunking.config import ChunkConfig
from app.services.chunking.structure import parse_markdown_units, pack_semantic_units
from app.services.chunking.chunker_registry import (
    register,
    get_chunker,
    chunk_document,
)

# Import chunkers to trigger registration
from app.services.chunking import pdf_chunker  # noqa: F401
from app.services.chunking import docx_chunker  # noqa: F401
from app.services.chunking import generic_chunker  # noqa: F401

__all__ = [
    "ChunkConfig",
    "parse_markdown_units",
    "pack_semantic_units",
    "register",
    "get_chunker",
    "chunk_document",
]
