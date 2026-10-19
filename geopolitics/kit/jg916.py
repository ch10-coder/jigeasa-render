"""9:16 components (kit v3 copy of rupee_short/rupee.py; the rupee-specific bits are reusable: coin, barrel, tank).
Rupee Short (9:16) components on top of jg.Scene. Times are local seconds of the Short.
New here: ticker HUD, decimal odometer, coin crack, real-data line chart, see-saw, donut, oil barrel, coin flow on the
official India outline, reserves tank, whip streak, screenshot pop, 9:16 photo backgrounds with focal points."""
import math, random, re
from pathlib import Path
from jg import Scene, SFX, MAP, icon

W, H = 1080, 1920
HEX = {"co": "#ff6b6b", "tl": "#2dd4bf", "am": "#fbbf24", "ink": "#f8fafc", "mute": "#94a3b8"}
SFX.update({"crack": ("mk", 759, -15), "glitch": ("mk", 2946, -21), "pour": ("mk", 2826, -23), "riser": ("mk", 2900, -17)})

DEV = "U+0900-097F,U+1CD0-1CF9,U+200C-200D,U+20A8,U+20B9,U+20F0,U+25CC,U+A830-A839,U+A8E0-A8FF"
LEXT = ("U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,"
        "U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF")
EXTRA_CSS = "".join(
    f'@font-face {{ font-family:"Poppins"; font-weight:{w}; font-display:block; src:url("assets/fonts/poppins-devanagari-{w}-normal.woff2") format("woff2"); unicode-range:{DEV}; }}'
    for w in (600, 700, 800, 900)) + "".join(
    f'@font-face {{ font-family:"Inter"; font-weight:{w}; font-display:block; src:url("assets/fonts/inter-latin-ext-{w}-normal.woff2") format("woff2"); unicode-range:{LEXT}; }}'
    for w in (600, 700)) + r"""
#grain { width: 1280px !important; height: 2120px !important; }
#vig { background: radial-gradient(1000px 1500px at 50% 46%, transparent 50%, rgba(0,0,0,0.5) 100%) !important; }
#ov-brand { bottom: auto; top: 1276px; right: 200px; font-size: 24px; }
.src { bottom: auto !important; top: 1236px; left: 60px; font-size: 22px !important; color: rgba(248,250,252,0.82) !important; }
.bgcred { right: auto; left: 60px; bottom: auto; top: 1278px; font-size: 17px !important; color: rgba(248,250,252,0.62) !important; }
.brk .bs { color: #cbd5e1 !important; }
.bgi img { object-fit: cover; filter: none !important; }
#bgshade { background: linear-gradient(180deg, rgba(11,18,32,0.5) 0%, rgba(11,18,32,0.16) 30%, rgba(11,18,32,0.2) 62%, rgba(11,18,32,0.72) 100%),
  repeating-linear-gradient(0deg, rgba(148,163,184,0.04) 0 1px, transparent 1px 80px), repeating-linear-gradient(90deg, rgba(148,163,184,0.04) 0 1px, transparent 1px 80px) !important; }
.brk { background: rgba(11,18,32,0.5) !important; }
.brk .bl { text-shadow: 0 10px 50px rgba(45,212,191,0.35); }
.kc { position: absolute; left: 60px; width: 860px; text-align: center; opacity: 0; }
.kc .pl { display: inline-block; padding: 12px 30px 16px; border-radius: 24px; background: rgba(11,18,32,0.86); line-height: 1.12; text-shadow: none; }
.kc .wd { display: inline-block; margin: 0 0.13em; color: #f8fafc; transform-origin: 50% 70%; }
.bgi.gray img { filter: grayscale(1) contrast(1.08) brightness(0.55); }
.tk { position: absolute; display: flex; align-items: center; gap: 16px; height: 54px; font: 800 36px "Poppins"; letter-spacing: 0.04em; white-space: nowrap; }
.tk .lb { color: #cbd5e1; }
.tk .vw { position: relative; width: 640px; height: 54px; perspective: 500px; }
.tk .v { position: absolute; left: 0; top: 0; line-height: 54px; white-space: nowrap; }
.tk .v small { font: 800 22px "Inter"; letter-spacing: 0.08em; margin-left: 12px; color: #cbd5e1; }
.tk .v.co { color: var(--coral); } .tk .v.tl { color: var(--teal); }
.cnum { position: absolute; font-weight: 900; line-height: 1; white-space: nowrap; }
.cnum .sf { font-size: 0.42em; letter-spacing: 0.02em; margin-left: 0.12em; }
.coin { position: absolute; }
.coin .img, .coin .shard { position: absolute; left: 0; top: 0; width: 100%; height: 100%; background-size: 100% 100%; }
.coin svg { position: absolute; left: 0; top: 0; }
.whip { position: absolute; left: -900px; top: -300px; width: 760px; height: 2600px; opacity: 0; pointer-events: none;
  background: linear-gradient(90deg, rgba(248,250,252,0) 0%, rgba(248,250,252,0.07) 28%, rgba(248,250,252,0.42) 48%, rgba(45,212,191,0.3) 56%, rgba(45,212,191,0.06) 74%, rgba(248,250,252,0) 100%); transform: skewX(-16deg); }
.flash { position: absolute; inset: 0; background: #fff; opacity: 0; pointer-events: none; }
.fc { position: absolute; left: 0; top: 0; width: 84px; height: 84px; margin: -42px 0 0 -42px; opacity: 0; }
.fc span { position: absolute; inset: 0; border-radius: 50%; font: 900 48px "Poppins"; line-height: 76px; text-align: center; color: #0b1220; text-shadow: none; }
.fc .r { background: #f59e0b; border: 4px solid #fde68a; box-shadow: inset 0 -7px 0 rgba(120,53,15,0.35); }
.fc .d { background: #2dd4bf; border: 4px solid #ccfbf1; box-shadow: inset 0 -7px 0 rgba(15,118,110,0.45); opacity: 0; }
.ss { position: absolute; border-radius: 28px; overflow: hidden; border: 4px solid #475569; box-shadow: 0 40px 90px rgba(0,0,0,0.65); }
.ss .cr { position: relative; z-index: 2; padding: 12px 18px; background: rgba(11,18,32,0.85); font: 700 24px "Inter"; color: #cbd5e1; text-align: center; white-space: nowrap; }
.ss img { display: block; width: 100%; }
.ir { position: absolute; display: flex; align-items: center; gap: 28px; white-space: nowrap; font: 800 68px "Poppins"; }
.ir .ul { position: absolute; left: 128px; right: 0; bottom: -12px; height: 7px; border-radius: 4px; transform-origin: 0 50%; }
.ir small { font: 700 30px "Inter"; color: #cbd5e1; margin-left: 6px; }
.chip.co { border-color: var(--coral); color: var(--coral); background: rgba(255,107,107,0.1); }
.hd2 { position: absolute; display: flex; align-items: center; gap: 22px; white-space: nowrap; font: 900 96px "Poppins"; letter-spacing: 0.01em; }
"""

