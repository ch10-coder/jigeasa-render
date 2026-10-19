// JIGEASA geo engine: a deterministic Google-Earth-style globe for HyperFrames scenes.
// Real data: NASA Blue Marble (July 2004) base, Sentinel-2 cloudless 2016 patches (EOX, CC BY 4.0),
// Terrarium/SRTM heights, DataMeet India boundary, Natural Earth (India view) borders.
//
// Usage inside a scene (see assets/geo/README.md):
//   import { createEarth, camAt, driveWithTimeline } from "../../assets/geo/engine.js";
//   const earth = await createEarth({ canvas, regions: ["hormuz"], assetBase: "../../assets/geo/" });
//   earth.render(camAt(CAM, t));            // CAM = [{t, lat, lon, alt, tilt, heading, ease}]
//   const p = earth.project(26.5, 56.4);    // {x, y, visible} in CSS px of the 1920x1080 frame
import * as THREE from "three";
import { Line2 } from "three/addons/lines/Line2.js";
import { LineMaterial } from "three/addons/lines/LineMaterial.js";
import { LineGeometry } from "three/addons/lines/LineGeometry.js";
import { REGIONS, LINES } from "./data.js";

export const R_KM = 6371;
const DEG = Math.PI / 180;

export function xyz(lat, lon, r = 1) {
  const p = lat * DEG, l = lon * DEG;
  return new THREE.Vector3(r * Math.cos(p) * Math.cos(l), r * Math.sin(p), -r * Math.cos(p) * Math.sin(l));
}

// ---------- camera keyframes ----------
const EASE = {
  linear: (x) => x,
  in: (x) => x * x,
  out: (x) => 1 - (1 - x) * (1 - x),
  inOut: (x) => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2),
  inOut3: (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
};

function slerpLatLon(a, b, k) {
  const va = xyz(a.lat, a.lon), vb = xyz(b.lat, b.lon);
  const dot = Math.min(1, Math.max(-1, va.dot(vb)));
  const om = Math.acos(dot);
  let v;
  if (om < 1e-6) v = va;
  else v = va.multiplyScalar(Math.sin((1 - k) * om) / Math.sin(om)).add(vb.multiplyScalar(Math.sin(k * om) / Math.sin(om)));
  v.normalize();
  return { lat: Math.asin(v.y) / DEG, lon: Math.atan2(-v.z, v.x) / DEG };
}

/** keys: [{t, lat, lon, alt (km), tilt (deg, 0 = straight down), heading (deg, 0 = north), ease}] sorted by t.
 *  `ease` on a key shapes the segment that ENDS at that key (default inOut). Altitude moves in log space. */
export function camAt(keys, t) {
  if (t <= keys[0].t) return { tilt: 0, heading: 0, ...keys[0] };
  for (let i = 1; i < keys.length; i++) {
    const a = keys[i - 1], b = keys[i];
    if (t <= b.t) {
      const k = (EASE[b.ease || "inOut"] || EASE.inOut)((t - a.t) / Math.max(1e-6, b.t - a.t));
      const ll = slerpLatLon(a, b, k);
      const alt = Math.exp(Math.log(a.alt) + (Math.log(b.alt) - Math.log(a.alt)) * k);
      let dh = ((b.heading || 0) - (a.heading || 0) + 540) % 360 - 180;
      return { lat: ll.lat, lon: ll.lon, alt, tilt: (a.tilt || 0) + ((b.tilt || 0) - (a.tilt || 0)) * k,
               heading: (a.heading || 0) + dh * k };
    }
  }
  return { tilt: 0, heading: 0, ...keys[keys.length - 1] };
}

/** Drive a render function from a paused GSAP timeline: seek-safe (onUpdate fires on every seek). */
export function driveWithTimeline(tl, duration, fn) {
  const proxy = { t: 0 };
  tl.to(proxy, { t: duration, duration, ease: "none", onUpdate: () => fn(proxy.t) }, 0);
  fn(0);
}

// ---------- shaders ----------
const SUN = new THREE.Vector3(-0.3, 0.8, -0.5).normalize(); // lights Asia + the Middle East (three.js axes)

