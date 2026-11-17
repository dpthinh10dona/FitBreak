from pydantic import BaseModel, Field
from typing import Optional, List

class FoodSuggestRequest(BaseModel):
    calories_need: int = Field(..., description="Mục tiêu calo/ngày")
    protein_need: int = Field(..., description="Mục tiêu protein (g)")
    daily_budget: int = Field(..., description="Ngân sách VNĐ/ngày")
    aim: str = Field(..., description="Mục tiêu: Tăng cơ / Giảm cân / Cân bằng")
    diet_type: str = Field(..., description="Chế độ ăn: vegetarian / eatclean / home_cooked")
    allergen: Optional[str] = Field("", description="Dị ứng, phân cách bằng ;")
    exclude_dishes: Optional[List[str]] = Field(default_factory=list, description="Danh sách món cũ cần loại bỏ để đổi món mới")
    food_recommendation: Optional[str] = Field(None, description="Lời khuyên dinh dưỡng y tế từ hồ sơ/khám sức khỏe")
    # Optional để giữ tương thích client cũ. Router kích hoạt guardrail khi có
    # đủ dữ liệu nhân trắc học.
    height_cm: Optional[float] = Field(None, gt=0)
    weight_kg: Optional[float] = Field(None, gt=0)
    age: Optional[int] = None
    free_minutes_per_week: Optional[int] = Field(None, ge=0)
    medical_conditions: List[str] = Field(default_factory=list)
    user_notes: str = ""
