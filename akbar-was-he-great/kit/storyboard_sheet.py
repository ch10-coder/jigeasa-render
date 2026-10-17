"""9:16 storyboard contact sheet: frames sorted by time, timecode label, red YouTube-Shorts safe-zone box (x 40-920, y 220-1200)
and caption band (y 1250). Usage: storyboard_sheet.py SHOTS_DIR OUT.jpg"""
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
    d.rectangle((x + 40 * k, y + LAB + 220 * k, x + 920 * k, y + LAB + 1200 * k), outline=(255, 50, 50), width=1)
    d.line((x, y + LAB + 1250 * k, x + W, y + LAB + 1250 * k), fill=(255, 120, 120), width=1)
sh.save(sys.argv[2], quality=86); print(sys.argv[2], sh.size, len(fs), "frames")
