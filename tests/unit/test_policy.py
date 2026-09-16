"""Unit tests for the escalation policy engine."""

import pytest
from src.decision.policy import EscalationPolicyEngine
from src.schemas.models import EvidenceItem


@pytest.fixture
def policy_engine():
    return EscalationPolicyEngine(thresholds_path="configs/thresholds.yaml")


def test_mandatory_intent_escalation(policy_engine):
    evidence = [EvidenceItem(conversation_id="c1", customer_issue="bill", brand_response="resp", similarity=0.85, intent="billing_subscriptions")]
    decision, reason, conf = policy_engine.evaluate(
        customer_message="I was charged twice on my card",
        predicted_intent="billing_subscriptions",
        intent_confidence=0.95,
        evidence=evidence,
    )
    assert decision == "ESCALATE"
    assert "Financial disputes" in reason


def test_low_retrieval_similarity_escalation(policy_engine):
    evidence = [EvidenceItem(conversation_id="c1", customer_issue="battery", brand_response="resp", similarity=0.20, intent="battery_power")]
    decision, reason, conf = policy_engine.evaluate(
        customer_message="My battery drains fast",
        predicted_intent="battery_power",
        intent_confidence=0.95,
        evidence=evidence,
    )
    assert decision == "ESCALATE"
    assert "No sufficiently similar historical resolution" in reason


def test_sensitive_keyword_escalation(policy_engine):
    evidence = [EvidenceItem(conversation_id="c1", customer_issue="stolen", brand_response="resp", similarity=0.90, intent="apple_id_account")]
    decision, reason, conf = policy_engine.evaluate(
        customer_message="My phone was stolen at gunpoint, need police report help",
        predicted_intent="apple_id_account",
        intent_confidence=0.95,
        evidence=evidence,
    )
    assert decision == "ESCALATE"
    assert "police" in reason.lower() or "stolen" in reason.lower() or "account-security" in reason.lower()


def test_safe_autohandle(policy_engine):
    evidence = [EvidenceItem(conversation_id="c1", customer_issue="watch compatible", brand_response="Yes it is", similarity=0.75, intent="general_inquiry_feedback")]
    decision, reason, conf = policy_engine.evaluate(
        customer_message="Does the Apple Watch Series 3 work with iPhone 6?",
        predicted_intent="general_inquiry_feedback",
        intent_confidence=0.90,
        evidence=evidence,
    )
    assert decision == "AUTO_HANDLE"
    assert "Routine technical support query" in reason
