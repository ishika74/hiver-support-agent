from __future__ import annotations

import re


INTENTS = [
    "PLAYBACK_TECH_ISSUE",
    "ACCOUNT_LOGIN",
    "BILLING_SUBSCRIPTION",
    "HOW_TO_FEATURE_Q",
    "COMPLAINT_NEGATIVE",
    "PRAISE_THANKS",
]


def classify(text: str) -> dict:
    text_lower = text.lower()

    scores = {intent: 0 for intent in INTENTS}

    playback_words = [
        "skip", "skipping", "buffer", "buffering", "pause",
        "not playing", "playback", "song", "music", "audio",
        "crash", "freeze", "error"
    ]

    account_words = [
        "login", "log in", "sign in", "password", "account",
        "username", "cannot access", "can't access"
    ]

    billing_words = [
        "charge", "charged", "payment", "billing", "subscription",
        "premium", "refund", "cancel", "money"
    ]

    howto_words = [
        "how do i", "how can i", "where can i", "how to",
        "change", "enable", "disable", "feature", "settings"
    ]

    complaint_words = [
        "bad", "terrible", "worst", "angry", "frustrated",
        "disappointed", "hate", "useless", "not working"
    ]

    praise_words = [
        "thanks", "thank you", "great", "awesome", "love",
        "excellent", "helpful", "amazing"
    ]

    keyword_groups = {
        "PLAYBACK_TECH_ISSUE": playback_words,
        "ACCOUNT_LOGIN": account_words,
        "BILLING_SUBSCRIPTION": billing_words,
        "HOW_TO_FEATURE_Q": howto_words,
        "COMPLAINT_NEGATIVE": complaint_words,
        "PRAISE_THANKS": praise_words,
    }

    for intent, words in keyword_groups.items():
        for word in words:
            if word in text_lower:
                scores[intent] += 1

    best_intent = max(scores, key=scores.get)
    best_score = scores[best_intent]

    if best_score == 0:
        best_intent = "COMPLAINT_NEGATIVE"
        confidence = 0.30
        reasoning = "No strong keyword match; assigned the fallback intent."
    else:
        confidence = min(0.95, 0.55 + best_score * 0.10)
        reasoning = (
            f"Matched {best_score} keyword(s) associated with "
            f"{best_intent}."
        )

    return {
        "intent": best_intent,
        "confidence": confidence,
        "reasoning": reasoning,
    }
