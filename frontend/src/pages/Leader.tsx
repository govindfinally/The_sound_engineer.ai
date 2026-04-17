import { useState } from "react";

const BACKEND_URL = "https://unvictimized-extracellular-charleigh.ngrok-free.dev";

export default function Leader() {
  const [bandName, setBandName] = useState("");
  const [bandCode, setBandCode] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [loading, setLoading] = useState(false);

  const createSession = async () => {
    if (!bandName) {
      alert("Enter band name");
      return;
    }

    try {
      setLoading(true);

      const res = await fetch(
        `${BACKEND_URL}/session/create?band_name=${encodeURIComponent(bandName)}`,
        { method: "POST" }
      );

      const data = await res.json();
      console.log("SESSION DATA:", data);

      if (!data.session_id) {
        alert("Failed to create session");
        return;
      }

      // ✅ store BOTH
      setBandCode(data.band_code);
      setSessionId(data.session_id);

    } catch (err) {
      console.error(err);
      alert("Error creating session");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <h1>Create Band Session</h1>

      <input
        type="text"
        placeholder="Enter Band Name"
        value={bandName}
        onChange={(e) => setBandName(e.target.value)}
        style={styles.input}
      />

      <button onClick={createSession} style={styles.button}>
        {loading ? "Creating..." : "Create Session"}
      </button>

      {/* ✅ SHOW BAND CODE */}
      {bandCode && (
        <div style={styles.codeBox}>
          <p>Band Code:</p>
          <h2>{bandCode}</h2>

          {/* ✅ NAVIGATE BUTTON */}
          <button
            style={styles.startBtn}
            onClick={() => {
              window.location.href = `/mixer/${sessionId}`;
            }}
          >
            Go to Mixer 🎚️
          </button>
        </div>
      )}
    </div>
  );
}

const styles: any = {
  container: {
    height: "100vh",
    background: "#0a0e27",
    color: "#fff",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    gap: "20px",
  },
  input: {
    padding: "10px",
    width: "250px",
    borderRadius: "6px",
    border: "none",
  },
  button: {
    padding: "10px 20px",
    background: "#00ffcc",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
  },
  codeBox: {
    marginTop: "20px",
    textAlign: "center",
  },
  startBtn: {
    marginTop: "10px",
    padding: "10px 20px",
    background: "#ffb347",
    border: "none",
    cursor: "pointer",
  },
};