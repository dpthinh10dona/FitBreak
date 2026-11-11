"""
DOCX to Markdown Document Converter.
Supports headings, paragraphs, formatted text (bold, italic), lists, and tables.
Includes both python-docx support and a pure standard-library OpenXML fallback.
"""

from __future__ import annotations

import os
import re
import zipfile
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from app.services.document_parser.converter_registry import register

logger = logging.getLogger("document_parser.docx")

# Namespaces in OpenXML DOCX documents
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS_MAP = {"w": W_NS}


class DocxOpenXMLParser:
    """
    Standard-library OpenXML parser for .docx files.
    Works without external dependencies by directly parsing word/document.xml.
    """

    @classmethod
    def can_parse(cls, file_path: Union[str, Path]) -> bool:
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                return "word/document.xml" in zf.namelist()
        except Exception:
            return False

    @classmethod
    def parse_to_markdown(cls, file_path: Union[str, Path]) -> str:
        with zipfile.ZipFile(file_path, "r") as zf:
            xml_content = zf.read("word/document.xml")

        tree = ET.fromstring(xml_content)
        body = tree.find("w:body", NS_MAP)
        if body is None:
            return ""

        md_lines: List[str] = []

        for elem in body:
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

            if tag == "p":
                md_line = cls._parse_paragraph(elem)
                if md_line:
                    md_lines.append(md_line)
            elif tag == "tbl":
                table_md = cls._parse_table(elem)
                if table_md:
                    md_lines.append(table_md)

        return "\n\n".join(md_lines).strip() + "\n"

    @classmethod
    def _parse_paragraph(cls, p_elem: ET.Element) -> str:
        # Check paragraph style
        p_style = None
        p_pr = p_elem.find("w:pPr", NS_MAP)
        is_list = False
        heading_level = 0

        if p_pr is not None:
            style_elem = p_pr.find("w:pStyle", NS_MAP)
            if style_elem is not None:
                style_val = style_elem.attrib.get(f"{{{W_NS}}}val", "")
                # Heading detection
                h_match = re.search(r"heading\s*(\d+)", style_val, re.IGNORECASE)
                if h_match:
                    heading_level = int(h_match.group(1))
                elif re.search(r"title", style_val, re.IGNORECASE):
                    heading_level = 1
                elif re.search(r"subtitle", style_val, re.IGNORECASE):
                    heading_level = 2

            num_pr = p_pr.find("w:numPr", NS_MAP)
            if num_pr is not None:
                is_list = True

        # Extract text runs with bold/italic formatting
        runs_text: List[str] = []
        for r in p_elem.findall("w:r", NS_MAP):
            r_pr = r.find("w:rPr", NS_MAP)
            is_bold = False
            is_italic = False

            if r_pr is not None:
                b_elem = r_pr.find("w:b", NS_MAP)
                if b_elem is not None and b_elem.attrib.get(f"{{{W_NS}}}val", "true").lower() not in ("0", "false"):
                    is_bold = True
                i_elem = r_pr.find("w:i", NS_MAP)
                if i_elem is not None and i_elem.attrib.get(f"{{{W_NS}}}val", "true").lower() not in ("0", "false"):
                    is_italic = True

            # Extract text elements
            t_elems = r.findall("w:t", NS_MAP)
            run_str = "".join([t.text or "" for t in t_elems])
            if not run_str:
                continue

            # Apply Markdown formatting
            if is_bold and is_italic:
                run_str = f"***{run_str.strip()}***"
            elif is_bold:
                run_str = f"**{run_str.strip()}**"
            elif is_italic:
                run_str = f"*{run_str.strip()}*"

            runs_text.append(run_str)

        full_text = " ".join("".join(runs_text).split())
        if not full_text:
            return ""

        if heading_level > 0:
            h_prefix = "#" * min(heading_level, 6)
            return f"<!-- section: {full_text} -->\n{h_prefix} {full_text}"
        elif is_list:
            return f"- {full_text}"
        else:
            return full_text

    @classmethod
    def _parse_table(cls, tbl_elem: ET.Element) -> str:
        rows_data: List[List[str]] = []

        for tr in tbl_elem.findall("w:tr", NS_MAP):
            row_cells: List[str] = []
            for tc in tr.findall("w:tc", NS_MAP):
                cell_text_parts: List[str] = []
                for p in tc.findall("w:p", NS_MAP):
                    p_text = cls._parse_paragraph(p)
                    # Remove comment markers from cell text if any
                    p_text = re.sub(r"<!--.*?-->", "", p_text).strip()
                    if p_text:
                        cell_text_parts.append(p_text)
                cell_text = " ".join(cell_text_parts).replace("|", "\\|")
                row_cells.append(cell_text.strip())
            if any(c for c in row_cells):
                rows_data.append(row_cells)

        if not rows_data:
            return ""

        # Normalize column counts
        max_cols = max(len(r) for r in rows_data)
        normalized_rows = [r + [""] * (max_cols - len(r)) for r in rows_data]

        header_row = normalized_rows[0]
        divider_row = [":---"] * max_cols
        data_rows = normalized_rows[1:]

        md_table_lines = [
            "| " + " | ".join(header_row) + " |",
            "| " + " | ".join(divider_row) + " |",
        ]
        for row in data_rows:
            md_table_lines.append("| " + " | ".join(row) + " |")

        return "\n".join(md_table_lines)


