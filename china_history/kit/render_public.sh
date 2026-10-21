#!/bin/sh
# One command per CI step (2026-10-17): mix audio in the PRIVATE repo, then lint/preview/4K-render in the PUBLIC repo.
# Usage: sh kit/render_public.sh /root/hf/<project> render/<project> "[preview] msg"   (or "[render] msg")
# Needs gh logged in; light on the phone (waits on GitHub, downloads ~10 MB of audio).
set -e
P=$(cd "$1" && pwd); BR=$2; MSG=$3; K=$(dirname "$0"); export TMPDIR=${TMPDIR:-/tmp/claude-0/ghtmp}; mkdir -p "$TMPDIR"
sh "$K/sync_repo.sh" "$P" "$BR" "[audio] ${MSG#*] }"
sleep 8; ID=$(gh run list -R ch10-coder/Video -b "$BR" -L 1 --json databaseId -q '.[0].databaseId')
echo "private audio run $ID"; gh run watch "$ID" -R ch10-coder/Video --exit-status >/dev/null
rm -rf "$P/audio/_ci"; gh run download "$ID" -R ch10-coder/Video -n audio -D "$P/audio/_ci" 2>/dev/null \
  || gh release download "audio-$(echo "$BR" | tr / -)" -R ch10-coder/Video -D "$P/audio/_ci" --clobber   # artifact quota full: release fallback
cp "$P/audio/_ci/master.m4a" "$P/audio/master.m4a"; cp "$P/audio/_ci/stems/audio_report.json" "$P/audio/audio_report.json" 2>/dev/null || cp "$P/audio/_ci/audio_report.json" "$P/audio/" 2>/dev/null || true
rm -rf "$P/audio/_ci"; cat "$P/audio/audio_report.json" 2>/dev/null | cut -c1-200; echo
JIG_PUBLIC=1 sh "$K/sync_repo.sh" "$P" "$BR" "$MSG"
sleep 8; echo "public run: $(gh run list -R ch10-coder/jigeasa-render -b "$BR" -L 1 --json databaseId,url -q '.[0].url')"
