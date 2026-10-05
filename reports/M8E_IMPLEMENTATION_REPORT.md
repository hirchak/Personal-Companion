# M8E — Conversation-first mobile UX + seamless local voice — AWAITING_REVIEW

Base/origin before implementation: `49d03d97d444083a63d18f3f3ec9ec8d295c19fd`; clean `main` independently verified.
Final implementation C: `c571c41e59d9f53d96480d1fc20e2cce60a54936`. Forward development checkpoints
`1438c03b93a5f9db0c32a0c458dbc72a76466dce`, `168d5acf6577e74f97fad995575d970c16e59925` and `84d64871eebd8ba10aaf0267e9a827f673afa95d` remain in history.
R is the evidence-only successor containing this report; its SHA and verified pushed origin/main are returned
externally after commit/publication, avoiding a recursive self-hash. Owner authorizes normal FF direct-main push;
no merge/tag/Release/deploy/owner-vault upgrade. CI NOT_RUN: no repository workflow found.

Authority: [complete owner goal](../prompts/M8E_CONVERSATION_FIRST_MOBILE_VOICE.md),
[contract](../docs/M8E_CONTRACT.md), [ADR-015](../docs/adr/ADR-015-M8E-CONSENT-AND-CONVERSATION-UX.md).
M8D exact C2/R2 external ACCEPT remains authoritative; its historical reports/evidence are preserved.

## Forward activation history correction

Owner now clarifies FIRST_REAL_PRIVATE_AI_TEST occurred before independent external account-setting verification.
Prior M8D activation/contract/review statements implying those controls had been confirmed OFF before that first
test are inaccurate and superseded here; historical commits/evidence are not rewritten.
TRAINING_CONTROL_CONFIRMATION = NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER.
CODEX_ENVIRONMENTS_CONFIRMATION = NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER.
No account/settings inspection or retroactive training-off claim. Owner reports a manual Ukrainian microphone →
local-whisper exercise; HUMAN_UA_ASR = PARTIAL_OWNER_PILOT / OPEN, not formal human quality acceptance.

## Product and binding

Default optional PRIVATE_LOCAL landing is Conversation. Four primary actions: Розмова / Щоденник / Творчість /
Більше. Paper/ink/sage identity, mobile bottom navigation/safe area, viewport-aware anchored composer and
independent thread scroll. Desktop history rail/mobile drawer, local first-message title, new/reopen/archive/delete.
Core-only M8C profile keeps its permitted journal landing; private phone routes remain denied.
Free requires no goal and resumes only its own bounded history. Deep selects/creates an agreed goal, resumes
exact pinned session/focus/map, offers prior local topics, pause/closure and explicit material scope renewal.
No unrelated Free retrieval, journal default inclusion or automatic memory promotion. Model choice is separate:
Free Luna/High; Deep economical Luna/Max or quality Sol6.1/High, correctly reflected in compact status.
Luna≤Max/Sol≤High; no fallback/PAYG. Historical assistant messages remain visible with AI OFF.

One onboarding sheet + explicit acceptance creates versioned local SQLite consent, bound to privacy/destination/
profiles/vault/restore epoch. Restart/unlock preserve acceptance; runtime resumes only after authentication.
Disable persists AI OFF; revoke clears consent/scopes and cancels jobs. Restore/material contract change requires
new acceptance. Local voice can be enabled independently. Local audio history/delete/text edits remain usable
after AI revoke. External Data Controls reminder is owner-controlled, never automatically certified by this app.
Legacy seven-checkbox API is session-only compatibility; the primary UI has no repeated checkbox flow.

Ordinary Send requires no popup: explicit Send authorizes current text inside accepted bounded scope; backend
constructs/freezes the canonical exact M8D payload/receipt and verifies source/profile/draft/skills/map hashes
before queue/run/commit. Optional exact inspection remains. Extra journals (≤10 exact revisions) require explicit
selection + contextual approval. Stale journal rejection is visible inside the sheet, preserves the draft, and
requires refreshed sources/new approval before fixture dispatch. Deep scope changes similarly fail closed.
No additional journal field is accepted by standard send. Exact source aliases, authority and canonical ordering
remain; payload inspection does not become provider authority or automatic journal/memory promotion.

