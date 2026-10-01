#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
M4_DEMO_ROOT="${1:-/private/tmp/personal-companion-m4-synthetic-demo}"
exec ./scripts/m2_demo.sh "$M4_DEMO_ROOT"
