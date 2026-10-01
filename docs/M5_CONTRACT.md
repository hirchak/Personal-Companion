# M5 contract — creative library, exact local feedback, optional space

Owner goal: [all 34 requirements](../prompts/M5_CREATIVE_SPACE.md). Status PROPOSED / AWAITING_REVIEW;
executor completion becomes AWAITING_REVIEW. External M4 synthetic ACCEPT is recorded in
[review](../reports/M4_ARCHITECT_REVIEW.md). M4 ASR/human-UA/Galaxy/private rollout remain NOT_RUN.
Architecture: [ADR-005](adr/ADR-005-M5-CREATIVE-SHARE-SPACE.md).

## Originals and organization

An item is the existing journal entry (`type=creative`); its UUID, raw text, USER_REPORTED provenance,
revision history, created/updated timestamps, CAS operation receipts, search, deletion/tombstones,
M2 encrypted outbox and sync wire v2 stay authoritative. `creative_kind` extends to idea/scene/
character/theme/phrase/shot/list/reference/other. Optional `creative_meta` holds only library=true,
title ≤160 codepoints, ≤8 distinct collections of ≤64, ≤8 distinct UUID related IDs and archive flag.
Existing journal tags remain ≤20 distinct ≤64. No second independent original is saved.

Direct capture creates one journal entry and metadata in one transaction. Promote adds metadata
explicitly to the same UUID. Remove collection edits only collections. Archive edits only archive.
Remove library sets metadata null; journal/raw text remains. Explicit source delete uses existing
M1–M2 transaction/history purge/tombstone semantics. New self/noncreative/missing relationships
are rejected transactionally; previously linked now-missing IDs are inert metadata, shown as missing
and removable. No graph traversal or related-text expansion. Historical revisions are previous
versions of the one journal original; not independently editable stores. Full typed metadata is in
immutable revisions and schema-5 backup. No psychological tags, vectors or inferred profile.

SQLite library browse/search is literal `instr`, bound parameters, kind/tag/collection/archive filters,
recent/newest sorting, 1–100 bounded page and explicit offset. UI uses 50/page. Search title and text;
no interpretation of SQL, Markdown, HTML, note instructions or fictional credentials.

## Phone and conflict behavior

The same EntryInput OpenAPI contract drives compiled CSP-safe phone validation. M2 AES-GCM IDB,
atomic commit/CAS, pending operations, credentials/receipts/reconciliation and delete epoch rules
remain. Creative actions work without pairing/network/AI. New phone capture timestamps persist;
legacy absent local timestamps are null, never fabricated. Changes in another local view fail CAS;
Mac conflicting revision returns normal M2 conflict and retains both variants for explicit choice.
Conflicted/repair-required creative items are read-only until normal journal reconciliation.
Reopen/browser restart keeps metadata and pending edits. IDB eviction remains possible.

## Selected creative export

Mac preview accepts 1–100 unique explicit ID+revision refs and nonempty allowlisted fields: raw_text,
title, creative_kind, tags, collections, related_ids (IDs only), timestamps, provenance. No full-library
selector; related text inclusion is always false. Response displays projected exact selected records,
fields, destination local_file, warning, Markdown and SHA-256. Preview artifact ≤2 MiB; in-memory plans contain refs/fields/hash only, no raw text copy. Five-minute owner-session plan;
export rejects wrong session/hash/expired or any edited/removed/deleted source. Markdown and JSON.
Raw text is fenced literally with a delimiter longer than any backtick run; HTML is data.

Phone uses the same projection and explicit ID/revision selection entirely offline; preview shows
phone scope and projected content. Download recomputes current projected SHA and pending-effective
revision, rejecting changed/deleted/conflicted entries. No network for phone export. File downloads
use browser Blob; Mac responses use loopback Content-Disposition. No paths or cloud destinations.
App does not write exports into source/Git. User chooses local browser destination.

## Feedback separation and approval

Separate SQLite feedback_drafts, no automatic source reader. Manually authored title (1–160), type
bug/feature/design/other, expected/actual/steps ≤4000 each, description ≤12000, visibility private or
intended_share, intended destination description (1–240). Source references and attachments are
explicitly unsupported (empty-only schema); no default journal/fiction/audio/transcript/health copy.
Private story with product words is still a journal entry; no implicit draft or approval.

Create/save uses immutable draft UUID and base-version CAS. Any save increments version and clears
approval. Preview shows complete exact Markdown and canonical JSON. SHA-256 covers draft_id,
version, restore_epoch, full content including destination/visibility/empty references/attachments,
and actual export_destination=local_file. Exact approval writes precisely hash+version+epoch after
recomputing in one transaction. UI requires saved unchanged draft, exact preview and checked explicit
approval. Native disabled fieldsets prevent draft/selection changes during pending save/approval/export/preview; a delayed old response cannot replace newly typed text. Unsaved edits hide approval/export immediately; stale cross-tab requests are refused.

