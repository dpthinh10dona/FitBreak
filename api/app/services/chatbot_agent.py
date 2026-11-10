import json
import logging
import re
from typing import Dict, Any, Optional

from app.core.ollama_client import generate_chat
from app.services.clinical_rag import retrieve_medical_docs

logger = logging.getLogger(__name__)

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

def format_user_profile(user_profile: Dict[str, Any]) -> str:
    """Format Supabase profile data into clear medical context."""
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

    # Health metrics (nếu có từ medical checkup)
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
        f"- Chỉ số xét nghiệm/bệnh lý lâm sàng: {metrics_str or 'Không có ghi nhận bất thường'}",
        f"- Chế độ dinh dưỡng đang áp dụng: \"{food_rec}\"",
        f"- Mức độ vận động hiện tại: \"{activity_level}\"",
    ]
    return "\n".join(profile_lines)


async def extract_profile_proposal(
    user_message: str,
    user_profile: Dict[str, Any],
    clinical_reply: str
) -> Dict[str, Any]:
    """
    Trích xuất đề xuất cập nhật hồ sơ (food_recommendation & level_of_physical_activity)
    cho Node UI xử lý riêng biệt mà không làm nhiễu câu trả lời lâm sàng.
    """
    clean_msg = user_message.lower()
    current_level = (user_profile.get("level_of_physical_activity") or "").lower()
    current_food = user_profile.get("food_recommendation") or ""

    proposal = {
        "has_update": False,
        "suggested_food_recommendation": None,
        "suggested_level_of_physical_activity": None,
        "reason": None,
        "conflict_detected": False,
        "conflict_message": None,
        "verification_question": "Bạn có muốn FitBreak cập nhật thông tin này vào hồ sơ cá nhân của bạn không?"
    }

    # 1. Phát hiện xung đột (Conflict)
    if "tập nặng" in clean_msg or "heavy" in clean_msg:
        if current_level == "light" or "tim" in current_food.lower() or "huyết áp" in current_food.lower():
            proposal["conflict_detected"] = True
            proposal["conflict_message"] = "Hồ sơ sức khỏe của bạn hiện được khuyến nghị ở mức 'Light' (vận động nhẹ/phục hồi). Việc tập nặng có thể gây nguy hiểm cho tim mạch hoặc cơ xương khớp."

    # 2. Nhận diện các vấn đề sức khỏe mới cần hạ mức vận động hoặc điều chỉnh dinh dưỡng
    stomach_keywords = ["đau dạ dày", "viêm loét", "trào ngược", "đau thượng vị", "đau bụng"]
    hypo_keywords = ["hạ đường huyết", "choáng váng", "chóng mặt", "tụt huyết áp", "ngất"]
    joint_keywords = ["đau khớp", "thoái hóa khớp", "chấn thương", "căng cơ", "đứt dây chằng", "đau lưng"]
    fatigue_keywords = ["kiệt sức", "mệt mỏi", "suy nhược", "sốt"]

    updates_food = []
    need_light_activity = False

    if any(k in clean_msg for k in stomach_keywords):
        updates_food.append("Ưu tiên thức ăn mềm, dễ tiêu hóa; kiêng đồ chua cay, nhiều dầu mỡ, cà phê, nước ngọt có ga và chất kích thích dạ dày")
        need_light_activity = True

    if any(k in clean_msg for k in hypo_keywords):
        updates_food.append("Chia nhỏ bữa ăn trong ngày để ổn định đường huyết, luôn mang theo đồ ăn nhẹ; bù nước và điện giải")
        need_light_activity = True

    if any(k in clean_msg for k in joint_keywords):
        need_light_activity = True

    if any(k in clean_msg for k in fatigue_keywords):
        need_light_activity = True

    if updates_food or (need_light_activity and current_level != "light"):
        proposal["has_update"] = True
        if updates_food:
            new_food_str = "; ".join(updates_food)
            # Kết hợp với lời khuyên cũ nếu chưa trùng
            if current_food and current_food != "Chưa có lời khuyên cụ thể":
                proposal["suggested_food_recommendation"] = f"{current_food}. Lưu ý mới: {new_food_str}."
            else:
                proposal["suggested_food_recommendation"] = new_food_str
            proposal["reason"] = "Phát hiện triệu chứng tiêu hóa/chuyển hóa mới cần tinh chỉnh chế độ dinh dưỡng"

        if need_light_activity and current_level != "light":
            proposal["suggested_level_of_physical_activity"] = "light"
            proposal["reason"] = (proposal["reason"] or "") + " - Đề xuất chuyển cường độ tập về 'Light' để bảo vệ cơ thể"

    return proposal


