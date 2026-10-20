"""QC of a finished render (kit v3; runs in CI after every [render], or alone with [review]). Works for 16:9 and 9:16.
Writes OUT/review.txt + review.json + contact sheets:
- frame sheets (9:16: 4 fps with the Shorts safe-zone box; 16:9: one frame every max(0.25, dur/400) s)
- black / freeze detection, video-vs-audio length, loudness (integrated, true peak, momentary spikes and holes)
- voice vs SFX balance from the audio_mix stems (stems/vo_mixed.wav + stems/sfx_mixed.wav)
- SFX cue density per second (from the cue list), same-sound repeats within 6 s
Usage: python3 review.py VIDEO OUT_DIR [--stems audio/stems] [--cues sfx_cues.json|short.json]"""
import argparse, json, re, subprocess, wave
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

def run(*a): return subprocess.run(list(a), capture_output=True, text=True)
def probe(v, sel, ent):
    return run("ffprobe", "-v", "error", "-select_streams", sel, "-show_entries", ent, "-of", "csv=p=0", str(v)).stdout.strip()

def sheets(V, O, W, H, dur):
    tall = H > W; fps = 4 if tall else max(1 / 8, min(4, 400 / max(dur, 1)))
    tw = 270 if tall else 320; th = round(tw * H / W); C, R = (8, 4) if tall else (6, 6)
    f = O / "frames"; f.mkdir(exist_ok=True)
    run("ffmpeg", "-v", "error", "-i", str(V), "-vf", f"fps={fps},scale={tw}:{th}", "-q:v", "4", str(f / "%05d.jpg"))
    fs = sorted(f.glob("*.jpg")); L = 22; k = tw / W; out = []
    for s0 in range(0, len(fs), C * R):
        sub = fs[s0:s0 + C * R]; rows = (len(sub) + C - 1) // C
        sh = Image.new("RGB", (C * (tw + 6) + 6, rows * (th + L + 6) + 6), (14, 16, 24)); d = ImageDraw.Draw(sh)
        for n, p in enumerate(sub):
            t = (s0 + n) / fps; x = 6 + (n % C) * (tw + 6); y = 6 + (n // C) * (th + L + 6)
            sh.paste(Image.open(p), (x, y + L)); d.text((x + 3, y + 5), f"{int(t // 60)}:{t % 60:05.2f}", fill=(251, 191, 36))
            if tall: d.rectangle((x + 40 * k, y + L + 220 * k, x + 920 * k, y + L + 1200 * k), outline=(255, 50, 50))
        p = O / f"sheet_{s0 // (C * R):02d}.jpg"; sh.save(p, quality=84); out.append(p.name)
    return out

def stems(sd):
    def rd(p):
        with wave.open(str(p)) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32768
            return x.reshape(-1, w.getnchannels()).mean(1), w.getframerate()
    vo, sr = rd(sd / "vo_mixed.wav"); sx, _ = rd(sd / "sfx_mixed.wav"); n = min(len(vo), len(sx)); hop = int(0.25 * sr); rows = []
    for i in range(0, n - hop, hop):
        a = 20 * np.log10(np.sqrt(np.mean(vo[i:i + hop] ** 2)) + 1e-9); b = 20 * np.log10(np.sqrt(np.mean(sx[i:i + hop] ** 2)) + 1e-9)
        rows.append((i / sr, a, b))
    act = [a for _, a, _ in rows if a > -45]; sf = [b for _, _, b in rows if b > -60]
    return {"vo_median_db": round(float(np.median(act)), 1) if act else None, "sfx_median_db": round(float(np.median(sf)), 1) if sf else None,
            "sfx_close_to_vo": [round(t, 2) for t, a, b in rows if a > -45 and b > a - 9],
            "sfx_loud_without_vo": [round(t, 2) for t, a, b in rows if a < -50 and b > -32]}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("out")
    ap.add_argument("--stems", default="audio/stems"); ap.add_argument("--cues", default=None)
    a = ap.parse_args(); V, O = Path(a.video), Path(a.out); O.mkdir(parents=True, exist_ok=True)
    W, H = map(int, probe(V, "v:0", "stream=width,height").split(",")[:2])
    vd = float(probe(V, "v:0", "stream=duration") or 0); ad = float(probe(V, "a:0", "stream=duration") or 0)
    rep = {"video": V.name, "size": f"{W}x{H}", "video_s": vd, "audio_s": ad, "av_diff_s": round(abs(vd - ad), 3)}
    rep["sheets"] = sheets(V, O, W, H, vd)
    log = run("ffmpeg", "-i", str(V), "-vf", "blackdetect=d=0.04:pix_th=0.06,freezedetect=n=0.002:d=0.8", "-an", "-f", "null", "-").stderr
    rep["black"] = re.findall(r"black_start:(\S+) black_end:(\S+)", log)
    rep["freeze"] = list(zip(re.findall(r"freeze_start: (\S+)", log), re.findall(r"freeze_end: (\S+)", log)))
    lg = run("ffmpeg", "-i", str(V), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-").stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", lg); P = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", lg)
    rep["lufs"] = float(I[-1]) if I else None; rep["true_peak_dbfs"] = float(P[-1]) if P else None
    mom = [(float(t), float(m)) for t, m in re.findall(r"t:\s*([\d.]+)\s+TARGET.*?M:\s*(-?[\d.]+)", lg)]
    if mom and rep["lufs"] is not None:
        rep["loud_spikes_s"] = sorted({round(t) for t, m in mom if m > rep["lufs"] + 7})[:60]
        rep["quiet_holes_s"] = sorted({round(t) for t, m in mom if m < -40 and 1 < t < vd - 1})[:60]
    sd = Path(a.stems)
    try: rep.update(stems(sd))
    except Exception as e: rep["stems"] = f"missing ({e})"
    if a.cues:
        cj = json.load(open(a.cues)); cues = cj["sfx"] if isinstance(cj, dict) else cj
        per = Counter(int(c[0]) for c in cues); last = {}; rpt = 0
        for t, k, r, db in sorted(cues, key=lambda c: c[0]):
            if k != "key" and (k, r) in last and 0.3 < t - last[(k, r)] < 6: rpt += 1   # separate events, not tick runs
            last[(k, r)] = t
        rep["cues"] = len(cues); rep["key_clicks"] = sum(c[1] == "key" for c in cues)
        rep["busiest_seconds"] = per.most_common(5); rep["same_sound_within_6s"] = rpt
    flags = []
    if rep["av_diff_s"] > 0.1: flags.append(f"video/audio length differ by {rep['av_diff_s']} s")
    if rep["black"]: flags.append(f"{len(rep['black'])} black segment(s)")
    if rep.get("lufs") is not None and not -15.5 <= rep["lufs"] <= -13: flags.append(f"loudness {rep['lufs']} LUFS (target -14)")
    if rep.get("true_peak_dbfs") is not None and rep["true_peak_dbfs"] > -1.0: flags.append(f"true peak {rep['true_peak_dbfs']} dBTP")
    if rep.get("vo_median_db") is not None and rep.get("sfx_median_db") is not None:
        gap = rep["vo_median_db"] - rep["sfx_median_db"]; rep["vo_sfx_gap_db"] = round(gap, 1)
        if not 12 <= gap <= 22: flags.append(f"VO-SFX gap {gap:.1f} dB (aim 15-18)")
    rep["flags"] = flags
    json.dump(rep, open(O / "review.json", "w"), indent=1)
    txt = [f"{k}: {v}" for k, v in rep.items() if k != "sheets"] + [f"sheets: {len(rep['sheets'])}"]
    (O / "review.txt").write_text("\n".join(txt)); print("\n".join(txt))

if __name__ == "__main__":
    main()
