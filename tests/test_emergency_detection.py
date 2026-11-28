"""Protect the deterministic warning path used before any LLM request."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from app.services.chatbot_agent import is_emergency_message


def test_allergy_with_breathing_difficulty_is_emergency():
    assert is_emergency_message("Tôi dị ứng đậu phộng, vừa khó thở; có nên tập nặng không?")


def test_allergy_without_breathing_difficulty_is_not_automatically_emergency():
    assert not is_emergency_message("Tôi dị ứng đậu phộng; nên tránh thực phẩm nào?")
