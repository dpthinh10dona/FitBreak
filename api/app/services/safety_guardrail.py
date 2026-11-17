"""Module Safety Guardrail cho nền tảng FitBreak.

Lớp kiểm duyệt an toàn y tế và tính hợp lệ của dữ liệu (Pre-processing & Post-processing Guardrails)
trước và sau khi gọi mô hình ngôn ngữ lớn (LLM - Ollama Llama 3.2 1B).
Đảm bảo ngăn chặn tuyệt đối các trường hợp nguy hiểm về mặt y khoa, chống chỉ định vận động/ăn uống,
hoặc các điều kiện thiếu hụt dữ liệu đầu vào.
"""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Dict, List, Literal, Optional
import pandas as pd
from pydantic import BaseModel, Field

# Khuyến cáo y khoa mặc định
DEFAULT_DISCLAIMER: str = (
    "FitBreak là hệ thống khuyến nghị lối sống và dinh dưỡng hỗ trợ học sinh - sinh viên, "
    "không thay thế chẩn đoán, tư vấn hay phác đồ điều trị chuyên khoa y tế. "
    "Khi có bệnh lý nền, chấn thương hoặc các dấu hiệu bất thường về thể chất, "
    "bạn bắt buộc phải tham khảo ý kiến bác sĩ hoặc chuyên gia y tế trước khi thực hiện."
)

# Từ điển các từ khóa bệnh lý nền, chấn thương & nhóm đặc biệt (viết thường, chuẩn Unicode NFC)
MEDICAL_KEYWORDS = [
    # Nhóm chuyển hóa / nội tiết / tim mạch
    "tiểu đường",
    "đái tháo đường",
    "huyết áp",
    "tim mạch",
    "suy thận",
    "gout",
    "gút",
    "mỡ máu",
    "gan nhiễm mỡ",
    "dạ dày",
    "rối loạn ăn uống",
    # Nhóm vận động / cơ xương khớp / hô hấp
    "chấn thương",
    "thoát vị đĩa đệm",
    "đau khớp",
    "gãy xương",
    "cột sống",
    "dây chằng",
    "hen suyễn",
    "khó thở",
    # Nhóm đối tượng y tế đặc biệt
    "mang thai",
    "có bầu",
    "cho con bú",
]


