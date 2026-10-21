"""Upscale every painting of one render unit in place with Real-ESRGAN x2 (CI only, CPU).
Flow 2K paintings (2752x1536) become 5504x3072, so a 4K frame with up to 1.4x camera zoom still has real detail.
Usage: python3 upscale.py UNIT_DIR/assets/paint MODEL.pth"""
import os, sys, time
from pathlib import Path
import numpy as np, torch
from PIL import Image
from spandrel import ModelLoader

torch.set_num_threads(os.cpu_count() or 4)

def esrgan(model, im, tile=384, pad=16):
    sc = model.scale
    a = torch.from_numpy(np.asarray(im.convert("RGB"), dtype=np.float32) / 255).permute(2, 0, 1)[None]
    _, _, h, w = a.shape
    out = torch.zeros(1, 3, h * sc, w * sc)
    with torch.no_grad():
        for y in range(0, h, tile):
            for x in range(0, w, tile):
                y0, x0 = max(y - pad, 0), max(x - pad, 0)
                y1, x1 = min(y + tile + pad, h), min(x + tile + pad, w)
                r = model(a[:, :, y0:y1, x0:x1]).clamp(0, 1)
                ty, tx = (y - y0) * sc, (x - x0) * sc
                th, tw = (min(y + tile, h) - y) * sc, (min(x + tile, w) - x) * sc
                out[:, :, y * sc:y * sc + th, x * sc:x * sc + tw] = r[:, :, ty:ty + th, tx:tx + tw]
    return Image.fromarray((out[0].permute(1, 2, 0).numpy() * 255).round().astype(np.uint8))

def main(d, weights):
    model = ModelLoader().load_from_file(weights).eval()
    for f in sorted(Path(d).glob("*.jpg")):
        im = Image.open(f)
        if im.width >= 4000: print(f"{f.name}: already {im.size}"); continue
        t = time.time(); up = esrgan(model, im)
        up.save(f, quality=94, subsampling=0)
        print(f"{f.name}: {im.size} -> {up.size} in {time.time() - t:.0f} s", flush=True)

if __name__ == "__main__":
    main(*sys.argv[1:3])
