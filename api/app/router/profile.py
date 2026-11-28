import logging
from fastapi import APIRouter, Request, Response, Form, Depends, HTTPException, status
from app.schemas.createProfile import createProfile
from app.schemas.updateProfile import updateProfile
from app.schemas.medicalCheckup import MedicalCheckupRequest
from app.services.medical_checkup import medical_checkup
from app.core.calculate_user_stats import calculateBMI, calculateBMR, calculateTDEE, calculateProtein
from app.core.token_authorization import tokenAuthorization, token_authorization
from datetime import date

PROFILE_COLUMNS = (
    "id,nickname,birth_year,gender,height,weight,goal,activity_frequency,"
    "bmi,bmr,tdee,protein,allergies,food_recommendation,"
    "level_of_physical_activity,status_flag,status_note"
)



def _classify_level_of_physical_activity(
    weight: float,
    height: float,
    sys_val: int = None,
    dia_val: int = None,
    time_val: int = None,
    glycemic_val: int = None,
    spo2_val: int = None,
) -> str:
    """
    Quy tắc phân loại cường độ luyện tập (level_of_physical_activity):
    - Tình trạng dinh dưỡng bình thường (BMI 18.5 - 22.9): 'heavy'
    - Tiền béo phì (BMI 23.0 - 24.9): 'medium'
    - Còn lại (nhẹ cân < 18.5, béo phì >= 25.0, hoặc có chỉ số nguy cơ cao về tim mạch/đường huyết/SpO2): 'light'
    """
    # 1. Kiểm tra các rủi ro y tế cấp tính (nếu có đo đạc tại nhà)
    # Huyết áp cao (độ 1, độ 2) hoặc tụt huyết áp
    if sys_val is not None and dia_val is not None:
        if sys_val >= 140 or dia_val >= 90 or sys_val < 90 or dia_val < 60:
            return "light"

    # Đường huyết cao (tiểu đường) hoặc tụt đường huyết nguy hiểm
    if glycemic_val is not None and time_val is not None:
        if glycemic_val < 70:
            return "light"
        if time_val == 0 and glycemic_val >= 125:
            return "light"
        elif time_val == 1 and glycemic_val >= 200:
            return "light"
        elif time_val == 2 and glycemic_val >= 140:
            return "light"

    # Nồng độ oxy trong máu SpO2 dưới mức chuẩn (< 94%)
    if spo2_val is not None and spo2_val <= 93:
        return "light"

    # 2. Phân loại theo BMI (Bảng chuẩn thể trạng dinh dưỡng)
    if weight and height and height > 0:
        bmi = weight / ((height / 100) ** 2)
        if 18.5 <= bmi < 23.0:
            return "heavy"
        elif 23.0 <= bmi < 25.0:
            return "medium"
        else:
            return "light"

    return "medium"

def _generate_diet_recommendation_from_bmi(weight: float, height: float) -> str:
    if not weight or not height or height <= 0:
        return None
    bmi = weight / ((height / 100) ** 2)
    if bmi < 18.5:
        return "Thể trạng nhẹ cân: Cần bổ sung thêm calo thặng dư giàu dinh dưỡng (các loại hạt, quả bơ, thực phẩm giàu đạm) để hỗ trợ tăng cân và tăng cơ an toàn."
    elif bmi >= 25.0:
        return "Thể trạng thừa cân / béo phì: Ưu tiên thực đơn giảm thâm hụt calo nhẹ, tăng tỷ trọng protein nạc và rau xanh nhiều chất xơ, hạn chế đồ chiên xào nhiều dầu mỡ."
    elif bmi >= 23.0:
        return "Thể trạng tiền béo phì: Cần kiểm soát lượng tinh bột tinh chế và dầu mỡ, ưu tiên protein nạc và rau củ để duy trì vóc dáng săn chắc."
    return "Thể trạng cân đối: Duy trì chế độ ăn đa dạng dưỡng chất, phân bổ đều đặn Protein, Carb phức hợp và chất béo lành mạnh."

router = APIRouter()
logger = logging.getLogger(__name__)


