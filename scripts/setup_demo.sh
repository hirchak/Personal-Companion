#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install --index-url https://pypi.org/simple -r requirements.lock
npm --prefix apps/web ci --registry=https://registry.npmjs.org
npm --prefix apps/web run build
