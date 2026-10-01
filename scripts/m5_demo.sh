#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
M5_DEMO_ROOT="${1:-/private/tmp/personal-companion-m5-synthetic-demo}"
exec ./scripts/m2_demo.sh "$M5_DEMO_ROOT"
