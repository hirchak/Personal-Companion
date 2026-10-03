#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
npm --prefix apps/web run build
M7B_DEMO_ROOT="${1:-/private/tmp/personal-companion-m7b-synthetic-demo}"
if [[ ! -d "$M7B_DEMO_ROOT" ]]; then .venv/bin/python -m apps.core.cli init --root "$M7B_DEMO_ROOT" --seed; fi
.venv/bin/python - "$M7B_DEMO_ROOT" <<'PY'
import sys
from pathlib import Path
from uuid import UUID
from apps.core.storage import Store,MARKER
from apps.core.conversation import Conversations
from apps.core.conversation_contracts import NewConversation,SendMessage
import json
store=Store(Path(sys.argv[1]))
if json.loads((store.root/'synthetic.json').read_text())!=MARKER:raise SystemExit('SYNTHETIC_ROOT_REQUIRED')
service=Conversations(store,synthetic_demo=True)
if not service.list()['items']:
 c=service.create(NewConversation(operation_id=UUID(int=701)))
 service.send(c['conversation']['id'],SendMessage(operation_id=UUID(int=702),base_revision=1,text='SYNTHETIC · Хочу перевірити цей простір на вигаданому прикладі.'))
print('Synthetic conversation/mock and M7A neutral practice explicitly enabled; no provider/phone required.',flush=True)
PY
exec .venv/bin/python -m apps.core.cli serve --mode m2-synthetic --synthetic-practices --synthetic-conversations --root "$M7B_DEMO_ROOT"
