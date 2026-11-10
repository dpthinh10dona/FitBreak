import json
import logging
import re
from typing import Dict, Any, Optional

from app.core.ollama_client import generate_chat
from app.services.clinical_rag import retrieve_medical_docs

logger = logging.getLogger(__name__)

# ==============================================================================
# AGENT 1: BÁC SĨ TRỢ LÝ ẢO (CLINICAL AI ADVISOR) - RAG-FIRST & MARKDOWN
# ==============================================================================
CLINICAL_ADVISOR_PROMPT_TEMPLATE = """# ROLE & OBJECTIVE
Bạn là Bác sĩ Trợ lý Ảo (Clinical AI Advisor). Nhiệm vụ của bạn là tiếp nhận mô tả triệu chứng hoặc thắc mắc sức khỏe từ người dùng, đối chiếu với tài liệu y khoa được truy xuất (RAG) và tình trạng sức khỏe sẵn có trong hồ sơ cá nhân để đưa ra câu trả lời tư vấn khoa học, an toàn, dễ hiểu và thấu cảm.

---

# CONTEXT VARIABLES
Bạn được cung cấp 3 biến ngữ cảnh:
1. {{user_message}}:
{user_message}

2. {{retrieved_medical_docs}}:
{retrieved_medical_docs}

3. {{current_user_profile}}:
{current_user_profile}

---

# CORE INSTRUCTIONS

1. **Phân tích đối chiếu (RAG-First):**
   - Dùng {{retrieved_medical_docs}} làm cơ sở tri thức chính để giải thích nguyên nhân khả dĩ và hướng điều trị/chăm sóc.
   - Không tự suy diễn các chẩn đoán chuyên sâu ngoài phạm vi tài liệu và triệu chứng đã nêu.

2. **Cá nhân hoá theo hồ sơ sẵn có:**
   - Luôn đối chiếu với {{current_user_profile}}. Mọi lời khuyên sinh hoạt/ăn uống tạm thời phải an toàn, không xung đột với bệnh nền hay dị ứng đã lưu (ví dụ: người dùng đang có tiền sử dạ dày thì không khuyên dùng các loại nước chua nhiều axit dù tài liệu nói về bổ sung vitamin C).

3. **Cấu trúc câu trả lời:**
   - **Nhận định sơ bộ:** Tóm tắt tình trạng và lý do xuất hiện triệu chứng dựa trên tài liệu.
   - **Giải pháp & Lời khuyên tức thì:** Các bước chăm sóc tại nhà, hướng dẫn sinh hoạt/dinh dưỡng ngắn hạn.
   - **Dấu hiệu cảnh báo (Red Flags):** Chỉ rõ các triệu chứng nguy hiểm cần lập tức tới cơ sở y tế.
   - **Miễn trừ trách nhiệm y tế (Disclaimer):** Lời nhắc rõ ràng rằng đây là tư vấn tham khảo, không thay thế chẩn đoán chuyên khoa của bác sĩ.

---

# FORMAT RESTRICTIONS
- Trả về định dạng Markdown tiêu chuẩn (in đậm, danh sách gạch đầu dòng).
- KHÔNG bọc đầu ra trong JSON, KHÔNG sinh cú pháp code block ``` trừ khi viết công thức.
- KHÔNG tự động hỏi xác nhận lưu dữ liệu Supabase (việc này do Node UI xử lý riêng).
"""

