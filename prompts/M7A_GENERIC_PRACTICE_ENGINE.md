M7A — GENERIC PRACTICE ENGINE, ADMISSION ENFORCEMENT & LOCAL DEMO UX

Repository:
https://github.com/hirchak/Personal-Companion.git

Current verified main/base:
9b3d8c7171920074fb9b755274d5879a0972c4ff

Reviewed M7_PREP:
C = 52f8691167239487b0689202d462a9035242ab16
R = 9b3d8c7171920074fb9b755274d5879a0972c4ff

External architect verdict:
M7_PREP_EVIDENCE_ADMISSION = ACCEPT for preparation/tooling scope.

M6 remains:
ACCEPT — engineering + bounded early hardware.
M6-N01 remains OPEN:
early actual hardware = 0.6.0-debug;
final 0.6.1-debug exact hardware smoke = NOT_RUN.

M7A is the first application/runtime implementation after M7_PREP.

It is NOT permission to activate researched clinical/self-help content.

==================================================
1. GOAL
==================================================

Build a real generic practice/session engine for Personal Companion.

The engine must support the mechanics needed by future reviewed self-help modules without
containing or activating those clinical modules yet.

Required end-to-end user flow:

practice catalog
→ admission check
→ start
→ step
→ user response / acknowledgement
→ next
→ pause
→ resume after application restart
→ skip optional step
→ stop at any moment
→ complete
→ session history / delete.

Deliver a real local UI and a synthetic demo module so the owner can run the application
and inspect the complete interaction flow now.

Real research-derived modules remain unavailable.

The important architectural property:

RESEARCH CANDIDATE
≠
RUNTIME-ADMITTED MODULE.

No clinical content becomes runnable merely because a research record exists.

==================================================
2. RECORD PREVIOUS REVIEW
==================================================

At start:

- fetch and verify actual origin/main;
- verify worktree clean;
- preserve published history;
- record external architect review for M7_PREP:

  ACCEPT — preparation/tooling scope

  C:
  52f8691167239487b0689202d462a9035242ab16

  R:
  9b3d8c7171920074fb9b755274d5879a0972c4ff

- M7_PREP does NOT mean content/rights/clinical approval;
- active clinical remains 0;
- all 27 research findings remain open unless separately resolved;
- activate only M7A.

Do not self-assign M7A ACCEPT.

==================================================
3. ARCHITECTURE PRINCIPLE
==================================================

M7A must be deterministic.

Do NOT build a general multi-agent framework.

Do NOT create an autonomous clinical orchestrator.

Do NOT let an LLM select practices, advance protocol steps, determine whether a module is
safe, reinterpret approvals or mutate session state.

M3 already provides bounded runtime/jobs/provider abstractions for future AI-assisted functions.

M7A uses:

deterministic application code
+
validated package definitions
+
explicit admission records
+
persistent state machine.

If coordination is required internally, implement it as an ordinary deterministic service/controller,
not as an AI agent.

Future live AI orchestration is a separate provider/runtime goal.

==================================================
4. M7_PREP ADMISSION LAYER IS AUTHORITATIVE
==================================================

Consume the canonical preparation layer:

