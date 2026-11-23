"""Audit CSV provenance without treating an attribution as row-level verification."""

import csv
import json
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "app" / "core" / "dataset"
OUTPUT = Path(__file__).resolve().parent / "reports" / "dataset_provenance.json"

DATASETS = {
    "food": {
        "file": "Vietnamese_Food_Database.csv",
        "name_column": "name",
        "context_reference": "https://chuyentrang.viendinhduong.vn/viewfilenew/vi/thu-vien-sach-chuyen-nganh/189/1.html",
        "context_note": "Tài liệu Viện Dinh dưỡng là nguồn tham khảo chung; chưa đối chiếu từng công thức và giá trị dinh dưỡng của CSV.",
    },
    "exercise": {
        "file": "Exercise_Database.csv",
        "name_column": "exercise",
        "context_reference": "https://www.who.int/publications/i/item/9789240015128",
        "context_note": "Hướng dẫn WHO chỉ hỗ trợ nguyên tắc vận động chung; không xác nhận từng bài tập hoặc thời lượng trong CSV.",
    },
}


def build() -> dict:
    datasets = {}
    for name, config in DATASETS.items():
        with (DATA_DIR / config["file"]).open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        citations = Counter(row.get("source_citation", "").strip() for row in rows)
        missing_period = sum(not row.get("valid_period", "").strip() for row in rows)
        missing_limit = sum(not row.get("limitation_type", "").strip() for row in rows)
        datasets[name] = {
            "file": config["file"],
            "row_count": len(rows),
            "source_citations": dict(citations),
            "rows_missing_valid_period": missing_period,
            "rows_missing_limitation": missing_limit,
            "rows_verified_against_original": 0,
            "verification_status": "PENDING_ROW_VERIFICATION",
            "context_reference": config["context_reference"],
            "context_note": config["context_note"],
            "review_items": [
                {"row_number": index + 2, "name": row.get(config["name_column"], ""),
                 "source_citation": row.get("source_citation", ""),
                 "valid_period": row.get("valid_period", ""),
                 "verification_status": "PENDING_ROW_VERIFICATION"}
                for index, row in enumerate(rows)
            ],
        }
        if name == "food":
            pho = next((row for row in rows if row.get("name") == "Phở bò chín"), None)
            if pho:
                datasets[name]["spot_checks"] = [{
                    "name": "Phở bò chín",
                    "csv_kcal": pho.get("calories"),
                    "official_reference": "https://chuyentrang.viendinhduong.vn/FileUpload/Documents/500%20mon%20an%20thong%20dung/%2814%29%20Pho.PDF",
                    "official_variants_kcal": [291, 352],
                    "result": "NOT_SAME_RECIPE",
                    "note": "Tài liệu gốc ghi hai công thức phở bò chín khác công thức CSV; không dùng trang này để xác nhận giá trị CSV.",
                }]
    report = {"datasets": datasets}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    result = build()
    print({name: item["row_count"] for name, item in result["datasets"].items()})
