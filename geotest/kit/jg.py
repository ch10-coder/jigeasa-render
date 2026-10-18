"""JIGEASA component library for HyperFrames scenes (Python -> HTML + GSAP + SFX cues). KIT v3 (2026-10-17).
Copy the skill's kit/ into the project at project start (project/kit/); fix bugs in the SKILL copy too.
Each Scene is one standalone HyperFrames project (chapters/<id>/index.html), rendered on its own and
concatenated later. Times passed to components are SCENE-LOCAL seconds.
Colour rule: teal = new / current fact to memorise, amber = dates / money / legacy, coral = outdated / negative.
v3 (pipeline audit 2026-10-17): Devanagari (for the rupee sign) + latin-ext font faces; arrows, play and check marks
drawn as inline SVG (Poppins has no arrow glyphs, Chrome used a thin fallback font); no text-shadow on text inside
filled boxes; humanised typewriter rhythm with a click cap; optional chapter pre-roll (JIG_PRE) so the final concat
can crossfade chapters; write(..., export=True) copies fonts/GSAP/photos (optionally baked grade); units.json
manifest for the CI; lazy timing.json; no MCQ component (user rule 2026-10-15: no quiz)."""
import json, math, os, random, re, shutil
from pathlib import Path

_HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("JIG_PROJECT") or (_HERE.parent if _HERE.name == "kit" else _HERE))
SKILL = Path(os.environ.get("JIG_SKILL", "/root/.claude/skills/jigeasa-video"))
LIBROOT = Path(os.environ.get("JIG_LIB", "/mnt/sdcard/TermuxFiles/Assets/jigeasa_library"))
FPS = 30
MAP = json.load(open(SKILL / "assets/map_paths.json"))
LIB = str(LIBROOT / "sfx")
PRE_ROLL = float(os.environ.get("JIG_PRE", "0"))   # lead-in seconds per chapter (not the first) for xfade transitions
TAG = "JKSSB  •  ECONOMY"                           # default chrome tag: set jg.TAG per video
ERAS = []                                           # era chip labels: set jg.ERAS per video (empty = no era bar)
KEY_GAP = 0.075                                     # min seconds between typewriter key clicks (~13/s, a fast typist)
GRAIN = 0.09                                        # film-grain opacity (0 = off)
PHOTO_SCALE = 2                                     # photos at 2x canvas: renders are 4K (user 2026-10-17)
_TIMING = None

def timing():
    global _TIMING
    if _TIMING is None: _TIMING = json.load(open(ROOT / "timing.json"))
    return _TIMING

def __getattr__(name):  # old scene files read jg.TIMING
    if name == "TIMING": return timing()
    raise AttributeError(name)

def fr(t):  # snap to frame
    return round(round(t * FPS) / FPS, 4)

# SFX shortcuts (Mixkit id or kenney path), default gain
SFX = {
    "whoosh": ("mk", 1473, -22), "swoosh": ("mk", 1478, -24), "fast": ("mk", 1492, -18), "air": ("mk", 1489, -20),
    "pop": ("mk", 2354, -20), "pop2": ("mk", 3005, -19), "click": ("kif", "select_002.ogg", -21),
    "tick": ("kif", "tick_002.ogg", -23), "impact": ("mk", 2182, -15), "deep": ("mk", 1143, -14),
    "epic": ("mk", 788, -12), "logo": ("mk", 2152, -13), "metal": ("mk", 2980, -13), "metal2": ("mk", 2983, -16),
    "type": ("mk", 1382, -15), "typing": ("mk", 1372, -22), "page": ("mk", 1104, -18), "paper": ("mk", 1530, -19),
    "sign": ("mk", 2368, -20), "gear": ("mk", 2858, -15), "gear2": ("mk", 2856, -16), "steam": ("mk", 1458, -18),
    "train": ("mk", 1628, -20), "coins": ("mk", 1939, -18), "coin": ("mk", 1993, -19), "bag": ("mk", 1989, -17),
    "hammer": ("mk", 833, -17), "door": ("mk", 200, -20), "mech": ("mk", 3117, -17), "reso": ("mk", 2609, -14),
    "ding": ("mk", 2870, -16), "notify": ("mk", 2867, -18), "grill": ("mk", 2177, -18), "machine": ("mk", 2689, -20),
    "swish": ("mk", 166, -22), "flying": ("mk", 2050, -20), "sweep": ("mk", 2411, -18), "bell": ("mk", 1368, -20),
    "thud": ("kip", "impactPunch_heavy_000.ogg", -13), "ping": ("kif", "pluck_002.ogg", -19), "marker": ("mk", 1478, -24),
}
KEYS = [1382, 1365, 1384, 1380, 1366, 1362, 1369, 1364, 1367, 1119]  # typewriter key hits (Mixkit)

