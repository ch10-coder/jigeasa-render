/* Historifing painting camera (seek-safe, deterministic GSAP).
   One call per frame, inside the frame's timeline script, BEFORE registering the timeline:
     HFKB.build(tl, document.querySelector('[data-composition-id="<frame_id>"]'), { fadeIn: 0.6, fadeOut: 0.6, xf: 0.8 });
   Markup per shot (all times in seconds, relative to the frame):
     <div id="<frame_id>-s3" class="clip kb-shot" data-start="21.40" data-duration="9.10" data-track-index="0"
          data-from="0.50,0.50,1.04" data-to="0.62,0.38,1.22" data-ease="sine.inOut">
       <div class="kb-fade"><div class="kb-cam"><img class="kb-img" src="assets/paint/P13.jpg" alt=""></div></div>
     </div>
   data-from / data-to = "cx,cy,zoom": the image point (0..1 from the left / top) the camera centres on, and the zoom
   (1 = whole painting fills the frame, 1.25 = 25 % closer). Pan and push are clamped so a painting edge never shows.
   Shot k+1 starts xf seconds before shot k ends and dissolves in on top of it; the first shot fades up from black
   (fadeIn) and the last one fades down to black (fadeOut) at the end of the frame. */
(function () {
  function parse(s) { return String(s).split(",").map(Number); }
  function frameVars(cx, cy, z) {
    z = Math.max(1, z || 1);
    var lim = (z - 1) * 50;                                   // % of the element size that stays covered
    var x = -(cx - 0.5) * z * 100, y = -(cy - 0.5) * z * 100;
    x = Math.max(-lim, Math.min(lim, x)); y = Math.max(-lim, Math.min(lim, y));
    return { scale: z, xPercent: x, yPercent: y };
  }
  function build(tl, root, o) {
    o = o || {};
    var xf = o.xf != null ? o.xf : 0.8, fin = o.fadeIn != null ? o.fadeIn : 0.6, fout = o.fadeOut != null ? o.fadeOut : 0.6;
    var shots = Array.prototype.slice.call(root.querySelectorAll(".kb-shot"));
    shots.sort(function (a, b) { return parseFloat(a.getAttribute("data-start")) - parseFloat(b.getAttribute("data-start")); });
    shots.forEach(function (el, i) {
      var s = parseFloat(el.getAttribute("data-start")), d = parseFloat(el.getAttribute("data-duration"));
      var cam = el.querySelector(".kb-cam"), fade = el.querySelector(".kb-fade");
      var a = frameVars.apply(null, parse(el.getAttribute("data-from")));
      var b = frameVars.apply(null, parse(el.getAttribute("data-to")));
      b.duration = d; b.ease = el.getAttribute("data-ease") || "sine.inOut";
      tl.fromTo(cam, a, b, s);
      if (i === 0 && fin > 0) tl.fromTo(fade, { opacity: 0 }, { opacity: 1, duration: fin, ease: "power1.out" }, s);
      else if (i > 0) tl.fromTo(fade, { opacity: 0 }, { opacity: 1, duration: xf, ease: "sine.inOut" }, s);
      if (i === shots.length - 1 && fout > 0) tl.to(fade, { opacity: 0, duration: fout, ease: "power1.in" }, s + d - fout);
    });
    return tl;
  }
  window.HFKB = { build: build, frameVars: frameVars };
})();
