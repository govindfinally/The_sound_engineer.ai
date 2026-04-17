"""
================================================================================
  the_sound_engineer / backend / instrument_node.py

  InstrumentNode — Represents a performer/device in LiveMix AI

  Features:
  - Real-time audio level tracking
  - Status classification (idle / active / warning / critical)
  - Feedback integration (multi-band support)
  - Adaptive EQ based on instrument profile
  - AI-agent hook for advanced mixing recommendations
  - Safe handling of missing or partial data

================================================================================
"""

from typing import Optional, Dict, Any, List
from instrument_profile import get_profile


class InstrumentNode:
    """
    Represents a single audio source (musician/device).

    Handles:
    - Audio level updates
    - Feedback data integration
    - EQ recommendation generation
    """

    def __init__(self, name: str, instrument: str, phoneID: str, position: str):
        self.name: str = name
        self.instrument: str = instrument
        self.phoneID: str = phoneID
        self.position: str = position

        # Audio state
        self.current_db: float = -60.0
        self.status: str = "idle"  # idle, active, warning, critical

        # Feedback state
        self.feedback_data: Optional[Dict[str, Any]] = None

        # FFT history (required by FeedbackDetector)
        self.fft_history: List = []

    # -------------------------------------------------------------------------
    # AUDIO LEVEL HANDLING
    # -------------------------------------------------------------------------
    def update_audio_level(self, db_level: float) -> None:
        """
        Update current audio level and assign status.

        Thresholds:
            critical : > -10 dB
            warning  : -20 to -10 dB
            active   : -50 to -20 dB
            idle     : < -50 dB
        """
        self.current_db = db_level

        if db_level > -10:
            self.status = "critical"
        elif db_level > -20:
            self.status = "warning"
        elif db_level > -50:
            self.status = "active"
        else:
            self.status = "idle"

    # -------------------------------------------------------------------------
    # FFT HANDLING
    # -------------------------------------------------------------------------
    def update_frame(self, fft_data, freqs=None, db_level: float = None) -> None:
        """
        Store FFT frame for feedback detection.

        Args:
            fft_data: FFT magnitude array (should be in dB scale)
            freqs: optional (not stored, but useful upstream)
            db_level: optional dB update
        """
        self.fft_history.append(fft_data)

        # Optional: keep memory bounded (important for real-time systems)
        if len(self.fft_history) > 20:
            self.fft_history.pop(0)

        if db_level is not None:
            self.update_audio_level(db_level)

    # -------------------------------------------------------------------------
    # FEEDBACK HANDLING
    # -------------------------------------------------------------------------
    def receive_feedback(self, feedback_dict: Dict[str, Any]) -> None:
        """
        Store feedback detection output from FeedbackDetector.

        Expected format:
        {
            'risk': bool,
            'freqs_hz': [float, ...],
            'growth_rates': [float, ...],
            'severity': 'warning' | 'critical',
            'confidence': float
        }
        """
        self.feedback_data = feedback_dict

    # -------------------------------------------------------------------------
    # RECOMMENDATION ENGINE
    # -------------------------------------------------------------------------
    def get_recommendation(self) -> Dict[str, Any]:
        """
        Generate structured recommendation for dashboard.

        Returns:
            dict containing:
            - node metadata
            - audio status
            - feedback data
            - EQ recommendation
        """

        profile = get_profile(self.instrument)
        feedback = self.feedback_data or {}

        has_feedback = feedback.get("risk", False)
        freqs = feedback.get("freqs_hz", [])
        confidence = feedback.get("confidence", 0.0)
        severity = feedback.get("severity", "none")

        recommendation = {
            "member_name": self.name,
            "instrument": self.instrument,
            "phone_id": self.phoneID,
            "position": self.position,
            "current_db": round(self.current_db, 2),
            "status": self.status,

            "has_feedback": has_feedback,
            "feedback_freqs": freqs,
            "confidence": confidence,
            "severity": severity,
        }

        # ---- ADAPTIVE EQ ----
        q = profile.get("feedback_q", 4.0)
        cut = profile.get("cut_db", -12.0)

        if has_feedback and freqs:
            eq_bands = []

            for f in freqs:
                eq_bands.append({
                    "type": "notch",
                    "freq_hz": int(f),
                    "q": q,
                    "gain_db": cut
                })

            recommendation["eq_recommendation"] = {
                "type": "multi_notch",
                "bands": eq_bands,
                "reason": f"{len(freqs)} feedback frequencies detected ({severity})"
            }

        else:
            recommendation["eq_recommendation"] = {
                "type": "none",
                "reason": "No feedback detected"
            }

        return recommendation

    # -------------------------------------------------------------------------
    # AI AGENT INTEGRATION (OPTIONAL)
    # -------------------------------------------------------------------------
    def apply_ai_agent(self, recommendation: Dict[str, Any], ai_agent=None) -> Dict[str, Any]:
        """
        Enhance recommendation using AI agent (optional layer).

        Args:
            recommendation: base rule-based output
            ai_agent: model or API with .predict()

        Returns:
            enriched recommendation
        """

        if ai_agent is None:
            return recommendation

        try:
            ai_output = ai_agent.predict(recommendation)
            recommendation["ai_adjustments"] = ai_output
        except Exception:
            recommendation["ai_adjustments"] = "fallback_used"

        return recommendation

    # -------------------------------------------------------------------------
    # DEBUG / LOGGING
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        return (
            f"InstrumentNode("
            f"name={self.name}, instrument={self.instrument}, "
            f"phoneID={self.phoneID}, position={self.position}, "
            f"current_db={self.current_db} dB, status={self.status})"
        )