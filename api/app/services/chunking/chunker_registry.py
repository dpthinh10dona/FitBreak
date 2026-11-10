"""
Chunker Registry for Document Chunking Pipeline.
Allows registering chunkers by file extension or document type.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Dict, List, Any, Optional, Union

from app.services.chunking.config import ChunkConfig

logger = logging.getLogger("chunking.registry")

# Map extension -> chunker: (markdown_text, source, config) -> list[dict]
_CHUNKER_REGISTRY: Dict[str, Callable[[str, str, Optional[ChunkConfig]], List[Dict[str, Any]]]] = {}


def register(extension: str):
    """
    Decorator to register a chunker function for a file extension.
    Example:
        @register(".docx")
        def chunk_docx_file(markdown_text: str, source: str, config: ChunkConfig | None = None) -> list[dict]:
            ...
    """
    norm_ext = extension.lower().strip()
    if norm_ext != "default" and not norm_ext.startswith("."):
        norm_ext = f".{norm_ext}"

    def decorator(fn: Callable[[str, str, Optional[ChunkConfig]], List[Dict[str, Any]]]):
        _CHUNKER_REGISTRY[norm_ext] = fn
        logger.debug(f"Đã đăng ký chunker cho: {norm_ext} -> {fn.__name__}")
        return fn

    return decorator


def get_chunker(extension_or_path: Union[str, Path]) -> Callable[[str, str, Optional[ChunkConfig]], List[Dict[str, Any]]]:
    """Retrieve registered chunker function for a given extension or file path."""
    if isinstance(extension_or_path, (str, Path)):
        p = Path(extension_or_path)
        ext = p.suffix.lower().strip()
        if not ext and str(extension_or_path).startswith("."):
            ext = str(extension_or_path).lower().strip()
    else:
        ext = ""

    if ext in _CHUNKER_REGISTRY:
        return _CHUNKER_REGISTRY[ext]

    if "default" in _CHUNKER_REGISTRY:
        return _CHUNKER_REGISTRY["default"]

    raise ValueError(
        f"Không tìm thấy chunker nào cho '{ext}' và không có default chunker. "
        f"Các chunker hiện có: {list(_CHUNKER_REGISTRY.keys())}"
    )


def chunk_document(
    markdown_text: str,
    source: str,
    extension: Optional[str] = None,
    config: Optional[ChunkConfig] = None,
) -> List[Dict[str, Any]]:
    """Chunks Markdown text using the appropriate chunker for source file type."""
    ext = extension or Path(source).suffix.lower()
    chunker = get_chunker(ext)
    return chunker(markdown_text, source, config)
