"""Fit the master audio to the joined video (kit v3, CI final job). Each unit renders to whole frames, so its mp4 can run up
to 1 frame longer than its nominal dur; over many units the video grows longer than the audio and the sound drifts early.
This cuts the master at every unit boundary and pads each piece with the unit's measured excess (silence, < 1 frame),
so every chapter starts in sync. Usage: python3 fit_audio.py vunits.json PARTS_DIR master.m4a OUT.m4a"""
import json, subprocess, sys
from pathlib import Path

def probe(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)]))

def main(uj, parts, master, out):
    units = json.load(open(uj)); S = 0.0; g = []
    for k, u in enumerate(units):
        real = probe(Path(parts) / f"{u['id']}.mp4"); e = max(0.0, real - u["dur"])
        end = f":end={S + u['dur']:.4f}" if k < len(units) - 1 else ""
        g.append(f"[0:a]atrim=start={S:.4f}{end},asetpts=PTS-STARTPTS,apad=pad_dur={e:.4f}[a{k}]"); S += u["dur"]
    g.append("".join(f"[a{k}]" for k in range(len(units))) + f"concat=n={len(units)}:v=0:a=1[aout]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", master, "-filter_complex", ";".join(g), "-map", "[aout]",
                    "-c:a", "aac", "-b:a", "256k", "-ar", "48000", out], check=True)
    print(f"fitted audio -> {out}: {probe(out):.3f} s")

if __name__ == "__main__":
    if len(sys.argv) != 5: sys.exit(__doc__)
    main(*sys.argv[1:])
