# 🎛️ The Sound Engineer.ai

> **Real-time multi-agent AI sound engineering for college bands and small venues.**  
> Every phone becomes a mic. Every instrument gets its own AI agent. No sound engineer needed.

---

## 🔥 What It Does

Live band playing? Each member opens the app on their phone, selects their instrument, and joins the session. From that point:

- Every phone streams audio as a **distributed microphone node**
- A dedicated **AI agent per instrument** analyzes that stream in real-time
- The system detects feedback, clipping, and frequency imbalances
- Each member receives **quantitative EQ recommendations** — exact Hz, dB, Q values — addressed by name

No guesswork. No "turn up the bass a bit." Just: *"Rohan (Guitar) — cut 2.4kHz by 3dB, Q=1.8."*

---

## 🏗️ Architecture

```
                    ┌─────────────────────────────┐
                    │        FastAPI Backend        │
                    │                               │
  Phone (Ananya) ──►│  instrument_node.py           │
  Phone (Rohan)  ──►│  ── per-instrument WebSocket  │
  Phone (Dev)    ──►│                               │
                    │  session_manager.py           │
                    │  ── Session + SessionManager  │
                    │                               │
                    │  quantitative_analyzer.py     │
                    │  ── FFT → EQ recommendations  │
                    │                               │
                    │  feedback_detector.py         │
                    │  ── 1.5dB/frame growth thresh │
                    │                               │
                    │  instrument_profiles.py       │
                    │  ── 40 instruments (incl.     │
                    │     Indian classical)         │
                    └─────────────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │       React PWA Frontend   │
                    │   (runs on each phone)     │
                    └────────────────────────────┘
```

**The "hive mind" model:** Each phone is simultaneously a mic input node AND a recommendation display. The backend orchestrates all streams together, giving the system a full acoustic picture of the venue.

---

## 🧠 AI / Technical Highlights

| Module | What it does |
|---|---|
| `instrument_profiles.py` | 40 instrument profiles with paper-backed EQ ranges — including sitar, tabla, bansuri, harmonium, sarod, veena |
| `quantitative_analyzer.py` | FFT-based frequency analysis → exact EQ recommendation output (Hz, dB, Q) |
| `feedback_detector.py` | Larsen effect detection using 1.5 dB/frame spectral growth threshold (Springer 2025) |
| `session_manager.py` | Multi-session orchestration with `Session` + `SessionManager` indexing |
| `instrument_node.py` | Per-instrument WebSocket node, streams audio from phone mic |
| `main.py` | FastAPI app — HTTP + WebSocket endpoints + HTML dashboard |

---

## 🎯 Target Users

- College bands and music societies
- College fests and auditorium concerts
- Small and semi-pro gigging bands

**Not targeting:** professional studios, enterprise audio, or recording setups. This is built for the 90% of bands who can't afford a dedicated sound engineer.

---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, WebSockets, NumPy (FFT)
- **Frontend:** React PWA (runs on any phone browser — no install)
- **Realtime:** WebSocket-based bidirectional streaming
- **Tested on:** Live phone via ngrok tunnel ✅

---

## 🚀 Running Locally

```bash
# Clone and set up
git clone https://github.com/govindfinally/the_sound_engineer.git
cd the_sound_engineer

# Backend
pip install -r requirements.txt
uvicorn main:app --reload

# Expose to phones on same network (or use ngrok)
ngrok http 8000

# Frontend (separate terminal)
cd frontend
npm install
npm start
```

Open the ngrok URL on any phone → select instrument → join session.

---

## 📍 Status

- ✅ Phase 1 Backend — all core modules built and tested
- ✅ Live phone test via ngrok — confirmed working
- 🔄 Phase 2 — Frontend PWA polish + multi-device session sync
- 🔜 Phase 3 — On-device ML inference for offline recommendations

---

## 👤 Author

**Govind** — B.Tech + M.Tech (Metallurgy + SDE), NIT Rourkela  
GitHub: [@govindfinally](https://github.com/govindfinally)
