import json
from pathlib import Path
from datetime import date
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from app.core.database import supabase
from app.core.token_authorization import token_authorization, tokenAuthorization
from app.schemas.chatbot import ChatBotRequest, ChatBotResponse, ProfileUpdateProposal, ConfirmProposalRequest
from app.services.chatbot_agent import analyze_and_chat
from app.services.clinical_rag import get_medical_knowledge_stats, ingest_new_medical_document
from app.services.knowledge_ingestor import DEFAULT_KNOWLEDGE_DIR

router = APIRouter(prefix="/chatbot", tags=["AI Health ChatBot"])

# Bộ đếm số câu hỏi trong ngày theo user_id: {date_str: {user_id: count}}
# Tối đa 3 câu hỏi / ngày, lưu trữ file JSON bền vững để không bị mất khi restart server / re-login
DAILY_LIMIT = 3
USAGE_FILE = Path(__file__).resolve().parents[1] / "core" / "dataset" / "chatbot_daily_usage.json"
user_daily_questions = defaultdict(lambda: defaultdict(int))

def _load_persisted_usage():
    if USAGE_FILE.exists():
        try:
            with open(USAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for d_str, u_map in data.items():
                    for u_id, cnt in u_map.items():
                        user_daily_questions[d_str][u_id] = cnt
        except Exception:
            pass

def _save_persisted_usage():
    try:
        data = {d_str: dict(u_map) for d_str, u_map in user_daily_questions.items()}
        with open(USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# Khởi tạo dữ liệu đã lưu
_load_persisted_usage()

def _get_daily_count(user_id: str) -> int:
    today_str = date.today().isoformat()
    return user_daily_questions[today_str][user_id]

def _increment_daily_count(user_id: str):
    today_str = date.today().isoformat()
    user_daily_questions[today_str][user_id] += 1
    _save_persisted_usage()

@router.get("/quota")
async def get_chatbot_quota(
    auth_data: tokenAuthorization = Depends(token_authorization)
):
    """Lấy hạn mức số câu hỏi còn lại trong ngày của người dùng."""
    user_id = auth_data.user_id
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unauthorized")

    count = _get_daily_count(user_id)
    remaining = max(0, DAILY_LIMIT - count)
    return {
        "daily_limit": DAILY_LIMIT,
        "used_today": count,
        "remaining_questions_today": remaining,
        "date": date.today().isoformat()
    }

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
    if agent_output.get("has_update") or agent_output.get("has_proposed_changes"):
        proposal = ProfileUpdateProposal(
            has_update=True,
            has_proposed_changes=True,
            conflict_detected=agent_output.get("conflict_detected", False),
            conflict_explanation=agent_output.get("conflict_explanation"),
            conflict_message=agent_output.get("conflict_message"),
            summary_for_ui_card=agent_output.get("summary_for_ui_card"),
            food_recommendation=agent_output.get("suggested_food_recommendation"),
            level_of_physical_activity=agent_output.get("suggested_level_of_physical_activity"),
            reason=agent_output.get("reason"),
            verification_question=agent_output.get("verification_question") or "Bạn có đồng ý để FitBreak cập nhật thông tin này vào hồ sơ cá nhân không?",
            proposed_updates=agent_output.get("proposed_updates"),
            requires_user_confirmation=True
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


@router.get("/knowledge-stats")
async def get_knowledge_statistics():
    """Lấy thống kê kho tài liệu và các chunk RAG hiện có của Bác sĩ FitBreak."""
    return get_medical_knowledge_stats()


@router.post("/ingest-document")
async def ingest_medical_document(
    file: UploadFile = File(...),
    auth_data: tokenAuthorization = Depends(token_authorization)
):
    """
    Nạp tài liệu y khoa mới (.docx, .pdf, .md, .txt) vào kho tri thức RAG.
    Hệ thống sẽ tự động Document Parsing -> Chunking -> Cập nhật chỉ mục tìm kiếm.
    """
    if not auth_data.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unauthorized")

    filename = file.filename
    ext = Path(filename).suffix.lower()
    if ext not in [".docx", ".pdf", ".md", ".txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng '{ext}' không được hỗ trợ. Chỉ hỗ trợ .docx, .pdf, .md, .txt"
        )

    save_path = DEFAULT_KNOWLEDGE_DIR / filename
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    try:
        res = ingest_new_medical_document(save_path)
        return {
            "success": True,
            "message": f"Đã nạp và phân mảnh thành công tài liệu: {filename}",
            "details": res
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xử lý nạp tài liệu: {str(exc)}"
        )
