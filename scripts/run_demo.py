"""Interactive and preset CLI demo for AppleSupport AI Customer Support Agent."""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.pipeline import CustomerSupportPipeline
from src.schemas.models import SupportRequest


PRESET_QUERIES = [
    "I was charged twice on my credit card for my monthly iCloud storage subscription.",
    "My iPhone 8 battery drains from 100% to 20% in two hours after updating to iOS 11.",
    "My iOS 11 software update has been stuck on 'Estimating time remaining' all morning.",
    "Someone from another country accessed my Apple ID and locked my iCloud account!",
    "I dropped my iPhone on concrete and the entire screen is shattered into pieces.",
    "Does the Apple Watch Series 3 work with iPhone 6?",
]


def print_support_result(query: str, res) -> None:
    print("\n" + "-" * 60)
    print(f"Customer:\n  {query}")
    print(f"\nIntent:\n  {res.intent}")
    print(f"\nConfidence:\n  {res.confidence:.2f}")
    print(f"\nDecision:\n  {res.decision}")
    print(f"\nReason:\n  {res.reason}")
    print(f"\nSuggested Response:\n  {res.response}")
    print("\nHistorical Evidence:")
    if res.evidence:
        for i, ev in enumerate(res.evidence, 1):
            print(f"  {i}. {ev.conversation_id} (similarity={ev.similarity:.2f}, intent={ev.intent})")
            print(f"     Historical Response: {ev.brand_response[:80]}...")
    else:
        print("  (None retrieved above threshold)")
    print("-" * 60)


def run_demo():
    print("=" * 60)
    print("APPLE SUPPORT AI AGENT — CLI DEMO")
    print("=" * 60)
    print("Loading models and historical retrieval index...")
    pipeline = CustomerSupportPipeline()
    print("Ready!\n")

    print("Running preset support interaction scenarios:")
    for query in PRESET_QUERIES:
        res = pipeline.process(SupportRequest(customer_message=query))
        print_support_result(query, res)

    print("\nPreset demo completed.")


if __name__ == "__main__":
    run_demo()
