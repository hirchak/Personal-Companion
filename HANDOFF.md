# M4 — implemented, preparing final C verification

Base/main 40b33a05248353b910acf733db99e21242ee0bd2, initial clean worktree. All 29 owner sections
received in prompts/M4_LOCAL_VOICE.md; historical specification blocker reports/M4_BLOCKER_REPORT.md
resolved. M3 external synthetic ACCEPT: reports/M3_ARCHITECT_REVIEW.md. M4 not self-accepted.

Implemented schema4 private attachment store/recovery and format2 audio-aware backup, strict paired
256 KiB chunk transfer (8 MiB/body400k/120s bounds), physical phone IDB3 encrypted separate chunks,
PCM16/WAV 16kHz mic capture, interrupted recording handling, quota rescue export/import, disabled/
fake/local-process ASR, candidate/edit/persistent explicit confirm/cancel/retry and retention.
No raw audio in M3 context or automatic AI work. Contract docs/M4_CONTRACT.md and ADR/runbooks ready.
Pre-final full suite257 Python (18 browser) PASS, web21/build PASS; latest changed tests still pending.

Next: review exact implementation, final C, run scripts/verify_m4.py on clean C, fix/re-C if needed,
write final report/state/handoff/devlog/evidence-only R, scan C→R and privacy, authorized normal
fast-forward origin/main push, verify R receipt and stop. No review branch or history rewrite.
No cloud/provider/system installs/model downloads/private data/rollout/clinical/Health/M5+.
Actual ASR/model/human UA NOT_RUN; Galaxy S24 Ultra HARDWARE_UNVERIFIED/NOT_RUN. Follow-up runbooks
record needed scoped permission; ffmpeg was only inspected, never assumed as runtime dependency.
Demo: ./scripts/m4_demo.sh /private/tmp/personal-companion-m4-synthetic-demo; loopback Mac /, phone /phone/.
