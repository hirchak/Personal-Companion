#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
M6_DEMO_ROOT="${1:-/private/tmp/personal-companion-m6-synthetic-demo}"
if [[ ! -d "$M6_DEMO_ROOT" ]]; then .venv/bin/python -m apps.core.cli init --root "$M6_DEMO_ROOT" --seed; fi
.venv/bin/python - "$M6_DEMO_ROOT" <<'PY'
import sys
from pathlib import Path
from uuid import UUID
sys.path.insert(0,'tests')
from m6_fixtures import batch,record
from apps.core.storage import Store,MARKER
from apps.core.health import HealthImport
import json
root=Path(sys.argv[1])
if json.loads((root/'synthetic.json').read_text())!=MARKER:raise SystemExit('SYNTHETIC_ROOT_REQUIRED')
h=HealthImport(Store(root))
if not h.records():h.apply(batch(record('sleep'),record(),epoch=str(UUID(int=6))),reconnect=True)
print('SYNTHETIC Health Connect copy ready; open «Дані з годинника». No actual device needed.')
PY
exec .venv/bin/python -m apps.core.cli serve --mode m2-synthetic --root "$M6_DEMO_ROOT"
