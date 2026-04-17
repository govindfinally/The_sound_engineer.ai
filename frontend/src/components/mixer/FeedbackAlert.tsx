interface FeedbackAlertProps {
  frequencies: number[];
}

export function FeedbackAlert({ frequencies }: FeedbackAlertProps) {
  if (frequencies.length === 0) return null;

  return (
    <div className="flex flex-col gap-1">
      {frequencies.map((freq) => (
        <div
          key={freq}
          className="flex items-center gap-1 px-2 py-0.5 rounded bg-neon-red/20 border border-neon-red/40 text-neon-red text-[10px] font-mono animate-pulse-glow"
        >
          <span>⚠</span>
          <span>{freq} Hz</span>
        </div>
      ))}
    </div>
  );
}
