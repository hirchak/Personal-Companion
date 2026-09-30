# M1 handoff — AWAITING_REVIEW

Owner goal: prompts/M1_LOCAL_JOURNAL.md. Synthetic only.
Base M1 R5: 175fc934ad16552759273d2ed6770835b6f28786.
Correction base R1: 56a29e8912b39bdb20687a4f8b6bf23824956607.
Final C: fd056cc4e91b826a032a871381dbf3a64180bd44. R2 next evidence-only commit; exact R/remote receipt in final handoff.
Standing push_main=true; this file PRE_PUSH. M0 external ACCEPT C3 preserved. CI NOT_RUN.

Full SQLite/API/Ukrainian UI/export/backup/restore remains in M1. Completion audit fixes
revision recorded_at_utc and generated read/history/receipt schemas, expands TCP/UDP/DNS
network guard, verifies TZ/event editing, keyboard and documented setup/launcher/restart/stop.
Legacy synthetic history has null recording time, never a fabricated historical value.
Exact final C clean source build + 104 tests/docs/privacy PASS. No code changes after final C.
Evidence/report: reports/M1_LOCAL_JOURNAL_REPORT.md, reports/evidence/M1/EXACT_FINAL_C_CHECKS.json,
reports/evidence/M1/COMPLETION_AUDIT.json. No implementation blocker; independent review pending.

Launch: ./scripts/setup_demo.sh, then
./scripts/demo.sh /private/tmp/personal-companion-m1-synthetic-demo.
Open http://127.0.0.1:8765; terminal one-time code, stop Ctrl+C.
Unknown root refused; no reseed on restart. Lock/reload clears unsaved text; save failure
keeps memory draft. Runbook: docs/INSTALLATION.md; contract v4 docs/M1_CONTRACT.md.

AI/deploy/private vault/M2+/phone/clinical/watch/ASR/game/autostart/release OFF.
Galaxy Watch7 metadata only, compatibility NOT_VERIFIED. Research DOCX not opened/ingested.
Next: architect review published C/R2; fixes forward only, new milestone requires owner goal.
