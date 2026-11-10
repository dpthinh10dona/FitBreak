"""
Semantic Markdown Unit Parsing and Packing.
Understands headers, paragraphs, lists, and tables to produce coherent chunks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from app.services.chunking.config import ChunkConfig


@dataclass
class SemanticUnit:
    """Represents a coherent markdown block (heading, paragraph, list, table)."""

    unit_type: str  # 'heading', 'paragraph', 'list', 'table', 'blockquote', 'other'
    content: str
    heading_level: int = 0
    heading_path: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


def parse_markdown_units(markdown_text: str) -> List[SemanticUnit]:
    """
    Parses Markdown text into a list of SemanticUnits while tracking active heading hierarchy.
    """
    lines = markdown_text.splitlines()
    units: List[SemanticUnit] = []

    current_headings: Dict[int, str] = {}
    current_lines: List[str] = []
    current_type: str = ""

    def get_heading_path() -> str:
        active = [current_headings[lvl] for lvl in sorted(current_headings.keys()) if current_headings[lvl]]
        return " > ".join(active)

    def flush_unit():
        nonlocal current_lines, current_type
        if not current_lines:
            return
        text = "\n".join(current_lines).strip()
        if text:
            units.append(
                SemanticUnit(
                    unit_type=current_type or "paragraph",
                    content=text,
                    heading_path=get_heading_path(),
                )
            )
        current_lines = []
        current_type = ""

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Empty line triggers flush for normal paragraphs
        if not stripped:
            if current_type not in ("table", "list"):
                flush_unit()
            i += 1
            continue

        # 1. Heading (#, ##, ...)
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            flush_unit()
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            # Update heading hierarchy
            current_headings = {lvl: txt for lvl, txt in current_headings.items() if lvl < level}
            current_headings[level] = heading_text

            units.append(
                SemanticUnit(
                    unit_type="heading",
                    content=stripped,
                    heading_level=level,
                    heading_path=get_heading_path(),
                )
            )
            i += 1
            continue

        # 2. Section comment marker <!-- section: ... -->
        section_match = re.match(r"^<!--\s*section:\s*(.*?)\s*-->$", stripped, re.IGNORECASE)
        if section_match:
            flush_unit()
            i += 1
            continue

        # 3. Table row (| ... |)
        if stripped.startswith("|") and stripped.endswith("|"):
            if current_type != "table":
                flush_unit()
                current_type = "table"
            current_lines.append(stripped)
            i += 1
            continue
        elif current_type == "table":
            flush_unit()

        # 4. List item (- , * , 1. )
        list_match = re.match(r"^(\s*[-*+]|\s*\d+\.)\s+", line)
        if list_match:
            if current_type != "list":
                flush_unit()
                current_type = "list"
            current_lines.append(line)
            i += 1
            continue
        elif current_type == "list":
            # If continuation line of list item
            if line.startswith("    ") or line.startswith("\t"):
                current_lines.append(line)
                i += 1
                continue
            else:
                flush_unit()

        # 5. Blockquote (> ...)
        if stripped.startswith(">"):
            if current_type != "blockquote":
                flush_unit()
                current_type = "blockquote"
            current_lines.append(line)
            i += 1
            continue
        elif current_type == "blockquote":
            flush_unit()

        # 6. Default paragraph
        if current_type != "paragraph":
            flush_unit()
            current_type = "paragraph"
        current_lines.append(line)
        i += 1

    flush_unit()
    return units


def pack_semantic_units(units: List[SemanticUnit], config: ChunkConfig) -> List[Dict[str, Any]]:
    """
    Groups semantic units into packed chunks conforming to ChunkConfig limits.
    Ensures headings and table context are preserved.
    """
    chunks: List[Dict[str, Any]] = []
    if not units:
        return chunks

    current_units: List[SemanticUnit] = []
    current_length = 0

    def make_chunk_dict(unit_list: List[SemanticUnit]) -> Dict[str, Any]:
        combined_text = "\n\n".join(u.content for u in unit_list).strip()
        # Derive heading path from the most informative unit
        heading_path = ""
        for u in reversed(unit_list):
            if u.heading_path:
                heading_path = u.heading_path
                break

        unit_types = list({u.unit_type for u in unit_list})
        return {
            "content": combined_text,
            "metadata": {
                "heading_path": heading_path,
                "unit_types": unit_types,
                "character_count": len(combined_text),
                "word_count": len(combined_text.split()),
            },
        }

    for unit in units:
        unit_len = len(unit.content)

        # If a single unit is longer than max_chunk_size, we flush current and split or keep it
        if unit_len > config.max_chunk_size:
            if current_units:
                chunks.append(make_chunk_dict(current_units))
                current_units = []
                current_length = 0

            # If it's a long paragraph, break by sentences/punctuation
            if unit.unit_type == "paragraph" and config.split_long_paragraphs:
                sentences = re.split(r"(?<=[.!?。])\s+", unit.content)
                buf: List[str] = []
                buf_len = 0
                for s in sentences:
                    if buf_len + len(s) > config.max_chunk_size and buf:
                        chunks.append({
                            "content": " ".join(buf).strip(),
                            "metadata": {
                                "heading_path": unit.heading_path,
                                "unit_types": ["paragraph"],
                            },
                        })
                        buf = [s]
                        buf_len = len(s)
                    else:
                        buf.append(s)
                        buf_len += len(s) + 1
                if buf:
                    chunks.append({
                        "content": " ".join(buf).strip(),
                        "metadata": {
                            "heading_path": unit.heading_path,
                            "unit_types": ["paragraph"],
                        },
                    })
            else:
                # Tables or other units kept intact to avoid data loss
                chunks.append(make_chunk_dict([unit]))
            continue

        # Check if adding this unit exceeds max_chunk_size
        if current_length + unit_len + 2 > config.max_chunk_size:
            if current_units:
                chunks.append(make_chunk_dict(current_units))
                current_units = []
                current_length = 0

        current_units.append(unit)
        current_length += unit_len + 2

    if current_units:
        chunks.append(make_chunk_dict(current_units))

    return chunks
