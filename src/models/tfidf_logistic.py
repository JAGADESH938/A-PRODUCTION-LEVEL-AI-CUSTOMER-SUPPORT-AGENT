"""Baseline B: TF-IDF + Logistic Regression Intent Classifier."""

import pickle
from pathlib import Path
from typing import List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.models.base import BaseIntentClassifier
from src.schemas.models import IntentPrediction


class TfidfLogisticClassifier(BaseIntentClassifier):
    """Standard TF-IDF Vectorizer + Multinomial Logistic Regression baseline."""

    def __init__(self, c_param: float = 1.0, max_features: int = 5000):
        self.c_param = c_param
        self.max_features = max_features
        self.pipeline: Optional[Pipeline] = None
        self.classes: List[str] = []

    def fit(self, texts: List[str], labels: List[str]) -> None:
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=self.max_features,
                stop_words="english",
                sublinear_tf=True,
            )),
            ("clf", LogisticRegression(
                C=self.c_param,
                max_iter=1000,
                class_weight=None,
                random_state=42,
            )),
        ])
        self.pipeline.fit(texts, labels)
        self.classes = list(self.pipeline.named_steps["clf"].classes_)

    def predict(self, text: str) -> IntentPrediction:
        if self.pipeline is None:
            raise ValueError("Model has not been fitted.")
        probs = self.pipeline.predict_proba([text])[0]
        max_idx = int(np.argmax(probs))
        pred_intent = self.classes[max_idx]
        confidence = float(probs[max_idx])

        prob_dict = {cls: round(float(p), 4) for cls, p in zip(self.classes, probs)}
        return IntentPrediction(
            intent=pred_intent,
            confidence=round(confidence, 4),
            probabilities=prob_dict,
        )

    def predict_batch(self, texts: List[str]) -> List[IntentPrediction]:
        if self.pipeline is None:
            raise ValueError("Model has not been fitted.")
        all_probs = self.pipeline.predict_proba(texts)
        results = []
        for probs in all_probs:
            max_idx = int(np.argmax(probs))
            results.append(IntentPrediction(
                intent=self.classes[max_idx],
                confidence=round(float(probs[max_idx]), 4),
                probabilities={cls: round(float(p), 4) for cls, p in zip(self.classes, probs)},
            ))
        return results

    def save(self, filepath: str) -> None:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump({"pipeline": self.pipeline, "classes": self.classes}, f)

    def load(self, filepath: str) -> None:
        with open(filepath, "rb") as f:
            data = pickle.load(f)
            self.pipeline = data["pipeline"]
            self.classes = data["classes"]
