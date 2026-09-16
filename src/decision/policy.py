"""Independent Escalation Decision Engine.

Evaluates intent classification confidence, retrieval similarity, mandatory intent rules,
and sensitive keywords to make transparent, conservative AUTO_HANDLE vs ESCALATE decisions.
"""

from typing import Any, Dict, List, Literal, Optional, Tuple
import yaml

from src.safety.guardrails import SafetyGuardrails
from src.schemas.models import EvidenceItem


class EscalationPolicyEngine:
    """Deterministic and policy-driven escalation manager."""

    def __init__(self, thresholds_path: str = "configs/thresholds.yaml"):
        with open(thresholds_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.thresholds = self.config.get("thresholds", {})
        self.weights = self.config.get("weights", {})
        self.mandatory_escalate_intents = set(self.config.get("mandatory_escalate_intents", []))
        self.sensitive_keywords = self.config.get("sensitive_risk_keywords", [])

    def calculate_confidence(
        self,
        intent_confidence: float,
        evidence: List[EvidenceItem],
    ) -> Tuple[float, float]:
        """Computes retrieval similarity and blended composite confidence score."""
        top_sim = evidence[0].similarity if evidence else 0.0

        w_intent = self.weights.get("intent_confidence_weight", 0.60)
        w_sim = self.weights.get("retrieval_similarity_weight", 0.40)

        composite = (w_intent * intent_confidence) + (w_sim * top_sim)
        return round(top_sim, 4), round(composite, 4)

    def evaluate(
        self,
        customer_message: str,
        predicted_intent: str,
        intent_confidence: float,
        evidence: List[EvidenceItem],
    ) -> Tuple[Literal["AUTO_HANDLE", "ESCALATE"], str, float]:
        """Evaluates policy signals and returns (decision, reason, composite_confidence)."""
        top_similarity, composite_confidence = self.calculate_confidence(
            intent_confidence, evidence
        )

        # 1. Rule: Safety trigger in customer message
        is_safe, violations = SafetyGuardrails.check_input_safety(customer_message)
        if not is_safe:
            return (
                "ESCALATE",
                f"Safety or security risk detected in customer query ({violations[0]}).",
                composite_confidence,
            )

        # 2. Rule: Sensitive risk keywords
        lower_msg = customer_message.lower()
        for kw in self.sensitive_keywords:
            if kw in lower_msg:
                return (
                    "ESCALATE",
                    f"Sensitive keyword trigger '{kw}' requires human specialist intervention.",
                    composite_confidence,
                )

        # 3. Rule: Mandatory escalation intents (Account security, billing fraud, hardware repair)
        if predicted_intent in self.mandatory_escalate_intents:
            reasons = {
                "apple_id_account": "Account-security issues require identity verification unavailable to the AI agent.",
                "billing_subscriptions": "Financial disputes and purchase refund requests require order-specific account access.",
                "screen_hardware": "Hardware damage and screen repairs require an in-person Genius Bar appointment or mail-in service.",
            }
            return (
                "ESCALATE",
                reasons.get(predicted_intent, f"Policy mandates escalation for intent '{predicted_intent}'."),
                composite_confidence,
            )

        # 4. Rule: Insufficient historical evidence
        min_sim = self.thresholds.get("retrieval_similarity_min", 0.55)
        if not evidence or top_similarity < min_sim:
            return (
                "ESCALATE",
                f"No sufficiently similar historical resolution retrieved (similarity {top_similarity:.2f} < threshold {min_sim:.2f}).",
                composite_confidence,
            )

        # 5. Rule: Intent classification confidence too low
        min_intent_conf = self.thresholds.get("intent_confidence_min", 0.70)
        if intent_confidence < min_intent_conf:
            return (
                "ESCALATE",
                f"Intent classification confidence is low ({intent_confidence:.2f} < {min_intent_conf:.2f}).",
                composite_confidence,
            )

        # 6. Rule: Composite confidence threshold
        min_composite = self.thresholds.get("composite_confidence_min", 0.72)
        if composite_confidence < min_composite:
            return (
                "ESCALATE",
                f"Composite confidence score is insufficient ({composite_confidence:.2f} < {min_composite:.2f}).",
                composite_confidence,
            )

        # Passed all checks -> Safe to auto-handle
        return (
            "AUTO_HANDLE",
            "Routine technical support query with high classification confidence and grounded historical evidence.",
            composite_confidence,
        )