CSS = r"""
@font-face { font-family: "Poppins"; font-weight: 600; font-display: block; src: url("assets/fonts/poppins-latin-600-normal.woff2") format("woff2"); }
@font-face { font-family: "Poppins"; font-weight: 700; font-display: block; src: url("assets/fonts/poppins-latin-700-normal.woff2") format("woff2"); }
@font-face { font-family: "Poppins"; font-weight: 800; font-display: block; src: url("assets/fonts/poppins-latin-800-normal.woff2") format("woff2"); }
@font-face { font-family: "Poppins"; font-weight: 900; font-display: block; src: url("assets/fonts/poppins-latin-900-normal.woff2") format("woff2"); }
@font-face { font-family: "Inter"; font-weight: 600; font-display: block; src: url("assets/fonts/inter-latin-600-normal.woff2") format("woff2"); }
@font-face { font-family: "Inter"; font-weight: 700; font-display: block; src: url("assets/fonts/inter-latin-700-normal.woff2") format("woff2"); }
:root { --bg: #0b1220; --ink: #f8fafc; --mute: #94a3b8; --amber: #fbbf24; --teal: #2dd4bf; --coral: #ff6b6b; --card: #131c31; --line: #263353; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 1920px; height: 1080px; overflow: hidden; background: var(--bg); }
#root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: "Poppins", system-ui, sans-serif; color: var(--ink); }
.full { position: absolute; inset: 0; overflow: hidden; }
.abs { position: absolute; }
.w { display: inline-block; }
.ta { color: var(--amber); } .tt { color: var(--teal); } .tm { color: var(--mute); } .tc { color: var(--coral); }
/* colour rule: teal = new/positive fact, amber = dates/years/money, coral = outdated/ended/negative */
#bg { background:
  radial-gradient(900px 600px at 15% 10%, rgba(45,212,191,0.12), transparent 60%),
  radial-gradient(1000px 700px at 90% 95%, rgba(251,191,36,0.10), transparent 60%),
  repeating-linear-gradient(0deg, rgba(148,163,184,0.045) 0 1px, transparent 1px 80px),
  repeating-linear-gradient(90deg, rgba(148,163,184,0.045) 0 1px, transparent 1px 80px), var(--bg); }
/* keyline */
.kl { position: absolute; left: 0; right: 0; text-align: center; white-space: nowrap; font-weight: 900; letter-spacing: -0.01em; }
.kl .bxw { isolation: isolate; position: relative; margin: 0 0.2em; }
.kl .bxw .bx { position: absolute; left: -0.16em; right: -0.16em; top: 5.5%; bottom: 8.5%; border-radius: 0.14em; z-index: -1; transform-origin: 0 50%; }
.kl .ba .bx { background: var(--amber); } .kl .bt .bx { background: var(--teal); } .kl .bc .bx { background: var(--coral); }
.kl .ba, .kl .bt, .kl .bc { color: var(--bg); }
.kl .sub { display: block; font-weight: 700; font-size: 0.4em; letter-spacing: 0.16em; color: var(--mute); margin-top: 0.35em; }
/* date card */
.stw { position: absolute; left: 0; right: 0; text-align: center; }
.stamp { display: inline-block; padding: 0.06em 0.4em 0; border: 0.085em solid var(--amber); border-radius: 0.16em; color: var(--amber); font-weight: 900; letter-spacing: 0.06em; line-height: 1.12; white-space: nowrap; background: rgba(11,18,32,0.35); text-shadow: none; }
.stamp.tl { border-color: var(--teal); color: var(--teal); } .stamp.co { border-color: var(--coral); color: var(--coral); }
.dtitle { position: absolute; left: 0; right: 0; text-align: center; font-weight: 900; font-size: 96px; white-space: nowrap; overflow: hidden; padding-bottom: 8px; }
.dtitle span { display: inline-block; }
.dsub { position: absolute; left: 0; right: 0; text-align: center; font: 700 34px "Inter"; letter-spacing: 0.18em; color: var(--mute); white-space: nowrap; }
/* cards */
.card { position: absolute; overflow: visible; padding-top: 40px !important; }
.card .rule { position: absolute; left: 0; top: 0; width: 100%; height: 6px; border-radius: 3px; background: rgba(248,250,252,0.85); transform-origin: 0 50%; }
.card.am .rule { background: var(--amber); } .card.tl .rule { background: var(--teal); }
.card .big .ch { display: inline-block; }
.card .big { font-weight: 900; line-height: 1; white-space: nowrap; }
.card .ttl { font-weight: 800; font-size: 46px; line-height: 1.15; }
.card .sb { font: 600 32px "Inter"; color: #cbd5e1; line-height: 1.35; margin-top: 14px; }

.tag { display: inline-block; height: 48px; padding: 0 20px; border-radius: 999px; font: 800 24px "Poppins"; letter-spacing: 0.14em; line-height: 46px; white-space: nowrap; text-shadow: none; }
.tag.am { background: var(--amber); color: var(--bg); } .tag.co { background: var(--coral); color: var(--bg); } .tag.tl { background: var(--teal); color: var(--bg); } .tag.mu { border: 3px solid var(--mute); color: var(--mute); line-height: 42px; }
/* numbered list */
.nl .it { position: absolute; left: 0; display: flex; align-items: center; gap: 30px; white-space: nowrap; }
.nl .nb { min-width: 128px; flex: none; font-weight: 900; font-size: 84px; line-height: 1; color: transparent; -webkit-text-stroke: 2.5px var(--teal); text-shadow: none; }
.nl .nb.am { -webkit-text-stroke-color: var(--amber); }
.nl .hd { position: relative; display: inline-block; }
.nl .ul { position: absolute; left: 0; right: 0; bottom: -10px; height: 5px; border-radius: 3px; background: var(--teal); transform-origin: 0 50%; }
.nl .ul.am { background: var(--amber); }
.nl .hd { font-weight: 800; font-size: 60px; line-height: 1.1; }
.nl .sd { font: 600 34px "Inter"; color: #cbd5e1; margin-top: 6px; }
.nl .ic { width: 64px; height: 64px; color: var(--teal); flex: none; }
/* chips */
.chip { position: absolute; height: 76px; padding: 0 34px; border-radius: 999px; font: 800 38px "Poppins"; line-height: 70px; white-space: nowrap; border: 3px solid var(--teal); color: var(--teal); background: rgba(45,212,191,0.08); }
.chip.am { border-color: var(--amber); color: var(--amber); background: rgba(251,191,36,0.08); }
.chip.fill { background: var(--teal); color: var(--bg); } .chip.am.fill { background: var(--amber); color: var(--bg); }
/* photo */
.ph { position: absolute; overflow: hidden; border-radius: 26px; box-shadow: 0 40px 90px rgba(0,0,0,0.5); border: 2px solid var(--line); }
.ph img { position: absolute; left: -6%; top: -6%; width: 112%; height: 112%; object-fit: cover; }
.ph.full { border-radius: 0; border: 0; inset: 0; }
.ph.full::after { content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(11,18,32,0.9) 0%, rgba(11,18,32,0.5) 45%, rgba(11,18,32,0.15) 80%), linear-gradient(0deg, rgba(11,18,32,0.7), transparent 45%); }
.phcap { position: absolute; font: 600 15px "Inter"; color: rgba(248,250,252,0.42); white-space: nowrap; }
.ph.gr img { filter: grayscale(1) contrast(1.08) brightness(0.92); }
.ph.gr::after { content: ""; position: absolute; inset: 0; background: rgba(45,212,191,0.16); mix-blend-mode: soft-light; }
.lower { position: absolute; display: flex; align-items: stretch; gap: 0; white-space: nowrap; }
.lower .bar { width: 12px; background: var(--teal); border-radius: 6px; }
.lower .tx { padding: 10px 30px 12px 26px; background: rgba(11,18,32,0.82); border-radius: 0 18px 18px 0; }
.lower .nm { font-weight: 800; font-size: 46px; line-height: 1.1; } .lower .rl { font: 600 28px "Inter"; color: var(--teal); margin-top: 4px; letter-spacing: 0.04em; }
/* swap */
.arrow { position: absolute; font-weight: 900; font-size: 120px; color: var(--mute); }
.strike { position: absolute; height: 12px; border-radius: 6px; background: var(--coral); transform-origin: 0 50%; }
/* counter */
.cnt { position: absolute; overflow: hidden; }
.cnt .dg { position: absolute; left: 0; top: 0; width: 100%; text-align: center; font-weight: 900; }
/* table */
.tb { position: absolute; }
.tb .row { position: absolute; left: 0; display: flex; align-items: center; border-radius: 22px; }
.tb .row.hd { font: 800 30px "Poppins"; letter-spacing: 0.14em; color: var(--mute); }
.tb .row.bd { border-radius: 0; border-bottom: 2px solid rgba(148,163,184,0.3); }
.tb .row.bd.hl { border-left: 10px solid var(--teal); background: linear-gradient(90deg, rgba(45,212,191,0.22), rgba(45,212,191,0)); }
.tb .cell { font-weight: 800; font-size: 50px; white-space: nowrap; padding: 0 30px; }
/* timeline */
.tln .ln { position: absolute; height: 6px; border-radius: 3px; background: var(--line); }
.tln .lnf { position: absolute; height: 6px; border-radius: 3px; background: var(--teal); transform-origin: 0 50%; }
.tln .nd { position: absolute; width: 34px; height: 34px; margin: -14px 0 0 -17px; border-radius: 50%; background: var(--bg); border: 6px solid var(--teal); }
.tln .yr { position: absolute; width: 360px; margin-left: -180px; text-align: center; font-weight: 900; font-size: 64px; white-space: nowrap; }
.tln .lb { position: absolute; width: 380px; margin-left: -190px; text-align: center; font: 700 32px "Inter"; color: #cbd5e1; line-height: 1.3; }
/* map */
.mapw { position: absolute; }
.m-in { fill: #131c31; stroke: #4a5b80; stroke-width: 1.4; }
.m-jk { fill: rgba(45,212,191,0.14); stroke: #5d76a3; stroke-width: 1.4; }
.m-st { fill: #131c31; stroke: #3a4a6e; stroke-width: 1.2; }
.pin { position: absolute; width: 0; height: 0; }
.pin .dot { position: absolute; left: -14px; top: -14px; width: 28px; height: 28px; border-radius: 50%; background: var(--amber); box-shadow: 0 0 0 8px rgba(251,191,36,0.25); }
.pin .pl { position: absolute; white-space: nowrap; font-weight: 800; font-size: 40px; text-shadow: 0 4px 18px rgba(11,18,32,0.9); }
.pin .ps { display: block; font: 700 28px "Inter"; color: var(--teal); }
/* chapter breaker */
.brk { position: absolute; inset: 0; background: rgba(11,18,32,0.9); display: flex; flex-direction: column; align-items: center; justify-content: center; }
.brk .bl { font-weight: 900; font-size: 210px; letter-spacing: 0.02em; color: var(--teal); white-space: nowrap; line-height: 1; }
.brk .bl .ch { display: inline-block; }
.brk .bs { font: 800 44px "Poppins"; letter-spacing: 0.22em; color: var(--mute); margin-top: 26px; white-space: nowrap; }
.m-state { fill: rgba(251,191,36,0.0); stroke: rgba(251,191,36,0.0); stroke-width: 2; }
/* chrome */
#ov-tag { position: absolute; top: 46px; left: 64px; font-size: 28px; letter-spacing: 0.18em; color: var(--teal); font-weight: 700; white-space: nowrap; }
#ov-brand { position: absolute; bottom: 40px; right: 64px; font-size: 26px; color: var(--mute); letter-spacing: 0.12em; font-weight: 600; }
#era { position: absolute; top: 40px; right: 64px; display: flex; gap: 10px; }
#era .e { height: 44px; padding: 0 18px; border-radius: 999px; font: 700 20px "Poppins"; letter-spacing: 0.08em; line-height: 42px; color: #64748b; border: 2px solid #26355a; white-space: nowrap; }
#era .e.on { color: var(--bg); background: var(--teal); border-color: var(--teal); }
#era .e.done { color: #94a3b8; border-color: #3a4a6e; }
.src { position: absolute; left: 64px; bottom: 44px; font: 600 18px "Inter"; color: rgba(248,250,252,0.55); white-space: nowrap; }
/* photo backgrounds */
.bgi { position: absolute; inset: 0; overflow: hidden; }
.bgi img { position: absolute; left: -5%; top: -5%; width: 110%; height: 110%; object-fit: cover; filter: grayscale(0.25) saturate(0.85) brightness(0.62) contrast(1.06); }
#bgshade { background: linear-gradient(180deg, rgba(11,18,32,0.66) 0%, rgba(11,18,32,0.5) 38%, rgba(11,18,32,0.8) 100%),
  repeating-linear-gradient(0deg, rgba(148,163,184,0.05) 0 1px, transparent 1px 80px), repeating-linear-gradient(90deg, rgba(148,163,184,0.05) 0 1px, transparent 1px 80px); }
.bgcred { position: absolute; right: 64px; bottom: 80px; font: 600 16px "Inter"; color: rgba(248,250,252,0.5); white-space: nowrap; }
#content { text-shadow: 0 4px 28px rgba(0,0,0,0.55); }
/* typewriter */
.ty { position: absolute; white-space: nowrap; }
.tyw { position: relative; display: inline-block; }
.tyw .gh { visibility: hidden; white-space: pre; }
.tyw .lv { position: absolute; left: 0; top: 0; white-space: pre; }
.tyw .c { display: none; }
.tyw .cur { display: inline-block; width: 0.07em; height: 0.92em; margin-left: 0.04em; vertical-align: -0.1em; background: var(--teal); }
.kl .ch { display: inline-block; }
#vig { background: radial-gradient(1300px 850px at 50% 50%, transparent 55%, rgba(0,0,0,0.42) 100%); pointer-events: none; }
#grain { position: absolute; left: -100px; top: -100px; width: 2120px; height: 1280px; opacity: 0.09; mix-blend-mode: overlay; pointer-events: none;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 1.4 0'/></filter><rect width='300' height='300' filter='url(%23n)'/></svg>"); }
"""