async def analyze_and_chat(
    user_message: str,
    user_profile: Dict[str, Any],
    history: list = None
) -> Dict[str, Any]:
    """
    Bác sĩ Trợ lý Ảo (Clinical AI Advisor) FitBreak:
    - RAG-First: Truy xuất tài liệu y khoa chuẩn xác.
    - Cá nhân hóa theo hồ sơ sức khỏe người dùng (health_metrics, food_recommendation, physical activity).
    - Trả lời bằng Markdown chuẩn (4 phần bắt buộc).
    - Không sinh JSON, không sinh cú pháp code block thừa.
    - Node UI tự động quản lý card xác nhận lưu Supabase.
    """
    # 1. RAG Retrieval
    retrieved_docs = retrieve_medical_docs(user_message, top_k=2)

    # 2. Format Profile
    profile_formatted = format_user_profile(user_profile)

    # 3. Build Full Clinical Prompt
    prompt = CLINICAL_ADVISOR_PROMPT_TEMPLATE.format(
        user_message=user_message,
        retrieved_medical_docs=retrieved_docs,
        current_user_profile=profile_formatted
    )

    try:
        # Gọi mô hình với text/plain để nhận văn bản Markdown tự nhiên
        raw_response = await generate_chat(prompt, response_mime_type="text/plain")
        clinical_reply = raw_response.strip()

        # Loại bỏ bọc code block nếu có
        if clinical_reply.startswith("```markdown"):
            clinical_reply = clinical_reply[len("```markdown"):].strip()
        if clinical_reply.startswith("```"):
            clinical_reply = clinical_reply[len("```"):].strip()
        if clinical_reply.endswith("```"):
            clinical_reply = clinical_reply[:-3].strip()

        # 4. Trích xuất Proposal ngầm cho Node UI
        proposal = await extract_profile_proposal(user_message, user_profile, clinical_reply)

        return {
            "reply": clinical_reply,
            "has_update": proposal.get("has_update", False),
            "suggested_food_recommendation": proposal.get("suggested_food_recommendation"),
            "suggested_level_of_physical_activity": proposal.get("suggested_level_of_physical_activity"),
            "reason": proposal.get("reason"),
            "conflict_detected": proposal.get("conflict_detected", False),
            "conflict_message": proposal.get("conflict_message"),
            "verification_question": proposal.get("verification_question")
        }

    except Exception as e:
        logger.error(f"Clinical AI Advisor error: {e}", exc_info=True)
        # Fallback an toàn dựa trên RAG
        fallback_reply = (
            "**Nhận định sơ bộ:**\n"
            "Hệ thống ghi nhận mô tả triệu chứng của bạn. Do kết nối mạng tạm thời bị gián đoạn, "
            "tôi xin đưa ra khuyến cáo an toàn sơ bộ dựa trên hồ sơ thể trạng của bạn.\n\n"
            "**Giải pháp & Lời khuyên tức thì:**\n"
            "- Hãy tạm dừng hoạt động thể chất và công việc, ngồi hoặc nằm nghỉ ngơi ở nơi thoáng mát.\n"
            "- Uống nước ấm từng ngụm nhỏ, giữ ấm cơ thể và theo dõi diễn biến sức khỏe.\n"
            "- Duy trì chế độ ăn thanh đạm, tránh các thực phẩm lạ, đồ cay nóng hoặc nhiều dầu mỡ.\n\n"
            "**Dấu hiệu cảnh báo (Red Flags):**\n"
            "- Nếu xuất hiện đau quặn dữ dội, choáng váng nặng, nôn ói nhiều hoặc khó thở, vui lòng đến ngay cơ sở y tế gần nhất.\n\n"
            "**Miễn trừ trách nhiệm y tế (Disclaimer):**\n"
            "*Thông tin tư vấn mang tính chất hỗ trợ ban đầu và không thay thế chẩn đoán chuyên khoa của bác sĩ.*"
        )
        return {
            "reply": fallback_reply,
            "has_update": False,
            "suggested_food_recommendation": None,
            "suggested_level_of_physical_activity": None,
            "reason": None,
            "conflict_detected": False,
            "conflict_message": None,
            "verification_question": None
        }
