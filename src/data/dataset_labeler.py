"""Dataset labeler for AppleSupport conversations.

Assigns intent labels to train, val, and test splits using taxonomy-defined
keywords and semantic patterns from configs/intents.yaml.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_taxonomy(config_path: str = "configs/intents.yaml") -> List[Dict[str, Any]]:
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("intents", [])


def match_intent(text: str, taxonomy: List[Dict[str, Any]]) -> str:
    """Matches text against taxonomy keywords with weighted domain scoring."""
    lower_text = text.lower()

    # Precedence order for edge/conflict cases:
    # 1. Billing & Financial (highest sensitivity)
    # 2. Account & Apple ID security
    # 3. Hardware / Broken screen
    # 4. Battery / Power
    # 5. Software update
    # 6. Audio / Bluetooth
    # 7. Wi-Fi / Cellular
    # 8. App / System performance
    # 9. General inquiry (fallback)

    scores: Dict[str, float] = {}
    for intent in taxonomy:
        name = intent["name"]
        keywords = intent.get("keywords", [])
        score = 0.0
        for kw in keywords:
            # Word boundary matching
            pattern = r"\b" + re.escape(kw.lower()) + r"\b"
            matches = len(re.findall(pattern, lower_text))
            if matches > 0:
                score += matches * (1.5 if len(kw.split()) > 1 else 1.0)
        scores[name] = score

    best_intent, max_score = max(scores.items(), key=lambda x: x[1])
    if max_score > 0.5:
        return best_intent

    return "general_inquiry_feedback"


def label_splits(
    data_dir: str = "data/processed",
    config_path: str = "configs/intents.yaml",
) -> None:
    taxonomy = load_taxonomy(config_path)
    logger.info("Loaded %d intents from %s", len(taxonomy), config_path)

    for split in ["train.jsonl", "val.jsonl", "test.jsonl"]:
        filepath = Path(data_dir) / split
        if not filepath.exists():
            continue

        records = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    text_to_classify = item.get("customer_text", "")
                    # If multi-turn context exists, include it for better disambiguation
                    if item.get("conversation_context"):
                        text_to_classify = f"{item['conversation_context']} {text_to_classify}"
                    item["intent"] = match_intent(text_to_classify, taxonomy)
                    records.append(item)

        # Count distribution
        counts = Counter([r["intent"] for r in records])
        logger.info("Distribution for %s: %s", split, dict(counts))

        # Overwrite with labeled records
        with open(filepath, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    logger.info("Dataset labeling complete.")


if __name__ == "__main__":
    from collections import Counter

    label_splits()
