# M4 — local voice and editable ASR engineering report

Status: **AWAITING_REVIEW**, complete synthetic engineering candidate. No self-ACCEPT.
External M3 ACCEPT is durable in [review record](M3_ARCHITECT_REVIEW.md).
All29 owner sections are recorded in [goal](../prompts/M4_LOCAL_VOICE.md).

| Identity | Value |
|---|---|
| Base / prior main | `40b33a05248353b910acf733db99e21242ee0bd2` |
| Final implementation C | `021961c27a455dbc4c75710f7b700cff24c8017c` |
| Earlier local implementation | `747bb8450d9361b9d5c476f0a8aa2c6bf6b6bfed` |
| Evidence R | This evidence-only commit; resolve through Git/final owner handoff, no recursive self-hash |
| Branch | main |
| Publication checkpoint | PRE_PUSH at evidence creation; authorized normal fast-forward C/R push follows checks |
| CI | NOT_RUN, no CI PASS claimed for C or R |

Exact publication/remote SHA receipt is returned in the final user handoff after R exists. Verify
actual origin/main against that R. Published history preserved; no review branch, merge or deploy.

## Result

Working Ukrainian microphone flow: generated fake mic → PCM16/WAV capture/elapsed/pause/stop/cancel
→ actual durable encrypted phone save or private Mac save → resumable paired chunks/durable receipt
→ explicit disabled/fake/local-process ASR lifecycle → separate candidate/edit → explicit confirmed
journal note → selected retention. Existing journal/M3 are independent; no automatic provider/memory
job and no raw audio in AI context. Phone quota failure retains available memory draft; encrypted
rescue export/import and explicit discard/phone-only deletion work without a Mac receipt.

SQLite schema4 private attachments/recovery and backup format2 include final audio hashes/files.
Phone physical IDB3 adds encrypted audio/chunks, leaving journal format2 intact. Transfer:256 KiB,
8 MiB total, body400000 bytes,120s capture, canonical order, duplicate/retry/resume/checksums, revoke/
epoch and strict destination-free schemas. Late cancelled receipts are not applied automatically;
explicit Mac status reconciliation can reveal already finalized or remotely deleted audio. Prior
M1/M2/M3 migration/backup/crypto/sync/runtime behavior remains covered. No ASR download/build/install.

## Exact-C verification

[Full commands, environment, timestamps, durations and exit codes](evidence/M4/EXACT_C_CHECKS.json).
Clean final C `021961c27a455dbc4c75710f7b700cff24c8017c` was verified; every collector command exited0:

| Verification | Result |
|---|---|
| npm --prefix apps/web run build | PASS (TypeScript + Vite built React) |
| npm --prefix apps/web test | 23 PASS; all13 existing M2 tests retained,10 new M4 tests |
| .venv/bin/python -m pytest -q | 257 PASS, including18 real-browser cases (8 new M4); one dependency deprecation warning |
| .venv/bin/python -m scripts.measure_m4 --output generated/m4-performance.json | PASS, synthetic local loopback/fake overhead only |
| python3 scripts/check_docs.py | PASS |
| python3 scripts/build_chatgpt_context.py | PASS, public canonical snapshot regenerated |
| python3 scripts/check_privacy.py --include-generated | PASS, all local Git objects including staged/unreachable, public worktree/generated context/built UI |
| git diff --check | PASS |

Environment: Python3.13.2, Nodev26.8.2, npm11.19.1, Darwin27.0.0 arm64, existing project-local
Chromium/Playwright1.55.0. Fake media WAV is programmatically generated in disposable temp roots;
no real voice, engine/model or live provider. [UI review](evidence/M4/UI_INSPECTION.json) documents
three individually inspected synthetic screenshots, desktop/mobile/keyboard/44px/no-overflow checks.

[M4-A01…A13 matrix](evidence/M4/ACCEPTANCE_MATRIX.json): PASS in synthetic scope, using actual
SQLite/filesystem, native WebCrypto/IDB, built React and actual fake-microphone Chromium, plus trusted
process fixture success/failure/timeout/cancel/process-group/output/path/tool tests. These are test
results, not external architect ACCEPT, Android acceptance or OS isolation proof.

