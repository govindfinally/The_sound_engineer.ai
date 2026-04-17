"""
================================================================================
  the_sound_engineer / backend / feedback_detector.py

  FeedbackDetector — Detects acoustic feedback using FFT growth tracking

  Features:
  - Multi-band feedback detection
  - Growth-rate based early warning (~200ms before feedback)
  - Confidence scoring
  - Severity classification (warning / critical)
  - Cross-node analysis support

================================================================================
"""

import numpy as np
from typing import List, Dict, Any


class FeedbackDetector:
    """
    Detects acoustic feedback by tracking frequency growth over time.

    Works on FFT magnitude history stored inside each InstrumentNode.
    """

    def __init__(
        self,
        threshold_db_per_frame: float = 1.5,
        window_frames: int = 3,
        max_bands: int = 3
    ):
        """
        Args:
            threshold_db_per_frame: Minimum growth rate to consider feedback
            window_frames: Number of frames to compare (temporal window)
            max_bands: Max number of feedback frequencies to detect
        """
        self.threshold = threshold_db_per_frame
        self.window = window_frames
        self.max_bands = max_bands

    # -------------------------------------------------------------------------
    # CORE DETECTION
    # -------------------------------------------------------------------------
    def analyze(self, node, freqs) -> Dict[str, Any]:
        """
        Analyze a single node for feedback risk.

        Args:
            node: InstrumentNode (must contain fft_history)
            freqs: Frequency array corresponding to FFT bins

        Returns:
            dict containing:
                - risk (bool)
                - freqs_hz (list)
                - growth_rates (list)
                - severity (str)
                - confidence (float)
        """

        # ---- SAFETY CHECK ----
        if not hasattr(node, "fft_history") or len(node.fft_history) < self.window:
            return {
                "risk": False,
                "member": getattr(node, "name", "unknown"),
                "message": "Not enough FFT data"
            }

        latest = node.fft_history[-1]
        older = node.fft_history[-self.window]

        # ---- GROWTH COMPUTATION ----
        growth = (latest - older) / self.window

        # ---- MULTI-BAND DETECTION ----
        indices = np.where(growth > self.threshold)[0]

        if len(indices) == 0:
            return {
                "risk": False,
                "member": node.name,
                "growth_rate": float(np.max(growth))
            }

        # Sort indices by growth rate
        sorted_indices = indices[np.argsort(growth[indices])]

        # Select top N dangerous frequencies
        top_indices = sorted_indices[-self.max_bands:]

        freqs_detected = [round(float(freqs[i]), 1) for i in top_indices]
        growth_rates = [float(growth[i]) for i in top_indices]

        max_rate = max(growth_rates)

        # ---- CONFIDENCE SCORING ----
        confidence = min(max_rate / 3.0, 1.0)

        # ---- SEVERITY CLASSIFICATION ----
        severity = "critical" if max_rate > 2.5 else "warning"

        return {
            "risk": True,
            "member": node.name,
            "instrument": getattr(node, "instrument", "unknown"),
            "freqs_hz": freqs_detected,
            "growth_rates": [round(g, 2) for g in growth_rates],
            "max_growth_rate": round(max_rate, 2),
            "severity": severity,
            "confidence": round(confidence, 2),
            "message": (
                f"{node.name} — Feedback risk at {freqs_detected} Hz "
                f"(max growth: {round(max_rate,2)} dB/frame)"
            )
        }

    # -------------------------------------------------------------------------
    # MULTI-NODE ANALYSIS
    # -------------------------------------------------------------------------
    def analyze_all(self, nodes: List, freqs) -> List[Dict[str, Any]]:
        """
        Analyze all nodes and return sorted alerts.

        Sorted by highest growth rate (most dangerous first).
        """

        alerts = []

        for node in nodes:
            result = self.analyze(node, freqs)

            if result.get("risk"):
                alerts.append(result)

        # Sort by max growth rate descending
        alerts.sort(key=lambda x: x["max_growth_rate"], reverse=True)

        return alerts

    # -------------------------------------------------------------------------
    # ACTION SUGGESTION
    # -------------------------------------------------------------------------
    def suggest_notch(self, freq_hz: float) -> Dict[str, Any]:
        """
        Suggest notch filter parameters for a given frequency.
        """

        return {
            "type": "notch",
            "freq_hz": float(freq_hz),
            "cut_db": -12.0,
            "q": 4.0,
            "message": f"Apply notch filter at {freq_hz} Hz (−12 dB, Q=4.0)"
        }