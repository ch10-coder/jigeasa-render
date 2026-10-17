"""JIGEASA audio mix (kit v3): SFX bed from a cue list + VO chain + sidechain ducking + two-pass loudnorm.
Replaces industrialization tools/audio.py + master.sh and rupee tools/short_audio.py. Fixed (pipeline audit 2026-10-17):
- SFX stay STEREO (old code summed them to mono) and each cue gets a small deterministic pitch/gain/pan variation,
  so one whoosh used 55 times in 13 min no longer sounds copy-pasted;
- overlapping cues pass a soft limiter (old code scaled the WHOLE bed down by its single loudest overlap);
- no lowpass 7-8 kHz on the SFX (it dulled clicks and whooshes; highpass now 55 Hz, not 80-90, keeps impact punch); a -3 dB
  presence dip at ~3 kHz leaves room for the voice instead;
- SFX duck under the voice (sidechain) and there is no bus compressor (it pumped the voice on every impact);
- one loudness target for long videos and Shorts: about -14 LUFS integrated, true peak about -1.5 dBTP.
Usage (in CI; on the phone only for a Short, never the long master):
  python3 audio_mix.py --voice audio/voice_paced.wav --cues sfx_cues.json --dur 777.4 --out audio/master.m4a \
      [--sfx-dir sfx] [--lufs -14] [--sfx-db 0] [--key-db 0] [--stems audio/stems] [--no-vary]
--cues takes a list of [t, kind, ref, gain_db] or a JSON object with a "sfx" list (short.json).
kind: mk / key = Mixkit id (file *_<id>.mp3), kip = Kenney impact file, kif = Kenney interface file."""
import argparse, json, os, random, re, subprocess, wave
from pathlib import Path
import numpy as np

SR = 44100
SOUND_OPTS = {2826: {"hit": 0, "tail": 1.6}}   # per-sound overrides (Mixkit 2826 "pour" starts ON the cue)

def dec(p, ch=2):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, "<f4").reshape(-1, ch).astype(np.float32)

def save(p, x):
    x = x.reshape(len(x), -1)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(x.shape[1]); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())

class Library:
    def __init__(self, root):
        self.root = Path(root); self.cache = {}
    def path(self, kind, ref):
        if kind in ("mk", "key"):
            hit = sorted((self.root / "mixkit").glob(f"*_{ref}.mp3"))
            if not hit: raise SystemExit(f"SFX missing: mixkit *_{ref}.mp3 under {self.root}")
            return hit[0]
        sub = "kenney_impact-sounds" if kind == "kip" else "kenney_interface-sounds"
        return self.root / "kenney" / sub / "Audio" / ref
    def load(self, kind, ref):
        """(stereo samples peak-normalised to 1, hit index): the hit (RMS peak, or the attack for key clicks) lands on the cue."""
        k = (kind, ref)
        if k in self.cache: return self.cache[k]
        x = dec(self.path(kind, ref)); m = np.abs(x).max(1)
        idx = np.where(m > m.max() * 10 ** (-50 / 20))[0]; x = x[idx[0]:idx[-1] + 1]; m = np.abs(x).max(1)
        w = int(0.02 * SR); rms = np.sqrt(np.convolve((x ** 2).mean(1), np.ones(w) / w, "same"))
        hit = int(np.argmax(m > m.max() * 0.3)) if kind == "key" else int(np.argmax(rms))
        o = SOUND_OPTS.get(ref, {}); hit = o.get("hit", hit)
        tail = o.get("tail", 0.16 if kind == "key" else 2.5)
        x = x[:min(len(x), hit + int(tail * SR))].copy()
        fl = min(len(x) - hit, int((0.06 if kind == "key" else 0.25) * SR))
        if fl > 0: x[-fl:] *= np.linspace(1, 0, fl, dtype=np.float32)[:, None]
        self.cache[k] = (x / (np.abs(x).max() + 1e-9), hit)
        return self.cache[k]

def vary(x, hit, kind, ref, t):
    """Deterministic round-robin: +-0.7 semitone (+-0.4 for keys), +-1.2 dB, small pan. Same input -> same output."""
    r = random.Random(f"{kind}:{ref}:{t:.3f}")
    semis = r.uniform(-0.4, 0.4) if kind == "key" else r.uniform(-0.7, 0.7)
    rate = 2 ** (semis / 12); n = int(len(x) / rate)
    pos = np.arange(n, dtype=np.float64) * rate; base = np.arange(len(x))
    y = np.stack([np.interp(pos, base, x[:, c]) for c in range(x.shape[1])], 1).astype(np.float32)
    pan = r.uniform(-0.12, 0.12) if kind == "key" else r.uniform(-0.22, 0.22); th = (pan + 1) * np.pi / 4
    y[:, 0] *= np.cos(th) * np.sqrt(2); y[:, 1] *= np.sin(th) * np.sqrt(2)
    return y * 10 ** (r.uniform(-1.2, 1.2) / 20), int(hit / rate)

def soft_limit(x, thr=0.7):
    a = np.abs(x); over = a > thr
    x[over] = np.sign(x[over]) * (thr + (1 - thr) * np.tanh((a[over] - thr) / (1 - thr)))
    return x

