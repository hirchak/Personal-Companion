# M8D C1/R1 — independent review FIX_REQUIRED

Independent review 2026-10-05 found M8D-R01 exact preview ordering/binding BLOCKING and M8D-R02 durable
settings-confirmation evidence REQUIRED correction. C1 results below are historical, not an accepted
private activation gate. See [review](M8D_ARCHITECT_REVIEW.md) and [forward fix report](M8D_REVIEW_FIX_REPORT.md).
Historical native4/4 samples stay bound to C1; no new inference is authorized or attributed to C2.

Base: `cee41e3a7638cf7efba511e93157ff5c3eb47ce7`. Implementation C: `d0b24846ced133864c45dc0b0eb71a1b01f0e947`. Evidence R is the evidence-only successor containing this final report;
its exact SHA is externally verified/returned after commit, without recursive self-hash.
Actual origin/main matched base immediately before C; normal FF publication is recorded below. External M8C ACCEPT/owner core activation are durable.
Real owner vault/operator terminal NOT TOUCHED; actual private AI/voice activation NOT_STARTED.

Implemented a distinct manifest-bound MAC_PRIVATE_AI_VOICE_PILOT_V1 profile, PRIVATE_LOCAL-only typed requests,
seven exact session acknowledgements/settings confirmations, separate local-voice gate, one neutral controller,
exact per-send current/history/goal/focus/map/journal preview, source/profile/draft/revision binding and defaultOFF
on lock/restart/restore. Journal selection defaultOFF/up to10 explicit revisions; no vault crawl, hidden Free-chat
retrieval, memory promotion or automatic journal writes. Personal records remain synthetic=false/PRIVATE_PERSONAL.

Final owner binding supersedes all earlier instructions: FREE Luna/high; explicit DEEP economical Luna/max or
quality Sol6.1/high. Luna ceilingMAX, Sol6.1 ceilingHIGH. Four NEW native attempts total across checkpoints;
failures/cancel/retries count, successful requests are not repeated. Native attempts consumed before final binding0,
Sol aboveHigh/max-ultra attempts before binding0. Final engineering ledger4/max4: four COMPLETED, failures0/cancel0/retry0. No further native attempts authorized.
No fallback/PAYG/credits purchase/new auth/billing/account route. TRAINING_CONTROL_CONFIRMATION = REQUIRED_AT_REAL_ACTIVATION / NOT_YET_CONFIRMED_TO_ARCHITECT.
CODEX_ENVIRONMENTS_CONFIRMATION = REQUIRED_AT_REAL_ACTIVATION / NOT_YET_CONFIRMED_TO_ARCHITECT.
No private account/settings inspection or zero-retention certification.

Private native client: read-only SDK auth reference, disposable state, installed public model catalog using supported
model_catalog_json/model-list; catalog support alone is not completed inference entitlement. Main deny-egress;
native process only owned loopback tunnel; separate isolated helper allows only CONNECT chatgpt.com:443 and relays
opaque end-to-end TLS, no payload logging/persistence/decryption. No vault/app-data filesystem authority or tools/
MCP/apps/plugins/browser/shell. Protected-volume/0700 temporary state gate precedes private text/audio writes.
[ADR-014](../docs/adr/ADR-014-M8D-OWNER-PRIVATE-AI-VOICE.md) carries boundaries and primary sources.

Pinned existing CPU whisper.cpp1.9.4-dev/small multilingual, exact model/binary hashes; no new assets/install/cloud.
Native synthetic Lesya TTS Chromium path verified through record/stop/local ASR/review/edit/insert/preview/manual
send, with fixture AI response. Actual human UA NOT_RUN/OPEN_HUMAN_TEST; owner five-utterance post-ACCEPT procedure
in [PILOT_HANDOFF](../docs/PILOT_HANDOFF.md). No real microphone/private audio/Health/phone data.

Private release format4/M8D, same schema11/core identity/at-rest/backup policy; old release formats remain supported.
Selectable real loopback lifecycle port leaves the current core app running. Protected backup binds exact producer/
source; source-fixture M8C→M8D upgrade/restart/restore/fresh-root M8C rollback/restart/uninstall KEEP DATA/exact-delete
rehearsal passes. Old M8C manager cannot validate a new M8D producer manifest; compatible pre-upgrade recovery uses
M8D manager or an M8C-produced backup. No compatibility claim for post-AI schema2 inference records on old M8C.

Exact-C checks on Darwin/arm64/Python3.13.2/Node26.8.2/Codex0.159.0, existing dependencies only:

| Check | Command | Result |
|---|---|---|
| Python | `.venv/bin/python -m pytest -q` | exit0, 780 PASS |
| Web | `npm --prefix apps/web test` | exit0, 50 PASS |
| Exact package/build | `.venv/bin/python -m apps.core.release prepare --output generated/releases/M8D-d0b24846ced133864c45dc0b0eb71a1b01f0e947` | exit0 |
| Chromium + native ASR | `.venv/bin/python -m scripts.verify_m8d_browser --package generated/releases/M8D-d0b24846ced133864c45dc0b0eb71a1b01f0e947` | exit0, fixture inference, nonloopback0/page-errors0 |
| Actual Mac lifecycle | `.venv/bin/python -m scripts.verify_m8d --package generated/releases/M8D-d0b24846ced133864c45dc0b0eb71a1b01f0e947 --previous-package generated/releases/M8C-a00a14277974b7f6c25846d0eb7a23879f86183a` | exit0 |
| Native private synthetic integration | `.venv/bin/python -m scripts.evaluate_m8d_private --package generated/releases/M8D-d0b24846ced133864c45dc0b0eb71a1b01f0e947` | exit0, four completed requests |
| Privacy | `.venv/bin/python scripts/check_privacy.py --include-generated` | PASS, all local objects/worktree/snapshots/UI; repeated before/after R |
| Docs/context | `check_docs.py` / `build_chatgpt_context.py` | PASS |