# ==============================================================================
# AGENT 2: ĐỘNG CƠ CÁ NHÂN HOÁ DỮ LIỆU SỨC KHOẺ (PERSONALIZATION LOGIC ENGINE)
# ==============================================================================
PERSONALIZATION_ENGINE_PROMPT_TEMPLATE = """# ROLE & OBJECTIVE
Bạn là Động cơ Cá nhân hoá Dữ liệu Sức khoẻ (Personalization Logic Engine). Nhiệm vụ của bạn là phân tích cuộc hội thoại giữa người dùng và Agent y khoa, đánh giá xem có cần điều chỉnh 2 trường dữ liệu trên Supabase: `food_recommendation` (chế độ dinh dưỡng) và `level_of_physical_activity` (cường độ vận động) hay không, đồng thời kiểm tra xung đột logic y khoa nghiêm ngặt.

---

# CONTEXT VARIABLES
1. {{user_message}}:
{user_message}

2. {{agent_response}}:
{agent_response}

3. {{current_user_profile}}:
{current_user_profile}

---

# LOGIC & CONFLICT RESOLUTION RULES

1. **Phát hiện nhu cầu cập nhật:**
   - Chỉ đề xuất thay đổi khi người dùng có triệu chứng mới kéo dài, bệnh lý cấp tính, hoặc có sự thay đổi rõ ràng về thể trạng.
   - Nếu câu hỏi chỉ mang tính tò mò/hỏi hộ ("bệnh sởi lây qua đâu?", "uống gì tốt cho tim?"), đặt `has_proposed_changes = false`.

2. **Quy tắc phân giải xung đột (CRITICAL):**
   - **Hard Constraints (Ràng buộc cứng):** `health_metrics` cố định (tiểu đường, suy thận, gãy xương, tăng huyết áp, dị ứng). Đề xuất mới TUYỆT ĐỐI KHÔNG ĐƯỢC vi phạm các ràng buộc này.
     - *Ví dụ vi phạm:* Đề xuất tập cardio cường độ cao khi người dùng có tiền sử suy tim hoặc đang sốt cao; đề xuất ăn chuối/cam khi hồ sơ có chỉ số suy thận tăng kali huyết.
   - Khi phát hiện xung đột: Đặt `conflict_detected = true`, ghi rõ lý do vào `conflict_explanation` và điều chỉnh đề xuất sao cho an toàn nhất hoặc giữ nguyên giá trị cũ.
   - **Nguyên tắc bổ sung/hợp nhất (Merge):** Nếu đề xuất mới an toàn và chi tiết hoá thêm cho khuyến nghị hiện có, hãy tích hợp một cách hài hoà thay vì xoá bỏ hoàn toàn dữ liệu cũ.

3. **Cơ chế xác nhận người dùng (Human-in-the-Loop):**
   - Mọi thay đổi đều ở trạng thái đề xuất chờ duyệt (`requires_user_confirmation: true`).
   - Cung cấp dữ liệu ngắn gọn, dễ hiểu để Frontend render thành giao diện Action Card (thẻ xác nhận với 2 nút: [Đồng ý cập nhật] / [Bỏ qua]).

---

# OUTPUT FORMAT (STRICT JSON ONLY)
Chỉ trả về duy nhất một khối JSON hợp lệ, không kèm bất kỳ văn bản dẫn nhập hay kết luận nào:

{{
  "has_proposed_changes": true,
  "conflict_detected": false,
  "conflict_explanation": null,
  "summary_for_ui_card": "Tóm tắt ngắn gọn thay đổi (1-2 câu) để hiển thị trên UI Card cho người dùng đọc",
  "proposed_updates": {{
    "food_recommendation": {{
      "previous_value": "Giá trị hiện tại lấy từ profile",
      "new_value": "Nội dung dinh dưỡng mới được đề xuất",
      "reason": "Lý do dựa trên triệu chứng hiện tại"
    }},
    "level_of_physical_activity": {{
      "previous_value": "Mức vận động hiện tại",
      "new_value": "Nghỉ ngơi | Vận động nhẹ | Trung bình | Năng động",
      "reason": "Lý do điều chỉnh cường độ"
    }}
  }},
  "requires_user_confirmation": true
}}
"""

