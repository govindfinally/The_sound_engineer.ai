interface WaveformVisualizerProps {
  data: number[];
  width?: number;
  height?: number;
}

export function WaveformVisualizer({ data, width = 120, height = 40 }: WaveformVisualizerProps) {
  const barWidth = width / data.length;

  return (
    <div className="flex items-end gap-[1px] overflow-hidden" style={{ width, height }}>
      {data.map((v, i) => (
        <div
          key={i}
          className="bg-primary/60 rounded-t-[1px] transition-all duration-75"
          style={{
            width: barWidth - 1,
            height: `${Math.max(2, v * height)}px`,
          }}
        />
      ))}
    </div>
  );
}
