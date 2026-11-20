from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.token_authorization import tokenAuthorization, token_authorization
from app.schemas.userSchedule import UserScheduleUpsert


router = APIRouter(prefix="/user-schedules")


@router.get("/me")
async def get_my_schedule(
    token: tokenAuthorization = Depends(token_authorization),
):
    try:
        response = (
            token.client.table("user_schedules")
            .select("selected_time_slots,workout_schedule,updated_at")
            .eq("user_id", token.user_id)
            .maybe_single()
            .execute()
        )
        return response.data or {
            "selected_time_slots": [],
            "workout_schedule": {},
            "updated_at": None,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể tải lịch tập từ cơ sở dữ liệu",
        ) from exc


@router.put("/me")
async def save_my_schedule(
    data: UserScheduleUpsert,
    token: tokenAuthorization = Depends(token_authorization),
):
    try:
        payload = {
            "user_id": token.user_id,
            "selected_time_slots": data.selected_time_slots,
            "workout_schedule": data.workout_schedule,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        response = (
            token.client.table("user_schedules")
            .upsert(payload, on_conflict="user_id")
            .execute()
        )
        if not response.data:
            raise RuntimeError("Supabase returned no saved schedule")
        return response.data[0]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể lưu lịch tập vào cơ sở dữ liệu",
        ) from exc

