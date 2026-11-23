"""Inventory local medical PDFs without treating an unreviewed file as approved."""

import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "app" / "core" / "dataset" / "medical_knowledge"
OUTPUT = Path(__file__).resolve().parent / "reports" / "source_inventory.json"
def extract_cover_metadata(reader: PdfReader) -> dict:
    cover = reader.pages[0].extract_text() or ""
    cover = " ".join(cover.split())
    header = cover[:650]
    decision = re.search(r"(?:Số\s*:\s*|Quyết định số\s*)(\d{3,5}\s*/\s*Q[ĐD]-BYT)", header, re.IGNORECASE)
    title = re.search(r"[“\"](Hướng dẫn[^”\"]+)[”\"]", cover, re.IGNORECASE)
    date_match = re.search(r"(?:Hà Nội,\s*ngày|Quyết định số[^()]{0,60}ngày)\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(20\d{2})", header, re.IGNORECASE)
    issued = f"{date_match[3]}-{int(date_match[2]):02d}-{int(date_match[1]):02d}" if date_match else None
    return {
        "extracted_decision": decision[1].replace(" ", "") if decision else None,
        "extracted_title": title[1].strip() if title else None,
        "extracted_issued_at": issued,
    }


def build_inventory() -> list[dict]:
    catalog = json.loads((KNOWLEDGE_DIR / "source_catalog.json").read_text(encoding="utf-8"))
    registered = {entry["file"]: entry for entry in catalog["sources"]}
    items = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.pdf")):
        record = registered.get(path.name, {})
        reader = PdfReader(str(path))
        items.append({
            "file": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "pages": len(reader.pages),
            **extract_cover_metadata(reader),
            "source_id": record.get("source_id"),
            "title": record.get("title"),
            "publisher": record.get("publisher"),
            "decision": record.get("decision"),
            "issued_at": record.get("issued_at"),
            "effective_at": record.get("effective_at"),
            "source_url": record.get("source_url"),
            "limitations": record.get("limitations"),
            "verification_status": record.get("verification_status", "PENDING_METADATA"),
            "eligible_for_rag": record.get("verification_status") == "APPROVED" and all(
                record.get(field) for field in ("source_id", "title", "file", "limitations", "source_url")
            ),
        })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({"sources": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return items


if __name__ == "__main__":
    sources = build_inventory()
    print(f"PDF: {len(sources)}, approved: {sum(s['eligible_for_rag'] for s in sources)}")