DEV = "U+0900-097F,U+1CD0-1CF9,U+200C-200D,U+20A8,U+20B9,U+20F0,U+25CC,U+A830-A839,U+A8E0-A8FF"
LEXT = ("U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,"
        "U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF")
FONT_CSS = "".join(  # the latin subsets have no rupee sign: without these faces Chrome draws it in a fallback font
    f'@font-face {{ font-family:"Poppins"; font-weight:{w}; font-display:block; src:url("assets/fonts/poppins-devanagari-{w}-normal.woff2") format("woff2"); unicode-range:{DEV}; }}\n'
    for w in (600, 700, 800, 900)) + "".join(
    f'@font-face {{ font-family:"Inter"; font-weight:{w}; font-display:block; src:url("assets/fonts/inter-latin-ext-{w}-normal.woff2") format("woff2"); unicode-range:{LEXT}; }}\n'
    for w in (600, 700))
CSS_V3 = r"""
/* v3: dark text inside filled boxes must not carry the global dark text-shadow (muddy halo) */
.kl .ba, .kl .bt, .kl .bc, .chip.fill, .tag, .stamp { text-shadow: none; }
/* v3: symbols as inline SVG (font-independent, weight-matched) */
svg.sym { display: inline-block; width: 0.82em; height: 0.82em; vertical-align: -0.08em; overflow: visible;
  fill: none; stroke: currentColor; stroke-width: 3.4; stroke-linecap: round; stroke-linejoin: round; }   /* ~ the stem of 700-800 text */
.kl svg.sym, .arrow svg.sym, .brk svg.sym, .stamp svg.sym, .dtitle svg.sym, .cnum svg.sym, .hd2 svg.sym { stroke-width: 4.2; }   /* 900 text */
/* v3: baked photo grade (photo_grade.py) replaces the per-frame CSS filter */
.baked .bgi img { filter: none; }
.grade-clean #bgshade { background: linear-gradient(180deg, rgba(11,18,32,0.58) 0%, rgba(11,18,32,0.26) 38%, rgba(11,18,32,0.34) 62%, rgba(11,18,32,0.74) 100%),
  radial-gradient(1200px 760px at 50% 46%, rgba(11,18,32,0.34), transparent 75%),
  repeating-linear-gradient(0deg, rgba(148,163,184,0.04) 0 1px, transparent 1px 80px), repeating-linear-gradient(90deg, rgba(148,163,184,0.04) 0 1px, transparent 1px 80px); }
"""
_SYM_PATH = {"→": '<path d="M4.5 12h15"/><path d="m13 5.5 6.5 6.5-6.5 6.5"/>', "←": '<path d="M19.5 12h-15"/><path d="M11 18.5 4.5 12 11 5.5"/>',
             "↑": '<path d="M12 19.5v-15"/><path d="M5.5 11 12 4.5l6.5 6.5"/>', "↓": '<path d="M12 4.5v15"/><path d="M18.5 13 12 19.5 5.5 13"/>',
             "▶": '<path d="M7 4.6v14.8L19.6 12z" fill="currentColor"/>', "✓": '<path d="M20 6.5 9.5 17 4 11.5"/>'}
_SYM_ENT = {"&#8594;": "→", "&rarr;": "→", "&#8592;": "←", "&larr;": "←", "&#8593;": "↑", "&uarr;": "↑", "&#8595;": "↓", "&darr;": "↓",
            "&#9654;": "▶", "&#9658;": "▶", "&#10003;": "✓", "&#10004;": "✓"}

def symbolize(html):
    """Replace arrow / play / check characters in TEXT (not tags, styles or scripts) with inline SVG."""
    parts = re.split(r"(<style\b.*?</style>|<script\b.*?</script>|<[^>]+>)", html, flags=re.S | re.I)
    for k in range(0, len(parts), 2):
        t = parts[k]
        for e, c in _SYM_ENT.items(): t = t.replace(e, c)
        parts[k] = re.sub("[→←↑↓▶✓]", lambda m: f'<svg class="sym" viewBox="0 0 24 24" aria-hidden="true">{_SYM_PATH[m.group(0)]}</svg>', t)
    return "".join(parts)

def icon(name, size=64, color="currentColor"):
    svg = (LIBROOT / f"icons/lucide/{name}.svg").read_text()
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S).strip()
    svg = re.sub(r'width="24"', f'width="{size}"', svg); svg = re.sub(r'height="24"', f'height="{size}"', svg)
    svg = svg.replace('stroke="currentColor"', f'stroke="{color}"').replace('class="', 'class="ic ')
    return " ".join(svg.split())

