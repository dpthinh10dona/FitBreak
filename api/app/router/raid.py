from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.updateBossHealth import updateBossHealth
from app.schemas.defeatBoss import defeatBoss
from app.core.token_authorization import tokenAuthorization, token_authorization
from app.services.raid_service import apply_boss_damage, advance_to_next_boss

router = APIRouter()


def _require_same_team(token: tokenAuthorization, requested_team: int) -> None:
    result = token.client.table("stats").select("team").eq("user_id", token.user_id).single().execute()
    actual_team = result.data.get("team") if result.data else None
    if actual_team is None or int(actual_team) != int(requested_team):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Không có quyền truy cập raid của đội này")

IMAGE_MAPPING = {
    1: "quest_alligator.png",
    2: "quest_axolotl.png",
    3: "quest_chameleon.png",
    4: "quest_falcon.png",
    5: "quest_goldenknight3.png"
}

@router.get("/get-raid-boss/{team_name}")
async def get_raid_boss(team_name: str, token: tokenAuthorization = Depends(token_authorization)):
    try:
        try:
            team_id = int(team_name.replace("team", ""))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mã đội không hợp lệ")

        _require_same_team(token, team_id)

        raid_res = token.client.table("raid").select("*").eq("team", team_id).single().execute()
        raid_data = raid_res.data
        if not raid_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raid team not found")
        
        boss_id = raid_data.get("boss_id", 1)

        boss_res = token.client.table("boss").select("*").eq("id", boss_id).single().execute()
        boss_data = boss_res.data
        
        if not boss_data:
            boss_res = token.client.table("boss").select("*").order("id", desc=False).limit(1).execute()
            boss_data = boss_res.data[0] if boss_res.data else {}

        image_name = boss_data.get("image") or IMAGE_MAPPING.get(boss_data.get("id", 1), "quest_alligator.png")
        supabase_url = token.client.supabase_url
        image_url = f"{supabase_url}/storage/v1/object/public/boss/{image_name}"

        return {
            "boss_id": boss_data.get("id", 1),
            "boss_name": boss_data.get("name", "Unknown Boss"),
            "health": raid_data.get("health", 100), 
            "max_health": boss_data.get("health", 100),   
            "reward_coins": boss_data.get("reward_coins", 10),
            "image_url": image_url
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể tải raid")


@router.post("/update-boss-health")
async def updateBossHealth(data: updateBossHealth,
                           token: tokenAuthorization = Depends(token_authorization)):
    try:
        _require_same_team(token, data.team)
        stats = token.client.table("stats").select("damage").eq("user_id", token.user_id).single().execute()
        server_damage = int((stats.data or {}).get("damage") or 0)
        if server_damage <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tài khoản chưa có chỉ số sát thương hợp lệ")
        result = apply_boss_damage(token.client, data.team, server_damage)
        return {"message": "Update boss health success", **result}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể cập nhật raid")

@router.post("/defeat_boss")
async def defeatBoss(data: defeatBoss,
                     token: tokenAuthorization = Depends(token_authorization)):
    try:
        _require_same_team(token, data.team)
        raid = token.client.table("raid").select("boss_id,health").eq("team", data.team).single().execute()
        raid_data = raid.data or {}
        if int(raid_data.get("boss_id") or 0) != data.boss_id or int(raid_data.get("health") or 1) > 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Boss chưa bị đánh bại hoặc trạng thái không khớp")
        result = advance_to_next_boss(token.client, data.team)
        reward = result["reward_coins"]
        return {
            "message": f"Boss defeated! All team members received {reward} coins.",
            "next_boss": result["next_boss"]
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể hoàn tất raid")
