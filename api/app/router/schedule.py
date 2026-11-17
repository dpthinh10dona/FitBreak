from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.schedule import schedule
from app.core.token_authorization import tokenAuthorization, token_authorization
from app.services.schedule_service import schedule_maker
from app.services.safety_guardrail import UserHealthInput, safety_guardrail

router = APIRouter()

@router.post("/schedule-maker")
@router.post("/schedule/generate")
@router.post("/generate")
@router.post("/api/schedule")
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

        def _number(*values, default):
            for value in values:
                if value is not None:
                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        continue
            return default

        total_free_minutes = 0
        for slots in timetable_data.values() if isinstance(timetable_data, dict) else []:
            if isinstance(slots, dict):
                total_free_minutes += int(slots.get("available_minutes") or slots.get("max_session_minutes") or 0)
            elif isinstance(slots, list):
                total_free_minutes += sum(int(slot or 0) for slot in slots)

        guardrail = safety_guardrail(UserHealthInput(
            height_cm=_number(inp.get("height_cm"), stat.get("height"), default=170),
            weight_kg=_number(inp.get("weight_kg"), stat.get("weight"), default=60),
            age=int(_number(inp.get("age"), stat.get("age"), default=19)),
            goal=str(stat.get("goal") or inp.get("goal") or inp.get("aim") or "duy_tri"),
            target_calories=_number(inp.get("target_calories"), stat.get("tdee"), default=2000),
            budget_vnd=_number(inp.get("budget_vnd"), inp.get("daily_budget"), default=80000),
            allergies=inp.get("allergies") or [],
            medical_conditions=inp.get("medical_conditions") or stat.get("medical_conditions") or [],
            user_notes=str(inp.get("user_notes") or stat.get("user_notes") or ""),
            free_minutes_per_week=int(inp.get("free_minutes_per_week") or total_free_minutes),
        ))
        if not guardrail.allow_ai_generation:
            blocked = guardrail.model_dump()
            return {"success": False, "guardrail": blocked, **blocked}

        result = await schedule_maker(user_info)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