def js_num(v):
    return f"{v:.3f}".rstrip("0").rstrip(".")

# --------------------------------------------------------------------------- backgrounds
def bgs916(s, items, crops):
    """items: [(key, t)], crops: key -> (src, focal_x, focal_y, credit, gray). Pre-cropped 9:16 files are made by build.py."""
    for k, (key, t) in enumerate(items):
        src, fx, fy, cred, gray = crops[key]
        s.assets.add(f"crop:{key}")
        nxt = items[k + 1][1] if k + 1 < len(items) else s.dur
        i = f"bgi{k}"; d = round(nxt - t + 1.0, 3)
        s.bg_html.append(f'<div class="bgi{" gray" if gray else ""}" id="{i}"><img src="assets/bg_{key}.jpg" alt="" /></div>'
                         f'<div class="bgcred" id="{i}c">{cred}</div>')
        fade = 0.01 if t <= 0.05 else 0.5
        zx = (-24, 24) if k % 2 == 0 else (24, -24)
        s.bg_js.append(
            (f"tl.set('#{i}', {{opacity:1}}, 0);" if t <= 0.05 else
             f"tl.fromTo('#{i}', {{opacity:0}}, {{opacity:1, duration:{fade}, ease:'power1.inOut'}}, {max(0.0, round(t - 0.25, 3))});")
            + f"tl.fromTo('#{i} img', {{scale:1.0, x:{zx[0]}}}, {{scale:1.08, x:{zx[1]}, duration:{d}, ease:'none'}}, {max(0.0, round(t - 0.25, 3))});"
            f"tl.fromTo('#{i}c', {{opacity:0}}, {{opacity:1, duration:0.4}}, {round(t + 0.3, 3)});"
            + (f"tl.to(['#{i}c'], {{opacity:0, duration:0.3}}, {round(nxt - 0.3, 3)});" if k + 1 < len(items) else ""))

# --------------------------------------------------------------------------- HUD + text
def ticker(s, t0, t1, states, x=64, y=96):
    """USD/INR HUD. states: [(t, value, 'co'|'tl', small)] - each new state flips in (rotationX)."""
    i = s.uid("tk")
    vs = "".join(f'<span class="v {c}" id="{i}v{k}" style="opacity:0">{v}<small>{sm}</small></span>' for k, (t, v, c, sm) in enumerate(states))
    js = f"tl.fromTo('#{i}', {{opacity:0, x:-30}}, {{opacity:1, x:0, duration:0.4, ease:'power3.out'}}, {t0});tl.set('#{i}v0', {{opacity:1}}, {t0});"
    for k in range(1, len(states)):
        t = states[k][0]
        js += (f"tl.to('#{i}v{k - 1}', {{rotationX:90, opacity:0, duration:0.18, ease:'power2.in'}}, {t});"
               f"tl.fromTo('#{i}v{k}', {{rotationX:-90, opacity:0}}, {{rotationX:0, opacity:1, duration:0.28, ease:'back.out(2)'}}, {round(t + 0.16, 3)});")
        s.cue(t + 0.16, "ding", -20)
    js += f"tl.to('#{i}', {{opacity:0, duration:0.3}}, {round(t1 - 0.3, 3)});"
    s.add(f'<div class="tk" id="{i}" style="left:{x}px;top:{y}px"><span class="lb">USD/INR</span><span class="vw">{vs}</span></div>', js)
    return i

def dcounter(s, vals, t1, x, y, w, size, colors, pre="", suf="", dec=2, align="center", label=None, label_y=None, label_size=32,
             ticks=True, enter="pop", group=None, tick_db=-27, sf_em=0.42):
    """Decimal odometer. vals: [(value, t, dur)] - first value pops in at t, each next one counts from the previous one."""
    i = s.uid("dn"); cols = [HEX.get(c, c) for c in colors]
    fmt = lambda v: f"{v:.{dec}f}"
    sf = f'<span class="sf" style="font-size:{sf_em}em">{suf}</span>' if suf else ""
    h = (f'<div class="cnum" id="{i}" style="left:{x}px;top:{y}px;width:{w}px;text-align:{align};font-size:{size}px;color:{cols[0]}">'
         f'<span id="{i}n">{pre}{fmt(vals[0][0])}</span>{sf}</div>')
    if label:
        h += (f'<div class="abs" id="{i}l" style="left:{x}px;top:{label_y}px;width:{w}px;text-align:{align};font:700 {label_size}px Inter;'
              f'letter-spacing:0.08em;color:#cbd5e1;white-space:nowrap">{label}</div>')
    t0 = vals[0][1]
    js = (f"tl.fromTo('#{i}', {{opacity:0, scale:0.55}}, {{opacity:1, scale:1, duration:0.4, ease:'back.out(2)'}}, {t0});" if enter == "pop"
          else (f"tl.fromTo('#{i}', {{scale:1.08}}, {{scale:1, duration:0.4, ease:'power3.out'}}, {t0});" if enter == "none"
                else f"tl.fromTo('#{i}', {{opacity:0, y:30}}, {{opacity:1, y:0, duration:0.35, ease:'power3.out'}}, {t0});"))
    prev = vals[0][0]
    for k, (v, t, d) in enumerate(vals[1:], 1):
        js += (f"(() => {{ const el = document.getElementById('{i}n'); const o = {{v:{prev}}};"
               f" tl.fromTo(o, {{v:{prev}}}, {{v:{v}, duration:{d}, ease:'power2.out', immediateRender:false,"
               f" onUpdate:() => {{ el.textContent = '{pre}' + o.v.toFixed({dec}); }} }}, {t}); }})();")
        if len(cols) > k and cols[k] != cols[k - 1]:
            js += f"tl.to('#{i}', {{color:'{cols[k]}', duration:0.3}}, {t});"
        if ticks:
            tk = t
            while tk < t + d - 0.05: s.cue(tk, "tick", tick_db); tk += 0.09
        prev = v
    if label: js += s.inout(f"#{i}l", round(t0 + 0.2, 3), None, "up")
    js += f"tl.to(['#{i}'{', ' + repr('#' + i + 'l') if label else ''}], {{opacity:0, filter:'blur(14px)', duration:0.3, ease:'power2.in'}}, {round(t1 - 0.3, 3)});"
    s.add(h, js)
    if enter != "none": s.cue(t0, "pop", -21)
    s.reserve(f"dcounter {pre}{vals[-1][0]}", t0, t1, y, (label_y or y + size) + (label_size if label else 0), x, x + w)
    return i

