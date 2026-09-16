"""Integration tests for CustomerSupportPipeline and FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app, load_pipeline
from src.pipeline import CustomerSupportPipeline
from src.schemas.models import ConversationTurn, SupportRequest


@pytest.fixture(scope="module")
def client():
    load_pipeline()
    with TestClient(app) as c:
        yield c


def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "apple_support_ai_agent"


def test_api_respond_billing_escalate(client):
    payload = {
        "customer_message": "I was charged twice on my credit card for my monthly iCloud storage subscription.",
    }
    response = client.post("/v1/support/respond", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "billing_subscriptions"
    assert data["decision"] == "ESCALATE"
    assert "response" in data
    assert "evidence" in data
    assert len(data["evidence"]) > 0


def test_api_respond_with_conversation_context(client):
    payload = {
        "customer_message": "Yes, I tried that restart already and it still drains fast.",
        "conversation_context": [
            {"role": "customer", "text": "My phone battery drains very quickly."},
            {"role": "brand", "text": "Have you tried restarting your device?"},
        ],
    }
    response = client.post("/v1/support/respond", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "intent" in data
    assert data["decision"] in ["AUTO_HANDLE", "ESCALATE"]


def test_api_validation_error_on_empty_message(client):
    payload = {"customer_message": ""}
    response = client.post("/v1/support/respond", json=payload)
    assert response.status_code == 422


def test_pipeline_edge_case_emoji_only():
    pipeline = CustomerSupportPipeline()
    req = SupportRequest(customer_message="😡📱💥😭")
    res = pipeline.process(req)
    assert res.decision in ["AUTO_HANDLE", "ESCALATE"]
    assert len(res.response) > 0


def test_pipeline_edge_case_very_long_message():
    pipeline = CustomerSupportPipeline()
    long_msg = "My phone is broken " * 200
    req = SupportRequest(customer_message=long_msg)
    res = pipeline.process(req)
    assert res.decision in ["AUTO_HANDLE", "ESCALATE"]
    assert len(res.response) > 0
