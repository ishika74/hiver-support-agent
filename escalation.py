"""
escalation.py

Decides AUTO_HANDLE vs ESCALATE for a classified message, with a human-readable reason.

Design: deliberately NOT a black box. It's a small set of explicit, auditable rules
layered on top of the intent prior, because for a support agent the *reason* a message
was or wasn't escalated is a product requirement, not a nice-to-have (see report.md,
"Problem framing").

Order of precedence:
  1. Hard safety/compliance triggers (always escalate, regardless of intent)
  2. Intent-level prior (from intents.DEFAULT_ESCALATE_PRIOR)
  3. Low-confidence classification (escalate rather than guess)
  4. Repeated/unresolved issue signal (thread already went back and forth) -> escalate
"""
from __future__ import annotations
import re
from dataclasses import dataclass

from intents import DEFAULT_ESCALATE_PRIOR

HARD_TRIGGERS = re.compile(
    r"\b(lawyer|legal action|sue|suing|gdpr|data breach|hacked|fraud|unauthorized charge|"
    r"self[- ]harm|suicide|threat(en(ing)?)?|discriminat)\b",
    re.I,
)

CONFIDENCE_ESCALATION_THRESHOLD = 0.6


@dataclass
class EscalationDecision:
    escalate: bool
    reason: str


def decide(text: str, intent: str, intent_confidence: float, prior_turns_in_thread: int = 0) -> EscalationDecision:
    if HARD_TRIGGERS.search(text or ""):
        return EscalationDecision(True, "Hard trigger: message contains a legal/safety/security keyword that always requires human review.")

    if intent_confidence < CONFIDENCE_ESCALATION_THRESHOLD:
        return EscalationDecision(
            True,
            f"Low classifier confidence ({intent_confidence:.2f} < {CONFIDENCE_ESCALATION_THRESHOLD}) for intent '{intent}'; escalating rather than guessing.",
        )

    # NOTE: this rule originally fired on ANY thread with >=3 prior turns, which
    # incorrectly escalated PRAISE_THANKS messages arriving at the end of a long
    # but successfully-resolved thread (found via run_eval.py's escalation
    # rule-logic check against golden examples real_003/004/008 -- see
    # report/REPORT.md failure analysis #1). A long thread is only a sign of
    # being "stuck" if the current message is not itself a resolution/praise signal.
    if prior_turns_in_thread >= 3 and intent != "PRAISE_THANKS":
        return EscalationDecision(
            True,
            f"Thread already has {prior_turns_in_thread} prior turns without resolution; likely needs a human to break the loop.",
        )

    if DEFAULT_ESCALATE_PRIOR.get(intent, True):
        return EscalationDecision(
            True,
            f"Intent '{intent}' touches account access, money, or reputational risk; escalated by policy.",
        )

    return EscalationDecision(
        False,
        f"Intent '{intent}' is a routine, low-risk category with confident classification ({intent_confidence:.2f}); auto-handling with a grounded reply.",
    )
