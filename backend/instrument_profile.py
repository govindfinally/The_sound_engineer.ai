"""
================================================================================
  the_sound_engineer / backend / instrument_profiles.py
  Complete Instrument Profile Registry
  
  Sources:
  - AES (Audio Engineering Society) Standards
  - Gear4Music Audio Frequency Reference (2023)
  - ResearchGate: Cajon FFT Analysis (PTEE 2017)
  - ResearchGate: Sarasvati Veena Vibro-Acoustic Study (Extrica 2023)
  - Academia.edu: Harmonics in Sitar (2025)
  - Stanford CCRMA: Sitar Spectrum Properties
  - CompMusic Project: Indian Instruments Computational Models (UPF)
  - Springer 2025: Acoustic Feedback / Howling Detection
================================================================================
"""
 
# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — PROFILES
# Every instrument that can be registered in a session.
#
# Fields per instrument:
#   freq_range      → (low_hz, high_hz)  fundamental playing range
#   harmonic_ext    → (low_hz, high_hz)  harmonics / overtone extension
#   ideal_range_db  → (min_db, max_db)   where this instrument should sit
#   clip_threshold  → float              danger zone — above this = clipping risk
#   q_cut           → float              Q for surgical cuts (narrow)
#   q_boost         → float              Q for boosts (always wider)
#   hp_filter_hz    → int | None         recommended high-pass filter cutoff
#   problem_zones   → list of tuples     (low_hz, high_hz, description)
#   category        → str                grouping for UI display
#   source          → str                data source / reference
# ══════════════════════════════════════════════════════════════════════════════
 
