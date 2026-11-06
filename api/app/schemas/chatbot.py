from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatMessage(BaseModel):
    role: str  # 'user' | 'assistant'
    content: str

class ChatBotRequest(BaseModel):
    message: str = Field(..., max_length=1000)
    history: Optional[List[ChatMessage]] = []

class ProfileUpdateProposal(BaseModel):
    has_update: bool = False
    food_recommendation: Optional[str] = None
    level_of_physical_activity: Optional[str] = None  # 'light' | 'medium' | 'heavy'
    reason: Optional[str] = None
    conflict_detected: bool = False
    conflict_message: Optional[str] = None
    verification_question: Optional[str] = None

class ChatBotResponse(BaseModel):
    reply: str
    remaining_questions_today: int
    proposal: Optional[ProfileUpdateProposal] = None

class ConfirmProposalRequest(BaseModel):
    food_recommendation: Optional[str] = None
    level_of_physical_activity: Optional[str] = None
