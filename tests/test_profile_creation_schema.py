"""Regression for the login onboarding failure when Supabase is not migrated."""

from types import SimpleNamespace
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from app.core.token_authorization import token_authorization
from app.main import app


class MissingColumnError(Exception):
    code = "42703"


class MissingInsertColumnError(Exception):
    code = "PGRST204"


class MissingProfileTableColumn:
    def select(self, _columns):
        return self

    def eq(self, _key, _value):
        return self

    def limit(self, _count):
        return self

    def execute(self):
        return SimpleNamespace(data=[])

    def upsert(self, *_args, **_kwargs):
        raise MissingInsertColumnError("column nickname missing from schema cache")


class FakeClient:
    def table(self, name):
        assert name == "profiles"
        return MissingProfileTableColumn()


def test_create_profile_reports_missing_migration():
    auth = SimpleNamespace(user_id="test-user", client=FakeClient())
    app.dependency_overrides[token_authorization] = lambda: auth
    try:
        with TestClient(app) as client:
            response = client.post("/profiles/create-profile", json={
                "nickname": "dpthinh",
                "birth_year": 2010,
                "gender": True,
                "height": 185,
                "weight": 80,
                "goal": "giảm cân",
                "activity_frequency": 1,
            })
        assert response.status_code == 503
        assert "migration" in response.json()["detail"]
        assert "dpthinh" not in response.text
    finally:
        app.dependency_overrides.clear()


class LegacyProfileTable:
    def __init__(self):
        self.columns = None
        self.write_count = 0

    def select(self, columns):
        self.columns = columns
        return self

    def eq(self, _key, _value):
        return self

    def limit(self, _count):
        return self

    def execute(self):
        if self.columns == "id":
            return SimpleNamespace(data=[{"id": "test-user"}])
        if self.columns != "*":
            raise MissingColumnError("column nickname does not exist")
        return SimpleNamespace(data=[{
            "id": "test-user", "name": "RunnerNick", "email": "private@example.com",
            "age": 16, "gender": True, "height": 185, "weight": 80,
            "goal": "giảm cân", "activity_frequency": 1, "bmi": 23.4, "tdee": 2100,
        }])

    def upsert(self, *_args, **_kwargs):
        self.write_count += 1
        raise AssertionError("Existing profile must not be overwritten")


def test_existing_legacy_profile_is_read_without_update():
    table = LegacyProfileTable()
    auth = SimpleNamespace(user_id="test-user", client=SimpleNamespace(table=lambda _name: table))
    app.dependency_overrides[token_authorization] = lambda: auth
    try:
        with TestClient(app) as client:
            response = client.get("/profiles/me")
            duplicate = client.post("/profiles/create-profile", json={
                "nickname": "new nickname", "birth_year": 2010, "gender": True,
                "height": 185, "weight": 80, "goal": "giảm cân", "activity_frequency": 1,
            })
        assert response.status_code == 200
        profile = response.json()
        assert profile["nickname"] == "RunnerNick"
        assert profile["birth_year"] >= 2000
        assert profile["bmi"] == 23.4 and profile["tdee"] == 2100
        assert "name" not in profile and "email" not in profile
        assert duplicate.status_code == 409
        assert table.write_count == 0
    finally:
        app.dependency_overrides.clear()
