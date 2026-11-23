from fastapi import APIRouter, Depends, HTTPException
from app.schemas.foodSuggestResponse import FoodSuggestResponse
from app.schemas.foodSuggestRequest import FoodSuggestRequest
from app.core.rate_limiter import RateLimiter
from app.core.token_authorization import token_authorization, tokenAuthorization
from app.services.rag_service import process_rag_pipeline
from app.services.safety_guardrail import (
    DEFAULT_DISCLAIMER,
    UserHealthInput,
    safety_guardrail,
)
from app.core.exceptions import (
        AIModelOfflineException,
        InvalidResponseError,
        InvalidUserInformationError,
        ModelNotFoundError,
        NoMatchingFoodsError,
        RequestTimeoutError,
    )

router = APIRouter()

@router.post(
    "/food-suggest",
    response_model=FoodSuggestResponse,
    dependencies=[Depends(RateLimiter(times=5, seconds=60, scope="food-suggest"))],
)
@router.post("/api/suggest-meal", response_model=FoodSuggestResponse)
async def food_suggest(
    req: FoodSuggestRequest,
    token: tokenAuthorization = Depends(token_authorization),
):
    try:
        user_info = req.model_dump()

        # Không phụ thuộc hoàn toàn vào payload của frontend. Component có thể
        # được submit trước khi request tải profile hoàn tất, trong khi hồ sơ
        # Supabase thực tế đã có đủ dữ liệu.
        profile_response = (
            token.client.table("profiles")
            .select("*")
            .eq("id", token.user_id)
            .execute()
        )
        profile = profile_response.data[0] if profile_response.data else {}
        activity_minutes = {1: 60, 2: 120, 3: 180}

        height_cm = req.height_cm if req.height_cm is not None else profile.get("height")
        weight_kg = req.weight_kg if req.weight_kg is not None else profile.get("weight")
        age = req.age if req.age is not None else profile.get("age")
        free_minutes = req.free_minutes_per_week
        if free_minutes is None:
            free_minutes = profile.get("free_minutes_per_week")
        if free_minutes is None:
            try:
                free_minutes = activity_minutes.get(int(profile.get("activity_frequency")))
            except (TypeError, ValueError):
                free_minutes = None

        medical_conditions = req.medical_conditions or profile.get("medical_conditions") or []
        if not isinstance(medical_conditions, list):
            medical_conditions = [str(medical_conditions)]
        user_notes = req.user_notes or profile.get("user_notes") or ""

        user_info.update({
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "age": age,
            "free_minutes_per_week": free_minutes,
            "medical_conditions": medical_conditions,
            "user_notes": user_notes,
        })

        required_health_fields = {
            "chiều cao": height_cm,
            "cân nặng": weight_kg,
            "tuổi": age,
            "thời gian vận động mỗi tuần": free_minutes,
        }
        missing_fields = [
            field_name
            for field_name, value in required_health_fields.items()
            if value is None
        ]
        if missing_fields:
            blocked = {
                "status": "INSUFFICIENT_DATA",
                "bmi": 0.0,
                "bmi_category": "Chưa xác định",
                "reasons": [
                    "Hồ sơ sức khỏe chưa đủ dữ liệu để kiểm tra an toàn trước khi tạo thực đơn: "
                    + ", ".join(missing_fields)
                    + ". Vui lòng cập nhật hồ sơ sức khỏe rồi thử lại."
                ],
                "disclaimer": DEFAULT_DISCLAIMER,
                "allow_ai_generation": False,
            }
            return FoodSuggestResponse(
                success=False,
                result={"guardrail": blocked, **blocked},
                error="INSUFFICIENT_DATA",
            )

        guardrail = safety_guardrail(UserHealthInput(
            height_cm=height_cm,
            weight_kg=weight_kg,
            age=age,
            goal=req.aim,
            target_calories=req.calories_need,
            budget_vnd=req.daily_budget,
            allergies=[item.strip() for item in (req.allergen or "").replace(",", ";").split(";") if item.strip()],
            medical_conditions=medical_conditions,
            user_notes=user_notes,
            free_minutes_per_week=free_minutes,
        ))
        if not guardrail.allow_ai_generation:
            blocked = guardrail.model_dump()
            return FoodSuggestResponse(
                success=False,
                result={"guardrail": blocked, **blocked},
                error=guardrail.status,
            )
        result = await process_rag_pipeline(user_info)
        if result.get("allow_ai_generation") is False:
            return FoodSuggestResponse(
                success=False,
                result=result,
                error=result.get("status", "INSUFFICIENT_DATA"),
            )
        return FoodSuggestResponse(success=True, result=result)
    except HTTPException:
        raise
    except InvalidResponseError:
        return FoodSuggestResponse(
            success=False,
            result={
                "status": "INSUFFICIENT_DATA",
                "allow_ai_generation": False,
                "reasons": ["Món ăn do AI đề xuất không khớp đúng một dòng dữ liệu; chưa thể xác nhận nguồn và giá trị dinh dưỡng."],
                "disclaimer": DEFAULT_DISCLAIMER,
            },
            error="INSUFFICIENT_DATA",
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Không thể tạo thực đơn từ dữ liệu đã cung cấp")
    # except AIModelOfflineException as e:
    #     raise HTTPException(status_code=503, detail=f"Ollama offline: {e}")
    # except ModelNotFoundError as e:
    #     raise HTTPException(status_code=404, detail=str(e))
    # except InvalidUserInformationError as e:
    #     raise HTTPException(status_code=422, detail=str(e))
    # except NoMatchingFoodsError as e:
    #     raise HTTPException(status_code=404, detail=str(e))
    # except RequestTimeoutError as e:
    #     raise HTTPException(status_code=504, detail=str(e))
    # except InvalidResponseError as e:
    #     raise HTTPException(status_code=502, detail=f"LLM trả về không hợp lệ: {e}")
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Lỗi không xác định: {e}")
