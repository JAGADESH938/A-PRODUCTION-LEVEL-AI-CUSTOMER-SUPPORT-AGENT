"""Evidence-grounded response generator with schema validation, retry logic, and safety filters."""

import json
import logging
from typing import List, Optional

from src.generation.prompt_builder import SYSTEM_PROMPT, build_response_prompt
from src.llm.base import BaseLLMProvider
from src.safety.guardrails import SafetyGuardrails
from src.schemas.models import ConversationTurn, EvidenceItem, SupportResponse

logger = logging.getLogger(__name__)


class GroundedResponseGenerator:
    """Generates schema-validated customer support responses grounded in historical evidence."""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def generate_response(
        self,
        customer_message: str,
        conversation_context: Optional[List[ConversationTurn]],
        predicted_intent: str,
        decision: str,
        escalation_reason: str,
        confidence: float,
        evidence: List[EvidenceItem],
    ) -> SupportResponse:
        prompt = build_response_prompt(
            customer_message=customer_message,
            conversation_context=conversation_context,
            predicted_intent=predicted_intent,
            decision=decision,
            escalation_reason=escalation_reason,
            evidence=evidence,
        )

        response_dict = None
        for attempt in range(2):
            try:
                response_dict = self.llm.generate_structured(
                    prompt=prompt,
                    system_prompt=SYSTEM_PROMPT,
                    temperature=0.0,
                )
                if response_dict and "response" in response_dict:
                    break
            except Exception as e:
                logger.warning("LLM response generation failed on attempt %d: %s", attempt + 1, e)

        # Fallback if generation failed or returned invalid format
        if not response_dict or not response_dict.get("response"):
            logger.error("LLM generation failed twice. Safe fallback to escalation.")
            return SupportResponse(
                intent=predicted_intent,
                response="We apologize for the inconvenience. Please send us a direct message so a team member can assist you further.",
                decision="ESCALATE",
                reason="Generation failure or malformed LLM response; falling back to safe human escalation.",
                confidence=round(confidence, 4),
                evidence=evidence,
            )

        resp_text = str(response_dict.get("response", "")).strip()

        # Output safety check
        is_safe, violations = SafetyGuardrails.check_output_safety(resp_text)
        if not is_safe:
            logger.warning("Guardrail violation in generated response: %s", violations)
            resp_text = (
                "Thanks for reaching out. Please send us a DM with more details so our support team can take a closer look."
            )
            decision = "ESCALATE"
            escalation_reason = f"Safety guardrail triggered on generated output ({violations[0]})."

        return SupportResponse(
            intent=predicted_intent,
            response=resp_text,
            decision=decision,
            reason=escalation_reason,
            confidence=round(confidence, 4),
            evidence=evidence,
        )
