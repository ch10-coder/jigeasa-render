"""Bake the background-photo grade into the JPEG (kit v3) instead of a per-frame CSS filter on a moving image.
Presets:
  deep  = the look used up to Industrialization v4 (CSS grayscale .25 + saturate .85 + brightness .62 + contrast 1.06)
  clean = brighter editorial look (user 2026-10-17: "dimmed stock photos" read as template work): more colour and
          light, gentle navy split-tone in the shadows, vignette; pair it with the lighter #bgshade that
          jg.Scene.write(grade="clean") switches on.
Usage: bake(src, out, (W, H), preset="clean", focal=(0.5, 0.5))   (Termux python: Pillow + numpy; light)."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance

NAVY = np.array([11, 18, 32], np.float32)
PRESETS = {
    "deep": dict(color=0.64, bright=0.62, contrast=1.06, navy=0.0, vig=0.0),
    "clean": dict(color=0.92, bright=0.86, contrast=1.05, navy=0.14, vig=0.30),
}

def cover(im, W, H, focal=(0.5, 0.5)):
    """Crop to the W:H aspect around a focal point, then resize (object-fit: cover)."""
    iw, ih = im.size; r = W / H
    cw, ch = (int(ih * r), ih) if iw / ih > r else (iw, int(iw / r))
    x0 = min(max(0, int(focal[0] * iw - cw / 2)), iw - cw); y0 = min(max(0, int(focal[1] * ih - ch / 2)), ih - ch)
    return im.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)

def bake(src, out, size=(1920, 1080), preset="clean", focal=(0.5, 0.5), oversize=1.12):
    """oversize: the CSS shows the image at 110-112 % for the Ken Burns pan, so bake a little larger than the canvas."""
    p = PRESETS[preset]; W, H = (round(size[0] * oversize), round(size[1] * oversize))
    im = cover(Image.open(src).convert("RGB"), W, H, focal)
    im = ImageEnhance.Color(im).enhance(p["color"]); im = ImageEnhance.Brightness(im).enhance(p["bright"])
    im = ImageEnhance.Contrast(im).enhance(p["contrast"])
    a = np.asarray(im).astype(np.float32)
    if p["navy"]:   # split-tone: shadows lean navy, highlights stay neutral
        lum = (a @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None] / 255
        k = p["navy"] * (1 - lum) ** 1.5
        a = a * (1 - k) + NAVY * k
    if p["vig"]:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = ((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2
        v = 1 - p["vig"] * np.clip(d - 0.35, 0, 1)
        a = a * v[..., None] + NAVY * (1 - v[..., None])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(out, quality=88)
    return out

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3: sys.exit("usage: photo_grade.py SRC OUT [deep|clean] [W H]")
    W, H = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1920, 1080)
    print(bake(sys.argv[1], sys.argv[2], (W, H), sys.argv[3] if len(sys.argv) > 3 else "clean"))
