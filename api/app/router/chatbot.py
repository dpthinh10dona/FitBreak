import os
import uuid
import tempfile
import logging
import secrets
from pathlib import Path
from datetime import date
from fastapi import APIRouter, Depends, Header, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from app.core.database import supabase
from app.core.token_authorization import require_admin, token_authorization, tokenAuthorization
from app.schemas.chatbot import ChatBotRequest, ChatBotResponse, ProfileUpdateProposal, ConfirmProposalRequest
from app.services.chatbot_agent import (
    MissingMedicalInformationError,
    OutOfMedicalScopeError,
    analyze_and_chat,
    classify_message_scope,
    emergency_result,
    is_emergency_message,
    needs_clarification_result,
    out_of_scope_result,
)
from app.services.clinical_rag import get_medical_knowledge_stats, ingest_new_medical_document
from app.services.medical_storage import persist_medical_document
from app.services.runtime_store import daily_chatbot_quota
from app.services.knowledge_ingestor import DEFAULT_KNOWLEDGE_DIR, load_source_catalog
from app.services.pii_scrubber import scrub_symptom
from app.services.live_eval_trace import trace as live_eval_trace, force_gemini_failure

router = APIRouter(prefix="/chatbot", tags=["AI Health ChatBot"])
logger = logging.getLogger(__name__)

DAILY_LIMIT = 3


@router.get("/sources/{source_id}")
async def get_approved_medical_source(source_id: str):
    """Serve only a catalogued PDF so citations remain accessible without guessed external URLs."""
    for record in load_source_catalog(DEFAULT_KNOWLEDGE_DIR).values():
        if record.get("source_id") != source_id or record.get("verification_status") != "APPROVED":
            continue
        filename = Path(record.get("file", "")).name
        if not filename.lower().endswith(".pdf") or filename != record.get("file"):
            break
        target = DEFAULT_KNOWLEDGE_DIR / filename
        if target.is_file():
            return FileResponse(target, media_type="application/pdf", filename=filename)
        break
    raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu nguồn đã duyệt.")

