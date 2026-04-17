# InstrumentNode Documentation

## Overview

InstrumentNode represents a single performer/device in LiveMix AI. It
tracks audio levels, receives feedback detection, and generates EQ
recommendations.

## Responsibilities

-   Track dB levels
-   Assign status (idle, active, warning, critical)
-   Store feedback data
-   Generate EQ recommendations

## Initialization

InstrumentNode(name, instrument, phoneID, position)

## Methods

### update_audio_level(db)

Updates audio level and assigns status: - \> -10 dB → critical - -20 to
-10 dB → warning - -50 to -20 dB → active - \< -50 dB → idle

### receive_feedback(feedback_dict)

Stores feedback detection: { "risk": True, "freq_hz": 2800,
"growth_rate": 2.1, "severity": "warning" }

### get_recommendation()

Returns structured output including EQ recommendation.

## EQ Logic

If feedback detected: - Apply notch filter - Gain: -12 dB - Q: 4.0

Else: - No change

## Pipeline

FFT → FeedbackDetector → InstrumentNode → Dashboard
