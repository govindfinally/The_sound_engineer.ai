import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

const WS_URL = "wss://unvictimized-extracellular-charleigh.ngrok-free.dev";

export default function Mixer() {
  const { sessionId } = useParams();

  const [members, setMembers] = useState<any[]>([]);
  const [data, setData] = useState<any>(null);

  const wsRef = useRef<WebSocket | null>(null);

  // ─────────────────────────────────────────────
  // CONNECT WEBSOCKET
  // ─────────────────────────────────────────────
  useEffect(() => {
    if (!sessionId) return;

    console.log("Connecting to:", sessionId);

    const ws = new WebSocket(`${WS_URL}/ws/session/${sessionId}`);

    ws.onopen = () => console.log("✅ WS CONNECTED");
    ws.onerror = (e) => console.log("❌ WS ERROR", e);
    ws.onclose = () => console.log("❌ WS CLOSED");

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      console.log("DATA:", msg);

      if (msg.event === "recommendations_updated") {
        setData(msg.data);
        setMembers(msg.data.members || []);
      }
    };

    wsRef.current = ws;

    return () => ws.close();
  }, [sessionId]);

  // ─────────────────────────────────────────────
  // FAKE AUDIO STREAM (IMPORTANT)
  // ─────────────────────────────────────────────
  useEffect(() => {
    const interval = setInterval(() => {
      if (!wsRef.current || members.length === 0) return;

      members.forEach((m) => {
        wsRef.current?.send(
          JSON.stringify({
            type: "update_level",
            phone_id: m.phone_id,
            db_level: -20 + Math.random() * 10,
            feedback: {},
          })
        );
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [members]);

  // ─────────────────────────────────────────────
  // UI
  // ─────────────────────────────────────────────
  return (
    <div style={styles.container}>
      <h1>Mixer Console</h1>
      <p>Session: {sessionId}</p>

      <div style={styles.mixer}>
        {members.length === 0 ? (
          <p>No members yet</p>
        ) : (
          members.map((m, i) => {
            const db = m.current_db ?? -60;

            return (
              <div key={i} style={styles.channel}>
                <div style={styles.name}>
                  {m.name || "Unknown"}
                </div>

                <div style={styles.instrument}>
                  {m.instrument}
                </div>

                {/* LEVEL METER */}
                <div style={styles.meter}>
                  <div
                    style={{
                      ...styles.fill,
                      height: `${Math.max(5, (db + 60) * 1.5)}%`,
                    }}
                  />
                </div>

                <div style={styles.db}>
                  {db.toFixed(1)} dB
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// STYLES
// ─────────────────────────────────────────────
const styles: any = {
  container: {
    height: "100vh",
    background: "#0a0e27",
    color: "#fff",
    padding: "20px",
  },

  mixer: {
    display: "flex",
    gap: "20px",
    marginTop: "20px",
  },

  channel: {
    width: "100px",
    background: "#111",
    padding: "10px",
    borderRadius: "8px",
    textAlign: "center",
  },

  name: {
    fontSize: "12px",
    marginBottom: "5px",
  },

  instrument: {
    fontSize: "10px",
    color: "#aaa",
    marginBottom: "10px",
  },

  meter: {
    height: "150px",
    background: "#222",
    display: "flex",
    alignItems: "flex-end",
  },

  fill: {
    width: "100%",
    background: "#00ffcc",
  },

  db: {
    fontSize: "12px",
    marginTop: "10px",
  },
};