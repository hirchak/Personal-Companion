# M8E — Conversation-first mobile UX + seamless local voice

Authority: [complete owner specification](../prompts/M8E_CONVERSATION_FIRST_MOBILE_VOICE.md).
Base: `49d03d97d444083a63d18f3f3ec9ec8d295c19fd`. Synthetic engineering only; AWAITING_REVIEW after delivery.

Conversation is the optional private profile's default landing. Primary navigation: Розмова / Щоденник /
Творчість / Більше. Original paper/ink/sage identity, 390px bottom navigation, independent thread scroll,
reachable composer and responsive visualViewport. Existing M8C core-only profile retains its permitted journal.
Free/Deep are first-class conversation modes. Free requires no goal; history resumes its own bounded context.
Deep pins an explicit agreed goal revision, focus/session/map/closures; active prior topics can be reopened.
New conversations have no implicit journal, unrelated conversations or memory promotion. Local titles use the
first user message's whitespace-normalized first 72 Unicode codepoints; no title provider calls.

Free Luna/High; Deep explicitly economical Luna/Max or quality Sol6.1/High. Ceilings Luna≤Max/Sol≤High,
no fallback/PAYG. Details and controls live in Settings; messages remain readable with AI OFF.

One local consent acceptance replaces seven checkboxes for new M8E activation. Consent binds version,
privacy contract, destination, all approved profiles, vault identity and restore epoch. SQLite local consent
is never public evidence; lock/restart suspend runtime but retain consent. Authenticated client restores an
enabled consent without repeated disclosures. Disable persists AI OFF; revoke deletes consent and Deep scope
approvals and cancels runtime. Restore and material contract/destination/profile changes invalidate consent.
Authenticated local audio history/delete and transcript edits remain available after AI revoke; new recording/ASR still requires local voice consent. Local voice can be explicitly enabled independently of AI.
Legacy M8D session-only acknowledgement remains a compatibility endpoint, never creates durable consent.
External OpenAI settings are owner-controlled; app never verifies them or asserts zero retention.

Ordinary explicit Send constructs a canonical M8D preview/receipt on backend, then uses the same frozen exact
payload and freshness checks at queue/run/commit. No added journal field exists on standard-send contract.
Extra journals require visible selection of ≤10 exact revisions, contextual approval, canonical payload and
stale rejection. Optional payload inspection remains available. No audio/hash/voice descriptor goes to provider.
Deep first/materially changed scope requires explicit approval: goal revision, session revision/focus/phase,
retrieval range, current conversation and goal-bound map/closures. Explicit map corrections renew scope;
advisory model updates within the agreed scope do not require a popup every turn. Per-message source/profile/
map/skill/payload hashes are still verified. Private FTS and digests never inject unrelated conversations.

Composer microphone uses existing M4 PCM16 WAV recorder (≤120s). Stop persists audio, auto starts approved
local whisper, then fills editable draft. Send reviews/records exact edited transcript revision before sending
only text. No auto-send, no separate save/insert ceremony in primary path. Unavailable/crashed ASR leaves durable
Mac audio with WAITING_FOR_LOCAL_ASR/FAILED/review state; Voice History lists date/duration/text/retry/use/delete.
Existing audio/transcript storage and restart recovery remain authoritative; no fabricated completion or
secure-erasure promise. Unfinished browser capture or failed Mac save stays visibly in tab with retry and
beforeunload warning; it is never advertised as durable before a validated receipt. PWA offline recording uses
existing encrypted IndexedDB audio/chunks, LOCAL_AUDIO_SAVED queue (WAITING_FOR_LOCAL_ASR presentation), survives
reload and can be deleted locally. It never automatically uploads on internet availability. Upload requires
existing eligible pairing; current synthetic transport remains loopback-only. No real phone transport gate,
Tailscale/certificates/pairing, public audio storage, cloud ASR, Vercel audio vault or provider audio.

Preserved: typed PRIVATE_LOCAL, native volume/owner-only/security preflight, auth/auto-lock/CSRF/Origin/Host,
main deny-egress, isolated provider/whisper processes, clinical0/all specialistsOFF/HealthOFF.
No real owner content/audio/path/receipt, live provider call, native ledger attempt, account inspection,
release/tag/deploy/system integration or next milestone in M8E.

## Forward owner clarification — 2026-10-05

Historical commits/reports remain unchanged. Owner now states that first real private AI/manual voice use
preceded independent external account-setting verification. Earlier durable statements claiming confirmed-OFF
before that first test are inaccurate and superseded by this clarification (including the M8D activation
report, accepted review's activation paragraph and M8D contract addendum).

FIRST_REAL_PRIVATE_AI_TEST = OCCURRED_BEFORE_INDEPENDENT_EXTERNAL_ACCOUNT_SETTING_VERIFICATION.
TRAINING_CONTROL_CONFIRMATION = NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER.
CODEX_ENVIRONMENTS_CONFIRMATION = NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER.
HUMAN_UA_ASR = PARTIAL_OWNER_PILOT / OPEN; an owner manual microphone→whisper exercise is not formal quality
acceptance. No private transcript/audio is copied. PHONE_TRANSPORT = NOT_ACTIVATED / NEEDS_TRANSPORT_GATE.

## M8E-R01 forward correction: pinned Deep goal revision

An existing Deep conversation and its DeepSession, WorkingMap, closures, scope, and inference payload remain
pinned to `conversation.goal_binding.id + revision`. Scope display/hash reads goal text from that immutable
revision. It separately reads the current goal only to verify that lifecycle state remains `ACTIVE`; a newer
ACTIVE revision does not invalidate or rebind the older conversation. Editing revision 1 to revision 2 affects
new Deep conversations only. Each revision retains its own revision-keyed Working Map and source lineage.
A PAUSED or COMPLETED current goal continues to fail closed with `GOAL_NOT_ACTIVE`, before message persistence
or provider execution. This preserves the M7D pinned-revision contract.
