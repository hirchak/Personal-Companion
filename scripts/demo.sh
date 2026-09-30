#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
DEMO_ROOT="${1:-/private/tmp/personal-companion-m1-synthetic-demo}"
if [ ! -e "$DEMO_ROOT" ]; then
  .venv/bin/python -m apps.core.cli init --root "$DEMO_ROOT" --seed
fi
exec .venv/bin/python -m apps.core.cli serve --root "$DEMO_ROOT" --port 8765