class Scene:
    def __init__(self, sid, era=None, tag=None, size=(1920, 1080), words=None, dur=None, pre=None):
        """Long-video scene (window from timing.json) or, with words+dur, a standalone piece such as a 9:16 Short
        (words already in its own local time). pre = lead-in seconds before local 0 (default JIG_PRE for every
        chapter except the first): only the first background photo shows there, so the concat can crossfade."""
        self.W, self.H = size
        if words is not None:
            self.id, self.g0 = sid, 0.0; self.dur = fr(dur); self.g1 = self.dur; self.words = words
        else:
            T = timing(); s = next(x for x in T["scenes"] if x["id"] == sid)
            self.id, self.g0, self.g1 = sid, fr(s["start"]), fr(s["end"])
            self.dur = fr(self.g1 - self.g0)
            self.words = [w for w in T["words"] if self.g0 - 0.05 <= w[0] < self.g1]
        self.pre = fr(pre if pre is not None else (PRE_ROLL if self.g0 > 0 else 0.0))
        self.html, self.js, self.sfx, self.assets = [], [], [], set()
        self.era, self.tag, self.n = era, (tag or TAG), 0
        self.boxes, self.bg_html, self.bg_js, self.bg_items, self.baked = [], [], [], [], False

    # ---- timing helpers -------------------------------------------------
    def w(self, tok, n=1, end=False, after=0.0):
        """scene-local time of the n-th word containing tok (case-insensitive), at/after `after`."""
        k = 0
        for a, b, t in self.words:
            if a - self.g0 + 1e-6 < after: continue
            if tok.lower() in t.lower():
                k += 1
                if k == n: return round((b if end else a) - self.g0, 3)
        raise KeyError(f"{self.id}: word '{tok}' #{n} after {after} not found")

    def uid(self, p):
        self.n += 1; return f"{p}{self.n}"

    def cue(self, t, name, db=None):
        kind, ref, g = SFX[name]; self.sfx.append([round(self.g0 + t, 3), kind, ref, g if db is None else db])

    def add(self, html, js=""):
        self.html.append(html); self.js.append(js)

    # ---- generic in/out --------------------------------------------------
    def inout(self, sel, t0, t1, kind="up", dur=0.5):
        f = {"up": "{opacity:0, y:50, filter:'blur(12px)'}", "left": "{opacity:0, x:-80}", "right": "{opacity:0, x:80}",
             "pop": "{opacity:0, scale:0.6}", "fade": "{opacity:0}", "down": "{opacity:0, y:-40}"}[kind]
        to = "{opacity:1, y:0, x:0, scale:1, filter:'blur(0px)', duration:%s, ease:%s}" % (
            dur, "'back.out(2)'" if kind == "pop" else "'power3.out'")
        js = f"tl.fromTo('{sel}', {f}, {to}, {t0});"
        if t1 is not None:
            js += f"tl.to('{sel}', {{opacity:0, filter:'blur(14px)', duration:0.35, ease:'power2.in'}}, {round(t1 - 0.35, 3)});"
        return js

    # ---- markup ------------------------------------------------------------
    @staticmethod
    def markup(main):
        """'*x*' amber box, '#x#' teal box, '_x_' teal, '^x^' amber, '~x~' mute (spans may hold spaces and be followed by
        punctuation). '+' inside a word = non-breaking space; a lone '+' stays a plus sign. Returns [(cls_key, text)]."""
        SP = "\ue000"  # private-use char: str.split() must not break a styled span (U+00A0 counts as whitespace in Python)
        main = re.sub(r"([*#_^~%=])([^*#_^~%=|]+?)\1", lambda m: m.group(1) + m.group(2).strip().replace(" ", SP) + m.group(1), main)
        out = []
        for tok in main.split():
            m = re.match(r"^([*#_^~%=])(.+)\1([.,:;!?]*)$", tok)
            if m:
                out.append((m.group(1), m.group(2).replace("+", " ").replace(SP, " ")))
                if m.group(3): out[-1] = (out[-1][0], out[-1][1]); out.append(("", m.group(3)))
            else:
                out.append(("", tok if tok == "+" else re.sub(r"(?<=\w)\+(?=\w)", " ", tok)))
        return out

    def reserve(self, kind, t0, t1, y0, y1, x0=0, x1=1920):
        self.boxes.append((kind, t0, t1, y0, y1, x0, x1))

    # ---- components ------------------------------------------------------
    def keyline(self, text, t0, t1, y=440, size=110, stagger=0.09, sfx="whoosh", box_at=None, x=None, kinetic=None):
        """Big key phrase. Words >=110px rise letter by letter (kinetic); boxes sweep in at box_at.
        '|' starts a small sub-line."""
        i = self.uid("kl"); main, _, sub = text.partition("|")
        kin = (size >= 110) if kinetic is None else kinetic
        toks = self.markup(main); parts = []; boxes = False
        for k, word in toks:
            if k == "" and re.fullmatch(r"[.,:;!?]+", word) and parts:
                parts[-1] = parts[-1][:-7] + word + "</span>"; continue
            cls = {"*": "w bxw ba", "#": "w bxw bt", "%": "w bxw bc", "_": "w tt", "^": "w ta", "~": "w tm", "=": "w tc", "": "w"}[k]
            if k in "*#%" and k:
                boxes = True; inner = f'<span class="bx"></span>{word}'
            elif kin:
                inner = "".join(f'<span class="ch">{"&nbsp;" if c == " " else c}</span>' for c in re.findall(r"&#?\w+;|.", word))
            else:
                inner = word
            parts.append(f'<span class="{cls}">{inner}</span>')
        html_main = " ".join(parts)
        sub_h = f'<span class="sub w">{sub.strip()}</span>' if sub else ""
        pos = f"left:{x}px;right:auto;text-align:left;" if x is not None else ""
        ba = box_at if box_at is not None else round(t0 + 0.3, 3)
        js = ""
        if kin:
            js += (f"tl.fromTo('#{i} .ch', {{opacity:0, yPercent:90, rotation:8, filter:'blur(6px)'}}, {{opacity:1, yPercent:0, rotation:0, filter:'blur(0px)', duration:0.42, ease:'back.out(1.7)', stagger:0.022}}, {t0});"
                   f"tl.fromTo('#{i} .bxw, #{i} .sub', {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.4, ease:'power3.out', stagger:0.08}}, {t0});")
        else:
            js += f"tl.fromTo('#{i} .w', {{opacity:0, y:46, filter:'blur(12px)'}}, {{opacity:1, y:0, filter:'blur(0px)', duration:0.45, ease:'power3.out', stagger:{stagger}}}, {t0});"
        if boxes:
            js += (f"tl.fromTo('#{i} .bx', {{scaleX:0}}, {{scaleX:1, duration:0.4, ease:'power4.out'}}, {ba});"
                   f"tl.fromTo('#{i} .ba, #{i} .bt, #{i} .bc', {{color:'#f8fafc'}}, {{color:'#0b1220', duration:0.2}}, {ba});")
        if t1: js += f"tl.to('#{i}', {{opacity:0, y:-20, filter:'blur(14px)', duration:0.35, ease:'power2.in'}}, {round(t1 - 0.35, 3)});"
        self.add(f'<div class="kl" id="{i}" style="{pos}top:{y}px;font-size:{size}px">{html_main}{sub_h}</div>', js)
        self.reserve(f"keyline '{text[:24]}'", t0, t1 or self.dur, y, y + size * (1.75 if sub else 1.25), 0 if x is None else x, 1920)
        if sfx: self.cue(t0, sfx)
        if boxes: self.cue(ba, "swish")
        return i

    def typer(self, text, t0, x=None, y=500, size=64, dur=None, t1=None, color="var(--ink)", weight=800, sfx=True, cursor=True,
              font="Poppins", bell=False, center=None, reserve=True):
        """Real-time typewriter text: characters appear one by one with key-click SFX, blinking cursor.
        Markup: ^amber^ and _teal_ spans. x=None -> centred (a hidden ghost copy keeps the line still while typing)."""
        i = self.uid("ty")
        segs = []  # (char, cls)
        for m in re.finditer(r"\^([^^]+)\^|_([^_]+)_|([^^_]+)", text):
            seg, cls = (m.group(1), "ta") if m.group(1) else ((m.group(2), "tt") if m.group(2) else (m.group(3), ""))
            for c in re.findall(r"&#?\w+;|.", seg): segs.append((c, cls))
        n = len(segs)
        dur = dur if dur is not None else min(2.2, max(0.5, n * 0.055))
        times = self._type_times(segs, t0, dur, i)
        ghost = "".join(f'<span class="{c2}">{c}</span>' for c, c2 in segs)
        live = "".join(f'<span class="c {c2}" id="{i}c{k}">{c}</span>' for k, (c, c2) in enumerate(segs))
        cur = f'<span class="cur" id="{i}k"></span>' if cursor else ""
        cen = (x is None) if center is None else center
        pos = "left:0;right:0;text-align:center;" if cen else f"left:{x}px;"
        self.add(f'<div class="ty" id="{i}" style="{pos}top:{y}px;font:{weight} {size}px {font};color:{color}">'
                 f'<span class="tyw"><span class="gh">{ghost}</span><span class="lv">{live}{cur}</span></span></div>', "")
        js = [f"tl.fromTo('#{i}', {{opacity:0}}, {{opacity:1, duration:0.01}}, {t0});"]
        last = -9.0
        for k in range(n):
            t = times[k]
            js.append(f"tl.set('#{i}c{k}', {{display:'inline'}}, {t});")
            if sfx and segs[k][0] not in (" ", "&nbsp;") and t - last >= KEY_GAP:   # v3: max ~13 clicks/s
                last = t; ref = KEYS[(k * 7 + self.n) % len(KEYS)]
                self.sfx.append([round(self.g0 + t, 3), "key", ref, -25 + ((k * 5) % 4) - 2])
        if cursor:  # cursor only while typing, gone right after (user 2026-10-15)
            js.append(f"tl.set('#{i}k', {{opacity:0}}, {round(t0 + dur + 0.15, 3)});")
        if bell: self.cue(t0 + dur + 0.05, "bell")
        if t1: js.append(f"tl.to('#{i}', {{opacity:0, filter:'blur(12px)', duration:0.3, ease:'power2.in'}}, {round(t1 - 0.3, 3)});")
        self.js[-1] = "".join(js)
        if reserve:
            wpx = n * size * 0.58
            x0_ = 960 - wpx / 2 if cen else x
            self.reserve(f"typer '{text[:24]}'", t0, t1 or self.dur, y, y + size * 1.3, x0_, x0_ + wpx)
        return i

    def _type_times(self, segs, t0, dur, seed):
        """v3 human typing rhythm: +-30 % jitter, a beat after spaces, a longer one after punctuation (deterministic)."""
        rnd = random.Random(f"{self.id}:{seed}")
        w = [(1.35 if c in (" ", "&nbsp;") else 1.9 if c in ",.;:!?|–—" else 1.0) * rnd.uniform(0.7, 1.3) for c, _ in segs]
        tot = sum(w) or 1.0; out, acc = [], 0.0
        for x in w: out.append(round(t0 + dur * acc / tot, 3)); acc += x
        return out

    def stamp(self, text, t0, t1, y=260, size=96, color="am", rot=-4, x=None):  # color: am | tl | co
        """Rubber-stamp slam (dates, verdicts): scales down from 2.4x with a metal + typewriter hit."""
        i = self.uid("st")
        pos = "" if x is None else f"left:{x}px;right:auto;text-align:left;"
        self.add(f'<div class="stw" id="{i}w" style="{pos}top:{y}px"><span class="stamp {color if color in ("tl", "co") else ""}" id="{i}" style="font-size:{size}px">{text}</span></div>',
                 f"tl.fromTo('#{i}', {{opacity:0, scale:2.4, rotation:{rot - 6}}}, {{opacity:1, scale:1, rotation:{rot}, duration:0.24, ease:'power4.in'}}, {t0});"
                 f"tl.fromTo('#{i}w', {{x:0}}, {{x:8, duration:0.04, yoyo:true, repeat:3, ease:'none'}}, {round(t0 + 0.24, 3)});"
                 f"tl.to('#{i}w', {{opacity:0, filter:'blur(12px)', duration:0.3, ease:'power2.in'}}, {round(t1 - 0.3, 3)});")
        self.cue(t0 + 0.2, "thud"); self.cue(t0 + 0.21, "type", -21)
        self.reserve(f"stamp '{text}'", t0, t1, y, y + size * 1.3)
        return i

    def bgs(self, items, credit_y=80):
        """Full-bleed topic photo backgrounds: items = [(src, t, credit)], each shows from t until the next one
        (crossfade 0.8 s), slow Ken Burns, navy tint + grid on top (#bgshade)."""
        for src, t, cred in items:
            self.assets.add(src); self.bg_items.append((src, t, cred))   # v3: JS made in write() (pre-roll aware)

    def _bg_parts(self, P):
        html, js, it = [], [], self.bg_items
        for k, (src, t, cred) in enumerate(it):
            nxt = it[k + 1][1] if k + 1 < len(it) else self.dur
            i = f"bgi{k}"; first = t <= 0.05; sx = (-30, 30) if k % 2 == 0 else (30, -30)
            st = 0.0 if first else round(max(0.0, t - 0.4) + P, 3); d = round(nxt - t + 1.0 + (P if first else 0.0), 3)
            html.append(f'<div class="bgi" id="{i}"><img src="assets/{Path(src).name}" alt="" /></div><div class="bgcred" id="{i}c">{cred}</div>')
            js.append((f"tl.set('#{i}', {{opacity:1}}, 0);" if first else
                       f"tl.fromTo('#{i}', {{opacity:0}}, {{opacity:1, duration:0.8, ease:'power1.inOut'}}, {st});")
                      + f"tl.fromTo('#{i} img', {{scale:1.0, x:{sx[0]}}}, {{scale:1.09, x:{sx[1]}, duration:{d}, ease:'none'}}, {st});"
                      + f"tl.fromTo('#{i}c', {{opacity:0}}, {{opacity:1, duration:0.4}}, {round(t + P + 0.3, 3)});"
                      + (f"tl.to('#{i}c', {{opacity:0, duration:0.3}}, {round(nxt + P - 0.3, 3)});" if k + 1 < len(it) else ""))
        return html, js

    def datecard(self, date, title, t0, t1, sub=None, y=250, title_at=None, sub_at=None, title_dur=None):
        """Date stamp + typed title + small sub line."""
        i = self.uid("dc")
        self.stamp(date, t0, t1, y=y, size=74)
        ta = title_at or round(t0 + 0.45, 3)
        self.typer(title, ta, y=y + 150, size=96 if len(title) <= 26 else 76, weight=900, dur=title_dur, t1=t1)
        if sub:
            self.add(f'<div class="dsub" id="{i}s" style="top:{y + 300}px">{sub}</div>',
                     f"tl.fromTo('#{i}s', {{opacity:0, y:20, scaleX:1.15}}, {{opacity:1, y:0, scaleX:1, duration:0.6, ease:'power3.out'}}, {sub_at or round(ta + 0.8, 3)});"
                     f"tl.to('#{i}s', {{opacity:0, filter:'blur(12px)', duration:0.3}}, {round(t1 - 0.3, 3)});")
        return i

    def photo(self, src, t0, t1, credit, box=(1000, 200, 760, 620), full=False, zoom=(1.0, 1.08), pan=(-30, 30), caption=None, grade=False):
        """grade=True: B&W + cool teal tint so portraits match the video's tone."""
        i = self.uid("ph"); self.assets.add(src)
        if full:
            h = f'<div class="ph full" id="{i}"><img src="assets/{Path(src).name}" alt="" /></div><div class="phcap" id="{i}c" style="left:64px;bottom:90px">{credit}</div>'
        else:
            x, y, w, hh = box
            h = (f'<div class="ph{" gr" if grade else ""}" id="{i}" style="left:{x}px;top:{y}px;width:{w}px;height:{hh}px"><img src="assets/{Path(src).name}" alt="" /></div>'
                 f'<div class="phcap" id="{i}c" style="left:{x}px;top:{y + hh + 14}px">{credit}</div>')
            if caption: h += f'<div class="abs" id="{i}k" style="left:{x}px;top:{y + hh + 48}px;font:700 34px Inter;color:#cbd5e1;white-space:nowrap">{caption}</div>'
        d = round(t1 - t0, 3)
        js = (f"tl.fromTo('#{i}', {{opacity:0, y:{0 if full else 60}}}, {{opacity:1, y:0, duration:0.55, ease:'power3.out'}}, {t0});"
              f"tl.fromTo('#{i} img', {{scale:{zoom[0]}, x:{pan[0]}}}, {{scale:{zoom[1]}, x:{pan[1]}, duration:{d}, ease:'none'}}, {t0});"
              f"tl.fromTo('#{i}c', {{opacity:0}}, {{opacity:1, duration:0.4}}, {round(t0 + 0.3, 3)});"
              f"tl.to(['#{i}', '#{i}c'], {{opacity:0, duration:0.4, ease:'power2.in'}}, {round(t1 - 0.4, 3)});")
        if caption: js += self.inout(f"#{i}k", round(t0 + 0.5, 3), t1, "up")
        self.add(h, js); self.cue(t0, "whoosh")
        return i

    def lower(self, name, role, t0, t1, x=120, y=800):
        """Lower third: name typed with key clicks, role fades in."""
        i = self.uid("lt")
        self.add(f'<div class="lower" id="{i}" style="left:{x}px;top:{y}px"><div class="bar"></div><div class="tx"><div class="nm" style="height:52px">&nbsp;</div><div class="rl">{role}</div></div></div>',
                 f"tl.fromTo('#{i}', {{opacity:0, x:-60}}, {{opacity:1, x:0, duration:0.4, ease:'power3.out'}}, {t0});"
                 f"tl.fromTo('#{i} .rl', {{opacity:0}}, {{opacity:1, duration:0.4}}, {round(t0 + 0.6, 3)});"
                 f"tl.to('#{i}', {{opacity:0, x:-40, duration:0.35, ease:'power2.in'}}, {round(t1 - 0.35, 3)});")
        self.typer(name, round(t0 + 0.15, 3), x=x + 38, y=y + 10, size=46, weight=800, t1=t1, dur=min(1.2, len(name) * 0.045))
        self.cue(t0, "swoosh")

    def numlist(self, items, times, t1, x=140, y=260, pitch=150, title=None, title_t=None, dim=True, amber=()):
        """items: (num, head, sub, icon or None). Outline numerals, underline sweep under each head."""
        i = self.uid("nl"); h = [f'<div class="nl abs" id="{i}" style="left:{x}px;top:{y}px">']
        if title: h.append(f'<div class="abs" id="{i}h" style="left:0;top:-120px;font-weight:900;font-size:72px;white-space:nowrap">{title}</div>')
        for k, (num, head, sub, ic) in enumerate(items):
            icn = icon(ic, 64, "#2dd4bf") if ic else ""
            am = " am" if k in amber else ""
            h.append(f'<div class="it" id="{i}i{k}" style="top:{k * pitch}px"><div class="nb{am}">{num}</div>'
                     f'<div><div class="hd">{head} {icn}<div class="ul{am}" id="{i}u{k}"></div></div>' + (f'<div class="sd">{sub}</div>' if sub else "") + "</div></div>")
        h.append("</div>")
        js = ""
        if title: js += self.inout(f"#{i}h", title_t if title_t is not None else round(times[0] - 0.4, 3), None, "left")
        for k, t in enumerate(times):
            js += (f"tl.fromTo('#{i}i{k}', {{opacity:0, x:-70}}, {{opacity:1, x:0, duration:0.45, ease:'power3.out'}}, {t});"
                   f"tl.fromTo('#{i}i{k} .nb', {{opacity:0, scale:1.8}}, {{opacity:1, scale:1, duration:0.35, ease:'power3.out'}}, {t});"
                   f"tl.fromTo('#{i}u{k}', {{scaleX:0}}, {{scaleX:1, duration:0.5, ease:'power3.inOut'}}, {round(t + 0.2, 3)});")
            if dim and k > 0: js += f"tl.to('#{i}i{k - 1}', {{opacity:0.45, duration:0.3}}, {t});"
            self.cue(t, "click")
        if dim: js += f"tl.to('#{i} .it', {{opacity:1, duration:0.3}}, {round(times[-1] + 1.2, 3)});"
        js += f"tl.to('#{i}', {{opacity:0, filter:'blur(14px)', duration:0.35, ease:'power2.in'}}, {round(t1 - 0.35, 3)});"
        self.add("".join(h), js)
        self.reserve("numlist", times[0], t1, y - (120 if title else 0), y + pitch * len(items), x, 1920)
        return i

    def cards(self, cards, times, t1, y=300, h=480, gap=60, x0=120, width=1680, big=150):
        """Editorial columns (no boxes): accent rule draws in, big value rises letter by letter, title + sub fade up.
        cards: (big, title, sub, color 'am'|'tl'|'', tag or None)"""
        i = self.uid("cd"); n = len(cards); cw = (width - gap * (n - 1)) / n; out = []; js = ""
        for k, (bg, ttl, sb, col, tg) in enumerate(cards):
            c = {"am": "var(--amber)", "tl": "var(--teal)"}.get(col, "var(--ink)")
            big_h = bg if bg.lstrip().startswith("<") else "".join(f'<span class="ch">{"&nbsp;" if ch == " " else ch}</span>' for ch in re.findall(r"&#?\w+;|.", bg))
            out.append(f'<div class="card {col}" id="{i}c{k}" style="left:{x0 + k * (cw + gap):.0f}px;top:{y}px;width:{cw:.0f}px">'
                       f'<div class="rule" id="{i}r{k}"></div>'
                       + (f'<div class="tag {col or "mu"}" style="margin-bottom:22px">{tg}</div>' if tg else "")
                       + f'<div class="big" style="font-size:{big}px;color:{c}">{big_h}</div><div class="ttl" style="margin-top:18px">{ttl}</div>'
                       + (f'<div class="sb">{sb}</div>' if sb else "") + "</div>")
            t = times[k]
            js += (f"tl.fromTo('#{i}c{k}', {{opacity:0}}, {{opacity:1, duration:0.2}}, {t});"
                   f"tl.fromTo('#{i}r{k}', {{scaleX:0}}, {{scaleX:1, duration:0.5, ease:'power3.inOut'}}, {t});"
                   f"tl.fromTo('#{i}c{k} .big .ch, #{i}c{k} .big > svg', {{opacity:0, yPercent:80, rotation:6}}, {{opacity:1, yPercent:0, rotation:0, duration:0.4, ease:'back.out(1.8)', stagger:0.035}}, {round(t + 0.15, 3)});"
                   f"tl.fromTo('#{i}c{k} .ttl, #{i}c{k} .sb, #{i}c{k} .tag', {{opacity:0, y:24}}, {{opacity:1, y:0, duration:0.4, ease:'power3.out', stagger:0.08}}, {round(t + 0.35, 3)});")
            self.cue(t, "swish"); self.cue(t + 0.15, "pop", -21)
        js += f"tl.to('#{i} .card', {{opacity:0, y:-30, filter:'blur(12px)', duration:0.35, ease:'power2.in', stagger:0.05}}, {round(t1 - 0.45, 3)});"
        self.add(f'<div id="{i}">' + "".join(out) + "</div>", js)
        self.reserve("cards", times[0], t1, y, y + h, x0, x0 + width)
        return i

    def chips(self, labels, times, t1, y=760, color="", fill=False, x0=None, gap=26, size=38):
        i = self.uid("ch"); wd = [len(re.sub(r'&\w+;', 'x', l)) * size * 0.7 + 80 for l in labels]; tot = sum(wd) + gap * (len(labels) - 1)
        x = (self.W - tot) / 2 if x0 is None else x0; out = []
        for k, l in enumerate(labels):
            out.append(f'<div class="chip {color}{" fill" if fill else ""}" id="{i}c{k}" style="left:{x:.0f}px;top:{y}px;font-size:{size}px">{l}</div>'); x += wd[k] + gap
        js = "".join(f"tl.fromTo('#{i}c{k}', {{opacity:0, scale:0.6, y:20}}, {{opacity:1, scale:1, y:0, duration:0.4, ease:'back.out(2.4)'}}, {t});" for k, t in enumerate(times))
        js += f"tl.to('#{i} .chip', {{opacity:0, duration:0.3}}, {round(t1 - 0.3, 3)});"
        for t in times: self.cue(t, "pop2")
        self.add(f'<div id="{i}">' + "".join(out) + "</div>", js)
        return i

    def swap(self, old, new, t0, tnew, t1, y=300, h=420, mid=None, big=110, type_old=None, type_new=None):
        """Old -> new (no boxes). old/new: (tag, name, full form [typed], extra). Old name amber + strike drawn
        exactly across it at tnew; new name teal; full forms type out under each (type_x = (start, dur))."""
        i = self.uid("sw")
        def col(c, side, k):
            tg, bg, ttl, sb = c
            x = 140 if k == "o" else 1060; cc = "var(--coral)" if side == "co" else "var(--teal)"
            return (f'<div class="abs" id="{i}{k}" style="left:{x}px;top:{y}px;width:740px">'
                    f'<div class="tag {side}">{tg}</div>'
                    f'<div style="margin-top:22px"><span class="abs-r" style="position:relative;display:inline-block;font-weight:900;font-size:{big}px;line-height:1.05;color:{cc};white-space:nowrap">{bg}'
                    + (f'<span class="strike" id="{i}s" style="left:-3%;width:106%;top:48%;transform:rotate(-4deg)"></span>' if k == "o" else "") + '</span></div>'
                    + '</div>')
        hh = (col(old, "co", "o") + f'<div class="arrow" id="{i}a" style="left:910px;top:{y + 60}px">&#8594;</div>' + col(new, "tl", "n"))
        js = (f"tl.fromTo('#{i}o', {{opacity:0, x:-80}}, {{opacity:1, x:0, duration:0.5, ease:'power3.out'}}, {t0});"
              f"tl.fromTo('#{i}s', {{scaleX:0}}, {{scaleX:1, duration:0.3, ease:'power4.out'}}, {tnew});"
              f"tl.to('#{i}o', {{opacity:0.55, duration:0.4}}, {tnew});"
              f"tl.fromTo('#{i}a', {{opacity:0, x:-40}}, {{opacity:1, x:0, duration:0.4, ease:'power3.out'}}, {tnew});"
              f"tl.fromTo('#{i}n', {{opacity:0, x:80}}, {{opacity:1, x:0, duration:0.5, ease:'back.out(1.6)'}}, {round(tnew + 0.15, 3)});"
              f"tl.to(['#{i}o','#{i}n','#{i}a'], {{opacity:0, filter:'blur(14px)', duration:0.35, ease:'power2.in'}}, {round(t1 - 0.35, 3)});")
        self.add(f'<div id="{i}">{hh}</div>', js)
        fy = y + 48 + 22 + int(big * 1.05) + 22   # tag pill + gap + name -> typed full form line
        for c, xx, kk in ((old, 140, "o"), (new, 1060, "n")):   # small extra line sits BELOW the typed full form
            if c[3]:
                self.add(f'<div class="abs" id="{i}{kk}x" style="left:{xx}px;top:{fy + 52}px;font:600 28px Inter;color:#94a3b8;white-space:nowrap">{c[3]}</div>',
                         f"tl.fromTo('#{i}{kk}x', {{opacity:0, y:12}}, {{opacity:1, y:0, duration:0.4}}, {round((t0 if kk == 'o' else tnew) + 1.2, 3)});"
                         f"tl.to('#{i}{kk}x', {{opacity:0, duration:0.3}}, {round(t1 - 0.35, 3)});")
        if old[2]:
            a, d = type_old or (round(t0 + 0.35, 3), None)
            self.typer(old[2], a, x=140, y=fy, size=30, weight=600, font="Inter", color="#cbd5e1", t1=t1, dur=d, reserve=False)
        if new[2]:
            a, d = type_new or (round(tnew + 0.45, 3), None)
            self.typer(new[2], a, x=1060, y=fy, size=30, weight=600, font="Inter", color="#f8fafc", t1=t1, dur=d, reserve=False)
        self.cue(t0, "swoosh"); self.cue(tnew, "grill"); self.cue(tnew + 0.15, "gear")
        self.reserve("swap", t0, t1, y, y + h)
        return i

    def counter(self, vals, t1, x, y, w=500, h=360, size=340, label=None, label_y=None, colors=None):
        """vals: [(text, t)]. Numeric values (e.g. '180', '500+', '78,000', '₹28,400 cr') COUNT like an odometer:
        first value counts up from 0, each next value counts from the previous one; colour follows `colors`."""
        i = self.uid("ct"); colors = colors or ["var(--ink)"] * len(vals)
        HEX = {"var(--teal)": "#2dd4bf", "var(--amber)": "#fbbf24", "var(--coral)": "#ff6b6b", "var(--ink)": "#f8fafc", "var(--mute)": "#94a3b8"}
        colors = [HEX.get(c, c) for c in colors]  # GSAP cannot tween CSS var() colours (dark flash mid-tween)
        num = lambda v: re.fullmatch(r"(\D*?)([\d,]+)(\D*)", v)
        parsed = [num(v) for v, _ in vals]
        lab = (f'<div class="abs" id="{i}l" style="left:{x}px;width:{w}px;top:{label_y or y + h}px;text-align:center;font:800 40px Poppins;'
               f'color:var(--mute);letter-spacing:0.08em;white-space:nowrap">{label}</div>') if label else ""
        js = ""
        if all(parsed):
            pre, suf = parsed[-1].group(1), parsed[-1].group(3)
            nums = [int(m.group(2).replace(",", "")) for m in parsed]
            hh = (f'<div class="cnt" id="{i}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">'
                  f'<div class="dg" id="{i}d" style="height:{h}px;line-height:{h}px;font-size:{size}px;color:{colors[0]}">{pre}0{suf}</div></div>' + lab)
            fmt = "Math.round(o.v).toLocaleString('en-IN')"
            js += f"tl.fromTo('#{i}d', {{opacity:0, scale:0.5}}, {{opacity:1, scale:1, duration:0.4, ease:'back.out(2)'}}, {vals[0][1]});"
            prev = 0
            for k, (n, (v, t)) in enumerate(zip(nums, vals)):
                p_, s_ = parsed[k].group(1), parsed[k].group(3)
                d = 0.9 if k == 0 else 0.75
                js += (f"(() => {{ const el = document.getElementById('{i}d'); const o = {{v:{prev}}};"
                       f" tl.fromTo(o, {{v:{prev}}}, {{v:{n}, duration:{d}, ease:'power2.out', immediateRender:false,"
                       f" onUpdate:() => {{ el.textContent = '{p_}' + {fmt} + '{s_}'; }} }}, {t}); }})();")
                if k: js += f"tl.to('#{i}d', {{color:'{colors[k]}', duration:0.3}}, {t});"
                prev = n
                tk = t
                while tk < t + d - 0.05: self.cue(tk, "tick", -27); tk += 0.09
            self.add(hh, js)
        else:  # non-numeric: digit roll (old behaviour)
            out = [f'<div class="dg" id="{i}d{k}" style="height:{h}px;line-height:{h}px;font-size:{size}px;color:{colors[k]}">{v}</div>' for k, (v, t) in enumerate(vals)]
            hh = f'<div class="cnt" id="{i}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">' + "".join(out) + "</div>" + lab
            js += f"tl.fromTo('#{i}d0', {{opacity:0, scale:0.4}}, {{opacity:1, scale:1, duration:0.45, ease:'back.out(2)'}}, {vals[0][1]});"
            for k in range(1, len(vals)): js += f"tl.set('#{i}d{k}', {{yPercent:100}}, 0);"
            for k in range(1, len(vals)):
                t = vals[k][1]
                js += (f"tl.to('#{i}d{k - 1}', {{yPercent:-100, duration:0.35, ease:'power3.in'}}, {round(t - 0.06, 3)});"
                       f"tl.to('#{i}d{k}', {{yPercent:0, duration:0.45, ease:'back.out(1.6)'}}, {t});")
                self.cue(t, "gear")
            self.add(hh, js)
        js2 = self.inout(f"#{i}l", vals[0][1] + 0.2, None, "up") if label else ""
        js2 += f"tl.to(['#{i}'{', ' + repr('#' + i + 'l') if label else ''}], {{opacity:0, filter:'blur(14px)', duration:0.35, ease:'power2.in'}}, {round(t1 - 0.35, 3)});"
        self.js[-1] += js2
        self.cue(vals[0][1], "pop")
        self.reserve("counter", vals[0][1], t1, y, (label_y or y + h) + 50, x, x + w)
        return i

    def table(self, cols, rows, times, t1, x=160, y=300, widths=None, rh=120, gap=22, hl=None):
        """cols: header labels; rows: list of cell lists (cell may contain html). hl: {row: 'tl'|'am'}"""
        i = self.uid("tb"); widths = widths or [1600 // len(cols)] * len(cols); W = sum(widths); out = []
        out.append(f'<div class="row hd" id="{i}h" style="top:0;width:{W}px;height:60px">' +
                   "".join(f'<div class="cell" style="width:{wd}px;font-size:28px">{c}</div>' for c, wd in zip(cols, widths)) + "</div>")
        for k, r in enumerate(rows):
            st = ""
            out.append(f'<div class="row bd{" hl" if (hl or {}).get(k) else ""}" id="{i}r{k}" style="top:{80 + k * (rh + gap)}px;width:{W}px;height:{rh}px;{st}">' +
                       "".join(f'<div class="cell" style="width:{wd}px">{c}</div>' for c, wd in zip(r, widths)) + "</div>")
        js = self.inout(f"#{i}h", round(times[0] - 0.3, 3), None, "fade")
        for k, t in enumerate(times):
            js += f"tl.fromTo('#{i}r{k}', {{opacity:0, x:-60}}, {{opacity:1, x:0, duration:0.45, ease:'power3.out'}}, {t});"; self.cue(t, "click")
        js += f"tl.to('#{i}', {{opacity:0, filter:'blur(14px)', duration:0.35, ease:'power2.in'}}, {round(t1 - 0.35, 3)});"
        self.add(f'<div class="tb" id="{i}" style="left:{x}px;top:{y}px">' + "".join(out) + "</div>", js)
        return i

    def timeline(self, nodes, t1, y=520, x0=220, x1=1700, draw_t=None):
        """nodes: (year, label, t, color 'tl'|'am')"""
        i = self.uid("tn"); n = len(nodes); xs = [x0 + (x1 - x0) * k / max(1, n - 1) for k in range(n)]
        h = [f'<div class="tln abs" id="{i}" style="left:0;top:0;width:1920px;height:1080px">',
             f'<div class="ln" style="left:{x0}px;top:{y}px;width:{x1 - x0}px"></div>',
             f'<div class="lnf" id="{i}f" style="left:{x0}px;top:{y}px;width:{x1 - x0}px"></div>']
        js = f"tl.fromTo('#{i} .ln', {{opacity:0}}, {{opacity:1, duration:0.4}}, {draw_t if draw_t is not None else round(nodes[0][2] - 0.4, 3)});"
        js += f"tl.set('#{i}f', {{scaleX:0}}, 0);"
        for k, (yr, lb, t, col) in enumerate(nodes):
            c = "var(--amber)" if col == "am" else "var(--teal)"
            h.append(f'<div class="nd" id="{i}n{k}" style="left:{xs[k]:.0f}px;top:{y}px;border-color:{c}"></div>'
                     f'<div class="yr" id="{i}y{k}" style="left:{xs[k]:.0f}px;top:{y - 120}px;color:{c}">{yr}</div>'
                     f'<div class="lb" id="{i}l{k}" style="left:{xs[k]:.0f}px;top:{y + 50}px">{lb}</div>')
            js += (f"tl.to('#{i}f', {{scaleX:{(xs[k] - x0) / (x1 - x0):.4f}, duration:0.5, ease:'power2.inOut'}}, {round(t - 0.25, 3)});"
                   f"tl.fromTo('#{i}n{k}', {{scale:0}}, {{scale:1, duration:0.4, ease:'back.out(3)'}}, {t});"
                   f"tl.fromTo('#{i}y{k}', {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.45, ease:'power3.out'}}, {t});"
                   f"tl.fromTo('#{i}l{k}', {{opacity:0, y:-20}}, {{opacity:1, y:0, duration:0.45, ease:'power3.out'}}, {round(t + 0.12, 3)});")
            self.cue(t, "tick")
        h.append("</div>")
        js += f"tl.to('#{i}', {{opacity:0, filter:'blur(14px)', duration:0.35, ease:'power2.in'}}, {round(t1 - 0.35, 3)});"
        self.add("".join(h), js)
        return i

    def india_map(self, pins, t0, t1, x=1010, y=150, scale=0.95, states=()):
        """pins: (name, lon, lat, sub, t, dx, dy) - official India outline (datameet).
        states: [(svg path d in india_view units, t)] highlighted (amber) when their plant is named."""
        i = self.uid("mp"); v = MAP["india_view"]; c = math.cos(math.radians(22))
        P = lambda lon, lat: ((lon - 67.5) * c * 30 * scale + x, (37.6 - lat) * 30 * scale + y)
        st_svg = "".join(f'<path class="m-state" id="{i}s{k}" d="{d}"/>' for k, (d, t) in enumerate(states))
        h = [f'<div class="mapw" id="{i}" style="left:0;top:0;width:1920px;height:1080px">',
             f'<svg class="abs" style="left:{x}px;top:{y}px" width="{848 * scale:.0f}" height="{948 * scale:.0f}" viewBox="0 0 848 948">'
             f'<path class="m-in" d="{v["india"]}"/><path class="m-jk" d="{v["jk"]}"/><path class="m-jk" d="{v["ladakh"]}"/>{st_svg}</svg>']
        js = f"tl.fromTo('#{i}', {{opacity:0, scale:1.08}}, {{opacity:1, scale:1, duration:0.7, ease:'power3.out'}}, {t0});"
        for k, (d, t) in enumerate(states):
            js += f"tl.to('#{i}s{k}', {{fill:'rgba(251,191,36,0.28)', stroke:'rgba(251,191,36,0.95)', duration:0.4}}, {t});"
        for k, (nm, lon, lat, sub, t, dx, dy) in enumerate(pins):
            px, py = P(lon, lat)
            h.append(f'<div class="pin" id="{i}p{k}" style="left:{px:.0f}px;top:{py:.0f}px"><div class="dot"></div>'
                     f'<div class="pl" style="left:{dx}px;top:{dy}px">{nm}<span class="ps">{sub}</span></div></div>')
            js += (f"tl.fromTo('#{i}p{k} .dot', {{scale:0}}, {{scale:1, duration:0.4, ease:'back.out(3)'}}, {t});"
                   f"tl.fromTo('#{i}p{k} .dot', {{boxShadow:'0 0 0 0px rgba(251,191,36,0.6)'}}, {{boxShadow:'0 0 0 34px rgba(251,191,36,0)', duration:0.9, ease:'power2.out'}}, {t});"
                   f"tl.fromTo('#{i}p{k} .pl', {{opacity:0, x:-20}}, {{opacity:1, x:0, duration:0.4, ease:'power3.out'}}, {round(t + 0.1, 3)});")
            self.cue(t, "ping")
        h.append("</div>")
        js += f"tl.to('#{i}', {{opacity:0, duration:0.4, ease:'power2.in'}}, {round(t1 - 0.4, 3)});"
        self.add("".join(h), js); self.cue(t0, "whoosh")
        return i

    def breaker(self, label, sub, t=0.0, dur=0.85):
        """Chapter breaker: full-screen era title that zooms through at the start of a new era (sits in the pause)."""
        i = self.uid("bk")
        chs = "".join(f'<span class="ch">{"&nbsp;" if ch == " " else ch}</span>' for ch in re.findall(r"&#?\w+;|.", label))
        self.add(f'<div class="brk" id="{i}"><div class="bl">{chs}</div><div class="bs">{sub}</div></div>',
                 f"tl.fromTo('#{i}', {{opacity:0}}, {{opacity:1, duration:0.12}}, {t});"
                 f"tl.fromTo('#{i} .ch', {{opacity:0, yPercent:70, scale:0.6}}, {{opacity:1, yPercent:0, scale:1, duration:0.35, ease:'back.out(1.8)', stagger:0.025}}, {t});"
                 f"tl.fromTo('#{i} .bs', {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.3}}, {round(t + 0.15, 3)});"
                 f"tl.to('#{i}', {{opacity:0, scale:1.35, filter:'blur(18px)', duration:0.3, ease:'power2.in'}}, {round(t + dur - 0.3, 3)});")
        self.cue(t, "fast"); self.cue(t + 0.12, "deep", -17)
        return i

    def jk_map(self, t0, t1, x=980, y=180, scale=1.0, label_t=None):
        i = self.uid("jk"); v = MAP["jk_view"]
        h = (f'<div class="mapw" id="{i}" style="left:0;top:0;width:1920px;height:1080px">'
             f'<svg class="abs" style="left:{x}px;top:{y}px" width="{821 * scale:.0f}" height="{618 * scale:.0f}" viewBox="0 0 821 618">'
             f'<path class="m-st" d="{v["hp"]}"/><path class="m-st" d="{v["punjab"]}"/>'
             f'<path class="m-jk" id="{i}j" d="{v["jk"]}"/><path class="m-st" d="{v["ladakh"]}" style="fill:#16203a"/></svg>'
             f'<div class="abs" id="{i}l" style="left:{x + 200 * scale:.0f}px;top:{y + 330 * scale:.0f}px;font:900 54px Poppins;color:var(--teal);letter-spacing:0.08em;white-space:nowrap">J&amp;K UT</div></div>')
        js = (f"tl.fromTo('#{i}', {{opacity:0, scale:1.1}}, {{opacity:1, scale:1, duration:0.8, ease:'power3.out'}}, {t0});"
              f"tl.fromTo('#{i}l', {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.45, ease:'power3.out'}}, {label_t or round(t0 + 0.6, 3)});"
              f"tl.to('#{i}', {{opacity:0, duration:0.4}}, {round(t1 - 0.4, 3)});")
        self.add(h, js); self.cue(t0, "whoosh")
        return i

    def captions(self, phrases, y=1400, size=66, right=60):
        """NOT for Shorts any more (user 2026-10-17: no running caption line). Long videos: ask first.
        Bold word-group captions (watched muted). phrases: [(t, text)] with *word* = amber keyword;
        each phrase shows until the next one (max 2.6 s)."""
        h, js = [], []
        for k, (t, text) in enumerate(phrases):
            i = f"cap{k}"; nxt = phrases[k + 1][0] if k + 1 < len(phrases) else self.dur
            body = re.sub(r"\*([^*]+)\*", r"<span class='ta'>\1</span>", text)
            h.append(f'<div class="abs" id="{i}" style="left:60px;right:{right}px;top:{y}px;text-align:center;opacity:0">'
                     f'<span style="display:inline-block;padding:10px 30px 14px;border-radius:22px;background:rgba(11,18,32,0.82);'
                     f'font:900 {size}px Poppins;line-height:1.15;color:#f8fafc;text-shadow:none">{body}</span></div>')
            js.append(f"tl.fromTo('#{i}', {{opacity:0, scale:0.86, y:18}}, {{opacity:1, scale:1, y:0, duration:0.16, ease:'back.out(2)'}}, {round(t, 3)});"
                      f"tl.set('#{i}', {{opacity:0}}, {round(min(nxt, t + 2.6), 3)});")
        self.add("".join(h), "".join(js))

    def raw(self, html, js="", sfx=()):
        self.add(html, js)
        for t, n in sfx: self.cue(t, n)

    # ---- output ----------------------------------------------------------
    def check_overlaps(self):
        """Warn when two text blocks share screen space at the same time (the s09 '1991 ke baad' + 'SSI' bug)."""
        bad = []
        for a in range(len(self.boxes)):
            for b in range(a + 1, len(self.boxes)):
                ka, a0, a1, ay0, ay1, ax0, ax1 = self.boxes[a]; kb, b0, b1, by0, by1, bx0, bx1 = self.boxes[b]
                t_ov = min(a1, b1) - max(a0, b0); y_ov = min(ay1, by1) - max(ay0, by0); x_ov = min(ax1, bx1) - max(ax0, bx0)
                if t_ov > 0.45 and y_ov > 12 and x_ov > 40:
                    bad.append(f"  {self.id}: {ka} [{a0:.1f}-{a1:.1f}] x {kb} [{b0:.1f}-{b1:.1f}]  y-overlap {y_ov:.0f}px")
        return bad

    def write(self, outdir, export=False, grade="clean", fonts=None, gsap=None):   # clean = user pick 2026-10-17
        """Write <outdir>/<id>/index.html (+ hyperframes.json, meta.json). export=True also copies fonts, GSAP and the
        photos (resized to the canvas width; grade='deep'|'clean' bakes background photos with photo_grade.py)."""
        d = Path(outdir) / self.id; d.mkdir(parents=True, exist_ok=True)
        bad = self.check_overlaps()
        for line in bad: print("OVERLAP", line)
        if bad and os.environ.get("JIG_STRICT"): raise SystemExit(f"{self.id}: {len(bad)} overlapping text blocks (JIG_STRICT=1)")
        if export and grade: self.baked = grade
        P = self.pre; T = fr(self.dur + P)
        era = ""
        if self.era is not None and ERAS:
            era = '<div id="era">' + "".join(
                f'<div class="e{" on" if k == self.era else (" done" if 0 <= k < self.era else "")}">{e}</div>' for k, e in enumerate(ERAS)) + "</div>"
        bgh, bgj = self._bg_parts(P)
        content_js = "\n".join(j for j in self.js if j)
        raw_bg = "\n".join(self.bg_js)
        if P:   # content (and hand-made bg tweens) move P later; the generated photo backgrounds already include P
            js_body = f"{content_js}\n{raw_bg}\ntl.shiftChildren({P});\n" + "\n".join(bgj)
        else:
            js_body = "\n".join(bgj) + f"\n{raw_bg}\n{content_js}"
        grain_div = '<div id="grain"></div>' if GRAIN else ""
        grain_js = (f"let s = {sum(map(ord, self.id)) % 97 + 3};\nconst rnd = () => ((s = (s * 9301 + 49297) % 233280) / 233280);\n"
                    f'for (let t = 0; t < {T}; t += 0.083) tl.set("#grain", {{ x: Math.round(rnd() * 90 - 45), y: Math.round(rnd() * 90 - 45) }}, t);') if GRAIN else ""
        css = CSS.replace("width: 1920px; height: 1080px;", f"width: {self.W}px; height: {self.H}px;").replace("opacity: 0.09; mix-blend-mode", f"opacity: {GRAIN}; mix-blend-mode")
        html = f"""<!doctype html>
<html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width={self.W}, height={self.H}" />
<title>JIGEASA {self.id}</title><script src="assets/vendor/gsap.min.js"></script>
<style>{FONT_CSS}{css}{CSS_V3}</style></head><body>
<div id="root" class="{f"baked grade-{self.baked}" if self.baked else ""}" data-composition-id="main" data-start="0" data-duration="{T}" data-width="{self.W}" data-height="{self.H}">
<div id="bg" class="full clip" data-start="0" data-duration="{T}" data-track-index="0"></div>
<div id="photos" class="full clip" data-start="0" data-duration="{T}" data-track-index="1">
{symbolize(chr(10).join(bgh + self.bg_html))}<div id="bgshade" class="full"></div>
</div>
<div id="content" class="full clip" data-start="0" data-duration="{T}" data-track-index="2">
{symbolize(chr(10).join(self.html))}
</div>
<div id="chrome" class="full clip" data-start="0" data-duration="{T}" data-track-index="3">
{symbolize(f'<div id="ov-tag">{self.tag}</div>{era}<div id="ov-brand">JIGEASA</div>')}<div id="vig" class="full"></div>{grain_div}
</div></div>
<script>
const tl = gsap.timeline({{ paused: true }});
{js_body}
{grain_js}
tl.set({{}}, {{}}, {T});
window.__timelines["main"] = tl;
</script></body></html>"""
        (d / "index.html").write_text(html)
        (d / "hyperframes.json").write_text(json.dumps({"$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
                                                         "paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}}, indent=2))
        (d / "meta.json").write_text(json.dumps({"id": f"jig-{self.id}", "name": f"JIGEASA {self.id}"}))
        (d / "photos.txt").write_text("\n".join(sorted(self.assets)))
        if export: export_assets(self, d / "assets", grade, fonts, gsap)
        return {"id": self.id, "start": self.g0, "dur": T, "pre": P, "sfx": self.sfx}


def export_assets(scene, a, grade=None, fonts=None, gsap=None):
    """fonts + GSAP + photos for one scene. Photos: RGB JPEG, max canvas width; background photos (bgs) baked with
    photo_grade.bake(preset=grade) when grade is set. Existing files are kept (the phone stays light)."""
    a = Path(a); (a / "fonts").mkdir(parents=True, exist_ok=True); (a / "vendor").mkdir(exist_ok=True)
    for p in Path(fonts or SKILL / "assets/fonts").glob("*.woff2"): shutil.copy(p, a / "fonts")
    shutil.copy(gsap or SKILL / "assets/vendor/gsap.min.js", a / "vendor")
    from PIL import Image
    bgset = {src for src, _, _ in scene.bg_items}
    for p in scene.assets:
        if p.startswith("crop:"): continue                   # 9:16 crops are made by the Short's build
        out = a / Path(p).name
        if out.exists(): continue
        if grade and p in bgset:
            from photo_grade import bake
            bake(p, out, (scene.W * PHOTO_SCALE, scene.H * PHOTO_SCALE), preset=grade); continue
        im = Image.open(p).convert("RGB"); mw = scene.W * PHOTO_SCALE
        if im.width > mw: im = im.resize((mw, round(im.height * mw / im.width)), Image.LANCZOS)
        im.save(out, quality=86)


def write_units(metas, path, base="chapters"):
    """units.json for the CI: one entry per rendered unit (chapter or Short) with its pre-roll."""
    json.dump([{"id": m["id"], "dir": f"{base}/{m['id']}", "start": m["start"], "dur": m["dur"], "pre": m.get("pre", 0.0)} for m in metas],
              open(path, "w"), indent=1)
