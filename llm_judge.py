"""
llm_judge.py

Scores a drafted reply against a rubric, using an LLM judge. Also ships a small
set of examples pre-scored by a human (me) so run_eval.py can report judge/human
agreement -- this is the evidence the brief asks for ("how well your judge
agrees with a human"), not just an assertion that the judge is trustworthy.

Rubric (1-5 each):
  groundedness   - does the reply match how this brand actually resolves this kind
                   of issue (per retrieved examples), rather than generic/invented advice?
  correctness    - is the troubleshooting/information factually sound and not misleading?
  tone           - does it match the brand's real tone (brief, friendly, on-brand)?
  actionability  - does the customer know what to do next (or that a human is coming)?

Overall = mean of the four, still 1-5.
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass

from llm_client import call_llm, QUALITY_MODEL

JUDGE_SYSTEM = """You are grading a customer-support reply drafted by an AI agent for
Spotify's Twitter support account. Score the DRAFTED_REPLY on 4 dimensions, 1-5 each
(5=excellent):

- groundedness: does it match how the brand actually resolves this kind of issue,
  based on RETRIEVED_HISTORICAL_EXAMPLES, rather than generic or invented advice?
  If no examples were retrieved, judge whether the reply avoids inventing brand-specific
  claims it can't support.
- correctness: is any troubleshooting/information given factually sound and not misleading?
- tone: brief, friendly, on-brand (matches examples' tone if available)?
- actionability: does the customer clearly know what happens next?

Respond with ONLY JSON:
{"groundedness": <1-5>, "correctness": <1-5>, "tone": <1-5>, "actionability": <1-5>, "rationale": "<one sentence>"}
"""


@dataclass
class JudgeScore:
    groundedness: int
    correctness: int
    tone: int
    actionability: int
    rationale: str

    @property
    def overall(self) -> float:
        return (self.groundedness + self.correctness + self.tone + self.actionability) / 4


def judge_reply(customer_text: str, reply: str, retrieved_examples: list, escalate: bool,
                 model: str = QUALITY_MODEL) -> JudgeScore:
    examples_str = "\n".join(
        f"- Customer: {c}\n  Brand: {b}" for c, b, _ in retrieved_examples
    ) or "(none retrieved)"
    prompt = f"""CUSTOMER_MESSAGE: {customer_text}
ESCALATE_DECISION: {escalate}
RETRIEVED_HISTORICAL_EXAMPLES:
{examples_str}

DRAFTED_REPLY: {reply}

Score it now."""
    raw = call_llm(prompt=prompt, system=JUDGE_SYSTEM, model=model, max_tokens=200)
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    obj = json.loads(cleaned)
    return JudgeScore(
        groundedness=int(obj["groundedness"]),
        correctness=int(obj["correctness"]),
        tone=int(obj["tone"]),
        actionability=int(obj["actionability"]),
        rationale=obj.get("rationale", ""),
    )


# --- Human-calibration set -------------------------------------------------
# 6 (customer, reply, human_overall_1to5) triples scored by hand, used to check
# judge/human agreement in run_eval.py. Keep this small and honest: 6 is enough
# to sanity-check gross miscalibration, NOT enough to certify the judge -- see
# report/REPORT.md, "What's misleading about my headline number".
HUMAN_CALIBRATION_SET = [
    {
        "customer_text": "@SpotifyCares the app crashes every single time I try to play a podcast on my Pixel 7",
        "reply": "Sorry about that! Could you try logging out, restarting your device, and logging back in? Let us know if it still crashes. /AY",
        "retrieved_examples": [],
        "escalate": False,
        "human_overall": 4,
    },
    {
        "customer_text": "@SpotifyCares I was charged twice for Premium this month, can I get one refunded",
        "reply": "Sorry to hear that! We'll take a closer look — a specialist will follow up with you over DM shortly to sort out the refund.",
        "retrieved_examples": [],
        "escalate": True,
        "human_overall": 5,
    },
    {
        "customer_text": "@SpotifyCares I was charged twice for Premium this month, can I get one refunded",
        "reply": "No problem, we've refunded you $9.99 right now, check your account in 24 hours!",
        "retrieved_examples": [],
        "escalate": True,
        "human_overall": 1,  # bad: an AI agent should never claim to have made a billing change
    },
    {
        "customer_text": "this app gets worse with every update, absolute joke @SpotifyCares",
        "reply": "We hear you and we're sorry it's been frustrating. Can you tell us a bit more about what's been going wrong so we can look into it? /CP",
        "retrieved_examples": [],
        "escalate": True,
        "human_overall": 4,
    },
    {
        "customer_text": "@SpotifyCares how do I make a collaborative playlist with my roommates",
        "reply": "Easy! Open the playlist, tap the ... menu, then 'Collaborative playlist', and share the link with your roommates 🎶",
        "retrieved_examples": [],
        "escalate": False,
        "human_overall": 5,
    },
    {
        "customer_text": "@SpotifyCares how do I make a collaborative playlist with my roommates",
        "reply": "We are sorry you're having trouble. Please DM us your account details so we can look into this.",
        "retrieved_examples": [],
        "escalate": False,
        "human_overall": 2,  # bad: treats a simple how-to as if it were a problem needing DM/account access
    },
]
