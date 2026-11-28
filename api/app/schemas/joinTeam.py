from pydantic import BaseModel, UUID4

class joinTeam(BaseModel):
    invite_code: UUID4
