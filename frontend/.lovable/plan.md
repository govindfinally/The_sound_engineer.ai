

# the_sound_engineer.ai — AI-Powered Live Sound Mixing Frontend

## Overview
A professional, real-time sound mixing web app for live bands with a dark, futuristic UI inspired by Ableton Live and pro audio consoles. Built with React + Vite + Tailwind CSS (Next.js isn't supported in Lovable, but we'll build the equivalent SPA).

## Design System
- **Background**: `#0a0e27` deep navy-black
- **Accents**: `#00d4ff` cyan neon, `#00ff88` green, `#ff3366` red, `#ffaa00` amber
- **Typography**: Inter/mono fonts, clean and minimal
- **Feel**: Spotify × Ableton × futuristic AI

## Pages & Flow

### 1. Home Screen (`/`)
- Centered branding: "the_sound_engineer.ai" with subtle glow
- Two large buttons: **Start Session (Leader)** / **Join Band (Member)**
- Animated background subtle grid/pulse effect

### 2. Leader Flow (`/leader`)
- Input band name → creates session (mock API call)
- Displays **band code** in large, copyable format
- "Waiting for members..." with live member list updating
- Button to proceed to Master Dashboard once members joined

### 3. Member Join Flow (`/join`)
- Form: Band Code, Name, Instrument (dropdown with guitar, vocals, drums, tabla, bass, keys, etc.)
- On join → transitions to **Live Streaming Screen**
- Shows: "LIVE — Streaming audio to mixer" with animated pulse indicator
- Simulated audio level meter

### 4. Master Dashboard (`/mixer/:sessionId`) — **Core Feature**

**Channel Strips** (horizontal scroll):
- Each member gets a vertical strip containing:
  - Name + instrument icon
  - Real-time **VU meter** (vertical, green→yellow→red gradient)
  - **Drag fader** (-60dB to 0dB) with dB readout
  - **Stereo pan knob** (L/R)
  - **EQ recommendations** panel (freq, gain, Q)
  - **Feedback alert** badges (⚠ frequency warnings)
  - Mute/Solo buttons

**Master Section** (right-side fixed):
- Master level meter
- Band Balance Score (0-100)
- Clarity Score (0-100)
- **AUTO MIX** toggle (neon glow when active)

**Auto Mix Behavior**:
- When enabled, faders animate to AI-recommended positions
- Auto-adjusted channels get a subtle highlight border
- Vocals boosted, loud instruments reduced

## Components
- `ChannelStrip` — individual mixer channel
- `VUMeter` — animated vertical level meter
- `Fader` — draggable volume slider
- `PanKnob` — stereo panning control
- `MasterChannel` — master output section with scores
- `FeedbackAlert` — warning badges for feedback frequencies
- `EQDisplay` — shows EQ recommendations per channel
- `JoinForm` — member registration form
- `LeaderPanel` — session creation + waiting room
- `WaveformVisualizer` — animated waveform display

## Real-Time Simulation
Since there's no backend connected yet, we'll use **mock WebSocket simulation** with `setInterval` to:
- Generate realistic fluctuating audio levels
- Simulate members joining
- Trigger feedback alerts randomly
- Update EQ recommendations

This makes the UI fully interactive and demonstrable without a backend.

## Responsive Design
- Desktop: full mixer layout with horizontal scroll
- Tablet: condensed strips, touch-friendly faders
- All interactions work with mouse and touch

