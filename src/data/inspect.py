"""Dataset inspection script for Twitter Customer Support dataset (twcs.csv).

Safely streams through large CSV in chunks without excessive memory usage.
Profiles columns, missing values, duplicates, author roles, and brand activity.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def inspect_dataset(
    csv_path: str = "data/raw/twcs.csv",
    output_report_path: str = "data/interim/data_inspection_report.json",
    chunk_size: int = 100_000,
) -> Dict[str, Any]:
    """Inspects the raw CSV file and computes profiling metrics."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found at {csv_path}")

    logger.info("Reading header and previewing first 5 rows...")
    preview_df = pd.read_csv(csv_path, nrows=5)
    columns = list(preview_df.columns)
    logger.info("Columns found: %s", columns)

    total_rows = 0
    null_counts: Dict[str, int] = {col: 0 for col in columns}
    inbound_counts: Dict[str, int] = {"True": 0, "False": 0, "Other": 0}
    brand_counts: Dict[str, int] = {}
    text_lengths = []
    seen_tweet_ids = set()
    duplicate_tweet_ids = 0

    logger.info("Streaming through CSV in chunks of %d...", chunk_size)
    for chunk_idx, chunk in enumerate(
        pd.read_csv(
            csv_path,
            chunksize=chunk_size,
            dtype={
                "tweet_id": str,
                "author_id": str,
                "inbound": str,
                "created_at": str,
                "text": str,
                "response_tweet_id": str,
                "in_reply_to_tweet_id": str,
            },
        )
    ):
        total_rows += len(chunk)

        # Null counts
        for col in columns:
            null_counts[col] += int(chunk[col].isna().sum())

        # Inbound distribution
        for val, count in chunk["inbound"].value_counts().items():
            val_str = str(val).strip()
            if val_str in inbound_counts:
                inbound_counts[val_str] += int(count)
            else:
                inbound_counts["Other"] += int(count)

        # Outbound authors are brand support accounts
        outbound = chunk[chunk["inbound"].astype(str).str.lower() == "false"]
        for author, count in outbound["author_id"].value_counts().items():
            brand_counts[author] = brand_counts.get(author, 0) + int(count)

        # Text length samples (sample 500 per chunk to keep memory minimal)
        sampled_texts = chunk["text"].dropna().sample(min(500, len(chunk)), random_state=42)
        text_lengths.extend(sampled_texts.str.len().tolist())

        if (chunk_idx + 1) % 5 == 0:
            logger.info("Processed %d rows...", total_rows)

    # Sort brand counts descending
    sorted_brands = sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)

    text_len_arr = np.array(text_lengths)
    report: Dict[str, Any] = {
        "file_path": str(path.resolve()),
        "file_size_bytes": path.stat().st_size,
        "total_rows": total_rows,
        "columns": columns,
        "null_counts": null_counts,
        "null_percentages": {k: round(v / total_rows * 100, 2) for k, v in null_counts.items()},
        "inbound_distribution": inbound_counts,
        "inbound_ratio": round(inbound_counts["True"] / max(1, inbound_counts["False"]), 3),
        "text_length_stats": {
            "min": int(text_len_arr.min()) if len(text_len_arr) else 0,
            "max": int(text_len_arr.max()) if len(text_len_arr) else 0,
            "mean": round(float(text_len_arr.mean()), 2) if len(text_len_arr) else 0,
            "median": float(np.median(text_len_arr)) if len(text_len_arr) else 0,
            "std": round(float(text_len_arr.std()), 2) if len(text_len_arr) else 0,
        },
        "top_brands_by_response_volume": [
            {"brand": b, "response_count": count} for b, count in sorted_brands[:25]
        ],
    }

    out_p = Path(output_report_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Inspection complete! Report saved to %s", output_report_path)
    logger.info("Total rows: %d", total_rows)
    logger.info("Top 5 brands: %s", sorted_brands[:5])
    return report


if __name__ == "__main__":
    inspect_dataset()
