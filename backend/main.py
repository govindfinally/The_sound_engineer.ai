"""
================================================================================
  the_sound_engineer / backend / main.py
  The Sound Engineer.ai — FastAPI Server
  Entry point for the entire backend.
================================================================================
"""

import asyncio
import json
import struct

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from session_manager import SessionManager
from quantitative_analyzer import (
    compute_fft,
    compute_band_energy,
    calculate_snr,
)

# ══════════════════════════════════════════════════════════════════════════════
# APP SETUP
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="The Sound Engineer.ai",
    description="Real-time AI sound engineer for college and small bands",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# One SessionManager instance for the whole server
manager = SessionManager()


# ══════════════════════════════════════════════════════════════════════════════
# REQUEST MODELS
# ══════════════════════════════════════════════════════════════════════════════

class CreateSessionRequest(BaseModel):
    band_name: str

class JoinSessionRequest(BaseModel):
    band_code: str

class RegisterMemberRequest(BaseModel):
    member_name: str
    instrument:  str
    phone_id:    str
    position:    str = "unknown"


# ══════════════════════════════════════════════════════════════════════════════
# HTTP ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
def health():
    """Quick check that the server is running."""
    return {
        "status":   "ok",
        "service":  "The Sound Engineer.ai",
        "sessions": len(manager.sessions),
    }


@app.post("/session/create")
def create_session(body: CreateSessionRequest):
    """
    Band manager creates a new session before the show.
    Returns a 6-character band code that members type to join.
    """
    session_id, band_code = manager.create_session(body.band_name)
    return {
        "session_id": session_id,
        "band_code":  band_code,
        "band_name":  body.band_name,
        "message":    f"Session created. Share code '{band_code}' with your band.",
    }



@app.post("/session/join")
def join_session(body: JoinSessionRequest):
    """
    Fix #2 + #3 — Member joins using band_code, gets back session_id.
    Flow: join (get session_id) → register → connect WebSocket.
    """
    session_id = manager.get_session_id_by_code(body.band_code)  # Fix #5 — uppercase handled inside
    if not session_id:
        raise HTTPException(status_code=404, detail=f"Band code {body.band_code.upper()} not found")
    info = manager.get_session_info(session_id)
    return {
        "session_id": session_id,
        "band_code":  body.band_code.upper(),
        "band_name":  info.get("session_name"),
        "message":    "Joined successfully. Now call /register.",
    }

@app.post("/session/{session_id}/register")
def register_member(session_id: str, body: RegisterMemberRequest):
    """
    Band member registers their instrument.
    Called when a member joins the session on their phone.
    """
    node = manager.add_node(
        session_id,
        body.member_name,
        body.instrument,
        body.phone_id,
        body.position,
    )
    if node is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "status":      "registered",
        "member_name": body.member_name,
        "instrument":  body.instrument,
        "phone_id":    body.phone_id,
        "freq_range":  node.freq_range,
        "message":     f"{body.member_name} registered as {body.instrument}",
    }


@app.get("/session/{session_id}/status")
def session_status(session_id: str):
    """
    Get full band status — all members, their levels, and recommendations.
    Called by the master phone dashboard.
    """
    if session_id not in manager.sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return manager.get_all_recommendations(session_id)



@app.get("/session/check/{session_id}")
def check_session(session_id: str):
    """Check if a session exists. Used by master page to validate before WS connect."""
    sid = session_id.strip()
    if sid not in manager.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    info = manager.get_session_info(sid)
    return {"exists": True, "band_name": info.get("session_name"), "band_code": info.get("band_code"), "member_count": len(info.get("members", []))}

@app.delete("/session/{session_id}")
def end_session(session_id: str):
    """End the session after the show."""
    success = manager.end_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "ended", "session_id": session_id}


# ══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET — MEMBER PHONE
# Each band member's phone connects here and streams audio
# ══════════════════════════════════════════════════════════════════════════════

