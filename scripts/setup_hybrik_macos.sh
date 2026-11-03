#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON39="${PYTHON39:-$HOME/.pyenv/versions/3.9.21/bin/python}"
[[ -x "$PYTHON39" ]] || { echo "Missing Python 3.9.21: $PYTHON39" >&2; exit 1; }
[[ -d HybrIK ]] || { echo 'Missing HybrIK directory' >&2; exit 1; }
[[ -f HybrIK/scripts/pytorch3d_cpu_bounds.patch ]] || { echo 'Missing required CPU patch; preserve it from the working checkout' >&2; exit 1; }
grep -q -- '--device' HybrIK/scripts/demo_video.py || { echo 'demo_video.py must support --device (working macOS modification missing)' >&2; exit 1; }
[[ -f HybrIK/model_files/basicModel_neutral_lbs_10_207_0_v1.0.0.pkl ]] || { echo 'Missing SMPL assets in HybrIK/model_files' >&2; exit 1; }
if [[ ! -d .venv ]]; then "$PYTHON39" -m venv .venv; fi
PY="$ROOT/.venv/bin/python"
"$PY" -m pip install --upgrade 'pip==26.0.1' 'setuptools==82.0.1' 'wheel==0.48.0'
"$PY" -m pip install 'torch==2.8.0' 'torchvision==0.23.0' 'torchaudio==2.8.0'
"$PY" -m pip install \
 'numpy==1.23.5' 'opencv-python==4.8.1.78' 'Cython==3.3.0' \
 'easydict==1.13' 'ffmpeg-python==0.2.0' 'future==1.0.0' \
 'fvcore==0.1.5.post20221221' 'gdown==5.2.2' 'iopath==0.1.10' \
 'joblib==1.5.3' 'matplotlib==3.9.4' 'ninja==1.13.2' \
 'pycocotools==2.0.11' 'PyYAML==6.0.3' 'scipy==1.10.1' \
 'six==1.17.0' 'terminaltables==3.1.10' 'tqdm==4.70.1' \
 'yacs==0.1.8' 'pytest-runner==6.0.1'
"$PY" -m pip install --no-build-isolation 'chumpy==0.70'
"$PY" -m pip install --no-build-isolation --no-deps --config-settings editable_mode=compat -e ./HybrIK
SRC="$ROOT/HybrIK/.cache/sources/pytorch3d"
mkdir -p "$(dirname "$SRC")"
if [[ ! -d "$SRC/.git" ]]; then git clone https://github.com/facebookresearch/pytorch3d.git "$SRC"; fi
git -C "$SRC" checkout 75ebeeaea0908c5527e7b1e305fbc7681382db47
PATCH="$ROOT/HybrIK/scripts/pytorch3d_cpu_bounds.patch"
if git -C "$SRC" apply --reverse --check "$PATCH" 2>/dev/null; then
 echo 'PyTorch3D CPU patch already applied'
else
 git -C "$SRC" apply --check "$PATCH"
 git -C "$SRC" apply "$PATCH"
fi
CC=clang CXX=clang++ MACOSX_DEPLOYMENT_TARGET=14.0 MAX_JOBS=4 \
 "$PY" -m pip install --no-build-isolation --no-deps "$SRC"
"$PY" - <<'PY'
import torch, pytorch3d, hybrik
from pytorch3d import _C
from hybrik.utils.presets import SimpleTransform3DSMPLCam
print('OK:', torch.__version__, pytorch3d.__file__, list(hybrik.__path__))
PY
printf '\nSetup complete. Run scripts/download_models.sh next.\n'
