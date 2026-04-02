import numpy as np
import math
def compute_fft(pcm_bytes:bytes, sample_rate:int):
    # Convert byte data to numpy array
    audio_data = np.frombuffer(pcm_bytes, dtype=np.float32)
    if len(audio_data) <256.0:
        return None
    
    # Apply a Hanning window to reduce spectral leakage
    window = np.hanning(len(audio_data))
    windowed_data = audio_data * window
    
    # Compute the FFT
    fft_result = np.fft.rfft(windowed_data)
    
    # Get the corresponding frequencies for the FFT bins
    freqs = np.fft.rfftfreq(len(windowed_data), d=1/sample_rate)
    
    magnitudes = np.abs(fft_result) / len(audio_data)
    return magnitudes, freqs 
def find_peak_frequency(magnitudes: np.ndarray, freqs: np.ndarray, freq_range: tuple) -> float:
    # step 1 — mask to instrument range
    # step 2 — check mask has values
    # step 3 — argmax inside mask
    # step 4 — return peak Hz
    lowest_freq, highest_freq = freq_range
    mask = (freqs >= lowest_freq) & (freqs <= highest_freq)
    if np.any(mask):
        masked_magnitudes = magnitudes[mask]
        masked_freqs = freqs[mask]
        peak_index = np.argmax(masked_magnitudes)
        peak_freq = masked_freqs[peak_index]
        return peak_freq
    else:
        return 0.0
def compute_band_energy(magnitudes: np.ndarray, freqs: np.ndarray, low_hz: float, high_hz: float) -> float:
    # step 1 — mask for band
    # step 2 — check mask
    # step 3 — RMS
    # step 4 — convert to dBFS
    # step 5 — return
    mask = (freqs >= low_hz) & (freqs <= high_hz)
    if not np.any(mask):
        return -100.0
    band_magnitudes = magnitudes[mask]
    rms = np.sqrt(np.mean(band_magnitudes**2))
    db  = 20 * np.log10(rms + 1e-9)   # +1e-9 handles rms=0, no separate check needed
    return round(float(db), 1)

def calculate_q(peak_freq: float, magnitudes: np.ndarray, freqs: np.ndarray, threshold_db: float = -3) -> float:
    # step 1 — peak magnitude
    # step 2 — threshold in linear
    # step 3 — find bins above threshold
    # step 4 — bandwidth
    # step 5 — check zero bandwidth
    # step 6 — Q = peak / bandwidth
    # step 7 — clamp
    # step 8 — return
    peak_magnitude   = float(np.max(magnitudes))   # max() returns the actual VALUE
    threshold_linear = peak_magnitude * (10 ** (threshold_db / 20))
    above_threshold = magnitudes >= threshold_linear
    if np.any(above_threshold):
        bandwidth_bins = np.where(above_threshold)[0]
        bandwidth_hz = freqs[bandwidth_bins[-1]] - freqs[bandwidth_bins[0]]
        if bandwidth_hz > 0:
            q = peak_freq / bandwidth_hz
            q_clamped = max(0.1, min(q, 10.0))
            return q_clamped
def calculate_snr(magnitudes: np.ndarray, freqs: np.ndarray, signal_range: tuple) -> float:
    # step 1 — signal mask
    # step 2 — noise mask
    # step 3 — signal power
    # step 4 — noise power
    # step 5 — check zero noise
    # step 6 — SNR = signal / noise
    # step 7 — return
    mask_signal = (freqs >= signal_range[0]) & (freqs <= signal_range[1])
    mask_noise = ~mask_signal
    signal_power = np.mean(magnitudes[mask_signal] ** 2)
    noise_power = np.mean(magnitudes[mask_noise] ** 2)
    if noise_power > 0:
        snr = signal_power /(noise_power + 1e-9 )# add small value to avoid division by zero
        return snr
    elif noise_power==0:
        return 999.0
if __name__ == "__main__":
    import struct

    # Simulate 4096 float32 PCM samples with a spike at 284 Hz
    sample_rate = 44100
    N = 4096
    t = np.linspace(0, N/sample_rate, N)
    signal = 0.5 * np.sin(2 * np.pi * 284 * t)  # pure 284 Hz tone
    pcm_bytes = struct.pack(f"{N}f", *signal)

    # Test compute_fft
    magnitudes, freqs = compute_fft(pcm_bytes, sample_rate)
    print(f"FFT computed: {len(magnitudes)} bins, max freq: {freqs[-1]:.0f} Hz")

    # Test find_peak_frequency
    peak = find_peak_frequency(magnitudes, freqs, (40, 300))
    print(f"Peak frequency: {peak:.1f} Hz")  # should be ~284 Hz

    # Test compute_band_energy
    energy = compute_band_energy(magnitudes, freqs, 40, 300)
    print(f"Band energy (40-300 Hz): {energy:.1f} dBFS")

    # Test calculate_q
    q = calculate_q(peak, magnitudes, freqs)
    print(f"Q value: {q:.2f}")

    # Test calculate_snr
    snr = calculate_snr(magnitudes, freqs, (40, 300))
    print(f"SNR: {snr:.2f}")