def textline(s, html, t0, t1, x=0, y=0, w=W, size=40, weight=800, color="var(--ink)", font="Poppins", align="center", kind="up", ls=0, sfx=None):
    i = s.uid("tx")
    s.add(f'<div class="abs" id="{i}" style="left:{x}px;top:{y}px;width:{w}px;text-align:{align};font:{weight} {size}px {font};'
          f'letter-spacing:{ls}em;color:{color};white-space:nowrap">{html}</div>', s.inout(f"#{i}", t0, t1, kind, 0.4))
    if sfx: s.cue(t0, sfx)
    return i

def src_line(s, text, t0, t1):
    i = s.uid("sr")
    s.add(f'<div class="src" id="{i}">{text}</div>', s.inout(f"#{i}", t0, t1, "fade", 0.4))

def whip(s, t):
    """Light streak sweeping across the frame + fast whoosh just before a beat change."""
    i = s.uid("wp")
    s.add(f'<div class="whip" id="{i}"></div>',
          f"tl.fromTo('#{i}', {{x:0, opacity:0}}, {{x:2700, opacity:1, duration:0.34, ease:'power2.inOut'}}, {round(t - 0.17, 3)});"
          f"tl.set('#{i}', {{opacity:0}}, {round(t + 0.18, 3)});")
    s.cue(t - 0.14, "fast", -20)

# --------------------------------------------------------------------------- hook: coin crack
def coin_crack(s, t_in, t_shake, t_crack, cx, cy, d, seed=11, group="#hk", pop=True):
    """Rs 1 coin (CC0 photo) that trembles, gets crack lines, then shatters into K clip-path shards."""
    i = s.uid("cn"); rnd = random.Random(seed); K = 8
    ix, iy = 0.47, 0.45
    angs = sorted((k + rnd.uniform(-0.28, 0.28)) * 2 * math.pi / K for k in range(K))
    edge = lambda a: (0.5 + 0.53 * math.cos(a), 0.5 + 0.53 * math.sin(a))
    def jag(p, q, n=3):
        out = []
        for j in range(1, n + 1):
            u = j / (n + 1); x = p[0] + (q[0] - p[0]) * u; y = p[1] + (q[1] - p[1]) * u
            dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy) or 1; off = rnd.uniform(-0.03, 0.03)
            out.append((x - dy / L * off, y + dx / L * off))
        return out
    spokes = [jag((ix, iy), edge(a)) for a in angs]
    shards, cracks = [], []
    for k in range(K):
        a0 = angs[k]; a1 = angs[(k + 1) % K] + (2 * math.pi if k + 1 == K else 0)
        arc = [edge(a0 + (a1 - a0) * u / 5) for u in range(6)]
        poly = [(ix, iy)] + spokes[k] + arc + list(reversed(spokes[(k + 1) % K]))
        cxs = sum(p[0] for p in poly) / len(poly); cys = sum(p[1] for p in poly) / len(poly)
        shards.append((poly, cxs - ix, cys - iy))
        pts = [(ix, iy)] + spokes[k] + [(0.5 + 0.47 * math.cos(a0), 0.5 + 0.47 * math.sin(a0))]
        cracks.append(" ".join(f"{p[0] * d:.1f},{p[1] * d:.1f}" for p in pts))
    s.assets.add("coin")
    url = "assets/coin_1rupee.png"
    h = [f'<div class="coin" id="{i}" style="left:{cx - d / 2:.0f}px;top:{cy - d / 2:.0f}px;width:{d}px;height:{d}px">',
         f'<div class="img" id="{i}im" style="background-image:url({url})"></div>']
    for k, (poly, vx, vy) in enumerate(shards):
        cp = ", ".join(f"{p[0] * 100:.2f}% {p[1] * 100:.2f}%" for p in poly)
        h.append(f'<div class="shard" id="{i}s{k}" style="background-image:url({url});clip-path:polygon({cp});opacity:0"></div>')
    lens = []
    for c in cracks:
        pts = [tuple(map(float, p.split(","))) for p in c.split()]
        lens.append(sum(math.dist(pts[j], pts[j + 1]) for j in range(len(pts) - 1)) + 2)
    h.append(f'<svg width="{d}" height="{d}" viewBox="0 0 {d} {d}" style="overflow:visible">' + "".join(
        f'<polyline id="{i}c{k}" points="{c}" fill="none" stroke="#fff7ed" stroke-width="5" stroke-linejoin="round" stroke-linecap="round" '
        f'stroke-dasharray="{L:.1f}" stroke-dashoffset="{L:.1f}" opacity="0.95"/>' for k, (c, L) in enumerate(zip(cracks, lens))) + "</svg></div>")
    js = ((f"tl.fromTo('#{i}', {{scale:0.62, rotation:-14}}, {{scale:1, rotation:0, duration:0.55, ease:'back.out(1.6)'}}, {t_in});"
           f"tl.to('#{i}', {{scale:1.05, rotation:5, duration:{round(t_crack - t_in - 0.6, 3)}, ease:'none'}}, {round(t_in + 0.55, 3)});") if pop else
          f"tl.fromTo('#{i}', {{scale:0.94, rotation:-6}}, {{scale:1.06, rotation:4, duration:{round(t_crack - t_in, 3)}, ease:'power1.in'}}, {t_in});")
    tq = t_shake; amp = 3
    while tq < t_crack - 0.06:   # escalating tremble
        js += f"tl.to('#{i}im', {{x:{amp if int(tq * 25) % 2 else -amp}, duration:0.04, ease:'none'}}, {round(tq, 3)});"
        tq += 0.04; amp = min(12, amp + 0.35)
    js += f"tl.to('#{i}im', {{x:0, duration:0.03}}, {round(t_crack - 0.05, 3)});"
    for k, L in enumerate(lens):
        js += f"tl.to('#{i}c{k}', {{attr:{{'stroke-dashoffset':0}}, duration:0.16, ease:'power2.out'}}, {round(t_crack - 0.2 + k * 0.006, 3)});"
    js += f"tl.set('#{i}im', {{opacity:0}}, {t_crack});tl.set('#{i} .shard', {{opacity:1}}, {t_crack});tl.set('#{i} svg', {{opacity:0}}, {round(t_crack + 0.05, 3)});"
    for k, (poly, vx, vy) in enumerate(shards):
        L = math.hypot(vx, vy) or 1; dist = rnd.uniform(260, 460); dx, dy = vx / L * dist, vy / L * dist
        rot = rnd.uniform(40, 140) * (1 if vx > 0 else -1)
        js += (f"tl.to('#{i}s{k}', {{x:{dx * 0.55:.0f}, y:{dy * 0.55 - 60:.0f}, rotation:{rot * 0.4:.0f}, duration:0.32, ease:'power2.out'}}, {t_crack});"
               f"tl.to('#{i}s{k}', {{x:{dx:.0f}, y:{dy + 980:.0f}, rotation:{rot:.0f}, opacity:0, duration:0.85, ease:'power2.in'}}, {round(t_crack + 0.32, 3)});")
    s.add("".join(h), js)
    # flash + glitch + shake on the hook group
    f = s.uid("fl")
    s.add(f'<div class="flash" id="{f}"></div>',
          f"tl.fromTo('#{f}', {{opacity:0}}, {{opacity:0.22, duration:0.04}}, {t_crack});tl.to('#{f}', {{opacity:0, duration:0.2}}, {round(t_crack + 0.05, 3)});"
          f"tl.set('{group}', {{filter:'drop-shadow(10px 0 0 rgba(255,40,80,0.85)) drop-shadow(-10px 0 0 rgba(0,230,255,0.85))'}}, {t_crack});"
          f"tl.set('{group}', {{filter:'drop-shadow(-6px 0 0 rgba(255,40,80,0.7)) drop-shadow(6px 0 0 rgba(0,230,255,0.7))'}}, {round(t_crack + 0.05, 3)});"
          f"tl.set('{group}', {{filter:'none'}}, {round(t_crack + 0.11, 3)});"
          f"tl.fromTo('{group}', {{x:0, y:0}}, {{x:16, y:-8, duration:0.035, yoyo:true, repeat:7, ease:'none'}}, {t_crack});"
          f"tl.set('{group}', {{x:0, y:0}}, {round(t_crack + 0.3, 3)});")
    s.cue(t_crack - 0.03, "crack", -17); s.cue(t_crack, "deep", -18); s.cue(t_crack + 0.02, "glitch", -22); s.cue(t_crack - 0.06, "riser", -20)
    s.reserve("coin", t_in, t_crack + 0.3, cy - d / 2, cy + d / 2, cx - d / 2, cx + d / 2)
    return i

