from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.schedule import schedule
from app.core.token_authorization import tokenAuthorization, token_authorization
from app.services.schedule_service import schedule_maker

router = APIRouter()

@router.post("/schedule-maker")
@router.post("/schedule/generate")
@router.post("/generate")
async def scheduleMaker(inp: dict,
                        token: tokenAuthorization = Depends(token_authorization)):
    try:
        stat = {}
        try:
            response = token.client.table("profiles").select("*").eq("id", token.user_id).execute()
            if response.data and len(response.data) > 0:
                stat = response.data[0]
        except Exception as db_err:
            print(f"[WARN] Error fetching profile in scheduleMaker: {db_err}")

        goal = stat.get("goal")
        if goal == "giảm cân": 
            goal = 0
        elif goal == "tăng cơ":
            goal = 1
        elif goal == "duy trì":
            goal = 2
        else:
            goal = inp.get("aim", 0)

        # Lấy trực tiếp level_of_physical_activity từ bảng profiles hoặc từ payload input
        level_of_physical_activity = stat.get("level_of_physical_activity") or inp.get("level")
        
        # Nếu cột này còn NULL (user cũ chưa cập nhật), fallback theo BMI hoặc activity_frequency
        if not level_of_physical_activity:
            bmi = stat.get("bmi")
            weight = stat.get("weight")
            height = stat.get("height")
            if bmi is None and weight and height and height > 0:
                bmi = weight / ((height / 100) ** 2)

            if bmi is not None:
                if 18.5 <= bmi < 23.0:
                    level_of_physical_activity = "heavy"
                elif 23.0 <= bmi < 25.0:
                    level_of_physical_activity = "medium"
                else:
                    level_of_physical_activity = "light"
            else:
                act_freq = stat.get("activity_frequency")
                if act_freq == 3:
                    level_of_physical_activity = "heavy"
                elif act_freq == 2:
                    level_of_physical_activity = "medium"
                else:
                    level_of_physical_activity = "medium"

        # Bóc tách timetable từ payload: inp có thể là {"timetable": {...}, "level": ...} hoặc trực tiếp là timetable dict
        timetable_data = inp.get("timetable", inp) if isinstance(inp, dict) and "timetable" in inp else inp

        user_info = {
            "timetable": timetable_data,
            "level_of_physical_activity": level_of_physical_activity,
            "aim": goal
        }

        result = await schedule_maker(user_info)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
