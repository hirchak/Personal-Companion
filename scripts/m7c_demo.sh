#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
M7C_DEMO_ROOT="${1:?Use a fresh dedicated synthetic root}"
M7C_ROUTE="${2:-OFF}"
M7C_MODEL="${3:-gpt-6-luna}"
case "$M7C_ROUTE" in OFF|CODEX_SUBSCRIPTION) ;; *) echo 'UNVERIFIED_PROVIDER_ROUTE'; exit 1;; esac
if [[ -e "$M7C_DEMO_ROOT" ]]; then echo 'M7C_DEMO_REQUIRES_FRESH_ROOT'; exit 1; fi
npm --prefix apps/web run build
.venv/bin/python -m apps.core.cli init --root "$M7C_DEMO_ROOT" --seed
.venv/bin/python - "$M7C_DEMO_ROOT" <<'PY'
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
print('Only original synthetic data. Goal/history seeded. Provider selection explicit; ledger max100 across runs.',flush=True)
PY
M7C_ASR_ARGS=()
if [[ "${M7C_LOCAL_ASR:-0}" == 1 ]]; then M7C_ASR_ARGS=(--local-asr); fi
exec .venv/bin/python -m apps.core.cli serve --root "$M7C_DEMO_ROOT" --m7c-synthetic --synthetic-practices --conversation-provider "$M7C_ROUTE" --conversation-model "$M7C_MODEL" "${M7C_ASR_ARGS[@]}"