# --------------------------------------------------------------------------- real-data line chart
def linechart(s, series, t0, t_end, t1, box, vmin, vmax, grid=(85, 90, 95), xlabels=(), markers=(), color="#ff6b6b", sweep=True, note=None):
    """series: [(day_number, value)]. Inverted scale: higher USD/INR (weaker rupee) sits LOWER, so the line falls as the rupee falls.
    markers: [(day_number, value, label_html, colour, (dx, dy), anchor)] pop in when the drawing passes them.
    note: (svg_text_inner, x, y) small axis note drawn with the axes, e.g. 'line neeche = rupee kamzor'."""
    i = s.uid("lc"); x, y, w, h = box
    d0, d1 = series[0][0], series[-1][0]
    X = lambda d: x + (d - d0) / (d1 - d0) * w
    Y = lambda v: y + (v - vmin) / (vmax - vmin) * h
    pts = [(X(d), Y(v)) for d, v in series]
    cum = [0.0]
    for a, b in zip(pts, pts[1:]): cum.append(cum[-1] + math.dist(a, b))
    L = cum[-1]
    path = "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in pts)
    area = path + f" L{pts[-1][0]:.1f} {y + h:.1f} L{pts[0][0]:.1f} {y + h:.1f} Z"
    dur = round(t_end - t0, 3)
    g = "".join(f'<line x1="{x}" y1="{Y(v):.1f}" x2="{x + w}" y2="{Y(v):.1f}" stroke="rgba(148,163,184,0.28)" stroke-width="2" stroke-dasharray="6 10"/>'
                f'<text x="{x - 14}" y="{Y(v) + 9:.1f}" text-anchor="end" style="font:700 28px Inter" fill="#cbd5e1">&#8377;{v}</text>' for v in grid)
    xl = "".join(f'<text x="{X(dn):.1f}" y="{y + h + 44}" text-anchor="{anc}" style="font:700 26px Inter;letter-spacing:0.06em" fill="#cbd5e1">{lab}</text>'
                 for dn, lab, anc in xlabels)
    mk_svg, mk_js = "", ""
    for k, (dn, v, lab, col, (dx, dy), anc) in enumerate(markers):
        px, py = X(dn), Y(v)
        j = min(range(len(series)), key=lambda q: abs(series[q][0] - dn)); tm = round(t0 + cum[j] / L * dur, 3)
        c = HEX.get(col, col)
        mk_svg += (f'<g id="{i}m{k}" opacity="0"><line x1="{px:.1f}" y1="{py:.1f}" x2="{px + dx * 0.55:.1f}" y2="{py + dy * 0.55:.1f}" stroke="{c}" stroke-width="3"/>'
                   f'<circle cx="{px:.1f}" cy="{py:.1f}" r="11" fill="{c}"/>'
                   f'<text x="{px + dx:.1f}" y="{py + dy:.1f}" text-anchor="{anc}" style="font:800 30px Poppins" fill="{c}">{lab}</text></g>')
        mk_js += (f"tl.fromTo('#{i}m{k}', {{opacity:0, y:10}}, {{opacity:1, y:0, duration:0.3, ease:'back.out(2)'}}, {tm});")
        s.cue(tm, "ping")
    # head dot follows the drawing tip (keypoints at equal arc length)
    N = 36; kps = []
    for q in range(1, N + 1):
        target = L * q / N; j = max(1, next(jj for jj in range(1, len(cum)) if cum[jj] >= target - 1e-6))
        u = (target - cum[j - 1]) / max(1e-6, cum[j] - cum[j - 1])
        kps.append((pts[j - 1][0] + (pts[j][0] - pts[j - 1][0]) * u, pts[j - 1][1] + (pts[j][1] - pts[j - 1][1]) * u))
    dot_js = "".join(f"tl.to('#{i}hd', {{x:{px:.1f}, y:{py:.1f}, duration:{dur / N:.4f}, ease:'none'}}, {round(t0 + q * dur / N, 4)});"
                     for q, (px, py) in enumerate(kps))
    svg = (f'<svg class="abs" id="{i}" style="left:0;top:0" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
           f'<defs><linearGradient id="{i}g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{color}" stop-opacity="0.34"/>'
           f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>'
           f'<clipPath id="{i}cp"><rect id="{i}cr" x="{x}" y="{y - 40}" width="0" height="{h + 80}"/></clipPath></defs>'
           f'<g id="{i}ax">{g}{xl}' + (f'<text x="{note[1]}" y="{note[2]}" style="font:800 30px Inter;letter-spacing:0.02em" fill="#e2e8f0">{note[0]}</text>' if note else "") + '</g>'
           f'<path d="{area}" fill="url(#{i}g)" clip-path="url(#{i}cp)"/>'
           f'<path id="{i}gl" d="{path}" fill="none" stroke="{color}" stroke-opacity="0.22" stroke-width="20" stroke-linejoin="round" stroke-linecap="round" '
           f'stroke-dasharray="{L:.1f}" stroke-dashoffset="{L:.1f}"/>'
           f'<path id="{i}ln" d="{path}" fill="none" stroke="{color}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round" '
           f'stroke-dasharray="{L:.1f}" stroke-dashoffset="{L:.1f}"/>{mk_svg}'
           f'<g id="{i}hd" transform="translate({pts[0][0]:.1f},{pts[0][1]:.1f})" opacity="0"><circle r="26" fill="{color}" opacity="0.25"/><circle r="12" fill="#fff"/></g></svg>')
    js = (f"tl.fromTo('#{i}ax', {{opacity:0}}, {{opacity:1, duration:0.35}}, {round(t0 - 0.3, 3)});"
          f"tl.set('#{i}hd', {{x:{pts[0][0]:.1f}, y:{pts[0][1]:.1f}}}, 0);tl.to('#{i}hd', {{opacity:1, duration:0.15}}, {t0});"
          f"tl.to(['#{i}ln', '#{i}gl'], {{attr:{{'stroke-dashoffset':0}}, duration:{dur}, ease:'none'}}, {t0});"
          f"tl.to('#{i}cr', {{attr:{{width:{w + 4}}}, duration:{dur}, ease:'none'}}, {t0});" + dot_js + mk_js +
          f"tl.to('#{i}', {{opacity:0, filter:'blur(14px)', duration:0.3, ease:'power2.in'}}, {round(t1 - 0.3, 3)});")
    s.add(svg, js)
    if sweep: s.cue(t0, "sweep", -22)
    s.reserve("linechart", t0, t1, y - 40, y + h + 50, x - 80, x + w)
    return i