@app.websocket("/ws/{session_id}/{phone_id}")
async def member_websocket(
    websocket: WebSocket,
    session_id: str,
    phone_id:   str,
):
    """
    WebSocket endpoint for each band member's phone.

    Flow every 93ms:
    1. Receive raw Float32 PCM bytes from phone mic
    2. Compute FFT
    3. Compute band energy → current_db
    4. Calculate SNR → utility score
    5. Update node frame
    6. Get recommendation
    7. Check feedback risk
    8. Send JSON back to phone
    """
    await websocket.accept()
    print(f"[CONNECTED] phone_id={phone_id} session={session_id[:8]}...")

    # Validate session and node exist
    if session_id not in manager.sessions:
        await websocket.send_text(json.dumps({"error": "Session not found"}))
        await websocket.close()
        return

    node = manager.get_node(session_id, phone_id)
    if node is None:
        await websocket.send_text(json.dumps({"error": "Member not registered. Call /register first."}))
        await websocket.close()
        return

    detector = manager.sessions[session_id]["feedback_detector"]

    # ── Smoothing state ───────────────────────────────────────────────────────
    frame_count   = 0          # total frames received
    action_counts = {}         # how many consecutive frames each action appeared
    last_action   = None       # last confirmed action
    SEND_EVERY    = 10         # send output every N frames (~1 second)
    CONFIRM_AFTER = 5          # only show recommendation if seen 5 times in a row

    try:
        while True:
            # ── Receive audio ─────────────────────────────────────────────
            pcm_bytes = await websocket.receive_bytes()

            # ── FFT analysis ──────────────────────────────────────────────
            fft_result = compute_fft(pcm_bytes, sample_rate=44100)
            if fft_result is None:
                continue

            magnitudes, freqs = fft_result

            # ── Energy and SNR ────────────────────────────────────────────
            low, high  = node.freq_range
            current_db = compute_band_energy(magnitudes, freqs, low, high)
            snr        = calculate_snr(magnitudes, freqs, node.freq_range)

            # ── Update node state ─────────────────────────────────────────
            node.update_frame(magnitudes, freqs, current_db)
            node.update_utility_score(snr)

            # ── Get recommendation ────────────────────────────────────────
            recommendation = node.get_recommendation()

            # ── Check feedback risk ───────────────────────────────────────
            feedback = detector.analyze(node)
            if feedback["risk"]:
                recommendation["feedback_alert"] = feedback
                recommendation["notch_filter"]   = detector.suggest_notch(feedback["freq_hz"])

            # ── Smoothing — only confirm stable recommendations ───────────
            # Extract current action ("cut", "boost", "ok", "feedback")
            if feedback["risk"]:
                current_action = f"feedback_{feedback['freq_hz']}"
            elif recommendation.get("alerts"):
                a = recommendation["alerts"][0]
                current_action = f"{a['type']}_{a['freq_hz']}"
            else:
                current_action = "ok"

            # Count consecutive occurrences of this action
            if current_action == last_action:
                action_counts[current_action] = action_counts.get(current_action, 0) + 1
            else:
                action_counts = {current_action: 1}
                last_action   = current_action

            confirmed = action_counts.get(current_action, 0) >= CONFIRM_AFTER

            # ── Rate limit — send every SEND_EVERY frames ────────────────
            frame_count += 1
            if frame_count % SEND_EVERY != 0:
                continue

            # ── Only send if recommendation is confirmed stable ───────────
            if not confirmed:
                # Send a "monitoring" status so screen doesn't look frozen
                await websocket.send_text(json.dumps({
                    "member":     node.name,
                    "instrument": node.instrument,
                    "status":     node.status,
                    "current_db": round(node.current_db, 1),
                    "message":    "Analysing...",
                    "alerts":     [],
                }, default=str))
                continue

            # ── Send confirmed recommendation ─────────────────────────────
            await websocket.send_text(json.dumps(recommendation, default=str))

    except WebSocketDisconnect:
        manager.remove_node(session_id, phone_id)
        print(f"[DISCONNECTED] phone_id={phone_id} left session {session_id[:8]}...")

    except Exception as e:
        print(f"[ERROR] phone_id={phone_id}: {e}")
        await websocket.close()


