from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal, List

class ChatBotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(..., min_length=1, max_length=99)

class FieldUpdateDetail(BaseModel):
    previous_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: Optional[str] = None

class ProposedUpdates(BaseModel):
    food_recommendation: Optional[FieldUpdateDetail] = None
    level_of_physical_activity: Optional[FieldUpdateDetail] = None

class ProfileUpdateProposal(BaseModel):
    has_update: bool = False
    has_proposed_changes: Optional[bool] = False
    conflict_detected: bool = False
    conflict_explanation: Optional[str] = None
    conflict_message: Optional[str] = None
    summary_for_ui_card: Optional[str] = None
    food_recommendation: Optional[str] = None
    level_of_physical_activity: Optional[str] = None  # 'light' | 'medium' | 'heavy'
    reason: Optional[str] = None
    verification_question: Optional[str] = None
    proposed_updates: Optional[ProposedUpdates] = None
    requires_user_confirmation: bool = True

class RetrievedChunk(BaseModel):
    doc_title: str
    section_or_page: Optional[str] = None
    raw_text: str
    similarity_score: float = 0.0

class ChatBotResponse(BaseModel):
    reply: str
    remaining_questions_today: int
    proposal: Optional[ProfileUpdateProposal] = None
    retrieved_chunks: List[RetrievedChunk] = Field(default_factory=list)
    status: str = "PASS"
    reason_code: Optional[str] = None
    allow_ai_generation: bool = True

class ConfirmProposalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status_flag: Literal["restrict_heavy_exercise", "maintain_activity", "nutrition_review"]
