"""Master end-to-end customer support pipeline.

Combines Intent Classification, Vector Retrieval, Policy Escalation Decision,
and Grounded Response Generation into an orchestrated single call.
"""

import logging
from typing import List, Optional

from src.decision.policy import EscalationPolicyEngine
from src.generation.generator import GroundedResponseGenerator
from src.llm.factory import get_llm_provider
from src.models.semantic_classifier import SemanticIntentClassifier
from src.retrieval.vector_store import LocalVectorStore
from src.schemas.models import ConversationTurn, SupportRequest, SupportResponse

logger = logging.getLogger(__name__)


class CustomerSupportPipeline:
    """Production pipeline for AppleSupport customer support interactions."""

    def __init__(
        self,
        classifier_path: str = "data/processed/main_intent_classifier.pkl",
        retrieval_index_path: str = "data/processed/retrieval_index.pkl",
        thresholds_path: str = "configs/thresholds.yaml",
        llm_provider_name: Optional[str] = None,
    ):
        logger.info("Initializing CustomerSupportPipeline...")
        # 1. Intent Classifier
        self.classifier = SemanticIntentClassifier()
        self.classifier.load(classifier_path)

        # 2. Retrieval Engine
        self.vector_store = LocalVectorStore()
        self.vector_store.load(retrieval_index_path)

        # 3. Decision Engine
        self.policy_engine = EscalationPolicyEngine(thresholds_path=thresholds_path)

        # 4. Response Generator
        llm = get_llm_provider(provider_name=llm_provider_name)
        self.generator = GroundedResponseGenerator(llm_provider=llm)
        logger.info("CustomerSupportPipeline initialized successfully.")

    def process(self, request: SupportRequest) -> SupportResponse:
        """Processes an incoming customer request end-to-end."""
        customer_text = request.customer_message.strip()

        # Format conversational context if provided
        context_str = ""
        if request.conversation_context:
            context_str = " ".join(t.text for t in request.conversation_context)

        classification_input = f"{context_str} {customer_text}".strip()

        # Step 1: Intent Classification
        pred = self.classifier.predict(classification_input)
        predicted_intent = pred.intent
        intent_conf = pred.confidence

        # Step 2: Evidence Retrieval
        evidence = self.vector_store.search(
            query=customer_text,
            top_k=3,
            min_similarity=0.0,
        )

        # Step 3: Escalation Decision Layer
        decision, reason, composite_conf = self.policy_engine.evaluate(
            customer_message=customer_text,
            predicted_intent=predicted_intent,
            intent_confidence=intent_conf,
            evidence=evidence,
        )

        # Step 4: Grounded Response Generation
        response = self.generator.generate_response(
            customer_message=customer_text,
            conversation_context=request.conversation_context,
            predicted_intent=predicted_intent,
            decision=decision,
            escalation_reason=reason,
            confidence=composite_conf,
            evidence=evidence,
        )

        return response
