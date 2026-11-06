from datetime import date
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import supabase
from app.core.token_authorization import token_authorization, tokenAuthorization
from app.schemas.chatbot import ChatBotRequest, ChatBotResponse, ProfileUpdateProposal, ConfirmProposalRequest
from app.services.chatbot_agent import analyze_and_chat

router = APIRouter(prefix="/chatbot", tags=["AI Health ChatBot"])

# Bộ đếm số câu hỏi trong ngày theo user_id: {date_str: {user_id: count}}
# Tối đa 3 câu hỏi / ngày
DAILY_LIMIT = 3
user_daily_questions = defaultdict(lambda: defaultdict(int))

def _get_daily_count(user_id: str) -> int:
    today_str = date.today().isoformat()
    return user_daily_questions[today_str][user_id]

def _increment_daily_count(user_id: str):
    today_str = date.today().isoformat()
    user_daily_questions[today_str][user_id] += 1

@router.post("/ask", response_model=ChatBotResponse)
async def ask_health_chatbot(
    payload: ChatBotRequest,
    auth_data: tokenAuthorization = Depends(token_authorization)
):
    user_id = auth_data.user_id
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unauthorized")

    # 1. Ràng buộc giới hạn từ: < 100 từ
    words = payload.message.strip().split()
    if len(words) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Câu hỏi quá dài ({len(words)} từ). Giới hạn tối đa dưới 100 từ mỗi câu hỏi!"
        )

    # 2. Ràng buộc số lượng câu hỏi trong ngày: Tối đa 3 câu/ngày
    current_count = _get_daily_count(user_id)
    if current_count >= DAILY_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Bạn đã sử dụng hết 3 lượt tư vấn miễn phí hôm nay. Vui lòng quay lại vào ngày mai!"
        )

    # 3. Lấy profile hiện tại từ Supabase
    profile_res = supabase.table("profiles").select("*").eq("id", user_id).execute()
    user_profile = profile_res.data[0] if (profile_res.data and len(profile_res.data) > 0) else {}

    # 4. Gửi qua AI Agent phân tích
    agent_output = await analyze_and_chat(
        user_message=payload.message,
        user_profile=user_profile,
        history=payload.history
    )

    # Tăng lượt đếm câu hỏi hôm nay
    _increment_daily_count(user_id)
    remaining = DAILY_LIMIT - _get_daily_count(user_id)

    # 5. Xây dựng đề xuất cập nhật nếu AI phát hiện thông tin mới
    proposal = None
    if agent_output.get("has_update"):
        proposal = ProfileUpdateProposal(
            has_update=True,
            food_recommendation=agent_output.get("suggested_food_recommendation"),
            level_of_physical_activity=agent_output.get("suggested_level_of_physical_activity"),
            reason=agent_output.get("reason"),
            conflict_detected=agent_output.get("conflict_detected", False),
            conflict_message=agent_output.get("conflict_message"),
            verification_question=agent_output.get("verification_question") or "Bạn có đồng ý để FitBreak cập nhật thông tin này vào hồ sơ cá nhân không?"
        )

    return ChatBotResponse(
        reply=agent_output.get("reply", "Bác sĩ FitBreak đã ghi nhận thông tin của bạn."),
        remaining_questions_today=remaining,
        proposal=proposal
    )

@router.post("/confirm-update")
async def confirm_profile_update(
    payload: ConfirmProposalRequest,
    auth_data: tokenAuthorization = Depends(token_authorization)
):
    """
    Chỉ khi người dùng bấm xác nhận 'Đúng / Đồng ý' thì thông tin mới được ghi vào Supabase.
    """
    user_id = auth_data.user_id
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unauthorized")

    update_fields = {}
    if payload.food_recommendation:
        update_fields["food_recommendation"] = payload.food_recommendation
    if payload.level_of_physical_activity:
        update_fields["level_of_physical_activity"] = payload.level_of_physical_activity

    if not update_fields:
        return {"success": False, "message": "Không có thông tin nào cần cập nhật."}

    supabase.table("profiles").update(update_fields).eq("id", user_id).execute()
    return {"success": True, "message": "Đã cập nhật hồ sơ cá nhân hóa thành công!", "updated": update_fields}
