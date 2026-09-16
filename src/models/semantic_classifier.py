"""Main System: High-Capacity Semantic Intent Classifier.

Uses a FeatureUnion of Word N-grams (1-3) and Character N-grams (3-5)
with calibrated probabilities, sublinear TF scaling, and balanced class weights.
Excels on noisy Twitter syntax, typos, slang, and abbreviations.
"""

import pickle
from pathlib import Path
from typing import List, Optional
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from src.models.base import BaseIntentClassifier
from src.schemas.models import IntentPrediction


class SemanticIntentClassifier(BaseIntentClassifier):
    """Calibrated high-capacity intent classifier resilient to social media noise."""

    def __init__(self, c_param: float = 1.0):
        self.c_param = c_param
        self.pipeline: Optional[Pipeline] = None
        self.classes: List[str] = []

    def fit(self, texts: List[str], labels: List[str]) -> None:
        # Word + Char-wb feature union
        features = FeatureUnion([
            ("word_tfidf", TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=12000,
                sublinear_tf=True,
                stop_words="english",
            )),
            ("char_tfidf", TfidfVectorizer(
                ngram_range=(3, 5),
                analyzer="char_wb",
                max_features=18000,
                sublinear_tf=True,
            )),
        ])

        base_svc = LinearSVC(
            C=self.c_param,
            class_weight="balanced",
            random_state=42,
            max_iter=3000,
        )

        calibrated_clf = CalibratedClassifierCV(
            estimator=base_svc,
            method="sigmoid",
            cv=3,
        )

        self.pipeline = Pipeline([
            ("features", features),
            ("clf", calibrated_clf),
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
