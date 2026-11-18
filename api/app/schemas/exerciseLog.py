from pydantic import BaseModel, Field
from datetime import datetime

class exerciseLog(BaseModel):
    exercise_id: str = Field(..., min_length=1, max_length=128)
    completed_at: datetime
    reward_coins: int = Field(..., ge=0, le=10)
