from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatMessage(BaseModel):
    role: str  # 'user' | 'assistant'
    content: str

class ChatBotRequest(BaseModel):
    message: str = Field(..., max_length=1000)
    history: Optional[List[ChatMessage]] = []

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

class ChatBotResponse(BaseModel):
    reply: str
    remaining_questions_today: int
    proposal: Optional[ProfileUpdateProposal] = None

class ConfirmProposalRequest(BaseModel):
    food_recommendation: Optional[str] = None
    level_of_physical_activity: Optional[str] = None