def _profile_write_error(exc: Exception, operation: str, stage: str) -> HTTPException:
    """Report a safe, actionable error without exposing record contents."""
    code = str(getattr(exc, "code", "") or "")
    logger.error("Profile %s failed at %s (Supabase code=%s)", operation, stage, code or "unknown")
    if code in {"42703", "PGRST204", "PGRST205"} or (
        code == "23502" and stage in {"profiles.upsert", "stats.upsert"}
    ):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cơ sở dữ liệu chưa cập nhật cấu trúc hồ sơ (nickname, birth_year). Cần áp dụng migration dữ liệu trước khi tạo hồ sơ.",
        )
    if code == "42501":
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Máy chủ chưa có quyền ghi hồ sơ trên Supabase. Cần kiểm tra chính sách RLS cho tài khoản đã đăng nhập.",
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Không thể lưu hồ sơ ở bước xử lý dữ liệu. Vui lòng thử lại sau.",
    )

@router.post("/profiles/create-profile")
async def createProfile(request: Request, data: createProfile,
                        token: tokenAuthorization = Depends(token_authorization)):
    stage = "calculate"
    try:
        bmi = calculateBMI(data.weight, data.height)
        bmr = calculateBMR(data.weight, data.height, date.today().year - data.birth_year, data.gender)
        tdee = calculateTDEE(bmr, data.activity_frequency)
        protein = calculateProtein(data.weight, data.activity_frequency)
        food_rec = _generate_diet_recommendation_from_bmi(data.weight, data.height)
        phys_level = _classify_level_of_physical_activity(data.weight, data.height)

        profile_payload = {
            "id": token.user_id,
            "nickname": data.nickname,
            "birth_year": data.birth_year,
            "gender": data.gender,
            "height": data.height,
            "weight": data.weight,
            "goal": data.goal,
            "activity_frequency": data.activity_frequency,
            "bmi": bmi,
            "bmr": bmr,
            "tdee": tdee,
            "protein": protein,
            "food_recommendation": food_rec,
            "level_of_physical_activity": phys_level
        }
        stage = "profiles.upsert"
        token.client.table("profiles").upsert(
            profile_payload, on_conflict="id"
        ).execute()

        stage = "stats.select"
        current_stats = token.client.table("stats").select("team").eq("user_id", token.user_id).execute()
        if current_stats.data:
            max_new_team = current_stats.data[0]["team"]
        else:
            stage = "stats.next_team"
            team_response = token.client.table("stats").select("team").order("team", desc=True).limit(1).execute()
            if team_response.data is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Khong tim thay data")
            max_current_team = team_response.data[0]['team'] if team_response.data else 0
            max_new_team = max_current_team + 1

        if not current_stats.data:
            stage = "stats.upsert"
            token.client.table("stats").upsert({
                "user_id": token.user_id,
                "team": max_new_team,
                "damage": 1,
                "coins": 0
            }, on_conflict="user_id").execute()

        # dang su dung mock data
        stage = "boss.select"
        boss_response = token.client.table("boss").select("*").eq("id", 1).single().execute()
        boss_stat = boss_response.data
        if not boss_stat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Boss not exist")

        stage = "raid.upsert"
        token.client.table("raid").upsert({
            "team": max_new_team,
            "boss_id": boss_stat["id"],
            "boss_name": boss_stat["name"],
            "health": boss_stat["health"],
            "reward_coins": boss_stat["reward_coins"]
        }, on_conflict="team").execute()

        stage = "avatar.upsert"
        token.client.table("user").upsert({
            "user_id": token.user_id,
            "skin": "Orange Skin",
            "shirt": "Blue Shirt",
            "hair": "Black Hair",
            "background": None,
            "weapon": None
        }, on_conflict="user_id").execute()

        return {"message": "Tạo profile thành công"}
    except HTTPException:
        raise
    except Exception as exc:
        raise _profile_write_error(exc, "create", stage) from exc

