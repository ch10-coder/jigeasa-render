// Shared motion helpers for the geo chapters (revision 2, 2026-10-19). Every helper is a pure function of t:
// build once, then call .update(t, ...) inside the driveWithTimeline callback. Seek-safe, no timers, no randomness.
// SFX are NOT played here: list them in the chapter's /*SFX*/ block (see README "SFX block"); the audio mix reads it.

export const TYPE_CPS = 24; // typed characters per second; tools/sfx_plan.py clicks at the same rate

export const clamp01 = (x) => Math.max(0, Math.min(1, x));
export const sm = (x) => { x = clamp01(x); return x * x * (3 - 2 * x); };
export const out3 = (x) => 1 - Math.pow(1 - clamp01(x), 3);
export const inOut = (x) => { x = clamp01(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
export const backOut = (x) => { x = clamp01(x); const c = 1.70158; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
export const prog = (t, a, d) => clamp01((t - a) / d);
/** 0 -> 1 -> 0 envelope: rises over f after a, falls over f before b. */
export const env = (t, a, b, f = 0.4) => Math.min(sm((t - a) / f), sm((b - t) / f));

const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");

/**
 * Kinetic typing. el = any text element (keep its CSS: Anton headline, kicker, chip...). The text is typed from t0
 * at cps characters/s with a caret that stays solid while typing and blinks twice after, then disappears.
 * Optional t1: the element fades out over 0.35 s before t1. Returns { update(t), end } (end = t when typing stops).
 * SFX: add ["<anchor>", <offset of t0>, "type", <text.length>] to the chapter's SFX block.
 */
export function typer(el, text, t0, { cps = TYPE_CPS, t1 = Infinity, caretColor = "currentColor" } = {}) {
  const n = text.length, end = t0 + n / cps;
  let last = "";
  return {
    end,
    update(t) {
      const k = Math.max(0, Math.min(n, Math.floor((t - t0) * cps + 1e-6)));
      const typing = t >= t0 && t < end;
      const blink = t >= end && t < end + 0.9 && Math.floor((t - end) / 0.225) % 2 === 0;
      const caret = typing || blink ? `<span style="display:inline-block;width:.08em;height:.82em;margin-left:.06em;vertical-align:-.04em;background:${caretColor}"></span>` : "";
      const html = esc(text.slice(0, k)) + caret;
      if (html !== last) { el.innerHTML = html || "&#8203;"; last = html; }
      el.style.opacity = t < t0 ? "0" : (t1 === Infinity ? "1" : sm((t1 - t) / 0.35).toFixed(3));
    },
  };
}

/**
 * Number counter: el.textContent = prefix + value + suffix, eased out from `from` to `to` over dur from t0.
 * fmt(v) overrides the number format (default: fixed `dec` decimals with thousands commas).
 * SFX: ["<anchor>", <offset of t0>, "count", <dur>] (ticks while it rolls + a hit when it lands).
 */
export function counter(el, { from = 0, to, t0, dur = 1.2, dec = 0, prefix = "", suffix = "", fmt = null }) {
  const f = fmt || ((v) => v.toLocaleString("en-IN", { minimumFractionDigits: dec, maximumFractionDigits: dec }));
  let last = "";
  return {
    end: t0 + dur,
    update(t) {
      const v = from + (to - from) * out3((t - t0) / dur);
      const s = prefix + f(dec ? v : Math.round(v)) + suffix;
      if (s !== last) { el.textContent = s; last = s; }
    },
  };
}

/**
 * Flag cards with leader lines: a line draws from a place on the globe to a card at the frame edge, then the card
 * pops in (flags + title + optional sub). Cards leave on t1. Used for country mentions (s01, s03, ...).
 *   const cards = flagCards({ html: labsDiv, svg: overlaySvg, items: [
 *     { flags: ["ir"], title: "Iran", sub: "Hormuz", lat: 27.2, lon: 56.3, x: 1480, y: 300, t0: 5.9, t1: 19 }, ...] });
 *   cards.update(t, earth)   // inside the drive callback, after earth.render()
 * x, y = the card's top-left in frame px (keep cards inside x 96..1824, y 80..1000, clear of the text block).
 * Timing: line draws t0 .. t0+0.45, card pops at t0+0.35 (SFX: ["<anchor>", <offset of t0> + 0.35, "pop"]).
 * Flags are assets/flags/<iso2>.svg (flag-icons, MIT): ir om sa iq kw qa ae us il pk cn ru ua tw in.
 */
let cssDone = false;
function injectCss() {
  if (cssDone) return; cssDone = true;
  const st = document.createElement("style");
  st.textContent = `
  .fx-card { position:absolute; left:0; top:0; display:flex; align-items:center; gap:16px; padding:14px 22px 14px 14px;
    background:rgba(4,9,27,.78); border:1px solid rgba(248,250,252,.16); border-radius:12px; opacity:0; white-space:nowrap;
    box-shadow:0 10px 30px rgba(2,6,16,.45); transform-origin:0 50%; will-change:transform,opacity; }
  .fx-card .fx-flags { display:flex; gap:8px; }
  .fx-card img { display:block; width:64px; height:48px; border-radius:5px; box-shadow:0 0 0 1px rgba(248,250,252,.22); object-fit:cover; }
  .fx-card .fx-t { font:700 26px Inter; letter-spacing:4px; text-transform:uppercase; color:#f8fafc; line-height:1.05; }
  .fx-card .fx-s { font:500 21px Inter; color:#cbd5e1; margin-top:5px; line-height:1.1; }
  .fx-card .fx-n { font:400 40px/1 Anton; color:#ff6b6b; margin-right:2px; }`;
  document.head.appendChild(st);
}
const NS = "http://www.w3.org/2000/svg";
export function flagCards({ html, svg, items, color = "#f8fafc" }) {
  injectCss();
  const cards = items.map((it) => {
    const el = document.createElement("div"); el.className = "fx-card";
    el.innerHTML = (it.num ? `<div class="fx-n">${esc(String(it.num))}</div>` : "") +
      `<div class="fx-flags">${(it.flags || []).map((f) => `<img src="assets/flags/${f}.svg" alt="">`).join("")}</div>` +
      `<div><div class="fx-t">${esc(it.title)}</div>${it.sub ? `<div class="fx-s">${esc(it.sub)}</div>` : ""}</div>`;
    html.appendChild(el);
    const line = document.createElementNS(NS, "path");
    line.setAttribute("fill", "none"); line.setAttribute("stroke", it.color || color); line.setAttribute("stroke-width", "2.5");
    line.setAttribute("stroke-linecap", "round"); line.setAttribute("opacity", "0"); svg.appendChild(line);
    const dot = document.createElementNS(NS, "circle"); dot.setAttribute("r", "6"); dot.setAttribute("fill", it.color || color);
    dot.setAttribute("opacity", "0"); svg.appendChild(dot);
    return { it, el, line, dot, w: 0, h: 0 };
  });
  return {
    cards,
    update(t, earth) {
      for (const c of cards) {
        const { it } = c, t1 = it.t1 ?? Infinity;
        const a = t < it.t0 ? 0 : sm((t1 - t) / 0.4);
        if (a <= 0.001) { c.el.style.opacity = "0"; c.line.setAttribute("opacity", "0"); c.dot.setAttribute("opacity", "0"); continue; }
        if (!c.w) { c.w = c.el.offsetWidth || 300; c.h = c.el.offsetHeight || 76; }
        const p = earth.project(it.lat, it.lon, 0);
        // anchor = the card edge facing the place, vertically centred
        const left = p.x < it.x + c.w / 2, ax = left ? it.x : it.x + c.w, ay = it.y + c.h / 2;
        const k = out3((t - it.t0) / 0.45);
        const ex = p.x + (ax - p.x) * k, ey = p.y + (ay - p.y) * k;
        // elbow: a short horizontal run into the card reads cleaner than a pure diagonal
        const mx = ax + (left ? -36 : 36);
        const d = k < 0.75 ? `M${p.x.toFixed(1)},${p.y.toFixed(1)} L${ex.toFixed(1)},${ey.toFixed(1)}`
          : `M${p.x.toFixed(1)},${p.y.toFixed(1)} L${(p.x + (mx - p.x) * Math.min(1, k)).toFixed(1)},${ay.toFixed(1)} L${ax.toFixed(1)},${ay.toFixed(1)}`;
        c.line.setAttribute("d", d);
        const vis = p.visible ? 1 : 0;
        c.line.setAttribute("opacity", (0.85 * a * vis).toFixed(3));
        c.dot.setAttribute("cx", p.x.toFixed(1)); c.dot.setAttribute("cy", p.y.toFixed(1));
        c.dot.setAttribute("opacity", (a * vis).toFixed(3));
        const pk = prog(t, it.t0 + 0.35, 0.45);
        c.el.style.opacity = (a * Math.min(1, pk * 1.6)).toFixed(3);
        c.el.style.transformOrigin = left ? "0 50%" : "100% 50%";
        c.el.style.transform = `translate(${it.x}px, ${it.y}px) scale(${(0.82 + 0.18 * backOut(pk)).toFixed(3)})`;
      }
    },
  };
}

/** Animated SVG path draw-on: el = <path>; sets dasharray/offset so it draws from t0 over dur (pure in t). */
export function drawOn(el, t0, dur) {
  let L = 0;
  return {
    update(t) {
      if (!L) { try { L = el.getTotalLength(); } catch (e) { L = 1000; } el.setAttribute("stroke-dasharray", `${L} ${L}`); }
      el.setAttribute("stroke-dashoffset", (L * (1 - inOut((t - t0) / dur))).toFixed(1));
    },
  };
}
