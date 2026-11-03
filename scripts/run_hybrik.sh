#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT/HybrIK"

VIDEO="../footage/processed/aidan_walking_85s_10s.mp4"
OUTPUT="res_aidan_walking_85s_10s"

if [[ ! -f "$VIDEO" ]]; then
    echo "Video not found: $VIDEO"
    exit 1
fi

if [[ -e "$OUTPUT" ]]; then
    echo "Output already exists: $OUTPUT"
    exit 1
fi

mkdir -p .cache/matplotlib

MPLCONFIGDIR=.cache/matplotlib \
  "$REPO_ROOT/.venv/bin/python" -u scripts/demo_video.py \
  --device cpu \
  --video-name "$VIDEO" \
  --out-dir "$OUTPUT" \
  --save-pk \
  --save-img

echo "Inference complete."
