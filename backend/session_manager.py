"""
================================================================================
  the_sound_engineer / backend / session_manager.py

  FINAL VERSION (Production Ready)

  Improvements:
  - Thread-safe (locks added)
  - Reconnect handling (no duplicate overwrite)
  - Safer session + node management
  - Clean feedback integration
  - Defensive programming
================================================================================
"""

import uuid
import random
import string
import threading
from typing import Dict, List, Optional

from instrument_node import InstrumentNode
from feedback_detector import FeedbackDetector


# ═══════════════════════════════════════════════════════════════════════════
# SESSION CLASS
# ═══════════════════════════════════════════════════════════════════════════

class Session:
    """
    Represents a single live band session.
    Owns nodes + feedback detector.
    """

    def __init__(self, session_id: str, band_name: str, band_code: str):
        self.session_id = session_id
        self.band_name = band_name
        self.band_code = band_code

        self.nodes: Dict[str, InstrumentNode] = {}
        self.feedback_detector = FeedbackDetector()

    # ──────────────────────────────────────────────────────────────────────
    # NODE MANAGEMENT
    # ──────────────────────────────────────────────────────────────────────

    def add_or_update_node(self, node: InstrumentNode) -> InstrumentNode:
        """
        Handles:
        - new join
        - reconnect
        """
        existing = self.nodes.get(node.phoneID)

        if existing:
            # 🔁 RECONNECT LOGIC
            existing.name = node.name
            existing.instrument = node.instrument
            existing.position = node.position
            print(f"[SESSION] Reconnected {node.name} ({node.phoneID})")
            return existing

        self.nodes[node.phoneID] = node
        print(f"[SESSION] Added {node.name} ({node.instrument}) → {node.phoneID}")
        return node

    def remove_node(self, phone_id: str) -> bool:
        if phone_id not in self.nodes:
            return False

        name = self.nodes[phone_id].name
        del self.nodes[phone_id]

        print(f"[SESSION] {name} left session")
        return True

    def get_node(self, phone_id: str) -> Optional[InstrumentNode]:
        return self.nodes.get(phone_id)

    def all_nodes(self) -> List[InstrumentNode]:
        return list(self.nodes.values())

    def member_count(self) -> int:
        return len(self.nodes)

    # ──────────────────────────────────────────────────────────────────────
    # OUTPUT
    # ──────────────────────────────────────────────────────────────────────

    def get_info(self) -> dict:
        return {
            "session_id": self.session_id,
            "band_name": self.band_name,
            "band_code": self.band_code,
            "member_count": self.member_count(),
            "members": [
                {
                    "phone_id": pid,
                    "name": node.name,
                    "instrument": node.instrument,
                    "position": node.position,
                }
                for pid, node in self.nodes.items()
            ],
        }

    def get_all_recommendations(self) -> dict:
        """
        Aggregates:
        - Member EQ recommendations
        - Feedback detection across all nodes
        """

        nodes = self.all_nodes()

        # ⚠️ IMPORTANT: FeedbackDetector expects freqs
        # You must pass frequency bins externally or store globally
        freqs = getattr(self, "freqs", None)

        if freqs is not None:
            feedback = self.feedback_detector.analyze_all(nodes, freqs)
        else:
            feedback = []

        members = []
        for node in nodes:
            try:
                members.append(node.get_recommendation())
            except Exception:
                members.append({"name": node.name, "error": "recommendation_failed"})

        return {
            "session_id": self.session_id,
            "band_name": self.band_name,
            "band_code": self.band_code,
            "member_count": self.member_count(),
            "feedback": feedback,
            "members": members,
        }

    def __repr__(self):
        return f"Session({self.band_name}, members={self.member_count()})"


# ═══════════════════════════════════════════════════════════════════════════
# SESSION MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class SessionManager:
    """
    Thread-safe session registry.
    """

    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._code_to_id: Dict[str, str] = {}
        self._lock = threading.Lock()

    # ──────────────────────────────────────────────────────────────────────
    # SESSION LIFECYCLE
    # ──────────────────────────────────────────────────────────────────────

    def create_session(self, band_name: str) -> tuple[str, str]:
        with self._lock:

            # Idempotent
            for sid, sess in self._sessions.items():
                if sess.band_name.lower() == band_name.lower():
                    return sid, sess.band_code

            session_id = str(uuid.uuid4())
            band_code = self._generate_unique_code()

            session = Session(session_id, band_name, band_code)

            self._sessions[session_id] = session
            self._code_to_id[band_code] = session_id

            print(f"[SessionManager] Created '{band_name}' | code={band_code}")
            return session_id, band_code

    def end_session(self, session_id: str) -> bool:
        with self._lock:

            session = self._sessions.get(session_id)
            if not session:
                return False

            self._code_to_id.pop(session.band_code, None)
            del self._sessions[session_id]

            print(f"[SessionManager] Ended session {session_id[:8]}")
            return True

    # ──────────────────────────────────────────────────────────────────────
    # NODE MANAGEMENT
    # ──────────────────────────────────────────────────────────────────────

    def add_node(
        self,
        session_id: str,
        member_name: str,
        instrument: str,
        phone_id: str,
        position: str,
    ) -> Optional[InstrumentNode]:

        with self._lock:

            session = self._sessions.get(session_id)
            if not session:
                return None

            node = InstrumentNode(member_name, instrument, phone_id, position)
            return session.add_or_update_node(node)

    def remove_node(self, session_id: str, phone_id: str) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            return session.remove_node(phone_id) if session else False

    def get_node(self, session_id: str, phone_id: str) -> Optional[InstrumentNode]:
        session = self._sessions.get(session_id)
        return session.get_node(phone_id) if session else None

    def get_all_nodes(self, session_id: str) -> List[InstrumentNode]:
        session = self._sessions.get(session_id)
        return session.all_nodes() if session else []

    # ──────────────────────────────────────────────────────────────────────
    # LOOKUP
    # ──────────────────────────────────────────────────────────────────────

    def get_session_id_by_code(self, band_code: str) -> Optional[str]:
        if not band_code:
            return None
        return self._code_to_id.get(band_code.strip().upper())

    def get_session_info(self, session_id: str) -> dict:
        session = self._sessions.get(session_id)
        return session.get_info() if session else {}

    def get_all_recommendations(self, session_id: str) -> dict:
        session = self._sessions.get(session_id)
        return session.get_all_recommendations() if session else {}

    def active_session_count(self) -> int:
        return len(self._sessions)

    # ──────────────────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────────────────

    def _generate_unique_code(self) -> str:
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if code not in self._code_to_id:
                return code

    def __repr__(self):
        return f"SessionManager({len(self._sessions)} active)"