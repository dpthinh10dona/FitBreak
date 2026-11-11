"""
Chunking for DOCX Documents.
Preserves section headers, table layouts, and clinical guidelines integrity.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.services.chunking.chunker_registry import register
from app.services.chunking.config import ChunkConfig
from app.services.chunking.structure import parse_markdown_units, pack_semantic_units


def chunk_docx(
    markdown_text: str,
    source: str,
    config: Optional[ChunkConfig] = None,
) -> List[Dict[str, Any]]:
    """
    Split DOCX Markdown into semantic units while preserving document structure,
    heading hierarchy, and metadata for RAG retrieval.
    """
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

        # Deduplication check
        content_hash = hashlib.sha1(content.casefold().encode("utf-8")).hexdigest()
        if content_hash in seen_hashes:
            continue
        seen_hashes.add(content_hash)

        chunk_index += 1
        heading_path = part.get("metadata", {}).get("heading_path", "")
        parent_id = hashlib.sha1((Path(source).name + ":" + heading_path).encode("utf-8")).hexdigest()[:12]

        # Extract top section title from heading path
        section_title = heading_path.split(" > ")[-1] if heading_path else Path(source).stem

        metadata: Dict[str, Any] = {
            "source_file": Path(source).name,
            "source_path": str(source),
            "doc_type": "docx",
            "chunk_id": f"chunk_{chunk_index}",
            "chunk_index": chunk_index,
            "section_title": section_title,
            "heading_path": heading_path,
            "parent_id": parent_id,
        }
        metadata.update(part.get("metadata", {}))

        chunks.append({
            "content": content,
            "metadata": metadata,
        })

    return chunks


@register(".docx")
def chunk_docx_file(
    markdown_text: str,
    source: str,
    config: Optional[ChunkConfig] = None,
) -> List[Dict[str, Any]]:
    return chunk_docx(markdown_text, source, config)
