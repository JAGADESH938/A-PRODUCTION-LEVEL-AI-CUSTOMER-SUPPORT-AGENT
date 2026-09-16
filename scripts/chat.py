"""Interactive Live Chat Terminal with AppleSupport AI Agent.

Allows you to enter any custom customer inquiry and view the full
step-by-step breakdown:
- Input Message
- Intent Classification & Confidence
- Historical Evidence Retrieved (with similarity scores)
- Escalation Decision & Justification
- Grounded Brand Response
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.pipeline import CustomerSupportPipeline
from src.schemas.models import SupportRequest


def start_chat():
    print("=" * 65)
    print("      APPLE SUPPORT AI AGENT — LIVE INTERACTIVE CHAT")
    print("=" * 65)
    print("Loading models and vector index... (takes ~2 seconds)")
    pipeline = CustomerSupportPipeline()
    print("Agent is ready!")
    print("Type your question below (or type 'quit' or 'exit' to stop).\n")

    while True:
        try:
            user_input = input("You > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["quit", "exit", "q"]:
                print("\nExiting chat. Goodbye!")
                break

            response = pipeline.process(SupportRequest(customer_message=user_input))

            print("\n" + "─" * 65)
            print(f" INPUT:              {user_input}")
            print(f" PREDICTED INTENT:   {response.intent}")
            print(f" CONFIDENCE SCORE:   {response.confidence:.2f}")
            print(f" DECISION:           {response.decision}")
            print(f" REASON:             {response.reason}")
            print(f"\n SUGGESTED RESPONSE:\n {response.response}")

            print("\n RETRIEVED HISTORICAL EVIDENCE:")
            if response.evidence:
                for i, ev in enumerate(response.evidence, 1):
                    print(f"   [{i}] (Similarity: {ev.similarity:.2f} | Intent: {ev.intent})")
                    print(f"       Response: {ev.brand_response[:90]}...")
            else:
                print("   (No historical matches above threshold)")
            print("─" * 65 + "\n")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat. Goodbye!")
            break


if __name__ == "__main__":
    start_chat()
