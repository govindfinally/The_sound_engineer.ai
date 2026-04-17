import type { Member } from "@/lib/mockWebSocket";
import { VUMeter } from "./VUMeter";
import { Fader } from "./Fader";
import { WaveformVisualizer } from "./WaveformVisualizer";
import { EQDisplay } from "./EQDisplay";
import { FeedbackAlert } from "./FeedbackAlert";

interface ChannelStripProps {
  member: Member;
  onFaderChange: (db: number) => void;
  onPanChange: (pan: number) => void;
  onMuteToggle: () => void;
  onSoloToggle: () => void;
}

const INSTRUMENT_ICONS: Record<string, string> = {
  guitar: '🎸', vocals: '🎤', drums: '🥁', bass: '🎸',
  keys: '🎹', tabla: '🪘', violin: '🎻', sax: '🎷',
};

export function ChannelStrip({ member, onFaderChange, onPanChange, onMuteToggle, onSoloToggle }: ChannelStripProps) {
  return (
    <div
      className={`flex flex-col items-center gap-2 p-3 rounded-lg border bg-card/80 backdrop-blur-sm min-w-[100px] w-[110px] transition-all ${
        member.autoAdjusted ? 'border-neon-cyan/40 glow-cyan' : 'border-border'
      } ${member.muted ? 'opacity-50' : ''}`}
    >
      {/* Name & Instrument */}
      <div className="text-center">
        <div className="text-lg">{INSTRUMENT_ICONS[member.instrument] || '🎵'}</div>
        <div className="text-xs font-semibold truncate w-full">{member.name}</div>
        <div className="text-[10px] text-muted-foreground capitalize">{member.instrument}</div>
      </div>

      {/* Waveform */}
      <WaveformVisualizer data={member.waveform} width={90} height={24} />

      {/* Feedback Alerts */}
      <FeedbackAlert frequencies={member.feedbackFreqs} />

      {/* VU Meter + Fader */}
      <div className="flex gap-2 items-stretch">
        <VUMeter level={member.level + member.faderDb} height={160} />
        <Fader value={member.faderDb} onChange={onFaderChange} autoAdjusted={member.autoAdjusted} />
      </div>

      {/* Pan */}
      <div className="w-full flex flex-col items-center gap-0.5">
        <span className="text-[9px] text-muted-foreground font-mono uppercase">Pan</span>
        <input
          type="range"
          min={-100}
          max={100}
          value={member.pan}
          onChange={(e) => onPanChange(Number(e.target.value))}
          className="w-full h-1.5 appearance-none rounded-full bg-secondary cursor-pointer"
        />
        <span className="text-[9px] font-mono text-muted-foreground">
          {member.pan === 0 ? 'C' : member.pan < 0 ? `L${Math.abs(member.pan)}` : `R${member.pan}`}
        </span>
      </div>

      {/* Mute/Solo */}
      <div className="flex gap-1 w-full">
        <button
          onClick={onMuteToggle}
          className={`flex-1 text-[10px] font-bold py-1 rounded transition-all ${
            member.muted ? 'bg-neon-red text-white' : 'bg-secondary text-muted-foreground hover:bg-secondary/80'
          }`}
        >
          M
        </button>
        <button
          onClick={onSoloToggle}
          className={`flex-1 text-[10px] font-bold py-1 rounded transition-all ${
            member.solo ? 'bg-neon-amber text-black' : 'bg-secondary text-muted-foreground hover:bg-secondary/80'
          }`}
        >
          S
        </button>
      </div>

      {/* EQ */}
      <EQDisplay eq={member.eq} />
    </div>
  );
}
