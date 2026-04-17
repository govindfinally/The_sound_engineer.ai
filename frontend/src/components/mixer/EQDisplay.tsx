interface EQDisplayProps {
  eq: { freq: number; gain: number; q: number }[];
}

export function EQDisplay({ eq }: EQDisplayProps) {
  return (
    <div className="space-y-1">
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-mono">EQ</span>
      {eq.map((band, i) => (
        <div key={i} className="flex items-center gap-1 text-[10px] font-mono text-foreground/80">
          <span className="text-primary">{band.freq}Hz</span>
          <span className={band.gain >= 0 ? 'text-neon-green' : 'text-neon-red'}>
            {band.gain >= 0 ? '+' : ''}{band.gain.toFixed(1)}dB
          </span>
          <span className="text-muted-foreground">Q{band.q.toFixed(1)}</span>
        </div>
      ))}
    </div>
  );
}
