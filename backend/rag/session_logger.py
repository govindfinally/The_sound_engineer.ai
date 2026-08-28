"""
================================================================================
  the_sound_engineer / backend / rag / session_logger.py

  Phase 3 — RAG memory layer (write side)

  Every time a session ends, we write a compact text summary of what
  happened — band composition, clashes detected, fixes given — into a
  JSONL corpus. retriever.py reads this corpus back for similarity search.

  Kept intentionally basic: no DB, just an append-only .jsonl file.
================================================================================
"""

import json
import os
import time
from typing import List, Dict, Optional

CORPUS_PATH = os.path.join(os.path.dirname(__file__), "data", "session_history.jsonl")


def _ensure_corpus_exists():
    os.makedirs(os.path.dirname(CORPUS_PATH), exist_ok=True)
    if not os.path.exists(CORPUS_PATH):
        open(CORPUS_PATH, "w").close()


def log_session(
    session_id: str,
    band_name: str,
    members: List[Dict],
    feedback_events: Optional[List[Dict]] = None,
    fixes_applied: Optional[List[str]] = None,
):
    """
    Call this from SessionManager.end_session() (or wherever a session
    is torn down) to persist a record for future retrieval.

    Args:
        session_id       : the session's UUID
        band_name        : e.g. "Midnight Static"
        members           : list of dicts like
                            {"name": "Rohan", "instrument": "electric_guitar_lead"}
                            (this is exactly what Session.get_info()["members"] gives you)
        feedback_events   : optional list of feedback/clash dicts already
                            produced by FeedbackDetector / ClashDetector
        fixes_applied     : optional list of human-readable fix strings,
                            e.g. ["Rohan (Guitar) — cut 2.4kHz -3dB Q=1.8"]
    """
    _ensure_corpus_exists()

    instruments = sorted(set(m["instrument"] for m in members))

    # Build one flat searchable text blob — this is what gets embedded/matched.
    # Keep it human-readable; it doubles as the "explanation" text later.
    text_parts = [
        f"band:{band_name}",
        f"instruments:{' '.join(instruments)}",
    ]
    if feedback_events:
        clash_desc = "; ".join(
            fe.get("description", str(fe)) for fe in feedback_events
        )
        text_parts.append(f"clashes:{clash_desc}")
    if fixes_applied:
        text_parts.append(f"fixes:{'; '.join(fixes_applied)}")

    record = {
        "session_id": session_id,
        "band_name": band_name,
        "timestamp": time.time(),
        "instruments": instruments,
        "member_count": len(members),
        "feedback_events": feedback_events or [],
        "fixes_applied": fixes_applied or [],
        "text": " | ".join(text_parts),
    }

    with open(CORPUS_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")


def load_all_sessions() -> List[Dict]:
    """Reads the full corpus back into memory. Fine at this scale (jsonl, append-only)."""
    _ensure_corpus_exists()
    records = []
    with open(CORPUS_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records