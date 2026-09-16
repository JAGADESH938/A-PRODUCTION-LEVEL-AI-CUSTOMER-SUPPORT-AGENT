"""Conversation builder and train/val/test splitter for AppleSupport.

Reconstructs multi-turn conversational threads between customer and AppleSupport.
Ensures zero data leakage by splitting on conversation_id.
"""

import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd
from src.data.clean import clean_tweet_text, pd_not_na

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def build_apple_conversations(
    raw_csv: str = "data/raw/twcs.csv",
    brand_name: str = "AppleSupport",
    max_conversations: int = 15_000,
    output_dir: str = "data/processed",
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    seed: int = 42,
) -> Dict[str, Any]:
    """Reconstructs dialogues and creates train/val/test splits."""
    random.seed(seed)
    raw_path = Path(raw_csv)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw CSV not found at {raw_csv}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Pass 1: Identifying %s brand responses and referenced parent tweets...", brand_name)
    brand_tweets: Dict[str, Dict[str, Any]] = {}
    needed_parent_ids: Set[str] = set()

    # Pass 1: Collect brand tweets
    for chunk in pd.read_csv(
        raw_csv,
        chunksize=100_000,
        dtype=str,
        usecols=["tweet_id", "author_id", "inbound", "created_at", "text", "in_response_to_tweet_id"],
    ):
        brand_chunk = chunk[chunk["author_id"] == brand_name]
        for _, row in brand_chunk.iterrows():
            tid = str(row["tweet_id"]).strip()
            parent_id = str(row["in_response_to_tweet_id"]).strip() if pd_not_na(row["in_response_to_tweet_id"]) else ""
            brand_tweets[tid] = {
                "tweet_id": tid,
                "author_id": brand_name,
                "inbound": False,
                "created_at": str(row["created_at"]),
                "text": str(row["text"]),
                "in_response_to_tweet_id": parent_id,
            }
            if parent_id:
                needed_parent_ids.add(parent_id)

    logger.info("Collected %d brand tweets. Needed parent customer tweets: %d", len(brand_tweets), len(needed_parent_ids))

    # Pass 2: Collect parent customer tweets
    logger.info("Pass 2: Retrieving parent customer tweets...")
    customer_tweets: Dict[str, Dict[str, Any]] = {}
    for chunk in pd.read_csv(
        raw_csv,
        chunksize=100_000,
        dtype=str,
        usecols=["tweet_id", "author_id", "inbound", "created_at", "text", "in_response_to_tweet_id"],
    ):
        matched = chunk[chunk["tweet_id"].isin(needed_parent_ids)]
        for _, row in matched.iterrows():
            tid = str(row["tweet_id"]).strip()
            parent_id = str(row["in_response_to_tweet_id"]).strip() if pd_not_na(row["in_response_to_tweet_id"]) else ""
            customer_tweets[tid] = {
                "tweet_id": tid,
                "author_id": str(row["author_id"]).strip(),
                "inbound": str(row["inbound"]).strip().lower() == "true",
                "created_at": str(row["created_at"]),
                "text": str(row["text"]),
                "in_response_to_tweet_id": parent_id,
            }

    logger.info("Retrieved %d matching customer tweets.", len(customer_tweets))

    # Build dialogues: (Customer query -> Brand reply)
    # Also check if customer tweet has a grandparent (multi-turn context)
    conversations: List[Dict[str, Any]] = []

    for brand_tid, b_tweet in brand_tweets.items():
        parent_tid = b_tweet["in_response_to_tweet_id"]
        if not parent_tid or parent_tid not in customer_tweets:
            continue

        c_tweet = customer_tweets[parent_tid]
        
        # Raw and cleaned texts
        c_raw = c_tweet["text"]
        b_raw = b_tweet["text"]
        c_clean = clean_tweet_text(c_raw)
        b_clean = clean_tweet_text(b_raw)

        if not c_clean or not b_clean:
            continue

        # Skip noise / pure mentions / too short
        if len(c_clean.split()) < 3 or len(b_clean.split()) < 3:
            continue

        # Check multi-turn context (if parent had a parent in customer_tweets or brand_tweets)
        history: List[Dict[str, str]] = []
        grandparent_id = c_tweet["in_response_to_tweet_id"]
        if grandparent_id:
            if grandparent_id in brand_tweets:
                gp = brand_tweets[grandparent_id]
                history.append({"speaker": "brand", "text": clean_tweet_text(gp["text"])})
            elif grandparent_id in customer_tweets:
                gp = customer_tweets[grandparent_id]
                history.append({"speaker": "customer", "text": clean_tweet_text(gp["text"])})

        history.append({"speaker": "customer", "text": c_clean})

        formatted_context = ""
        if len(history) > 1:
            formatted_context = "\n".join(
                f"{item['speaker'].capitalize()}: {item['text']}" for item in history[:-1]
            )

        conversation_record = {
            "conversation_id": f"conv_{parent_tid}_{brand_tid}",
            "customer_tweet_id": parent_tid,
            "brand_tweet_id": brand_tid,
            "customer_text": c_clean,
            "raw_customer_text": c_raw,
            "brand_response": b_clean,
            "raw_brand_response": b_raw,
            "turns_count": len(history) + 1,
            "conversation_context": formatted_context,
            "created_at": b_tweet["created_at"],
        }
        conversations.append(conversation_record)

    logger.info("Total reconstructed valid conversations: %d", len(conversations))

    # Shuffle deterministically and limit if max_conversations is set
    random.shuffle(conversations)
    if max_conversations and len(conversations) > max_conversations:
        conversations = conversations[:max_conversations]

    # Conversation-level train / val / test split
    total = len(conversations)
    n_train = int(total * train_ratio)
    n_val = int(total * val_ratio)
    train_data = conversations[:n_train]
    val_data = conversations[n_train : n_train + n_val]
    test_data = conversations[n_train + n_val :]

    logger.info("Split sizes: Train=%d, Val=%d, Test=%d", len(train_data), len(val_data), len(test_data))

    # Save to jsonl
    def save_jsonl(records: List[Dict[str, Any]], filename: str):
        filepath = out_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")
        logger.info("Saved %d records to %s", len(records), filepath)

    save_jsonl(conversations, "all_conversations.jsonl")
    save_jsonl(train_data, "train.jsonl")
    save_jsonl(val_data, "val.jsonl")
    save_jsonl(test_data, "test.jsonl")

    summary = {
        "total_conversations": total,
        "train_count": len(train_data),
        "val_count": len(val_data),
        "test_count": len(test_data),
        "multi_turn_count": sum(1 for c in conversations if c["turns_count"] > 2),
    }

    with open(out_dir / "split_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    build_apple_conversations()
