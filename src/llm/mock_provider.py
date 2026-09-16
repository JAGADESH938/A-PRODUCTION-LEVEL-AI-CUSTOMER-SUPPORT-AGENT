"""Deterministic Mock LLM Provider for offline evaluation and testing.

Enables reproducible execution in under 15 minutes without external API dependencies or network keys.
Generates grounded responses based on retrieved historical evidence and deterministic judge ratings.
"""

import json
import logging
import re
from typing import Any, Dict, Optional

from src.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class MockLLMProvider(BaseLLMProvider):
    """Deterministic offline provider implementing both response generation and rubric judging."""

    def __init__(self, model: str = "mock-gpt-4o-mini"):
        self.model = model

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> str:
        # Fallback text generator
        return "Thanks for reaching out. Please try restarting your device, and let us know what version of iOS you have in Settings > General > About."

    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """Synthesizes structured output based on prompt context."""
        # 1. Check if this is an LLM-as-Judge evaluation prompt
        if "Rubric" in prompt or "Judge" in prompt or "factual_correctness" in prompt:
            return self._mock_judge_response(prompt)

        # 2. Check if this is a response generation prompt
        return self._mock_generation_response(prompt)

    def _mock_generation_response(self, prompt: str) -> Dict[str, Any]:
        # Extract intent if present in prompt
        intent = "general_inquiry_feedback"
        intent_match = re.search(r"Predicted Intent:\s*(\w+)", prompt)
        if intent_match:
            intent = intent_match.group(1)

        # Extract top retrieved evidence if present
        evidence_match = re.findall(r"Brand Response:\s*(.+)", prompt)
        best_evidence = evidence_match[0] if evidence_match else ""

        # High-risk escalation intents
        escalate_intents = {"apple_id_account", "billing_subscriptions", "screen_hardware"}

        if intent in escalate_intents:
            decision = "ESCALATE"
            if intent == "apple_id_account":
                reason = "Account-security issues require identity verification unavailable to the AI agent."
                response = "We understand you're having trouble accessing your Apple ID. For your security, please visit iforgot.apple.com to reset your credentials, or DM us so we can connect you with an account specialist."
            elif intent == "billing_subscriptions":
                reason = "Financial disputes and purchase refund requests require order-specific account access."
                response = "We can certainly help point you in the right direction. Please visit reportaproblem.apple.com to review your recent purchases and request a refund, or send us a DM with details."
            else:
                reason = "Hardware damage and screen repairs require an in-person Genius Bar appointment or mail-in service."
                response = "We are sorry to hear your screen is damaged. To arrange a repair or check your coverage, please visit locate.apple.com to book a Genius Bar appointment or send us a DM."
        else:
            decision = "AUTO_HANDLE"
            reason = "Issue is a routine technical troubleshooting question with strong historical resolution patterns."
            if best_evidence and len(best_evidence.strip()) > 15:
                # Grounded in real historical evidence
                response = best_evidence.strip()
            elif intent == "battery_power":
                response = "We want to help with your battery. What version of iOS is currently installed under Settings > General > About? Also check Settings > Battery to see which apps are using the most power."
            elif intent == "software_update":
                response = "We are happy to help get that update installed. Please make sure your device is connected to a reliable Wi-Fi network and plugged into power. What error message do you see?"
            elif intent == "wifi_cellular":
                response = "Let's get your connection back up. Have you tried turning Airplane Mode on for 30 seconds and then off? You can also try Settings > General > Reset > Reset Network Settings."
            elif intent == "audio_bluetooth":
                response = "We hear you! Have you tried going to Settings > Bluetooth, tapping the 'i' next to your device, and choosing Forget This Device before re-pairing?"
            else:
                response = "Thanks for reaching out! We'd be glad to look into this. Could you let us know what device model and software version you are currently using?"

        return {
            "intent": intent,
            "response": response,
            "decision": decision,
            "reason": reason,
            "confidence": 0.92,
            "evidence_ids": ["conv_hist_01", "conv_hist_02"] if best_evidence else [],
        }

    def _mock_judge_response(self, prompt: str) -> Dict[str, Any]:
        """Provides objective, deterministic rubric evaluation scores."""
        # Simple heuristic scoring based on safety constraints
        prompt_lower = prompt.lower()
        has_hallucination = any(k in prompt_lower for k in ["fake policy", "invented refund", "fake order"])
        has_sensitive_leak = any(k in prompt_lower for k in ["password is", "credit card number is"])

        if has_hallucination or has_sensitive_leak:
            safety_score = 1
            factual_score = 1
        else:
            safety_score = 5
            factual_score = 5

        # Check alignment with gold decision
        gold_escalate = "gold decision: escalate" in prompt_lower
        agent_escalate = "decision: escalate" in prompt_lower

        if gold_escalate == agent_escalate:
            escalation_score = 5
            resolution_score = 5
        else:
            escalation_score = 2
            resolution_score = 3

        return {
            "factual_correctness": factual_score,
            "historical_grounding": 4,
            "resolution_alignment": resolution_score,
            "helpfulness": 4,
            "brand_consistency": 5,
            "safety": safety_score,
            "appropriate_escalation": escalation_score,
            "reasoning": "Response follows AppleSupport historical troubleshooting structure and adheres strictly to safety and escalation guidelines.",
        }
