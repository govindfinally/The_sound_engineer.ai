"""
beamformer.py — Delay-and-Sum Beamformer
The Sound Engineer.ai · Phase 2

Science:
    Time delay of τ samples in time domain = phase rotation in frequency domain:
        FFT_shifted(k) = FFT(k) × e^(-j·2π·k·τ / N)
    where k = frequency bin index, N = original signal length.

    This lets us align all phone signals without touching time-domain audio.
    After alignment, we weight by utility_score and average → coherent signals add,
    noise cancels.

    Formula:  Y(f) = (1 / W_total) × Σ  weight_m × X_m(f) × e^(-j·2π·f·τ_m / N)

Source: Advances in Microphone Array Processing, arXiv 2025.
        Ad-hoc arrays (random placement) still work with Delay-and-Sum.
"""

import numpy as np
import sys
import os

# Frequency zone boundaries (Hz) — matches band_analyzer output structure
FREQ_ZONES = {
    "sub_bass":  (20,   60),
    "bass":      (60,   250),
    "low_mids":  (250,  500),
    "mids":      (500,  2000),
    "high_mids": (2000, 4000),
    "highs":     (4000, 20000),
}

# dB thresholds for zone status
HOT_THRESHOLD_DB   = -12.0   # above this → 'hot'
ALERT_THRESHOLD_DB = -20.0   # above this → 'alert'
OK_THRESHOLD_DB    = -40.0   # above this → 'ok', below → 'silent'


class DelayAndSumBeamformer:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    # ------------------------------------------------------------------
    # Core: phase shift one FFT by τ samples
    # ------------------------------------------------------------------
    def apply_phase_shift(self, fft_complex: np.ndarray, delay_samples: int) -> np.ndarray:
        """
        Applies a time-domain delay of `delay_samples` in frequency domain.

        Args:
            fft_complex   : Complex FFT array (output of np.fft.rfft, length = N//2 + 1)
            delay_samples : Integer — how many samples to shift (can be negative)

        Returns:
            Phase-shifted complex FFT of same shape.
        """
        n_bins = len(fft_complex)
        # Original signal length inferred from rfft bin count
        # rfft of N-sample signal → N//2 + 1 bins, so N = 2*(n_bins - 1)
        N = 2 * (n_bins - 1)

        k = np.arange(n_bins)  # frequency bin indices 0 … N//2
        phase = np.exp(-1j * 2 * np.pi * k * delay_samples / N)
        return fft_complex * phase

    # ------------------------------------------------------------------
    # Main: combine all phone FFTs into one beamformed signal
    # ------------------------------------------------------------------
    def combine(
        self,
        node_ffts: dict,   # {phone_id: complex_fft_array}
        delays:    dict,   # {phone_id: delay_samples}  ← from GCCPHATSync
        weights:   dict,   # {phone_id: utility_score}  ← from InstrumentNode
    ) -> np.ndarray:
        """
        Weighted Delay-and-Sum beamforming in frequency domain.

        Steps:
        1. For each phone: shift its FFT by its delay
        2. Multiply by its utility weight
        3. Sum all shifted+weighted FFTs
        4. Divide by total weight → combined complex FFT
        5. Return magnitude

        Args:
            node_ffts : {phone_id: np.ndarray (complex)}
            delays    : {phone_id: int (delay_samples, can be negative)}
            weights   : {phone_id: float (0.0 – 1.0)}

        Returns:
            np.ndarray — combined FFT magnitude (same length as input FFTs)
        """
        if not node_ffts:
            raise ValueError("node_ffts is empty — no phones to beamform")

        # Determine output array length from first node
        first_id   = next(iter(node_ffts))
        n_bins     = len(node_ffts[first_id])
        combined   = np.zeros(n_bins, dtype=complex)
        total_weight = 0.0

        for phone_id, fft_complex in node_ffts.items():
            delay  = delays.get(phone_id, 0)      # default: no shift if unknown
            weight = weights.get(phone_id, 1.0)   # default: equal weight

            if weight <= 0:
                continue  # skip dead/muted nodes

            shifted    = self.apply_phase_shift(fft_complex, delay)
            combined  += weight * shifted
            total_weight += weight

        if total_weight == 0:
            return np.zeros(n_bins)

        combined /= total_weight
        return np.abs(combined)   # magnitude — same format as quantitative_analyzer output

    # ------------------------------------------------------------------
    # Venue picture: zone-by-zone analysis of the combined signal
    # ------------------------------------------------------------------
    def get_venue_picture(
        self,
        combined_fft: np.ndarray,  # output of combine()
        n_samples: int = None,     # original signal length (used for Hz mapping)
    ) -> dict:
        """
        Analyses the beamformed signal by frequency zone.

        Args:
            combined_fft : np.ndarray — FFT magnitude array from combine()
            n_samples    : int — original signal length.
                           If None, inferred as 2*(len(combined_fft) - 1)

        Returns:
            {
            'combined_fft' : np.ndarray,
            'peak_db'      : float,
            'headroom_db'  : float,
            'zone_analysis': {
                'sub_bass':  {'db': float, 'status': str},
                'bass':      {'db': float, 'status': str},
                ...
              }
            }
        """
        n_bins = len(combined_fft)
        if n_samples is None:
            n_samples = 2 * (n_bins - 1)

        # Hz per bin
        hz_per_bin = self.sample_rate / n_samples

        # Overall peak in dB
        peak_linear = np.max(combined_fft) if np.max(combined_fft) > 0 else 1e-10
        peak_db     = 20 * np.log10(peak_linear + 1e-10)
        headroom_db = 0.0 - peak_db  # headroom to 0 dBFS

        zone_analysis = {}
        for zone_name, (hz_low, hz_high) in FREQ_ZONES.items():
            bin_low  = int(hz_low  / hz_per_bin)
            bin_high = int(hz_high / hz_per_bin)
            bin_high = min(bin_high, n_bins - 1)

            if bin_low >= bin_high:
                zone_analysis[zone_name] = {"db": -96.0, "status": "silent"}
                continue

            zone_slice  = combined_fft[bin_low:bin_high]
            zone_energy = np.mean(zone_slice ** 2)
            zone_db     = 10 * np.log10(zone_energy + 1e-10)

            if zone_db > HOT_THRESHOLD_DB:
                status = "hot"
            elif zone_db > ALERT_THRESHOLD_DB:
                status = "alert"
            elif zone_db > OK_THRESHOLD_DB:
                status = "ok"
            else:
                status = "silent"

            zone_analysis[zone_name] = {
                "db":     round(zone_db, 2),
                "status": status
            }

        return {
            "combined_fft":  combined_fft,
            "peak_db":       round(peak_db, 2),
            "headroom_db":   round(headroom_db, 2),
            "zone_analysis": zone_analysis,
        }


