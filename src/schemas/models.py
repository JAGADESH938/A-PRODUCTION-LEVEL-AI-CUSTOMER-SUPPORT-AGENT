"""Pydantic schemas for intent, retrieval, decision, and API contracts."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    role: Literal["customer", "brand", "agent"]
    text: str


class SupportRequest(BaseModel):
    customer_message: str = Field(..., min_length=1, description="Latest customer message")
    conversation_context: Optional[List[ConversationTurn]] = Field(
        default=None, description="Preceding conversational turns"
    )


class EvidenceItem(BaseModel):
    conversation_id: str
    customer_issue: str
    brand_response: str
    similarity: float
    intent: Optional[str] = None


class SupportResponse(BaseModel):
    intent: str
    response: str
    decision: Literal["AUTO_HANDLE", "ESCALATE"]
    reason: str
    confidence: float
    evidence: List[EvidenceItem] = Field(default_factory=list)


class IntentPrediction(BaseModel):
    intent: str
    confidence: float
    probabilities: Dict[str, float] = Field(default_factory=dict)


class LLMJudgeScore(BaseModel):
    factual_correctness: int = Field(..., ge=0, le=5)
    historical_grounding: int = Field(..., ge=0, le=5)
    resolution_alignment: int = Field(..., ge=0, le=5)
    helpfulness: int = Field(..., ge=0, le=5)
    brand_consistency: int = Field(..., ge=0, le=5)
    safety: int = Field(..., ge=0, le=5)
    appropriate_escalation: int = Field(..., ge=0, le=5)
    reasoning: str
