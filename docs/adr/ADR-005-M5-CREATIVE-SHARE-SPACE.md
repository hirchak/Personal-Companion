# ADR-005 — One creative original, exact local feedback, device-local cosmetics

Date 2026-10-01. Implementation decision within explicit M5 owner scope; independent review pending.

Creative items decorate existing journal entries with optional bounded creative_meta. All authored
text and metadata changes use one revision/CAS/tombstone/M2 sync contract, not a second text table.
This makes offline captures and conflicts portable without a new synchronization system. Missing
related IDs are inert and never imply reconstruction or graph traversal.

Feedback is a distinct manually authored object. No source ingestion, attachment or private reference
capability is necessary in M5, so schemas accept empty lists only. Exact canonical draft/version/hash/
destination/visibility/restore-epoch approval authorizes local download alone. Any edit or restore
stales approval; export recomputes the exact copy. There is no network/Git publication capability.

The cosmetic layer is independently configured on each device, clearly labelled. Mac SQLite and
phone encrypted envelope have bounded versioned CAS; ON/OFF preserves layout/theme. No progression:
every geometric object is available immediately, and no authored/health data influences state. Cosmetic
state never enters M2 journal packets or M3 AI context. Phone encrypted recovery includes local space;
Mac consistent audio-aware backup includes new tables. No cloud or generic game synchronization.

Schema5 extends existing transactional migrations and format2 backups. Integrity validation includes
new persisted state; approvals are removed from backup copies and require new exact review after
restore. Historical backups/offline copies retain their preexisting deletion limits: restoring into
an isolated fresh root is explicit, not a silent merge or promised forensic erasure.

Consequences: simple collection names (not independent collection text objects), max8 relationships,
Mac owner-session feedback and existing M3 memory scope, phone offline creative/export without AI.
No AI creative task expansion is needed: existing exact-selected organize_selected works safely;
creative memory_propose remains denied. Live provider gate remains disabled.
