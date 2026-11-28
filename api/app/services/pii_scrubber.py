"""Minimize user supplied text before it reaches an external AI provider."""

import json
import re
import unicodedata
from typing import Any

MAX_SYMPTOM_CHARS = 99
_EMAIL = re.compile(r"(?<![\w.])[-\w.+]+@[-\w]+(?:\.[-\w]+)+", re.UNICODE)
_PHONE = re.compile(r"(?<!\w)(?:\+84|0)[\s.\-]?(?:\d[\s.\-]?){8,10}(?!\w)")
_UPPER = "".join(chr(code) for code in range(0xC0, 0x1F00) if chr(code).isupper())
_WORD = rf"[A-Z{re.escape(_UPPER)}][a-zà-ỹđ]+"
_INTRO = re.compile(
    rf"(?i:\b(?:tôi tên là|em tên là|mình tên là|tên tôi là|tên em là|em là|tôi là))\s+"
    rf"{_WORD}(?:\s+{_WORD}){{0,3}}",
    re.UNICODE,
)
_FULL_NAME = re.compile(rf"(?<!\w){_WORD}(?:\s+{_WORD}){{1,3}}(?!\w)", re.UNICODE)
_UPPER_NAME = re.compile(rf"(?<!\w)[A-Z{re.escape(_UPPER)}]{{2,}}(?:\s+[A-Z{re.escape(_UPPER)}]{{2,}}){{1,3}}(?!\w)")


def scrub_pii(text: str) -> str:
    """Replace common identifiers; heuristic name detection can have false negatives."""
    clean = unicodedata.normalize("NFC", text or "")
    clean = _EMAIL.sub("[EMAIL]", clean)
    clean = _PHONE.sub("[PHONE]", clean)
    clean = _INTRO.sub("[NAME]", clean)
    clean = _FULL_NAME.sub("[NAME]", clean)
    clean = _UPPER_NAME.sub("[NAME]", clean)
    return clean


def scrub_symptom(text: str) -> str:
    """Reject long symptom questions before any model or embedding request."""
    value = (text or "").strip()
    if not value or len(value) > MAX_SYMPTOM_CHARS:
        raise ValueError("Câu hỏi triệu chứng phải dài từ 1 đến 99 ký tự.")
    return scrub_pii(value)


def anonymous_health_payload(profile: dict[str, Any], symptom: str) -> dict[str, Any]:
    """Explicit allowlist for all user data inserted into AI prompts."""
    allergies = profile.get("allergies")
    if isinstance(allergies, list):
        allergies = [scrub_pii(str(item))[:80] for item in allergies[:10]]
    elif isinstance(allergies, str):
        allergies = [scrub_pii(item.strip())[:80] for item in allergies.split(",")[:10] if item.strip()]
    else:
        allergies = []
    return {
        "bmi": profile.get("bmi") if isinstance(profile.get("bmi"), (int, float)) else None,
        "tdee": profile.get("tdee") if isinstance(profile.get("tdee"), (int, float)) else None,
        "allergies": allergies,
        "symptom": scrub_symptom(symptom),
    }


def anonymous_health_json(profile: dict[str, Any], symptom: str) -> str:
    return json.dumps(anonymous_health_payload(profile, symptom), ensure_ascii=False)
