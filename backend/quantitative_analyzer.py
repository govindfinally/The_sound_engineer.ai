# GCC-PHAT(τ) = IFFT [ X₁(f) · X₂*(f) / |X₁(f) · X₂*(f)| ] the formula for GCC-PHAT, where X₁ and X₂ are the FFTs of the two signals, and * denotes complex conjugation.
from ast import Return
from itertools import combinations
from typing import List, Dict
import sys
import numpy as np
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))




import numpy as np


def compute_fft(pcm_bytes, sample_rate: int = 44100):
    """
    Convert raw PCM bytes from phone mic into FFT magnitudes + frequencies.

    Args:
        pcm_bytes   : Raw bytes (float32 LE) from WebSocket stream.
                      Also accepts np.ndarray directly (for testing).
        sample_rate : Default 44100 Hz.

    Returns:
        (magnitudes, freqs) — both np.ndarray of length N//2 + 1
        None               — if input is too short (< 256 samples)
    """
    if isinstance(pcm_bytes, np.ndarray):
        samples = pcm_bytes.astype(np.float32)
    else:
        samples = np.frombuffer(pcm_bytes, dtype=np.float32)

    if len(samples) < 256:
        return None

    window     = np.hanning(len(samples))
    fft_result = np.fft.rfft(samples * window)
    magnitudes = np.abs(fft_result) / len(samples)
    freqs      = np.fft.rfftfreq(len(samples), d=1.0 / sample_rate)
    return magnitudes, freqs


def find_peak_frequency(magnitudes, freqs, freq_range) -> float:
    """
    Find the exact Hz of the loudest frequency within an instrument's range.

    Args:
        magnitudes : Output from compute_fft
        freqs      : Output from compute_fft
        freq_range : Tuple (low_hz, high_hz) from instrument profile

    Returns:
        float — peak frequency in Hz, rounded to 1 decimal.
        0.0   — if no bins found in range.
    """
    low, high = freq_range
    mask = (freqs >= low) & (freqs <= high)
    if not mask.any():
        return 0.0
    peak_idx  = np.argmax(magnitudes[mask])
    peak_freq = float(freqs[mask][peak_idx])
    return round(peak_freq, 1)


def compute_band_energy(magnitudes, freqs, low_hz: float, high_hz: float) -> float:
    """
    Calculate the RMS energy in a frequency band, in dBFS.

    Args:
        magnitudes : Output from compute_fft
        freqs      : Output from compute_fft
        low_hz     : Lower bound of band
        high_hz    : Upper bound of band

    Returns:
        float — energy in dBFS (always negative for real audio).
        -100.0 — silence / no bins in range.
    """
    mask = (freqs >= low_hz) & (freqs < high_hz)
    if not mask.any():
        return -100.0
    rms = np.sqrt(np.mean(magnitudes[mask] ** 2))
    db  = 20 * np.log10(rms + 1e-9)
    return round(float(db), 1)


def calculate_q(peak_freq: float, magnitudes, freqs, threshold_db: float = -3) -> float:
    """
    Calculate the Q factor for the EQ filter at peak_freq.

    Q = peak_freq / bandwidth
    bandwidth = span of frequencies within threshold_db of peak magnitude.

    Args:
        peak_freq     : Center frequency in Hz (from find_peak_frequency)
        magnitudes    : Output from compute_fft
        freqs         : Output from compute_fft
        threshold_db  : How far below peak to measure bandwidth. Default -3 dB.

    Returns:
        float — Q value clamped to [0.5, 4.0].
        1.4   — default when bandwidth cannot be measured.
    """
    peak_magnitude   = np.max(magnitudes)
    threshold_linear = peak_magnitude * (10 ** (threshold_db / 20))
    above_threshold  = freqs[magnitudes >= threshold_linear]

    if len(above_threshold) < 2:
        return 1.4

    bandwidth = float(above_threshold.max() - above_threshold.min())
    if bandwidth == 0:
        return 1.4

    q = peak_freq / bandwidth
    q = float(np.clip(q, 0.5, 4.0))
    return round(q, 2)


def calculate_snr(magnitudes, freqs, signal_range) -> float:
    """
    Signal-to-Noise Ratio — how clean is this phone's audio?

    Signal = energy inside instrument's frequency range.
    Noise  = everything outside it.

    Used by InstrumentNode.update_utility_score() for beamforming weight.

    Args:
        magnitudes   : Output from compute_fft
        freqs        : Output from compute_fft
        signal_range : Tuple (low_hz, high_hz) — instrument's freq range

    Returns:
        float — SNR value. Higher = cleaner.
        999.0 — perfect signal (zero noise, synthetic test only).
    """
    low, high    = signal_range
    signal_mask  = (freqs >= low) & (freqs <= high)
    noise_mask   = ~signal_mask

    signal_power = np.mean(magnitudes[signal_mask] ** 2)
    noise_power  = np.mean(magnitudes[noise_mask]  ** 2)

    if noise_power == 0:
        return 999.0

    snr = signal_power / (noise_power + 1e-9)
    return round(float(snr), 2)


# ----------------------------------------------------------------------
if __name__ == '__main__':
    import struct

    sample_rate = 44100
    N = 4096
    t = np.linspace(0, N / sample_rate, N)
    signal = 0.5 * np.sin(2 * np.pi * 284 * t)   # pure 284 Hz tone
    pcm_bytes = struct.pack(f'{N}f', *signal)

    result = compute_fft(pcm_bytes)
    assert result is not None, "compute_fft returned None"
    magnitudes, freqs = result
    print(f"FFT bins : {len(magnitudes)}, max freq : {freqs[-1]:.0f} Hz")

    peak = find_peak_frequency(magnitudes, freqs, (40, 300))
    print(f"Peak freq : {peak} Hz")          # expect ~284

    energy = compute_band_energy(magnitudes, freqs, 40, 300)
    print(f"Band energy : {energy} dBFS")

    q = calculate_q(peak, magnitudes, freqs)
    print(f"Q value : {q}")

    snr = calculate_snr(magnitudes, freqs, (40, 300))
    print(f"SNR : {snr}")

    assert abs(peak - 284) < 15, f"Peak {peak} Hz too far from 284 Hz"
    print("\n✅ All checks passed")