def format_user_profile(user_profile: Dict[str, Any]) -> str:
    """Format Supabase profile data into medical context string."""
    if not user_profile:
        return "Chưa có thông tin hồ sơ sức khỏe trên hệ thống."

    height = user_profile.get("height")
    weight = user_profile.get("weight")
    
    bmi_str = "Chưa đo"
    bmi_category = ""
    if height and weight and height > 0:
        bmi = weight / ((height / 100) ** 2)
        bmi_str = f"{bmi:.1f} kg/m²"
        if bmi < 18.5:
            bmi_category = "Nhẹ cân"
        elif bmi < 23:
            bmi_category = "Bình thường"
        elif bmi < 25:
            bmi_category = "Tiền béo phì"
        elif bmi < 30:
            bmi_category = "Béo phì độ I"
        else:
            bmi_category = "Béo phì độ II"

    food_rec = user_profile.get("food_recommendation") or "Chưa có lời khuyên dinh dưỡng cụ thể"
    activity_level = user_profile.get("level_of_physical_activity") or "Chưa xác định"
    allergies = user_profile.get("allergies") or "Không có dị ứng ghi nhận"

    metrics = user_profile.get("health_metrics")
    metrics_str = ""
    if isinstance(metrics, dict):
        bp = f"Huyết áp: {metrics.get('systolic', '')}/{metrics.get('diastolic', '')} mmHg" if 'systolic' in metrics else ""
        sugar = f"Đường huyết: {metrics.get('glycemic_index', '')} mg/dL" if 'glycemic_index' in metrics else ""
        cond = f"Bệnh lý/Lưu ý: {metrics.get('conditions', '')}" if 'conditions' in metrics else ""
        metrics_str = ", ".join(filter(None, [bp, sugar, cond]))

    profile_lines = [
        f"- Chỉ số thể trạng: Chiều cao {height or '?'} cm, Cân nặng {weight or '?'} kg | BMI: {bmi_str} ({bmi_category})",
        f"- Tiền sử dị ứng y khoa (ràng buộc cứng): {allergies}",
        f"- Chỉ số xét nghiệm/bệnh lý lâm sàng (Hard Constraints): {metrics_str or 'Không có ghi nhận bất thường'}",
        f"- Chế độ dinh dưỡng đang áp dụng (food_recommendation): \"{food_rec}\"",
        f"- Mức độ vận động hiện tại (level_of_physical_activity): \"{activity_level}\"",
    ]
    return "\n".join(profile_lines)


def map_activity_to_code(activity_str: Optional[str]) -> Optional[str]:
    """Map Vietnamese activity levels to database codes ('light', 'medium', 'heavy')."""
    if not activity_str:
        return None
    s = activity_str.strip().lower()
    if any(k in s for k in ["nghỉ ngơi", "nhẹ", "light", "phục hồi"]):
        return "light"
    elif any(k in s for k in ["trung bình", "medium", "vừa"]):
        return "medium"
    elif any(k in s for k in ["năng động", "heavy", "nặng", "cường độ cao"]):
        return "heavy"
    return "light"


async def run_clinical_advisor(
    user_message: str,
    user_profile: Dict[str, Any]
) -> str:
    """Agent 1: Clinical AI Advisor (RAG-First, Markdown only)."""
    retrieved_docs = retrieve_medical_docs(user_message, top_k=2)
    profile_formatted = format_user_profile(user_profile)

    prompt = CLINICAL_ADVISOR_PROMPT_TEMPLATE.format(
        user_message=user_message,
        retrieved_medical_docs=retrieved_docs,
        current_user_profile=profile_formatted
    )

    raw_response = await generate_chat(prompt, response_mime_type="text/plain")
    clinical_reply = raw_response.strip()

    # Clean code blocks if any
    if clinical_reply.startswith("```markdown"):
        clinical_reply = clinical_reply[len("```markdown"):].strip()
    if clinical_reply.startswith("```"):
        clinical_reply = clinical_reply[len("```"):].strip()
    if clinical_reply.endswith("```"):
        clinical_reply = clinical_reply[:-3].strip()

    return clinical_reply


