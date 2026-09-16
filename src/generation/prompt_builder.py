"""Prompt template builder for grounded customer support response generation."""

from typing import List, Optional
from src.schemas.models import ConversationTurn, EvidenceItem


SYSTEM_PROMPT = """You are Apple Support's automated support assistant on Twitter.
Your role is to assist users with technical troubleshooting according to historical Apple Support patterns.

CRITICAL OPERATIONAL RULES:
1. Ground your response STRICTLY in the provided Historical Brand Evidence and Brand Response Patterns.
2. Maintain Apple Support's signature voice: concise, empathetic, polite, professional, and clear.
3. If the decision is ESCALATE, direct the customer clearly to the official self-service resource (e.g., iforgot.apple.com, reportaproblem.apple.com, locate.apple.com) or invite them to send a DM.
4. DO NOT hallucinate: never promise refunds, never state actions have been taken on customer accounts, never invent order numbers or ticket IDs.
5. DO NOT request sensitive secrets: never ask for passwords, PINs, full credit cards, or two-factor codes.
6. Return your response in STRICT JSON format adhering to the requested schema.
"""


def build_response_prompt(
    customer_message: str,
    conversation_context: Optional[List[ConversationTurn]],
    predicted_intent: str,
    decision: str,
    escalation_reason: str,
    evidence: List[EvidenceItem],
) -> str:
    """Builds the evidence-grounded prompt for the LLM."""
    context_str = "None (First turn)"
    if conversation_context:
        context_str = "\n".join(f"{t.role.capitalize()}: {t.text}" for t in conversation_context)

    evidence_str = "No historical evidence available."
    if evidence:
        evidence_items = []
        for i, ev in enumerate(evidence, start=1):
            evidence_items.append(
                f"Evidence {i} (Similarity: {ev.similarity:.2f}, Intent: {ev.intent}):\n"
                f"  Customer Issue: {ev.customer_issue}\n"
                f"  Brand Response: {ev.brand_response}"
            )
        evidence_str = "\n\n".join(evidence_items)

    prompt = f"""### Customer Support Case:
Customer Message:
"{customer_message}"

Conversation Context:
{context_str}

### System Classifications & Policy Decision:
Predicted Intent: {predicted_intent}
Policy Decision: {decision}
Decision Reason: {escalation_reason}

### Historical Brand Evidence:
{evidence_str}

### Required Output JSON Format:
{{
  "intent": "{predicted_intent}",
  "response": "<Your concise, evidence-grounded AppleSupport response here>",
  "decision": "{decision}",
  "reason": "{escalation_reason}",
  "confidence": 0.95,
  "evidence_ids": {[f'"{e.conversation_id}"' for e in evidence]}
}}
"""
    return prompt
