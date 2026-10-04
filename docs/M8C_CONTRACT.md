# M8C — private local core runtime

Authority: [owner goal](../prompts/M8C_PRIVATE_LOCAL_PILOT_RUNTIME.md), [ADR-013](adr/ADR-013-M8C-PRIVATE-LOCAL-CORE.md).
Executor completion AWAITING_REVIEW. Actual private pilot NOT_STARTED; actual private root NOT_CREATED.
Every private-mode test uses ORIGINAL SYNTHETIC content; domain provenance remains PRIVATE_PERSONAL/USER_REPORTED.

| ID | Acceptance | Authoritative evidence |
|---|---|---|
| M8C-A01 | External M8B ACCEPT exact C/R durable | reports/M8B_ARCHITECT_REVIEW.md; STATE/HANDOFF/ROADMAP |
| M8C-A02 | Distinct typed root, corruption/loose-flag refusal | root_types/local_private/storage; deterministic binding tests |
| M8C-A03 | Explicit init/new-empty/exact release/consent/security | initialize-private; preflight/init-negative tests |
| M8C-A04 | Loopback/auth/CSRF/Host/Origin/deny-egress | API/launcher; auth/security/egress tests; Mac process/Chromium |
| M8C-A05 | Core-only runtime profile | manifest3/profile/API allowlist/runtime.set_mode tests |
| M8C-A06 | No provider/env/clinical/Health/ASR/phone/cloud activation | optional factory + HTTP negative tests; defaults after lifecycle |
| M8C-A07 | Exact-volume/native security READY or fails closed | strict PrivatePreflight; unmocked actual Mac + negative status tests |
| M8C-A08 | Explicit protected local backup container | policy/FileVault/0700/0600/ACL checks; protection refusal tests |
| M8C-A09 | Exact release/source/snapshot/policy/root provenance | backup4/snapshot attestation/trusted hashes; tamper tests |
| M8C-A10 | Private→fresh private restore/renewed acknowledgement | deterministic + exact Mac backup/restore; history/tombstones |
| M8C-A11 | Cross-mode restore refused before roots | private→synthetic and reverse negative tests |
| M8C-A12 | Upgrade/restart/failure/fresh-root rollback/restart | deterministic transactional failure + actual Mac lifecycle |
| M8C-A13 | Uninstall KEEP DATA | private lifecycle + generic removal regression |
| M8C-A14 | Separate exact-root private delete/backups kept | delete-private-data; confirmation/wrong-kind/unknown tests |
| M8C-A15 | Truthful private UI, journal default, unsafe controls absent | real Chromium mode/CRUD/menu/lock; synthetic screenshots |
| M8C-A16 | Actual Mac final-C private runtime synthetic content | MAC_PREFLIGHT/MAC_LIFECYCLE/release manifest/exact-C checks |
| M8C-A17 | No real private/provider/system/phone/Health activation | scope counters + canonical evidence/history/privacy review |
| M8C-A18 | Exact post-ACCEPT owner/data-owner procedure | PILOT_HANDOFF/INSTALL/UPGRADE/RECOVERY/UNINSTALL |
| M8C-A19 | Core READY only if all core checks/lifecycle pass | independent PILOT_READINESS with tested-Mac scope |
| M8C-A20 | Actual private pilot NOT_STARTED | STATE/report/evidence; real root NOT_CREATED |

Forbidden optional routes return403 after authentication; unauthenticated API content returns401.
Normal startup never initializes. Data schema11 unchanged; PRIVATE_LOCAL identity is an optional mode-specific
integrity table. Format1/2 manifests and synthetic backup1/2/3 remain supported; private requires manifest3/backup4.
Owner-only means current owner UID, directory0700/file0600 and no extended ACL grants, no silent permission repair.
Security is verified FileVault-protected APFS volume, not application-encrypted DB/archives. Protected archive copies
on unencrypted storage lose protection. Compromised/unlocked OS outside scope; no assurance against admin/same-user
malware/other localhost clients. OS/cloud agents outside app are owner's separate storage-routing responsibility.
Unknown native protection state blocks init/backup/restore/start; no OS change is made. Runtime capability/egress gates
are independent of environment credentials. No retention auto-delete/import/discovery/update/download/upload.
No in-place downgrade; old M8A/B package cannot receive private backup. Rollback requires compatible private-aware
M8C package and independently retained producer/backup hashes. Future restore repeats current security/consent.
After independent ACCEPT + explicit owner/data-owner activation no extra core milestone if criteria pass;
AI/ASR/Health/clinical/phone gates remain independent, never automatic.
