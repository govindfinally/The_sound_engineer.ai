"""
================================================================================
  the_sound_engineer / backend / rag / retriever.py

  Phase 3 — RAG memory layer (read side)

  Basic TF-IDF + cosine similarity, built on plain numpy — no sklearn,
  no FAISS, no embedding API calls. Good enough for a few hundred/
  thousand past sessions. Swap this class out for a real vector store
  later without touching rag_advisor.py's interface.
================================================================================
"""

import math
from collections import Counter
from typing import List, Dict, Tuple

import numpy as np

from .session_logger import load_all_sessions


def _tokenize(text: str) -> List[str]:
    return [t for t in text.lower().replace("|", " ").replace(":", " ").split() if t]


class SessionRetriever:
    """
    Builds a TF-IDF matrix over all logged session texts and lets you
    query it with a new (unlogged) text — e.g. "instruments: bass_guitar
    electric_guitar_lead tabla" for a session that's about to start.
    """

    def __init__(self):
        self.records: List[Dict] = []
        self.vocab: Dict[str, int] = {}
        self.idf: np.ndarray = np.array([])
        self.doc_vectors: np.ndarray = np.array([])
        self._build_index()

    def _build_index(self):
        self.records = load_all_sessions()
        if not self.records:
            return

        tokenized_docs = [_tokenize(r["text"]) for r in self.records]

        # vocab
        vocab_set = sorted(set(tok for doc in tokenized_docs for tok in doc))
        self.vocab = {tok: i for i, tok in enumerate(vocab_set)}
        n_docs = len(tokenized_docs)
        n_vocab = len(vocab_set)

        # term frequency matrix
        tf = np.zeros((n_docs, n_vocab), dtype=np.float32)
        for i, doc in enumerate(tokenized_docs):
            counts = Counter(doc)
            for tok, c in counts.items():
                tf[i, self.vocab[tok]] = c / len(doc)

        # inverse document frequency
        df = (tf > 0).sum(axis=0)
        self.idf = np.log((1 + n_docs) / (1 + df)) + 1  # smoothed idf

        self.doc_vectors = tf * self.idf  # broadcast

    def refresh(self):
        """Call after new sessions are logged so the index picks them up."""
        self._build_index()

    def _vectorize_query(self, text: str) -> np.ndarray:
        tokens = _tokenize(text)
        vec = np.zeros(len(self.vocab), dtype=np.float32)
        counts = Counter(tokens)
        for tok, c in counts.items():
            idx = self.vocab.get(tok)
            if idx is not None:
                vec[idx] = (c / len(tokens)) * self.idf[idx]
        return vec

    def search(self, query_text: str, top_k: int = 3) -> List[Tuple[Dict, float]]:
        """
        Returns up to top_k (session_record, similarity_score) pairs,
        sorted by descending similarity. Empty list if corpus is empty
        or nothing matches.
        """
        if len(self.records) == 0 or self.doc_vectors.size == 0:
            return []

        q_vec = self._vectorize_query(query_text)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []

        doc_norms = np.linalg.norm(self.doc_vectors, axis=1)
        doc_norms[doc_norms == 0] = 1e-9  # avoid div by zero

        sims = (self.doc_vectors @ q_vec) / (doc_norms * q_norm)

        ranked_idx = np.argsort(-sims)[:top_k]
        results = [
            (self.records[i], float(sims[i])) for i in ranked_idx if sims[i] > 0
        ]
        return results