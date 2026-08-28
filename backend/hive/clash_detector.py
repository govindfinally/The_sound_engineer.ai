"""
clash_detector.py — Frequency Clash Detector
The Sound Engineer.ai · Phase 2

A frequency clash occurs when two instruments compete in the same frequency
zone with comparable energy levels. The instrument lower in the priority
hierarchy gets a cut recommendation; the higher-priority one gets a boost.

Priority order (descending):
    vocals → lead_guitar → drums → bass_guitar → rhythm_guitar → keys → other

Clash zones (Hz ranges where instruments commonly fight):
    low_end    :   40 –  200  (bass vs kick drum)
    low_mids   :  200 –  500  (bass vs rhythm guitar, keys)
    mids       :  500 – 2000  (vocals vs guitar, keys)
    presence   : 2000 – 5000  (vocals vs lead guitar)
    air        : 5000 – 12000 (cymbals vs hi-hat — less common)

Clash threshold: if both instruments have energy > -30 dBFS in the overlap
zone AND energy difference < CLASH_SENSITIVITY_DB, it's a clash.
"""

import sys
import os
from itertools import combinations

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from quantitative_analyzer import compute_band_energy

# ------------------------------------------------------------------
# Priority — lower index = higher priority
# ------------------------------------------------------------------
PRIORITY = [
    "vocals",
    "lead_guitar",
    "drums",
    "bass_guitar",
    "rhythm_guitar",
    "keys",
    "other",
]

# ------------------------------------------------------------------
# Known instrument pair → frequency zones where they typically clash
# Keys are frozensets so order doesn't matter
# ------------------------------------------------------------------
KNOWN_CLASH_ZONES = {
    frozenset({"bass_guitar", "drums"}):         [(40,  200)],
    frozenset({"bass_guitar", "rhythm_guitar"}): [(200, 500)],
    frozenset({"bass_guitar", "keys"}):          [(200, 500)],
    frozenset({"vocals",      "lead_guitar"}):   [(500, 2000), (2000, 5000)],
    frozenset({"vocals",      "rhythm_guitar"}): [(500, 2000)],
    frozenset({"vocals",      "keys"}):          [(500, 2000)],
    frozenset({"lead_guitar", "rhythm_guitar"}): [(200, 2000)],
    frozenset({"lead_guitar", "keys"}):          [(500, 2000)],
    frozenset({"rhythm_guitar","keys"}):         [(200, 2000)],
    frozenset({"drums",       "lead_guitar"}):   [(2000, 5000)],
}

# Both instruments must be above this dBFS to count as clashing
ENERGY_FLOOR_DB    = -30.0

# Energy difference within this range = clash (both fighting equally)
CLASH_SENSITIVITY_DB = 12.0

# EQ correction strength tiers
CORRECTION_DB = {
    "severe": 4.0,   # energy diff < 3 dB
    "moderate": 3.0, # energy diff 3–7 dB
    "mild": 2.0,     # energy diff 7–12 dB
}


def _priority_rank(instrument_type: str) -> int:
    """Lower rank = higher priority. Unknown instruments go last."""
    try:
        return PRIORITY.index(instrument_type.lower())
    except ValueError:
        return len(PRIORITY)


def _correction_amount(energy_diff_db: float) -> float:
    if energy_diff_db < 3.0:
        return CORRECTION_DB["severe"]
    elif energy_diff_db < 7.0:
        return CORRECTION_DB["moderate"]
    else:
        return CORRECTION_DB["mild"]


