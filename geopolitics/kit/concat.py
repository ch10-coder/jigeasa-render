"""Join rendered units into one video (kit v3). Runs in CI (final job); safe to test on the phone with tiny clips only.
units.json: [{id, dur, pre, xfade?}] in order; dur INCLUDES the unit's pre-roll (jg.Scene.write returns it that way).
- every pre == 0 -> concat demuxer, stream copy (no re-encode; the old behaviour)
- some pre > 0  -> xfade chain: unit k's pre-roll overlaps the last `pre` seconds of the video so far, so the joined
  length = sum(dur) - sum(pre) = the audio master length. Transition per unit: units[k]["xfade"] (ffmpeg xfade
  name: fade, fadeblack, smoothleft, circleopen, zoomin, ...), default "fade". Re-encodes once (x264 CRF 15).
Usage: python3 concat.py units.json PARTS_DIR OUT.mp4"""
import json, os, subprocess, sys
from pathlib import Path

def plan(units):
    """(xfade offsets, expected length) - pure function, unit-tested in the skill audit."""
    L = units[0]["dur"] - units[0].get("pre", 0.0); offs = []
    for u in units[1:]:
        p = u.get("pre", 0.0); offs.append(round(L - p, 4)); L += u["dur"] - p
    return offs, round(L, 4)

def main(uj, parts, out):
    units = json.load(open(uj)); parts = Path(parts); files = [str(parts / f"{u['id']}.mp4") for u in units]
    offs, L = plan(units)
    if not any(u.get("pre", 0.0) for u in units[1:]):
        lst = Path(out).with_suffix(".txt"); lst.write_text("".join(f"file '{Path(f).resolve()}'\n" for f in files))
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-an", "-c:v", "copy", out]
    else:
        g = [f"[{k}:v]settb=AVTB,fps=30,format=yuv420p[v{k}]" for k in range(len(files))]; prev = "v0"
        for k, (u, o) in enumerate(zip(units[1:], offs), start=1):
            nxt = f"x{k}" if k < len(files) - 1 else "vout"
            g.append(f"[{prev}][v{k}]xfade=transition={u.get('xfade', 'fade')}:duration={u['pre']}:offset={o}[{nxt}]"); prev = nxt
        cmd = ["ffmpeg", "-y", "-v", "error"] + sum((["-i", f] for f in files), []) + [
            "-filter_complex", ";".join(g), "-map", "[vout]", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
            "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
            "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    got = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out]))
    print(f"joined {len(files)} units -> {out}: {got:.3f} s (expected {L:.3f})")
    if os.environ.get("JIG_ALIGN") and not any(u.get("pre", 0.0) for u in units[1:]):
        L = round(sum(float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f])) for f in files), 4)
        print(f"JIG_ALIGN: expected = sum of rendered units {L:.3f} s (fit_audio.py pads the audio to match)")
    if abs(got - L) > 0.05: sys.exit(f"length mismatch {got:.3f} vs {L:.3f}: audio would drift")

if __name__ == "__main__":
    if len(sys.argv) != 4: sys.exit(__doc__)
    main(*sys.argv[1:])
