"""
================================================================================
  the_sound_engineer / backend / rag / rag_advisor.py

  Phase 3 — RAG memory layer (orchestration)

  This is the only file the rest of the app needs to import. It wraps
  retriever.py + session_logger.py behind a simple interface:

      advisor = RAGAdvisor()
      advisor.log_completed_session(...)          # write
      advisor.suggest_for_new_session([...])       # read

  Kept template-based on purpose (no LLM call) — this is the "basic"
  version. Later you can take the retrieved context this returns and
  feed it into an LLM prompt for a natural-language explanation instead
  of the template string.
================================================================================
"""

from typing import List, Dict

from .session_logger import log_session
from .retriever import SessionRetriever


class RAGAdvisor:
    def __init__(self):
        self.retriever = SessionRetriever()

    # ── WRITE SIDE ──────────────────────────────────────────────────────
    def log_completed_session(
        self,
        session_id: str,
        band_name: str,
        members: List[Dict],
        feedback_events: List[Dict] = None,
        fixes_applied: List[str] = None,
    ):
        log_session(session_id, band_name, members, feedback_events, fixes_applied)
        self.retriever.refresh()  # keep index in sync with the new record

    # ── READ SIDE ───────────────────────────────────────────────────────
    def suggest_for_new_session(self, instrument_list: List[str], top_k: int = 3) -> Dict:
        """
        Call this right after a new session's members have joined
        (e.g. once instrument registration is done, before the first
        recommendation is sent out).

        Returns:
            {
              "matches_found": int,
              "suggestions": [
                  {
                    "band_name": str,
                    "similarity": float,   # 0..1
                    "known_clashes": [...],
                    "fixes_that_worked": [...],
                  },
                  ...
              ]
            }
        """
        query_text = f"instruments: {' '.join(instrument_list)}"
        results = self.retriever.search(query_text, top_k=top_k)

        suggestions = []
        for record, score in results:
            suggestions.append({
                "band_name": record["band_name"],
                "similarity": round(score, 3),
                "known_clashes": [
                    fe.get("description", str(fe))
                    for fe in record.get("feedback_events", [])
                ],
                "fixes_that_worked": record.get("fixes_applied", []),
            })

        return {
            "matches_found": len(suggestions),
            "suggestions": suggestions,
        }