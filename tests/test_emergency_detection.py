"""Protect the deterministic warning path used before any LLM request."""

import sys
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from app.services.chatbot_agent import (
    asthma_exercise_warning_result,
    is_active_asthma_exercise_question,
    is_emergency_message,
)
from app.services.clinical_rag import _required_topic_source_ids
from app.main import app
from app.core.token_authorization import token_authorization, tokenAuthorization


def test_allergy_with_breathing_difficulty_is_emergency():
    assert is_emergency_message("Tôi dị ứng đậu phộng, vừa khó thở; có nên tập nặng không?")


def test_allergy_without_breathing_difficulty_is_not_automatically_emergency():
    assert not is_emergency_message("Tôi dị ứng đậu phộng; nên tránh thực phẩm nào?")


def test_active_asthma_breathlessness_gets_grounded_warning():
    question = "Em bị hen, có nên tập cường độ nặng khi đang khó thở?"
    assert is_active_asthma_exercise_question(question)
    assert _required_topic_source_ids(question) == {"BYT-5850-2021"}
    result = asthma_exercise_warning_result()
    assert result["status"] == "MEDICAL_WARNING"
    assert result["allow_ai_generation"] is False
    assert "Không nên tập cường độ nặng" in result["reply"]
    assert "[SOURCE:BYT-5850-2021]" in result["reply"]
    assert "Vị trí: Trang 26" in result["reply"]
    assert "BYT-2767-2023" not in result["reply"]


def test_chatbot_endpoint_answers_active_asthma_warning_without_using_quota():
    app.dependency_overrides[token_authorization] = lambda: tokenAuthorization(
        client=None, user_id=f"asthma-test-{uuid4()}", user_email="eval@example.invalid"
    )
    try:
        response = TestClient(app).post(
            "/chatbot/ask",
            json={"message": "Em bị hen, có nên tập cường độ nặng khi đang khó thở?"},
        )
    finally:
        app.dependency_overrides.pop(token_authorization, None)
    assert response.status_code == 200
    assert response.json()["status"] == "MEDICAL_WARNING"
    assert response.json()["reason_code"] == "ASTHMA_BREATHLESSNESS_WARNING"
    assert response.json()["remaining_questions_today"] == 3
