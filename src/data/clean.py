"""Text cleaning and normalization utilities for tweets."""

import re
from typing import Dict, Optional


def clean_tweet_text(text: str, mask_handles: bool = True, mask_urls: bool = True) -> str:
    """Normalizes raw tweet text while preserving meaning and structure."""
    if not isinstance(text, str) or not text.strip():
        return ""

    cleaned = text

    # Remove BOM and zero-width spaces
    cleaned = cleaned.replace("\ufeff", "").replace("\u200b", "")

    # Mask URLs if requested
    if mask_urls:
        cleaned = re.sub(r"https?://\S+|www\.\S+", "[URL]", cleaned)

    # Normalize/mask handles if requested
    if mask_handles:
        # Keep brand handle clean or normalize user handles
        cleaned = re.sub(r"@\w+", "@user", cleaned)

    # Normalize excessive whitespaces / tabs / newlines
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def normalize_record(record: Dict[str, str]) -> Optional[Dict[str, str]]:
    """Validates and cleans a raw tweet record."""
    raw_text = record.get("text", "")
    if not isinstance(raw_text, str) or not raw_text.strip():
        return None

    cleaned_text = clean_tweet_text(raw_text)
    if not cleaned_text:
        return None

    return {
        "tweet_id": str(record.get("tweet_id", "")).strip(),
        "author_id": str(record.get("author_id", "")).strip(),
        "inbound": str(record.get("inbound", "")).strip().lower() == "true",
        "created_at": str(record.get("created_at", "")).strip(),
        "raw_text": raw_text.strip(),
        "cleaned_text": cleaned_text,
        "response_tweet_id": str(record.get("response_tweet_id", "")).strip()
        if pd_not_na(record.get("response_tweet_id"))
        else "",
        "in_response_to_tweet_id": str(record.get("in_response_to_tweet_id", "")).strip()
        if pd_not_na(record.get("in_response_to_tweet_id"))
        else "",
    }


def pd_not_na(val: Optional[str]) -> bool:
    """Checks if value is not NA/null/empty."""
    if val is None:
        return False
    s = str(val).strip()
    return s != "" and s.lower() not in ("nan", "none", "null")