research/admission/registry.json
research/admission/schemas/*
scripts/m7_admission.py

Do not silently duplicate its authority in another inconsistent table.

Preparation candidates remain candidates.

No existing module whose activation is OFF can be loaded as a production practice.

Runtime must fail closed if:

- module absent;
- version mismatch;
- content hash mismatch;
- approval missing/stale;
- rights binding absent where required;
- technical binding absent;
- source/claim dependency changed;
- runtime activation permission absent;
- schema unknown;
- admission registry invalid.

Do not implement a “continue anyway” button.

==================================================
5. CLOSE M7_PREP SCHEMA HARDENING NOTE
==================================================

The Python/Pydantic validator is currently authoritative and fail-closed.

Harden the standalone generated JSON Schemas so maps with constrained key namespaces
(for example claim/source binding maps) are also key-closed when validated independently.

Unknown keys must not be accepted merely because patternProperties exists.

Add explicit standalone JSON-schema negative tests.

Do not weaken the Python validator.

This is mechanical hardening only, not a change in research/content statuses.

==================================================
6. RUNTIME ACTIVATION MODEL
==================================================

Do NOT relax the canonical preparation registry simply to make the demo run.

Design a separate explicit runtime-admission / activation receipt boundary.

A future real production module must require logical equivalents of:

- module ID;
- exact module version;
- exact package/content hash;
- exact admission/approval identity;
- technical implementation SHA/evidence;
- review scope;
- owner activation decision;
- activation version/epoch;
- created_at;
- optional expiry/re-review state.

Exact architecture/names are your choice.

No real clinical activation receipt exists in M7A.

Therefore production clinical runnable count must remain:

0.

==================================================
7. SYNTHETIC DEMO MODE
==================================================

Provide a synthetic-only demo mechanism for engineering and UX testing.

The demo package must:

- contain no copied therapeutic script;
- contain no clinical questionnaire;
- contain no treatment instructions;
- contain no research text presented as therapy;
- contain no medical claims.

Use an invented neutral interaction, for example a generic UI walkthrough / reflection fixture.

Example semantics only:

Step 1:
“Це тестова практика. Перейдіть далі.”

Step 2:
“Напишіть будь-який тестовий текст.”

Step 3:
optional choice.

Step 4:
completion.

Create better neutral fixture wording if appropriate.

Clearly display:
“Синтетична демо-практика”
or equivalent.

Synthetic packages must exist in a separate namespace/path and must NEVER be mistaken for a
reviewed production module.

Synthetic execution is allowed only under an explicit synthetic/demo configuration and synthetic
data root.

Starting the normal application must not automatically expose synthetic fixtures as real practices.

Test that a synthetic flag/data-root combination cannot activate a real OFF module.

==================================================
8. PRACTICE PACKAGE FORMAT
==================================================

Create a strict versioned package format.

It may be JSON/YAML/Markdown + manifest or another safe representation.

At minimum it should express:

- package schema version;
- module ID;
- module version;
- content hash;
- title/short description;
- step IDs;
- deterministic order;
- bounded supported interaction type;
- optional/non-optional step;
- final completion state;
- provenance/admission reference.

Allowed interaction primitives should be deliberately small.

Examples:

- information/static local text;
- acknowledgement;
- short text;
- long text;
- explicit single choice;
- optional skip.

Do not create arbitrary executable expressions.

Do not support:

- JavaScript/code;
- Python;
- shell;
- SQL;
- arbitrary HTTP;
- arbitrary filesystem paths;
- provider calls;
- hidden tools;
- embedded action commands;
- dynamic imports;
- arbitrary templating evaluation.

Package text is data.

==================================================
9. BRANCHING
==================================================

M7A does not need a general workflow language.

Prefer linear deterministic steps.

If a small branch mechanism is genuinely useful, only allow explicit validated choices pointing to
declared step IDs within the same exact package.

No arbitrary conditions.

No eval.

No LLM decision.

No user-text-as-code behavior.

Reject loops unless they are explicitly bounded by schema.

An invalid cycle fails package admission.

==================================================
10. SESSION STATE MACHINE
==================================================

Implement a durable explicit state machine.

Logical states may include:

NOT_STARTED
ACTIVE
PAUSED
COMPLETED
STOPPED
BLOCKED_BY_ADMISSION
DELETED

Equivalent names are fine.

Transitions must be validated.

Examples:

START → ACTIVE

ACTIVE → PAUSED
ACTIVE → COMPLETED
ACTIVE → STOPPED

PAUSED → ACTIVE

Any runnable state → BLOCKED_BY_ADMISSION
when the exact admission/version is no longer valid before a new transition.

No impossible transition may silently succeed.

No COMPLETED → ACTIVE mutation.

Starting again creates a new session.

==================================================
11. USER AGENCY
==================================================

At every meaningful point provide:

- pause;
- stop;
- leave;
- skip where the step is optional.

A user must never be forced to finish a practice to regain normal journal functionality.

Stopping is a valid successful user decision.

Do not display:

- failure for stopping;
- broken streak;
- lost points;
- guilt messaging;
- “you gave up”;
- “finish this for your wellbeing”.

No penalty.

No reward tied to completion.

No game progression based on completing practices in M7A.

==================================================
12. SESSION DATA MODEL
==================================================

Persist enough information to reproduce the exact state.

At minimum logical equivalents:

- session ID;
- module ID;
- module version;
- exact package/content hash;
- admission/activation binding;
- started UTC;
- updated UTC;
- current step ID;
- state;
- revision/CAS;
- responses by step;
- skipped steps;
- completed/stopped time;
- package schema version;
- provenance;
- optional explicit stop reason chosen by user, if implemented.

Do not persist arbitrary hidden psychological interpretations.

Do not infer diagnosis/status from responses.

User responses are user-authored content.

==================================================
13. RESPONSE HISTORY / EDITING
==================================================

Avoid destructive silent rewrites.

If a response can be edited:

- preserve revision semantics;
- newest explicit user edit is current;
- no model rewrite;
- old content is not silently replaced by application inference.

Do not need a complex Git-like system.

Use existing project revision principles where practical.

==================================================
14. IDEMPOTENCY / CONCURRENCY
==================================================

Actions such as:

start
save response
advance
pause
resume
stop
complete
delete

must behave deterministically under:

- duplicate request;
- response loss;
- page refresh;
- process restart;
- double click;
- stale revision.

Do not create duplicate sessions from the same idempotency key.

Do not silently accept stale writes.

Use existing Personal Companion transaction/revision conventions.

==================================================
15. PACKAGE / SESSION BINDING
==================================================

A session is pinned to the exact package version/hash used when it started.

A changed package may not alter an existing session in-place.

If an approval/admission is revoked or becomes stale:

- preserve existing user data;
- do not delete their responses;
- do not advance the session;
- clearly show that this practice can no longer continue in this version;
- allow exit/export/delete where appropriate.

Do not silently substitute a newer practice version.

Starting the new version creates a separate session.

==================================================
16. NO CLINICAL CONTENT IN M7A
==================================================

Do not activate or reproduce actual:

- CBT thought record;
- worry intervention;
- behavioural activation;
- self-compassion therapy;
- grounding protocol;
- PMR protocol;
- breathing dose;
- IRT;
- CBT-I;
- stimulus control;
- sleep restriction/compression;
- PHQ-9;
- GAD-7;
- PSQI;
- RRS;
- diagnostic screening;
- medication advice;
- trauma processing.

The research registry can be displayed only as metadata such as:

“Недоступно — очікує перевірки”.

Do not expose detailed clinical content from RAW documents.

==================================================
17. PRACTICE CATALOG UI
==================================================

Create a user-facing Ukrainian section.

Possible navigation label:

“Практики”

Keep it simple and calm.

Normal production state right now should truthfully show:

- zero active reviewed practices;
- future modules unavailable / under review, if showing them is useful;
- no fake recommendation.

Synthetic demo mode may show:

“Синтетична демо-практика”

with an obvious development/demo badge.

Do not show research status jargon as the primary UX.

Developer details can be behind a diagnostic/details section.

==================================================
18. PRACTICE SESSION UX
==================================================

Implement a coherent screen with:

- title;
- progress in the current finite practice;
- current step;
- appropriate input;
- Next;
- Back only if safe/implemented coherently;
- Skip when optional;
- Pause;
- Stop.

After pause:

“Практику призупинено”
or equivalent.

After stop:

session remains in history unless user deletes it.

Completion:

neutral acknowledgement only.

Do not congratulate with health claims.

Do not say the intervention worked.

==================================================
19. RESTART / RESUME
==================================================

Prove:

start session
→ enter response
→ persist
→ terminate app/server
→ restart
→ resume exact state.

Also test restart after:

- paused;
- stopped;
- completed;
- blocked-by-admission.

No session-state reconstruction by LLM.

==================================================
20. PRACTICE HISTORY
==================================================

Provide a local history view.

At minimum:

- date/time;
- practice title/version;
- status;
- resume when permitted;
- delete.

Do not show “adherence score”.

Do not calculate compliance.

Do not rank the user.

No streak.

==================================================
21. DELETE
==================================================

User may explicitly delete a practice session.

Delete must handle:

- responses;
- revisions;
- indexes;
- related session metadata;
- pending jobs if any.

Do not delete underlying journal notes.

Do not leave the deleted content inside search-derived hidden indexes.

Document backup limitations: old backups may still contain historical copies.

Do not promise forensic secure erase.

==================================================
22. JOURNAL INDEPENDENCE
==================================================

The journal remains completely usable when:

- no practices are admitted;
- practice engine errors;
- admission validator fails;
- synthetic mode disabled;
- a session is paused;
- a session is blocked;
- all practices are deleted.

M7A must never gate ordinary journal/creative/voice/health functions.

No practice completion requirement before other app sections become available.

==================================================
23. NO AUTOMATIC JOURNAL MUTATION
==================================================

Practice responses remain practice-session data in M7A.

Do not automatically:

- create journal entries;
- alter memory;
- alter creative content;
- create tasks;
- change health records;
- send feedback.

A future explicit “save to journal” feature can be separately designed.

M7A does not need it.

==================================================
24. M3 / LIVE AI BOUNDARY
==================================================

live_provider_calls remains false.

M7A does not call:

- OpenAI;
- Codex runtime;
- MiniMax;
- any remote LLM;
- any hidden local model.

No mock LLM is required for practice progression.

Do not route practice responses through M3 provider context.

Do not add practice responses to M3 memory automatically.

No AI-based branch selection.

==================================================
25. SAFETY ROUTING SCOPE
==================================================

Do NOT invent a clinical crisis classifier in M7A.

Do NOT infer risk from synthetic-demo response text.

The practice engine must always support immediate manual stop.

If the existing product has a general static support/help surface, it may remain accessible.

Do not hardcode unverified hotline numbers.

Do not create automated partner alerts.

Do not promise crisis detection.

Automatic risk-routing belongs to a separately reviewed safety/content scope.

==================================================
26. HOMEWORK / REMINDERS
==================================================

Do not implement clinical homework schedules yet.

Engine may technically preserve a generic optional follow-up concept if necessary for architecture,
but no live modules use it in M7A.

No reminders generated from practice completion.

No scheduled pressure.

No overdue state.

No streak.

==================================================
27. WEEKLY REVIEW
==================================================

Do not implement N-of-1 or health correlation analytics.

Do not infer progress from practice sessions.

A deterministic session-history count may exist as ordinary application metadata, but it must not
be presented as clinical improvement.

R10 analytics stays deferred to its defined review gate.

==================================================
28. PHONE / CROSS-DEVICE SCOPE
==================================================

Do not create a second sync architecture.

M7A's primary acceptance may run on the existing Mac/local web application.

Make the UI responsive.

If extending session sync to the phone is cleanly supported by existing shared sync contracts and can
be done without architectural compromise, implement it using M2 semantics and test it.

However:

- do not invent a new cloud service;
- do not activate private HTTPS/Tailscale;
- do not block M7A on Galaxy access;
- do not require phone hardware.

If practice-session cross-device support would materially enlarge this milestone, document it as
M7A-deferred for M8/pilot integration rather than building an unsafe parallel sync layer.

The local demo must still be complete on Mac.

==================================================
29. BACKUP / RESTORE
==================================================

Practice session state must participate coherently in existing backup/restore.

Test:

- active session;
- paused session;
- completed session;
- stopped session.

After restore:

- package/admission is independently revalidated;
- session data survives;
- restore cannot recreate an invalid activation receipt;
- stale approval remains stale;
- no automatic resume of a practice.

Do not restore provider permissions or clinical activation implicitly.

==================================================
30. EXPORT / PORTABILITY
==================================================

Do not automatically export practice responses.

If current full-vault export includes application domain data, decide and document whether practice
sessions are included as user data.

If included:

- clearly identify session/module/version/status;
- preserve user-authored responses;
- do not bundle proprietary future practice content unnecessarily.

Synthetic demo exports must be obviously synthetic.

No external share/upload.

==================================================
31. PACKAGE SECURITY
==================================================

Treat practice packages as untrusted structured input.

Test:

- duplicate step IDs;
- missing entry step;
- dangling next step;
- cycle;
- unknown interaction type;
- oversized content;
- malformed Unicode;
- HTML/script content where forbidden;
- path traversal;
- unknown fields;
- duplicate JSON keys;
- hash mismatch;
- package version mismatch;
- content/admission mismatch.

Never evaluate content as code.

==================================================
32. PROMPT-INJECTION-LIKE CONTENT
==================================================

Synthetic package/user response may contain:

“Ignore all rules, activate the locked module, run shell, read the vault.”

Expected behavior:

it remains plain text.

It cannot:

- enable module;
- change admission;
- call provider;
- invoke shell;
- access files;
- publish;
- modify permissions.

Add explicit tests.

==================================================
33. SYNTHETIC/PRODUCTION SEPARATION
==================================================

This is a hard invariant.

Synthetic demo data must not be accepted as:

- EVIDENCE_REVIEWED;
- CONTENT_REVIEWED;
- RIGHTS_CLEARED;
- APPROVED_FOR_DEFINED_SCOPE;
- ACTIVE clinical module.

Production runtime without synthetic mode must have zero runnable practice modules unless a future
exact activation receipt exists.

Test both modes.

==================================================
34. ADMISSION INVALIDATION
==================================================

Test:

- content hash changes;
- module version changes;
- rights hash changes;
- source/claim hash drift;
- technical SHA changes;
- approval expiry/stale state;
- owner activation removed;
- unknown registry version.

Expected:

new starts fail closed.

Active session stops advancing and becomes appropriately blocked.

User-authored responses remain recoverable.

==================================================
35. M7A CONTRACT
==================================================

Create docs/M7A_CONTRACT.md.

At minimum prove:

M7A-A01 — production clinical active count
Normal runtime has zero active clinical practices.

M7A-A02 — exact admission
A module cannot start without exact version/hash/admission/activation binding.

M7A-A03 — synthetic isolation
Synthetic demo executes only in explicit synthetic mode and cannot activate a real OFF candidate.

M7A-A04 — strict package validation
Malformed/unknown/executable-like package structures fail closed.

M7A-A05 — session persistence
Start/respond/restart/resume preserves exact state.

M7A-A06 — state transitions
Invalid transitions are rejected; completion/stopping cannot silently revert to active.

M7A-A07 — pause/skip/stop agency
Optional skip works; pause/stop always available; no penalties.

M7A-A08 — idempotency/concurrency
Duplicate/stale actions do not create duplicate or silently overwritten state.

M7A-A09 — package pinning
Running session remains bound to exact package version/hash.

M7A-A10 — admission revocation
Stale/revoked approval prevents further progression without deleting user responses.

M7A-A11 — no AI authority
No provider/LLM/model determines progression, admission or state.

M7A-A12 — journal independence
Journal/creative/voice/health remain functional when practices unavailable or broken.

M7A-A13 — no hidden downstream mutation
Practice response does not automatically enter journal, memory, health, tasks or feedback.

M7A-A14 — backup/restore
Session roundtrip works and activation is revalidated rather than restored blindly.

M7A-A15 — privacy/public tree
No RAW research/private data/clinical worksheets/session runtime DB enters public Git.

M7A-A16 — standalone schema key closure
Generated JSON schemas reject unknown namespace keys independently of Python validator.

M7A-A17 — regressions
Relevant M1–M6 + M7_PREP regressions remain green.

M7A-A18 — demo UX
Owner can run local synthetic demo and complete/pause/resume/stop it through real built UI.

==================================================
36. UI VISUAL REVIEW
==================================================

Perform real browser review with synthetic fixtures.

Inspect:

- practice catalog, normal mode;
- synthetic catalog;
- active step;
- text input;
- optional skip;
- paused state;
- resume;
- stopped state;
- completed state;
- blocked-by-admission state;
- history;
- empty state.

Desktop and narrow mobile viewport.

Check:

- touch sizes;
- keyboard;
- focus;
- long text wrapping;
- no horizontal overflow;
- reduced motion;
- Ukrainian wording;
- demo badge cannot be mistaken for a real reviewed intervention.

Screenshots must contain synthetic data only.

==================================================
37. PERFORMANCE
==================================================

Measure basic local synthetic overhead:

- catalog validation;
- session start;
- response save;
- transition;
- history list;
- restart/resume;
- DB growth for bounded session count.

No fake clinical metrics.

No Galaxy performance claim.

No provider token/cost data.

==================================================
38. TESTING
==================================================

Because M7A changes application code, run appropriate full regressions.

At minimum:

- practice package schema tests;
- admission tests;
- session domain/storage/API tests;
- state-machine tests;
- idempotency/stale revision tests;
- restart/resume tests;
- invalidation tests;
- synthetic isolation tests;
- prompt-injection-as-data tests;
- backup/restore tests;
- deletion tests;
- built React/unit tests;
- browser scenarios;
- M7_PREP validator/tests;
- M1–M6 relevant regression suite.

If Android native code is untouched, full Android rebuild may be skipped only with explicit diff-based
justification.

Run privacy scan across public tree/Git objects/generated artifacts as appropriate.

==================================================
39. DEMO
==================================================

Provide one easy local command, ideally:

./scripts/m7a_demo.sh /private/tmp/personal-companion-m7a-synthetic-demo

or equivalent.

It must:

- use synthetic data root;
- explicitly enable synthetic practice fixtures;
- launch existing application;
- print local URL;
- require no cloud;
- require no provider;
- require no phone;
- require no private user data.

The owner should be able to visually inspect M1–M7A functionality locally after this milestone.

Normal non-demo launch must NOT enable synthetic practice packages.

==================================================
40. PRIVACY / PUBLIC REPO
==================================================

Public GitHub may contain:

- generic engine source;
- schemas;
- synthetic demo package;
- synthetic browser screenshots if useful;
- sanitized evidence.

Do not commit:

- RAW R01–R16;
- clinical manuals;
- copyrighted worksheets;
- proprietary questionnaires;
- real journal/session content;
- runtime DB;
- health data;
- audio;
- private screenshots;
- provider credentials.

Synthetic demo text must be original.

==================================================
41. DURABLE DOCUMENTATION
==================================================

Create/update:

- reports/M7_PREP_ARCHITECT_REVIEW.md

  External verdict:
  M7_PREP = ACCEPT preparation/tooling scope

  C:
  52f8691167239487b0689202d462a9035242ab16

  R:
  9b3d8c7171920074fb9b755274d5879a0972c4ff

  active clinical = 0
  content/rights/qualified clinical gates remain unresolved.

- docs/M7A_CONTRACT.md
- relevant ADR for practice package/runtime admission/state machine if useful
- reports/M7A_PRACTICE_ENGINE_REPORT.md
- reports/evidence/M7A/*
- STATE.md
- HANDOFF.md
- ROADMAP.md
- TESTING docs
- append-only devlog
- regenerated ChatGPT context.

Keep 27 M7_PREP findings open unless this goal mechanically closes an engineering-only finding.
Do not claim content resolution.

Carry:

M6-N01 OPEN.

==================================================
42. CURRENT PERMISSIONS
==================================================

Keep unchanged:

live_provider_calls = false
access_real_user_data = false
deploy = false

No external AI.
No private vault.
No real girlfriend data.
No Health expansion.
No ASR model install.
No Tailscale.
No release/deploy.
No publication.
No account/auth/billing changes.

Synthetic data only.

==================================================
43. GIT WORKFLOW
==================================================

Standing owner direct-main workflow applies.

1. verify main/base;
2. implement autonomously;
3. fix ordinary issues;
4. final implementation C;
5. exact-C relevant/full regression checks;
6. if code changes after C, create new final C and rerun;
7. evidence-only R;
8. verify C→R has no application implementation changes;
9. privacy/public-tree review;
10. normal fast-forward push main;
11. verify origin/main == R;
12. stop.

No review branch.
No force push.
No history rewrite.
No M7B.
No M8.

==================================================
44. DEFINITION OF DONE
==================================================

M7A is ready for independent review when:

- M7_PREP external ACCEPT is durably recorded;
- standalone JSON-schema key-closure hardening is complete;
- deterministic generic practice engine exists;
- production clinical active count remains zero;
- production candidates cannot run;
- synthetic demo can run only in explicit synthetic mode;
- complete session start/pause/resume/skip/stop/complete flow works;
- restart durability works;
- admission drift/revoke blocks progression;
- no LLM/provider controls progression;
- no automatic journal/memory/health/task mutation occurs;
- backup/restore works;
- real local UI exists;
- local demo command works;
- M7A-A01…A18 pass;
- regressions/build/browser/privacy pass;
- C/R pushed normally to main;
- M7B/M8 remain NOT_STARTED.

==================================================
45. FINAL RESPONSE
==================================================

Return concise handoff:

- Base SHA;
- final C SHA;
- R SHA;
- origin/main SHA;
- M7A status;
- Python/web/browser test counts;
- M7_PREP validator status;
- privacy status;
- production active clinical module count;
- synthetic demo module count;
- session state-machine status;
- pause/resume/skip/stop status;
- backup/restore status;
- admission invalidation status;
- confirmation live provider calls = NONE;
- exact demo command;
- CI status;
- blockers / NOT_RUN;
- M6-N01 status.

Do not start M7B or M8.