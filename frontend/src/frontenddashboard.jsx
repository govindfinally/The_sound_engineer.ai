import React, { useState, useRef, useEffect } from 'react';

// CONFIG
const BACKEND_URL = 'https://unvictimized-extracellular-charleigh.ngrok-free.dev';
const WS_URL = 'wss://unvictimized-extracellular-charleigh.ngrok-free.dev';

export default function App() {
  const [mode, setMode] = useState('home');
  const [sessionId, setSessionId] = useState('');
  const [bandCode, setBandCode] = useState('');
  const [members, setMembers] = useState([]);
  const [data, setData] = useState(null);
  const [autoMix, setAutoMix] = useState(false);

  const wsRef = useRef(null);

  // ─────────────────────────────────────────────────────────────
  // WEBSOCKET
  // ─────────────────────────────────────────────────────────────
  const connectWS = (sid) => {
    const ws = new WebSocket(`${WS_URL}/ws/session/${sid}`);

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.event === "recommendations_updated") {
        setData(msg.data);
        setMembers(msg.data.members || []);
      }
    };

    wsRef.current = ws;
  };

  // ─────────────────────────────────────────────────────────────
  // AI AUTO MIX LOGIC (CORE)
  // ─────────────────────────────────────────────────────────────
  const computeAutoMix = () => {
    if (!members.length) return {};

    let mix = {};

    members.forEach(m => {
      let level = m.current_db ?? -60;

      // 🎯 RULES (basic AI)
      if (m.instrument.includes("vocals")) {
        mix[m.phone_id] = level + 3; // boost vocals
      } else if (m.instrument.includes("guitar")) {
        mix[m.phone_id] = level - 2;
      } else if (m.instrument.includes("drums")) {
        mix[m.phone_id] = level - 1;
      } else {
        mix[m.phone_id] = level;
      }
    });

    return mix;
  };

  const autoMixLevels = computeAutoMix();

  // ─────────────────────────────────────────────────────────────
  // UI
  // ─────────────────────────────────────────────────────────────
  if (mode === 'home') {
    return (
      <div style={styles.home}>
        <h1>🎧 the_sound_engineer.ai</h1>
        <button onClick={() => setMode('dashboard')}>Open Mixer</button>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────
  // DASHBOARD (ABLETON STYLE)
  // ─────────────────────────────────────────────────────────────
  return (
    <div style={styles.container}>
      
      {/* HEADER */}
      <div style={styles.header}>
        <h2>MIXER CONSOLE</h2>

        <button
          style={autoMix ? styles.autoOn : styles.autoOff}
          onClick={() => setAutoMix(!autoMix)}
        >
          {autoMix ? "🤖 AUTO MIX ON" : "AUTO MIX"}
        </button>
      </div>

      {/* MIXER STRIPS */}
      <div style={styles.mixer}>
        {members.map((m, i) => {
          const db = m.current_db ?? -60;
          const finalLevel = autoMix ? autoMixLevels[m.phone_id] : db;

          return (
            <div key={i} style={styles.channel}>

              {/* NAME */}
              <div style={styles.name}>{m.name}</div>

              {/* LEVEL METER */}
              <div style={styles.meter}>
                <div
                  style={{
                    ...styles.meterFill,
                    height: `${Math.max(5, (finalLevel + 60) * 1.5)}%`,
                    background:
                      finalLevel > -10 ? "#ff4d4d" :
                      finalLevel > -25 ? "#ffb347" :
                      "#00ffcc"
                  }}
                />
              </div>

              {/* FADER */}
              <input
                type="range"
                min="-60"
                max="0"
                value={finalLevel}
                readOnly
                style={styles.fader}
              />

              {/* DB VALUE */}
              <div style={styles.db}>{finalLevel.toFixed(1)} dB</div>

              {/* FEEDBACK ALERT */}
              {data?.feedback?.map((f, idx) =>
                f.member === m.name ? (
                  <div key={idx} style={styles.feedback}>
                    ⚠ {f.freqs_hz.join(",")} Hz
                  </div>
                ) : null
              )}
            </div>
          );
        })}

        {/* MASTER CHANNEL */}
        <div style={styles.master}>
          <h3>MASTER</h3>

          <div style={styles.masterMeter}>
            <div style={{
              ...styles.masterFill,
              height: `${members.length * 10}%`
            }} />
          </div>

          <div style={styles.masterText}>
            Band Balance: {members.length > 0 ? "LIVE" : "IDLE"}
          </div>
        </div>

      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// STYLES (ABLETON DARK)
// ─────────────────────────────────────────────────────────────
const styles = {
  home: {
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    background: "#0a0e27",
    color: "#fff"
  },

  container: {
    height: "100vh",
    background: "#0a0e27",
    color: "#fff",
    display: "flex",
    flexDirection: "column"
  },

  header: {
    padding: "10px 20px",
    borderBottom: "1px solid #222",
    display: "flex",
    justifyContent: "space-between"
  },

  mixer: {
    flex: 1,
    display: "flex",
    padding: 20,
    gap: 10,
    overflowX: "auto"
  },

  channel: {
    width: 100,
    background: "#111",
    padding: 10,
    borderRadius: 8,
    display: "flex",
    flexDirection: "column",
    alignItems: "center"
  },

  name: {
    fontSize: 12,
    marginBottom: 10
  },

  meter: {
    width: 20,
    height: 150,
    background: "#222",
    display: "flex",
    alignItems: "flex-end"
  },

  meterFill: {
    width: "100%",
    transition: "0.1s"
  },

  fader: {
    writingMode: "bt-lr",
    height: 120
  },

  db: {
    fontSize: 12,
    marginTop: 5
  },

  feedback: {
    color: "red",
    fontSize: 10,
    marginTop: 5
  },

  master: {
    width: 120,
    background: "#222",
    padding: 10,
    textAlign: "center"
  },

  masterMeter: {
    height: 200,
    background: "#111",
    display: "flex",
    alignItems: "flex-end"
  },

  masterFill: {
    width: "100%",
    background: "#00ffcc"
  },

  masterText: {
    fontSize: 12,
    marginTop: 10
  },

  autoOn: {
    background: "#00ffcc",
    border: "none",
    padding: "6px 12px"
  },

  autoOff: {
    background: "#444",
    border: "none",
    padding: "6px 12px",
    color: "#fff"
  }
};