@router.get("/quota")
async def get_chatbot_quota(
    auth_data: tokenAuthorization = Depends(token_authorization)
):
    """Lấy hạn mức số câu hỏi còn lại trong ngày của người dùng."""
    user_id = auth_data.user_id
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unauthorized")

    count = await daily_chatbot_quota.get(user_id)
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

    # 1. Giới hạn trực tiếp theo độ dài chuỗi: tối đa 100 ký tự.
    message = payload.message.strip()
    character_count = len(message)
    if character_count > 99:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Câu hỏi quá dài ({character_count} ký tự). Giới hạn tối đa 100 ký tự mỗi câu hỏi."
        )

    message = scrub_symptom(message)

    # 2. Ràng buộc số lượng câu hỏi trong ngày: Tối đa 3 câu/ngày
    current_count = 0 if live_eval_trace.get() is not None else await daily_chatbot_quota.get(user_id)
    # Cấp cứu được chặn bằng quy tắc xác định để không phụ thuộc vào độ trễ của model.
    if is_emergency_message(message):
        agent_output = emergency_result()
        return ChatBotResponse(
            reply=agent_output["reply"],
            remaining_questions_today=max(0, DAILY_LIMIT - current_count),
            proposal=None,
            status=agent_output["status"],
            reason_code=agent_output.get("reason_code"),
            allow_ai_generation=False,
        )

    # Dùng model hiểu ngữ nghĩa thay cho bộ lọc từ khóa cứng. Câu ngoài phạm vi
    # vẫn được chặn trước truy vấn hồ sơ/RAG và không trừ lượt hỏi.
    try:
        scope_status = await classify_message_scope(message)
    except OutOfMedicalScopeError:
        agent_output = out_of_scope_result()
        return ChatBotResponse(
            reply=agent_output["reply"],
            remaining_questions_today=max(0, DAILY_LIMIT - current_count),
            proposal=None,
            status=agent_output["status"],
            reason_code=agent_output["reason_code"],
            allow_ai_generation=False,
        )
    except MissingMedicalInformationError as exc:
        agent_output = needs_clarification_result(exc.clarification_question)
        return ChatBotResponse(
            reply=agent_output["reply"],
            remaining_questions_today=max(0, DAILY_LIMIT - current_count),
            proposal=None,
            status=agent_output["status"],
            reason_code=agent_output["reason_code"],
            allow_ai_generation=False,
        )
    except Exception as exc:
        logger.warning("Không thể phân loại phạm vi bằng model; tiếp tục theo luồng an toàn: %s", exc)
        scope_status = "IN_SCOPE"

    if scope_status == "OUT_OF_SCOPE":
        agent_output = out_of_scope_result()
        return ChatBotResponse(
            reply=agent_output["reply"],
            remaining_questions_today=max(0, DAILY_LIMIT - current_count),
            proposal=None,
            status=agent_output["status"],
            reason_code=agent_output.get("reason_code"),
            allow_ai_generation=False,
        )

    if current_count >= DAILY_LIMIT and live_eval_trace.get() is None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Bạn đã sử dụng hết 3 lượt tư vấn miễn phí hôm nay. Vui lòng quay lại vào ngày mai!"
        )

    # 3. Lấy profile hiện tại từ Supabase (dùng auth_data.client đã xác thực JWT)
    try:
        profile_res = auth_data.client.table("profiles").select("bmi,tdee,allergies").eq("id", user_id).execute()
    except Exception as exc:
        # Some deployed schemas predate the optional allergies column.
        if str(getattr(exc, "code", "")) != "42703" or "allergies" not in str(exc):
            raise
        profile_res = auth_data.client.table("profiles").select("bmi,tdee").eq("id", user_id).execute()
    user_profile = profile_res.data[0] if (profile_res.data and len(profile_res.data) > 0) else {}

    # 4. Gửi qua AI Agent phân tích
    agent_output = await analyze_and_chat(
        user_message=message,
        user_profile=user_profile,
        scope_status=scope_status,
    )

    # Chỉ trừ lượt khi hệ thống thực sự tạo được câu trả lời đã kiểm chứng.
    if agent_output.get("status", "PASS") == "PASS" and live_eval_trace.get() is None:
        current_count = await daily_chatbot_quota.increment(user_id)
    remaining = max(0, DAILY_LIMIT - current_count)

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
        reply=agent_output.get("reply", "Trợ lý FitBreak đã ghi nhận thông tin của bạn."),
        remaining_questions_today=remaining,
        proposal=proposal,
        retrieved_chunks=agent_output.get("retrieved_chunks", []),
        status=agent_output.get("status", "PASS"),
        reason_code=agent_output.get("reason_code", "ANSWER_AVAILABLE"),
        allow_ai_generation=agent_output.get("allow_ai_generation", True),
    )


@router.post("/live-eval", include_in_schema=False)
async def live_evaluate_chatbot(
    payload: ChatBotRequest,
    force_primary_failure: bool = False,
    x_live_eval_secret: str | None = Header(default=None),
    auth_data: tokenAuthorization = Depends(token_authorization),
):
    """Run the real chatbot path with request-scoped evidence and no daily quota usage."""
    expected = os.getenv("FITBREAK_LIVE_EVAL_SECRET", "")
    if (
        os.getenv("FITBREAK_LIVE_EVAL_ENABLED", "false").lower() != "true"
        or not expected
        or not x_live_eval_secret
        or not secrets.compare_digest(x_live_eval_secret, expected)
    ):
        raise HTTPException(status_code=404, detail="Not found")
    current = {"model_events": [], "retrieval_origin": None, "retrieved_rag_chunks": []}
    trace_token = live_eval_trace.set(current)
    failure_token = force_gemini_failure.set(force_primary_failure)
    try:
        response = await ask_health_chatbot(payload, auth_data)
        return {
            "user_query_scrubbed": scrub_symptom(payload.message),
            "chatbot_response": response.model_dump(),
            "trace": current,
        }
    finally:
        force_gemini_failure.reset(failure_token)
        live_eval_trace.reset(trace_token)

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

    notes = {
        "restrict_heavy_exercise": "Đang có cảnh báo hạn chế tập nặng",
        "maintain_activity": "Duy trì mức vận động phù hợp",
        "nutrition_review": "Cần xem lại chế độ dinh dưỡng",
    }
    update_fields = {"status_flag": payload.status_flag, "status_note": notes[payload.status_flag]}
    if payload.status_flag == "restrict_heavy_exercise":
        update_fields["level_of_physical_activity"] = "light"

    auth_data.client.table("profiles").update(update_fields).eq("id", user_id).execute()

    # Lưu active_health_flags vào bảng health_states để liên thông sang Lịch tập & Thực đơn
    active_flags = payload.health_flags
    if active_flags is None:
        if payload.status_flag == "restrict_heavy_exercise":
            active_flags = ["high_blood_pressure", "chest_pain_or_fatigue"]
        elif payload.status_flag == "maintain_activity":
            active_flags = []
        else:
            active_flags = ["chest_pain_or_fatigue"]

    try:
        auth_data.client.table("health_states").upsert(
            {
                "user_id": user_id,
                "active_health_flags": active_flags,
                "status_flag": payload.status_flag,
            },
            on_conflict="user_id",
        ).execute()
    except Exception:
        pass

    return {
        "success": True,
        "message": "Đã cập nhật hồ sơ cá nhân hóa thành công!",
        "updated": update_fields,
        "active_health_flags": active_flags,
    }


