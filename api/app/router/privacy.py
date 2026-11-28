import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import create_client
from app.core.token_authorization import token_authorization, tokenAuthorization
from app.core.database import SUPABASE_URL

router = APIRouter(prefix="/api/privacy", tags=["Privacy Center"])


def _safe_select_by_user(client, table_name: str, user_id: str) -> list:
    """Safely query rows belonging to user_id; returns [] if table is missing or empty."""
    try:
        res = client.table(table_name).select("*").eq("user_id", user_id).execute()
        return res.data or []
    except Exception:
        return []


def _safe_delete_by_user(client, table_name: str, user_id: str) -> bool:
    """Safely delete rows belonging to user_id; returns True if executed without error."""
    try:
        client.table(table_name).delete().eq("user_id", user_id).execute()
        return True
    except Exception:
        return False


@router.get("/export")
async def export_user_data(auth: tokenAuthorization = Depends(token_authorization)):
    """
    Xuất toàn bộ dữ liệu cá nhân của người dùng hiện tại dưới dạng JSON.
    """
    user_id = auth.user_id
    client = auth.client

    profile = _safe_select_by_user(client, "profiles", user_id)
    vitals = _safe_select_by_user(client, "vitals", user_id)
    workouts = _safe_select_by_user(client, "workouts", user_id)
    health_states = _safe_select_by_user(client, "health_states", user_id)
    schedules = _safe_select_by_user(client, "user_schedules", user_id)

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "email": auth.user_email,
        "data": {
            "profile": profile,
            "vitals": vitals,
            "workouts": workouts,
            "health_states": health_states,
            "schedules": schedules,
        },
    }


@router.delete("/health-logs")
async def clear_health_logs(auth: tokenAuthorization = Depends(token_authorization)):
    """
    Xóa sạch lịch sử sinh hiệu, ghi chú chỉ số cá nhân và trạng thái cảnh báo sức khỏe.
    Bảo toàn tài khoản Supabase Auth, Nickname, Avatar và điểm XP / cấp độ.
    """
    user_id = auth.user_id
    client = auth.client

    cleared = []
    for table in ("vitals", "health_states"):
        if _safe_delete_by_user(client, table, user_id):
            cleared.append(table)

    return {
        "status": "success",
        "message": "Đã xóa toàn bộ nhật ký sinh hiệu và trạng thái sức khỏe. Hồ sơ định danh và điểm XP được giữ nguyên.",
        "cleared_tables": cleared,
    }


@router.delete("/account")
async def delete_account_permanently(auth: tokenAuthorization = Depends(token_authorization)):
    """
    Xóa vĩnh viễn toàn bộ dữ liệu trên PostgreSQL và xóa tài khoản khỏi Supabase Auth
    bằng SUPABASE_SERVICE_ROLE_KEY.
    """
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not SUPABASE_URL or not service_role_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Thiếu cấu hình SUPABASE_SERVICE_ROLE_KEY trên máy chủ để thực hiện xóa tài khoản.",
        )

    admin_client = create_client(SUPABASE_URL, service_role_key)
    user_id = auth.user_id

    # 1. Xóa dữ liệu trên các bảng phụ thuộc trước, sau đó đến profiles
    for table in ("vitals", "health_states", "workouts", "user_schedules", "profiles"):
        _safe_delete_by_user(admin_client, table, user_id)

    # 2. Xóa vĩnh viễn user khỏi Supabase Auth
    try:
        admin_client.auth.admin.delete_user(user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể xóa tài khoản khỏi Supabase Auth: {str(exc)}",
        )

    return {
        "status": "success",
        "message": "Tài khoản và toàn bộ dữ liệu cá nhân đã được xóa vĩnh viễn.",
    }