const surfaceVert = /* glsl */ `
  varying vec2 vUv; varying vec3 vN; varying vec3 vW;
  void main() {
    vUv = uv;
    vec4 w = modelMatrix * vec4(position, 1.0);
    vW = w.xyz; vN = normalize(mat3(modelMatrix) * normal);
    gl_Position = projectionMatrix * viewMatrix * w;
  }`;
const surfaceFrag = /* glsl */ `
  uniform sampler2D map; uniform vec3 sun; uniform float feather; uniform float opacity;
  uniform float fogKm; uniform vec3 haze; uniform float isPatch; uniform float fresScale;
  varying vec2 vUv; varying vec3 vN; varying vec3 vW;
  void main() {
    vec3 c = texture2D(map, vUv).rgb * 255.0;
    bool ocean = c.b > c.r * 1.25 && c.b > c.g * 1.05;
    if (!ocean) c *= vec3(0.96, 1.06, 0.92);
    vec3 n = normalize(vN);
    vec3 up = normalize(vW);
    float ndl = clamp(dot(isPatch > 0.5 ? n : up, sun), 0.0, 1.0);
    float light = isPatch > 0.5 ? clamp(0.32 + 0.80 * ndl, 0.0, 1.05) : clamp(0.30 + 0.9 * pow(ndl, 0.7), 0.0, 1.12);
    vec3 v = normalize(cameraPosition - vW);
    float nv = clamp(dot(up, v), 0.0, 1.0);
    float fres = pow(1.0 - nv, 3.0) * fresScale;
    c = c * light;
    c = c * (1.0 - 0.5 * fres) + fres * vec3(90.0, 160.0, 255.0) * 0.7;
    float dkm = length(cameraPosition - vW) * 6371.0;
    float fog = fogKm > 0.0 ? pow(1.0 - exp(-dkm / fogKm), 1.2) : 0.0;
    c = mix(c, haze, fog);
    float a = opacity;
    // patches: let the Blue Marble ocean show through their (flat, repainted) sea so no box edge appears
    if (isPatch > -0.5 && feather > 0.0) {
      vec3 raw = texture2D(map, vUv).rgb;
      float blu = raw.b / max(max(raw.r, raw.g), 0.02);
      a *= 1.0 - smoothstep(1.35, 1.9, blu) * (1.0 - smoothstep(0.25, 0.45, max(raw.r, max(raw.g, raw.b))));
    }
    if (feather > 0.0) {
      float e = min(min(vUv.x, 1.0 - vUv.x), min(vUv.y, 1.0 - vUv.y));
      a *= smoothstep(0.0, feather, e);
    }
    gl_FragColor = vec4(clamp(c / 255.0, 0.0, 1.0), a);
  }`;

const atmoVert = /* glsl */ `
  varying vec3 vN; varying vec3 vW;
  void main() { vec4 w = modelMatrix * vec4(position, 1.0); vW = w.xyz; vN = normalize(mat3(modelMatrix) * normal);
                gl_Position = projectionMatrix * viewMatrix * w; }`;
const atmoFrag = /* glsl */ `
  uniform float strength; varying vec3 vN; varying vec3 vW;
  void main() {
    vec3 v = normalize(cameraPosition - vW);
    // back faces of the shell: -dot runs 0 at the outer rim to ~0.26 where the ray grazes the Earth
    float x = clamp(-dot(normalize(vN), v) / 0.26, 0.0, 1.0);
    float i = pow(x, 2.2);
    gl_FragColor = vec4(vec3(0.27, 0.55, 1.0) * i * strength, i * strength);
  }`;

const skyFrag = /* glsl */ `
  uniform float amount; uniform float horizon; varying vec2 vUv;
  void main() {
    vec3 top = vec3(18.0, 40.0, 86.0) / 255.0, hz = vec3(150.0, 180.0, 220.0) / 255.0, space = vec3(4.0, 7.0, 15.0) / 255.0;
    float t = clamp((1.0 - vUv.y) / max(0.05, 1.0 - horizon), 0.0, 1.0);
    vec3 sky = mix(top, hz, t);
    gl_FragColor = vec4(mix(space, sky, amount), 1.0);
  }`;