def strip_accents(text: str) -> str:
    """Loại bỏ dấu tiếng Việt để đối soát từ khóa dạng không dấu (case/accent insensitive)."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", text).lower().replace("đ", "d")


# Chuẩn bị danh sách từ khóa không dấu song song
UNACCENTED_KEYWORD_MAP = {kw: strip_accents(kw) for kw in MEDICAL_KEYWORDS}


class UserHealthInput(BaseModel):
    """Schema dữ liệu đầu vào về tình trạng sức khỏe và mục tiêu của người dùng."""

    height_cm: float = Field(..., gt=0, description="Chiều cao tính bằng cm")
    weight_kg: float = Field(..., gt=0, description="Cân nặng tính bằng kg")
    age: int = Field(..., description="Tuổi của người dùng")
    goal: str = Field(..., description="Mục tiêu: 'giam_can', 'tang_co', 'duy_tri'")
    target_calories: Optional[float] = Field(
        default=None, description="Calo mục tiêu/ngày (nếu có)"
    )
    budget_vnd: float = Field(..., ge=0, description="Ngân sách ăn uống mỗi ngày (VNĐ)")
    allergies: List[str] = Field(
        default_factory=list, description="Danh sách các dị ứng thức ăn"
    )
    medical_conditions: List[str] = Field(
        default_factory=list, description="Các bệnh lý người dùng đã tick chọn trên UI"
    )
    user_notes: Optional[str] = Field(
        default="", description="Ghi chú tự do do người dùng nhập vào"
    )
    free_minutes_per_week: int = Field(
        ..., ge=0, description="Tổng số phút rảnh trong tuần để tập luyện"
    )


class GuardrailResult(BaseModel):
    """Schema kết quả kiểm duyệt an toàn y tế và dữ liệu của FitBreak."""

    status: Literal["PASS", "MEDICAL_WARNING", "INSUFFICIENT_DATA"]
    bmi: float = Field(..., description="Chỉ số khối cơ thể (làm tròn 2 chữ số thập phân)")
    bmi_category: str = Field(..., description="Phân loại thể trạng theo chuẩn WHO/IDP")
    reasons: List[str] = Field(
        default_factory=list, description="Danh sách lý do cụ thể bằng tiếng Việt"
    )
    disclaimer: str = Field(
        default=DEFAULT_DISCLAIMER, description="Khuyến cáo y tế mặc định"
    )
    allow_ai_generation: bool = Field(
        ..., description="True chỉ khi status == 'PASS', cho phép gọi LLM"
    )


def classify_bmi(bmi: float) -> str:
    """Phân loại tình trạng thể trọng dựa trên chỉ số BMI."""
    if bmi < 16.0:
        return "Gầy độ III (Suy dinh dưỡng nặng)"
    elif bmi < 17.0:
        return "Gầy độ II (Thiếu cân vừa)"
    elif bmi < 18.5:
        return "Gầy độ I (Thiếu cân nhẹ)"
    elif bmi < 23.0:
        return "Bình thường (Chuẩn người châu Á)"
    elif bmi < 25.0:
        return "Tiền béo phì / Thừa cân nhẹ"
    elif bmi < 30.0:
        return "Béo phì độ I"
    elif bmi < 35.0:
        return "Béo phì độ II"
    else:
        return "Béo phì độ III (Béo phì bệnh lý nghiêm trọng)"


def scan_medical_keywords(text: str) -> List[str]:
    """Quét và nhận diện các từ khóa bệnh lý nền, chấn thương, mang thai.

    Hỗ trợ cả chuỗi tiếng Việt có dấu và không dấu cơ bản (accent-insensitive).
    """
    if not text:
        return []

    norm_text = unicodedata.normalize("NFC", text).lower()
    unaccented_text = strip_accents(norm_text)

    detected: List[str] = []
    for original_kw, unaccented_kw in UNACCENTED_KEYWORD_MAP.items():
        # Kiểm tra khớp từ khóa có dấu hoặc không dấu với word boundaries linh hoạt
        pattern_original = r"(?i)(?:\b|_)" + re.escape(original_kw) + r"(?:\b|_)"
        pattern_unaccented = r"(?i)(?:\b|_)" + re.escape(unaccented_kw) + r"(?:\b|_)"

        if re.search(pattern_original, norm_text) or re.search(
            pattern_unaccented, unaccented_text
        ):
            detected.append(original_kw)

    return detected


def safety_guardrail(user_input: UserHealthInput) -> GuardrailResult:
    """Hàm kiểm duyệt tiền xử lý (Pre-processing Safety Guardrail).

    Đánh giá an toàn y tế và tính khả thi của dữ liệu người dùng trước khi gọi LLM.
    Thứ tự ưu tiên kiểm tra:
    1. Cảnh báo y tế (MEDICAL_WARNING) - Ưu tiên cao nhất.
    2. Thiếu căn cứ dữ liệu (INSUFFICIENT_DATA) - Chỉ kích hoạt khi không có cảnh báo y tế.
    3. Hợp lệ (PASS) - Cho phép gọi LLM sinh thực đơn & bài tập.
    """
    # 1. Tính toán BMI
    height_m = user_input.height_cm / 100.0
    bmi = round(user_input.weight_kg / (height_m**2), 2)
    bmi_cat = classify_bmi(bmi)

    medical_warnings: List[str] = []
    insufficient_data_reasons: List[str] = []

    # --- NHÓM 1: KIỂM TRA NGƯỠNG BMI & ĐỘ TUỔI ---
    if bmi < 16.0:
        medical_warnings.append(
            f"Chỉ số BMI của bạn là {bmi:.2f} ({bmi_cat}). Đây là tình trạng suy dinh dưỡng/thiếu cân nghiêm trọng. "
            "Bạn bắt buộc phải thăm khám bác sĩ chuyên khoa dinh dưỡng hoặc cơ sở y tế để được lập phác đồ phục hồi thể trạng."
        )
    elif bmi >= 35.0:
        medical_warnings.append(
            f"Chỉ số BMI của bạn là {bmi:.2f} ({bmi_cat}). Bạn thuộc nhóm béo phì nguy cơ cao với chuyển hóa và tim mạch. "
            "Cần có sự theo dõi, chỉ định trực tiếp từ bác sĩ chuyên khoa trước khi áp dụng các chế độ ăn kiêng hay lịch tập luyện cường độ cao."
        )

    if user_input.age < 12 or user_input.age > 65:
        medical_warnings.append(
            f"Độ tuổi hiện tại của bạn là {user_input.age} tuổi, nằm ngoài dải đối tượng học sinh - sinh viên (12–24 tuổi) "
            "mà thuật toán mô hình hóa của FitBreak đã được huấn luyện và kiểm thử lâm sàng. "
            "Vui lòng tham vấn ý kiến chuyên gia y tế cho lứa tuổi phù hợp."
        )

    # --- NHÓM 2: KIỂM TRA NGƯỠNG CALO & MÂU THUẪN MỤC TIÊU ---
    if user_input.target_calories is not None:
        if user_input.target_calories < 1000:
            medical_warnings.append(
                f"Mức năng lượng mục tiêu {user_input.target_calories:.0f} kcal/ngày quá thấp (dưới 1000 kcal/ngày), "
                "tiềm ẩn nguy cơ hạ đường huyết, suy nhược chuyển hóa và teo cơ nghiêm trọng."
            )
        elif user_input.target_calories > 4500:
            medical_warnings.append(
                f"Mức năng lượng mục tiêu {user_input.target_calories:.0f} kcal/ngày vượt quá ngưỡng hấp thu và chuyển hóa sinh lý thông thường "
                "(trừ vận động viên chuyên nghiệp), có nguy cơ gây quá tải cho hệ tiêu hóa, gan và thận."
            )

    # Mâu thuẫn mục tiêu nguy hiểm: Đang thiếu cân nhưng vẫn muốn giảm cân
    norm_goal = user_input.goal.strip().lower()
    if bmi < 18.5 and norm_goal in ["giam_can", "giamcan", "weight_loss"]:
        medical_warnings.append(
            f"Chỉ số BMI hiện tại là {bmi:.2f} (đang ở mức thiếu cân/gầy), việc tiếp tục chọn mục tiêu 'Giảm cân' "
            "là phản khoa học và có thể dẫn đến rối loạn ăn uống, suy giảm miễn dịch nghiêm trọng."
        )

    # --- NHÓM 3: QUÉT TỪ KHÓA BỆNH LÝ NỀN & CHẤN THƯƠNG ---
    # Tổng hợp văn bản từ medical_conditions và user_notes
    combined_texts = list(user_input.medical_conditions)
    if user_input.user_notes:
        combined_texts.append(user_input.user_notes)

    full_medical_text = " ".join(combined_texts)
    detected_keywords = scan_medical_keywords(full_medical_text)

    if detected_keywords:
        unique_keywords = list(dict.fromkeys(detected_keywords))
        formatted_kw_list = ", ".join(f"'{kw}'" for kw in unique_keywords)
        medical_warnings.append(
            f"Phát hiện dấu hiệu/bệnh lý hoặc chống chỉ định y tế đặc biệt: {formatted_kw_list}. "
            "Hệ thống FitBreak không được phép tự động kê đơn hay lập bài tập cho các bệnh nhân có bệnh lý nền "
            "hoặc chấn thương thực thể khi chưa có chẩn đoán y khoa chính thức."
        )

    # NẾU CÓ CẢNH BÁO Y TẾ -> TRẢ VỀ MEDICAL_WARNING (Ưu tiên tuyệt đối)
    if medical_warnings:
        return GuardrailResult(
            status="MEDICAL_WARNING",
            bmi=bmi,
            bmi_category=bmi_cat,
            reasons=medical_warnings,
            disclaimer=DEFAULT_DISCLAIMER,
            allow_ai_generation=False,
        )

    # --- NHÓM 4: KIỂM TRA ĐIỀU KIỆN THIẾU CĂN CỨ DỮ LIỆU ---
    if user_input.budget_vnd < 25000:
        insufficient_data_reasons.append(
            f"Ngân sách ăn uống ({user_input.budget_vnd:,.0f} VNĐ/ngày) quá thấp, dưới ngưỡng tối thiểu 25,000 VNĐ/ngày. "
            "Cơ sở dữ liệu thực phẩm dinh dưỡng chuẩn y khoa không thể thiết lập thực đơn 3 bữa đảm bảo vi chất và calo với chi phí này."
        )

    if user_input.free_minutes_per_week < 30:
        insufficient_data_reasons.append(
            f"Tổng thời gian rảnh ({user_input.free_minutes_per_week} phút/tuần) không đạt mức tối thiểu 30 phút/tuần "
            "để thuật toán phân bổ ít nhất một buổi tập luyện phục hồi hoặc thích nghi thể chất."
        )

    if insufficient_data_reasons:
        return GuardrailResult(
            status="INSUFFICIENT_DATA",
            bmi=bmi,
            bmi_category=bmi_cat,
            reasons=insufficient_data_reasons,
            disclaimer=DEFAULT_DISCLAIMER,
            allow_ai_generation=False,
        )

    # --- TẤT CẢ ĐIỀU KIỆN ĐỀU AN TOÀN VÀ ĐỦ CĂN CỨ -> PASS ---
    return GuardrailResult(
        status="PASS",
        bmi=bmi,
        bmi_category=bmi_cat,
        reasons=["Tất cả chỉ số sức khỏe, thể trạng và dữ liệu đầu vào đều nằm trong ngưỡng an toàn."],
        disclaimer=DEFAULT_DISCLAIMER,
        allow_ai_generation=True,
    )


class MealsSufficiencyResult(BaseModel):
    """Schema kết quả kiểm tra độ đầy đủ của danh sách món ăn sau lọc (Post-filter)."""

    status: Literal["PASS", "INSUFFICIENT_DATA"]
    allow_ai_generation: bool = Field(..., description="True chỉ khi status == 'PASS'")
    valid_items_count: int = Field(..., description="Số lượng món ăn hợp lệ đếm được")
    reasons: List[str] = Field(default_factory=list, description="Danh sách lý do chi tiết bằng tiếng Việt")
    suggestion: str = Field(default="", description="Gợi ý hành động khắc phục cho người dùng")


def check_filtered_meals_sufficiency(
    filtered_df: pd.DataFrame,
    target_calories: float,
    daily_budget_vnd: float,
    min_required_items: int = 3,
) -> MealsSufficiencyResult:
    """Kiểm tra tính đầy đủ của dữ liệu món ăn sau bước lọc Pandas (Post-filter Data Sufficiency Check).

    Chặn gọi LLM Llama 3.2 1B khi dữ liệu còn lại không đủ số lượng tối thiểu,
    không đủ ngân sách hoặc không thể đáp ứng mức calo mục tiêu (chống hallucination).

    Args:
        filtered_df: DataFrame món ăn sau bộ lọc dị ứng và chế độ ăn.
                     Chứa các cột: id, ten_mon (hoặc name), calories, price_vnd (hoặc cost_vnd).
        target_calories: Mức calo mục tiêu 1 ngày của người dùng (kcal).
        daily_budget_vnd: Ngân sách ăn uống tối đa 1 ngày của người dùng (VNĐ).
        min_required_items: Số lượng món tối thiểu cho 3 bữa (mặc định 3).

    Returns:
        MealsSufficiencyResult (status, allow_ai_generation, valid_items_count, reasons, suggestion).
    """
    reasons: List[str] = []
    default_suggestion = (
        "Bạn có thể thử tăng ngân sách ngày hoặc điều chỉnh lại danh sách thực phẩm loại trừ để mở rộng lựa chọn."
    )

    # 1. Kiểm tra an toàn DataFrame rỗng hoặc thiếu số lượng tối thiểu
    if filtered_df is None or filtered_df.empty:
        return MealsSufficiencyResult(
            status="INSUFFICIENT_DATA",
            allow_ai_generation=False,
            valid_items_count=0,
            reasons=[
                f"Kho dữ liệu đã xác minh chỉ còn 0 món phù hợp sau khi loại trừ dị ứng/chế độ ăn, "
                f"không đủ tối thiểu {min_required_items} món để lập thực đơn 3 bữa."
            ],
            suggestion=default_suggestion,
        )

    # Chuẩn hóa & làm sạch DataFrame: loại bỏ NaN ở các cột cần kiểm tra
    df_clean = filtered_df.copy()

    # Nhận diện cột giá linh hoạt
    price_col = None
    for col in ["price_vnd", "cost_vnd", "price", "cost"]:
        if col in df_clean.columns:
            price_col = col
            break

    # Nhận diện cột calo linh hoạt
    cal_col = "calories" if "calories" in df_clean.columns else None

    # Làm sạch các giá trị không hợp lệ hoặc NaN
    if price_col:
        df_clean[price_col] = pd.to_numeric(df_clean[price_col], errors="coerce").fillna(float("inf"))
    if cal_col:
        df_clean[cal_col] = pd.to_numeric(df_clean[cal_col], errors="coerce").fillna(0.0)

    valid_items_count = len(df_clean)

    # Logic 1: len(filtered_df) < min_required_items
    if valid_items_count < min_required_items:
        reasons.append(
            f"Kho dữ liệu đã xác minh chỉ còn {valid_items_count} món phù hợp sau khi loại trừ dị ứng/chế độ ăn, "
            f"không đủ tối thiểu {min_required_items} món để lập thực đơn 3 bữa."
        )
        return MealsSufficiencyResult(
            status="INSUFFICIENT_DATA",
            allow_ai_generation=False,
            valid_items_count=valid_items_count,
            reasons=reasons,
            suggestion=default_suggestion,
        )

    # Logic 2: Kiểm tra khả năng đáp ứng Ngân sách (price_vnd)
    if price_col and daily_budget_vnd > 0:
        # Lấy 3 món có giá rẻ nhất trong filtered_df
        cheapest_3 = df_clean.nsmallest(min_required_items, price_col)
        total_cheapest_price = float(cheapest_3[price_col].sum())

        if total_cheapest_price > daily_budget_vnd:
            reasons.append(
                f"Ngân sách hiện tại không đủ để kết hợp 3 bữa ăn tối thiểu từ các món hợp lệ "
                f"(chi phí thấp nhất cần {total_cheapest_price:,.0f} VNĐ cho 3 món rẻ nhất, "
                f"vượt ngân sách {daily_budget_vnd:,.0f} VNĐ/ngày)."
            )

    # Logic 3: Kiểm tra khả năng đáp ứng Calo (calories)
    if cal_col and target_calories > 0:
        # Lấy 3 món có calo cao nhất trong filtered_df
        top_3_cal = df_clean.nlargest(min_required_items, cal_col)
        total_max_calories = float(top_3_cal[cal_col].sum())
        calorie_threshold = target_calories * 0.80  # Hụt quá 20%

        if total_max_calories < calorie_threshold:
            reasons.append(
                f"Các món ăn còn lại sau bộ lọc không đủ mức năng lượng cần thiết cho mục tiêu của bạn "
                f"(tổng calo 3 món cao nhất chỉ đạt {total_max_calories:.0f} kcal, "
                f"hụt quá 20% so với mục tiêu {target_calories:.0f} kcal/ngày)."
            )

    # NẾU CÓ BẤT KỲ ĐIỀU KIỆN KHÔNG THỎA MÃN -> INSUFFICIENT_DATA
    if reasons:
        return MealsSufficiencyResult(
            status="INSUFFICIENT_DATA",
            allow_ai_generation=False,
            valid_items_count=valid_items_count,
            reasons=reasons,
            suggestion=default_suggestion,
        )

    # THỎA MÃN TẤT CẢ ĐIỀU KIỆN -> PASS
    return MealsSufficiencyResult(
        status="PASS",
        allow_ai_generation=True,
        valid_items_count=valid_items_count,
        reasons=[
            f"Dữ liệu món ăn đầy đủ ({valid_items_count} món khả dụng), đáp ứng tốt calo mục tiêu và ngân sách."
        ],
        suggestion="Dữ liệu hợp lệ, sẵn sàng để mô hình AI xây dựng thực đơn tối ưu.",
    )


def check_meal_data_sufficiency(
    filtered_foods_df: pd.DataFrame,
    target_calories: float,
    daily_budget_vnd: float,
) -> Dict[str, Any]:
    """Kiểm tra tính đầy đủ và khả thi của DataFrame món ăn sau bước lọc Pandas (Post-filter).

    Đảm bảo mô hình LLM (Llama 3.2 1B) có đủ dữ liệu để xếp thực đơn 3 bữa (Sáng, Trưa, Tối)
    mà không bị ép phải bịa món mới (hallucination) hoặc lặp lại cùng một món.

    Args:
        filtered_foods_df: DataFrame món ăn sau khi lọc dị ứng và chế độ ăn.
                           Hỗ trợ các cột: calories, price_vnd (hoặc cost_vnd), ten_mon (hoặc name).
        target_calories: Calo mục tiêu người dùng cần nạp mỗi ngày (TDEE).
        daily_budget_vnd: Ngân sách ăn uống tối đa mỗi ngày của người dùng (VNĐ).

    Returns:
        dict gồm:
            - status: "PASS" hoặc "INSUFFICIENT_DATA"
            - allow_ai_generation: bool (True chỉ khi status == "PASS")
            - available_count: int (số lượng món hợp lệ còn lại trong DataFrame)
            - reasons: List[str] (danh sách lý do cụ thể bằng tiếng Việt)
            - suggestion: str (hướng dẫn cụ thể cho người dùng khắc phục)
    """
    reasons: List[str] = []
    suggestions: List[str] = []

    # 1. Kiểm tra an toàn DataFrame rỗng
    if filtered_foods_df is None or filtered_foods_df.empty:
        return {
            "status": "INSUFFICIENT_DATA",
            "allow_ai_generation": False,
            "available_count": 0,
            "reasons": [
                "Sau khi lọc theo chế độ ăn và danh sách dị ứng, không còn món ăn nào khả dụng trong cơ sở dữ liệu."
            ],
            "suggestion": (
                "Vui lòng kiểm tra lại danh sách dị ứng hoặc chuyển chế độ ăn sang 'Không kiêng' "
                "để hệ thống có thể tiếp cận nguồn thực phẩm đa dạng hơn."
            ),
        }

    available_count = len(filtered_foods_df)

    # Nhận diện cột calo và giá linh hoạt (hỗ trợ cả calories/cost_vnd và calories/price_vnd)
    cal_col = "calories" if "calories" in filtered_foods_df.columns else None
    price_col = None
    for candidate in ["price_vnd", "cost_vnd", "price", "cost"]:
        if candidate in filtered_foods_df.columns:
            price_col = candidate
            break

    # Điều kiện 1: Thiếu số lượng tối thiểu cho 3 bữa (yêu cầu >= 3 món khác nhau)
    if available_count < 3:
        reasons.append(
            f"Sau khi lọc dị ứng và chế độ ăn, hệ thống chỉ tìm thấy {available_count} món hợp lệ "
            "(yêu cầu tối thiểu 3 món ăn khác nhau để thiết lập thực đơn 3 bữa Sáng - Trưa - Tối không trùng lặp)."
        )
        suggestions.append(
            "Hãy thử nới lỏng các tiêu chí kiêng cữ hoặc bỏ bớt các dị ứng thứ yếu không nguy hiểm."
        )

    # Điều kiện 2: Không đủ khả năng đáp ứng Calo mục tiêu
    # Giả sử mỗi ngày ăn tối đa 3-4 phần, nếu món giàu calo nhất x3 vẫn hụt > 15% so với target_calories
    if cal_col is not None and target_calories > 0:
        max_cal = float(filtered_foods_df[cal_col].max())
        cal_threshold = target_calories * 0.85
        if max_cal * 3 < cal_threshold:
            reasons.append(
                f"Các món ăn còn lại có năng lượng quá thấp (món cao nhất chỉ đạt {max_cal:.0f} kcal). "
                f"Ngay cả khi ăn 3 phần tối đa vẫn chỉ đạt {max_cal * 3:.0f} kcal, "
                f"không thể tiệm cận ngưỡng calo mục tiêu {target_calories:.0f} kcal/ngày (thiếu hụt trên 15%)."
            )
            suggestions.append(
                "Bạn nên bổ sung thêm các món có chứa tinh bột phức, chất béo lành mạnh hoặc giảm mức calo mục tiêu."
            )

    # Điều kiện 3: Không đủ khả năng đáp ứng Ngân sách tối thiểu
    # Nếu chọn 3 món rẻ nhất vẫn vượt ngân sách ngày
    if price_col is not None and daily_budget_vnd > 0:
        min_price = float(filtered_foods_df[price_col].min())
        if min_price * 3 > daily_budget_vnd:
            reasons.append(
                f"Chi phí các món ăn vượt mức chi trả (món rẻ nhất có giá {min_price:,.0f} VNĐ). "
                f"Tổng 3 bữa ăn tối thiểu cần {min_price * 3:,.0f} VNĐ, vượt quá ngân sách {daily_budget_vnd:,.0f} VNĐ/ngày của bạn."
            )
            suggestions.append(
                f"Vui lòng tăng ngân sách ăn uống tối thiểu lên ít nhất {min_price * 3:,.0f} VNĐ/ngày "
                "hoặc lựa chọn các thực phẩm bình dân tự nấu tại nhà."
            )

    if reasons:
        return {
            "status": "INSUFFICIENT_DATA",
            "allow_ai_generation": False,
            "available_count": available_count,
            "reasons": reasons,
            "suggestion": " ".join(suggestions) if suggestions else "Vui lòng điều chỉnh lại bộ lọc dinh dưỡng.",
        }

    return {
        "status": "PASS",
        "allow_ai_generation": True,
        "available_count": available_count,
        "reasons": [
            f"Dữ liệu món ăn đầy đủ ({available_count} món khả dụng), đáp ứng tốt calo mục tiêu và ngân sách."
        ],
        "suggestion": "Dữ liệu hợp lệ, sẵn sàng để mô hình AI xây dựng thực đơn tối ưu.",
    }


def check_exercise_data_sufficiency(
    filtered_exercises_df: pd.DataFrame, free_minutes_per_week: int
) -> Dict[str, Any]:
    """Kiểm tra tính đầy đủ và khả thi của DataFrame bài tập sau bước lọc Pandas (Post-filter).

    Đảm bảo có đủ bài tập luân phiên các nhóm cơ và đủ thời lượng tập tối thiểu
    trước khi chuyển cho thuật toán xếp lịch.

    Args:
        filtered_exercises_df: DataFrame bài tập sau khi lọc theo cấp độ thể chất (light/medium/heavy).
        free_minutes_per_week: Tổng số phút rảnh trong tuần người dùng đã đăng ký.

    Returns:
        dict gồm:
            - status: "PASS" hoặc "INSUFFICIENT_DATA"
            - allow_ai_generation: bool (True chỉ khi status == "PASS")
            - available_count: int (số lượng bài tập khả dụng)
            - reasons: List[str] (danh sách lý do cụ thể bằng tiếng Việt)
            - suggestion: str (hướng dẫn cụ thể cho người dùng khắc phục)
    """
    reasons: List[str] = []
    suggestions: List[str] = []

    available_count = (
        0 if filtered_exercises_df is None or filtered_exercises_df.empty else len(filtered_exercises_df)
    )

    # Điều kiện 1: Thiếu đa dạng bài tập (yêu cầu >= 2 bài để tránh quá tải nhóm cơ)
    if available_count < 2:
        reasons.append(
            f"Sau khi lọc theo cấp độ thể chất, chỉ còn {available_count} bài tập hợp lệ trong cơ sở dữ liệu "
            "(yêu cầu tối thiểu 2 bài tập để luân phiên nhóm cơ và phục hồi thể lực an toàn)."
        )
        suggestions.append(
            "Cần bổ sung thêm bài tập phục hồi hoặc mở rộng phạm vi cấp độ thể chất phù hợp."
        )

    # Điều kiện 2: Không đủ quỹ thời gian rảnh (yêu cầu >= 30 phút/tuần)
    if free_minutes_per_week < 30:
        reasons.append(
            f"Tổng quỹ thời gian rảnh là {free_minutes_per_week} phút/tuần, không đạt thời lượng tối thiểu 30 phút/tuần "
            "theo thiết kế chuẩn của thuật toán phân bổ lịch tập FitBreak."
        )
        suggestions.append(
            "Vui lòng đăng ký thêm ít nhất một khung giờ 30 phút rảnh trong tuần để bắt đầu lộ trình vận động."
        )

    if reasons:
        return {
            "status": "INSUFFICIENT_DATA",
            "allow_ai_generation": False,
            "available_count": available_count,
            "reasons": reasons,
            "suggestion": " ".join(suggestions),
        }

    return {
        "status": "PASS",
        "allow_ai_generation": True,
        "available_count": available_count,
        "reasons": [
            f"Dữ liệu bài tập đầy đủ ({available_count} bài tập khả dụng), quỹ thời gian ({free_minutes_per_week} phút/tuần) đủ điều kiện xếp lịch."
        ],
        "suggestion": "Dữ liệu hợp lệ, sẵn sàng để xếp lịch vận động tuần.",
    }


def check_filtered_data_sufficiency(
    filtered_foods_count: int, filtered_exercises_count: int
) -> GuardrailResult:
    """Hàm kiểm duyệt hậu xử lý (Post-retrieval Guardrail) sau khi lọc DataFrame bằng Pandas.

    Nếu số lượng món ăn hoặc bài tập còn lại quá ít do bộ lọc dị ứng/ngân sách quá khắt khe,
    hệ thống sẽ từ chối gọi LLM để tránh sinh ảo giác (hallucination).
    """
    reasons: List[str] = []

    if filtered_foods_count < 3:
        reasons.append(
            f"Sau khi lọc theo chế độ ăn và dị ứng, chỉ còn {filtered_foods_count} món ăn hợp lệ (yêu cầu tối thiểu 3 món cho 3 bữa). "
            "Cơ sở dữ liệu chưa có đủ thực phẩm an toàn đã xác minh cho tổ hợp dị ứng/chế độ ăn này."
        )

    if filtered_exercises_count < 2:
        reasons.append(
            f"Sau khi lọc theo cấp độ thể chất, chỉ còn {filtered_exercises_count} bài tập hợp lệ (yêu cầu tối thiểu 2 bài). "
            "Hệ thống không đủ căn cứ để xây dựng chu kỳ tập luyện cân bằng đa nhóm cơ."
        )

    if reasons:
        return GuardrailResult(
            status="INSUFFICIENT_DATA",
            bmi=0.0,
            bmi_category="Chưa xác định",
            reasons=reasons,
            disclaimer=DEFAULT_DISCLAIMER,
            allow_ai_generation=False,
        )

    return GuardrailResult(
        status="PASS",
        bmi=0.0,
        bmi_category="Hợp lệ",
        reasons=["Cơ sở dữ liệu đã lọc đủ số lượng thực phẩm và bài tập đã xác minh."],
        disclaimer=DEFAULT_DISCLAIMER,
        allow_ai_generation=True,
    )


# ==============================================================================
# KHỐI TEST CASE KIỂM THỬ TRỰC TIẾP
# ==============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("FITBREAK AI SAFETY & CLINICAL GUARDRAIL BENCHMARK")
    print("=" * 80)

    # 1. Test Case 1: PASS - Người dùng học sinh bình thường, các chỉ số chuẩn mực
    test_case_pass = UserHealthInput(
        height_cm=170.0,
        weight_kg=62.0,
        age=19,
        goal="tang_co",
        target_calories=2200,
        budget_vnd=80000,
        allergies=["seafood"],
        medical_conditions=[],
        user_notes="Em là sinh viên năm nhất, muốn tập thêm thể lực sau giờ học.",
        free_minutes_per_week=180,
    )

    # 2. Test Case 2: MEDICAL_WARNING do BMI bất thường & có bệnh lý nền trong notes
    test_case_medical_warning_bmi_disease = UserHealthInput(
        height_cm=160.0,
        weight_kg=95.0,  # BMI = 37.11 (Béo phì độ III)
        age=20,
        goal="giam_can",
        target_calories=1500,
        budget_vnd=120000,
        allergies=[],
        medical_conditions=["huyết áp cao"],
        user_notes="Bác sĩ bảo em có dấu hiệu tiểu đường type 2 và hay khó thở khi leo cầu thang.",
        free_minutes_per_week=120,
    )

    # 3. Test Case 3: MEDICAL_WARNING do Calo bất thường (< 1000 kcal) & mâu thuẫn mục tiêu
    test_case_medical_warning_calories = UserHealthInput(
        height_cm=165.0,
        weight_kg=45.0,  # BMI = 16.53 (Thiếu cân gầy độ II)
        age=16,
        goal="giam_can",  # Mâu thuẫn: đang thiếu cân lại đòi giảm cân
        target_calories=800,  # Nguy cơ suy nhược (< 1000 kcal)
        budget_vnd=50000,
        allergies=[],
        medical_conditions=[],
        user_notes="Em muốn ép cân cấp tốc trước kỳ thi.",
        free_minutes_per_week=90,
    )

    # 4. Test Case 4: INSUFFICIENT_DATA do ngân sách quá thấp (< 25.000 VNĐ) & thời gian rảnh không đủ
    test_case_insufficient_data = UserHealthInput(
        height_cm=168.0,
        weight_kg=58.0,
        age=18,
        goal="duy_tri",
        target_calories=1800,
        budget_vnd=15000,  # Quá thấp cho 3 bữa ăn đầy đủ
        allergies=[],
        medical_conditions=[],
        user_notes="",
        free_minutes_per_week=15,  # Không đủ 30 phút/tuần
    )

    test_cases = [
        ("TEST CASE 1: PASS (An toàn)", test_case_pass),
        ("TEST CASE 2: MEDICAL_WARNING (BMI nguy cơ cao & bệnh lý nền)", test_case_medical_warning_bmi_disease),
        ("TEST CASE 3: MEDICAL_WARNING (Calo < 1000 kcal & mâu thuẫn giảm cân)", test_case_medical_warning_calories),
        ("TEST CASE 4: INSUFFICIENT_DATA (Ngân sách < 25k & thời gian < 30p)", test_case_insufficient_data),
    ]

    for title, case_input in test_cases:
        print(f"\n--- {title} ---")
        result = safety_guardrail(case_input)
        print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))

    # 5. Test Case phụ cho check_filtered_data_sufficiency (Post-retrieval)
    print("\n--- TEST CASE 5: check_filtered_data_sufficiency (Món ăn còn < 3) ---")
    post_retrieval_result = check_filtered_data_sufficiency(
        filtered_foods_count=1, filtered_exercises_count=5
    )
    print(json.dumps(post_retrieval_result.model_dump(), indent=2, ensure_ascii=False))

    # 6. Test Case cho check_meal_data_sufficiency (Pandas Post-filter)
    print("\n" + "=" * 80)
    print("TEST CASES CHO check_meal_data_sufficiency & check_exercise_data_sufficiency")
    print("=" * 80)

    # Ca 1: DataFrame chỉ còn 2 món -> INSUFFICIENT_DATA
    df_two_foods = pd.DataFrame([
        {"id": 1, "ten_mon": "Phở bò", "calories": 450, "price_vnd": 40000, "meal_type": "breakfast"},
        {"id": 2, "ten_mon": "Cơm gà xối mỡ", "calories": 650, "price_vnd": 45000, "meal_type": "lunch"},
    ])
    res_meal_insufficient = check_meal_data_sufficiency(
        filtered_foods_df=df_two_foods,
        target_calories=2000,
        daily_budget_vnd=100000,
    )
    print("\n--- TEST CASE MEAL 1: Chỉ còn 2 món (Kỳ vọng: INSUFFICIENT_DATA) ---")
    print(json.dumps(res_meal_insufficient, indent=2, ensure_ascii=False))

    # 7. Test Case chuyên biệt cho check_filtered_meals_sufficiency
    print("\n" + "=" * 80)
    print("TEST CASES CHUYÊN BIỆT CHO check_filtered_meals_sufficiency (3 KỊCH BẢN)")
    print("=" * 80)

    # Kịch bản 1: Còn 2 món -> INSUFFICIENT_DATA (Thiếu số lượng tối thiểu cho 3 bữa)
    df_scenario_1 = pd.DataFrame([
        {"id": 1, "ten_mon": "Phở bò", "calories": 450, "price_vnd": 40000},
        {"id": 2, "ten_mon": "Bánh mì ốp la", "calories": 350, "price_vnd": 25000},
    ])
    res_sc1 = check_filtered_meals_sufficiency(
        filtered_df=df_scenario_1,
        target_calories=2000,
        daily_budget_vnd=100000,
        min_required_items=3,
    )
    print("\n--- KỊCH BẢN 1: Còn 2 món (< 3 món) ---")
    print(json.dumps(res_sc1.model_dump(), indent=2, ensure_ascii=False))

    # Kịch bản 2: Còn 5 món nhưng tổng 3 món rẻ nhất vượt ngân sách ngày -> INSUFFICIENT_DATA
    df_scenario_2 = pd.DataFrame([
        {"id": 1, "ten_mon": "Bò bít tết hảo hạng", "calories": 700, "price_vnd": 75000},
        {"id": 2, "ten_mon": "Cá hồi áp chảo sốt bơ", "calories": 650, "price_vnd": 85000},
        {"id": 3, "ten_mon": "Sườn cừu nướng thảo mộc", "calories": 800, "price_vnd": 95000},
        {"id": 4, "ten_mon": "Gà nướng phô mai cao cấp", "calories": 750, "price_vnd": 70000},
        {"id": 5, "ten_mon": "Tôm hùm sốt bơ tỏi", "calories": 600, "price_vnd": 110000},
    ])
    # 3 món rẻ nhất: 70k + 75k + 85k = 230k > ngân sách 150k
    res_sc2 = check_filtered_meals_sufficiency(
        filtered_df=df_scenario_2,
        target_calories=2000,
        daily_budget_vnd=150000,
        min_required_items=3,
    )
    print("\n--- KỊCH BẢN 2: Còn 5 món nhưng tổng giá 3 món rẻ nhất vượt ngân sách ---")
    print(json.dumps(res_sc2.model_dump(), indent=2, ensure_ascii=False))

    # Kịch bản 3: Còn 5 món thỏa mãn đầy đủ số lượng, calo và ngân sách -> PASS
    df_scenario_3 = pd.DataFrame([
        {"id": 1, "ten_mon": "Phở bò chín", "calories": 480, "price_vnd": 40000},
        {"id": 2, "ten_mon": "Cơm sườn bì chả", "calories": 680, "price_vnd": 45000},
        {"id": 3, "ten_mon": "Ức gà xào nấm", "calories": 520, "price_vnd": 35000},
        {"id": 4, "ten_mon": "Cá thu kho tộ", "calories": 490, "price_vnd": 35000},
        {"id": 5, "ten_mon": "Bún chả thịt nướng", "calories": 580, "price_vnd": 40000},
    ])
    # 3 món rẻ nhất: 35k + 35k + 40k = 110k <= ngân sách 130k
    # 3 món calo cao nhất: 680 + 580 + 520 = 1780 kcal >= 2000 * 0.8 = 1600 kcal
    res_sc3 = check_filtered_meals_sufficiency(
        filtered_df=df_scenario_3,
        target_calories=2000,
        daily_budget_vnd=130000,
        min_required_items=3,
    )
    print("\n--- KỊCH BẢN 3: Còn 5 món thỏa mãn đầy đủ (PASS) ---")
    print(json.dumps(res_sc3.model_dump(), indent=2, ensure_ascii=False))