class ClashDetector:

    # ------------------------------------------------------------------
    def analyze_pair(self, node_a, node_b) -> list:
        """
        Check for frequency clashes between two InstrumentNodes.

        Uses compute_band_energy on the overlap zones defined in
        KNOWN_CLASH_ZONES for this instrument pair.

        Args:
            node_a : InstrumentNode (must have .instrument_type, .magnitudes, .freqs)
            node_b : InstrumentNode

        Returns:
            List of clash dicts — one per clashing zone. Empty if no clash.
            Each dict: {
                'instrument_a'  : str,
                'instrument_b'  : str,
                'member_a'      : str,
                'member_b'      : str,
                'zone_hz'       : (low, high),
                'energy_a_db'   : float,
                'energy_b_db'   : float,
                'winner'        : str  (instrument type),
                'loser'         : str,
                'loser_member'  : str,
                'correction_db' : float,
                'severity'      : str  ('severe' | 'moderate' | 'mild'),
                'recommendation': str,
            }
        """
        type_a = node_a.instrument_type.lower()
        type_b = node_b.instrument_type.lower()
        pair   = frozenset({type_a, type_b})

        # If no FFT data yet, skip
        if node_a.magnitudes is None or node_b.magnitudes is None:
            return []

        zones = KNOWN_CLASH_ZONES.get(pair, [])
        if not zones:
            return []

        clashes = []
        for (low_hz, high_hz) in zones:
            energy_a = compute_band_energy(node_a.magnitudes, node_a.freqs, low_hz, high_hz)
            energy_b = compute_band_energy(node_b.magnitudes, node_b.freqs, low_hz, high_hz)

            # Both must be loud enough to actually be clashing
            if energy_a < ENERGY_FLOOR_DB or energy_b < ENERGY_FLOOR_DB:
                continue

            energy_diff = abs(energy_a - energy_b)
            if energy_diff > CLASH_SENSITIVITY_DB:
                continue  # one is clearly dominant — not a real clash

            # Determine winner by priority
            rank_a = _priority_rank(type_a)
            rank_b = _priority_rank(type_b)

            if rank_a <= rank_b:
                winner_node, loser_node = node_a, node_b
                winner_type, loser_type = type_a, type_b
                loser_energy = energy_b
            else:
                winner_node, loser_node = node_b, node_a
                winner_type, loser_type = type_b, type_a
                loser_energy = energy_a

            correction = _correction_amount(energy_diff)

            # Severity label
            if energy_diff < 3.0:
                severity = "severe"
            elif energy_diff < 7.0:
                severity = "moderate"
            else:
                severity = "mild"

            # Human-readable recommendation
            center_hz = int((low_hz + high_hz) / 2)
            recommendation = (
                f"{loser_node.member_name} ({loser_type.replace('_', ' ').title()}) — "
                f"Cut {correction:.1f} dB around {center_hz} Hz "
                f"[{low_hz}–{high_hz} Hz clash with "
                f"{winner_node.member_name} ({winner_type.replace('_', ' ').title()})]"
            )

            clashes.append({
                "instrument_a":   type_a,
                "instrument_b":   type_b,
                "member_a":       node_a.member_name,
                "member_b":       node_b.member_name,
                "zone_hz":        (low_hz, high_hz),
                "energy_a_db":    energy_a,
                "energy_b_db":    energy_b,
                "winner":         winner_type,
                "loser":          loser_type,
                "loser_member":   loser_node.member_name,
                "correction_db":  correction,
                "severity":       severity,
                "recommendation": recommendation,
            })

        return clashes

    # ------------------------------------------------------------------
    def analyze_all(self, nodes: list) -> list:
        """
        Run clash detection across every pair of nodes in the session.

        Args:
            nodes : List of InstrumentNode objects

        Returns:
            List of all clash dicts, sorted by severity (severe first).
            Empty list if no clashes detected.
        """
        if len(nodes) < 2:
            return []

        all_clashes = []
        for node_a, node_b in combinations(nodes, 2):
            pair_clashes = self.analyze_pair(node_a, node_b)
            all_clashes.extend(pair_clashes)

        # Sort: severe → moderate → mild
        severity_order = {"severe": 0, "moderate": 1, "mild": 2}
        all_clashes.sort(key=lambda c: severity_order.get(c["severity"], 3))

        return all_clashes

    # ------------------------------------------------------------------
    def get_summary(self, clashes: list) -> dict:
        """
        Summarise clash results for the band_analyzer output.

        Args:
            clashes : Output of analyze_all()

        Returns:
            {
              'total_clashes' : int,
              'severe_count'  : int,
              'affected_members': list[str],
              'top_clash'     : dict | None  (the most severe clash),
            }
        """
        if not clashes:
            return {
                "total_clashes":    0,
                "severe_count":     0,
                "affected_members": [],
                "top_clash":        None,
            }

        affected = set()
        for c in clashes:
            affected.add(c["member_a"])
            affected.add(c["member_b"])

        return {
            "total_clashes":    len(clashes),
            "severe_count":     sum(1 for c in clashes if c["severity"] == "severe"),
            "affected_members": sorted(affected),
            "top_clash":        clashes[0],   # already sorted by severity
        }


# ----------------------------------------------------------------------
if __name__ == "__main__":
    import numpy as np
    import struct

    # ---- Minimal fake InstrumentNode for testing ----
    class FakeNode:
        def __init__(self, member_name, instrument_type, freq_hz, energy=0.5):
            self.member_name     = member_name
            self.instrument_type = instrument_type
            fs  = 44100
            N   = 4096
            t   = np.linspace(0, N / fs, N)
            sig = energy * np.sin(2 * np.pi * freq_hz * t)
            sig += energy * np.sin(2 * np.pi * (freq_hz * 1.2) * t)  # harmonic
            window     = np.hanning(N)
            fft_result = np.fft.rfft(sig * window)
            self.magnitudes = np.abs(fft_result) / N
            self.freqs      = np.fft.rfftfreq(N, d=1.0 / fs)

    # Ravi's bass guitar and Arjun's drums — both playing hard in 40-200 Hz
    ravi  = FakeNode("Ravi",  "bass_guitar", freq_hz=80,  energy=0.6)
    arjun = FakeNode("Arjun", "drums",       freq_hz=100, energy=0.55)
    priya = FakeNode("Priya", "vocals",      freq_hz=800, energy=0.7)
    karan = FakeNode("Karan", "lead_guitar", freq_hz=900, energy=0.65)

    detector = ClashDetector()

    print("=== Pair: Bass vs Drums ===")
    clashes = detector.analyze_pair(ravi, arjun)
    for c in clashes:
        print(f"  [{c['severity'].upper()}] {c['recommendation']}")
    if not clashes:
        print("  No clash detected")

    print("\n=== Pair: Vocals vs Lead Guitar ===")
    clashes = detector.analyze_pair(priya, karan)
    for c in clashes:
        print(f"  [{c['severity'].upper()}] {c['recommendation']}")
    if not clashes:
        print("  No clash detected")

    print("\n=== Full Band Analysis ===")
    all_clashes = detector.analyze_all([ravi, arjun, priya, karan])
    summary     = detector.get_summary(all_clashes)
    print(f"  Total clashes    : {summary['total_clashes']}")
    print(f"  Severe clashes   : {summary['severe_count']}")
    print(f"  Affected members : {summary['affected_members']}")
    if summary["top_clash"]:
        print(f"  Top clash        : {summary['top_clash']['recommendation']}")