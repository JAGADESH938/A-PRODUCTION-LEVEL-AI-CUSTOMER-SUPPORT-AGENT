"""Unit tests for text cleaning and normalization."""

import pytest
from src.data.clean import clean_tweet_text, pd_not_na


def test_clean_tweet_text_urls_and_handles():
    raw = "@AppleSupport I need help with my iPhone! Check this link: https://t.co/abc1234"
    cleaned = clean_tweet_text(raw, mask_handles=True, mask_urls=True)
    assert "@user" in cleaned
    assert "[URL]" in cleaned
    assert "https://t.co/abc1234" not in cleaned
    assert "@AppleSupport" not in cleaned


def test_clean_tweet_text_empty_and_whitespace():
    assert clean_tweet_text("") == ""
    assert clean_tweet_text("   \n\t  ") == ""
    assert clean_tweet_text(None) == ""


def test_clean_tweet_text_zero_width_spaces():
    raw = "Hello\u200bWorld\ufeff!"
    cleaned = clean_tweet_text(raw)
    assert cleaned == "HelloWorld!"


def test_pd_not_na():
    assert pd_not_na("12345") is True
    assert pd_not_na("") is False
    assert pd_not_na(None) is False
    assert pd_not_na("nan") is False
    assert pd_not_na("None") is False
    assert pd_not_na("NULL") is False
