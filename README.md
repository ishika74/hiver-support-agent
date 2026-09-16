# Spotify Support Agent — Hiver SDE Intern Take-Home

An AI support agent for **@SpotifyCares** that classifies intent, drafts a reply grounded
in how Spotify has historically resolved similar issues, and decides whether to
auto-handle or escalate to a human, with a stated reason.

**Read this first:** the CSV provided with this assignment is a **99-row sample** of the
full ~3M-row Kaggle "Customer Support on Twitter" dataset, not the full file. That
materially shapes what's in this repo — see the accompanying Report (Word document, submitted separately), section *"What's
misleading about my headline number"*, for the full honest accounting. Short version:
the pipeline and eval harness are built to scale to the full dataset with no code
changes, but the numbers in this repo are demo-scale, not production-scale.

## Why SpotifyCares

The sample contains message counts across 12 brands. `AppleSupport` has the most rows
(13) but almost all of them are generic "please DM us" deflections with no visible
resolution. `SpotifyCares` has fewer rows (8) but includes one complete, real,
multi-turn troubleshooting thread that actually resolves (device → app/OS version →
distance-from-speaker → fixed → thanks). That's much more useful for grounding replies
in real resolution patterns than a pile of near-identical "DM us" tweets. See
`decision_log.md` #1.

## Repo layout

```
src/
  ingest.py           # loads the CSV, reconstructs customer<->brand threads for one brand
  intents.py          # 6-intent taxonomy + two baseline classifiers (trivial, keyword)
  retrieval.py         # TF-IDF retrieval over historical resolved exchanges (grounding)
  classifier.py         # LLM intent classifier
  reply_generator.py     # LLM reply drafting, grounded in retrieved examples
  escalation.py           # deterministic, auditable auto-handle/escalate rules + reason
  pipeline.py              # orchestrates the above into one SupportAgent.handle() call
  llm_judge.py              # LLM-as-judge rubric + a small human-calibration set
  run_eval.py                # the eval harness (baselines + full system + judge agreement)
  llm_client.py                # thin Gemini API wrapper (swap models/providers here)
eval/
  build_golden_set.py   # builds golden_eval.jsonl (40 hand-labelled examples: 8 real + 32 synthetic)
  golden_eval.jsonl      # the golden set itself
  labeling_notes.md       # sampling & labeling methodology
data/
  sample.csv             # the CSV provided with the assignment
decision_log.md          # 13 non-obvious decisions and why
```

**Note:** the written report (problem framing, results, failure analysis, "what's
misleading about my headline number", next steps) is delivered as a separate Word
document, not inside this repo — see `Report.docx` alongside this zip/repo link.

## Setup (< 15 minutes)

```bash
git clone <this-repo>
cd hiver-support-agent
python3 -m pip install -r requirements.txt
export GEMINI_API_KEY=...        # free key from https://aistudio.google.com/apikey
                                  # needed for the LLM-dependent steps below
```

## Reproduce the headline results

**Step 1 — baselines (no API key needed, runs in ~2 seconds):**
```bash
cd src
python3 run_eval.py --baselines-only
```
This reproduces the two required baselines (trivial majority-class, and a transparent
keyword/regex classifier) plus a rule-logic sanity check on the escalation policy
(evaluated against gold intents, to isolate escalation-rule bugs from classifier errors).

**Step 2 — full LLM system + judge (needs `GEMINI_API_KEY`, ~2-3 minutes for 40 examples):**
```bash
python3 run_eval.py
```
This runs intent classification, retrieval-grounded reply drafting, escalation, and
LLM-judge scoring end-to-end over `eval/golden_eval.jsonl`, and additionally reports how
well the judge agrees with a small hand-scored calibration set
(`llm_judge.HUMAN_CALIBRATION_SET`). Per-example output goes to `eval/eval_results.csv`.

**Step 3 — try a single message interactively (CLI):**
```bash
python3 pipeline.py "my spotify app keeps crashing every time I open a podcast"
```

**Step 3b — or use the optional local web UI instead of the CLI:**
```bash
python3 app.py
```
Then open **http://127.0.0.1:5000** in your browser. Type a message, click "Run agent,"
and see the intent, confidence, escalation decision + reason, retrieved historical
examples, and drafted reply rendered on the page — no need to type a new command for
every message. This is a convenience addition on top of the same `SupportAgent` used by
the CLI and the eval harness; it doesn't change any pipeline logic. Requires
`GEMINI_API_KEY` to be set, same as the CLI. Press Ctrl+C in the terminal to stop the
server when done.

**Step 4 — regenerate or extend the golden set:**
```bash
cd ../eval
python3 build_golden_set.py
```
See `labeling_notes.md` for how to scale this from the current 40-example demo set to
the full 150-250 the brief asks for once you have the full Kaggle CSV.

## Models used

- **All LLM steps** (intent classification, escalation reasoning, reply drafting, judge):
  `gemini-3.6-flash`, via the **free tier of Google AI Studio** (no credit card required),
  called through Google's newer **Interactions API** (`client.interactions.create`).

Why not split fast/cheap vs. quality-sensitive across two models the way you might with
Claude Haiku/Sonnet or GPT-4o-mini/GPT-4o? As of mid-2026, Gemini 2.5 Pro is no longer
available on the free tier — only Flash and Flash-Lite are — so there's no free
"upgrade" model to reach for on the quality-sensitive steps (reply drafting, judging).
This is a real capability ceiling of the free setup, called out explicitly in
the accompanying Report (Word document, submitted separately), not a design choice made for its own sake.

Both are overridable via `HIVER_FAST_MODEL` / `HIVER_QUALITY_MODEL` env vars — e.g. set
`HIVER_QUALITY_MODEL=gemini-3.6-pro` (if/when such a tier exists on billing) if you later add
billing and want better reply/judge quality, or point `src/llm_client.py`'s `call_llm` function at a different provider
entirely (Claude, GPT-4o, a local model) — the rest of the pipeline is provider-agnostic.

### Getting a free Gemini API key

1. Go to **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)**.
2. Sign in with any Google account.
3. Click **Create API key** → choose "Create key in new project" (or an existing one).
4. Copy the key (starts with `AIza...`).
5. `export GEMINI_API_KEY=AIza...` in your terminal before running anything below.

