"""
Converter Registry for Document Parsing Pipeline.
Allows registering and resolving file converters by file extension.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Dict, Union

logger = logging.getLogger("document_parser.registry")

# Map of extension (e.g. ".pdf", ".docx") -> converter callable: (file_path, output_dir) -> str (Markdown)
_CONVERTER_REGISTRY: Dict[str, Callable[[Union[str, Path], str], str]] = {}


def register(extension: str):
    """
    Decorator to register a document converter function for a specific extension.
    Example:
        @register(".docx")
        def docx_to_markdown(file_path: str | Path, output_dir: str) -> str:
            ...
    """
    norm_ext = extension.lower().strip()
    if not norm_ext.startswith("."):
        norm_ext = f".{norm_ext}"

    def decorator(fn: Callable[[Union[str, Path], str], str]):
        _CONVERTER_REGISTRY[norm_ext] = fn
        logger.debug(f"Đã đăng ký converter cho định dạng: {norm_ext} -> {fn.__name__}")
        return fn

    return decorator


def get_converter(extension_or_path: Union[str, Path]) -> Callable[[Union[str, Path], str], str]:
    """Retrieve registered converter function for a file path or extension."""
    if isinstance(extension_or_path, (str, Path)):
        p = Path(extension_or_path)
        ext = p.suffix.lower().strip()
        if not ext and str(extension_or_path).startswith("."):
            ext = str(extension_or_path).lower().strip()
    else:
        ext = ""

    if ext in _CONVERTER_REGISTRY:
        return _CONVERTER_REGISTRY[ext]

    raise ValueError(
        f"Không tìm thấy converter nào cho định dạng '{ext}'. "
        f"Các định dạng được hỗ trợ hiện tại: {list(_CONVERTER_REGISTRY.keys())}"
    )


def is_supported(extension_or_path: Union[str, Path]) -> bool:
    """Check if the given extension or file path is supported by any registered converter."""
    ext = Path(extension_or_path).suffix.lower().strip()
    return ext in _CONVERTER_REGISTRY


def convert_document(file_path: Union[str, Path], output_dir: Union[str, Path, None] = None) -> str:
    """
    Parse any supported document to Markdown string.
    If output_dir is provided, the Markdown content is also saved to a .md file there.
    """
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Không tìm thấy tệp tài liệu: {file_path}")

    out_dir_str = str(output_dir) if output_dir is not None else None
    converter = get_converter(p)
    return converter(p, out_dir_str)
