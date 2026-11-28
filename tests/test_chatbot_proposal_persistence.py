"""The chatbot writes derived profile fields only after proposal confirmation."""

import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient
from postgrest.exceptions import APIError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from app.core.token_authorization import token_authorization
from app.main import app


class ProfileQuery:
    def __init__(self, writes):
        self.writes = writes
        self.values = None

    def update(self, values):
        self.values = values
        return self

    def select(self, _columns):
        return self

    def eq(self, _key, _value):
        return self

    def execute(self):
        if self.values is None:
            return SimpleNamespace(data=[{"bmi": 22.0, "tdee": 2100, "allergies": []}])
        if "status_flag" in self.values:
            raise APIError({"message": "column profiles.status_flag does not exist", "code": "42703"})
        self.writes.append(self.values)
        return SimpleNamespace(data=[self.values])


class MissingHealthStates:
    def upsert(self, *_args, **_kwargs):
        raise APIError({"message": "table health_states not found", "code": "PGRST205"})


class ProfileClient:
    def __init__(self):
        self.writes = []

    def table(self, name):
        return ProfileQuery(self.writes) if name == "profiles" else MissingHealthStates()


class CompleteProfileQuery(ProfileQuery):
    def execute(self):
        if self.values is None:
            return SimpleNamespace(data=[{"bmi": 22.0, "tdee": 2100}])
        self.writes.append(self.values)
        return SimpleNamespace(data=[self.values])


class HealthStateQuery:
    def __init__(self, client):
        self.client = client
        self.values = None

    def select(self, _columns):
        return self

    def eq(self, _key, _value):
        return self

    def limit(self, _count):
        return self

    def upsert(self, values, **_kwargs):
        self.values = values
        return self

    def execute(self):
        if self.values is None:
            return SimpleNamespace(data=[{"active_health_flags": self.client.flags}])
        self.client.flags = self.values["active_health_flags"]
        self.client.health_writes.append(self.values)
        return SimpleNamespace(data=[self.values])


class CompleteProfileClient(ProfileClient):
    def __init__(self):
        super().__init__()
        self.flags = ["high_blood_pressure"]
        self.health_writes = []

    def table(self, name):
        return CompleteProfileQuery(self.writes) if name == "profiles" else HealthStateQuery(self)


def test_asthma_proposal_only_persists_after_confirm():
    db = ProfileClient()
    user_id = f"proposal-{uuid4()}"
    app.dependency_overrides[token_authorization] = lambda: SimpleNamespace(
        client=db, user_id=user_id, user_email="eval@example.invalid"
    )
    try:
        with TestClient(app) as client:
            answer = client.post(
                "/chatbot/ask",
                json={"message": "Em bị hen, có nên tập cường độ nặng khi đang khó thở?"},
            )
            assert answer.status_code == 200
            proposal = answer.json()["proposal"]
            assert proposal["level_of_physical_activity"] == "light"
            assert proposal["food_recommendation"] is None
            assert db.writes == []
            saved = client.post(
                "/chatbot/confirm-update",
                json={
                    "status_flag": "restrict_heavy_exercise",
                    "level_of_physical_activity": proposal["level_of_physical_activity"],
                },
            )
    finally:
        app.dependency_overrides.pop(token_authorization, None)
    assert saved.status_code == 200
    assert saved.json()["success"] is True
    assert db.writes == [{"level_of_physical_activity": "light"}]


def test_confirm_persists_food_and_activity_without_raw_chat():
    db = ProfileClient()
    app.dependency_overrides[token_authorization] = lambda: SimpleNamespace(
        client=db, user_id=f"proposal-{uuid4()}", user_email="eval@example.invalid"
    )
    try:
        with TestClient(app) as client:
            saved = client.post(
                "/chatbot/confirm-update",
                json={
                    "status_flag": "maintain_activity",
                    "food_recommendation": "Ăn rau và uống đủ nước",
                    "level_of_physical_activity": "medium",
                },
            )
    finally:
        app.dependency_overrides.pop(token_authorization, None)
    assert saved.status_code == 200
    assert db.writes == [{
        "food_recommendation": "Ăn rau và uống đủ nước",
        "level_of_physical_activity": "medium",
    }]
    assert "message" not in db.writes[0]
    assert "reply" not in db.writes[0]


def test_generated_fields_reach_card_then_confirmation(monkeypatch):
    from app.router import chatbot

    async def in_scope(_message):
        return "IN_SCOPE"

    async def generated(user_message, user_profile, scope_status):
        assert scope_status == "IN_SCOPE"
        assert user_message and user_profile["bmi"] == 22.0
        return {
            "reply": "Khuyến nghị có trích dẫn [SOURCE:NDD-KHUYEN-NGHI]",
            "status": "PASS",
            "has_proposed_changes": True,
            "suggested_food_recommendation": "Ăn rau và uống đủ nước",
            "suggested_level_of_physical_activity": "medium",
            "summary_for_ui_card": "Điều chỉnh ăn uống và vận động",
            "proposed_updates": {
                "food_recommendation": {"new_value": "Ăn rau và uống đủ nước"},
                "level_of_physical_activity": {"new_value": "medium"},
            },
        }

    monkeypatch.setattr(chatbot, "classify_message_scope", in_scope)
    monkeypatch.setattr(chatbot, "analyze_and_chat", generated)
    db = ProfileClient()
    app.dependency_overrides[token_authorization] = lambda: SimpleNamespace(
        client=db, user_id=f"proposal-{uuid4()}", user_email="eval@example.invalid"
    )
    try:
        with TestClient(app) as client:
            answer = client.post("/chatbot/ask", json={"message": "Nên ăn gì để vận động phù hợp?"})
            assert answer.status_code == 200
            proposal = answer.json()["proposal"]
            assert proposal["food_recommendation"] == "Ăn rau và uống đủ nước"
            assert proposal["level_of_physical_activity"] == "medium"
            assert db.writes == []
            saved = client.post("/chatbot/confirm-update", json={
                "status_flag": "maintain_activity",
                "food_recommendation": proposal["food_recommendation"],
                "level_of_physical_activity": proposal["level_of_physical_activity"],
            })
    finally:
        app.dependency_overrides.pop(token_authorization, None)
    assert saved.status_code == 200
    assert db.writes == [{
        "food_recommendation": "Ăn rau và uống đủ nước",
        "level_of_physical_activity": "medium",
    }]


def test_confirm_preserves_existing_health_flags_on_new_schema():
    db = CompleteProfileClient()
    app.dependency_overrides[token_authorization] = lambda: SimpleNamespace(
        client=db, user_id=f"proposal-{uuid4()}", user_email="eval@example.invalid"
    )
    try:
        with TestClient(app) as client:
            response = client.post("/chatbot/confirm-update", json={
                "status_flag": "restrict_heavy_exercise",
                "level_of_physical_activity": "heavy",
            })
    finally:
        app.dependency_overrides.pop(token_authorization, None)
    assert response.status_code == 200
    assert response.json()["health_state_saved"] is True
    assert response.json()["status_saved"] is True
    assert db.writes[0]["level_of_physical_activity"] == "light"
    assert db.health_writes[0]["active_health_flags"] == ["high_blood_pressure"]
