/* JIGEASA shared 3D coin — Akbar's real square gold mohur (LACMA M.77.55.11, public domain) as a Three.js object.
 * Classic script (needs assets/vendor/three.min.js loaded first). Deterministic and seek-safe: it never animates on its
 * own; the frame's GSAP timeline tweens a plain state object and calls coin.render(state) from onUpdate (and on hf-seek).
 *
 *   const coin = JigCoin.make(canvasEl, { px: 1000, front: "coin_obv", back: "coin_rev" });
 *   window.__hf = window.__hf || {}; window.__hf.buildReady = window.__hf.buildReady || {};
 *   window.__hf.buildReady["coin-01"] = coin.ready;            // register synchronously in the same script
 *   const S = JigCoin.state({ rotY: -0.3 });                    // { rotX, rotY, rotZ, scale, x, y, glow, glowColor, dim }
 *   tl.to(S, { rotY: 0.2, duration: 2, ease: "power3.out", onUpdate: () => coin.render(S) }, 0);
 *   coin.render(S);                                             // first paint
 *
 * px = CSS size of the (square) canvas; the drawing buffer is px * 2 so 4K renders stay sharp.
 * rotY = PI shows the back face. glow 0..1 adds a coloured rim light (teal good side / coral dark side).
 * dim 0..1 desaturates/darkens the metal (the "daag" side). Faces: assets/img/<name>.png (RGBA cut-outs, 1400 px).
 */
(function () {
  const T = window.THREE;
  function state(o) {
    return Object.assign({ rotX: 0.12, rotY: -0.3, rotZ: -0.05, scale: 1, x: 0, y: 0, glow: 0, glowColor: "#2dd4bf", dim: 0 }, o || {});
  }
  function roundedSquare(s, r) {
    const h = s / 2, sh = new T.Shape();
    sh.moveTo(-h + r, -h); sh.lineTo(h - r, -h); sh.quadraticCurveTo(h, -h, h, -h + r); sh.lineTo(h, h - r);
    sh.quadraticCurveTo(h, h, h - r, h); sh.lineTo(-h + r, h); sh.quadraticCurveTo(-h, h, -h, h - r); sh.lineTo(-h, -h + r);
    sh.quadraticCurveTo(-h, -h, -h + r, -h); return sh;
  }
  function envMap(renderer) {   // a tiny studio for metal reflections (core three only, no addons)
    const pm = new T.PMREMGenerator(renderer), sc = new T.Scene();
    sc.add(new T.Mesh(new T.SphereGeometry(10, 32, 16), new T.MeshBasicMaterial({ color: 0x1b2440, side: T.BackSide })));
    const lamp = (c, x, y, z, w, h) => { const m = new T.Mesh(new T.PlaneGeometry(w, h), new T.MeshBasicMaterial({ color: c, side: T.DoubleSide }));
      m.position.set(x, y, z); m.lookAt(0, 0, 0); sc.add(m); };
    lamp(0xfff1cc, 3, 4, 5, 6, 3); lamp(0xffe2a0, -5, 1, 3, 2, 6); lamp(0x2dd4bf, 5, -2, -3, 3, 3); lamp(0xffffff, 0, 6, -2, 8, 1);
    const tex = pm.fromScene(sc, 0.03).texture; pm.dispose(); return tex;
  }
  function make(canvas, opt) {
    opt = Object.assign({ px: 1000, front: "coin_obv", back: "coin_rev", dpr: 2 }, opt || {});
    const renderer = new T.WebGLRenderer({ canvas, alpha: true, antialias: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(opt.dpr); renderer.setSize(opt.px, opt.px, false);
    renderer.outputEncoding = T.sRGBEncoding; renderer.toneMapping = T.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
    const scene = new T.Scene(); scene.environment = envMap(renderer);
    const camera = new T.PerspectiveCamera(28, 1, 0.1, 50); camera.position.set(0, 0, 4.6);
    const key = new T.DirectionalLight(0xfff0d0, 2.4); key.position.set(2.5, 3, 4); scene.add(key);
    scene.add(new T.HemisphereLight(0xfff4dd, 0x1a2340, 0.9));
    const rim = new T.PointLight(0x2dd4bf, 0, 12); rim.position.set(-2.2, 1.2, -1.5); scene.add(rim);
    const loader = new T.TextureLoader();
    const load = (n) => new Promise((res, rej) => loader.load(`assets/img/${n}.png`, (t) => { t.encoding = T.sRGBEncoding; t.anisotropy = 8; res(t); }, undefined, rej));
    const faceMat = () => new T.MeshStandardMaterial({ transparent: true, alphaTest: 0.5, metalness: 0.78, roughness: 0.36, envMapIntensity: 1.25, color: 0xffffff });
    const fm = faceMat(), bm = faceMat();
    const bodyMat = new T.MeshStandardMaterial({ color: 0xc9971f, metalness: 0.9, roughness: 0.3, envMapIntensity: 1.3 });
    const D = 0.085, S = 1.5;
    const body = new T.Mesh(new T.ExtrudeGeometry(roundedSquare(S * 0.95, 0.09), { depth: D, bevelEnabled: true, bevelThickness: 0.012, bevelSize: 0.012, bevelSegments: 3, curveSegments: 6 }), bodyMat);
    body.position.z = -D / 2;
    const front = new T.Mesh(new T.PlaneGeometry(S, S), fm); front.position.z = D / 2 + 0.013;
    const back = new T.Mesh(new T.PlaneGeometry(S, S), bm); back.position.z = -D / 2 - 0.013; back.rotation.y = Math.PI;
    const coin = new T.Group(); coin.add(body, front, back); scene.add(coin);
    let last = state();
    function render(st) {
      st = st || last; last = st;
      coin.rotation.set(st.rotX, st.rotY, st.rotZ); coin.scale.setScalar(st.scale); coin.position.set(st.x, st.y, 0);
      rim.intensity = 6 * st.glow; rim.color.set(st.glowColor);
      const k = 1 - 0.55 * st.dim; fm.color.setRGB(k, k * (1 - 0.1 * st.dim), k * (1 - 0.18 * st.dim)); bm.color.copy(fm.color);
      bodyMat.color.setRGB(0.79 * k, 0.59 * k, 0.12 * k); fm.metalness = bm.metalness = 0.78 - 0.4 * st.dim;
      renderer.render(scene, camera);
    }
    const ready = Promise.all([load(opt.front), load(opt.back)]).then(([a, b]) => { fm.map = a; bm.map = b; fm.needsUpdate = bm.needsUpdate = true; render(last); });
    window.addEventListener("hf-seek", () => render(last));
    return { render, ready, three: { renderer, scene, camera, coin } };
  }
  window.JigCoin = { make, state };
})();
