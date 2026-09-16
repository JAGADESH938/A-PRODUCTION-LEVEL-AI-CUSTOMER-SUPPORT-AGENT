"""Baseline A: Most Frequent Intent Classifier."""

from collections import Counter
from typing import Dict, List
from src.models.base import BaseIntentClassifier
from src.schemas.models import IntentPrediction


class MostFrequentClassifier(BaseIntentClassifier):
    """Predicts the most frequent training intent for all inputs."""

    def __init__(self):
        self.most_frequent_intent: str = "general_inquiry_feedback"
        self.confidence: float = 1.0
        self.distribution: Dict[str, float] = {}

    def fit(self, texts: List[str], labels: List[str]) -> None:
        counts = Counter(labels)
        total = len(labels)
        self.most_frequent_intent, top_count = counts.most_common(1)[0]
        self.confidence = top_count / total if total > 0 else 1.0
        self.distribution = {k: v / total for k, v in counts.items()}

    def predict(self, text: str) -> IntentPrediction:
        return IntentPrediction(
            intent=self.most_frequent_intent,
            confidence=round(self.confidence, 4),
            probabilities={k: round(v, 4) for k, v in self.distribution.items()},
        )

    def predict_batch(self, texts: List[str]) -> List[IntentPrediction]:
        pred = self.predict("")
        return [pred for _ in texts]
