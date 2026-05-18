"""
position_estimator.py — Phone Position Estimator
The Sound Engineer.ai · Phase 2

Science:
    GCC-PHAT gives us the time delay between every pair of phones.
    delay_seconds × speed_of_sound = distance between those phones.

    Full triangulation needs ≥3 phones with known anchor positions.
    MVP uses simpler zone classification based on delay from master phone.

    Master phone (reference) is assumed near stage.
    All other phones are classified relative to master.

    Zones:
        near_stage  →  0 – 3 m   → weight_multiplier 1.0
        mid_venue   →  3 – 8 m   → weight_multiplier 0.7
        far_venue   →  8 + m     → weight_multiplier 0.4

Source: Wireless Acoustic Sensor Networks — Springer 2023.
        Utility score drives node selection in ad-hoc arrays.
"""


import numpy as np

# Zone boundaries in meters
ZONE_BOUNDARIES = {
    "near_stage": (0.0, 3.0),
    "mid_venue":  (3.0, 8.0),
    "far_venue":  (8.0, float("inf")),
}

# Beamformer weight multiplier per zone
# Near-stage phones hear the instruments more cleanly → higher trust
ZONE_WEIGHTS = {
    "near_stage": 1.0,
    "mid_venue":  0.7,
    "far_venue":  0.4,
}


class PositionEstimator:
    def __init__(self, speed_of_sound: float = 343.0):
        self.speed_of_sound = speed_of_sound  # m/s at ~20°C room temperature

    # ------------------------------------------------------------------
    def classify_zone(self, distance_m: float) -> str:
        """
        Classify a phone into a venue zone based on its distance from master.

        Args:
            distance_m : Distance in meters (always positive).

        Returns:
            'near_stage' | 'mid_venue' | 'far_venue'
        """
        distance_m = abs(distance_m)  # delay can be negative — distance is not
        for zone, (low, high) in ZONE_BOUNDARIES.items():
            if low <= distance_m < high:
                return zone
        return "far_venue"  # safety fallback

    # ------------------------------------------------------------------
    def estimate_all_positions(self, delays: dict) -> dict:
        """
        Estimate zone + distance for every phone using delays from GCCPHATSync.

        Master phone = the phone that appears most as phone1 in delay pairs.
        All distances are relative to master.

        Args:
            delays : Output of GCCPHATSync.sync_all_nodes()
                     { (phone1_id, phone2_id): {delay_samples, delay_seconds,
                                                distance_meters, confidence} }

        Returns:
            { phone_id: {
                'zone':              str,
                'distance_m':        float,
                'weight_multiplier': float,
                'confidence':        float,
              }
            }
        """
        if not delays:
            return {}

        # Find master phone — the one that appears most as phone1 (reference)
        phone1_counts = {}
        for (p1, p2) in delays.keys():
            phone1_counts[p1] = phone1_counts.get(p1, 0) + 1
            phone1_counts.setdefault(p2, 0)

        master_id = max(phone1_counts, key=phone1_counts.get)

        # Master is always near_stage (it's the reference / stage phone)
        positions = {
            master_id: {
                "zone":              "near_stage",
                "distance_m":        0.0,
                "weight_multiplier": ZONE_WEIGHTS["near_stage"],
                "confidence":        1.0,
            }
        }

        # For every other phone: find its delay pair with master
        for (p1, p2), info in delays.items():
            # We want pairs that include master
            if p1 == master_id:
                target = p2
            elif p2 == master_id:
                target = p1
            else:
                continue  # pair doesn't involve master — skip for now

            if target in positions:
                continue  # already estimated

            distance_m = abs(info["distance_meters"])
            zone       = self.classify_zone(distance_m)

            positions[target] = {
                "zone":              zone,
                "distance_m":        round(distance_m, 2),
                "weight_multiplier": ZONE_WEIGHTS[zone],
                "confidence":        round(float(info["confidence"]), 3),
            }

        # Any phone not paired with master — classify from nearest known phone
        all_phone_ids = set()
        for p1, p2 in delays.keys():
            all_phone_ids.add(p1)
            all_phone_ids.add(p2)

        for phone_id in all_phone_ids:
            if phone_id in positions:
                continue
            # Find best available delay for this phone
            best = self._find_best_indirect(phone_id, delays, positions)
            if best:
                positions[phone_id] = best
            else:
                # No usable pair at all — assume mid_venue as safe default
                positions[phone_id] = {
                    "zone":              "mid_venue",
                    "distance_m":        -1.0,   # -1 = unknown
                    "weight_multiplier": ZONE_WEIGHTS["mid_venue"],
                    "confidence":        0.0,
                }

        return positions

    # ------------------------------------------------------------------
    def _find_best_indirect(self, phone_id: str, delays: dict, known: dict) -> dict:
        """
        If phone_id has no direct pair with master, estimate from another
        known phone. Uses the highest-confidence pair available.
        """
        best_confidence = -1.0
        best_result     = None

        for (p1, p2), info in delays.items():
            if p1 == phone_id:
                anchor = p2
            elif p2 == phone_id:
                anchor = p1
            else:
                continue

            if anchor not in known:
                continue

            confidence = float(info["confidence"])
            if confidence > best_confidence:
                best_confidence = confidence
                anchor_dist     = known[anchor]["distance_m"]
                extra_dist      = abs(info["distance_meters"])
                # Rough estimate: unknown phone is anchor_dist + extra away from stage
                total_dist      = anchor_dist + extra_dist
                zone            = self.classify_zone(total_dist)
                best_result     = {
                    "zone":              zone,
                    "distance_m":        round(total_dist, 2),
                    "weight_multiplier": ZONE_WEIGHTS[zone],
                    "confidence":        round(confidence, 3),
                }

        return best_result


# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Simulate GCCPHATSync output for 3 phones
    # phone1 = master (near stage)
    # phone2 = mid venue (~5m away)
    # phone3 = far back (~10m away)

    fs = 44100

    fake_delays = {
        ("phone1", "phone2"): {
            "delay_samples":  int(5.0 / 343.0 * fs),   # 5m → ~641 samples
            "delay_seconds":  5.0 / 343.0,
            "distance_meters": 5.0,
            "confidence":     0.87,
        },
        ("phone1", "phone3"): {
            "delay_samples":  int(10.0 / 343.0 * fs),  # 10m → ~1282 samples
            "delay_seconds":  10.0 / 343.0,
            "distance_meters": 10.0,
            "confidence":     0.63,
        },
        ("phone2", "phone3"): {
            "delay_samples":  int(5.0 / 343.0 * fs),
            "delay_seconds":  5.0 / 343.0,
            "distance_meters": 5.0,
            "confidence":     0.71,
        },
    }

    estimator = PositionEstimator()
    positions = estimator.estimate_all_positions(fake_delays)

    print("Phone Positions:\n")
    for phone_id, info in positions.items():
        print(f"  {phone_id}")
        print(f"    zone              : {info['zone']}")
        print(f"    distance_m        : {info['distance_m']} m")
        print(f"    weight_multiplier : {info['weight_multiplier']}")
        print(f"    confidence        : {info['confidence']}")
        print()

    # Assertions
    assert positions["phone1"]["zone"] == "near_stage",  "Master should be near_stage"
    assert positions["phone2"]["zone"] == "mid_venue",   "phone2 should be mid_venue"
    assert positions["phone3"]["zone"] == "far_venue",   "phone3 should be far_venue"
    assert positions["phone1"]["weight_multiplier"] > positions["phone2"]["weight_multiplier"]
    assert positions["phone2"]["weight_multiplier"] > positions["phone3"]["weight_multiplier"]

    print("✅ All assertions passed")