# --------------------------------------------------------------------------- funda: see-saw
def seesaw(s, t_in, t_arrows, t_tilt, t_lbl_d, t_lbl_r, t1, cx=540, cy=640, L=640, tilt=-14, cd=110, fs_r=52, fs_d=60, asz=80):
    """Value see-saw: $ on the right, Rs on the left. DEMAND arrows push the $ end up -> beam tilts, Rs end goes down."""
    i = s.uid("sw")
    beam = (f'<div class="abs" id="{i}b" style="left:{cx - L / 2:.0f}px;top:{cy - 9}px;width:{L}px;height:18px;border-radius:9px;'
            f'background:linear-gradient(180deg,#e2e8f0,#94a3b8);box-shadow:0 10px 30px rgba(0,0,0,0.5)">'
            f'<div class="abs" style="left:{-cd * 0.36:.0f}px;top:{-cd + 8}px;width:{cd}px;height:{cd}px;border-radius:50%;background:#f59e0b;box-shadow:inset 0 -9px 0 rgba(120,53,15,0.35);'
            f'border:5px solid #fde68a;font:900 {cd * 0.62:.0f}px Poppins;line-height:{cd - 10}px;text-align:center;color:#0b1220;text-shadow:none">&#8377;</div>'
            f'<div class="abs" style="right:{-cd * 0.36:.0f}px;top:{-cd + 8}px;width:{cd}px;height:{cd}px;border-radius:50%;background:#2dd4bf;box-shadow:inset 0 -9px 0 rgba(15,118,110,0.45);'
            f'border:5px solid #ccfbf1;font:900 {cd * 0.62:.0f}px Poppins;line-height:{cd - 10}px;text-align:center;color:#0b1220;text-shadow:none">$</div></div>')
    stand = (f'<svg class="abs" style="left:{cx - 90}px;top:{cy + 6}px" width="180" height="220" viewBox="0 0 180 220">'
             f'<polygon points="90,0 160,200 20,200" fill="#334155" stroke="#94a3b8" stroke-width="4"/><rect x="0" y="198" width="180" height="16" rx="8" fill="#94a3b8"/></svg>')
    ax = cx + L / 2 - 70
    arrows = "".join(f'<div class="abs" id="{i}a{k}" style="left:{ax - asz / 2 + (k - 1) * asz * 0.78:.0f}px;top:{cy + 70}px;color:#fbbf24;opacity:0">{icon("arrow-big-up", asz, "#fbbf24")}</div>'
                     for k in range(3))
    dem = f'<div class="abs" id="{i}dm" style="left:{ax - 200:.0f}px;top:{cy + 80 + asz + 10}px;width:400px;text-align:center;font:900 46px Poppins;letter-spacing:0.12em;color:#fbbf24;opacity:0">DEMAND</div>'
    lr = f'<div class="abs" id="{i}lr" style="left:{cx - 20}px;top:{cy - cd - 190}px;width:400px;text-align:center;font:900 {fs_r}px Poppins;color:#2dd4bf;white-space:nowrap;opacity:0">$ &#8593; MEHENGA</div>'
    ld = f'<div class="abs" id="{i}ld" style="left:{cx - L / 2 - 20:.0f}px;top:{cy + 160}px;width:400px;text-align:center;font:900 {fs_d}px Poppins;color:#ff6b6b;white-space:nowrap;opacity:0">&#8377; &#8595; GIRA</div>'
    h = f'<div id="{i}">{stand}{beam}{arrows}{dem}{lr}{ld}</div>'
    js = (f"tl.fromTo('#{i}', {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.4, ease:'power3.out'}}, {t_in});"
          f"tl.set('#{i}b', {{rotation:0, transformOrigin:'50% 50%'}}, 0);")
    for k, t in enumerate(t_arrows):
        js += f"tl.fromTo('#{i}a{k}', {{opacity:0, y:220}}, {{opacity:1, y:0, duration:0.35, ease:'back.out(1.8)'}}, {t});"
        s.cue(t, "pop2", -20)
    js += f"tl.fromTo('#{i}dm', {{opacity:0, y:20}}, {{opacity:1, y:0, duration:0.3}}, {t_arrows[0]});"
    js += (f"tl.to('#{i}b', {{rotation:{tilt}, duration:0.6, ease:'back.out(1.5)'}}, {t_tilt});"
           f"tl.to(['#{i}a0', '#{i}a1', '#{i}a2', '#{i}dm'], {{y:-{abs(math.sin(math.radians(tilt))) * L / 2:.0f}, duration:0.6, ease:'back.out(1.5)'}}, {t_tilt});")
    s.cue(t_tilt + 0.25, "gear", -18)
    js += s.inout(f"#{i}lr", t_lbl_r, None, "pop", 0.4) + s.inout(f"#{i}ld", t_lbl_d, None, "pop", 0.4)
    s.cue(t_lbl_r, "pop", -21); s.cue(t_lbl_d, "thud", -16)
    js += f"tl.to('#{i}', {{opacity:0, filter:'blur(14px)', duration:0.3, ease:'power2.in'}}, {round(t1 - 0.3, 3)});"
    s.add(h, js)
    s.reserve("seesaw", t_in, t1, cy - 340, cy + 260, 60, 1020)
    return i

