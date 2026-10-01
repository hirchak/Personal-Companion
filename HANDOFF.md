# M2 handoff — AWAITING_REVIEW

Base main/M1 R b4c8af5f975e1a92c6d06fd023b82155cae6fc73.
Final C 67cb03969d344fe37f45f1d97d021405bea6b126; R next evidence-only commit, exact R/remote
receipt final message (PRE_PUSH here). M1 external ACCEPT recorded, last_reviewed_sha=M1 C.
Goal prompts/M2_OFFLINE_PWA_SYNC.md; contract docs/M2_CONTRACT.md; report reports/M2_OFFLINE_PWA_SYNC_REPORT.md.

Encrypted IDB/PWA/outbox/foreground sync, scoped pairing/revoke, conflicts as new revision
mutations, tombstones/restore epoch/re-pair, safe updates, pressure/eviction/recovery implemented.
One Journal domain shared transaction. MAC schema2 migration, no real vault touched.
Exact C clean source: 120 Python + 11 crypto/store tests and full build/browser/docs/privacy PASS.
No runtime payload/credential/API cache or plaintext durable key. No OS/hardware security claim.

Actual Galaxy S24 Ultra route/Chrome/install/wake/Keystore HARDWARE_UNVERIFIED/NOT_RUN;
ADR-002 private Serve/MagicDNS HTTPS candidate needs separate route/client/account permissions.
No cert trust/router/tunnel/remote activation/deploy/accounts/paid/provider calls. AI/health/voice/M3+ OFF.
M2-A01…A11 synthetic PASS; A12 NOT_RUN. CI NOT_RUN. Independent review remains pending.

Start: ./scripts/setup_demo.sh; ./scripts/m2_demo.sh /private/tmp/personal-companion-m2-synthetic-demo.
Open http://127.0.0.1:8765/ for Mac (terminal unlock), /phone/ for desktop PWA (local passphrase).
Mac settings issue one-use invitation; stop Ctrl+C. /phone/ localhost is not a Galaxy-to-Mac route.
Synthetic browser suite: .venv/bin/python -m pytest tests/test_m2_browser.py tests/test_m2_ui.py -q.
Manual Android/recovery/transport runbooks and caveats in docs/M2_ANDROID_GATE.md and INSTALLATION.
Next: architect review exact pushed C/R, forward fixes only. No next milestone without owner goal.
