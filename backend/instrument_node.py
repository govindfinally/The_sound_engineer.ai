"""
================================================================================
  the_sound_engineer / backend / instrument_node.py (FIXED)
  Handles missing feedback keys gracefully
================================================================================
"""

import json
from instrument_profile import get_profile


class InstrumentNode:
    def __init__(self, name: str, instrument: str, phoneID: str, position: str):
        self.name       = name
        self.instrument = instrument
        self.phoneID    = phoneID
        self.position   = position
        self.current_db = -60.0
        self.status     = "idle"  # idle, active, warning, critical
        self.feedback_data = None

    def update_audio_level(self, db_level: float):
        """Update the current dB reading."""
        self.current_db = db_level
        if db_level > -10:
            self.status = "critical"
        elif db_level > -20:
            self.status = "warning"
        elif db_level > -50:
            self.status = "active"
        else:
            self.status = "idle"

    def receive_feedback(self, feedback_dict: dict):
        """Store feedback data from feedback_detector."""
        self.feedback_data = feedback_dict

    def get_recommendation(self) -> dict:
        """
        Return quantitative EQ recommendation for this member.
        Handles missing feedback keys with sensible defaults.
        """
        profile = get_instrument_profile(self.instrument)
        
        # Safely extract feedback data with defaults
        feedback = self.feedback_data or {}
        has_feedback = feedback.get("has_feedback", False)
        feedback_freq = feedback.get("freq_hz", None)
        confidence = feedback.get("confidence", 0.0)

        # Base recommendation structure
        rec = {
            "member_name":   self.name,
            "instrument":    self.instrument,
            "phone_id":      self.phoneID,
            "position":      self.position,
            "current_db":    round(self.current_db, 2),
            "status":        self.status,
            "profile":       profile,
            "has_feedback":  has_feedback,
            "feedback_freq": feedback_freq,
            "confidence":    confidence,
        }

        # If feedback detected, add EQ recommendation
        if has_feedback and feedback_freq:
            rec["eq_recommendation"] = {
                "type": "notch",
                "center_freq_hz": int(feedback_freq),
                "bandwidth_q": 10.0,
                "gain_db": -12.0,
                "reason": f"Feedback detected at {int(feedback_freq)} Hz. Apply tight notch filter."
            }
        else:
            rec["eq_recommendation"] = {
                "type": "none",
                "reason": "No feedback detected. Maintain current settings."
            }

        return rec

    def __repr__(self):
        return (
            f"InstrumentNode(name={self.name}, instrument={self.instrument}, "
            f"phoneID={self.phoneID}, position={self.position}, "
            f"current_db={self.current_db} dB, status={self.status})"
        )