from types import SimpleNamespace
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

from app.core.token_authorization import token_authorization
from app.main import app


class TeamRosterRpc:
    def __init__(self, rows):
        self.rows = rows
        self.name = None

    def rpc(self, name):
        self.name = name
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


def test_get_team_uses_authorized_public_roster_rpc():
    db = TeamRosterRpc([
        {"id": "00000000-0000-0000-0000-000000000001", "nickname": "Runner", "goal": "health"},
    ])
    app.dependency_overrides[token_authorization] = lambda: SimpleNamespace(client=db, user_id="ignored")
    try:
        with TestClient(app) as client:
            response = client.get("/get-team")
        assert response.status_code == 200
        assert response.json() == db.rows
        assert db.name == "get_my_team_roster"
    finally:
        app.dependency_overrides.clear()


