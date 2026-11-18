import re

from pydantic import BaseModel, EmailStr, Field, field_validator

class signUp(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=256)

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        checks = (
            (r"[A-Z]", "chữ hoa"),
            (r"[a-z]", "chữ thường"),
            (r"\d", "chữ số"),
            (r"[^A-Za-z0-9]", "ký tự đặc biệt"),
        )
        missing = [label for pattern, label in checks if not re.search(pattern, value)]
        if missing:
            raise ValueError("Mật khẩu phải có " + ", ".join(missing) + ".")
        return value