# ══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET — MASTER PHONE
# The band manager's phone gets full band status every 500ms
# ══════════════════════════════════════════════════════════════════════════════

@app.websocket("/ws/master/{session_id}")
async def master_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket for the master phone (band manager / sound person).
    Sends full band status every 500ms.
    """
    await websocket.accept()

    # Strip any whitespace/newlines from session_id
    session_id = session_id.strip()
    print(f"[MASTER CONNECTED] session={session_id[:8]}...")

    # Debug — print all active sessions
    print(f"[MASTER DEBUG] Active sessions: {list(manager.sessions.keys())}")

    if session_id not in manager.sessions:
        await websocket.send_text(json.dumps({
            "error": f"Session not found. Active sessions: {len(manager.sessions)}",
            "hint":  "Make sure you copied the full session ID from the member page"
        }))
        await websocket.close()
        return

    # Send immediately on connect so master sees data right away
    result = manager.get_all_recommendations(session_id)
    await websocket.send_text(json.dumps(result, default=str))

    try:
        while True:
            await asyncio.sleep(0.5)
            result = manager.get_all_recommendations(session_id)
            await websocket.send_text(json.dumps(result, default=str))

    except WebSocketDisconnect:
        print(f"[MASTER DISCONNECTED] session={session_id[:8]}...")

    except Exception as e:
        print(f"[MASTER ERROR] {e}")
        await websocket.close()


# ══════════════════════════════════════════════════════════════════════════════
# TEST PAGE
# Open http://localhost:8000 in browser to test mic input
# ══════════════════════════════════════════════════════════════════════════════


@app.get("/master", response_class=HTMLResponse)
def master_page():
    return """
