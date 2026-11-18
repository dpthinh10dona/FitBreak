from pydantic import BaseModel, Field, model_validator

class updateProfile(BaseModel):
    name : str = Field(..., min_length=1, max_length=100)
    age : int = Field(..., ge=12, le=65)
    gender : bool
    height : int = Field(..., ge=100, le=230)
    weight : float = Field(..., ge=30, le=200)
    goal : str
    activity_frequency : int = Field(..., ge=1, le=3)

    @model_validator(mode="after")
    def validate_safe_bmi(self):
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
    