PROFILES = {
 
    # ── WESTERN — STRINGS ────────────────────────────────────────────────────
 
    "bass_guitar": {
        "freq_range":     (40, 300),
        "harmonic_ext":   (300, 2000),
        "ideal_range_db": (-28.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.4,
        "q_boost":        0.7,
        "hp_filter_hz":   40,
        "problem_zones":  [
            (40,  100,  "Sub-clash with kick drum fundamental"),
            (250, 400,  "Mud zone — clashes with kick drum body and guitar low-mids"),
        ],
        "category": "Western — Strings",
        "source":   "AES + Gear4Music frequency reference",
    },
 
    "electric_guitar_lead": {
        "freq_range":     (82, 1200),
        "harmonic_ext":   (1200, 6000),
        "ideal_range_db": (-28.0, -18.0),
        "clip_threshold": -6.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   80,
        "problem_zones":  [
            (250,  500,  "Low-mid mud — competes with bass and rhythm guitar"),
            (800,  1200, "Boxy/honky zone — competes directly with vocals"),
            (3000, 5000, "Harshness zone — listener fatigue"),
        ],
        "category": "Western — Strings",
        "source":   "AES mixing conventions + Gear4Music",
    },
 
    "electric_guitar_rhythm": {
        "freq_range":     (82, 1200),
        "harmonic_ext":   (1200, 5000),
        "ideal_range_db": (-30.0, -20.0),
        "clip_threshold": -6.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   100,
        "problem_zones":  [
            (250, 500,  "Mud zone — cut to leave space for lead guitar"),
            (800, 1200, "Honky zone — reduce to let vocals through"),
        ],
        "category": "Western — Strings",
        "source":   "AES mixing conventions",
    },
 
    "acoustic_guitar": {
        "freq_range":     (80, 1200),
        "harmonic_ext":   (1200, 8000),
        "ideal_range_db": (-28.0, -18.0),
        "clip_threshold": -6.0,
        "q_cut":          1.3,
        "q_boost":        0.7,
        "hp_filter_hz":   80,
        "problem_zones":  [
            (200, 400,  "Body boom — common in dreadnought guitars"),
            (800, 1200, "Boxy zone — competes with vocals"),
        ],
        "category": "Western — Strings",
        "source":   "AES + SoundGym reference",
    },
 
    "bass_guitar_fretless": {
        "freq_range":     (40, 300),
        "harmonic_ext":   (300, 3000),
        "ideal_range_db": (-28.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.4,
        "q_boost":        0.7,
        "hp_filter_hz":   40,
        "problem_zones":  [
            (40,  100, "Sub-clash with kick drum"),
            (250, 400, "Mud zone — fretless has more mid harmonic content than fretted"),
        ],
        "category": "Western — Strings",
        "source":   "AES mixing conventions",
    },
 
    "violin": {
        "freq_range":     (196, 3000),
        "harmonic_ext":   (3000, 12000),
        "ideal_range_db": (-26.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   150,
        "problem_zones":  [
            (250, 400,  "Body resonance clash with guitar and vocals"),
            (2000, 4000,"Harshness zone — can cut through mix aggressively"),
        ],
        "category": "Western — Strings",
        "source":   "AES orchestral mixing reference",
    },
 
    "cello": {
        "freq_range":     (65, 1000),
        "harmonic_ext":   (1000, 8000),
        "ideal_range_db": (-28.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.4,
        "q_boost":        0.7,
        "hp_filter_hz":   60,
        "problem_zones":  [
            (100, 300,  "Competes with bass guitar and piano left hand"),
            (250, 500,  "Mud zone shared with most mid-range instruments"),
        ],
        "category": "Western — Strings",
        "source":   "AES orchestral mixing reference",
    },
 
    "viola": {
        "freq_range":     (130, 1200),
        "harmonic_ext":   (1200, 8000),
        "ideal_range_db": (-28.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.4,
        "q_boost":        0.7,
        "hp_filter_hz":   100,
        "problem_zones":  [
            (250, 500, "Dense mid zone — clashes with guitar and vocals simultaneously"),
        ],
        "category": "Western — Strings",
        "source":   "AES orchestral mixing reference",
    },
 
    # ── WESTERN — VOCALS ─────────────────────────────────────────────────────
 
    "vocals_male": {
        "freq_range":     (85, 1100),
        "harmonic_ext":   (1100, 8000),
        "ideal_range_db": (-24.0, -14.0),
        "clip_threshold": -6.0,
        "q_cut":          1.4,
        "q_boost":        0.7,
        "hp_filter_hz":   80,
        "problem_zones":  [
            (100, 300,  "Proximity effect / chest voice buildup"),
            (200, 500,  "Mud zone — competes with guitars and bass"),
            (5000, 8000,"Sibilance — de-essing target"),
        ],
        "category": "Western — Vocals",
        "source":   "AES + standard live vocal EQ practice",
    },
 
    "vocals_female": {
        "freq_range":     (165, 1100),
        "harmonic_ext":   (1100, 12000),
        "ideal_range_db": (-24.0, -14.0),
        "clip_threshold": -6.0,
        "q_cut":          1.2,
        "q_boost":        0.7,
        "hp_filter_hz":   100,
        "problem_zones":  [
            (200, 500,  "Mud zone — reduce for clarity"),
            (5000, 8000,"Sibilance — de-essing target"),
            (8000, 12000, "Air zone — boost gently for brightness"),
        ],
        "category": "Western — Vocals",
        "source":   "AES + standard live vocal EQ practice",
    },
 
    "backing_vocals": {
        "freq_range":     (100, 1100),
        "harmonic_ext":   (1100, 8000),
        "ideal_range_db": (-30.0, -20.0),
        "clip_threshold": -6.0,
        "q_cut":          1.4,
        "q_boost":        0.7,
        "hp_filter_hz":   120,
        "problem_zones":  [
            (200, 500,  "Cut more aggressively than lead vocals to leave space"),
            (2000, 4000,"Presence zone — reduce to sit behind lead vocals"),
        ],
        "category": "Western — Vocals",
        "source":   "AES live mixing conventions",
    },
 
    # ── WESTERN — PERCUSSION ─────────────────────────────────────────────────
 
    "drums_full_kit": {
        "freq_range":     (20, 20000),
        "harmonic_ext":   (20, 20000),
        "ideal_range_db": (-22.0, -12.0),
        "clip_threshold": -3.0,
        "q_cut":          1.8,
        "q_boost":        0.7,
        "hp_filter_hz":   None,
        "problem_zones":  [
            (40,  100,  "Kick drum vs bass guitar fundamental clash"),
            (200, 400,  "Snare body clashes with bass guitar low-mids"),
            (2000, 8000,"Cymbal harshness — check hi-hat and crash levels"),
        ],
        "category": "Western — Percussion",
        "source":   "AES + drum mixing reference",
    },
 
    "kick_drum": {
        "freq_range":     (40, 200),
        "harmonic_ext":   (200, 2000),
        "ideal_range_db": (-20.0, -10.0),
        "clip_threshold": -3.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   40,
        "problem_zones":  [
            (40,  80,   "Sub clash with bass guitar — sidechain recommended"),
            (300, 500,  "Boxiness — cut to tighten kick punch"),
        ],
        "category": "Western — Percussion",
        "source":   "AES drum mixing reference",
    },
 
    "snare_drum": {
        "freq_range":     (100, 800),
        "harmonic_ext":   (800, 10000),
        "ideal_range_db": (-20.0, -10.0),
        "clip_threshold": -3.0,
        "q_cut":          2.0,
        "q_boost":        0.7,
        "hp_filter_hz":   80,
        "problem_zones":  [
            (200, 400, "Body resonance — cut ring with narrow Q 2.0–3.0"),
            (800, 1500,"Papery/thin sound — check if snare needs more body"),
        ],
        "category": "Western — Percussion",
        "source":   "AES drum mixing reference",
    },
 
    "cajon": {
        "freq_range":     (42, 8000),
        "harmonic_ext":   (8000, 16000),
        "ideal_range_db": (-22.0, -12.0),
        "clip_threshold": -3.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   40,
        "problem_zones":  [
            (42,  75,   "Box resonance — lowest cavity resonance at 42 Hz, 53 Hz, 74 Hz (paper-backed)"),
            (200, 400,  "Body thud — can clash with bass in small venues"),
        ],
        "category": "Western — Percussion",
        "source":   "ResearchGate: Cajon FFT Analysis, PTEE 2017 (resonances at 42, 53.1, 74.7 Hz)",
    },
 
    "djembe": {
        "freq_range":     (60, 8000),
        "harmonic_ext":   (8000, 16000),
        "ideal_range_db": (-22.0, -12.0),
        "clip_threshold": -3.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   50,
        "problem_zones":  [
            (60,  200,  "Bass slap tone — can overwhelm vocals in small venues"),
            (200, 400,  "Mid body — clashes with other percussion"),
        ],
        "category": "Western — Percussion",
        "source":   "AES world music mixing reference",
    },
 
    # ── WESTERN — KEYS ───────────────────────────────────────────────────────
 
    "piano": {
        "freq_range":     (27, 4186),
        "harmonic_ext":   (4186, 12000),
        "ideal_range_db": (-26.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.2,
        "q_boost":        0.6,
        "hp_filter_hz":   80,
        "problem_zones":  [
            (80,  300,  "Left hand clashes with bass guitar simultaneously"),
            (250, 500,  "Mud accumulation zone — cut for clarity"),
        ],
        "category": "Western — Keys",
        "source":   "AES + Gear4Music (piano range A0=27.5 Hz, C8=4186 Hz)",
    },
 
    "keyboard_synth": {
        "freq_range":     (20, 20000),
        "harmonic_ext":   (20, 20000),
        "ideal_range_db": (-26.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.2,
        "q_boost":        0.7,
        "hp_filter_hz":   40,
        "problem_zones":  [
            (250, 500,  "Universal mud zone — applies to all synth patches"),
            (2000, 4000,"Lead synth competes directly with vocals here"),
        ],
        "category": "Western — Keys",
        "source":   "AES live mixing conventions",
    },
 
    "organ": {
        "freq_range":     (16, 8000),
        "harmonic_ext":   (8000, 16000),
        "ideal_range_db": (-26.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.2,
        "q_boost":        0.6,
        "hp_filter_hz":   40,
        "problem_zones":  [
            (60,  120,  "Sub/bass clash — organ pedals vs bass guitar"),
            (250, 500,  "Mud zone — organ fills this entire range simultaneously"),
        ],
        "category": "Western — Keys",
        "source":   "AES mixing conventions",
    },
 
    # ── WESTERN — WIND ───────────────────────────────────────────────────────
 
    "trumpet": {
        "freq_range":     (165, 988),
        "harmonic_ext":   (988, 5000),
        "ideal_range_db": (-26.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.4,
        "q_boost":        0.7,
        "hp_filter_hz":   100,
        "problem_zones":  [
            (150, 250,  "Mud — reduce for clarity"),
            (450, 550,  "Resonance ring — check and cut narrow"),
            (2000, 5000,"Brightness zone — can dominate mix aggressively"),
        ],
        "category": "Western — Wind",
        "source":   "AES brass mixing reference",
    },
 
    "saxophone": {
        "freq_range":     (100, 1500),
        "harmonic_ext":   (1500, 6000),
        "ideal_range_db": (-26.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.4,
        "q_boost":        0.7,
        "hp_filter_hz":   80,
        "problem_zones":  [
            (200, 500,  "Honk zone — classic saxophone mud"),
            (2000, 4000,"Reed harshness — can be piercing"),
        ],
        "category": "Western — Wind",
        "source":   "AES + Gear4Music wind instrument reference",
    },
 
    "flute": {
        "freq_range":     (262, 2349),
        "harmonic_ext":   (2349, 12000),
        "ideal_range_db": (-26.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.3,
        "q_boost":        0.7,
        "hp_filter_hz":   200,
        "problem_zones":  [
            (250, 500,  "Clashes with guitar and brass in mid zone"),
            (5000, 8000,"Breath noise — can accumulate here"),
        ],
        "category": "Western — Wind",
        "source":   "AES orchestral mixing reference",
    },
 
    "clarinet": {
        "freq_range":     (147, 1568),
        "harmonic_ext":   (1568, 8000),
        "ideal_range_db": (-26.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.4,
        "q_boost":        0.7,
        "hp_filter_hz":   100,
        "problem_zones":  [
            (250, 500,  "Mid mud — competes with guitars and brass"),
            (5000, 7000,"Reed noise zone — cut narrow if harsh"),
        ],
        "category": "Western — Wind",
        "source":   "AES orchestral mixing reference",
    },
 
    "trombone": {
        "freq_range":     (73, 493),
        "harmonic_ext":   (493, 4000),
        "ideal_range_db": (-26.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.4,
        "q_boost":        0.7,
        "hp_filter_hz":   60,
        "problem_zones":  [
            (100, 300,  "Overlaps bass guitar and kick drum heavily"),
            (250, 500,  "Mud zone — cut to separate from bass instruments"),
        ],
        "category": "Western — Wind",
        "source":   "AES brass mixing reference",
    },
 
    # ── INDIAN — STRING INSTRUMENTS ──────────────────────────────────────────
 
    "sitar": {
        "freq_range":     (138, 3520),
        "harmonic_ext":   (3520, 12000),
        "ideal_range_db": (-26.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   100,
        "problem_zones":  [
            (250, 500,  "Mid mud — sympathetic strings fill this range continuously"),
            (2000, 5000,"Jawari shimmer — characteristic but can overwhelm vocals"),
        ],
        "category": "Indian — String",
        "source":   "Academia.edu: Harmonics in Sitar (2025); Stanford CCRMA Sitar Spectrum; fundamental Sa at ~138 Hz (Jodi string)",
    },
 
    "sarod": {
        "freq_range":     (100, 3000),
        "harmonic_ext":   (3000, 10000),
        "ideal_range_db": (-26.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   80,
        "problem_zones":  [
            (100, 300,  "Deep body resonance — metal fingerboard adds low-mid bite"),
            (250, 500,  "Mud zone — broader than sitar due to metal body"),
            (2000, 5000,"Upper harmonic brightness — can pierce in small venues"),
        ],
        "category": "Indian — String",
        "source":   "Britannica Sarod article; India-Instruments.com encyclopedia; CompMusic UPF — described as wider tonal bandwidth than rubab esp. in middle and high registers",
    },
 
    "veena": {
        "freq_range":     (150, 3000),
        "harmonic_ext":   (3000, 10000),
        "ideal_range_db": (-26.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   100,
        "problem_zones":  [
            (280, 300,  "Natural resonance peaks at 280 and 300 Hz (paper-backed FFT measurement)"),
            (560, 600,  "First overtone resonance peaks at 560 and 600 Hz (paper-backed)"),
        ],
        "category": "Indian — String",
        "source":   "Extrica 2023: Sarasvati Veena Vibro-Acoustic Study — FFT peaks confirmed at 280, 300, 560, 600 Hz",
    },
 
    "tanpura": {
        "freq_range":     (65, 500),
        "harmonic_ext":   (500, 6000),
        "ideal_range_db": (-32.0, -22.0),
        "clip_threshold": -6.0,
        "q_cut":          1.3,
        "q_boost":        0.6,
        "hp_filter_hz":   60,
        "problem_zones":  [
            (65, 300,   "Drone fills low-mid range continuously — can muddy the mix"),
            (250, 500,  "Sympathetic resonance zone — check against main melody instrument"),
        ],
        "category": "Indian — String",
        "source":   "CompMusic UPF Indian Instruments; Raman 1921 string termination study",
    },
 
    "sarangi": {
        "freq_range":     (130, 1500),
        "harmonic_ext":   (1500, 8000),
        "ideal_range_db": (-28.0, -18.0),
        "clip_threshold": -6.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   100,
        "problem_zones":  [
            (250, 500,  "Sympathetic string mud — 35+ sympathetic strings fill this zone"),
            (2000, 4000,"Bow noise and harmonic brightness — check against vocals"),
        ],
        "category": "Indian — String",
        "source":   "CompMusic UPF — Hindustani chordophone sympathetic string analysis",
    },
 
    # ── INDIAN — PERCUSSION ──────────────────────────────────────────────────
 
    "tabla": {
        "freq_range":     (60, 8000),
        "harmonic_ext":   (8000, 16000),
        "ideal_range_db": (-22.0, -12.0),
        "clip_threshold": -3.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   50,
        "problem_zones":  [
            (60,  200,  "Bayan (left drum) bass tone — can clash with bass instruments"),
            (200, 500,  "Mid resonance — check against other percussion"),
        ],
        "category": "Indian — Percussion",
        "source":   "CompMusic UPF Indian Instruments; MomentsLog.com Tabla analysis",
    },
 
    "mridangam": {
        "freq_range":     (60, 8000),
        "harmonic_ext":   (8000, 16000),
        "ideal_range_db": (-22.0, -12.0),
        "clip_threshold": -3.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   50,
        "problem_zones":  [
            (60,  200,  "Bass aperture — large side produces sub-bass tone"),
            (500, 2000, "Treble aperture — small side can be sharp and piercing"),
        ],
        "category": "Indian — Percussion",
        "source":   "CompMusic UPF; C.V. Raman 1934 Mridangam acoustics article",
    },
 
    # ── INDIAN — WIND ────────────────────────────────────────────────────────
 
    "bansuri": {
        "freq_range":     (240, 2100),
        "harmonic_ext":   (2100, 10000),
        "ideal_range_db": (-26.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.3,
        "q_boost":        0.7,
        "hp_filter_hz":   180,
        "problem_zones":  [
            (250, 500,  "Mid zone — competes with sarod, sitar in ensemble"),
            (4000, 8000,"Breath noise and upper harmonics — can be harsh miked closely"),
        ],
        "category": "Indian — Wind",
        "source":   "CompMusic UPF: Bansuri (north Indian bamboo flute) — 6 or 7 finger holes",
    },
 
    "shehnai": {
        "freq_range":     (240, 2000),
        "harmonic_ext":   (2000, 8000),
        "ideal_range_db": (-26.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.4,
        "q_boost":        0.7,
        "hp_filter_hz":   180,
        "problem_zones":  [
            (250, 500,  "Reed nasal tone accumulates in this zone"),
            (3000, 6000,"Shrill upper harmonics — check carefully in small venues"),
        ],
        "category": "Indian — Wind",
        "source":   "AES world music reference",
    },
 
    # ── INDIAN — KEYS / DRONE ────────────────────────────────────────────────
 
    "harmonium": {
        "freq_range":     (100, 3136),
        "harmonic_ext":   (3136, 8000),
        "ideal_range_db": (-28.0, -18.0),
        "clip_threshold": -6.0,
        "q_cut":          1.2,
        "q_boost":        0.6,
        "hp_filter_hz":   80,
        "problem_zones":  [
            (100, 500,  "Reed drone fills this range continuously — can dominate a mix"),
            (250, 500,  "Universal mud zone — harmonium hand-pumped reeds accumulate here"),
        ],
        "category": "Indian — Keys",
        "source":   "CompMusic UPF Indian Instruments; Gearspace harmonium tuning discussion — hand-pumped reed organ, fixed in equal temperament",
    },
 
    # ── WORLD / FOLK ─────────────────────────────────────────────────────────
 
    "ukulele": {
        "freq_range":     (262, 1175),
        "harmonic_ext":   (1175, 6000),
        "ideal_range_db": (-28.0, -18.0),
        "clip_threshold": -6.0,
        "q_cut":          1.3,
        "q_boost":        0.7,
        "hp_filter_hz":   200,
        "problem_zones":  [
            (800, 1500, "Nasal zone — ukulele body resonance can be honky"),
        ],
        "category": "World / Folk",
        "source":   "AES mixing reference",
    },
 
    "mandolin": {
        "freq_range":     (196, 2637),
        "harmonic_ext":   (2637, 10000),
        "ideal_range_db": (-28.0, -18.0),
        "clip_threshold": -6.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   150,
        "problem_zones":  [
            (250, 500,  "Mid mud — competes with guitar and vocals"),
            (3000, 6000,"Bite zone — can be excessively bright in small rooms"),
        ],
        "category": "World / Folk",
        "source":   "AES mixing conventions",
    },
 
    "banjo": {
        "freq_range":     (130, 2000),
        "harmonic_ext":   (2000, 8000),
        "ideal_range_db": (-28.0, -18.0),
        "clip_threshold": -6.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   100,
        "problem_zones":  [
            (800, 2000, "Twang zone — banjo head resonance can be harsh"),
            (3000, 6000,"Metallic brightness — check carefully"),
        ],
        "category": "World / Folk",
        "source":   "AES mixing conventions",
    },
 
    # ── ELECTRONIC ───────────────────────────────────────────────────────────
 
    "dj_controller": {
        "freq_range":     (20, 20000),
        "harmonic_ext":   (20, 20000),
        "ideal_range_db": (-20.0, -10.0),
        "clip_threshold": -3.0,
        "q_cut":          1.0,
        "q_boost":        0.7,
        "hp_filter_hz":   None,
        "problem_zones":  [
            (20,  80,   "Sub-bass — electronic music often overloads this range"),
            (250, 500,  "Mid mud from sample layers"),
        ],
        "category": "Electronic",
        "source":   "AES live sound mixing for electronic music",
    },
 
    "drum_machine": {
        "freq_range":     (20, 20000),
        "harmonic_ext":   (20, 20000),
        "ideal_range_db": (-22.0, -12.0),
        "clip_threshold": -3.0,
        "q_cut":          1.5,
        "q_boost":        0.7,
        "hp_filter_hz":   None,
        "problem_zones":  [
            (40,  100,  "Kick sample sub clash with bass synth"),
            (200, 400,  "Snare sample mid clash with other instruments"),
        ],
        "category": "Electronic",
        "source":   "AES electronic music mixing reference",
    },
 
    # ── CATCH-ALL ────────────────────────────────────────────────────────────
 
    "other": {
        "freq_range":     (20, 20000),
        "harmonic_ext":   (20, 20000),
        "ideal_range_db": (-28.0, -16.0),
        "clip_threshold": -6.0,
        "q_cut":          1.4,
        "q_boost":        0.7,
        "hp_filter_hz":   80,
        "problem_zones":  [
            (250, 500,  "Universal mud zone — applies to almost all instruments"),
        ],
        "category": "Other",
        "source":   "Generic AES defaults — used when instrument is not in registry",
    },
}
 
 
# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
 
def get_profile(instrument: str) -> dict:
    """
    Safe profile lookup.
    If instrument is not in PROFILES, falls back to 'other'
    so any unknown instrument is still handled gracefully.
    """
    instrument = instrument.lower().strip().replace(" ", "_")
    if instrument in PROFILES:
        return PROFILES[instrument]
    print(f"[WARNING] Instrument '{instrument}' not in registry — using 'other' profile")
    return PROFILES["other"]
    
if __name__ == "__main__":
    ans = get_profile("Electric Guitar Lead")  # Example usage
    print(ans)
