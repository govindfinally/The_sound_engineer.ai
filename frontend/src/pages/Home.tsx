import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden">
      {/* Background grid effect */}
      <div className="absolute inset-0 opacity-[0.03]" style={{
        backgroundImage: 'linear-gradient(hsl(var(--primary)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--primary)) 1px, transparent 1px)',
        backgroundSize: '40px 40px',
      }} />

      <div className="relative z-10 flex flex-col items-center gap-10">
        {/* Branding */}
        <div className="text-center space-y-3">
          <h1 className="text-5xl md:text-7xl font-black tracking-tight text-glow-cyan">
            <span className="text-primary">the_sound_engineer</span>
            <span className="text-neon-green">.ai</span>
          </h1>
          <p className="text-muted-foreground text-lg font-light tracking-wide">
            AI-Powered Real-Time Sound Mixing for Live Bands
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4">
          <button
            onClick={() => navigate("/leader")}
            className="px-8 py-4 rounded-lg bg-primary text-primary-foreground font-semibold text-lg glow-cyan hover:scale-105 transition-all"
          >
            🎛️ Start Session (Leader)
          </button>
          <button
            onClick={() => navigate("/join")}
            className="px-8 py-4 rounded-lg border border-primary/40 text-foreground font-semibold text-lg hover:bg-primary/10 hover:border-primary/60 transition-all"
          >
            🎵 Join Band (Member)
          </button>
        </div>

        {/* Subtle tagline */}
        <p className="text-xs text-muted-foreground/60 font-mono tracking-widest uppercase">
          Spotify × Ableton × AI Engineer
        </p>
      </div>
    </div>
  );
}
