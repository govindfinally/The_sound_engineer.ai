import React, { useState, useEffect, useRef } from 'react';

const BACKEND_URL = 'http://127.0.0.1:8000';
const WS_URL = 'ws://127.0.0.1:8000';

export default function LiveMixDashboard() {
  const [mode, setMode] = useState('home'); // home, session, dashboard
  const [bandName, setBandName] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [bandCode, setBandCode] = useState('');
  const [members, setMembers] = useState([]);
  const [recommendations, setRecommendations] = useState(null);
  const wsRef = useRef(null);

  
  const createSession = async () => {
    if (!bandName.trim()) return;
    try {
      const res = await fetch(`${BACKEND_URL}/session/create?band_name=${encodeURIComponent(bandName)}`);
      const data = await res.json();
      if (data.success) {
        setSessionId(data.session_id);
        setBandCode(data.band_code);
        setMode('session');
        connectWebSocket(data.session_id);
      }
    } catch (e) {
      console.error('Create session error:', e);
    }
  };


  const connectWebSocket = (sid) => {
    if (wsRef.current) wsRef.current.close();
    const ws = new WebSocket(`${WS_URL}/ws/session/${sid}`);

    ws.onopen = () => console.log('WebSocket connected');
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.event === 'recommendations_updated') {
        setRecommendations(msg.data);
        setMembers(msg.data.members || []);
      } else if (msg.event === 'member_joined') {
        console.log('Member joined:', msg.member);
      }
    };
    ws.onerror = (e) => console.error('WebSocket error:', e);
    ws.onclose = () => console.log('WebSocket disconnected');

    wsRef.current = ws;
  };

  const sendUpdate = (phoneId, dbLevel, feedback = {}) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'update_level',
        phone_id: phoneId,
        db_level: dbLevel,
        feedback,
      }));
    }
  };

  useEffect(() => {
    if (mode === 'dashboard' && members.length > 0) {
      const interval = setInterval(() => {
        members.forEach((m) => {
          const randomDb = Math.random() * 40 - 60;
          sendUpdate(m.phone_id, randomDb);
        });
      }, 1500);
      return () => clearInterval(interval);
    }
  }, [mode, members]);


  if (mode === 'home') {
    return (
      <div style={styles.container}>
        <style>{css}</style>
        <div style={styles.hero}>
          <div style={styles.logo}>♪ the sound engineer .ai</div>
          <p style={styles.tagline}>Real-time AI Sound Engineering for Your Band</p>
          
          <div style={styles.inputGroup}>
            <input
              type="text"
              placeholder="Enter your band name..."
              value={bandName}
              onChange={(e) => setBandName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && createSession()}
              style={styles.input}
            />
            <button onClick={createSession} style={styles.ctaButton}>
              START SESSION
            </button>
          </div>

          <p style={styles.hint}>Each band member will register from their own phone</p>
        </div>
      </div>
    );
  }

  if (mode === 'session') {
    return (
      <div style={styles.container}>
        <style>{css}</style>
        <div style={styles.sessionSetup}>
          <h1 style={styles.heading}>{bandName}</h1>
          <div style={styles.codeDisplay}>
            <p style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#999' }}>BAND CODE</p>
            <div style={styles.codeBig}>{bandCode}</div>
            <p style={{ margin: '12px 0 0 0', fontSize: '12px', color: '#666' }}>
              📱 Share this code with band members
            </p>
          </div>

          <button
            onClick={() => setMode('dashboard')}
            style={styles.launchButton}
          >
            LAUNCH DASHBOARD →
          </button>

          <button
            onClick={() => {
              setMode('home');
              setBandName('');
              setSessionId('');
              setBandCode('');
            }}
            style={styles.backButton}
          >
            ← Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.dashContainer}>
      <style>{css}</style>
      
      {/* HEADER */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.dashTitle}>LIVE CONTROL</h1>
          <p style={styles.dashSubtitle}>{bandName}</p>
        </div>
        <div style={styles.headerStats}>
          <div style={styles.stat}>
            <span style={styles.statLabel}>Code</span>
            <span style={styles.statValue}>{bandCode}</span>
          </div>
          <div style={styles.stat}>
            <span style={styles.statLabel}>Members</span>
            <span style={styles.statValue}>{members.length}</span>
          </div>
        </div>
      </div>

      {/* MEMBERS GRID */}
      <div style={styles.membersGrid}>
        {members.length === 0 ? (
          <div style={styles.emptyState}>
            <p style={{ fontSize: '14px', color: '#aaa', margin: 0 }}>
              Waiting for band members to join...
            </p>
          </div>
        ) : (
          members.map((m, idx) => (
            <MemberCard key={idx} member={m} onUpdate={sendUpdate} />
          ))
        )}
      </div>

      {/* FEEDBACK PANEL */}
      {recommendations && (
        <div style={styles.feedbackPanel}>
          <h3 style={styles.feedbackTitle}>BAND FEEDBACK</h3>
          {recommendations.feedback && (
            <div style={styles.feedbackContent}>
              <p style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#ddd' }}>
                {recommendations.feedback.summary || 'All systems nominal'}
              </p>
            </div>
          )}
        </div>
      )}

      {/* FOOTER */}
      <div style={styles.footer}>
        <button
          onClick={() => {
            if (wsRef.current) wsRef.current.close();
            setMode('home');
            setBandName('');
            setSessionId('');
            setBandCode('');
            setMembers([]);
          }}
          style={styles.endButton}
        >
          END SESSION
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// MEMBER CARD COMPONENT
// ─────────────────────────────────────────────────────────────────────────

function MemberCard({ member, onUpdate }) {
  const [db, setDb] = useState(member.current_db || -60);

  const updateLevel = (newDb) => {
    setDb(newDb);
    onUpdate(member.phone_id, newDb);
  };

  const statusColor = {
    idle: '#555',
    active: '#4ade80',
    warning: '#facc15',
    critical: '#ef4444',
  }[member.status] || '#666';

  const dbPercent = Math.max(0, Math.min(100, (db + 60) / 60 * 100));

  return (
    <div style={{ ...styles.memberCard, borderLeftColor: statusColor }}>
      {/* NAME & INSTRUMENT */}
      <div style={styles.memberHeader}>
        <h3 style={styles.memberName}>{member.member_name}</h3>
        <span style={styles.instrument}>{member.instrument}</span>
      </div>

      {/* STATUS INDICATOR */}
      <div style={{ ...styles.statusBadge, backgroundColor: statusColor }}>
        {member.status.toUpperCase()}
      </div>

      {/* dB LEVEL METER */}
      <div style={styles.levelMeter}>
        <div style={styles.meterLabel}>
          <span>dB</span>
          <span style={styles.meterValue}>{db.toFixed(1)}</span>
        </div>
        <div style={styles.meterBar}>
          <div style={{
            ...styles.meterFill,
            width: `${dbPercent}%`,
            backgroundColor: statusColor,
          }} />
        </div>
      </div>

      {/* SLIDER CONTROL */}
      <input
        type="range"
        min="-80"
        max="0"
        step="0.5"
        value={db}
        onChange={(e) => updateLevel(parseFloat(e.target.value))}
        style={styles.slider}
      />

      {/* EQ RECOMMENDATION */}
      {member.eq_recommendation && (
        <div style={styles.eqBox}>
          <p style={styles.eqLabel}>EQ RECOMMENDATION</p>
          {member.eq_recommendation.type === 'notch' ? (
            <>
              <p style={styles.eqValue}>
                🎯 Notch @ {member.eq_recommendation.center_freq_hz} Hz
              </p>
              <p style={styles.eqSmall}>Q: {member.eq_recommendation.bandwidth_q} | Gain: {member.eq_recommendation.gain_db} dB</p>
              <p style={styles.eqReason}>{member.eq_recommendation.reason}</p>
            </>
          ) : (
            <p style={styles.eqValue}>✓ No feedback detected</p>
          )}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// STYLES
// ─────────────────────────────────────────────────────────────────────────

const styles = {
  container: {
    minHeight: '100vh',
    background: '#0a0e27',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: "'Inter', sans-serif",
    padding: '20px',
  },
  hero: {
    maxWidth: '500px',
    textAlign: 'center',
  },
  logo: {
    fontSize: '48px',
    fontWeight: '900',
    color: '#00d4ff',
    marginBottom: '16px',
    letterSpacing: '-2px',
    fontFamily: "'Space Mono', monospace",
  },
  tagline: {
    fontSize: '16px',
    color: '#aaa',
    margin: '0 0 40px 0',
    lineHeight: '1.6',
  },
  inputGroup: {
    display: 'flex',
    gap: '12px',
    marginBottom: '24px',
  },
  input: {
    flex: 1,
    padding: '14px 16px',
    fontSize: '14px',
    background: '#1a1f3a',
    border: '2px solid #333',
    borderRadius: '6px',
    color: '#fff',
    outline: 'none',
  },
  ctaButton: {
    padding: '14px 24px',
    fontSize: '13px',
    fontWeight: 'bold',
    background: 'linear-gradient(135deg, #00d4ff, #0099ff)',
    color: '#000',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    letterSpacing: '1px',
  },
  hint: {
    fontSize: '12px',
    color: '#666',
    margin: 0,
  },
  sessionSetup: {
    maxWidth: '400px',
    textAlign: 'center',
  },
  heading: {
    fontSize: '32px',
    color: '#fff',
    margin: '0 0 32px 0',
    fontWeight: 'bold',
  },
  codeDisplay: {
    background: '#1a1f3a',
    border: '2px solid #00d4ff',
    borderRadius: '8px',
    padding: '24px',
    marginBottom: '32px',
  },
  codeBig: {
    fontSize: '48px',
    fontWeight: '900',
    color: '#00d4ff',
    fontFamily: "'Space Mono', monospace",
    letterSpacing: '2px',
    margin: '8px 0',
  },
  launchButton: {
    width: '100%',
    padding: '16px',
    fontSize: '14px',
    fontWeight: 'bold',
    background: '#00d4ff',
    color: '#000',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    marginBottom: '12px',
    letterSpacing: '1px',
  },
  backButton: {
    width: '100%',
    padding: '12px',
    fontSize: '13px',
    background: 'transparent',
    color: '#aaa',
    border: '1px solid #444',
    borderRadius: '6px',
    cursor: 'pointer',
  },
  dashContainer: {
    minHeight: '100vh',
    background: '#0a0e27',
    display: 'flex',
    flexDirection: 'column',
    fontFamily: "'Inter', sans-serif",
  },
  header: {
    padding: '24px 32px',
    borderBottom: '2px solid #1a1f3a',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dashTitle: {
    fontSize: '28px',
    fontWeight: 'bold',
    color: '#00d4ff',
    margin: '0 0 4px 0',
    letterSpacing: '2px',
    fontFamily: "'Space Mono', monospace",
  },
  dashSubtitle: {
    fontSize: '14px',
    color: '#888',
    margin: 0,
  },
  headerStats: {
    display: 'flex',
    gap: '24px',
  },
  stat: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  statLabel: {
    fontSize: '11px',
    color: '#666',
    textTransform: 'uppercase',
    letterSpacing: '1px',
  },
  statValue: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#00d4ff',
  },
  membersGrid: {
    flex: 1,
    padding: '32px',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
    gap: '20px',
    overflow: 'auto',
  },
  emptyState: {
    gridColumn: '1 / -1',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '300px',
  },
  memberCard: {
    background: '#1a1f3a',
    border: '2px solid #333',
    borderLeftWidth: '6px',
    borderRadius: '8px',
    padding: '20px',
    transition: 'all 0.3s ease',
  },
  memberHeader: {
    marginBottom: '12px',
  },
  memberName: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#fff',
    margin: '0 0 4px 0',
  },
  instrument: {
    fontSize: '12px',
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  statusBadge: {
    display: 'inline-block',
    fontSize: '10px',
    fontWeight: 'bold',
    color: '#fff',
    padding: '4px 8px',
    borderRadius: '4px',
    marginBottom: '12px',
    letterSpacing: '0.5px',
  },
  levelMeter: {
    marginBottom: '16px',
  },
  meterLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '12px',
    color: '#999',
    marginBottom: '6px',
  },
  meterValue: {
    color: '#00d4ff',
    fontWeight: 'bold',
    fontFamily: "'Space Mono', monospace",
  },
  meterBar: {
    height: '8px',
    background: '#0a0e27',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  meterFill: {
    height: '100%',
    transition: 'width 0.15s ease',
  },
  slider: {
    width: '100%',
    marginBottom: '16px',
    cursor: 'pointer',
  },
  eqBox: {
    background: '#0f1428',
    border: '1px solid #00d4ff',
    borderRadius: '6px',
    padding: '12px',
    fontSize: '12px',
  },
  eqLabel: {
    margin: '0 0 6px 0',
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    fontSize: '10px',
  },
  eqValue: {
    margin: '4px 0',
    color: '#00d4ff',
    fontWeight: 'bold',
    fontFamily: "'Space Mono', monospace",
  },
  eqSmall: {
    margin: '4px 0',
    color: '#999',
    fontSize: '11px',
  },
  eqReason: {
    margin: '6px 0 0 0',
    color: '#aaa',
    fontSize: '11px',
    fontStyle: 'italic',
  },
  feedbackPanel: {
    padding: '20px 32px',
    borderTop: '2px solid #1a1f3a',
    background: '#0f1428',
  },
  feedbackTitle: {
    fontSize: '14px',
    fontWeight: 'bold',
    color: '#00d4ff',
    margin: '0 0 12px 0',
    letterSpacing: '1px',
    textTransform: 'uppercase',
  },
  feedbackContent: {
    display: 'flex',
    gap: '12px',
  },
  footer: {
    padding: '20px 32px',
    borderTop: '2px solid #1a1f3a',
    display: 'flex',
    gap: '12px',
  },
  endButton: {
    flex: 1,
    padding: '12px',
    fontSize: '13px',
    fontWeight: 'bold',
    background: '#ef4444',
    color: '#fff',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    letterSpacing: '0.5px',
  },
};

const css = `
  * {
    box-sizing: border-box;
  }

  input[type="range"] {
    width: 100%;
    height: 6px;
    border-radius: 3px;
    background: #0a0e27;
    outline: none;
    -webkit-appearance: none;
    appearance: none;
  }

  input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #00d4ff;
    cursor: pointer;
    box-shadow: 0 0 8px rgba(0, 212, 255, 0.5);
  }

  input[type="range"]::-moz-range-thumb {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #00d4ff;
    cursor: pointer;
    border: none;
    box-shadow: 0 0 8px rgba(0, 212, 255, 0.5);
  }

  input[type="text"]:focus {
    border-color: #00d4ff !important;
    box-shadow: 0 0 12px rgba(0, 212, 255, 0.3);
  }

  button:hover {
    transform: translateY(-2px);
    transition: all 0.2s ease;
  }

  @media (max-width: 768px) {
    input[type="range"] {
      height: 8px;
    }

    input[type="range"]::-webkit-slider-thumb {
      width: 16px;
      height: 16px;
    }

    input[type="range"]::-moz-range-thumb {
      width: 16px;
      height: 16px;
    }
  }
`;