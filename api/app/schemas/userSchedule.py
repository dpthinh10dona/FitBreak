from typing import Any

from pydantic import BaseModel, Field


class UserScheduleUpsert(BaseModel):
    selected_time_slots: list[str] = Field(default_factory=list)
    workout_schedule: dict[str, Any] = Field(default_factory=dict)

