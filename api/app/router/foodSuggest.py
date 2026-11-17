from fastapi import APIRouter, Depends, HTTPException
from app.schemas.foodSuggestResponse import FoodSuggestResponse
from app.schemas.foodSuggestRequest import FoodSuggestRequest
from app.core.rate_limiter import RateLimiter
from app.services.rag_service import process_rag_pipeline
from app.services.safety_guardrail import UserHealthInput, safety_guardrail
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
async def food_suggest(req: FoodSuggestRequest):
    try:
        user_info = req.model_dump()
        health_fields = (req.height_cm, req.weight_kg, req.age, req.free_minutes_per_week)
        if all(value is not None for value in health_fields):
            guardrail = safety_guardrail(UserHealthInput(
                height_cm=req.height_cm,
                weight_kg=req.weight_kg,
                age=req.age,
                goal=req.aim,
                target_calories=req.calories_need,
                budget_vnd=req.daily_budget,
                allergies=[item.strip() for item in (req.allergen or "").replace(",", ";").split(";") if item.strip()],
                medical_conditions=req.medical_conditions,
                user_notes=req.user_notes,
                free_minutes_per_week=req.free_minutes_per_week,
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
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
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
