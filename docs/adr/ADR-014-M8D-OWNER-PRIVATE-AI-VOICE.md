# ADR-014 — Owner-bounded private AI and local voice

2026-10-04. IMPLEMENTED_AWAITING_REVIEW; actual private AI activation NOT_STARTED.
Authority: final owner binding in prompts/M8D_PRIVATE_AI_VOICE_PILOT.md. Scope this owner's Mac,
original synthetic engineering fixtures only; no commercial, third-party or zero-retention certification.

Preserve ADR-013 PRIVATE_LOCAL identity, storage/security/backup policy and schema11. Release format4/M8D
adds a distinct MAC_PRIVATE_AI_VOICE_PILOT_V1 manifest-bound optional profile. Core vault is unchanged;
post-review application upgrade preserves it. AI and local voice start OFF after restart/lock/restore.
Session-local seven Boolean owner disclosures/settings confirmations, separate three local-voice acknowledgements,
and exact per-send private context preview are required. TRAINING_CONTROL_CONFIRMATION = REQUIRED_AT_REAL_ACTIVATION / NOT_YET_CONFIRMED_TO_ARCHITECT.
CODEX_ENVIRONMENTS_CONFIRMATION = REQUIRED_AT_REAL_ACTIVATION / NOT_YET_CONFIRMED_TO_ARCHITECT.
Synthetic fixture acknowledgements establish no real owner/architect confirmation. No account/settings/credential inspection.

Use one existing neutral ConversationController. Private contracts are separately typed, synthetic=false;
private records retain PRIVATE_PERSONAL/USER_AUTHORED/MODEL_GENERATED provenance. Original synthetic test
content labels reside in fixture text/evidence; production cannot relabel private records synthetic.
FREE current text plus six recent same-conversation sources; DEEP explicit goal/revision/focus/maps/closures/
range. Private DEEP never automatically imports other Free conversations. Journal defaultOFF; at most10 exact
selected revisions, explicit preview with hashes/model/effort/draft/purpose/session generation binding; changed
source/profile/restart fails closed. Journal-derived map items retain source revisions and stale invalidation,
never USER_STATED from a journal; model output cannot grant USER_CONFIRMED authority. No memory promotion,
whole-vault discovery, automatic journal writes, creative/Health inference or clinical modules.

Final profiles: FREE Luna/high; explicit DEEP economical Luna/max or quality Sol6.1/high. Luna ceilingMAX,
Sol6.1 ceilingHIGH; native installed catalog verified before inference. No substitution/fallback. Engineering
four-attempt ledger counts failures/cancels/retries across restarts; production owner manual attempt receipts
are separate local metadata. Native thread/turn model, effort and permission profile must match. Invalid schema,
unsafe source/authority/language/tool output remains visible FAILED; no fabricated/automatic fallback response.

Main process deny-egress retained. Provider native client gets only bounded serialized text and a disposable
CODEX_HOME, existing SDK auth through a read-only local reference, installed public model catalog via supported
model_catalog_json. Application never reads/copies credential bytes. Global config, histories, memories, app/vault
files unavailable. Native OS sandbox permits installed code/system libraries, exact SDK auth/catalog and temporary
state; only one owned loopback transport port, no direct external sockets. Tool/MCP/app/plugin/browser/shell
capabilities disabled; any server tool request fails. Timeout120s; no native request/stream retries.

A separate isolated helper accepts only CONNECT chatgpt.com:443 and relays opaque end-to-end TLS. It never parses
TLS auth/content, persists payloads, accepts other hosts/ports or changes the provider endpoint. It has no vault,
app data or credential file permissions; only OS DNS resolver and fixed-target HTTPS transport. This adds a local
transport boundary to the existing subscription route, no gateway/auth/API billing replacement. Metadata-only
errors; no explicit SDK plaintext log opt-in; ephemeral child state removed on completion/failure/cancel.
Local same-user/admin or compromised/unlocked OS remains out of scope.

Existing pinned CPU whisper.cpp1.9.4-dev/small multilingual only; exact binary/model/receipt checks plus OS deny-
network/filesystem sandbox. Assets may be explicitly selected outside the installed package for the owner pilot,
without download/install. Microphone record→stop→PCM signal guard→local candidate→review/edit→insert draft→
private preview→explicit text send. No auto-send or audio in provider payload. NO_SPEECH blocks; UNCERTAIN requires
review/edit. Audio remains local until visible manual deletion; no secure-erasure claim. Human UA quality remains
OPEN_HUMAN_TEST; five owner utterances only after architect ACCEPT, no uploaded recordings.

Existing first-party local app-server route is permitted for local applications using existing auth; this does
not establish hosted/commercial or zero-retention suitability. Training OFF is separate from retention. Sources:
[app-server auth](https://learn.chatgpt.com/docs/app-server), [auth](https://learn.chatgpt.com/docs/auth),
[configuration](https://learn.chatgpt.com/docs/config-file/config-reference),
[data controls](https://help.openai.com/en/articles/7730893-data-controls-in-chatgpt).
Clinical0/all five specialistsOFF/27findingsOPEN. Health/phone/cloudASR/embeddings/sync/telemetry/publicationOFF/NONE.
M7D-N02 human language review stays OPEN; actual owner vault is never accessed in M8D engineering.

Private provider/ASR temporary work directories require owner-only access and freshly verified protected local volume before writing text/audio/client state. Unsafe, cloud/Git or unverified temporary storage fails closed; no arbitrary TMPDIR escape of the at-rest policy.

2026-10-08 owner-local M8E transport correction (AWAITING_REVIEW): the reference Mac's DNS returns IPv6 first,
but its IPv6 TCP route stalls while IPv4 reaches the fixed subscription destination. The TLS-blind helper now
uses an explicit IPv4 socket to `chatgpt.com:443`. Host/port allowlisting, OS isolation, opaque TLS forwarding,
SDK-only credentials, and all no-fallback/PAYG/inference boundaries remain. This is address-family selection for
the same first-party route, not a model/provider substitution. Live readiness remains separately owner-scoped.


2026-10-05 independent review correction (M8D-R01/R02): C1 exact preview ordering claim was invalid with
selected journals. Use one canonical provider payload constructor, freeze the full validated object at preview,
bind ordered context + exact reflection_state and the whole request to approval hashes, and reuse that object
after freshness checks. Preview-only source placeholder maps to the subsequently persisted current-message
alias without changing any provider representation. Local source snapshots remain for freshness/provenance;
they are not the displayed/transmitted object. Stored legacy approvals fail closed; no historical record rewrite
or live inference. Current correction status AWAITING_REVIEW after checks/publication, never self-ACCEPT.
