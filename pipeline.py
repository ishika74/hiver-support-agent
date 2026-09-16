"""
pipeline.py

End-to-end agent: text in -> (intent, reply, escalation decision + reason) out.

    python pipeline.py "my spotify keeps skipping songs on my iphone"
"""
from __future__ import annotations
import sys

# Windows' default console encoding (cp1252) can't print emoji or other
# non-ASCII characters that real Twitter replies/customer messages contain,
# which crashes with UnicodeEncodeError on `print()`. Force UTF-8 output with
# a safe fallback instead of a hard crash. No-op on platforms where stdout is
# already UTF-8 (Mac/Linux).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass  # Python < 3.7 doesn't have reconfigure(); not a concern here.

from dataclasses import dataclass

from ingest import load_raw, build_exchanges_for_brand, clean_text
from retrieval import ExchangeRetriever
from classifier import classify
from reply_generator import draft_reply
from escalation import decide as decide_escalation


@dataclass
class AgentResult:
    customer_text: str
    intent: str
    intent_confidence: float
    intent_reasoning: str
    retrieved_examples: list
    reply: str
    escalate: bool
    escalation_reason: str


class SupportAgent:
    def __init__(self, csv_path: str, brand: str):
        self.brand = brand
        df = load_raw(csv_path)
        self.exchanges = build_exchanges_for_brand(df, brand)
        self.retriever = ExchangeRetriever(self.exchanges)

    def handle(self, customer_text: str, prior_turns_in_thread: int = 0) -> AgentResult:
        customer_text = clean_text(customer_text)

        cls = classify(customer_text)
        intent, confidence, reasoning = cls["intent"], cls["confidence"], cls["reasoning"]

        esc = decide_escalation(customer_text, intent, confidence, prior_turns_in_thread)

        hits = self.retriever.retrieve(customer_text, k=3)
        reply = draft_reply(customer_text, intent, hits, esc.escalate)

        return AgentResult(
            customer_text=customer_text,
            intent=intent,
            intent_confidence=confidence,
            intent_reasoning=reasoning,
            retrieved_examples=[(h.exchange.customer_text, h.exchange.brand_text, h.score) for h in hits],
            reply=reply,
            escalate=esc.escalate,
            escalation_reason=esc.reason,
        )


if __name__ == "__main__":
    import os
    text = sys.argv[1] if len(sys.argv) > 1 else "my spotify keeps skipping songs on my iphone"
    # Resolve the CSV path relative to THIS FILE's location, not the current
    # working directory, so this works whether you run it from src/ or from
    # the project root (a real bug in an earlier version of this file --
    # it used to hardcode "data/sample.csv" assuming cwd==project root).
    default_csv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sample.csv")
    agent = SupportAgent(default_csv, "SpotifyCares")
    result = agent.handle(text)
    print("INTENT:      ", result.intent, f"(confidence={result.intent_confidence:.2f})")
    print("REASONING:   ", result.intent_reasoning)
    print("ESCALATE:    ", result.escalate)
    print("ESC. REASON: ", result.escalation_reason)
    print("RETRIEVED:   ", len(result.retrieved_examples), "historical examples")
    print("REPLY:       ", result.reply)
