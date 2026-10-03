#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
npm --prefix apps/web run build
M7A_DEMO_ROOT="${1:-/private/tmp/personal-companion-m7a-synthetic-demo}"
if [[ ! -d "$M7A_DEMO_ROOT" ]]; then .venv/bin/python -m apps.core.cli init --root "$M7A_DEMO_ROOT" --seed; fi
.venv/bin/python - "$M7A_DEMO_ROOT" <<'PY'
import sys
from pathlib import Path
from apps.core.storage import Store, MARKER
import json
s=Store(Path(sys.argv[1]))
if json.loads((s.root/'synthetic.json').read_text())!=MARKER:raise SystemExit('SYNTHETIC_ROOT_REQUIRED')
print('Synthetic practices explicitly ON; open «Практики». Cloud/providers/phone not required.',flush=True)
PY
exec .venv/bin/python -m apps.core.cli serve --mode m2-synthetic --synthetic-practices --root "$M7A_DEMO_ROOT"
