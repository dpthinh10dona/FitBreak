"""
Document Parser Module for FitBreak RAG.
Converts PDF, DOCX, and Text documents to standardized Markdown.
"""

from app.services.document_parser.converter_registry import (
    register,
    get_converter,
    convert_document,
    is_supported,
)

# Import converters to trigger registration
from app.services.document_parser import pdf_converter  # noqa: F401
from app.services.document_parser import docx_converter  # noqa: F401
from app.services.document_parser import text_converter  # noqa: F401

__all__ = [
    "register",
    "get_converter",
    "convert_document",
    "is_supported",
]