class PythonDocxParser:
    """Parser using python-docx library if installed."""

    @classmethod
    def available(cls) -> bool:
        try:
            import docx  # noqa: F401
            return True
        except ImportError:
            return False

    @classmethod
    def parse_to_markdown(cls, file_path: Union[str, Path]) -> str:
        import docx

        doc = docx.Document(str(file_path))
        md_lines: List[str] = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            style_name = (p.style.name or "").lower()
            if "heading 1" in style_name:
                md_lines.append(f"<!-- section: {text} -->\n# {text}")
            elif "heading 2" in style_name:
                md_lines.append(f"<!-- section: {text} -->\n## {text}")
            elif "heading 3" in style_name:
                md_lines.append(f"### {text}")
            elif "heading 4" in style_name:
                md_lines.append(f"#### {text}")
            elif "list" in style_name:
                md_lines.append(f"- {text}")
            else:
                # Format runs inside paragraph
                formatted_runs = []
                for run in p.runs:
                    r_text = run.text
                    if not r_text:
                        continue
                    if run.bold and run.italic:
                        formatted_runs.append(f"***{r_text.strip()}***")
                    elif run.bold:
                        formatted_runs.append(f"**{r_text.strip()}**")
                    elif run.italic:
                        formatted_runs.append(f"*{r_text.strip()}*")
                    else:
                        formatted_runs.append(r_text)
                para_md = "".join(formatted_runs).strip()
                if para_md:
                    md_lines.append(para_md)

        # Parse tables
        for table in doc.tables:
            table_rows: List[List[str]] = []
            for row in table.rows:
                cells = [c.text.strip().replace("\n", " ").replace("|", "\\|") for c in row.cells]
                if any(cells):
                    table_rows.append(cells)
            if table_rows:
                max_c = max(len(r) for r in table_rows)
                header = table_rows[0] + [""] * (max_c - len(table_rows[0]))
                divider = [":---"] * max_c
                t_lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(divider) + " |"]
                for r in table_rows[1:]:
                    r_norm = r + [""] * (max_c - len(r))
                    t_lines.append("| " + " | ".join(r_norm) + " |")
                md_lines.append("\n".join(t_lines))

        return "\n\n".join(md_lines).strip() + "\n"


@register(".docx")
def docx_to_markdown(file_path: Union[str, Path], output_dir: Optional[str] = None) -> str:
    """
    Main converter entrypoint for .docx documents.
    Registered in converter_registry for extension .docx.
    """
    p = Path(file_path)
    logger.info(f"Đang phân tích cú pháp tệp Word DOCX: {p.name}")

    if PythonDocxParser.available():
        try:
            md = PythonDocxParser.parse_to_markdown(p)
        except Exception as exc:
            logger.warning(f"python-docx thất bại ({exc}), chuyển sang OpenXML engine tích hợp sẵn...")
            md = DocxOpenXMLParser.parse_to_markdown(p)
    else:
        md = DocxOpenXMLParser.parse_to_markdown(p)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        out_path = Path(output_dir) / f"{p.stem}.md"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
        logger.info(f"Đã lưu kết quả phân tích cú pháp DOCX sang Markdown tại: {out_path}")

    return md
