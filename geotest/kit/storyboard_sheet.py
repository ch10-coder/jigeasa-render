"""9:16 storyboard contact sheet: frames sorted by time, timecode label, text safe zone (y 200-1520) + the like/comment column (x 910+, y 1000+); visuals may fill the whole frame. Usage: storyboard_sheet.py SHOTS_DIR OUT.jpg"""
import glob, re, sys
from PIL import Image, ImageDraw
fs = glob.glob(sys.argv[1] + "/*.png")
def t_of(f):
    m = re.search(r"t([0-9]+\.[0-9]+)", f.split("/")[-1])
    return float(m.group(1)) if m else 0.0
fs.sort(key=t_of); W, H, COLS, LAB = 270, 480, 6, 26; k = W / 1080
rows = (len(fs) + COLS - 1) // COLS
sh = Image.new("RGB", (COLS * W + (COLS + 1) * 8, rows * (H + LAB + 8) + 8), (14, 16, 24)); d = ImageDraw.Draw(sh)
for n, f in enumerate(fs):
    im = Image.open(f).convert("RGB").resize((W, H)); x = 8 + (n % COLS) * (W + 8); y = 8 + (n // COLS) * (H + LAB + 8)
    sh.paste(im, (x, y + LAB)); d.text((x + 4, y + 6), f"{t_of(f):.2f}s", fill=(251, 191, 36))
    d.rectangle((x + 40 * k, y + LAB + 200 * k, x + 1040 * k, y + LAB + 1520 * k), outline=(255, 70, 70), width=1)   # text zone (2026-10-17)
    d.rectangle((x + 910 * k, y + LAB + 1000 * k, x + 1040 * k, y + LAB + 1520 * k), outline=(255, 160, 60), width=1)   # like/comment column
sh.save(sys.argv[2], quality=86); print(sys.argv[2], sh.size, len(fs), "frames")
