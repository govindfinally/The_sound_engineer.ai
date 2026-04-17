import { useMemo } from "react";

interface VUMeterProps {
  level: number; // -60 to 0 dB
  height?: number;
}

export function VUMeter({ level, height = 200 }: VUMeterProps) {
  const percentage = useMemo(() => {
    const clamped = Math.max(-60, Math.min(0, level));
    return ((clamped + 60) / 60) * 100;
  }, [level]);

  const segments = 20;
  const activeSegments = Math.round((percentage / 100) * segments);

  return (
    <div className="flex flex-col-reverse gap-[2px] w-6" style={{ height }}>
      {Array.from({ length: segments }, (_, i) => {
        const isActive = i < activeSegments;
        const ratio = i / segments;
        let colorClass = "bg-neon-green/20";
        if (isActive) {
          if (ratio > 0.85) colorClass = "bg-neon-red shadow-[0_0_6px_hsl(var(--neon-red)/0.5)]";
          else if (ratio > 0.65) colorClass = "bg-neon-amber shadow-[0_0_4px_hsl(var(--neon-amber)/0.3)]";
          else colorClass = "bg-neon-green shadow-[0_0_4px_hsl(var(--neon-green)/0.3)]";
        }
        return (
          <div
            key={i}
            className={`w-full rounded-[1px] transition-all duration-75 ${colorClass}`}
            style={{ height: `${100 / segments}%` }}
          />
        );
      })}
    </div>
  );
}
