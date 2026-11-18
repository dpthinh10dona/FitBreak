from pydantic import BaseModel, Field

class defeatBoss(BaseModel):
    boss_id: int = Field(..., ge=1)
    team: int = Field(..., ge=1)
