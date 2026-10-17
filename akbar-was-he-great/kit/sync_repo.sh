#!/bin/sh
# Phone-side step (light): copy one kit-based project into ch10-coder/Video and push; the commit message picks the CI mode.
# Usage: sh kit/sync_repo.sh /root/hf/<project> render/<project> "[preview] what changed"
#   copies: kit/, units.json, preview.json, sfx_cues.json | short.json, timing.json, audio_mix.args, review_run.txt,
#           every unit dir in units.json (index.html, hyperframes.json, meta.json, assets/), audio/voice_paced.(flac|wav)
#           or tools/ + the files listed in ci_files.txt (inputs of tools/prep_audio.py), and only the SFX the cues use.
# Writes .github/workflows/render-<slug>.yml from kit/ci/render.yml. Refuses files > 95 MB (GitHub limit 100 MB).
# Optional env: CLAUDE_SESSION_URL (adds a Claude-Session trailer), CO_AUTHOR (default Claude Opus 5.5),
#   JIG_REPO (clone to use, default /root/hf/Video-repo), DRY_RUN=1 (copy + stage only: no commit, no push),
#   JIG_PUBLIC=1: push to the PUBLIC ch10-coder/jigeasa-render instead: no raw SFX, no voice files, but audio/master.m4a
#   (+ audio_report.json) from the private [audio] run, plus fonts' OFL texts and the photo licence list.
set -e
P=$(cd "$1" && pwd); BR=$2; MSG=$3; S=$(basename "$P")
if [ -n "$JIG_PUBLIC" ]; then GH=ch10-coder/jigeasa-render; R=${JIG_REPO:-/root/hf/jigeasa-render}; else GH=ch10-coder/Video; R=${JIG_REPO:-/root/hf/Video-repo}; fi
[ -n "$BR" ] && [ -n "$MSG" ] || { echo "usage: sync_repo.sh PROJECT_DIR BRANCH MESSAGE"; exit 2; }
L=${JIG_LIB:-/mnt/sdcard/TermuxFiles/Assets/jigeasa_library}/sfx
[ -d $R/.git ] || gh repo clone $GH $R -- -q
cd $R && git fetch -q origin
if git ls-remote --exit-code --heads origin "$BR" >/dev/null 2>&1; then git checkout -q -B "$BR" "origin/$BR"; else git checkout -q -B "$BR" origin/main; fi
D=$R/$S; rm -rf "$D"; mkdir -p "$D/audio" "$R/.github/workflows"
cp -r "$P/kit" "$D/"; rm -rf "$D/kit/__pycache__"
for f in units.json preview.json sfx_cues.json short.json timing.json audio_mix.args review_run.txt; do [ -f "$P/$f" ] && cp "$P/$f" "$D/"; done
python3 - "$P" "$D" <<'PY'
import json, shutil, sys
from pathlib import Path
P, D = Path(sys.argv[1]), Path(sys.argv[2])
SKIP = shutil.ignore_patterns("kit", "audio", "voice", "node_modules", "renders", "snapshots", "capture", "tools", "boards", ".hyperframes", "__pycache__", "*.md", ".media")
for u in json.load(open(P / "units.json")):
    s, d = P / u["dir"], D / u["dir"]
    if (s / "compositions").is_dir():   # a HyperFrames workflow project (index + sub-compositions): copy the whole tree
        shutil.copytree(s, d, ignore=SKIP, dirs_exist_ok=True, copy_function=lambda a, b: open(b, "wb").write(open(a, "rb").read())); continue   # plain copy: proot breaks sendfile on Termux-owned files
    d.mkdir(parents=True, exist_ok=True)
    for f in ("index.html", "hyperframes.json", "meta.json"): shutil.copy(s / f, d / f)
    shutil.copytree(s / "assets", d / "assets")
PY
if [ -n "$JIG_PUBLIC" ]; then
  if [ -f "$P/audio/master.m4a" ]; then cp "$P/audio/master.m4a" "$D/audio/"; elif [ -z "$NO_AUDIO" ]; then echo "no audio/master.m4a: run the private [audio] step first (kit/render_public.sh), or NO_AUDIO=1 for a sketch preview"; exit 4; fi
  [ -f "$P/audio/audio_report.json" ] && cp "$P/audio/audio_report.json" "$D/audio/"
  cp /root/.claude/skills/jigeasa-video/assets/fonts/OFL-*.txt "$D/" 2>/dev/null || true
  cp "${JIG_LIB:-/mnt/sdcard/TermuxFiles/Assets/jigeasa_library}/LICENSES.md" "$D/PHOTO_AND_SFX_CREDITS.md"
elif [ -f "$P/audio/voice_paced.flac" ]; then cp "$P/audio/voice_paced.flac" "$D/audio/"
elif [ -f "$P/audio/voice_paced.wav" ] && [ ! -f "$P/tools/prep_audio.py" ]; then cp "$P/audio/voice_paced.wav" "$D/audio/"; fi
if [ -z "$JIG_PUBLIC" ] && [ -f "$P/tools/prep_audio.py" ]; then
  cp -r "$P/tools" "$D/"; rm -rf "$D/tools/__pycache__"
  [ -f "$P/ci_files.txt" ] && while read -r f; do [ -n "$f" ] && mkdir -p "$D/$(dirname "$f")" && cp "$P/$f" "$D/$f"; done < "$P/ci_files.txt"
fi
[ -n "$JIG_PUBLIC" ] || python3 - "$P" "$D" "$L" <<'PY'
import glob, json, shutil, sys
from pathlib import Path
P, D, L = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
c = json.load(open(P / "sfx_cues.json")) if (P / "sfx_cues.json").exists() else json.load(open(P / "short.json"))["sfx"]
n = 0
for t, k, r, db in c:
    if k in ("mk", "key"):
        src = glob.glob(f"{L}/mixkit/*_{r}.mp3")
        if not src: raise SystemExit(f"SFX mixkit {r} not in the library")
        dst = D / "sfx/mixkit" / Path(src[0]).name
    else:
        sub = "kenney_impact-sounds" if k == "kip" else "kenney_interface-sounds"; src = [f"{L}/kenney/{sub}/Audio/{r}"]
        dst = D / "sfx/kenney" / sub / "Audio" / r
    if not dst.exists(): dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy(src[0], dst); n += 1
print("sfx files", n)
PY
sed "s|__PROJECT__|$S|g; s|__BRANCH__|$BR|g" "$P/kit/ci/render.yml" > "$R/.github/workflows/render-$S.yml"
big=$(find "$D" -type f -size +97280k)   # 95 MB; busybox find has no M suffix
[ -z "$big" ] || { echo "too big for GitHub (>95 MB): $big - commit FLAC or let tools/prep_audio.py make it in CI"; exit 3; }
git add -A
if [ -n "$DRY_RUN" ]; then git status --short | sed -n "1,12p"; echo "DRY_RUN: staged $(git diff --cached --name-only | wc -l) files, nothing committed"; exit 0; fi
T="Co-Authored-By: ${CO_AUTHOR:-Claude Opus 5.5 <noreply@anthropic.com>}"
[ -n "$CLAUDE_SESSION_URL" ] && T="$T
Claude-Session: $CLAUDE_SESSION_URL"
git -c user.name=ch10-coder -c user.email=7889304846ch10@gmail.com commit -q -m "$MSG

$T"
git push -q -u origin "$BR"
git log --oneline -1
