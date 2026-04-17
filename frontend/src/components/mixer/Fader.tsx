interface FaderProps {
  value: number; // -60 to 0
  onChange: (value: number) => void;
  autoAdjusted?: boolean;
}

export function Fader({ value, onChange, autoAdjusted }: FaderProps) {
  return (
    <div className="flex flex-col items-center gap-1 w-full">
      <div className={`relative w-8 h-48 rounded bg-secondary/50 border ${autoAdjusted ? 'border-neon-cyan/50 glow-cyan' : 'border-border'} flex items-center justify-center`}>
        <input
          type="range"
          min={-60}
          max={0}
          step={0.5}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="absolute w-44 h-2 appearance-none bg-transparent cursor-pointer"
          style={{
            transform: "rotate(-90deg)",
            WebkitAppearance: "none",
          }}
        />
        {/* Track visualization */}
        <div className="absolute bottom-0 w-1 rounded-full bg-muted" style={{ height: '100%' }}>
          <div
            className="absolute bottom-0 w-full rounded-full bg-primary transition-all duration-75"
            style={{ height: `${((value + 60) / 60) * 100}%` }}
          />
        </div>
      </div>
      <span className="font-mono text-xs text-muted-foreground">
        {value.toFixed(1)} dB
      </span>
    </div>
  );
}
