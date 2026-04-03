"""
================================================================================
  the_sound_engineer / backend / feedback_detector.py

  Detects acoustic feedback / howling BEFORE it becomes audible.

  Science basis:
  - Springer 2025: Acoustic Feedback Detection via Notch Filters
  - DIVA Portal: Multi-criteria howling detection (peak-to-neighbor ratio
    + frame-based growth tracking)
  - Threshold: 1.5 dB/frame growth rate → ~200ms warning before audible howl

  How it works:
  - Every 93ms a new FFT frame arrives per node
  - We track how fast each frequency bin's magnitude is growing
  - If any bin grows > 1.5 dB/frame for 3 consecutive frames → alert
  - We then recommend an exact notch filter (freq_hz, cut_db, Q)
================================================================================
"""

import numpy as np
from typing import List, Optional


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

GROWTH_THRESHOLD_WARNING  = 1.5   # dB/frame — from Springer 2025 paper
GROWTH_THRESHOLD_CRITICAL = 2.5   # dB/frame — imminent screech
NOTCH_CUT_DB              = -12.0 # standard feedback notch depth
NOTCH_Q                   = 4.0   # narrow Q for notch filter


# ══════════════════════════════════════════════════════════════════════════════
# CLASS — FeedbackDetector
# ══════════════════════════════════════════════════════════════════════════════

class FeedbackDetector:
    """
    Monitors all active InstrumentNodes for pre-howl conditions.
    One instance shared across the entire session.
    """

    def __init__(self, threshold: float = GROWTH_THRESHOLD_WARNING,
                window_frames: int = 3):
        """
        Args:
            threshold:     dB/frame growth rate that triggers a warning alert.
                        From Springer 2025: 1.5 dB/frame gives ~200ms warning.
            window_frames: How many frames to compare for growth calculation.
                        3 frames × 93ms = 280ms lookback window.
        """
        self.threshold     = threshold
        self.window_frames = window_frames


    # ─────────────────────────────────────────────────────────────────────────
    def analyze(self, node) -> dict:
        """
        Analyze one InstrumentNode for feedback risk.

        Looks at node.fft_history — compares latest frame to
        window_frames ago. Calculates growth rate per FFT bin.

        Formula (from Springer 2025):
            growth[k] = (latest_frame[k] - older_frame[k]) / window_frames
            where k = FFT bin index

        Args:
            node: InstrumentNode instance with fft_history populated

        Returns:
            dict with keys:
                risk        → bool
                severity    → "none" | "warning" | "critical"
                freq_hz     → float — which frequency is growing
                growth_rate → float — dB/frame
                member      → str — who to alert
                instrument  → str
                message     → str — human readable alert
        """
        # Need at least window_frames + 1 frames to compare
        if len(node.fft_history) < self.window_frames + 1:
            return {
                "risk":        False,
                "severity":    "none",
                "freq_hz":     0.0,
                "growth_rate": 0.0,
                "member":      node.name,
                "instrument":  node.instrument,
                "message":     "Not enough frames yet",
            }

        # ── Get frames to compare ─────────────────────────────────────────
        latest_frame = np.array(node.fft_history[-1])
        older_frame  = np.array(node.fft_history[-(self.window_frames + 1)])

        # ── Calculate growth rate per bin (dB/frame) ──────────────────────
        # Convert to dB first for meaningful growth measurement
        latest_db = 20 * np.log10(latest_frame + 1e-9)
        older_db  = 20 * np.log10(older_frame  + 1e-9)
        growth    = (latest_db - older_db) / self.window_frames

        # ── Find the bin with maximum growth ─────────────────────────────
        max_growth_idx  = int(np.argmax(growth))
        max_growth_rate = float(growth[max_growth_idx])

        # ── Map bin index to Hz ───────────────────────────────────────────
        # Reconstruct freq for that bin using standard formula
        # freq[k] = k × (sample_rate / N)
        # We estimate N from fft_history length: N = (len(frame) - 1) × 2
        N           = (len(latest_frame) - 1) * 2
        sample_rate = 44100
        freq_hz     = float(max_growth_idx * (sample_rate / N))

        # ── Determine severity ────────────────────────────────────────────
        if max_growth_rate >= GROWTH_THRESHOLD_CRITICAL:
            severity = "critical"
            risk     = True
        elif max_growth_rate >= self.threshold:
            severity = "warning"
            risk     = True
        else:
            severity = "none"
            risk     = False

        # ── Build message ─────────────────────────────────────────────────
        if risk:
            emoji   = "🔴" if severity == "critical" else "⚠️"
            message = (
                f"{emoji} {node.name} ({node.instrument.replace('_', ' ').title()}) "
                f"— Feedback risk at {round(freq_hz, 1)} Hz! "
                f"Growth: {round(max_growth_rate, 2)} dB/frame "
                f"[{severity.upper()}]"
            )
        else:
            message = f"{node.name} ({node.instrument}) — No feedback risk"

        return {
            "risk":        risk,
            "severity":    severity,
            "freq_hz":     round(freq_hz, 1),
            "growth_rate": round(max_growth_rate, 2),
            "member":      node.name,
            "instrument":  node.instrument,
            "message":     message,
        }


    # ─────────────────────────────────────────────────────────────────────────
    def analyze_all(self, nodes: list) -> list:
        """
        Run analyze() across ALL active nodes in the session.
        Returns only the alerts (risk=True), sorted by severity.

        Args:
            nodes: list of InstrumentNode instances

        Returns:
            list of alert dicts, critical first then warnings
            Empty list if no feedback risk detected anywhere
        """
        alerts = []

        for node in nodes:
            result = self.analyze(node)
            if result["risk"]:
                alerts.append(result)

        # Sort: critical first, then warning, then by growth_rate descending
        alerts.sort(
            key=lambda x: (
                0 if x["severity"] == "critical" else 1,
                -x["growth_rate"]
            )
        )

        return alerts


    # ─────────────────────────────────────────────────────────────────────────
    def suggest_notch(self, freq_hz: float) -> dict:
        """
        Given a feedback frequency, return the exact notch filter to apply.

        Standard feedback notch from AES:
        - Cut depth: -12 dB (enough to break the loop without killing the tone)
        - Q: 4.0 (narrow — only targets the exact feedback frequency)

        Args:
            freq_hz: The feedback frequency detected by analyze()

        Returns:
            dict with exact EQ settings to apply immediately
        """
        return {
            "type":       "notch",
            "freq_hz":    round(freq_hz, 1),
            "cut_db":     NOTCH_CUT_DB,
            "q":          NOTCH_Q,
            "message":    (
                f"Apply notch filter at {round(freq_hz, 1)} Hz — "
                f"Cut {abs(NOTCH_CUT_DB)} dB, Q={NOTCH_Q}"
            )
        }


    # ─────────────────────────────────────────────────────────────────────────
    def get_session_summary(self, nodes: list) -> dict:
        """
        Full feedback summary for the master phone dashboard.
        Runs analyze_all() and builds a clean summary.

        Returns:
            dict with:
                any_risk      → bool — is ANY node at risk right now?
                total_alerts  → int
                critical_count→ int
                warning_count → int
                alerts        → list of alert dicts
                notch_filters → list of suggested notch filters
        """
        alerts        = self.analyze_all(nodes)
        critical      = [a for a in alerts if a["severity"] == "critical"]
        warnings      = [a for a in alerts if a["severity"] == "warning"]
        notch_filters = [self.suggest_notch(a["freq_hz"]) for a in alerts]

        return {
            "any_risk":       len(alerts) > 0,
            "total_alerts":   len(alerts),
            "critical_count": len(critical),
            "warning_count":  len(warnings),
            "alerts":         alerts,
            "notch_filters":  notch_filters,
        }


    # ─────────────────────────────────────────────────────────────────────────
    def __repr__(self):
        return (f"FeedbackDetector("
                f"threshold={self.threshold} dB/frame, "
                f"window={self.window_frames} frames)")


