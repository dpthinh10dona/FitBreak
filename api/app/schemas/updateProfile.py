from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import date

class updateProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nickname : str = Field(..., min_length=1, max_length=32)
    birth_year : int = Field(..., ge=1900)
    gender : bool
    height : int = Field(..., ge=100, le=230)
    weight : float = Field(..., ge=30, le=200)
    goal : str
    activity_frequency : int = Field(..., ge=1, le=3)

    @model_validator(mode="after")
    def validate_safe_bmi(self):
        if not 12 <= date.today().year - self.birth_year <= 65:
            raise ValueError("Năm sinh phải tương ứng độ tuổi từ 12 đến 65.")
        bmi = self.weight / ((self.height / 100) ** 2)
        if bmi < 16:
            raise ValueError(
                f"BMI {bmi:.1f} quá thấp (dưới 16). Vui lòng kiểm tra lại chiều cao, "
                "cân nặng hoặc tham khảo nhân viên y tế."
            )
        if bmi >= 35:
            raise ValueError(
                f"BMI {bmi:.1f} quá cao (từ 35 trở lên). Vui lòng kiểm tra lại chiều cao, "
                "cân nặng hoặc tham khảo nhân viên y tế."
            )
        return self
    