Approved export revalidates exact current copy in a read transaction; emits Markdown/JSON with
approved version/hash, intended destination/visibility, exported UTC time, absent references and
attachments, local_file and publication NOT_PERFORMED. There is no publication tool/route, GitHub
issue/email/Slack/Telegram/client provider call or sender. Private text can never alter permissions.
Manual authored content may contain private text; the user must review the exact local copy.
This is an exact local export gate, not a proof that manually typed content is safe to publish.

## Optional cosmetics and parity

Original CSS/SVG geometry: books, vase, geometric print on a shelf. OFF by default. Persist only
enabled/theme (paper/sage/clay), fixed owned IDs and a permutation layout; all objects available from
start. No progress events, unlocks, streaks, scores, reminders, rewards, timers, random/paid mechanics,
health/symptom/sleep/sentiment/secret or disclosure inputs. Explicit ON/OFF never touches entries,
feedback, AI memory or voice. Same commands and APIs stay available in both modes.

Chosen scope: **device-local, independently configured**. Mac SQLite personal_space uses versioned
CAS + idempotent identical retry. Phone state is in its AES-GCM journal envelope with version/local
CAS, persisted OFF keeps theme/layout, included in encrypted recovery. No cosmetic state enters M2
packets, AI context or external services. Phone UI states only this-device scope; no synced claim.
Mac feedback/M3 memory retain their existing owner-session scope; a phone-sized Mac interface has
all feedback/voice/memory functions. Paired offline PWA has creative/journal/voice parity and local
cosmetics; it does not claim offline feedback or offline AI-memory capabilities.

## Backup, deletion and previous behavior

Schema 5 migrates 1–4 transactionally with preupgrade snapshot and rollback. M4 backup format2
continues: consistent SQLite + validated audio attachment manifest/checksums. New tables receive
typed integrity checks on reopen and before restore activation. Backup copies clear feedback approval;
live approval unchanged. Restore increments epoch, clears approvals before activation; old exact hashes
are unusable, fresh saved-copy review required. Old schema2/3/4 backups migrate normally.

Deleting a creative original blocks stale packets/replayed create through tombstones; related IDs do
not reconstruct it. M3 pending/accepted source-derived suggestions become STALE on source edit/delete;
organization outputs contain typed refs/groups, not hidden raw-text copies. Creative memory inference
remains denied. No automatic AI after save/sync/voice.

Historical backups can contain previously captured content, as with existing M4 backups. Restore is
an explicit operation into a new empty root, not a merge into the current vault. It never mutates
current tombstones; revoked credentials/new restore epoch block stale devices. No guarantee that
historical/offline copies are erased, nor forensic deletion claim. A historical restore cannot know
future deletions not present in that snapshot; keep this limit visible rather than claiming otherwise.

## Acceptance mapping

| ID | Required proof | Synthetic tests / evidence |
|---|---|---|
| M5-A01 | Original+metadata durability/archive/promote | test_m5_domain all-kinds/durability; m5.test encrypted restart; browser library |
| M5-A02 | One original, organization/suggestion separation | domain metadata/history; creative mock; UI edits |
| M5-A03 | Tags/collections/relations/search/missing links | domain literal queries/relations; phone archive/removal; browser filters |
| M5-A04 | Phone offline restart/safe sync/conflict/delete | real Chromium persistent offline/sync/conflict; domain M2/epoch; Vitest CAS |
| M5-A05 | Exact minimized selected export | domain fields/hash/session/change; phone hash/stale/delete; browser downloads |
| M5-A06 | Source never auto-feedback | domain adversarial empty feedback; API refs refusal; browser private source |
| M5-A07 | Exact approval/edit invalidation | domain CAS/destination/visibility/hash; browser preview/edit/reload |
| M5-A08 | Correct approved local artifact, no sender | guarded domain export; denied API publication; browser egress/download |
| M5-A09 | Data-as-instructions contained | synthetic note/fiction/voice-like instructions; no auto approval; local literal fences |
| M5-A10 | OFF functional parity / no data loss | domain+Vitest state; browser creative/export/journal/voice/memory OFF |
| M5-A11 | No pressure/reward/inference mechanics | strict state allowlist tests; static/manual source review |
| M5-A12 | Persisted cosmetics/CAS/device scope | SQLite reopen/idempotency/backup; encrypted IDB restart/recovery; real phone+Mac |
| M5-A13 | Explicit M3 creative organization, no memory | exact-selected mock/no unselected context/accepted stale; prior M3 gates |
| M5-A14 | Generic original visuals/public tree privacy | diff/rights review, public/all-object/generated/built scan, synthetic screenshot inspection |
| M5-A15 | Full M1–M4 + new-state backup/migration | full Python/Vitest/build/browser, M4 audio tests, damaged restore/epoch |

PASS records command, exact C, environment, exit code. UI pictures are supporting evidence;
not privacy proof. M5 is never self-ACCEPTED. Live providers/real private/Health/clinical/deploy/
external publication/M6+ remain OFF; actual ASR/Galaxy/private rollout/human UA not executed.
