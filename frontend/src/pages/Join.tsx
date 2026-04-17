import { useState } from "react";

const BACKEND_URL = "https://unvictimized-extracellular-charleigh.ngrok-free.dev";

export default function Join() {
  const [bandCode, setBandCode] = useState("");
  const [name, setName] = useState("");
  const [instrument, setInstrument] = useState("");
  const [loading, setLoading] = useState(false);

  const joinSession = async () => {
    if (!bandCode || !name || !instrument) {
      alert("Fill all fields");
      return;
    }

    // ✅ persistent phone ID
    let phoneId = localStorage.getItem("phone_id");
    if (!phoneId) {
      phoneId = Math.random().toString(36).substring(7);
      localStorage.setItem("phone_id", phoneId);
    }

    try {
      setLoading(true);

      const url = `${BACKEND_URL}/session/join?band_code=${encodeURIComponent(
        bandCode
      )}&member_name=${encodeURIComponent(
        name
      )}&instrument=${encodeURIComponent(
        instrument
      )}&phone_id=${phoneId}&position=front`;

      console.log("JOIN URL:", url);

      const res = await fetch(url, { method: "POST" });

      const text = await res.text();
      console.log("RAW RESPONSE:", text);

      const data = JSON.parse(text);
      console.log("JOIN DATA:", data);

      if (!data.session_id) {
        alert("Join failed. Check band code.");
        return;
      }

      // ✅ redirect properly
      window.location.href = `/mixer/${data.session_id}`;

    } catch (err) {
      console.error("JOIN ERROR:", err);
      alert("Error joining session");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <h1>Join Band</h1>

      <input
        placeholder="Band Code"
        value={bandCode}
        onChange={(e) => setBandCode(e.target.value)}
        style={styles.input}
      />

      <input
        placeholder="Your Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        style={styles.input}
      />

      <input
        placeholder="Instrument"
        value={instrument}
        onChange={(e) => setInstrument(e.target.value)}
        style={styles.input}
      />

      <button onClick={joinSession} style={styles.button}>
        {loading ? "Joining..." : "Join"}
      </button>
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
    gap: "15px",
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
    cursor: "pointer",
    borderRadius: "6px",
  },
};