"""
intents.py

Intent taxonomy for SpotifyCares, derived by reading the actual exchanges in the
data (see decision_log.md, decision #3, for why these six and not Banking77's 77).

    PLAYBACK_TECH_ISSUE   - skipping, buffering, crashing, stopping mid-song, device/app bugs
    ACCOUNT_LOGIN         - can't log in, password, linked accounts, account access
    BILLING_SUBSCRIPTION  - charges, refunds, plan changes, premium/free, cancellations
    HOW_TO_FEATURE_Q      - "how do I...", feature availability/education questions
    COMPLAINT_NEGATIVE    - general dissatisfaction / venting without a concrete actionable ask
    PRAISE_THANKS         - positive feedback, thanks, issue confirmed resolved

Two baselines are included here on purpose, matching the assignment's requirement
for "at least two baselines (a trivial one and a simple one)":

    TrivialBaseline -> always predicts the single most frequent class in the
                        training/reference distribution ("majority class").
    KeywordBaseline -> simple, transparent keyword/regex rules per intent.
                        This is the "simple" baseline the LLM must beat.
"""
from __future__ import annotations
import re
from collections import Counter

INTENTS = [
    "PLAYBACK_TECH_ISSUE",
    "ACCOUNT_LOGIN",
    "BILLING_SUBSCRIPTION",
    "HOW_TO_FEATURE_Q",
    "COMPLAINT_NEGATIVE",
    "PRAISE_THANKS",
]

# Whether a human should generally review this intent before it goes out.
# This is a PRIOR used by escalation.py, not a hard rule -- it gets combined with
# per-message signals (see escalation.py).
DEFAULT_ESCALATE_PRIOR = {
    "PLAYBACK_TECH_ISSUE": False,
    "ACCOUNT_LOGIN": True,      # touches account security/access -> human by default
    "BILLING_SUBSCRIPTION": True,  # money -> human by default
    "HOW_TO_FEATURE_Q": False,
    "COMPLAINT_NEGATIVE": True,  # reputational risk / needs judgment call
    "PRAISE_THANKS": False,
}


class TrivialBaseline:
    """Always predicts the majority class. Needs no data, no keywords, nothing."""

    def __init__(self, majority_label: str = "PLAYBACK_TECH_ISSUE"):
        self.majority_label = majority_label

    def fit(self, texts, labels):
        if labels:
            self.majority_label = Counter(labels).most_common(1)[0][0]
        return self

    def predict(self, text: str) -> str:
        return self.majority_label


_KEYWORD_RULES = [
    ("BILLING_SUBSCRIPTION", re.compile(
        r"\b(refund|charge(d)?|billing|invoice|cancel(led|ing)?|subscription|premium plan|"
        r"payment|price|renew|trial)\b", re.I)),
    ("ACCOUNT_LOGIN", re.compile(
        r"\b(log ?in|log ?out|password|can'?t access|account (is )?(locked|hacked|disabled)|"
        r"linked account|sign ?in|reset)\b", re.I)),
    ("PLAYBACK_TECH_ISSUE", re.compile(
        r"\b(skip(ping)?|buffer(ing)?|crash(ing|es|ed)?|freeze|freezing|stop(s|ped|ping)?|"
        r"lag(ging)?|glitch|bug|won'?t (play|load|open)|not (working|loading))\b", re.I)),
    ("HOW_TO_FEATURE_Q", re.compile(
        r"\b(how do i|how can i|is there a way|does spotify have|feature request|wish (it|you) "
        r"(had|could))\b", re.I)),
    ("PRAISE_THANKS", re.compile(
        r"\b(thanks|thank you|brilliant|awesome|appreciate|great job|resolved|working now|"
        r"fixed|fingers crossed)\b", re.I)),
    ("COMPLAINT_NEGATIVE", re.compile(
        r"\b(hate|worst|terrible|awful|sucks|sux|ridiculous|unacceptable|disappointed|angry|"
        r"furious)\b", re.I)),
]


class KeywordBaseline:
    """Transparent, explainable regex rules. First matching rule wins; falls back
    to COMPLAINT_NEGATIVE (a safe-ish default: better to over-flag than to silently
    misclassify an upset customer as a how-to question)."""

    def predict(self, text: str) -> str:
        for label, pattern in _KEYWORD_RULES:
            if pattern.search(text or ""):
                return label
        return "COMPLAINT_NEGATIVE"
