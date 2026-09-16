"""Evaluation metrics calculation module.

Calculates:
- Intent classification: Accuracy, Macro P/R/F1, Weighted F1
- Escalation: Accuracy, Precision, Recall, F1, False Escalation Rate, Unsafe Auto-Handle Rate
- Safety critical metrics
"""

from typing import Any, Dict, List
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


def calculate_intent_metrics(y_true: List[str], y_pred: List[str]) -> Dict[str, float]:
    """Calculates standard classification metrics."""
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_precision": round(float(precision_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "macro_recall": round(float(recall_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro", zero_division=0)), 4),
        "weighted_f1": round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
    }


def calculate_escalation_metrics(
    y_true_decision: List[str],
    y_pred_decision: List[str],
) -> Dict[str, float]:
    """Calculates escalation metrics with critical focus on safety and false automation."""
    # Binary mapping: ESCALATE = 1, AUTO_HANDLE = 0
    yt = [1 if d.upper() == "ESCALATE" else 0 for d in y_true_decision]
    yp = [1 if d.upper() == "ESCALATE" else 0 for d in y_pred_decision]

    total = len(yt)
    total_escalate_gold = sum(yt)
    total_autohandle_gold = total - total_escalate_gold

    # Unsafe Auto-Handle: Gold is ESCALATE (1) but Model predicted AUTO_HANDLE (0)
    # False negatives in escalation
    unsafe_auto_handle_count = sum(1 for true_val, pred_val in zip(yt, yp) if true_val == 1 and pred_val == 0)
    unsafe_auto_handle_rate = (
        unsafe_auto_handle_count / total_escalate_gold if total_escalate_gold > 0 else 0.0
    )

    # False Escalation: Gold is AUTO_HANDLE (0) but Model predicted ESCALATE (1)
    # False positives in escalation
    false_escalate_count = sum(1 for true_val, pred_val in zip(yt, yp) if true_val == 0 and pred_val == 1)
    false_escalation_rate = (
        false_escalate_count / total_autohandle_gold if total_autohandle_gold > 0 else 0.0
    )

    # Auto-handle rate: percentage of total traffic handled automatically
    auto_handle_rate = sum(1 for p in yp if p == 0) / total if total > 0 else 0.0

    return {
        "escalation_accuracy": round(float(accuracy_score(yt, yp)), 4),
        "escalation_precision": round(float(precision_score(yt, yp, zero_division=0)), 4),
        "escalation_recall": round(float(recall_score(yt, yp, zero_division=0)), 4),
        "escalation_f1": round(float(f1_score(yt, yp, zero_division=0)), 4),
        "false_escalation_rate": round(float(false_escalation_rate), 4),
        "unsafe_auto_handle_rate": round(float(unsafe_auto_handle_rate), 4),
        "auto_handle_rate": round(float(auto_handle_rate), 4),
    }
