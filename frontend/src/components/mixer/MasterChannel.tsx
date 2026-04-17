import { VUMeter } from "./VUMeter";

interface MasterChannelProps {
  level: number;
  balanceScore: number;
  clarityScore: number;
  autoMix: boolean;
  onAutoMixToggle: () => void;
}

function ScoreRing({ label, score }: { label: string; score: number }) {
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score > 70 ? 'text-neon-green' : score > 40 ? 'text-neon-amber' : 'text-neon-red';

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative w-16 h-16">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r={radius} fill="none" stroke="hsl(var(--secondary))" strokeWidth="3" />
          <circle
            cx="32" cy="32" r={radius} fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className={`${color} transition-all duration-300`}
          />
        </svg>
        <div className={`absolute inset-0 flex items-center justify-center font-mono text-sm font-bold ${color}`}>
          {score}
        </div>
      </div>
      <span className="text-[10px] text-muted-foreground font-mono uppercase tracking-wider">{label}</span>
    </div>
  );
}

export function MasterChannel({ level, balanceScore, clarityScore, autoMix, onAutoMixToggle }: MasterChannelProps) {
  return (
    <div className="flex flex-col items-center gap-4 p-4 rounded-lg border border-primary/30 bg-card/90 backdrop-blur-sm min-w-[140px] glow-cyan">
      <div className="text-xs font-bold uppercase tracking-widest text-primary font-mono">Master</div>

      {/* Stereo VU */}
      <div className="flex gap-2">
        <VUMeter level={level} height={180} />
        <VUMeter level={level - 2} height={180} />
      </div>

      <div className="font-mono text-sm text-foreground">
        {level.toFixed(1)} dB
      </div>

      {/* Scores */}
      <div className="flex gap-3">
        <ScoreRing label="Balance" score={balanceScore} />
        <ScoreRing label="Clarity" score={clarityScore} />
      </div>

      {/* Auto Mix Toggle */}
      <button
        onClick={onAutoMixToggle}
        className={`w-full py-2 px-4 rounded font-mono text-xs font-bold uppercase tracking-wider transition-all ${
          autoMix
            ? 'bg-primary text-primary-foreground glow-cyan animate-pulse-glow'
            : 'bg-secondary text-muted-foreground hover:bg-secondary/80'
        }`}
      >
        {autoMix ? '⚡ Auto Mix ON' : 'Auto Mix OFF'}
      </button>
    </div>
  );
}
