#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
M2_DEMO_ROOT="${1:-/private/tmp/personal-companion-m2-synthetic-demo}"
if [ ! -e "$M2_DEMO_ROOT" ]; then
 .venv/bin/python -m apps.core.cli init --root "$M2_DEMO_ROOT" --seed
fi
exec .venv/bin/python -m apps.core.cli serve --root "$M2_DEMO_ROOT" --port 8765 --mode m2-synthetic