// ---------- earth ----------
function seeded(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

function loadImage(url) {
  return new Promise((res, rej) => new THREE.ImageLoader().load(url, res, undefined, rej));
}

function decodeDem(img, meta) {
  const c = document.createElement("canvas");
  c.width = img.width; c.height = img.height;
  const g = c.getContext("2d", { willReadFrequently: true });
  g.drawImage(img, 0, 0);
  const d = g.getImageData(0, 0, img.width, img.height).data;
  const h = new Float32Array(img.width * img.height);
  for (let i = 0; i < h.length; i++) h[i] = meta.h_min + ((d[i * 4] * 256 + d[i * 4 + 1]) / 65535) * (meta.h_max - meta.h_min);
  return { w: img.width, h: img.height, data: h };
}

function sampleDem(dem, u, v) {
  const x = Math.min(dem.w - 1.001, Math.max(0, u * (dem.w - 1))), y = Math.min(dem.h - 1.001, Math.max(0, v * (dem.h - 1)));
  const x0 = Math.floor(x), y0 = Math.floor(y), fx = x - x0, fy = y - y0, W = dem.w, D = dem.data;
  return D[y0 * W + x0] * (1 - fx) * (1 - fy) + D[y0 * W + x0 + 1] * fx * (1 - fy) + D[(y0 + 1) * W + x0] * (1 - fx) * fy + D[(y0 + 1) * W + x0 + 1] * fx * fy;
}

/**
 * opts: { canvas, width=1920, height=1080, assetBase, regions: [ids], exag=1.0,
 *         world=true, india=true, lines: [{id, pts:[[lon,lat],...], color:"#fbbf24", width:5, dashed:false, h:0}] }
 */
export async function createEarth(opts) {
  const W = opts.width || 1920, H = opts.height || 1080, base = opts.assetBase || "../../assets/geo/";
  const renderer = new THREE.WebGLRenderer({ canvas: opts.canvas, antialias: true, alpha: false, preserveDrawingBuffer: true });
  const dpr = window.devicePixelRatio || 1;
  renderer.setPixelRatio(dpr);
  renderer.setSize(W, H, false);
  renderer.autoClear = false;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(opts.vfov || 23.1, W / H, 1e-5, 60);

  // sky / space backdrop
  const skyScene = new THREE.Scene(), skyCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const skyMat = new THREE.ShaderMaterial({ uniforms: { amount: { value: 0 }, horizon: { value: 0.6 } },
    vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }", fragmentShader: skyFrag, depthWrite: false });
  skyScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), skyMat));

  // stars (seeded)
  const rnd = seeded(7), sp = [];
  for (let i = 0; i < 2600; i++) {
    const u = rnd() * 2 - 1, th = rnd() * Math.PI * 2, r = 40;
    sp.push(r * Math.sqrt(1 - u * u) * Math.cos(th), r * u, r * Math.sqrt(1 - u * u) * Math.sin(th));
  }
  const starGeo = new THREE.BufferGeometry(); starGeo.setAttribute("position", new THREE.Float32BufferAttribute(sp, 3));
  const starMat = new THREE.PointsMaterial({ color: 0xdfe8ff, size: 1.3 * dpr, sizeAttenuation: false, transparent: true, opacity: 0.8, depthWrite: false });
  const stars = new THREE.Points(starGeo, starMat); scene.add(stars);

  const loader = new THREE.TextureLoader();
  const baseTex = loader.load(base + "bm_jul_5400.jpg");
  baseTex.colorSpace = THREE.NoColorSpace; baseTex.anisotropy = 8;
  const mk = (map, extra = {}) => new THREE.ShaderMaterial({
    uniforms: { map: { value: map }, sun: { value: SUN }, feather: { value: 0 }, opacity: { value: 1 },
                fogKm: { value: 0 }, haze: { value: new THREE.Vector3(170, 192, 220) }, isPatch: { value: 0 }, fresScale: { value: 1 } },
    vertexShader: surfaceVert, fragmentShader: surfaceFrag, ...extra });
  const earthMat = mk(baseTex);
  const earth = new THREE.Mesh(new THREE.SphereGeometry(1, 360, 180), earthMat);
  earth.renderOrder = 0; scene.add(earth);

  const atmoMat = new THREE.ShaderMaterial({ uniforms: { strength: { value: 1 } }, vertexShader: atmoVert, fragmentShader: atmoFrag,
    side: THREE.BackSide, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false });
  const atmo = new THREE.Mesh(new THREE.SphereGeometry(1.035, 180, 90), atmoMat); scene.add(atmo);

  // region patches (Sentinel-2 texture, optional terrain)
  const patches = {};
  const exag = opts.exag || 1.0;
  await Promise.all((opts.regions || []).map(async (id) => {
    const meta = REGIONS[id];
    const tex = await new Promise((res, rej) => loader.load(base + id + ".jpg", res, undefined, rej));
    tex.colorSpace = THREE.NoColorSpace; tex.anisotropy = 8;
    let dem = null;
    if (meta.dem) dem = decodeDem(await loadImage(base + meta.dem), meta);
    const [lon0, lat0, lon1, lat1] = meta.bbox;
    const nx = dem ? 400 : 120, ny = Math.round(nx * (lat1 - lat0) / (lon1 - lon0));
    const pos = [], uv = [], idx = [];
    for (let j = 0; j <= ny; j++) for (let i = 0; i <= nx; i++) {
      const u = i / nx, v = j / ny, lat = lat1 - (lat1 - lat0) * v, lon = lon0 + (lon1 - lon0) * u;
      const h = dem ? Math.max(0, sampleDem(dem, u, v)) * exag : 0;
      const p = xyz(lat, lon, 1 + h / 1000 / R_KM + 0.000004);
      pos.push(p.x, p.y, p.z); uv.push(u, 1 - v);
    }
    for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
      const a = j * (nx + 1) + i, b = a + 1, c = a + nx + 1, d = c + 1;
      idx.push(a, c, b, b, c, d);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
    g.setIndex(idx); g.computeVertexNormals();
    const m = mk(tex, { transparent: true, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
    m.uniforms.feather.value = 0.16; m.uniforms.isPatch.value = dem ? 1 : 0;
    const mesh = new THREE.Mesh(g, m); mesh.renderOrder = 1; scene.add(mesh);
    patches[id] = { mesh, mat: m, dem, meta };
  }));

  // lines (screen-space width)
  const lineObjs = {};
  const addLine = (id, rings, color, width, opacity = 1, dashed = false, hKm = 0) => {
    const group = new THREE.Group();
    const mat = new LineMaterial({ color: new THREE.Color(color), linewidth: width * dpr, transparent: true, opacity,
      dashed, dashSize: 0.004, gapSize: 0.0025, worldUnits: false, depthTest: true, depthWrite: false });
    mat.resolution.set(W * dpr, H * dpr);
    for (const ring of rings) {
      if (ring.length < 2) continue;
      const arr = [];
      for (const [lon, lat] of ring) { const p = xyz(lat, lon, 1 + hKm / R_KM + 0.0004); arr.push(p.x, p.y, p.z); }
      const geo = new LineGeometry(); geo.setPositions(arr);
      const ln = new Line2(geo, mat); if (dashed) ln.computeLineDistances(); ln.renderOrder = 2; group.add(ln);
    }
    scene.add(group); lineObjs[id] = { group, mat, base: opacity };
  };
  if (opts.world !== false) addLine("world", LINES.world, "#ffffff", 1.2, 0.32);
  if (opts.india !== false) { addLine("india_glow", LINES.india, "#2dd4bf", 9, 0.22); addLine("india", LINES.india, "#2dd4bf", 3, 1); }
  for (const l of opts.lines || []) addLine(l.id, [l.pts], l.color || "#fbbf24", l.width || 4, l.opacity ?? 1, !!l.dashed, l.h || 0);

  let cur = null;
  function place(c) {
    const P = xyz(c.lat, c.lon, 1 + (c.targetH || 0) / R_KM);
    const up = P.clone().normalize();
    const east = new THREE.Vector3(0, 1, 0).cross(up).normalize();
    if (east.lengthSq() < 1e-8) east.set(1, 0, 0);
    const north = up.clone().cross(east).normalize();
    const th = (c.tilt || 0) * DEG, hd = (c.heading || 0) * DEG;
    const fwdH = north.clone().multiplyScalar(Math.cos(hd)).add(east.clone().multiplyScalar(Math.sin(hd)));
    const d = up.clone().multiplyScalar(-Math.cos(th)).add(fwdH.clone().multiplyScalar(Math.sin(th))).normalize();
    const dist = (c.alt / R_KM) / Math.max(Math.cos(th), 0.2);
    const C = P.clone().sub(d.clone().multiplyScalar(dist));
    const right = east.clone().multiplyScalar(Math.cos(hd)).sub(north.clone().multiplyScalar(Math.sin(hd)));
    camera.position.copy(C);
    camera.up.copy(right.clone().cross(d).normalize());
    camera.lookAt(P);
    camera.near = Math.max(1e-6, dist * 0.02); camera.far = c.alt > 2000 ? Math.max(dist + 1.5, 45) : dist + 1.5;
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld();
  }

  function render(c) {
    cur = c;
    place(c);
    const lowness = Math.min(1, Math.max(0, (Math.log(900) - Math.log(Math.max(c.alt, 1))) / (Math.log(900) - Math.log(60))));
    const sky = lowness * Math.min(1, (c.tilt || 0) / 35);
    skyMat.uniforms.amount.value = sky;
    starMat.opacity = 0.8 * (1 - Math.min(1, sky * 2));
    atmoMat.uniforms.strength.value = 1 - lowness;
    // haze only for low tilted views, scaled with altitude so a dive never washes out
    const tiltK = Math.min(1, Math.max(0, ((c.tilt || 0) - 25) / 25));
    const fogKm = tiltK > 0 && c.alt < 400 ? (c.alt * 6 + 160) / tiltK : 0;
    const fresScale = Math.min(1, Math.max(0, (c.alt - 250) / 1500));
    for (const m of [earthMat, ...Object.values(patches).map((p) => p.mat)]) {
      m.uniforms.fogKm.value = fogKm; m.uniforms.fresScale.value = fresScale;
    }
    const lineFade = Math.min(1, Math.max(0, (Math.log(c.alt) - Math.log(250)) / (Math.log(900) - Math.log(250))));
    for (const id in lineObjs) {
      const o = lineObjs[id];
      const keep = !(id === "world" || id === "india" || id === "india_glow");
      o.mat.opacity = o.base * (keep ? 1 : lineFade) * (o.user ?? 1);
      o.group.visible = o.mat.opacity > 0.003;
    }
    renderer.clear();
    renderer.render(skyScene, skyCam);
    renderer.clearDepth();
    renderer.render(scene, camera);
  }

  function heightAt(lat, lon) {
    for (const id in patches) {
      const p = patches[id];
      if (!p.dem) continue;
      const [lon0, lat0, lon1, lat1] = p.meta.bbox;
      if (lon >= lon0 && lon <= lon1 && lat >= lat0 && lat <= lat1)
        return Math.max(0, sampleDem(p.dem, (lon - lon0) / (lon1 - lon0), (lat1 - lat) / (lat1 - lat0))) * exag;
    }
    return 0;
  }

  /** Screen position (CSS px of the W x H frame) of a point; h in metres (default: terrain height). */
  function project(lat, lon, h) {
    const hm = h ?? heightAt(lat, lon);
    const P = xyz(lat, lon, 1 + hm / 1000 / R_KM);
    const toCam = camera.position.clone().sub(P);
    const facing = P.clone().normalize().dot(toCam.clone().normalize()) > -0.05;
    const v = P.clone().project(camera);
    return { x: (v.x + 1) / 2 * W, y: (1 - v.y) / 2 * H, visible: facing && v.z < 1 && v.z > -1 };
  }

  function setLineOpacity(id, a) { if (lineObjs[id]) lineObjs[id].user = a; }
  function setPatchOpacity(id, a) { if (patches[id]) patches[id].mat.uniforms.opacity.value = a; }

  return { render, project, heightAt, setLineOpacity, setPatchOpacity, renderer, scene, camera, get cam() { return cur; } };
}
