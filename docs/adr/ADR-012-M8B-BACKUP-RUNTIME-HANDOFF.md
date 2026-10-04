# ADR-012 — Release-aware backup, runtime-only prerequisites and honest pilot handoff

2026-10-04. ACCEPTED_EXTERNAL_REVIEW; M8B real reference Mac with synthetic data only.

New release manifest format2 / M8B-<exact Git C> binds requirements.runtime.lock separately from full
requirements.lock (dev/test/build input remains pinned and recorded). New runtime checks only12 actual
application dependencies. Existing M8A manifest format1 remains explicit compatibility with historical full-lock
requirements; no retroactive dependency/provenance relabeling. No automatic dependency installation/download.
The driver copies already-installed runtime distributions into a disposable pip-free venv; pytest/Playwright/httpx
are absent there. Build/test tools run separately in existing project environment.

Store backup format1/2 compatibility remains. Optional release_context produces format3: exact producing full
manifest + source release reference + snapshot schema/format/time. Producing manager sources must match all
core Python hashes in the supplied producing manifest. During upgrade the NEW manager creates the backup;
its producer identity differs from the OLD active source release. Do not falsely attribute creation to old code.

The metadata is also recorded in a snapshot-only SQLite release_backup_provenance row before the snapshot hash
is finalized. Restore checks exact metadata equality, producing manifest integrity, schema/time/app-version
consistency and independently expected producer manifest hash before creating target roots. Restored live roots
remove this snapshot-only attestation (no new live domain/schema migration); canonical domain provenance stays.
Standalone generic backup keeps historical M7D label and no release claim. Legacy release restore needs explicit
--allow-legacy-backup and returns LEGACY_UNKNOWN_PRODUCER. Historical artifacts are unchanged.

Backup receipt also returns SHA256 of manifest.json. Operator should retain it separately and pass
--backup-manifest-hash for strongest unsigned integrity binding of the entire receipt/content set.
Default expected producer is the target package hash; across-release restore/rollback explicitly supplies trusted
--producer-manifest-hash. Embedded checksums/metadata are NOT signatures. A fully rewritten unsigned backup plus
recomputed hashes is not authenticated without independently retained trusted hash; no stronger claim.

Actual-Mac preflight schema admits only sanitized OS/macOS/arm64/Python/model/chip/runtime/port/writability/disk
class facts, never username/serial/account/private paths. It applies only to the Mac running Codex, not all Macs.
New inactive MAC_CORE_PROFILE is a planned handoff contract; no activation route/private root is created.
Current Store and packaged launcher remain synthetic-only. Therefore distinguish READY synthetic Mac dry run from
NOT_READY actual MAC_CORE_PILOT until PRIVATE_DATA_RUNTIME_PROFILE_REQUIRED is resolved under separate owner goal/
data-owner consent/storage policy. This core gate is independent of optional AI/ASR/Health/clinical/phone modules.

Phone route remains candidate-only ADR-002; no existing authorized HTTPS/pairing route was proven. Record
PHONE_PRIVATE_TRANSPORT_REQUIRED / NEEDS_TRANSPORT_GATE without inspecting private accounts/endpoints or
installing networking/trust. Galaxy/human UA/Health0.6.1 gates remain NOT_RUN.

External M8B ACCEPT exact C434b1cd5/R1533a69c recorded in reports/M8B_ARCHITECT_REVIEW.md.
The synthetic-only runtime/inactive handoff above describes M8B; M8C adds a separately reviewed private mode
without reinterpreting historical evidence: [ADR-013](ADR-013-M8C-PRIVATE-LOCAL-CORE.md).
