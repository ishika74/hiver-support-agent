"""
run_eval.py

Runs the golden eval set (eval/golden_eval.jsonl) through:
  1. TrivialBaseline (majority class) -- intent accuracy only, no cost, no API key needed
  2. KeywordBaseline (regex rules)    -- intent accuracy only, no cost, no API key needed
  3. Full LLM system (classifier + escalation + retrieval + reply generator)
     -- requires GEMINI_API_KEY; also runs the LLM judge on generated replies
  4. Judge/human agreement check on llm_judge.HUMAN_CALIBRATION_SET

Usage:
    python run_eval.py --baselines-only      # no API key needed, runs in seconds
    python run_eval.py                       # full run, needs GEMINI_API_KEY

Outputs a metrics summary to stdout and a per-example CSV to eval/eval_results.csv
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict

from intents import TrivialBaseline, KeywordBaseline, INTENTS
from ingest import load_raw, build_exchanges_for_brand
from escalation import decide as decide_escalation


def load_golden(path: str):
    records = []
    with open(path) as f:
        for line in f:
            records.append(json.loads(line))
    return records


def prf1(y_true, y_pred, positive_label):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == positive_label and p == positive_label)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != positive_label and p == positive_label)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == positive_label and p != positive_label)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def macro_f1(y_true, y_pred, labels):
    f1s = [prf1(y_true, y_pred, lbl)[2] for lbl in labels]
    return sum(f1s) / len(f1s)


def run_intent_baselines(records):
    labels = [r["gold_intent"] for r in records]

    trivial = TrivialBaseline().fit([], labels)
    trivial_preds = [trivial.predict(r["customer_text"]) for r in records]
    trivial_acc = sum(p == t for p, t in zip(trivial_preds, labels)) / len(labels)
    trivial_f1 = macro_f1(labels, trivial_preds, INTENTS)

    keyword = KeywordBaseline()
    keyword_preds = [keyword.predict(r["customer_text"]) for r in records]
    keyword_acc = sum(p == t for p, t in zip(keyword_preds, labels)) / len(labels)
    keyword_f1 = macro_f1(labels, keyword_preds, INTENTS)

    print("=== Intent classification: baselines (no API key needed) ===")
    print(f"TrivialBaseline (majority class={trivial.majority_label}): "
          f"accuracy={trivial_acc:.2%}  macro-F1={trivial_f1:.3f}")
    print(f"KeywordBaseline (regex rules):                            "
          f"accuracy={keyword_acc:.2%}  macro-F1={keyword_f1:.3f}")
    print()

    # Per-intent breakdown for the keyword baseline, since that's the bar the LLM must clear
    print("KeywordBaseline per-intent precision/recall/F1:")
    for lbl in INTENTS:
        p, r, f = prf1(labels, keyword_preds, lbl)
        n = labels.count(lbl)
        print(f"  {lbl:22s} n={n:2d}  P={p:.2f} R={r:.2f} F1={f:.2f}")
    print()
    return {
        "trivial": {"accuracy": trivial_acc, "macro_f1": trivial_f1},
        "keyword": {"accuracy": keyword_acc, "macro_f1": keyword_f1},
    }


def run_escalation_rule_check(records):
    """Escalation logic is deterministic given (intent, confidence, prior_turns), so we
    can sanity-check it against gold labels using the GOLD intent (i.e. assuming perfect
    classification) to isolate rule-logic errors from classifier errors."""
    correct = 0
    for r in records:
        decision = decide_escalation(
            r["customer_text"], r["gold_intent"], intent_confidence=0.9,
            prior_turns_in_thread=r["prior_turns_in_thread"],
        )
        if decision.escalate == r["gold_escalate"]:
            correct += 1
    acc = correct / len(records)
    print("=== Escalation rule-logic check (given GOLD intent, isolates rule bugs) ===")
    print(f"Accuracy vs gold escalate label: {acc:.2%}  ({correct}/{len(records)})")
    print()
    return acc


def run_full_llm_system(records, csv_path, brand):
    """Requires GEMINI_API_KEY. Runs classifier + escalation + retrieval + reply
    generation + judge on every golden example."""
    from pipeline import SupportAgent
    from llm_judge import judge_reply

    agent = SupportAgent(csv_path, brand)

    rows = []
    y_true_intent, y_pred_intent = [], []
    esc_correct = 0
    judge_scores = []

    for r in records:
        try:
            result = agent.handle(r["customer_text"], prior_turns_in_thread=r["prior_turns_in_thread"])
        except Exception as e:
            print(f"  [WARN] pipeline failed on {r['id']}: {e}", file=sys.stderr)
            continue

        y_true_intent.append(r["gold_intent"])
        y_pred_intent.append(result.intent)
        esc_ok = result.escalate == r["gold_escalate"]
        esc_correct += esc_ok

        try:
            score = judge_reply(r["customer_text"], result.reply, result.retrieved_examples, result.escalate)
            judge_scores.append(score.overall)
        except Exception as e:
            print(f"  [WARN] judge failed on {r['id']}: {e}", file=sys.stderr)
            score = None

        rows.append({
            "id": r["id"], "source": r["source"], "customer_text": r["customer_text"],
            "gold_intent": r["gold_intent"], "pred_intent": result.intent,
            "intent_confidence": result.intent_confidence, "intent_correct": result.intent == r["gold_intent"],
            "gold_escalate": r["gold_escalate"], "pred_escalate": result.escalate, "escalate_correct": esc_ok,
            "escalation_reason": result.escalation_reason, "reply": result.reply,
            "judge_overall": score.overall if score else None,
        })

    with open(os.path.join(os.path.dirname(csv_path) or ".", "eval_results.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    intent_acc = sum(p == t for p, t in zip(y_pred_intent, y_true_intent)) / len(y_true_intent)
    intent_f1 = macro_f1(y_true_intent, y_pred_intent, INTENTS)
    esc_acc = esc_correct / len(rows)
    avg_judge = sum(judge_scores) / len(judge_scores) if judge_scores else None

    print("=== Full LLM system ===")
    print(f"Intent accuracy: {intent_acc:.2%}   macro-F1: {intent_f1:.3f}")
    print(f"Escalation accuracy (end-to-end, includes classifier error): {esc_acc:.2%}")
    if avg_judge:
        print(f"Avg LLM-judge overall score (1-5): {avg_judge:.2f}  (n={len(judge_scores)})")
    print(f"Per-example results written to eval_results.csv")
    print()


def run_judge_human_agreement():
    from llm_judge import judge_reply, HUMAN_CALIBRATION_SET
    diffs = []
    print("=== Judge vs human agreement (calibration set, n={}) ===".format(len(HUMAN_CALIBRATION_SET)))
    for ex in HUMAN_CALIBRATION_SET:
        score = judge_reply(ex["customer_text"], ex["reply"], ex["retrieved_examples"], ex["escalate"])
        diff = abs(score.overall - ex["human_overall"])
        diffs.append(diff)
        print(f"  human={ex['human_overall']}  judge={score.overall:.2f}  |diff|={diff:.2f}  "
              f"reply='{ex['reply'][:50]}...'")
    mae = sum(diffs) / len(diffs)
    within_1 = sum(d <= 1.0 for d in diffs) / len(diffs)
    print(f"\nMean absolute error: {mae:.2f} (on a 1-5 scale)")
    print(f"Within 1 point of human: {within_1:.0%}")
    print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default="../eval/golden_eval.jsonl")
    ap.add_argument("--csv", default="../data/sample.csv")
    ap.add_argument("--brand", default="SpotifyCares")
    ap.add_argument("--baselines-only", action="store_true",
                     help="Skip everything that needs an LLM API key")
    args = ap.parse_args()

    records = load_golden(args.golden)
    print(f"Loaded {len(records)} golden examples "
          f"({sum(r['source']=='real' for r in records)} real, "
          f"{sum(r['source']=='synthetic' for r in records)} synthetic)\n")

    run_intent_baselines(records)
    run_escalation_rule_check(records)

    if args.baselines_only:
        print("Skipping LLM system + judge (--baselines-only). Set GEMINI_API_KEY and "
              "re-run without this flag to get the headline numbers.")
    else:
        run_full_llm_system(records, args.csv, args.brand)
        run_judge_human_agreement()
