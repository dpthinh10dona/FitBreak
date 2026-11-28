from fastapi import APIRouter, Depends, HTTPException, status
from app.core.token_authorization import tokenAuthorization, token_authorization
from app.schemas.joinTeam import joinTeam
from app.schemas.getTeam import getTeam

router = APIRouter()

@router.post("/join-team")
async def joinTeam(data: joinTeam, 
                   token: tokenAuthorization = Depends(token_authorization)):
    try:
        response = token.client.table("raid").select("team").eq("invite_code", str(data.invite_code)).limit(1).execute()
        stat = response.data
        if not stat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
        team = stat[0]["team"]

        token.client.table("stats").update({
            "team" : team
        }).eq("user_id", token.user_id).execute()

        return {"message" : "Join team successfully"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể tham gia đội")

@router.get("/get-team")
async def getTeam(token: tokenAuthorization = Depends(token_authorization)):
    try:
        user_stat = token.client.table("stats").select("team").eq("user_id", token.user_id).single().execute()
        if not user_stat.data or user_stat.data.get("team") is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User chưa thuộc team nào")

        current_team = user_stat.data["team"]

        team_stats = token.client.table("stats").select("user_id").eq("team", current_team).execute()
        if not team_stats.data:
            return []

        member_ids = [item["user_id"] for item in team_stats.data]

        profiles_response = token.client.table("profiles").select("id,nickname,goal").in_("id", member_ids).execute()

        return profiles_response.data

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể tải thông tin đội")

@router.get("/my-team-code")
async def my_team_code(token: tokenAuthorization = Depends(token_authorization)):
    response = token.client.table("stats").select("team").eq("user_id", token.user_id).single().execute()
    team = response.data.get("team") if response.data else None
    if team is None:
        return {"invite_code": None}
    invite = token.client.table("raid").select("invite_code").eq("team", team).single().execute()
    return {"invite_code": invite.data.get("invite_code") if invite.data else None}
