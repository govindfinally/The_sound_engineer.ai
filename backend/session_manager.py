"""
================================================================================
  the_sound_engineer / backend / session_manager.py
  Fixed version — all 6 architectural issues resolved
================================================================================
"""

import uuid
import random
import string

from instrument_node import InstrumentNode
from feedback_detector import FeedbackDetector


class SessionManager:
    def __init__(self):
        self.sessions    = {}   # session_id → session dict
        self.code_to_id  = {}   # band_code  → session_id  (Fix #1)

    # ─────────────────────────────────────────────────────────────────────────
    def create_session(self, band_name: str):
        """
        Creates a new session.
        Fix #6 — checks if a session for this band name already exists.
        Returns existing session if found, creates new one if not.
        """
        # Fix #6 — prevent duplicate sessions for same band name
        for sid, sess in self.sessions.items():
            if sess["name"].lower() == band_name.lower():
                print(f"[INFO] Session for '{band_name}' already exists — returning existing.")
                return sid, sess["band_code"]

        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Fix #5 — always uppercase band code
        band_code  = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=6
        )).upper()

        # Ensure band code is unique
        while band_code in self.code_to_id:
            band_code = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=6
            )).upper()

        self.sessions[session_id] = {
            "name":             band_name,
            "nodes":            {},
            "feedback_detector": FeedbackDetector(),
            "band_code":        band_code,
        }

        # Fix #1 — maintain reverse lookup
        self.code_to_id[band_code] = session_id

        print(f"[SESSION CREATED] '{band_name}' | code={band_code} | id={session_id[:8]}...")
        return session_id, band_code

    # ─────────────────────────────────────────────────────────────────────────
    def get_session_id_by_code(self, band_code: str):
        """
        Fix #1 + Fix #5 — lookup session_id from band_code.
        Uses the reverse lookup dict. Case-insensitive.
        Returns session_id string or None if not found.
        """
        code = band_code.strip().upper()   # Fix #5 — normalize to uppercase
        return self.code_to_id.get(code)

    # ─────────────────────────────────────────────────────────────────────────
    def add_node(self, session_id: str, member_name: str, instrument: str,
                phoneID: str, position: str):
        """
        Register a band member in a session.
        Returns the InstrumentNode or None if session not found.
        """
        if session_id not in self.sessions:
            print(f"[ERROR] Session {session_id[:8]}... not found")
            return None

        node = InstrumentNode(member_name, instrument, phoneID, position)
        self.sessions[session_id]["nodes"][phoneID] = node
        print(f"[REGISTERED] {member_name} ({instrument}) in session {session_id[:8]}...")
        return node

    # ─────────────────────────────────────────────────────────────────────────
    def get_session_info(self, session_id: str) -> dict:
        """Returns basic session info."""
        if session_id not in self.sessions:
            return {}
        session = self.sessions[session_id]
        return {
            "session_id":   session_id,
            "session_name": session["name"],
            "band_code":    session["band_code"],
            "members":      [
                {"phone_id": pid, "name": n.name, "instrument": n.instrument}
                for pid, n in session["nodes"].items()
            ]
        }

    # ─────────────────────────────────────────────────────────────────────────
    def get_node(self, session_id: str, phone_id: str):
        """Get one specific node by phone_id. Returns None if not found."""
        if session_id not in self.sessions:
            return None
        return self.sessions[session_id]["nodes"].get(phone_id)

    # ─────────────────────────────────────────────────────────────────────────
    def get_all_nodes(self, session_id: str) -> list:
        """Get all nodes in a session as a list."""
        if session_id not in self.sessions:
            return []
        return list(self.sessions[session_id]["nodes"].values())

    # ─────────────────────────────────────────────────────────────────────────
    def remove_node(self, session_id: str, phone_id: str) -> bool:
        """Remove one member from session (on disconnect)."""
        if session_id not in self.sessions:
            return False
        if phone_id not in self.sessions[session_id]["nodes"]:
            return False
        name = self.sessions[session_id]["nodes"][phone_id].name
        del self.sessions[session_id]["nodes"][phone_id]
        print(f"[REMOVED] {name} left session {session_id[:8]}...")
        return True

    # ─────────────────────────────────────────────────────────────────────────
    def end_session(self, session_id: str) -> bool:
        """
        End a session and clean up.
        Fix #4 — also removes band_code from reverse lookup to prevent ghost codes.
        """
        if session_id not in self.sessions:
            return False

        # Fix #4 — remove from reverse lookup too
        band_code = self.sessions[session_id]["band_code"]
        if band_code in self.code_to_id:
            del self.code_to_id[band_code]

        del self.sessions[session_id]
        print(f"[SESSION ENDED] {session_id[:8]}... | code {band_code} released")
        return True

    # ─────────────────────────────────────────────────────────────────────────
    def get_all_recommendations(self, session_id: str) -> dict:
        """Master dashboard output — full band status."""
        if session_id not in self.sessions:
            return {}
        session = self.sessions[session_id]
        nodes   = list(session["nodes"].values())
        
        feedback = session["feedback_detector"].get_session_summary(nodes)
        members  = [node.get_recommendation() for node in nodes]
        return {
            "session_id":   session_id,
            "band_name":    session["name"],
            "band_code":    session["band_code"],
            "member_count": len(nodes),
            "feedback":     feedback,
            "members":      members,
        }

    # ─────────────────────────────────────────────────────────────────────────
    def __repr__(self):
        return f"SessionManager — {len(self.sessions)} active sessions"


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sm = SessionManager()

    # Create session
    sid, code = sm.create_session("Jazz Night")
    print(f"\nCreated: {sid[:8]}... | Code: {code}")

    # Fix #5 test — lowercase code should still work
    found_id = sm.get_session_id_by_code(code.lower())
    print(f"Lookup by lowercase code '{code.lower()}': {'✅ Found' if found_id else '❌ Not found'}")

    # Fix #6 test — duplicate session name
    sid2, code2 = sm.create_session("Jazz Night")
    print(f"Duplicate session test: {'✅ Same ID returned' if sid == sid2 else '❌ New session created'}")

    # Register members
    sm.add_node(sid, "Alice", "electric_guitar_lead", "phone123", "left")
    sm.add_node(sid, "Bob",   "bass_guitar",          "phone456", "right")

    nodes = sm.get_all_nodes(sid)
    print(f"\nAll nodes in session: {len(nodes)},{nodes}")
    sm.get_all_recommendations(sid)  
    print(f"Members: {[n.name for n in nodes]}")

    # Fix #4 test — end session cleans up code
    sm.end_session(sid)
    ghost = sm.get_session_id_by_code(code)
    print(f"Ghost code test after end_session: {'✅ Cleaned up' if ghost is None else '❌ Ghost code exists'}")

    print(f"\nFinal state: {sm}")