@router.post("/profiles/update-profile")
async def updateProfile(request: Request, data: updateProfile,
                        token: tokenAuthorization = Depends(token_authorization)):
    stage = "calculate"
    try:
        bmi = calculateBMI(data.weight, data.height)
        bmr = calculateBMR(data.weight, data.height, date.today().year - data.birth_year, data.gender)
        tdee = calculateTDEE(bmr, data.activity_frequency)
        protein = calculateProtein(data.weight, data.activity_frequency)

        phys_level = _classify_level_of_physical_activity(data.weight, data.height)

        update_payload = {
            "id" : token.user_id,
            "nickname" : data.nickname,
            "birth_year" : data.birth_year,
            "gender" : data.gender,
            "height" : data.height,
            "weight" : data.weight,
            "goal" : data.goal,
            "activity_frequency" : data.activity_frequency,
            "bmi" : bmi,
            "bmr" : bmr,
            "tdee" : tdee,
            "protein": protein,
            "level_of_physical_activity": phys_level
        }

        # Giữ khuyến nghị chuyên môn từ lần khám nếu đã có; chỉ tạo khuyến nghị
        # BMI cơ bản cho hồ sơ chưa từng được đánh giá y tế.
        stage = "profiles.select"
        current_prof = token.client.table("profiles").select("food_recommendation").eq("id", token.user_id).execute()
        has_existing_rec = current_prof.data and current_prof.data[0].get("food_recommendation")
        if not has_existing_rec:
            update_payload["food_recommendation"] = _generate_diet_recommendation_from_bmi(
                data.weight, data.height
            )

        stage = "profiles.update"
        response = token.client.table("profiles").update(update_payload).eq("id", token.user_id).execute()
        saved_profile = {key: value for key, value in (response.data[0] if response.data else update_payload).items()
                         if key in PROFILE_COLUMNS.split(",")}
        return {
            "message": "Cập nhật profile thành công",
            "profile": saved_profile,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise _profile_write_error(exc, "update", stage) from exc

@router.get("/profiles/me")
async def getMyProfile(token: tokenAuthorization = Depends(token_authorization)):
    try:
        response = token.client.table("profiles").select(PROFILE_COLUMNS).eq("id", token.user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except HTTPException:
        raise
    except Exception:
        return None

@router.post("/profiles/medical-checkup")
async def analyze_medical_checkup(data: MedicalCheckupRequest, token: tokenAuthorization = Depends(token_authorization)):
    try:
        # Neu weight va height khong duoc gui len tu form y te, lay tu profile
        w = data.weight
        h = data.height
        if w is None or h is None:
            user_prof = token.client.table("profiles").select("weight, height").eq("id", token.user_id).execute()
            if user_prof.data and len(user_prof.data) > 0:
                p = user_prof.data[0]
                if w is None and p.get("weight"):
                    w = float(p["weight"])
                if h is None and p.get("height"):
                    h = float(p["height"])

        result = await medical_checkup(
            weight=w,
            height=h,
            sys=data.sys,
            dia=data.dia,
            time=data.time,
            glycemic_index=data.glycemic_index,
            spo2_index=data.spo2_index
        )

        # Cập nhật lời khuyên dinh dưỡng & level_of_physical_activity vào profiles
        update_data = {}
        diet_advices = result.get("recommendations", {}).get("diet_advice", [])
        if diet_advices:
            update_data["food_recommendation"] = "; ".join(diet_advices)

        # Tính toán mức độ vận động phù hợp dựa trên kết quả kiểm tra sức khỏe
        computed_phys_level = _classify_level_of_physical_activity(
            weight=w,
            height=h,
            sys_val=data.sys,
            dia_val=data.dia,
            time_val=data.time,
            glycemic_val=data.glycemic_index,
            spo2_val=data.spo2_index,
        )
        update_data["level_of_physical_activity"] = computed_phys_level

        try:
            token.client.table("profiles").update(update_data).eq("id", token.user_id).execute()
        except Exception as save_err:
            print(f"[WARN] Không thể cập nhật thông tin y tế vào profiles: {save_err}")

        return {"success": True, "result": result}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể xử lý dữ liệu khám sức khỏe")
