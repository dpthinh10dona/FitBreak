from pydantic import BaseModel, Field

class updateBossHealth(BaseModel):
    team: int = Field(..., ge=1)
    damage: int = Field(..., ge=0, le=1000)
