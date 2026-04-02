from instrument_profile import get_profile
import numpy as np
class InstrumentNode:
    def __init__(self, name, instrument,phoneID,position): # node that gets created when created by the player
        self.name = name
        self.member_name = name
        self.instrument = instrument
        self.phoneID=phoneID
        self.position=position
        self.fft_history=[]
        self.peakfreq_history=[]
        self.current_db = -60.0
        self.status = "idle"
        self.utility_score = 1.0
        # static data
        self.profile        = get_profile(instrument)
        self.freq_range     = self.profile["freq_range"]
        self.ideal_range_db = self.profile["ideal_range_db"]
        self.clip_threshold = self.profile["clip_threshold"]
        self.q_cut          = self.profile["q_cut"]
        self.q_boost        = self.profile["q_boost"]
        self.hp_filter_hz   = self.profile["hp_filter_hz"]
        self.problem_zones  = self.profile["problem_zones"]
        # dynamic data
        self.fft_history        = []     # last 10 FFT magnitude arrays
        self.peak_freq_history  = []     # last 10 peak Hz values
        self.current_db         = -60.0  # current energy level
        self.snr                = 0.0    # signal to noise ratio
        self.utility_score      = 1.0    # 0.0 to 1.0
        self.weight             = 1.0    # beamforming weight
        self.status             = "idle"
    def update_frame(self, fft_magnitudes: np.ndarray, 
                    freqs: np.ndarray, current_db: float):
        "Called every 93ms with new audio frame data."
        self.fft_history.append(fft_magnitudes)
        if len(self.fft_history) > 10:
            self.fft_history.pop(0)
        self.current_db=current_db
        
        lowest_freq,highest_freq=self.freq_range
        mask = (freqs >= lowest_freq) & (freqs <= highest_freq)
        peak_freq = 0
        if np.any(mask):
            masked_magnitudes = fft_magnitudes[mask]
            masked_freqs = freqs[mask]
            peak_index = np.argmax(masked_magnitudes)
            peak_freq = masked_freqs[peak_index]
            self.peak_freq_history.append(peak_freq)
        if current_db > self.clip_threshold:
            self.status = "critical"
        elif current_db > self.ideal_range_db[1]:
            self.status = "alert"
        elif current_db < self.ideal_range_db[0]:
            self.status = "alert"
        else:
            self.status = "active"
        print(f"Updated node '{self.name}' with current dB: {current_db:.2f}, peak freq: {peak_freq:.2f} Hz, status: {self.status}")
        
    def calculate_gain_correction(self):
        print("Calculating gain correction based on current profile and input data...")
        if not self.fft_history:
            return {"action": "waiting", "message": "No audio data yet"}
        latest_peak_freq = self.peak_freq_history[-1] if self.peak_freq_history else 0
        target_db=self.ideal_range_db[1]
        correction_db=self.current_db-target_db
        if correction_db > 0.5:
            action="cut"
            q=self.q_cut
        elif correction_db < -0.5:
            action="boost"
            q=self.q_boost
        else:
            action="none"
            q=0.0
        
        print(f"Calculated gain correction: {correction_db:.2f} dB, action: {action}")
        return {"action":        action,
            "freq_hz":   float(round(latest_peak_freq, 1)),
            "correction_db": round(abs(correction_db), 1),
            "q":             q,
            "current_db":    round(self.current_db, 1),
            "target_db":     round(target_db, 1),
        }

    
    def feedback_risk_check(self):
        print("Checking for feedback risk...")
        if len(self.fft_history) < 2:
            return {"risk": "unknown", "message": "Not enough data"}
        lattest = self.fft_history[-1 ] 
        oldest = self.fft_history[0]
        growth=(lattest-oldest)/3
        
        max_growth_idx  = int(np.argmax(growth))
        max_growth_rate = float(growth[max_growth_idx])

        # Threshold from Springer 2025 paper: 1.5 dB/frame
        if max_growth_rate > 1.5:
            return {
                "risk":        True,
                "freq_hz":     round(float(self.peak_freq_history[-1]), 1),
                "growth_rate": round(max_growth_rate, 2),
                "severity":    "critical" if max_growth_rate > 2.5 else "warning",
            }

        return {"risk": False, "growth_rate": round(max_growth_rate, 2)}

    def update_utility_score(self, snr_value: float):
        """Rates how clean this phone's audio is. 0.0 = bad, 1.0 = perfect."""

        self.snr           = snr_value
        self.utility_score = round(snr_value / (snr_value + 10), 2)
        self.weight        = self.utility_score  # used in beamforming

        if self.utility_score < 0.3:
            print(f"[WARNING] {self.name}'s phone has low audio quality "
                f"(score: {self.utility_score})")

    # ─────────────────────────────────────────────────────
    def get_recommendation(self) -> dict:
        """Final output — what the master dashboard shows for this member."""

        gain    = self.calculate_gain_correction()
        feedback = self.feedback_risk_check()
        alerts  = []

        if gain["action"] in ("cut", "boost"):
            alerts.append({
                "type":    gain["action"],
                "freq_hz": gain["freq_hz"],
                "db":      gain["correction_db"],
                "q":       gain["q"],
                "message": (
                    f"{self.member_name} ({self.instrument.replace('_',' ').title()}) "
                    f"— {gain['action'].capitalize()} {gain['freq_hz']} Hz "
                    f"by {gain['correction_db']} dB, Q={gain['q']}"
                )
            })

        if feedback["risk"]:
            alerts.append({
                "type":    "feedback",
                "freq_hz": feedback["freq_hz"],
                "message": (
                    f"{self.member_name} — Feedback risk at "
                    f"{feedback['freq_hz']} Hz! "
                    f"Growth: {feedback['growth_rate']} dB/frame"
                )
            })

        return {
            "member":        self.member_name,
            "instrument":    self.instrument,
            "status":        self.status,
            "current_db":    round(self.current_db, 1),
            "utility_score": self.utility_score,
            "alerts":        alerts,
        }

    # ─────────────────────────────────────────────────────
    def __repr__(self):
        return (f"InstrumentNode(name={self.name}, instrument={self.instrument}, "
                f"phoneID={self.phoneID}, position={self.position}, "
                f"current_db={self.current_db:.1f} dB, status={self.status})")


# ── Quick test ──────────────────────────────────────────
if __name__ == "__main__":
    import numpy as np

    # Create a node for Ravi
    node = InstrumentNode("Ravi", "bass_guitar", "ws_node_1", "stage_left")
    print(node)

    # Simulate 5 audio frames
    sample_rate = 44100
    N = 4096
    freqs = np.fft.rfftfreq(N, d=1.0/sample_rate)

    for i in range(5):
        # Fake FFT data — spike at 284 Hz (simulating mud problem)
        fft_data = np.random.uniform(0.0001, 0.001, len(freqs))
        spike_idx = np.argmin(np.abs(freqs - 284))
        fft_data[spike_idx] = 0.8   # big spike at 284 Hz
        current_db = -18.3          # above ideal range

        node.update_frame(fft_data, freqs, current_db)

    print("\n--- Gain Correction ---")
    print(node.calculate_gain_correction())

    print("\n--- Feedback Risk ---")
    print(node.feedback_risk_check())

    print("\n--- Full Recommendation ---")
    rec = node.get_recommendation()
    for alert in rec["alerts"]:
        print(" →", alert["message"])