# ══════════════════════════════════════════════════════════════════════════════
# QUICK TEST
# Run: python feedback_detector.py
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))

    from instrument_node import InstrumentNode
    import numpy as np

    print("=" * 60)
    print("  FeedbackDetector — Test")
    print("=" * 60)

    # ── Setup ─────────────────────────────────────────────────
    detector    = FeedbackDetector()
    sample_rate = 44100
    N           = 4096
    freqs       = np.fft.rfftfreq(N, d=1.0/sample_rate)

    # Create two nodes
    node_ravi  = InstrumentNode("Ravi",  "bass_guitar",        "ws_1", "stage_left")
    node_sneha = InstrumentNode("Sneha", "electric_guitar_lead","ws_2", "stage_right")

    print(f"\nDetector: {detector}")
    print(f"\nSimulating 6 audio frames...")
    print(f"Ravi   — normal signal throughout")
    print(f"Sneha  — feedback building at 2,800 Hz from frame 4\n")

    for i in range(6):
        # Ravi — normal flat signal, no growth
        ravi_fft = np.random.uniform(0.0001, 0.001, len(freqs))
        node_ravi.update_frame(ravi_fft, freqs, -20.0)

        # Sneha — feedback growing at 2800 Hz after frame 3
        sneha_fft = np.random.uniform(0.0001, 0.001, len(freqs))
        feedback_bin = np.argmin(np.abs(freqs - 2800))
        if i >= 3:
            # Simulate exponential growth at 2800 Hz
            sneha_fft[feedback_bin] = 0.01 * (3 ** (i - 2))
        node_sneha.update_frame(sneha_fft, freqs, -18.0)

        print(f"  Frame {i+1} — Sneha @ 2800 Hz magnitude: {sneha_fft[feedback_bin]:.4f}")

    # ── Run analysis ──────────────────────────────────────────
    print("\n--- analyze(Ravi) ---")
    ravi_result = detector.analyze(node_ravi)
    print(f"  Risk: {ravi_result['risk']} | {ravi_result['message']}")

    print("\n--- analyze(Sneha) ---")
    sneha_result = detector.analyze(node_sneha)
    print(f"  Risk: {sneha_result['risk']}")
    print(f"  Severity: {sneha_result['severity']}")
    print(f"  Freq: {sneha_result['freq_hz']} Hz")
    print(f"  Growth: {sneha_result['growth_rate']} dB/frame")
    print(f"  Message: {sneha_result['message']}")

    print("\n--- suggest_notch ---")
    if sneha_result["risk"]:
        notch = detector.suggest_notch(sneha_result["freq_hz"])
        print(f"  {notch['message']}")

    print("\n--- analyze_all (full band) ---")
    summary = detector.get_session_summary([node_ravi, node_sneha])
    print(f"  Any risk:    {summary['any_risk']}")
    print(f"  Total alerts:{summary['total_alerts']}")
    print(f"  Critical:    {summary['critical_count']}")
    print(f"  Warnings:    {summary['warning_count']}")
    for alert in summary["alerts"]:
        print(f"  → {alert['message']}")
    for notch in summary["notch_filters"]:
        print(f"  → {notch['message']}")

    print("\n" + "=" * 60)