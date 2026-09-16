"""Unit tests for intent classification models."""

import pytest
from src.models.most_frequent import MostFrequentClassifier
from src.models.semantic_classifier import SemanticIntentClassifier
from src.models.tfidf_logistic import TfidfLogisticClassifier


def test_most_frequent_classifier():
    texts = ["battery drain", "screen cracked", "battery dying", "battery dead"]
    labels = ["battery_power", "screen_hardware", "battery_power", "battery_power"]

    clf = MostFrequentClassifier()
    clf.fit(texts, labels)

    pred = clf.predict("some random text")
    assert pred.intent == "battery_power"
    assert pred.confidence == 0.75


def test_tfidf_logistic_classifier():
    texts = [
        "my battery is draining fast",
        "battery dead",
        "screen is cracked and broken",
        "shattered display glass",
    ]
    labels = [
        "battery_power",
        "battery_power",
        "screen_hardware",
        "screen_hardware",
    ]

    clf = TfidfLogisticClassifier()
    clf.fit(texts, labels)

    pred = clf.predict("battery is completely drained")
    assert pred.intent == "battery_power"
    assert pred.confidence > 0.4


def test_semantic_classifier_loaded():
    clf = SemanticIntentClassifier()
    clf.load("data/processed/main_intent_classifier.pkl")

    pred = clf.predict("My iPhone battery drops from 100% to 20% in an hour")
    assert pred.intent == "battery_power"
    assert pred.confidence > 0.5
    assert len(pred.probabilities) == 9