<!DOCTYPE html>
<html>
<head>
  <title>The Sound Engineer.ai — Master</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: monospace; background: #0a0a0a; color: #fff; padding: 1rem; }
    h2 { color: #00ff88; margin-bottom: 1rem; font-size: 1.2rem; }
    .setup { background: #111; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
    input { background: #1a1a1a; color: #fff; border: 1px solid #333; padding: .4rem .8rem;
            font-size: 0.95rem; border-radius: 4px; margin: .2rem; width: 220px; }
    button { background: #00ff88; color: #000; border: none; padding: .5rem 1.2rem;
             font-size: 0.95rem; border-radius: 4px; cursor: pointer; margin: .2rem; font-weight: bold; }
    .band-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 0.8rem; }
    .member-card { background: #111; border-radius: 8px; padding: 1rem; border-left: 4px solid #333; }
    .member-card.ok       { border-left-color: #00ff88; }
    .member-card.alert    { border-left-color: #ffd166; }
    .member-card.critical { border-left-color: #ff4d6a; }
    .member-name { font-size: 1rem; font-weight: bold; color: #fff; }
    .member-inst { font-size: 0.8rem; color: #888; margin-bottom: 0.5rem; }
    .level { font-size: 0.85rem; margin-bottom: 0.4rem; }
    .alert-box { background: #1a1a1a; border-radius: 4px; padding: 0.4rem 0.6rem; margin: 0.3rem 0; font-size: 0.85rem; }
    .cut     { color: #ffd166; }
    .boost   { color: #60a5fa; }
    .ok-txt  { color: #00ff88; }
    .feedback-box { background: #2a0000; border-radius: 4px; padding: 0.4rem 0.6rem;
                    margin: 0.3rem 0; font-size: 0.85rem; color: #ff4d6a; }
    #status { color: #888; font-size: 0.85rem; margin: 0.5rem 0; }
    #band-status { background: #111; padding: 0.6rem 1rem; border-radius: 6px;
                   margin-bottom: 1rem; font-size: 0.9rem; }
  </style>
</head>
<body>
  <h2>🎚️ The Sound Engineer.ai — Master Dashboard</h2>

  <div class="setup">
    <input id="sessionId" placeholder="Paste session ID here"/>
    <button onclick="connect()">Connect</button>
  </div>

  <div id="band-status" style="display:none"></div>
  <p id="status">Not connected</p>
  <div class="band-grid" id="band-grid"></div>

<script>
let ws;

async function connect() {
  const raw = document.getElementById("sessionId").value.trim();
  if (!raw) { alert("Paste session ID"); return; }
  document.getElementById("status").textContent = "🔄 Checking session...";

  // Verify session exists first
  const check = await fetch(`/session/check/${raw}`);
  if (!check.ok) {
    document.getElementById("status").textContent = "❌ Session not found — check ID";
    document.getElementById("band-grid").innerHTML = "<div style='color:#ff4d6a;padding:1rem;background:#111;border-radius:8px;'>Session ID not found.<br><small>Go to the member page, create/join a session, and copy the full Session ID.</small></div>";
    return;
  }
  const info = await check.json();
  const bs = document.getElementById("band-status");
  bs.style.display = "block";
  bs.innerHTML = `<span style="color:#00ff88;font-weight:bold;">🎵 ${info.band_name}</span> &nbsp;|&nbsp; Code: <strong>${info.band_code}</strong> &nbsp;|&nbsp; Members registered: ${info.member_count}`;

  document.getElementById("status").textContent = "🔄 Connecting WebSocket...";
  ws = new WebSocket(`wss://${window.location.host}/ws/master/${raw}`);
  ws.onopen    = () => { document.getElementById("status").textContent = "🟢 Connected — waiting for data..."; };
  ws.onclose   = () => { document.getElementById("status").textContent = "🔴 Disconnected"; };
  ws.onerror   = (e) => { document.getElementById("status").textContent = "❌ Connection error — check session ID"; };
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.error) {
      document.getElementById("status").textContent = "❌ " + data.error;
      document.getElementById("band-grid").innerHTML = "<div style='color:#ff4d6a;padding:1rem;'>" + data.error + "<br><small>" + (data.hint||'') + "</small></div>";
      return;
    }
    document.getElementById("status").textContent = "🟢 Live — updating every 500ms";
    renderBand(data);
  };
}

function renderBand(data) {
  // Band summary bar
  const bs = document.getElementById("band-status");
  bs.style.display = "block";
  const fb = data.feedback || {};
  const anyRisk = fb.any_risk;
  bs.innerHTML = `
    <span style="color:#00ff88;font-weight:bold;">🎵 ${data.band_name || "Band"}</span>
    &nbsp;|&nbsp; Members: ${data.member_count || 0}
    &nbsp;|&nbsp; Feedback: <span style="color:${anyRisk?'#ff4d6a':'#00ff88'};font-weight:bold;">${anyRisk ? '🔴 RISK' : '✅ OK'}</span>
    ${fb.critical_count > 0 ? `&nbsp;|&nbsp; <span style="color:#ff4d6a">${fb.critical_count} CRITICAL</span>` : ''}
  `;

  // Member cards
  const grid = document.getElementById("band-grid");
  grid.innerHTML = "";
  const members = data.members || [];
  if (members.length === 0) {
    grid.innerHTML = "<div style='color:#555;padding:1rem;background:#111;border-radius:8px;'>" +
      "<div style='color:#fff;margin-bottom:0.5rem;'>⏳ Waiting for band members to connect...</div>" +
      "<div style='font-size:0.85rem;'>Share the band code <strong style='color:#00ff88;'>" + (data.band_code||'') + "</strong> with your band members.</div>" +
      "<div style='font-size:0.85rem;margin-top:0.3rem;'>Members open the main page, enter the code, register, and click Start.</div>" +
      "</div>";
    return;
  }

  members.forEach(m => {
    const card = document.createElement("div");
    const st   = m.status || "idle";
    card.className = `member-card ${st}`;

    let alertsHtml = "";
    if (m.alerts && m.alerts.length > 0) {
      m.alerts.forEach(a => {
        alertsHtml += `<div class="alert-box">
          <span class="${a.type}">${a.type==="cut"?"✂️ CUT":"📈 BOOST"} ${a.freq_hz} Hz by ${a.db} dB — Q=${a.q}</span>
        </div>`;
      });
    } else {
      alertsHtml = `<div class="alert-box ok-txt">✅ Balanced</div>`;
    }

    card.innerHTML = `
      <div class="member-name">${m.member}</div>
      <div class="member-inst">${(m.instrument||'').replace(/_/g,' ').toUpperCase()}</div>
      <div class="level">Level: ${m.current_db} dBFS &nbsp;|\&nbsp; 
        <span style="color:${st==='critical'?'#ff4d6a':st==='alert'?'#ffd166':'#00ff88'}">${st.toUpperCase()}</span>
      </div>
      ${alertsHtml}
    `;
    grid.appendChild(card);
  });

  // Feedback alerts at the bottom
  if (fb.alerts && fb.alerts.length > 0) {
    fb.alerts.forEach(a => {
      const card = document.createElement("div");
      card.className = "member-card critical";
      card.innerHTML = `
        <div class="member-name">🔴 FEEDBACK RISK</div>
        <div class="member-inst">${a.member} — ${a.instrument}</div>
        <div class="feedback-box">${a.message}</div>
      `;
      grid.appendChild(card);
    });
  }
}
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def test_page():
    return """
<!DOCTYPE html>
<html>
<head>
  <title>The Sound Engineer.ai — Test</title>
  <style>
    body { font-family: monospace; background: #0a0a0a; color: #00ff88;
           padding: 2rem; max-width: 800px; margin: 0 auto; }
    h2   { color: #fff; }
    button { background: #00ff88; color: #000; border: none;
             padding: .6rem 1.4rem; font-size: 1rem;
             border-radius: 4px; cursor: pointer; margin: .4rem; }
    button:hover { background: #00cc66; }
    pre  { background: #111; padding: 1rem; border-radius: 6px;
           white-space: pre-wrap; font-size: 0.85rem; min-height: 200px; }
    input { background: #111; color: #fff; border: 1px solid #333;
            padding: .4rem .8rem; font-size: 1rem; border-radius: 4px;
            margin: .2rem; width: 200px; }
    .status { margin: .5rem 0; }
    .green  { color: #00ff88; }
    .red    { color: #ff4d6a; }
    .yellow { color: #ffd166; }
  </style>
</head>
<body>
  <h2>🎚️ The Sound Engineer.ai — Live Test</h2>

  <div class="status">
    <strong>Step 1 — Create Session</strong><br>
    <input id="bandName" placeholder="Band name" value="Test Band"/>
    <button onclick="createSession()">Create Session</button>
  </div>

  <div class="status">
    <strong>Step 1b — OR Join with Band Code</strong><br>
    <input id="bandCode" placeholder="Band code e.g. XK9J2L"/>
    <button onclick="joinSession()">Join</button>
  </div>

  <div class="status">
    <strong>Step 2 — Register Your Instrument</strong><br>
    <input id="memberName" placeholder="Your name" value="Ravi"/>
    <select id="instrument" style="background:#111;color:#fff;padding:.4rem;border:1px solid #333;border-radius:4px;">
      <option value="bass_guitar">Bass Guitar</option>
      <option value="electric_guitar_lead">Lead Guitar</option>
      <option value="electric_guitar_rhythm">Rhythm Guitar</option>
      <option value="acoustic_guitar">Acoustic Guitar</option>
      <option value="vocals_male">Vocals (Male)</option>
      <option value="vocals_female">Vocals (Female)</option>
      <option value="backing_vocals">Backing Vocals</option>
      <option value="drums_full_kit">Drums (Full Kit)</option>
      <option value="kick_drum">Kick Drum</option>
      <option value="cajon">Cajon</option>
      <option value="piano">Piano/Keyboard</option>
      <option value="keyboard_synth">Synth/Keys</option>
      <option value="tabla">Tabla</option>
      <option value="sitar">Sitar</option>
      <option value="sarod">Sarod</option>
      <option value="harmonium">Harmonium</option>
      <option value="bansuri">Bansuri</option>
      <option value="trumpet">Trumpet</option>
      <option value="saxophone">Saxophone</option>
      <option value="violin">Violin</option>
      <option value="other">Other</option>
    </select>
    <button onclick="registerMember()">Register</button>
  </div>

  <div class="status">
    <strong>Step 3 — Start Mic</strong><br>
    <button onclick="startMic()">▶ Start</button>
    <button onclick="stopMic()">⏹ Stop</button>
  </div>

  <p id="status" class="green">Status: idle</p>
  <pre id="output">Waiting for analysis...</pre>

<script>
let sessionId = null;
let phoneId   = "phone_" + Math.random().toString(36).substr(2,8);
let ws, ctx, processor, stream;


async function joinSession() {
  const code = document.getElementById('bandCode').value.trim().toUpperCase();
  if (!code) { alert('Enter band code'); return; }
  const res  = await fetch('/session/join', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ band_code: code })
  });
  const data = await res.json();
  if (res.ok) {
    sessionId = data.session_id;
    setStatus('✅ Joined: ' + data.band_name + ' | Code: ' + code, 'green');
    document.getElementById('output').innerHTML = '<div style="color:#00ff88">✅ Joined session! Now register your instrument.</div>';
  } else {
    setStatus('❌ Code not found: ' + code, 'red');
  }
}

async function createSession() {
  const res  = await fetch("/session/create", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ band_name: document.getElementById("bandName").value })
  });
  const data = await res.json();
  sessionId  = data.session_id;
  setStatus(`✅ Session created | Code: ${data.band_code}`, "green");
  document.getElementById("output").innerHTML = `
    <div style="background:#111;padding:1rem;border-radius:6px;">
      <div style="color:#fff;font-size:1rem;margin-bottom:0.5rem;">✅ Session Created!</div>
      <div style="margin:0.4rem 0;">🎵 Band: <strong>${data.band_name}</strong></div>
      <div style="margin:0.4rem 0;">🔑 Band Code: <strong style="color:#00ff88;font-size:1.2rem;">${data.band_code}</strong> <small>(share with band)</small></div>
      <div style="margin:0.4rem 0;">🆔 Session ID: <span id="sidDisplay" style="color:#60a5fa;word-break:break-all;font-size:0.85rem;">${data.session_id}</span></div>
      <button onclick="copyId()" style="margin-top:0.5rem;font-size:0.8rem;padding:0.3rem 0.8rem;">📋 Copy Session ID for Master</button>
    </div>
  `;
}

function copyId() {
  const sid = document.getElementById("sidDisplay");
  if (sid) {
    navigator.clipboard.writeText(sid.textContent);
    setStatus("📋 Session ID copied!", "green");
  }
}

async function registerMember() {
  if (!sessionId) { alert("Create session first"); return; }
  const res  = await fetch(`/session/${sessionId}/register`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      member_name: document.getElementById("memberName").value,
      instrument:  document.getElementById("instrument").value,
      phone_id:    phoneId,
      position:    "stage"
    })
  });
  const data = await res.json();
  setStatus(`✅ ${data.message}`, "green");
  document.getElementById("output").innerHTML = `
    <div style="background:#111;padding:1rem;border-radius:6px;">
      <div style="color:#fff;font-size:1rem;">✅ ${data.message}</div>
      <div style="margin-top:0.5rem;color:#888;font-size:0.85rem;">Session ID: <span style="color:#60a5fa;">${sessionId}</span></div>
      <button onclick="navigator.clipboard.writeText('${sessionId}').then(()=>setStatus('📋 Copied!','green'))" 
              style="margin-top:0.4rem;font-size:0.8rem;padding:0.3rem 0.8rem;">📋 Copy Session ID for Master</button>
      <div style="margin-top:0.5rem;color:#00ff88;">→ Now click ▶ Start to stream audio</div>
    </div>
  `;
}

async function startMic() {
  if (!sessionId) { alert("Create session and register first"); return; }
  stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  ctx    = new AudioContext({ sampleRate: 44100 });
  const src = ctx.createMediaStreamSource(stream);
  processor = ctx.createScriptProcessor(4096, 1, 1);
  src.connect(processor);
  processor.connect(ctx.destination);

  ws = new WebSocket(`wss://${window.location.host}/ws/${sessionId}/${phoneId}`);
  ws.onopen    = () => setStatus("🎙️ Streaming audio...", "green");
  ws.onclose   = () => setStatus("🔴 Disconnected", "red");
  ws.onerror   = () => setStatus("❌ WebSocket error", "red");
  ws.onmessage = (e) => { renderRecommendation(JSON.parse(e.data)); };

  processor.onaudioprocess = (e) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const float32 = e.inputBuffer.getChannelData(0);
    ws.send(float32.buffer);
  };
}

function stopMic() {
  if (processor) processor.disconnect();
  if (stream)    stream.getTracks().forEach(t => t.stop());
  if (ws)        ws.close();
  setStatus("⏹ Stopped", "red");
}

function setStatus(msg, cls) {
  const el = document.getElementById("status");
  el.textContent  = msg;
  el.className    = cls;
}

function renderRecommendation(data) {
  let html = "";
  html += `<div style="font-size:1.1rem;font-weight:bold;color:#fff;margin-bottom:0.5rem;">
    🎵 ${data.member || ""} — ${(data.instrument||'').replace(/_/g,' ').toUpperCase()}
  </div>`;
  const dbColor = (data.current_db||0) > -20 ? "#ffd166" : "#00ff88";
  html += `<div style="margin-bottom:0.5rem;">
    Status: <span style="color:${data.status==='critical'?'#ff0000':data.status==='alert'?'#ff4d6a':'#00ff88'};font-weight:bold;">${(data.status||'').toUpperCase()}</span>
    &nbsp;|&nbsp; Level: <span style="color:${dbColor}">${data.current_db} dBFS</span>
  </div>`;
  if (data.message === "Analysing...") {
    html += "<div style='color:#888;font-style:italic;'>🔍 Analysing audio...</div>";
    document.getElementById("output").innerHTML = html;
    setStatus("🎙️ Listening...", "green"); return;
  }
  if (data.alerts && data.alerts.length > 0) {
    data.alerts.forEach(a => {
      const c = a.type==="cut"?"#ffd166":a.type==="boost"?"#60a5fa":"#ff4d6a";
      html += `<div style="background:#1a1a1a;border-left:4px solid ${c};padding:0.6rem 1rem;margin:0.4rem 0;border-radius:4px;">
        <div style="color:${c};font-weight:bold;font-size:1rem;">${a.type==="cut"?"✂️ CUT":"📈 BOOST"} ${a.freq_hz} Hz by ${a.db} dB — Q=${a.q}</div>
        <div style="color:#ccc;font-size:0.85rem;margin-top:0.2rem;">${a.message}</div>
      </div>`;
    });
    setStatus("⚠️ Action needed", "yellow");
  } else {
    html += "<div style='color:#00ff88;'>✅ Mix sounds balanced</div>";
    setStatus("✅ Mix OK", "green");
  }
  if (data.feedback_alert && data.feedback_alert.risk) {
    html += `<div style="background:#2a0000;border-left:4px solid #ff4d6a;padding:0.6rem 1rem;margin:0.4rem 0;border-radius:4px;">
      <div style="color:#ff4d6a;font-weight:bold;">🔴 FEEDBACK RISK — ${data.feedback_alert.freq_hz} Hz</div>
      ${data.notch_filter?"<div style='color:#ffd166;font-size:0.85rem;'>"+data.notch_filter.message+"</div>":""}
    </div>`;
    setStatus("🔴 FEEDBACK!", "red");
  }
  document.getElementById("output").innerHTML = html;
}
</script>
</body>
</html>
"""


# ══════════════════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("  The Sound Engineer.ai — Server Starting...")
    print("  http://localhost:8000       — Test page")
    print("  http://localhost:8000/docs  — API docs")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)