# ----------------------------------------------------------------------
# Test
# ----------------------------------------------------------------------
if __name__ == "__main__":
    fs = 44100
    t  = np.linspace(0, 1, fs, endpoint=False)

    # Two phones recording the same 440 Hz tone, phone2 is 1000 samples late
    signal1 = np.sin(2 * np.pi * 440 * t) + 0.05 * np.random.randn(fs)
    delay_samples = 1000
    signal2 = np.concatenate((np.zeros(delay_samples), signal1[:-delay_samples]))
    signal2 += 0.1 * np.random.randn(fs)   # phone2 has more noise → lower weight

    fft1 = np.fft.rfft(signal1)
    fft2 = np.fft.rfft(signal2)

    beamer = DelayAndSumBeamformer(sample_rate=fs)

    node_ffts = {"phone1": fft1, "phone2": fft2}
    delays    = {"phone1": 0, "phone2": 1000}        # phone2 is 1000 samples behind
    weights   = {"phone1": 0.9, "phone2": 0.4}       # phone1 cleaner → higher weight

    combined_mag = beamer.combine(node_ffts, delays, weights)
    picture      = beamer.get_venue_picture(combined_mag, n_samples=fs)

    print(f"Peak dB      : {picture['peak_db']}")
    print(f"Headroom dB  : {picture['headroom_db']}")
    print("\nZone Analysis:")
    for zone, info in picture["zone_analysis"].items():
        print(f"  {zone:<12} → {info['db']:>7.2f} dB  [{info['status']}]")

    # Sanity check: 440 Hz should be in the 'bass' zone (250–500 Hz)
    assert picture["zone_analysis"]["bass"]["status"] != "silent", \
        "440 Hz should show energy in bass zone"
    print("\n✅ Sanity check passed — 440 Hz visible in bass zone")