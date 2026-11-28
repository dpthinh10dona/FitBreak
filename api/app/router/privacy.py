"""Authenticated export and deletion of user owned data."""

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from supabase import create_client

from app.core.database import SUPABASE_URL
from app.core.token_authorization import tokenAuthorization, token_authorization

router = APIRouter(prefix="/api/privacy", tags=["Privacy Center"])

# profiles uses id; other application tables use user_id.
USER_TABLES = (
    ("vitals", "user_id"),
    ("health_states", "user_id"),
    ("workouts", "user_id"),
    ("user_schedules", "user_id"),
    ("exercise_logs", "user_id"),
    ("stats", "user_id"),
    ("user", "user_id"),
    ("profiles", "id"),
)
OPTIONAL_TABLES = {"vitals", "health_states", "workouts"}


def _missing_optional_table(exc: Exception, table_name: str) -> bool:
    return table_name in OPTIONAL_TABLES and str(getattr(exc, "code", "")) in {
        "42P01", "PGRST205",
    }


def _rows(client, table_name: str, key: str, user_id: str) -> list:
    try:
        return client.table(table_name).select("*").eq(key, user_id).execute().data or []
    except Exception as exc:
        if _missing_optional_table(exc, table_name):
            return []
        raise HTTPException(status_code=500, detail=f"Cannot verify {table_name}.") from exc


def _delete_and_verify(client, table_name: str, key: str, user_id: str) -> None:
    try:
        client.table(table_name).delete().eq(key, user_id).execute()
    except Exception as exc:
        if _missing_optional_table(exc, table_name):
            return
        raise HTTPException(status_code=500, detail=f"Cannot delete {table_name}.") from exc
    if _rows(client, table_name, key, user_id):
        raise HTTPException(status_code=500, detail=f"Deletion of {table_name} was incomplete.")


@router.get("/export")
async def export_user_data(auth: tokenAuthorization = Depends(token_authorization)):
    user_id = auth.user_id
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "email": auth.user_email,
        "data": {
            "profile": _rows(auth.client, "profiles", "id", user_id),
            "vitals": _rows(auth.client, "vitals", "user_id", user_id),
            "workouts": _rows(auth.client, "workouts", "user_id", user_id),
            "health_states": _rows(auth.client, "health_states", "user_id", user_id),
            "schedules": _rows(auth.client, "user_schedules", "user_id", user_id),
        },
    }


@router.delete("/health-logs")
async def clear_health_logs(auth: tokenAuthorization = Depends(token_authorization)):
    for table_name in ("vitals", "health_states"):
        _delete_and_verify(auth.client, table_name, "user_id", auth.user_id)
    try:
        auth.client.table("profiles").update({
            "status_flag": None, "status_note": None,
        }).eq("id", auth.user_id).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Cannot clear profile health state.") from exc
    profile = _rows(auth.client, "profiles", "id", auth.user_id)
    if profile and (profile[0].get("status_flag") or profile[0].get("status_note")):
        raise HTTPException(status_code=500, detail="Profile health state was not cleared.")
    return {"status": "success", "cleared_tables": ["vitals", "health_states"]}


@router.delete("/account")
async def delete_account_permanently(auth: tokenAuthorization = Depends(token_authorization)):
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not SUPABASE_URL or not service_role_key:
        raise HTTPException(status_code=500, detail="Account deletion is not configured.")
    if not auth.user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")

    try:
        admin_client = create_client(SUPABASE_URL, service_role_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Cannot initialize account deletion.") from exc

    owned_teams = {
        row["team"] for row in _rows(admin_client, "stats", "user_id", auth.user_id)
        if row.get("team") is not None
    }
    for table_name, key in USER_TABLES:
        _delete_and_verify(admin_client, table_name, key, auth.user_id)

    # Raid state belongs to a team. Keep it while another member still uses it.
    for team in owned_teams:
        if not admin_client.table("stats").select("user_id").eq("team", team).execute().data:
            try:
                admin_client.table("raid").delete().eq("team", team).execute()
            except Exception as exc:
                raise HTTPException(status_code=500, detail="Cannot delete unused team state.") from exc
            if admin_client.table("raid").select("team").eq("team", team).execute().data:
                raise HTTPException(status_code=500, detail="Unused team state was not deleted.")

    try:
        admin_client.auth.admin.delete_user(auth.user_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Cannot delete Auth account.") from exc
    return {"status": "success"}
