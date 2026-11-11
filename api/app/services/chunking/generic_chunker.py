"""
Generic and Markdown Document Chunker.
Used for Markdown, Text files, and fallback for any unregistered document types.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.services.chunking.chunker_registry import register
from app.services.chunking.config import ChunkConfig
from app.services.chunking.structure import parse_markdown_units, pack_semantic_units


def chunk_generic_text(
    markdown_text: str,
    source: str,
    config: Optional[ChunkConfig] = None,
) -> List[Dict[str, Any]]:
    config = config or ChunkConfig()
    units = parse_markdown_units(markdown_text)
    packed_parts = pack_semantic_units(units, config)

    chunks: List[Dict[str, Any]] = []
    chunk_index = 0
    seen_hashes: set[str] = set()

    for part in packed_parts:
        content = part["content"].strip()
        if not content:
            continue

        content_hash = hashlib.sha1(content.casefold().encode("utf-8")).hexdigest()
        if content_hash in seen_hashes:
            continue
        seen_hashes.add(content_hash)

        chunk_index += 1
        heading_path = part.get("metadata", {}).get("heading_path", "")
        section_title = heading_path.split(" > ")[-1] if heading_path else Path(source).stem

        metadata: Dict[str, Any] = {
            "source_file": Path(source).name,
            "source_path": str(source),
            "doc_type": Path(source).suffix.lstrip(".").lower() or "text",
            "chunk_id": f"chunk_{chunk_index}",
            "chunk_index": chunk_index,
            "section_title": section_title,
            "heading_path": heading_path,
        }
        metadata.update(part.get("metadata", {}))

        chunks.append({
            "content": content,
            "metadata": metadata,
        })

    return chunks


@register(".md")
def chunk_markdown_file(
    markdown_text: str,
    source: str,
    config: Optional[ChunkConfig] = None,
) -> List[Dict[str, Any]]:
    return chunk_generic_text(markdown_text, source, config)


@register(".txt")
def chunk_txt_file(
    markdown_text: str,
    source: str,
    config: Optional[ChunkConfig] = None,
) -> List[Dict[str, Any]]:
    return chunk_generic_text(markdown_text, source, config)


@register("default")
def chunk_default_file(
    markdown_text: str,
    source: str,
    config: Optional[ChunkConfig] = None,
) -> List[Dict[str, Any]]:
    return chunk_generic_text(markdown_text, source, config)
