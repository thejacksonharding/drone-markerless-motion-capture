#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/HybrIK"
[[ -x "$ROOT/.venv/bin/python" ]] || { echo 'Run setup first' >&2; exit 1; }
mkdir -p pretrained_models
MODEL=pretrained_models/hybrik_hrnet.pth
EXPECTED=2151501a9999eca0940b5e8898511d964956f504780099e996e3ae59e22a94b4
if [[ ! -f "$MODEL" ]]; then
 "$ROOT/.venv/bin/python" -m gdown --fuzzy \
  'https://drive.google.com/file/d/1gp3549vIEKfbc8SDQ-YF3Idi1aoR3DkW/view' \
  --output "$MODEL" --no-cookies
fi
ACTUAL="$(shasum -a 256 "$MODEL" | awk '{print $1}')"
[[ "$ACTUAL" == "$EXPECTED" ]] || { echo "Checkpoint hash mismatch: $ACTUAL" >&2; exit 1; }
for asset in basicModel_neutral_lbs_10_207_0_v1.0.0.pkl h36m_mean_beta.npy J_regressor_h36m.npy; do
 [[ -f "model_files/$asset" ]] || { echo "Missing model_files/$asset (not distributed by this script)" >&2; exit 1; }
done
echo 'Checkpoint SHA-256 and SMPL asset filenames verified.'