async def run_personalization_engine(
    user_message: str,
    agent_response: str,
    user_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """Agent 2: Personalization Logic Engine (Conflict Detection & Strict JSON Schema)."""
    profile_formatted = format_user_profile(user_profile)

    prompt = PERSONALIZATION_ENGINE_PROMPT_TEMPLATE.format(
        user_message=user_message,
        agent_response=agent_response,
        current_user_profile=profile_formatted
    )

    try:
        raw_json = await generate_chat(prompt, response_mime_type="application/json")
        clean_json = raw_json.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()

        data = json.loads(clean_json)
        return data
    except Exception as e:
        logger.warning(f"Agent 2 (Personalization Engine) JSON parse failed: {e}. Falling back to default.")
        return {
            "has_proposed_changes": False,
            "conflict_detected": False,
            "conflict_explanation": None,
            "summary_for_ui_card": None,
            "proposed_updates": {
                "food_recommendation": None,
                "level_of_physical_activity": None
            },
            "requires_user_confirmation": True
        }


async def analyze_and_chat(
    user_message: str,
    user_profile: Dict[str, Any],
    history: list = None
) -> Dict[str, Any]:
    """
    FitBreak Multi-Agent Healthcare Telehealth Architecture:
    1. Agent 1 (Clinical AI Advisor): RAG-First, Markdown advice, empathetic, evidence-based.
    2. Agent 2 (Personalization Logic Engine): Strictly evaluates Supabase updates and clinical conflicts.
    3. UI Human-in-the-Loop Action Card: Renders proposal waiting for user confirmation.
    """
    try:
        # Step 1: Run Agent 1 (Clinical AI Advisor)
        clinical_reply = await run_clinical_advisor(user_message, user_profile)

        # Step 2: Run Agent 2 (Personalization Logic Engine)
        personalization = await run_personalization_engine(
            user_message=user_message,
            agent_response=clinical_reply,
            user_profile=user_profile
        )

        has_proposed = personalization.get("has_proposed_changes", False)
        proposed = personalization.get("proposed_updates") or {}

        # Extract food recommendation update
        food_update = proposed.get("food_recommendation")
        new_food_val = food_update.get("new_value") if isinstance(food_update, dict) else None

        # Extract physical activity update
        act_update = proposed.get("level_of_physical_activity")
        raw_act_val = act_update.get("new_value") if isinstance(act_update, dict) else None
        code_act_val = map_activity_to_code(raw_act_val)

        conflict_detected = personalization.get("conflict_detected", False)
        conflict_msg = personalization.get("conflict_explanation")
        summary_ui = personalization.get("summary_for_ui_card")

        return {
            "reply": clinical_reply,
            "has_update": has_proposed,
            "has_proposed_changes": has_proposed,
            "conflict_detected": conflict_detected,
            "conflict_explanation": conflict_msg,
            "conflict_message": conflict_msg,
            "summary_for_ui_card": summary_ui,
            "suggested_food_recommendation": new_food_val,
            "suggested_level_of_physical_activity": code_act_val,
            "suggested_level_display": raw_act_val,
            "reason": summary_ui,
            "verification_question": summary_ui or "Bạn có đồng ý để FitBreak cập nhật thông tin này vào hồ sơ cá nhân không?",
            "proposed_updates": proposed
        }

    except Exception as e:
        logger.error(f"Multi-Agent Telehealth execution error: {e}", exc_info=True)
        fallback_reply = (
            "**Nhận định sơ bộ:**\n"
            "Hệ thống ghi nhận câu hỏi của bạn. Kết nối mạng hiện đang chậm, "
            "tôi xin gửi khuyến cáo an toàn sơ bộ dựa trên hồ sơ thể trạng của bạn.\n\n"
            "**Giải pháp & Lời khuyên tức thì:**\n"
            "- Hãy tạm dừng các vận động mạnh và nghỉ ngơi tại nơi thoáng khí.\n"
            "- Uống nước ấm từng ngụm nhỏ, giữ ấm cơ thể và duy trì chế độ ăn thanh đạm.\n\n"
            "**Dấu hiệu cảnh báo (Red Flags):**\n"
            "- Nếu xuất hiện đau dữ dội, choáng ngất hoặc khó thở, vui lòng đến ngay cơ sở y tế gần nhất.\n\n"
            "**Miễn trừ trách nhiệm y tế (Disclaimer):**\n"
            "*Thông tin tư vấn mang tính chất hỗ trợ ban đầu và không thay thế chẩn đoán chuyên khoa của bác sĩ.*"
        )
        return {
            "reply": fallback_reply,
            "has_update": False,
            "has_proposed_changes": False,
            "conflict_detected": False,
            "conflict_explanation": None,
            "conflict_message": None,
            "summary_for_ui_card": None,
            "suggested_food_recommendation": None,
            "suggested_level_of_physical_activity": None,
            "reason": None,
            "verification_question": None,
            "proposed_updates": None
        }