## Voice/offline

Composer mic → original recording indicator/duration/Cancel/Finish → durable local PCM16 WAV → automatic approved
local whisper → editable composer draft → explicit Send. No automatic AI send or save/insert ceremony. Send saves
reviewed transcript revision and exact edited text before source-bound dispatch. Provider payload contains no
raw audio/audio hash/voice descriptor. Existing M4 Mac staging/fsync/receipts/recovery/retention remains authority.
Unavailable/failed ASR preserves audio; Voice History shows time/duration/state/text, retry/use/delete after reload.
Browser capture before persistence and failed Mac persistence stay visibly non-durable, with retry/unload warning;
no browser-crash/background/secure-erasure guarantee is invented.

Phone offline simulation uses existing encrypted PWA IndexedDB audio/chunks and LOCAL_AUDIO_SAVED queue,
presented as waiting for local ASR/private Mac transport. Recording/reload/deletion work with unavailable Mac;
internet availability never grants audio upload. Existing upload refuses absent pairing/repair before any request.
No new storage stack, public audio cloud, cloud ASR, Vercel private vault, pairing/Tailscale/certificates or real
phone transport. Offline Chromium uses the existing synthetic loopback PWA harness; PRIVATE_LOCAL phone remains
OFF. PHONE_TRANSPORT = NOT_ACTIVATED / NEEDS_TRANSPORT_GATE; no Galaxy/hardware/keyboard PASS is claimed.

## Validation

| Final exact-C check | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | exit0, 800 PASS |
| `npm --prefix apps/web test` | exit0, 51 PASS |
| `python -m apps.core.release prepare` (full command in CHECKS.json) | exit0, exact-C build |
| `python -m scripts.verify_m8e_browser --package ...` | exit0, Chromium + native local ASR, fixture AI only |
| `python -m scripts.verify_m8d --package ... --previous-package ...` | exit0, protected synthetic Mac lifecycle |
| `scripts/check_docs.py`, `scripts/build_chatgpt_context.py`, `scripts/check_privacy.py --include-generated` | final publication checks, exit codes in DOCS_PRIVACY.json |


Environment: Darwin/arm64, Python3.13.2, Node26.8.2/npm11.19.1, CodexCLI0.159.0, existing Chromium/whisper assets.
Installed cached model catalog exposes gpt-6.1-sol/high; catalog is capability evidence, not new inference
entitlement or a claim about the sampled development model. No new dependencies/model download/system install.
First overlapping C1 verification runs hit timing deadlines (KDF/process/UI); they were stopped/repeated serially
without loosening timeouts/security rules. An isolated prior microphone quota case passed unchanged. Those interim
runs are not final-C PASS evidence. Final checks above bind the final C explicitly; fixture inference is not live.

Local unsigned compatibility package retains format4/M8D identifier with exact final C:
`M8D-c571c41e59d9f53d96480d1fc20e2cce60a54936`; manifest
`e738ade91d917fba60312685ffb92eb4614b53d3e35e206eae94c9e5b57e40f9`, schema11, runtime lock
`f17abf6ca517eaa32131af3ed3f21690a6ea5f2c6a2481a10a518b3dfcc54b6e`. No release/tag/deploy or real-vault install.
Bounded visual review covers synthetic desktop/390px empty/active/Deep/recording/transcribing/history/privacy;
390×540 viewport simulation and no horizontal overflow. Review fixed status overlap/Deep wrapping and the clipped empty Deep prompt; final
review confirms the result. One Impeccable detector run reported only pre-existing style.css border-top8px warning.
No proprietary assets or copied private conversation/audio. See [evidence](evidence/M8E/CHECKS.json).

Real owner vault inspected = NO; live provider calls = 0; native provider evaluation driver not run.
Historical public M8D native4/4 evidence remains unchanged; no extra native inference is attributed to this goal.
FileVault/owner-only/typed-root/auth/auto-lock/CSRF/Origin/Host/main deny-egress/provider isolation preserved.
Clinical0/all5specialistsOFF/HealthOFF/27findingsOPEN. Human/phone gates stay open. M8E AWAITING_REVIEW; STOP.
