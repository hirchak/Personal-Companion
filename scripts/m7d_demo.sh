#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
M7D_DEMO_ROOT="${1:?Use a fresh dedicated synthetic root}"
M7D_ROUTE="${2:-OFF}"
M7D_MODEL="${3:-gpt-6-luna}"
case "$M7D_ROUTE" in OFF|CODEX_SUBSCRIPTION) ;; *) echo 'UNVERIFIED_PROVIDER_ROUTE'; exit 1;; esac
if [[ -e "$M7D_DEMO_ROOT" ]]; then echo 'M7D_DEMO_REQUIRES_FRESH_ROOT'; exit 1; fi
npm --prefix apps/web run build
.venv/bin/python -m apps.core.cli init --root "$M7D_DEMO_ROOT" --seed
.venv/bin/python - "$M7D_DEMO_ROOT" <<'PY'
import sys
from pathlib import Path
from uuid import UUID
from apps.core.storage import Store
from apps.core.conversation import Conversations
from apps.core.conversation_contracts import NewConversation,SendMessage
from apps.core.reflection import Reflection
from apps.core.reflection_contracts import GoalCreate
c=Conversations(Store(Path(sys.argv[1])),True)
g=Reflection(c).create(GoalCreate(operation_id=UUID(int=70101),text='ORIGINAL SYNTHETIC · Вигаданий персонаж хоче зрозуміти, як спланувати паперовий сад без поспіху.',user_agreed=True))
p=c.create(NewConversation(operation_id=UUID(int=70102)))
c.send(p['conversation']['id'],SendMessage(operation_id=UUID(int=70103),base_revision=1,text='ORIGINAL SYNTHETIC · Вчора вигаданий персонаж мав дві ідеї паперового саду.'),respond=False)
print('Only original synthetic data. Goal/history seeded. Provider selection explicit; ledger max48 across runs.',flush=True)
PY
M7D_ASR_ARGS=()
if [[ "${M7D_LOCAL_ASR:-0}" == 1 ]]; then M7D_ASR_ARGS=(--local-asr); fi
exec .venv/bin/python -m apps.core.cli serve --root "$M7D_DEMO_ROOT" --m7d-synthetic --synthetic-practices --conversation-provider "$M7D_ROUTE" --conversation-model "$M7D_MODEL" --conversation-effort "${4:-max}" "${M7D_ASR_ARGS[@]}"
