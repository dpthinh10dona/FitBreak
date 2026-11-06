import json
import logging
from typing import Dict, Any, Optional
from app.core.ollama_client import generate_chat

logger = logging.getLogger(__name__)

async def analyze_and_chat(
    user_message: str,
    user_profile: Dict[str, Any],
    history: list = None
) -> Dict[str, Any]:
    """
    AI Agent 2 vai trò:
    1. Bác sĩ/Chuyên gia dinh dưỡng tư vấn chuẩn y khoa.
    2. Bộ trích xuất thông tin (food_recommendation & level_of_physical_activity).
    """
    current_food = user_profile.get("food_recommendation") or "Chưa có lời khuyên cụ thể"
    current_level = user_profile.get("level_of_physical_activity") or "Chưa xác định"
    height = user_profile.get("height")
    weight = user_profile.get("weight")

    system_prompt = f"""[ROLE]
Bạn là "FitBreak Health Doctor" - Trợ lý Bác sĩ Y học Thể thao & Dinh dưỡng lâm sàng thuộc nền tảng FitBreak.
Nhiệm vụ của bạn:
1. Trả lời câu hỏi sức khỏe, dinh dưỡng, triệu chứng, bệnh lý, bài tập của người dùng một cách ấm áp, khoa học và ngắn gọn (dưới 150 từ).
2. NẾU người dùng hỏi các chủ đề KHÔNG liên quan đến y tế, sức khỏe, thể dục, dinh dưỡng (ví dụ: code, chính trị, game ngoài lề,...), hãy lịch sự từ chối và hướng họ quay lại sức khỏe.
3. PHÂN TÍCH xem câu hỏi/triệu chứng của người dùng có chứa thông tin sức khỏe mới để cá nhân hóa hay không:
   - `food_recommendation`: Lời khuyên chế độ ăn (ví dụ người dùng bị đau dạ dày, tiểu đường, gout, dị ứng sữa, hạ đường huyết...).
   - `level_of_physical_activity`: Cường độ vận động phù hợp. CHỈ CHỌN 1 TRONG 3 GIÁ TRỊ: "light", "medium", "heavy".
     * "light": Người đang có bệnh mạn tính, đau xương khớp, huyết áp, mệt mỏi, thừa cân nhiều hoặc suy nhược.
     * "medium": Thể trạng vừa phải, tiền béo phì hoặc hồi phục nhẹ.
     * "heavy": Khỏe mạnh hoàn toàn, không bệnh lý giới hạn vận động.

[HỒ SƠ HIỆN TẠI TỪ HỆ THỐNG KIỂM TRA SỨC KHỎE FITBREAK]
- Chiều cao: {height} cm | Cân nặng: {weight} kg
- Cường độ tập luyện hiện tại trên hệ thống: "{current_level}"
- Lời khuyên dinh dưỡng hiện tại trên hệ thống: "{current_food}"

[QUY TẮC ĐỐI LẬP & TỔNG HỢP]
- Nếu thông tin người dùng đưa ra mâu thuẫn trực tiếp với dữ liệu kiểm tra sức khỏe (ví dụ hệ thống đang xếp "light" vì bệnh tim/BMI cao, nhưng người dùng nói muốn tập bài cực nặng "heavy"):
  -> Đặt `conflict_detected: true`, cảnh báo người dùng và ưu tiên tuân thủ chỉ số kiểm tra sức khỏe của hệ thống để an toàn tính mạng.
- Nếu người dùng cung cấp thông tin bệnh lý/tình trạng mới bổ ích:
  -> Hãy tổng hợp cùng với lời khuyên đang có để tạo ra phiên bản `suggested_food_recommendation` đầy đủ nhất.
  -> Đặt `has_update: true` và đưa ra `verification_question` ngắn gọn để hỏi ý kiến người dùng trước khi cập nhật.

[YÊU CẦU OUTPUT JSON THUẦN TÚY]
Chỉ trả về 1 JSON object hợp lệ:
{{
  "reply": "Nội dung trả lời tư vấn cho người dùng...",
  "has_update": false,
  "suggested_food_recommendation": null hoặc "chuỗi lời khuyên mới đã tổng hợp",
  "suggested_level_of_physical_activity": null hoặc "light" / "medium" / "heavy",
  "reason": "Lý do đề xuất cập nhật",
  "conflict_detected": false,
  "conflict_message": null hoặc "Cảnh báo đối lập với chỉ số kiểm tra sức khỏe...",
  "verification_question": null hoặc "Bạn có muốn FitBreak cập nhật thông tin này vào hồ sơ cá nhân của bạn không?"
}}
"""

    prompt = f"{system_prompt}\n\n[CÂU HỎI CỦA NGƯỜI DÙNG]:\n{user_message}"

    try:
        raw_response = await generate_chat(prompt)
        # Parse JSON
        clean_json = raw_response.strip()
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
        
        data = json.loads(clean_json)
        return data
    except Exception as e:
        logger.error(f"Chatbot agent error: {e}")
        return {
            "reply": "Chào bạn, tôi là Bác sĩ FitBreak. Hiện tại hệ thống đang phân tích triệu chứng của bạn, bạn có thể nêu rõ hơn cảm giác hoặc chỉ số sức khỏe của mình không?",
            "has_update": False,
            "suggested_food_recommendation": None,
            "suggested_level_of_physical_activity": None,
            "reason": None,
            "conflict_detected": False,
            "conflict_message": None,
            "verification_question": None
        }
