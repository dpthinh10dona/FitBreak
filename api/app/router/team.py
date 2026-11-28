import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.token_authorization import tokenAuthorization, token_authorization
from app.schemas.joinTeam import joinTeam

router = APIRouter()
logger = logging.getLogger(__name__)


def _team_roster_error(exc: Exception) -> HTTPException:
    """Return a safe, actionable roster error without exposing database data."""
    code = str(getattr(exc, "code", "") or "")
    logger.exception("Team roster query failed (Supabase code=%s)", code or "unknown")
    if code in {"42703", "42883", "PGRST202", "PGRST204", "PGRST205"}:
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cơ sở dữ liệu chưa cập nhật chức năng danh sách đội. Cần áp dụng migration team roster.",
        )
    if code == "42501":
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Máy chủ chưa có quyền đọc danh sách đội. Cần kiểm tra migration team roster và RLS.",
        )
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Không thể tải thông tin đội lúc này. Vui lòng thử lại sau.",
    )


@router.post("/join-team")
async def joinTeam(
    data: joinTeam,
    token: tokenAuthorization = Depends(token_authorization),
):
    try:
        response = token.client.table("raid").select("team").eq(
            "invite_code", str(data.invite_code)
        ).limit(1).execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

        token.client.table("stats").update({"team": response.data[0]["team"]}).eq(
            "user_id", token.user_id
        ).execute()
        return {"message": "Join team successfully"}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Joining team failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Không thể tham gia đội lúc này. Vui lòng thử lại sau.",
        )


@router.get("/get-team")
async def getTeam(token: tokenAuthorization = Depends(token_authorization)):
    try:
        # The RPC verifies membership and returns only public roster fields.
        # Direct multi-user profile reads conflict with owner-only RLS policies.
        response = token.client.rpc("get_my_team_roster").execute()
        return response.data or []
    except HTTPException:
        raise
    except Exception as exc:
        raise _team_roster_error(exc) from exc


@router.get("/my-team-code")
async def my_team_code(token: tokenAuthorization = Depends(token_authorization)):
    try:
        response = token.client.table("stats").select("team").eq(
            "user_id", token.user_id
        ).single().execute()
        team = response.data.get("team") if response.data else None
        if team is None:
            return {"invite_code": None}
        invite = token.client.table("raid").select("invite_code").eq("team", team).single().execute()
        return {"invite_code": invite.data.get("invite_code") if invite.data else None}
    except Exception:
        logger.exception("Loading team invite code failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Không thể tải mã mời đội lúc này. Vui lòng thử lại sau.",
        )
