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


class MissingProfileTableColumn:
    def upsert(self, *_args, **_kwargs):
        raise MissingColumnError("column nickname does not exist")


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
