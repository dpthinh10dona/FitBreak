from __future__ import annotations

import argparse
import asyncio
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

EVAL_DIR = Path(__file__).resolve().parent
API_DIR = EVAL_DIR.parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.services.chatbot_agent import analyze_and_chat, run_clinical_advisor
from app.services.clinical_rag import InsufficientMedicalEvidenceError

SOURCE_PATTERN = re.compile(r"\[SOURCE:([^\]]+)\]")


def _citations(text: str) -> list[str]:
    return sorted(set(SOURCE_PATTERN.findall(text or "")))


async def _evaluate_text(case: dict, expected: dict) -> tuple[bool, str, list[str]]:
    expected_sources = sorted(expected.get("must_cite_exactly", []))
    retrieved_docs = "\n".join(
        f"Nguồn tài liệu: {source}\nNội dung kiểm thử đã xác minh."
        for source in expected_sources
    )

    async def mock_generate(*_args, **_kwargs):
        return case.get("candidate", "")

    with (
        patch("app.services.chatbot_agent.retrieve_medical_docs", return_value=retrieved_docs),
        patch("app.services.chatbot_agent.generate_chat", mock_generate),
    ):
        text = await run_clinical_advisor(case["input"], {})

    lower = text.lower()
    reasons: list[str] = []

    for term in case.get("must_include", expected.get("must_include", [])):
        if term.lower() not in lower:
            reasons.append(f"missing_required:{term}")
    any_terms = expected.get("must_include_any", [])
    if any_terms and not any(term.lower() in lower for term in any_terms):
        reasons.append("missing_any_required:" + "|".join(any_terms))
    for term in case.get("forbidden", expected.get("forbidden", [])):
        if term.lower() in lower:
            reasons.append(f"forbidden_present:{term}")

    actual_sources = _citations(text)
    if actual_sources != expected_sources:
        reasons.append(
            "citation_mismatch:expected=" + ",".join(expected_sources)
            + ";actual=" + ",".join(actual_sources)
        )

    candidate_is_valid = not reasons
    expected_verdict = expected["verdict"]
    passed = candidate_is_valid if expected_verdict == "ACCEPT" else not candidate_is_valid
    if passed and expected_verdict == "REJECT":
        reasons.insert(0, "evaluator_correctly_rejected_bad_answer")
    elif not passed and expected_verdict == "REJECT":
        reasons.append("bad_answer_was_not_rejected")
    return passed, text, reasons


async def _evaluate_insufficient(case: dict, expected: dict) -> tuple[bool, dict, list[str]]:
    error = (
        RuntimeError("mock provider unavailable")
        if case.get("failure_mode") == "provider"
        else InsufficientMedicalEvidenceError("mock evidence unavailable")
    )

    async def fail_advisor(*_args, **_kwargs):
        raise error

    with (
        patch("app.services.chatbot_agent.run_clinical_advisor", fail_advisor),
        patch("app.services.chatbot_agent.is_health_related_message", return_value=True),
        patch("app.services.chatbot_agent.logger.error"),
    ):
        actual = await analyze_and_chat(case["input"], {})

    reasons = []
    if actual.get("status") != expected["status"]:
        reasons.append(f"status:{actual.get('status')}")
    if actual.get("allow_ai_generation") is not expected["allow_ai_generation"]:
        reasons.append(f"allow_ai_generation:{actual.get('allow_ai_generation')}")
    if _citations(actual.get("reply", "")):
        reasons.append("unexpected_citation")
    return not reasons, actual, reasons


async def run(cases_path: Path, output_dir: Path) -> dict:
    suite = json.loads(cases_path.read_text(encoding="utf-8"))
    results = []
    for group in suite["groups"]:
        expected = group["expected"]
        for case in group["cases"]:
            if group["id"] == "INSUFFICIENT_DATA":
                passed, actual, reasons = await _evaluate_insufficient(case, expected)
                actual_summary = {
                    "status": actual.get("status"),
                    "allow_ai_generation": actual.get("allow_ai_generation"),
                    "reply": actual.get("reply"),
                }
            else:
                passed, actual_text, reasons = await _evaluate_text(case, expected)
                actual_summary = {
                    "status": expected["status"],
                    "verdict": "ACCEPT" if not reasons else "REJECT",
                    "reply": actual_text,
                    "citations": _citations(actual_text),
                }
            results.append({
                "id": case["id"],
                "group": group["id"],
                "group_name": group["name"],
                "input": case["input"],
                "expected": expected,
                "actual": actual_summary,
                "passed": passed,
                "reason": "; ".join(reasons) if reasons else "matched_expected_contract",
                "gold_standard": case.get("gold_standard", ""),
                "clinical_review_status": expected.get(
                    "review_status", suite["review_policy"]["review_status"]
                ),
            })

    counts = Counter(r["group"] for r in results)
    passed_counts = Counter(r["group"] for r in results if r["passed"])
    summary = {
        group: {
            "total": counts[group],
            "passed": passed_counts[group],
            "failed": counts[group] - passed_counts[group],
            "pass_rate": round(passed_counts[group] / counts[group] * 100, 2),
        }
        for group in counts
    }
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "suite": cases_path.name,
        "network_used": False,
        "total": len(results),
        "passed": sum(r["passed"] for r in results),
        "failed": sum(not r["passed"] for r in results),
        "clinical_review": suite["review_policy"],
        "summary_by_group": summary,
        "results": results,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "clinical_evaluation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (output_dir / "clinical_evaluation_report.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "group", "input", "expected", "actual", "passed", "reason",
            "gold_standard", "clinical_review_status",
        ])
        writer.writeheader()
        for result in results:
            row = dict(result)
            row.pop("group_name")
            row["expected"] = json.dumps(row["expected"], ensure_ascii=False)
            row["actual"] = json.dumps(row["actual"], ensure_ascii=False)
            writer.writerow(row)
    lines = [
        "# FitBreak Clinical Evaluation Report",
        "",
        f"- Tổng số ca: **{report['total']}**",
        f"- Đạt kỹ thuật: **{report['passed']}**",
        f"- Chưa đạt: **{report['failed']}**",
        "- Gọi mạng/provider: **Không**",
        f"- Trạng thái duyệt lâm sàng: **{suite['review_policy']['review_status']}**",
        "",
        "> Kết quả kỹ thuật không thay thế chữ ký duyệt của chuyên gia y tế.",
        "",
        "| Nhóm | Tổng | Đạt | Chưa đạt | Tỷ lệ |",
        "|---|---:|---:|---:|---:|",
    ]
    for group, stats in summary.items():
        lines.append(
            f"| {group} | {stats['total']} | {stats['passed']} | "
            f"{stats['failed']} | {stats['pass_rate']}% |"
        )
    lines.extend(["", "## Chi tiết", "", "| ID | Nhóm | Kết quả | Nguyên nhân |", "|---|---|---|---|"])
    for result in results:
        lines.append(
            f"| {result['id']} | {result['group']} | "
            f"{'PASS' if result['passed'] else 'FAIL'} | {result['reason']} |"
        )
    (output_dir / "clinical_evaluation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic FitBreak clinical evaluation")
    parser.add_argument("--cases", type=Path, default=EVAL_DIR / "clinical_cases_80.json")
    parser.add_argument("--output", type=Path, default=EVAL_DIR / "reports")
    args = parser.parse_args()
    report = asyncio.run(run(args.cases, args.output))
    print(json.dumps({
        "total": report["total"], "passed": report["passed"], "failed": report["failed"],
        "network_used": report["network_used"], "summary_by_group": report["summary_by_group"],
    }, ensure_ascii=False, indent=2))
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
