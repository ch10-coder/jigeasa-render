"""Upscale test: 1K and Flow-2K paintings to a 3840x2160 frame, with and without Real-ESRGAN.

Usage: python upscale.py in out
Writes out/<name>_<method>.jpg (full 4K frames) and out/compare_<region>.jpg (100% crops, 2x2 grid).
"""
import sys, os, time
import numpy as np, torch
from PIL import Image, ImageDraw, ImageFont
from spandrel import ModelLoader

W, H = 3840, 2160
torch.set_num_threads(os.cpu_count() or 4)


def cover(im, w=W, h=H):
    """Resize (Lanczos) to cover w x h, then centre-crop, like the video frame will."""
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def esrgan(im, path, tile=384, pad=16):
    model = ModelLoader().load_from_file(path).eval()
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


def main(src, dst):
    os.makedirs(dst, exist_ok=True)
    one, two = Image.open(f"{src}/P40_1k.jpg").convert("RGB"), Image.open(f"{src}/P40_2k.jpg").convert("RGB")
    print("1K", one.size, "2K", two.size)
    res = {}
    t = time.time(); res["A_1k_lanczos"] = cover(one)
    res["B_1k_esrgan_x4"] = cover(esrgan(one, "RealESRGAN_x4plus.pth")); print("x4 on 1K", round(time.time() - t), "s")
    res["C_2k_lanczos"] = cover(two)
    t = time.time(); res["D_2k_esrgan_x2"] = cover(esrgan(two, "RealESRGAN_x2plus.pth")); print("x2 on 2K", round(time.time() - t), "s")
    for k, im in res.items():
        im.save(f"{dst}/P40_{k}.jpg", quality=93)

    labels = {"A_1k_lanczos": "1  1K -> 4K  bina AI", "B_1k_esrgan_x4": "2  1K -> 4K  AI (Real-ESRGAN)",
              "C_2k_lanczos": "3  Flow 2K -> 4K  bina AI", "D_2k_esrgan_x2": "4  Flow 2K -> 4K  AI (Real-ESRGAN)"}
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
    except OSError:
        font = ImageFont.load_default()
    regions = {"faces": (1133, 1285), "gate": (672, 205)}  # 960x540 crops at 100% of the 4K frame
    for name, (x, y) in regions.items():
        sheet = Image.new("RGB", (1920 + 8, 1080 + 8), "black")
        for i, k in enumerate(labels):
            c = res[k].crop((x, y, x + 960, y + 540))
            d = ImageDraw.Draw(c)
            d.rectangle((0, 0, 620, 50), fill=(0, 0, 0))
            d.text((12, 6), labels[k], font=font, fill=(255, 230, 160))
            sheet.paste(c, ((i % 2) * 968, (i // 2) * 548))
        sheet.save(f"{dst}/compare_{name}.jpg", quality=92)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
