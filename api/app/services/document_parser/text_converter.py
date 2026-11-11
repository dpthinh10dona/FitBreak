"""
Text and Markdown Document Converter.
Reads .txt and .md files and passes them cleanly into the parsing pipeline.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Union

from app.services.document_parser.converter_registry import register


@register(".txt")
def txt_to_markdown(file_path: Union[str, Path], output_dir: Optional[str] = None) -> str:
    p = Path(file_path)
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        out_path = Path(output_dir) / f"{p.stem}.md"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

    return content


@register(".md")
def md_to_markdown(file_path: Union[str, Path], output_dir: Optional[str] = None) -> str:
    p = Path(file_path)
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        out_path = Path(output_dir) / f"{p.stem}.md"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

    return content
