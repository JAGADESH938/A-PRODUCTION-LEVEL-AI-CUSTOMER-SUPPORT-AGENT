"""Abstract base class for intent classifiers."""

from abc import ABC, abstractmethod
from typing import List
from src.schemas.models import IntentPrediction


class BaseIntentClassifier(ABC):
    """Abstract interface for all intent classification models."""

    @abstractmethod
    def fit(self, texts: List[str], labels: List[str]) -> None:
        """Trains or fits the classifier."""
        pass

    @abstractmethod
    def predict(self, text: str) -> IntentPrediction:
        """Predicts the intent and confidence for a single input text."""
        pass

    @abstractmethod
    def predict_batch(self, texts: List[str]) -> List[IntentPrediction]:
        """Predicts intents for a batch of input texts."""
        pass
