"""
retrieval.py

Grounds reply drafting in "how this brand has historically resolved similar issues"
by retrieving the k most similar past customer messages (from build_exchanges_for_brand)
and handing their real brand replies to the reply generator as few-shot evidence.

Uses TF-IDF + cosine similarity (scikit-learn) rather than a hosted embeddings API:
    - fully offline / free / deterministic
    - fine at this scale (hundreds-thousands of exchanges per brand)
    - swap for a real embedding model if/when the knowledge base grows large
      (see decision_log.md #9)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ingest import Exchange


@dataclass
class RetrievalHit:
    exchange: Exchange
    score: float


class ExchangeRetriever:
    def __init__(self, exchanges: List[Exchange]):
        self.exchanges = exchanges
        self.vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
        corpus = [ex.customer_text for ex in exchanges] or [""]
        self.matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(self, query_text: str, k: int = 3) -> List[RetrievalHit]:
        if not self.exchanges:
            return []
        q_vec = self.vectorizer.transform([query_text])
        sims = cosine_similarity(q_vec, self.matrix)[0]
        ranked = sorted(
            zip(self.exchanges, sims), key=lambda x: x[1], reverse=True
        )
        return [RetrievalHit(ex, float(s)) for ex, s in ranked[:k] if s > 0]
