#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/HybrIK/res_aidan_walking_85s_10s}"
"$ROOT/.venv/bin/python" - "$OUT/res.pk" <<'PY'
import pickle, sys
from pathlib import Path
p = Path(sys.argv[1])
with p.open('rb') as f: data = pickle.load(f)  # Trusted local inference output only.
for k,v in data.items(): print(k, getattr(v,'shape',type(v).__name__))
assert data['pred_xyz_29'].shape[1:] == (29,3)
print('Frame count:', data['pred_xyz_29'].shape[0])
PY
