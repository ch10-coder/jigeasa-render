# Geo engine: how a chapter scene is built

Every chapter is ONE standalone HyperFrames composition: `compositions/frames/sNN-<id>.html`. `tools/make_units.py` copies it to `units/sNN/index.html` next to an `assets/` link, so **write every asset path as `assets/...`** (never `../`). A chapter is rendered on its own in CI, and the chapters are joined afterwards.

## Skeleton (copy this, then fill)

The reference unit is `/root/hf/geotest/u/t1/index.html` (a working dive from space onto 3D Karakoram terrain). Keep its head exactly:

- `<script src="assets/vendor/gsap.min.js">` plus an importmap mapping `three` to `./assets/vendor/three/three.module.min.js` and `three/addons/` to `./assets/vendor/three/addons/`
- `@font-face` for Anton (`assets/fonts/Anton-Regular.ttf`) and Inter 500/600/700 (`assets/fonts/inter-latin-<w>-normal.woff2`)
- the root `<div id="root" data-composition-id="main" data-start="0" data-duration="<DUR>" data-width="1920" data-height="1080">`
- `<canvas id="earth">` as the first child (full-bleed), with every HTML layer above it
- a `<script type="module">` that awaits `createEarth`, builds ONE paused GSAP timeline, calls `driveWithTimeline(tl, DUR, fn)`, adds the text tweens, then sets `window.__timelines["main"] = tl` LAST, and resolves the `window.__hf.buildReady["earth"]` promise

## API (`assets/geo/engine.js`)

```js
import { createEarth, camAt, driveWithTimeline, xyz } from "./assets/geo/engine.js";
const earth = await createEarth({
  canvas, assetBase: "./assets/geo/",
  regions: ["hormuz"],          // Sentinel-2 patches to load (ids below); terrain patches carry heights
  world: true, india: true,     // Natural Earth (India view) borders, DataMeet India boundary (teal)
  lines: [{ id: "lane", pts: [[lon, lat], ...], color: "#fbbf24", width: 5, dashed: true }],
  exag: 1.0,                    // terrain height exaggeration
});
earth.render(camAt(CAM, t));    // CAM = [{t, lat, lon, alt(km), tilt(deg, 0 = looking straight down), heading(deg, 0 = north), ease}]
earth.project(lat, lon, h_m?) // -> {x, y, visible} in frame px (h defaults to the terrain height)
earth.setLineOpacity("lane", a) // 0..1 (user multiplier); world/india lines fade out by themselves below ~250 km
earth.setPatchOpacity("hormuz", a)
```

- `camAt` interpolates position along the great circle and altitude in log space. The `ease` on a key shapes the segment that ends at it (`inOut` by default, plus `out`, `in`, `linear`, `inOut3`).
- **Altitude guide:** 15,000–22,000 km = whole globe; 3,000–5,000 km = a sub-continent; 600–1,000 km = a sea or strait; 20–60 km with tilt 50–65° = Google-Earth 3D terrain.
- **Speed:** at most ~6° of globe spin per second at globe scale. Dives take 3–5 s. No cuts inside a chapter: the camera carries the story.
- **Chapter joins:** start and end every chapter at its "globe hand-off" camera, given in your packet, so the joins line up.

## Region patches (`assets/geo/regions.json`)

| id | area | detail | terrain |
|---|---|---|---|
| hormuz | Strait of Hormuz, Persian Gulf mouth, Gulf of Oman (53.5–60.2 E, 23.4–28.6 N) | Sentinel-2 z9, world borders burned in | light |
| punjab | Ferozepur–Kasur border (73.6–75.6 E, 30.2–31.9 N) | Sentinel-2 z11, India boundary burned in | flat |
| kashmir | Kashmir valley, Pir Panjal, Pahalgam (74.4–75.9 E, 33.2–34.6 N) | z11 | yes |
| ladakh | Ladakh, Galwan, Pangong (77.4–79.2 E, 33.6–35.4 N) | z11 | yes |
| karakoram | K2, Shaksgam, 1963 line in coral (75.7–77.5 E, 35.0–36.9 N) | z11, India teal + kabza coral burned in | yes |
| taiwan | Taiwan Strait (117.5–123.5 E, 21.0–26.8 N) | z9 | light |

Outside a patch the globe is NASA Blue Marble (July). It looks sharp down to ~1,500 km altitude.

## HTML layers (all text is HTML, never in the canvas)

- Text block (style A): `.kicker` = an amber 44×6 rule plus tracked Inter 700 caps (28 px, letter-spacing 5 px, amber). Headline = two Anton lines, 150–190 px, uppercase: line 1 in #f8fafc, line 2 is the keyword in #ff6b6b (danger) or #fbbf24 (money/dates). Subtitle = Inter 500, 38–40 px, #e2e8f0. Left margin 96 px. A left scrim (`linear-gradient(90deg, rgba(4,9,27,.82) 0 26%, transparent 55%)`) sits behind the text only while text is up (fade it with the block).
- Shadows: `text-shadow: 0 3px 2.5px rgba(2,6,16,.7), 0 8px 26px rgba(2,6,16,.4)`. Never use a wide glow.
- Map labels: tracked Inter 700 caps, 26 px, letter-spacing 5 px, with a leader line (an SVG line, 2 px, white at 0.8) from a 5 px dot at the pin. Each frame, position them from `earth.project()` inside the `driveWithTimeline` callback (set `transform: translate(...)`), and hide them when `visible` is false.
- Pulses (hotspots): an HTML/SVG coral dot (r 11) with a white core and 3 rings. Scale and opacity are driven by the time `t` inside the same callback (`phase = (t % 1.6) / 1.6`), so they stay seek-safe.
- Counters: Anton digits counted from the timeline (a proxy object tweened, then `textContent` set in onUpdate, with fixed decimals).
- Credits line: bottom centre, Inter 500 20 px, #cbd5e1, for whatever imagery is on screen.
- Symbols (₹, arrows, ✓): inline SVG or the `Poppins` Devanagari face for ₹ (`assets/fonts/poppins-devanagari-700-normal.woff2`). Never use a font arrow.

## Timing

`timing/sNN.json` holds the chapter's cues: `{dur, cues: [{id, t, text}]}`. The times are ESTIMATES until the voice is made. Put them in the scene as one table that the voice step can rewrite:

```js
/*CUES*/ const CUES = {"c01": 0.6, "c02": 5.2, ...}; /*END CUES*/
const DUR = /*DUR*/ 87.9 /*END DUR*/;
```

Every visual beat is placed with `CUES.cNN + offset`, never a bare number. The root `data-duration` must equal `DUR`; the voice step rewrites both.

## Determinism

- No `Date.now()`, no `performance.now()`, no `Math.random()` (use the seeded `seeded()` pattern if needed), no `requestAnimationFrame` loops, no network fetches at render time. All data is local.
- A pulse or loop must be a pure function of `t`.
- Do not tween `.clip` elements. Animate inner nodes.
