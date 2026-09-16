"""Training and comparative evaluation script for intent classification models.

Compares:
- Baseline A: Most Frequent Intent
- Baseline B: Standard TF-IDF + Logistic Regression
- Main Model: Semantic FeatureUnion + Calibrated LinearSVC

Reports:
- Accuracy, Macro Precision, Macro Recall, Macro F1, Weighted F1, Per-intent F1
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score

from src.models.most_frequent import MostFrequentClassifier
from src.models.semantic_classifier import SemanticIntentClassifier
from src.models.tfidf_logistic import TfidfLogisticClassifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_split(filepath: str) -> List[Dict[str, Any]]:
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def prepare_inputs(records: List[Dict[str, Any]]) -> (List[str], List[str]):
    texts = []
    labels = []
    for r in records:
        text = r.get("customer_text", "")
        if r.get("conversation_context"):
            text = f"{r['conversation_context']} {text}"
        texts.append(text)
        labels.append(r["intent"])
    return texts, labels


def evaluate_model(y_true: List[str], y_pred: List[str], classes: List[str]) -> Dict[str, Any]:
    acc = np.mean([1 if yt == yp else 0 for yt, yp in zip(y_true, y_pred)])
    macro_p = precision_score(y_true, y_pred, average="macro", zero_division=0)
    macro_r = recall_score(y_true, y_pred, average="macro", zero_division=0)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)

    clf_report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    conf_matrix = confusion_matrix(y_true, y_pred, labels=classes).tolist()

    return {
        "accuracy": round(float(acc), 4),
        "macro_precision": round(float(macro_p), 4),
        "macro_recall": round(float(macro_r), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "classification_report": clf_report,
        "confusion_matrix": conf_matrix,
        "classes": classes,
    }


def run_training_pipeline(
    data_dir: str = "data/processed",
    output_report_path: str = "reports/intent_classification_benchmark.json",
) -> Dict[str, Any]:
    train_records = load_split(f"{data_dir}/train.jsonl")
    val_records = load_split(f"{data_dir}/val.jsonl")
    test_records = load_split(f"{data_dir}/test.jsonl")

    X_train, y_train = prepare_inputs(train_records)
    X_val, y_val = prepare_inputs(val_records)
    X_test, y_test = prepare_inputs(test_records)

    classes = sorted(list(set(y_train)))
    logger.info("Training on %d records, validating on %d, testing on %d across %d classes.",
                len(X_train), len(X_val), len(X_test), len(classes))

    # 1. Baseline A: Most Frequent
    logger.info("Training Baseline A (Most Frequent)...")
    baseline_a = MostFrequentClassifier()
    baseline_a.fit(X_train, y_train)
    preds_a = [p.intent for p in baseline_a.predict_batch(X_test)]
    metrics_a = evaluate_model(y_test, preds_a, classes)
    logger.info("Baseline A: Accuracy=%.4f, Macro-F1=%.4f", metrics_a["accuracy"], metrics_a["macro_f1"])

    # 2. Baseline B: TF-IDF + Logistic Regression
    logger.info("Training Baseline B (TF-IDF + Logistic Regression)...")
    baseline_b = TfidfLogisticClassifier(c_param=1.0)
    baseline_b.fit(X_train, y_train)
    preds_b = [p.intent for p in baseline_b.predict_batch(X_test)]
    metrics_b = evaluate_model(y_test, preds_b, classes)
    baseline_b.save(f"{data_dir}/baseline_b_classifier.pkl")
    logger.info("Baseline B: Accuracy=%.4f, Macro-F1=%.4f", metrics_b["accuracy"], metrics_b["macro_f1"])

    # 3. Main Model: Calibrated Semantic Classifier
    logger.info("Training Main Model (Calibrated Semantic Classifier)...")
    main_model = SemanticIntentClassifier(c_param=1.5)
    main_model.fit(X_train, y_train)
    preds_main = [p.intent for p in main_model.predict_batch(X_test)]
    metrics_main = evaluate_model(y_test, preds_main, classes)
    main_model.save(f"{data_dir}/main_intent_classifier.pkl")
    logger.info("Main Model: Accuracy=%.4f, Macro-F1=%.4f", metrics_main["accuracy"], metrics_main["macro_f1"])

    results = {
        "dataset_sizes": {
            "train": len(X_train),
            "val": len(X_val),
            "test": len(X_test),
        },
        "baseline_a_most_frequent": metrics_a,
        "baseline_b_tfidf_logistic": metrics_b,
        "main_semantic_classifier": metrics_main,
    }

    Path(output_report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info("Benchmark report saved to %s", output_report_path)
    return results


if __name__ == "__main__":
    run_training_pipeline()