# --------------------------------------------------------------------------- oil: donut + barrel
def donut(s, pct, t_in, t_fill, d_fill, t1, cx=540, cy=640, r=210, sw=46, color="#ff6b6b"):
    i = s.uid("dt"); C = 2 * math.pi * r
    h = (f'<svg class="abs" id="{i}" style="left:{cx - r - sw}px;top:{cy - r - sw}px" width="{2 * (r + sw)}" height="{2 * (r + sw)}" viewBox="0 0 {2 * (r + sw)} {2 * (r + sw)}">'
         f'<circle cx="{r + sw}" cy="{r + sw}" r="{r}" fill="rgba(11,18,32,0.55)" stroke="rgba(148,163,184,0.22)" stroke-width="{sw}"/>'
         f'<circle id="{i}a" cx="{r + sw}" cy="{r + sw}" r="{r}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" '
         f'stroke-dasharray="{C:.1f}" stroke-dashoffset="{C:.1f}" transform="rotate(-90 {r + sw} {r + sw})"/></svg>')
    js = (f"tl.fromTo('#{i}', {{opacity:0, scale:0.7}}, {{opacity:1, scale:1, duration:0.45, ease:'back.out(1.7)'}}, {t_in});"
          f"tl.to('#{i}a', {{attr:{{'stroke-dashoffset':{C * (1 - pct / 100):.1f}}}, duration:{d_fill}, ease:'power2.inOut'}}, {t_fill});"
          f"tl.to('#{i}', {{opacity:0, filter:'blur(14px)', duration:0.3, ease:'power2.in'}}, {round(t1 - 0.3, 3)});")
    s.add(h, js); s.cue(t_fill, "sweep", -22)
    s.reserve("donut", t_in, t1, cy - r - sw, cy + r + sw, cx - r - sw, cx + r + sw)
    return i

def barrel(s, t_in, t_f0, t_f1, t1, x=110, y=470, w=300, h=430, lv0=0.22, lv1=0.92):
    i = s.uid("br"); ih = h - 40; top = 20
    y0 = top + ih * (1 - lv0); y1 = top + ih * (1 - lv1)
    hoops = "".join(f'<rect x="-6" y="{yy}" width="{w + 12}" height="14" rx="7" fill="#475569"/>' for yy in (h * 0.2, h * 0.5 - 7, h * 0.8 - 14))
    svg = (f'<svg class="abs" id="{i}" style="left:{x}px;top:{y}px;overflow:visible" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
           f'<defs><clipPath id="{i}c"><rect x="10" y="{top}" width="{w - 20}" height="{ih}" rx="34"/></clipPath>'
           f'<linearGradient id="{i}lg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#78350f"/><stop offset="0.45" stop-color="#d97706"/><stop offset="1" stop-color="#78350f"/></linearGradient></defs>'
           f'<rect x="0" y="0" width="{w}" height="{h}" rx="44" fill="rgba(15,23,42,0.75)" stroke="#94a3b8" stroke-width="6"/>'
           f'<g clip-path="url(#{i}c)"><rect id="{i}lq" x="10" y="{y0:.1f}" width="{w - 20}" height="{ih + 20}" fill="url(#{i}lg)"/>'
           f'<rect id="{i}sh" x="10" y="{y0 - 6:.1f}" width="{w - 20}" height="12" fill="#fbbf24" opacity="0.7"/></g>{hoops}'
           f'<text x="{w / 2}" y="{h / 2 + 24}" text-anchor="middle" style="font:900 60px Poppins" fill="rgba(11,18,32,0.75)">OIL</text></svg>')
    js = (f"tl.fromTo('#{i}', {{opacity:0, x:-80}}, {{opacity:1, x:0, duration:0.45, ease:'power3.out'}}, {t_in});"
          f"tl.to('#{i}lq', {{attr:{{y:{y1:.1f}}}, duration:{round(t_f1 - t_f0, 3)}, ease:'power1.inOut'}}, {t_f0});"
          f"tl.to('#{i}sh', {{attr:{{y:{y1 - 6:.1f}}}, duration:{round(t_f1 - t_f0, 3)}, ease:'power1.inOut'}}, {t_f0});"
          f"tl.to('#{i}', {{opacity:0, filter:'blur(14px)', duration:0.3, ease:'power2.in'}}, {round(t1 - 0.3, 3)});")
    s.add(svg, js); s.cue(t_f0, "pour")
    s.reserve("barrel", t_in, t1, y, y + h, x, x + w)
    return i

# --------------------------------------------------------------------------- FPI: India outline + coin flow
def india_outline(s, t_in, t1, x=70, y=470, scale=0.5):
    i = s.uid("in"); v = MAP["india_view"]
    svg = (f'<svg class="abs" id="{i}" style="left:{x}px;top:{y}px" width="{848 * scale:.0f}" height="{948 * scale:.0f}" viewBox="0 0 848 948">'
           f'<g fill="rgba(45,212,191,0.12)" stroke="#2dd4bf" stroke-width="3.5" stroke-linejoin="round">'
           f'<path d="{v["india"]}"/><path d="{v["jk"]}"/><path d="{v["ladakh"]}"/></g></svg>')
    s.add(svg, f"tl.fromTo('#{i}', {{opacity:0, scale:1.08}}, {{opacity:1, scale:1, duration:0.6, ease:'power3.out'}}, {t_in});"
               f"tl.to('#{i}', {{opacity:0, filter:'blur(14px)', duration:0.3, ease:'power2.in'}}, {round(t1 - 0.3, 3)});")
    s.cue(t_in, "whoosh", -24)
    P = lambda lon, lat: ((lon - 67.5) * math.cos(math.radians(22)) * 30 * scale + x, (37.6 - lat) * 30 * scale + y)
    s.reserve("india", t_in, t1, y, y + 948 * scale, x, x + 848 * scale)
    return i, P