No payment method needed. Note: on the free tier, Google's terms allow your
prompts/outputs to be used to improve their models and may be human-reviewed — fine for
this public-Twitter-data demo, but worth knowing if you ever point this pipeline at real
customer PII.

## Troubleshooting

**`ModuleNotFoundError` for pandas/google/sklearn** — you're not in the virtual
environment, or `pip install -r requirements.txt` didn't finish. Re-activate the venv
and re-run the install; verify with `pip show pandas`.

**404 error mentioning a model name / "no longer available to new users"** — Google
periodically retires specific model names and API method surfaces. `src/llm_client.py`
already has a 3-way fallback (newer Interactions API → older generate_content API →
older fallback model) for exactly this, so this should self-heal on a fresh
`pip install -U google-genai`. If it still fails, check the current model names at
[ai.google.dev](https://ai.google.dev) and set `HIVER_FAST_MODEL/HIVER_QUALITY_MODEL`
env vars to override.

**You're on Python 3.9** — this matters more than it looks. Python 3.9 reached
end-of-life in October 2025, and Google's `google-genai` SDK (along with most actively
maintained packages) has been dropping 3.9 support through 2026. If `pip install -U
google-genai` silently installs an old cached version instead of the latest, you'll get
confusing `AttributeError`s or 404s that look like a code bug but are actually a Python
version mismatch. Check your version:
```
python --version
```
If it says 3.9.x, install Python 3.11 or 3.12 from [python.org/downloads](https://python.org/downloads)
(check "Add to PATH" during install), then **delete your old `venv` folder entirely**
and recreate it with the new Python:
```
rmdir /s /q venv          (Windows)   /  rm -rf venv        (Mac/Linux)
py -3.12 -m venv venv     (Windows)   /  python3.12 -m venv venv   (Mac/Linux)
```
then reactivate and reinstall as in Setup above.

**`FileNotFoundError` for `data/sample.csv`** — make sure you're running scripts from
either the project root (`python src/pipeline.py ...`) or from inside `src/`
(`python pipeline.py ...`, `python run_eval.py ...`) — both work, since paths are
resolved relative to each script's own file location, not the current directory.

## What "good" means here

See the accompanying Report (Word document, submitted separately) for the full problem framing, but briefly: a reply is "good" if
it (a) matches how Spotify actually resolves this kind of issue rather than inventing
generic advice, (b) never makes an account/billing change or promise the AI can't
actually keep, and (c) is honest with the customer about what happens next. Escalation
is deliberately biased toward over-escalating account/billing/reputational-risk cases —
for a real brand account, a wrong auto-reply is much more expensive than an unnecessary
human touch.
