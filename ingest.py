"""
ingest.py
Loads the raw "Customer Support on Twitter" CSV and reconstructs
customer <-> brand conversation threads for a single brand.

The raw schema (Kaggle thoughtvector/customer-support-on-twitter):
    tweet_id, author_id, inbound, created_at, text,
    response_tweet_id, in_response_to_tweet_id

`inbound=True`  -> written by a customer (author_id is a numeric-ish anon id)
`inbound=False` -> written by a brand account (author_id is the brand handle, e.g. "SpotifyCares")

We do NOT assume the full 3M-row file. This works on any subsample with the
same schema, including the tiny sample.csv shipped in this repo.
"""
from __future__ import annotations

import re
import pandas as pd
from dataclasses import dataclass, field


@dataclass
class Exchange:
    """One (customer message -> brand reply) resolved pair, with a bit of thread context."""
    thread_root_id: int
    customer_tweet_id: int
    customer_text: str
    brand_tweet_id: int
    brand_text: str
    brand: str
    # prior turns in the same thread before this exchange (oldest first), for context
    prior_turns: list = field(default_factory=list)


URL_RE = re.compile(r"https?://\S+")
HANDLE_RE = re.compile(r"@\w+")


def clean_text(text: str) -> str:
    """Light normalization used everywhere downstream (kept minimal on purpose --
    we want the model to see real noisy tweet text, just without dangling URLs)."""
    if not isinstance(text, str):
        return ""
    text = URL_RE.sub("", text).strip()
    return text


def load_raw(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, dtype={"author_id": str})
    df["tweet_id"] = df["tweet_id"].astype(int)
    df["inbound"] = df["inbound"].astype(bool)
    # in_response_to_tweet_id / response_tweet_id come in as float/NaN or comma-lists in the
    # full dataset (a tweet can have multiple responses). We only need the single parent id.
    df["in_response_to_tweet_id"] = pd.to_numeric(
        df["in_response_to_tweet_id"], errors="coerce"
    )
    return df


def build_exchanges_for_brand(df: pd.DataFrame, brand: str, max_context_turns: int = 4):
    """
    Find every brand reply to `brand`, walk back to the customer message it replied to,
    and walk further back to collect prior context turns in the same thread.

    Returns a list[Exchange].
    """
    by_id = {int(r.tweet_id): r for r in df.itertuples()}
    exchanges = []

    brand_replies = df[(df["inbound"] == False) & (df["author_id"] == brand)]

    for r in brand_replies.itertuples():
        if pd.isna(r.in_response_to_tweet_id):
            continue
        parent_id = int(r.in_response_to_tweet_id)
        parent = by_id.get(parent_id)
        if parent is None or not parent.inbound:
            continue  # brand replying to itself / to another brand / orphaned id -> skip

        # walk backwards to build prior context (best-effort; sample data is sparse so
        # most threads will simply have 0 prior turns)
        prior = []
        cursor = parent
        hops = 0
        while hops < max_context_turns:
            if pd.isna(cursor.in_response_to_tweet_id):
                break
            gp_id = int(cursor.in_response_to_tweet_id)
            gp = by_id.get(gp_id)
            if gp is None:
                break
            speaker = "brand" if not gp.inbound else "customer"
            prior.insert(0, (speaker, clean_text(gp.text)))
            cursor = gp
            hops += 1

        exchanges.append(
            Exchange(
                thread_root_id=prior[0][1] if False else parent_id,  # kept simple
                customer_tweet_id=parent_id,
                customer_text=clean_text(parent.text),
                brand_tweet_id=int(r.tweet_id),
                brand_text=clean_text(r.text),
                brand=brand,
                prior_turns=prior,
            )
        )

    return exchanges


if __name__ == "__main__":
    import sys
    import collections

    path = sys.argv[1] if len(sys.argv) > 1 else "data/sample.csv"
    df = load_raw(path)
    outbound_counts = df[df["inbound"] == False]["author_id"].value_counts()
    print("Brands present (outbound message counts):")
    print(outbound_counts)

    brand = sys.argv[2] if len(sys.argv) > 2 else "SpotifyCares"
    exchanges = build_exchanges_for_brand(df, brand)
    print(f"\nResolved exchanges for {brand}: {len(exchanges)}")
    for ex in exchanges:
        print("-" * 60)
        print("CUSTOMER:", ex.customer_text)
        print("BRAND:   ", ex.brand_text)