def coin_flow(s, start, end, n, t0, t_last, fly=1.15, seed=5, t1=None):
    """n coins leave `start`, arc to `end`, flipping Rs -> $ halfway (each in 6 straight hops along a quadratic Bezier)."""
    rnd = random.Random(seed); i = s.uid("cf"); h, js = [], ""
    for k in range(n):
        tk = round(t0 + (t_last - t0) * k / max(1, n - 1), 3)
        sx, sy = start[0] + rnd.uniform(-26, 26), start[1] + rnd.uniform(-26, 26)
        ex, ey = end[0] + rnd.uniform(-40, 40), end[1] + rnd.uniform(-30, 30)
        mx, my = (sx + ex) / 2, (sy + ey) / 2; px, py = -(ey - sy), (ex - sx); pl = math.hypot(px, py) or 1
        bend = rnd.uniform(140, 300); qx, qy = mx + px / pl * bend, my + py / pl * bend
        B = lambda u: ((1 - u) ** 2 * sx + 2 * (1 - u) * u * qx + u * u * ex, (1 - u) ** 2 * sy + 2 * (1 - u) * u * qy + u * u * ey)
        c = f"{i}c{k}"
        h.append(f'<div class="fc" id="{c}"><span class="r">&#8377;</span><span class="d">$</span></div>')
        js += f"tl.set('#{c}', {{x:{sx:.0f}, y:{sy:.0f}, scale:0.6}}, 0);tl.to('#{c}', {{opacity:1, scale:1, duration:0.12}}, {tk});"
        for q in range(1, 7):
            bx, by = B(q / 6)
            js += f"tl.to('#{c}', {{x:{bx:.0f}, y:{by:.0f}, duration:{fly / 6:.3f}, ease:'none'}}, {round(tk + (q - 1) * fly / 6, 3)});"
        tf = round(tk + fly * 0.45, 3)
        js += (f"tl.to('#{c}', {{scaleX:0, duration:0.07, ease:'power1.in'}}, {tf});"
               f"tl.set('#{c} .r', {{opacity:0}}, {round(tf + 0.07, 3)});tl.set('#{c} .d', {{opacity:1}}, {round(tf + 0.07, 3)});"
               f"tl.to('#{c}', {{scaleX:1, duration:0.07, ease:'power1.out'}}, {round(tf + 0.07, 3)});"
               f"tl.to('#{c}', {{opacity:0, scale:0.5, duration:0.12}}, {round(tk + fly - 0.06, 3)});")
        if k % 3 == 0: s.cue(tk, "coin", -24)
    s.add(f'<div id="{i}">' + "".join(h) + "</div>", js)
    return i

# --------------------------------------------------------------------------- RBI: reserves tank
def tank(s, t_in, t_d0, t_d1, t1, x=130, y=480, w=300, h=460, vtop=800, vbot=700, v0=785.71, v1=726.03, ticks=(800, 775, 750, 725, 700)):
    i = s.uid("tn"); pad = 18
    Yv = lambda v: pad + (vtop - v) / (vtop - vbot) * (h - 2 * pad)
    tk = "".join(f'<line x1="{w - 2}" y1="{Yv(t):.1f}" x2="{w + 22}" y2="{Yv(t):.1f}" stroke="#94a3b8" stroke-width="3"/>'
                 f'<text x="{w + 30}" y="{Yv(t) + 9:.1f}" style="font:700 26px Inter" fill="#94a3b8">${t}B</text>' for t in ticks)
    svg = (f'<svg class="abs" id="{i}" style="left:{x}px;top:{y}px;overflow:visible" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
           f'<defs><clipPath id="{i}c"><rect x="8" y="8" width="{w - 16}" height="{h - 16}" rx="30"/></clipPath>'
           f'<linearGradient id="{i}g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#0f766e"/><stop offset="0.5" stop-color="#2dd4bf"/><stop offset="1" stop-color="#0f766e"/></linearGradient></defs>'
           f'<rect x="0" y="0" width="{w}" height="{h}" rx="38" fill="rgba(15,23,42,0.7)" stroke="#cbd5e1" stroke-width="6"/>'
           f'<g clip-path="url(#{i}c)"><rect id="{i}lq" x="8" y="{Yv(v0):.1f}" width="{w - 16}" height="{h}" fill="url(#{i}g)" opacity="0.92"/>'
           f'<rect id="{i}sf" x="8" y="{Yv(v0) - 5:.1f}" width="{w - 16}" height="10" fill="#ccfbf1" opacity="0.8"/></g>{tk}'
           f'<rect x="{w * 0.12:.0f}" y="16" width="16" height="{h - 32}" rx="8" fill="rgba(255,255,255,0.18)"/></svg>')
    js = (f"tl.fromTo('#{i}', {{opacity:0, y:40}}, {{opacity:1, y:0, duration:0.45, ease:'power3.out'}}, {t_in});"
          f"tl.to('#{i}lq', {{attr:{{y:{Yv(v1):.1f}}}, duration:{round(t_d1 - t_d0, 3)}, ease:'power2.inOut'}}, {t_d0});"
          f"tl.to('#{i}sf', {{attr:{{y:{Yv(v1) - 5:.1f}}}, duration:{round(t_d1 - t_d0, 3)}, ease:'power2.inOut'}}, {t_d0});"
          f"tl.to('#{i}', {{opacity:0, filter:'blur(14px)', duration:0.3, ease:'power2.in'}}, {round(t1 - 0.3, 3)});")
    s.add(svg, js); s.cue(t_in, "door", -22); s.cue(t_d0, "air", -22)
    s.reserve("tank", t_in, t1, y, y + h, x, x + w + 110)
    return i