## Synthetic measurements

[Loopback/worker/file/DB/idle metrics](evidence/M4/SYNTHETIC_LOCAL_PERFORMANCE.json),
[actual browser encryption/write metrics](evidence/M4/SYNTHETIC_BROWSER_CRYPTO_IDB.json).
One generated19s tone /608044 bytes: upload13.702ms, individual chunks5.467/4.943/3.275ms,
finalize checksum/PCM/fsync/DB17.008ms, fake-ASR lifecycle15.895ms (worker4.835ms).
Audio file608044 bytes; logical voice metadata2079 UTF-8 bytes; preallocated DB stayed172032 bytes.
Browser AES-GCM and atomic IDB timings are recorded separately. Idle observation0.401s consumed
0.000578 process CPU seconds; harness peak RSS93372416 bytes. No matched old-version idle baseline
comparison, actual-model latency, human UA accuracy, Galaxy performance or cloud/token/cost claim.
These single harness measurements are descriptive, not throughput or idle regression guarantees.

## Privacy and gates

Public-data scan PASS. Retained screenshots show only synthetic fixture/product UI; no raw audio,
weights, DB/IDB dumps, auth, private endpoint or real-user material committed. Audio remains classified
PRIVATE_PERSONAL even in tests. Source/material rights: programmatically generated tones/noise and
project test text/UI; no private research/recording ingestion. R01/R02/R03 RAW and R04 clinical content
not opened/activated. Scan is heuristic plus deliberate artifact inspection, not an absolute guarantee.

- M4-A14: **LOCAL_ASR_BACKEND_NOT_RUN**. REAL_LOCAL_ASR_MODEL = NOT_RUN / PERMISSION_REQUIRED.
  Actual speech model executed: **NO**. Actual engine/model/version/hash: none verified/executed.
  Deterministic fake ASR and hash-pinned trusted Python fixture only; same-user CLI is not an OS sandbox.
- Ukrainian speech-model benchmark/WER/CER: **NOT_RUN**; HUMAN_UA_QUALITY **NOT_RUN**.
  Tone/noise/silence test pipeline behavior; they cannot prove human speech accuracy.
- M4-A15: Galaxy S24 Ultra **HARDWARE_UNVERIFIED / NOT_RUN**; private transport rollout remains NOT_RUN.
- Live OpenAI/Codex/MiniMax/cloud ASR/provider calls OFF/NOT_RUN; clinical, Health, real private data,
  system installs/trust/Tailscale/LAN/deploy and M5+ OFF/NOT_STARTED.

[Local-ASR follow-up](../docs/M4_LOCAL_ASR_RUNBOOK.md): named pinned engine and multilingual model
source/license/hash, owner-scoped download/project-local build and offline benchmark permission,
inspected actual argv and validated filesystem/egress gate. No guessed model-size/performance values.
[Galaxy microphone gate](../docs/M4_ANDROID_MIC_GATE.md) requires separately authorized secure
private-origin rollout and actual synthetic phone run. These deferred gates do not block the synthetic
engineering foundation. Historical receipt blocker is [resolved](M4_BLOCKER_REPORT.md).

## Demo and reproduction

```bash
./scripts/m4_demo.sh /private/tmp/personal-companion-m4-synthetic-demo
npm --prefix apps/web run build
.venv/bin/python -m pytest -q tests/test_m4_browser.py
```

Demo is loopback only: Mac `/`, synthetic phone `/phone/`, code from terminal for Mac unlock.
Use only generated/test media in this scope. Open «Голосовий запис» near the heading; save/reopen,
pair/upload from phone, explicitly enable synthetic fake ASR, edit/save edit/confirm and choose retention.
The pytest command generates fake microphone WAV and disposable profiles automatically, without real
microphone input. Actual recognition requires its separate gate; no cloud fallback. Browser eviction,
in-memory crash loss, non-guaranteed background recording, OS encryption/isolation and non-forensic
retention/remote erasure limits remain explicit. Next: independent review of pushed C/R; no M5.
