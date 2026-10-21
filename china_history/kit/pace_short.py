"""kit v3 copy of rupee_short/tools/pace_short.py: edit TARGET / GAP / ANCHORS / DRAMA_AFTER per video (project/kit/ -> ROOT = project).
Long videos: MAX_TEMPO = 1.0 (no speed-up) and GAP = {"lead": 0.25, "comma": 0.22, "sentence": 0.42, "beat": 0.8, "drama": 0.6}
(keep ~0.5 s after key facts; the Industrialization pace.py squashed every pause to 0.34 s).
Pace the Rupee Short voice (Termux python + numpy + ffmpeg): shorten silences found in the AUDIO (energy), sized by
what the STT says sits around them (comma / sentence end / beat change), then, if still long, a gentle atempo.
Writes audio/voice_paced.wav and timing.json {total, tempo, beats:[{id,start,end}], words:[[t0,t1,text]]}."""
import json, subprocess, wave
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent; A = ROOT / "audio"; SR = 44100
TARGET = 52.8          # paced voice length we aim for (Short <= 60 s incl. the CTA tail)
MAX_TEMPO = 1.07
GAP = {"lead": 0.06, "comma": 0.13, "sentence": 0.23, "beat": 0.32, "drama": 0.26}
ANCHORS = [("b1-hook", "एक"), ("b2-funda", "Dollar"), ("b3-oil", "पहली"), ("b4-fpi", "दूसरी"), ("b5-rbi", "RBI"),
           ("b6-asar", "नुकसान"), ("b7-exam", "Exam")]
DRAMA_AFTER = {1}      # word index 1 = "dollar" in "Ek dollar..." keeps a dramatic beat

def load(p):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                                        capture_output=True, check=True).stdout, "<f4").astype(np.float64)
def save(p, y):
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(y, -1, 1) * 32767).astype("<i2").tobytes())

x = load(A / "full_raw.mp3")
W = [[w["start"], w["end"], w["text"]] for w in json.load(open(A / "stt_raw.json"))["words"] if w.get("type") == "word"]
# beat start word indices (sequential search)
starts, k = [], 0
for bid, tok in ANCHORS:
    while W[k][2].strip("।.,?!") != tok: k += 1
    starts.append((bid, k)); k += 1
beat_first = {i for _, i in starts[1:]}

# silence runs from 10 ms RMS
hop = int(0.01 * SR); n = len(x) // hop
db = 20 * np.log10(np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
quiet = db < -42; runs = []; i = 0
while i < n:
    if quiet[i]:
        j = i
        while j < n and quiet[j]: j += 1
        if j - i >= 14: runs.append((i * 0.01, j * 0.01))
        i = j
    else: i += 1

def kind(a, b):
    if a < 0.05: return "lead"
    nxt = next((m for m, w in enumerate(W) if w[0] >= a - 0.12), None)   # first word starting after this silence
    if nxt is None: return "tail"
    prev = nxt - 1
    if nxt in beat_first: return "beat"
    if prev in DRAMA_AFTER: return "drama"
    return "sentence" if W[prev][2][-1:] in "।.?!" else "comma"

edits = []
for a, b in runs:
    kd = kind(a, b)
    if kd == "tail": continue
    tgt = GAP[kd]
    if b - a > tgt + 0.02: edits.append((a, b, tgt, kd))

pieces, m, pos, newpos = [], [], 0.0, 0.0
F = int(0.006 * SR)
for a, b, tgt, kd in edits:
    mid_a = a + tgt / 2; mid_b = b - tgt / 2     # keep tgt/2 of silence on each side, cut the middle
    seg = x[int(pos * SR):int(mid_a * SR)].copy()
    if pieces and len(seg) > F: seg[:F] *= np.linspace(0, 1, F)
    if len(seg) > F: seg[-F:] *= np.linspace(1, 0, F)
    pieces.append(seg); m.append((pos, newpos)); newpos += len(seg) / SR; pos = mid_b
seg = x[int(pos * SR):].copy()
if len(seg) > F: seg[:F] *= np.linspace(0, 1, F)
pieces.append(seg); m.append((pos, newpos)); newpos += len(seg) / SR
y = np.concatenate(pieces)

def T(t):  # raw -> paced (cut regions collapse to their join point)
    for k in range(len(m)):
        r0, n0 = m[k]; r1 = m[k + 1][0] if k + 1 < len(m) else 1e9
        if t < r0: return n0
        if t < r1:
            seglen = (m[k + 1][1] - n0) if k + 1 < len(m) else 1e9
            return n0 + min(t - r0, seglen)
    return newpos

paced = len(y) / SR
tempo = round(min(MAX_TEMPO, max(1.0, paced / TARGET)), 3)
if tempo < 1.01: tempo = 1.0
save(A / "voice_paced_1x.wav", y)
if tempo > 1.0:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(A / "voice_paced_1x.wav"), "-af", f"atempo={tempo}", "-ar", str(SR), "-ac", "1",
                    str(A / "voice_paced.wav")], check=True)
else:
    save(A / "voice_paced.wav", y)
total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(A / "voice_paced.wav")]))
words = [[round(T(s) / tempo, 3), round(T(e) / tempo, 3), t] for s, e, t in W]
beats = []
for k, (bid, wi) in enumerate(starts):
    s0 = 0.0 if k == 0 else round(words[wi][0] - GAP["beat"] / tempo / 2, 3)   # cut in the middle of the pause before the beat
    beats.append({"id": bid, "start": s0})
for k in range(len(beats)):
    beats[k]["end"] = beats[k + 1]["start"] if k + 1 < len(beats) else round(total, 3)
json.dump({"total": round(total, 3), "tempo": tempo, "beats": beats, "words": words}, open(ROOT / "timing.json", "w"), ensure_ascii=False, indent=0)
print(f"raw {len(x) / SR:.2f}s -> paced {paced:.2f}s -> tempo {tempo} -> {total:.2f}s; edits {len(edits)}",
      {k: sum(1 for e in edits if e[3] == k) for k in GAP})
for b_ in beats: print(f"  {b_['id']:9s} {b_['start']:6.2f} - {b_['end']:6.2f}  ({b_['end'] - b_['start']:.2f}s)")
