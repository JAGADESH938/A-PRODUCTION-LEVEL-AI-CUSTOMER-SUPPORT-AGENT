"""Evaluation script for historical response retrieval.

Measures:
- Recall@1, Recall@3, Recall@5
- MRR (Mean Reciprocal Rank)
- Intent Consistency Rate (top-1 and top-3)
- Retrieval Failure Cases Collection
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from src.retrieval.vector_store import LocalVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def evaluate_retrieval(
    index_path: str = "data/processed/retrieval_index.pkl",
    test_jsonl: str = "data/processed/test.jsonl",
    sample_size: int = 500,
    output_report_path: str = "reports/retrieval_benchmark.json",
) -> Dict[str, Any]:
    logger.info("Loading vector index from %s...", index_path)
    store = LocalVectorStore()
    store.load(index_path)

    logger.info("Loading test queries from %s...", test_jsonl)
    test_records = []
    with open(test_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                test_records.append(json.loads(line))

    if sample_size and len(test_records) > sample_size:
        test_records = test_records[:sample_size]

    logger.info("Evaluating retrieval over %d test queries...", len(test_records))

    recall_at_1 = []
    recall_at_3 = []
    recall_at_5 = []
    reciprocal_ranks = []
    top_1_intent_match = []
    top_3_intent_match = []
    failures = []

    for item in test_records:
        query = item.get("customer_text", "")
        gold_intent = item.get("intent", "")
        if not query.strip():
            continue

        retrieved = store.search(query=query, top_k=5)
        if not retrieved:
            recall_at_1.append(0)
            recall_at_3.append(0)
            recall_at_5.append(0)
            reciprocal_ranks.append(0)
            continue

        # Intent consistency check
        intents_retrieved = [doc.intent for doc in retrieved if doc.intent]

        # Intent match at 1
        top_1_match = 1 if len(intents_retrieved) > 0 and intents_retrieved[0] == gold_intent else 0
        top_1_intent_match.append(top_1_match)

        # Intent match in top 3
        top_3_match = 1 if any(i == gold_intent for i in intents_retrieved[:3]) else 0
        top_3_intent_match.append(top_3_match)

        # Recall at K (intent consistency proxy)
        recall_at_1.append(top_1_match)
        recall_at_3.append(top_3_match)
        recall_at_5.append(1 if any(i == gold_intent for i in intents_retrieved[:5]) else 0)

        # Reciprocal Rank
        rank = 0
        for idx, doc_intent in enumerate(intents_retrieved):
            if doc_intent == gold_intent:
                rank = idx + 1
                break
        reciprocal_ranks.append(1.0 / rank if rank > 0 else 0.0)

        # Log failure cases if top 1 failed and similarity was low or mismatched
        if top_1_match == 0 and len(failures) < 20:
            failures.append({
                "query": query,
                "gold_intent": gold_intent,
                "top_retrieved_intent": intents_retrieved[0] if intents_retrieved else "NONE",
                "top_similarity": retrieved[0].similarity if retrieved else 0.0,
                "top_brand_response": retrieved[0].brand_response if retrieved else "",
            })

    metrics = {
        "sample_size": len(test_records),
        "recall_at_1": round(float(np.mean(recall_at_1)), 4),
        "recall_at_3": round(float(np.mean(recall_at_3)), 4),
        "recall_at_5": round(float(np.mean(recall_at_5)), 4),
        "mrr": round(float(np.mean(reciprocal_ranks)), 4),
        "top_1_intent_consistency": round(float(np.mean(top_1_intent_match)), 4),
        "top_3_intent_consistency": round(float(np.mean(top_3_intent_match)), 4),
        "sample_failures": failures[:5],
    }

    logger.info("Retrieval Evaluation Results: Recall@1=%.4f, Recall@3=%.4f, Recall@5=%.4f, MRR=%.4f",
                metrics["recall_at_1"], metrics["recall_at_3"], metrics["recall_at_5"], metrics["mrr"])

    Path(output_report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    return metrics


if __name__ == "__main__":
    evaluate_retrieval()