@router.delete("/health-flags")
async def clear_active_health_flags(
    auth_data: tokenAuthorization = Depends(token_authorization),
):
    """Gỡ bỏ trạng thái cảnh báo sức khỏe khi chỉ số người dùng đã ổn định."""
    user_id = auth_data.user_id
    try:
        auth_data.client.table("profiles").update(
            {"status_flag": "maintain_activity", "status_note": "Chỉ số sức khỏe ổn định"}
        ).eq("id", user_id).execute()
    except Exception:
        pass
    try:
        auth_data.client.table("health_states").upsert(
            {
                "user_id": user_id,
                "active_health_flags": [],
                "status_flag": "maintain_activity",
            },
            on_conflict="user_id",
        ).execute()
    except Exception:
        pass
    return {"success": True, "active_health_flags": []}


@router.get("/knowledge-stats")
async def get_knowledge_statistics(
    auth_data: tokenAuthorization = Depends(require_admin),
):
    """Lấy thống kê kho tài liệu và các chunk RAG hiện có của Bác sĩ FitBreak."""
    return get_medical_knowledge_stats()


@router.post("/ingest-document")
async def ingest_medical_document(
    file: UploadFile = File(...),
    auth_data: tokenAuthorization = Depends(require_admin)
):
    """
    Nạp tài liệu y khoa mới (.docx, .pdf, .md, .txt) vào kho tri thức RAG.
    Hệ thống sẽ tự động Document Parsing -> Chunking -> Cập nhật chỉ mục tìm kiếm.
    """
    filename = Path(file.filename or "upload").name
    ext = Path(filename).suffix.lower()
    allowed_types = {
        ".pdf": {"application/pdf"},
        ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/zip"},
        ".md": {"text/markdown", "text/plain", "application/octet-stream"},
        ".txt": {"text/plain", "application/octet-stream"},
    }
    if ext not in allowed_types or file.content_type not in allowed_types[ext]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Định dạng hoặc MIME type của tài liệu không được hỗ trợ."
        )

    max_upload_bytes = int(os.getenv("MAX_UPLOAD_BYTES", str(8 * 1024 * 1024)))
    content = await file.read(max_upload_bytes + 1)
    if len(content) > max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Tài liệu vượt quá dung lượng cho phép.")

    if ext == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Nội dung file không phải PDF hợp lệ.")
    if ext == ".docx" and not content.startswith(b"PK\x03\x04"):
        raise HTTPException(status_code=400, detail="Nội dung file không phải DOCX hợp lệ.")
    if ext in {".md", ".txt"}:
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Tài liệu văn bản phải sử dụng UTF-8.")

    object_name = f"uploads/{uuid.uuid4().hex}{ext}"
    try:
        stored_remotely = persist_medical_document(object_name, content, file.content_type)
        with tempfile.TemporaryDirectory(prefix="fitbreak-ingest-") as temp_dir:
            save_path = Path(temp_dir) / filename
            save_path.write_bytes(content)
            res = ingest_new_medical_document(save_path)
        return {
            "success": True,
            "message": "Đã nạp và phân mảnh thành công tài liệu y khoa.",
            "storage_object": object_name if stored_remotely else None,
            "storage_persisted": stored_remotely,
            "details": res,
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể xử lý tài liệu được tải lên."
        )