def build_bed(cues, dur, lib, sfx_db=0.0, key_db=0.0, do_vary=True):
    n = int(dur * SR); bed = np.zeros((n + 4 * SR, 2), np.float32); last = {}; used = 0
    for t, kind, ref, db in sorted(cues, key=lambda c: c[0]):
        if kind != "key" and last.get((kind, ref), -9) > t - 0.05: continue   # double trigger (same sound < 50 ms apart); 0.09 s odometer ticks stay
        last[(kind, ref)] = t
        x, hit = lib.load(kind, ref)
        if do_vary: x, hit = vary(x, hit, kind, ref, t)
        x = x * 10 ** ((db + (key_db if kind == "key" else sfx_db)) / 20); i = int(t * SR) - hit
        if i < 0: x = x[-i:]; i = 0
        if i >= len(bed): continue
        bed[i:i + len(x)] += x[:len(bed) - i]; used += 1
    return soft_limit(bed[:n]), used

def loudnorm(pre, out, lufs, tp=-1.5):
    j = subprocess.run(["ffmpeg", "-v", "info", "-i", str(pre), "-af", f"loudnorm=I={lufs}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    J = json.loads(j[j.rindex("{"):j.rindex("}") + 1])
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(pre), "-af",
                    f"loudnorm=I={lufs}:TP={tp}:LRA=11:measured_I={J['input_i']}:measured_TP={J['input_tp']}:measured_LRA={J['input_lra']}:"
                    f"measured_thresh={J['input_thresh']}:linear=true,alimiter=limit=0.82:attack=1:release=40:level=disabled",
                    "-ar", str(SR), "-c:a", "aac", "-b:a", "192k", str(out)], check=True)

def balance(vo, sx):
    """VO vs SFX level per 0.25 s window (dB): the numbers the review reads."""
    hop = int(0.25 * SR); n = min(len(vo), len(sx)); rows = []
    for i in range(0, n - hop, hop):
        a = 20 * np.log10(np.sqrt(np.mean(vo[i:i + hop] ** 2)) + 1e-9); b = 20 * np.log10(np.sqrt(np.mean(sx[i:i + hop] ** 2)) + 1e-9)
        rows.append((i / SR, a, b))
    act = [a for _, a, _ in rows if a > -45]; sfx = [b for _, _, b in rows if b > -60]
    return {"vo_median_db": round(float(np.median(act)), 1) if act else None,
            "sfx_median_db": round(float(np.median(sfx)), 1) if sfx else None,
            "sfx_within_6db_of_vo": [round(t, 2) for t, a, b in rows if a > -45 and b > a - 6][:40]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True); ap.add_argument("--cues", required=True); ap.add_argument("--dur", type=float)
    ap.add_argument("--out", required=True); ap.add_argument("--sfx-dir", default=os.environ.get("JIG_SFX", "/mnt/sdcard/TermuxFiles/Assets/jigeasa_library/sfx"))
    ap.add_argument("--lufs", type=float, default=-14.0); ap.add_argument("--sfx-db", type=float, default=0.0); ap.add_argument("--key-db", type=float, default=0.0)
    ap.add_argument("--stems", default=None); ap.add_argument("--no-vary", action="store_true")
    a = ap.parse_args()
    cj = json.load(open(a.cues)); cues = cj["sfx"] if isinstance(cj, dict) else cj
    dur = a.dur or (cj.get("dur") if isinstance(cj, dict) else None)
    if not dur: raise SystemExit("--dur missing (or give a short.json with dur)")
    out = Path(a.out); st = Path(a.stems) if a.stems else out.parent / "stems"; st.mkdir(parents=True, exist_ok=True)
    bed, used = build_bed(cues, dur, Library(a.sfx_dir), a.sfx_db, a.key_db, not a.no_vary)
    v = dec(a.voice, 1)[:, 0]; n = int(dur * SR); vo = np.zeros(n, np.float32); vo[:min(n, len(v))] = v[:n]
    save(st / "vo.wav", vo); save(st / "sfx.wav", bed); pre = st / "pre.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(st / "vo.wav"), "-i", str(st / "sfx.wav"), "-filter_complex",
                    "[0]highpass=f=75,equalizer=f=200:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.2:g=2.5,deesser=i=0.35,"
                    "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3dB,pan=stereo|c0=c0|c1=c0,asplit=3[v][vk][vm];"   # pan, not aformat: aformat upmixes mono at -3 dB
                    "[1]highpass=f=55,equalizer=f=3000:t=q:w=0.9:g=-3,volume=-3dB[s0];"
                    "[s0][vk]sidechaincompress=threshold=0.08:ratio=2.5:attack=15:release=250,asplit=2[s][sm];"
                    "[v][s]amix=inputs=2:normalize=0,alimiter=limit=0.89:attack=2:release=50[mix]",
                    "-map", "[mix]", "-ac", "2", str(pre), "-map", "[vm]", "-ac", "1", str(st / "vo_mixed.wav"),
                    "-map", "[sm]", "-ac", "1", str(st / "sfx_mixed.wav")], check=True)
    loudnorm(pre, out, a.lufs)
    vm = dec(st / "vo_mixed.wav", 1)[:, 0]; sm = dec(st / "sfx_mixed.wav", 1)[:, 0]   # levels as heard (after EQ/duck)
    lg = subprocess.run(["ffmpeg", "-v", "info", "-i", str(out), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", lg); P = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", lg)
    rep = {"out": str(out), "dur": dur, "cues": len(cues), "cues_used": used, "lufs": float(I[-1]) if I else None,
           "true_peak_dbfs": float(P[-1]) if P else None, **balance(vm, sm)}
    json.dump(rep, open(st / "audio_report.json", "w"), indent=1); print(json.dumps(rep))

if __name__ == "__main__":
    main()