# --------------------------------------------------------------------------- screenshot proof
def shot_pop(s, t_in, t1, x=250, y=640, w=640, rot=-5, circle=None, t_circle=None, credit="", inner=False, ih=862):
    """User's Google screenshot card (assets/google_card.jpg, 1080 x ih) tilts in; optional coral circle (card px).
    inner=True: the credit strip sits under the image inside the card."""
    i = s.uid("ss"); k = w / 1080; hh = ih * k
    circ = ""
    if circle:
        cx, cy, r = circle; C = 2 * math.pi * r * k
        circ = (f'<svg class="abs" style="left:0;top:0" width="{w}" height="{hh:.0f}"><circle id="{i}o" cx="{cx * k:.1f}" cy="{cy * k:.1f}" r="{r * k:.1f}" fill="none" '
                f'stroke="#ff6b6b" stroke-width="7" stroke-dasharray="{C:.1f}" stroke-dashoffset="{C:.1f}" transform="rotate(-90 {cx * k:.1f} {cy * k:.1f})"/></svg>')
    s.assets.add("google_card")
    cr = f'<div class="cr">{credit}</div>' if inner else ""
    h = (f'<div class="ss" id="{i}" style="left:{x}px;top:{y}px;width:{w}px"><img src="assets/google_card.jpg" alt=""/>{circ}{cr}</div>'
         f'<div class="abs" id="{i}t" style="left:{x}px;top:{y + hh + 18:.0f}px;width:{w}px;text-align:center;font:600 22px Inter;color:#cbd5e1;white-space:nowrap">{"" if inner else credit}</div>')
    js = (f"tl.fromTo('#{i}', {{opacity:0, x:260, rotation:{rot + 10}, scale:0.85}}, {{opacity:1, x:0, rotation:{rot}, scale:1, duration:0.4, ease:'back.out(1.5)'}}, {t_in});"
          f"tl.fromTo('#{i}t', {{opacity:0}}, {{opacity:1, duration:0.3}}, {round(t_in + 0.2, 3)});"
          f"tl.to('#{i} img', {{scale:1.05, duration:{round(t1 - t_in, 3)}, ease:'none', transformOrigin:'85% 85%'}}, {t_in});"
          f"tl.to(['#{i}', '#{i}t'], {{opacity:0, filter:'blur(12px)', duration:0.25, ease:'power2.in'}}, {round(t1 - 0.25, 3)});")
    if circle: js += f"tl.to('#{i}o', {{attr:{{'stroke-dashoffset':0}}, duration:0.35, ease:'power2.out'}}, {t_circle});"
    s.add(h, js); s.cue(t_in, "swoosh", -22); s.cue(t_circle or t_in, "marker", -22)
    return i

# --------------------------------------------------------------------------- asar rows
def header(s, text, ic, color, t_in, t1, x=110, y=280, size=96):
    i = s.uid("hd")
    s.add(f'<div class="hd2" id="{i}" style="left:{x}px;top:{y}px;font-size:{size}px;color:{color}">{text}{icon(ic, int(size * 0.85), color)}</div>',
          s.inout(f"#{i}", t_in, t1, "left", 0.4))
    s.cue(t_in, "pop", -20)
    return i

def item(s, ic, text, color, t_in, t1, x=120, y=430, sub="", isz=100):
    i = s.uid("it"); c = HEX.get(color, color)
    sm = f"<small>{sub}</small>" if sub else ""
    s.add(f'<div class="ir" id="{i}" style="left:{x}px;top:{y}px">{icon(ic, isz, c)}<span>{text}{sm}</span>'
          f'<div class="ul" id="{i}u" style="background:{c}"></div></div>',
          f"tl.fromTo('#{i}', {{opacity:0, x:-60}}, {{opacity:1, x:0, duration:0.38, ease:'power3.out'}}, {t_in});"
          f"tl.fromTo('#{i}u', {{scaleX:0}}, {{scaleX:1, duration:0.45, ease:'power3.inOut'}}, {round(t_in + 0.15, 3)});"
          f"tl.to('#{i}', {{opacity:0, filter:'blur(12px)', duration:0.3, ease:'power2.in'}}, {round(t1 - 0.3, 3)});")
    s.cue(t_in, "click", -22)
    return i

# --------------------------------------------------------------------------- v2: karaoke captions + loop ending
def captions_karaoke(s, phrases, words, y=1232, size=64, end=None):
    """phrases: [[(text, word_index), ...], ...]. The phrase pops in on its first word; each word turns amber (and lifts a
    little) while it is spoken (from its word start until the next token starts); the phrase leaves at the next phrase or
    0.45 s after its last word."""
    h, js = [], []
    starts = [words[p[0][1]][0] for p in phrases]
    for k, ph in enumerate(phrases):
        i = f"kc{k}"; t0 = round(starts[k], 3)
        last_end = words[ph[-1][1]][1]
        t1 = starts[k + 1] if k + 1 < len(phrases) else (end or last_end + 0.6)
        t1 = round(min(t1, last_end + 0.45) if k + 1 < len(phrases) and starts[k + 1] - last_end > 0.6 else t1, 3)
        spans = "".join(f'<span class="wd" id="{i}w{j}">{tx}</span>' for j, (tx, wi) in enumerate(ph))
        h.append(f'<div class="kc" id="{i}" style="top:{y}px"><span class="pl" style="font:900 {size}px Poppins">{spans}</span></div>')
        js.append(f"tl.fromTo('#{i}', {{opacity:0, scale:0.88, y:16}}, {{opacity:1, scale:1, y:0, duration:0.14, ease:'back.out(2)'}}, {t0});"
                  f"tl.set('#{i}', {{opacity:0}}, {t1});")
        for j, (tx, wi) in enumerate(ph):
            a = round(max(t0, words[wi][0]), 3)
            b = round(words[ph[j + 1][1]][0] if j + 1 < len(ph) else t1, 3)
            js.append(f"tl.fromTo('#{i}w{j}', {{color:'#f8fafc', y:0, scale:1}}, {{color:'#fbbf24', y:-4, scale:1.07, duration:0.07, immediateRender:false}}, {a});"
                      f"tl.to('#{i}w{j}', {{color:'#f8fafc', y:0, scale:1, duration:0.07}}, {max(a + 0.08, round(b - 0.02, 3))});")
    s.add("".join(h), "".join(js))

def loop_end(s, t, coin_cx=540, coin_cy=860, d=560):
    """Last ~0.5 s rebuilds the opening frame ('$1 =', Rs 85.60, intact coin) so YouTube's loop is seamless."""
    s.add('<div class="abs" id="le1" style="left:0;right:0;top:200px;text-align:center;font:900 110px Poppins;letter-spacing:0.02em;opacity:0">$1 =</div>'
          '<div class="cnum" id="le2" style="left:0;top:330px;width:1080px;text-align:center;font-size:230px;color:#f8fafc;opacity:0">₹85.60</div>'
          f'<div class="coin" id="le3" style="left:{coin_cx - d / 2:.0f}px;top:{coin_cy - d / 2:.0f}px;width:{d}px;height:{d}px;opacity:0">'
          '<div class="img" style="background-image:url(assets/coin_1rupee.png)"></div></div>',
          f"tl.fromTo(['#le1', '#le2'], {{opacity:0, y:-30}}, {{opacity:1, y:0, duration:0.3, ease:'power3.out'}}, {t});"
          f"tl.fromTo('#le3', {{opacity:0, scale:1.25, rotation:12}}, {{opacity:1, scale:0.94, rotation:-6, duration:0.38, ease:'power3.out'}}, {t});")
    s.cue(t, "swoosh", -20)
