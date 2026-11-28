"""Offline privacy evidence: HTTP routes use a strict in-memory Supabase double."""

import asyncio
import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "offline-test-key")
os.environ.setdefault("GEMINI_API_KEY", "offline-test-key")

from app.main import app
from app.core.token_authorization import token_authorization
from app.router import privacy
from app.services.chatbot_agent import run_personalization_engine
from app.services.pii_scrubber import anonymous_health_payload, scrub_pii

USER_ID = "user-1"
OTHER_ID = "user-2"


class FakeQuery:
    def __init__(self, tables, name):
        self.tables = tables
        self.name = name
        self.operation = "select"
        self.filter_key = None
        self.filter_value = None
        self.values = None

    def select(self, _columns):
        self.operation = "select"
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def update(self, values):
        self.operation = "update"
        self.values = values
        return self

    def eq(self, key, value):
        self.filter_key, self.filter_value = key, value
        return self

    def execute(self):
        assert self.filter_key is not None, "A user filter is required"
        rows = self.tables[self.name]
        matching = [row for row in rows if row.get(self.filter_key) == self.filter_value]
        if self.operation == "delete":
            self.tables[self.name] = [row for row in rows if row not in matching]
        elif self.operation == "update":
            for row in matching:
                row.update(self.values)
        return SimpleNamespace(data=deepcopy(matching))


class FakeSupabase:
    def __init__(self):
        self.tables = {
            "profiles": [{"id": USER_ID, "nickname": "Runner", "avatar": "dragon",
                          "status_flag": "restrict_heavy_exercise", "status_note": "warning"},
                         {"id": OTHER_ID, "nickname": "Other"}],
            "stats": [{"user_id": USER_ID, "xp": 42, "team": 1},
                      {"user_id": OTHER_ID, "xp": 9, "team": 2}],
            "raid": [{"team": 1}, {"team": 2}],
            "user": [{"user_id": USER_ID, "skin": "dragon"}],
            "vitals": [{"user_id": USER_ID, "pulse": 80}, {"user_id": OTHER_ID, "pulse": 70}],
            "health_states": [{"user_id": USER_ID, "status_flag": "warning"}],
            "workouts": [{"user_id": USER_ID, "exercise": "walk"}],
            "user_schedules": [{"user_id": USER_ID, "schedule": {}}],
            "exercise_logs": [{"user_id": USER_ID, "exercise_id": "x"}],
        }
        self.auth_users = {USER_ID, OTHER_ID}
        self.auth = SimpleNamespace(admin=SimpleNamespace(delete_user=self.delete_auth_user))

    def table(self, name):
        assert name in self.tables, f"Unexpected table: {name}"
        return FakeQuery(self.tables, name)

    def delete_auth_user(self, user_id):
        self.auth_users.remove(user_id)


@pytest.fixture
def api_client(monkeypatch):
    db = FakeSupabase()
    auth = SimpleNamespace(client=db, user_id=USER_ID, user_email="user@example.com")
    app.dependency_overrides[token_authorization] = lambda: auth
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "offline-service-role-key")
    monkeypatch.setattr(privacy, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(privacy, "create_client", lambda *_args: db)
    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        app.dependency_overrides.clear()


def test_pii_scrubbing_removes_sensitive_info():
    raw = "Tôi tên là Nguyễn Văn An, email an@example.com, gọi 0912345678 hoặc +84 912 345 678"
    clean = scrub_pii(raw)
    assert "[NAME]" in clean and "[EMAIL]" in clean
    assert clean.count("[PHONE]") == 2
    for secret in ("Nguyễn Văn An", "an@example.com", "0912345678", "+84 912 345 678"):
        assert secret not in clean


def test_llm_payload_is_strictly_anonymous(monkeypatch):
    captured = []

    async def fake_generate_chat(prompt, **_kwargs):
        captured.append(prompt)
        return json.dumps({"has_proposed_changes": False})

    monkeypatch.setattr("app.services.chatbot_agent.generate_chat", fake_generate_chat)
    profile = {"id": USER_ID, "nickname": "Nguyễn Văn An", "email": "an@example.com",
               "bmi": 22.1, "tdee": 2100, "allergies": ["Đậu phộng"]}
    symptom = "Tôi tên là Nguyễn Văn An, đau đầu"
    payload = anonymous_health_payload(profile, symptom)
    assert set(payload) == {"bmi", "tdee", "allergies", "symptom"}
    asyncio.run(run_personalization_engine(symptom, "Tư vấn chung.", profile))
    assert len(captured) == 1
    outgoing = captured[0]
    assert json.dumps(payload, ensure_ascii=False) in outgoing
    for secret in (USER_ID, "nickname", "Nguyễn Văn An", "an@example.com"):
        assert secret not in outgoing


def test_symptom_input_length_guardrail(api_client, monkeypatch):
    client, _db = api_client
    called = AsyncMock(side_effect=AssertionError("LLM must not be called"))
    monkeypatch.setattr("app.router.chatbot.classify_message_scope", called)
    response = client.post("/chatbot/ask", json={"message": "a" * 100})
    assert response.status_code == 422
    called.assert_not_awaited()


def test_clear_health_logs_preserves_account(api_client):
    client, db = api_client
    response = client.delete("/api/privacy/health-logs")
    assert response.status_code == 200, response.text
    assert db.table("vitals").select("*").eq("user_id", USER_ID).execute().data == []
    assert db.table("health_states").select("*").eq("user_id", USER_ID).execute().data == []
    profile = db.table("profiles").select("*").eq("id", USER_ID).execute().data[0]
    stats = db.table("stats").select("*").eq("user_id", USER_ID).execute().data[0]
    assert (profile["nickname"], profile["avatar"], stats["xp"]) == ("Runner", "dragon", 42)
    assert profile["status_flag"] is None and profile["status_note"] is None
    assert USER_ID in db.auth_users
    assert db.table("vitals").select("*").eq("user_id", OTHER_ID).execute().data


def test_hard_delete_account_and_all_data(api_client):
    client, db = api_client
    response = client.delete("/api/privacy/account")
    assert response.status_code == 200, response.text
    for table_name, key in privacy.USER_TABLES:
        assert db.table(table_name).select("*").eq(key, USER_ID).execute().data == [], table_name
    assert USER_ID not in db.auth_users
    assert OTHER_ID in db.auth_users
    assert db.table("profiles").select("*").eq("id", OTHER_ID).execute().data
    assert db.table("raid").select("*").eq("team", 1).execute().data == []
    assert db.table("raid").select("*").eq("team", 2).execute().data