Release: `M8D-d0b24846ced133864c45dc0b0eb71a1b01f0e947`. Manifest `4dcef73b066f3adf7c969baedb9d76b39d7885e58967c44c90e8cd986a57a866`. Runtime lock `f17abf6ca517eaa32131af3ed3f21690a6ea5f2c6a2481a10a518b3dfcc54b6e`.
Unsigned local engineering package; no tag, GitHub Release, deploy, signing/notarization or autostart.
Source-fixture pre-C rehearsals are separate; only exact-C artifacts below support the delivered release.
Impeccable detector: one pre-existing unrelated style warning, no introduced private-controls warning.

| Native case | Model / effort | State | Seconds |
|---|---|---|---|
| FREE current + same-conversation continuity | gpt-6-luna / high | COMPLETED | 9.105 |
| DEEP agreed goal/focus/confirmed fixture takeaway/continuity | gpt-6-luna / max | COMPLETED | 61.910 |
| Comparable DEEP goal/focus/takeaway/continuity | gpt-6.1-sol / high | COMPLETED | 29.980 |
| Genuine local-ASR candidate → reviewed/edited text + selected journal → AI | gpt-6-luna / high | COMPLETED | 9.664 |

Both Deep requests returned valid source-bound working maps (4/3 items), respected formal-VY/no declared cause
and retained the explicit goal/focus. The same bounded scenario and explicit synthetic fixture takeaway were
used, not extra benchmarking or an LLM judge. One case/model is not a general quality or speed ranking;
the original synthetic candidate samples are independent human-review material. No automatic winner/fallback.
Fourth request combines both required integrations inside the ceiling: only exact approved edited text and one
journal revision, unselected sentinel absent, audio/hash/source descriptor absent from actual provider payload.
No max/ultra attempts preceded final binding; Sol aboveHigh0, Luna/max1 explicitly authorized.

Actual Mac: native private preflight PASS, verified protected APFS/FileVault data and backup volumes,
owner-only permissions/path/app-data separation/loopback/auth/lock/restart; application-level database/archive
encryption NOT_IMPLEMENTED. Temporary provider/ASR storage also requires protected volume before private writes.
Exact backup producer/source verified; M8C→M8D restart/restore/defaultOFF/fresh compatible M8C rollback/restart/
uninstall KEEP DATA/separate confirmed disposable deletion preserve journal revision and backups. No in-place
downgrade or actual owner-vault action. Fixture and exact-C disposable runtime containers cleaned.

Public evidence: [checks](evidence/M8D/CHECKS.json), [manifest](evidence/M8D/RELEASE_MANIFEST.json),
[Mac lifecycle](evidence/M8D/M8D_PRIVATE_LIFECYCLE.json), [Chromium](evidence/M8D/CHROMIUM_PRIVATE_LOCAL.json),
[native samples/ledger](evidence/M8D/NATIVE_PRIVATE_CONVERSATION.json),
[final owner binding](evidence/M8D/OWNER_COST_BINDING.json), [privacy scan](evidence/M8D/PRIVACY_PUBLIC_TREE.json). Screenshots contain ORIGINAL SYNTHETIC text only.

Clinical0/all five specialistsOFF/27findingsOPEN; Health/phone/embeddings/cloudASR/sync/telemetry/publicationOFF/NONE.
M7D-N02 OPEN_HUMAN_LANGUAGE_REVIEW; M7C-N03 OPEN_HUMAN_TEST; M6-N01 final0.6.1 hardware NOT_RUN.
M7C-N02 = READY_FOR_THIS_OWNER_BOUNDED_PILOT_ONLY_AFTER_M8D_ACCEPT; universal/third-party/zero-retention gate remains OPEN.
MAC core readiness/started owner core pilot stays independently accepted M8C. M8D does not execute optional activation.

Review status after delivery: AWAITING_REVIEW. No tag/GitHub Release/deploy/force/history rewrite/next milestone.


| Independent readiness | Result |
|---|---|
| PRIVATE_AI_ENGINEERING | READY |
| LOCAL_VOICE_ENGINEERING | READY |
| PRIVATE_AI_PROVIDER_ROUTE | READY_FOR_OWNER_BOUNDED_PILOT_AFTER_M8D_ACCEPT |
| PRIVATE_VAULT_CONTEXT | EXPLICIT_SELECTION_ONLY |
| RAW_AUDIO_TO_PROVIDER | NEVER |
| ACTIVATION_PROCEDURE | READY, NOT EXECUTED |
| M7C-N03 | OPEN_HUMAN_TEST / actual human UA NOT_RUN |
| M7D-N02 | OPEN_HUMAN_LANGUAGE_REVIEW |
| CLINICAL / Health | OFF / OFF |
| PHONE | NEEDS_TRANSPORT_GATE |
| ACTUAL_PRIVATE_AI_ACTIVATION | NOT_STARTED |
| Real private data / real human audio / system changes | 0 / 0 / 0 |

Post-ACCEPT procedure in PILOT_HANDOFF upgrades the existing vault's application without recreating/importing
or migrating real data during M8D. Fresh preflight, exact accepted release, local owner acknowledgements,
explicit profile and reviewed per-send preview remain mandatory. Current accepted M8C core continues unchanged.
Publication: C + evidence-only R normal FF main, origin/main must equal R; CI status is separately reported
from the exact GitHub run. No self-accept, further provider attempt, real AI/voice activation or next milestone.
