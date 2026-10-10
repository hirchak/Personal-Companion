# M8F — checkpoint, final verification pending

Base: f32038f62e276400c41fb21c76ce753316b7aaa7. Status IN_PROGRESS.
Authority: [complete goal](../prompts/M8F_MACOS_APP_INSTALLER_UPDATES.md).
[Contract](../docs/M8F_CONTRACT.md), [architecture](../docs/adr/ADR-018-M8F-STANDALONE-MACOS.md),
[build/distribution](../docs/M8F_BUILD_AND_DISTRIBUTION.md), [guide](../docs/M8F_USER_GUIDE.md).

Final implementation C and evidence-only R are not claimed before exact final verification.
C1–C8 packaging/GUI findings and failed runs are preserved under ignored generated/m8f; final report
will bind safe receipts and exact commands/statuses. Real embedded core/Whisper/backup/restore worked
on fresh protected original-synthetic roots. Physical hardware is M2/8GB, not the requested16GB.

A C8 microphone attempt unexpectedly captured possibly non-synthetic audio and ran local ASR.
Potential transcript appeared in accessibility output; it is not used as evidence or committed.
The candidate was stopped; exact affected test root was deleted without reading file contents after
explicit scoped owner authorization. No external inference/upload or real owner-pilot access occurred.
This incident remains a material scope deviation, not a clean synthetic-only claim.
Final LOCAL_TEST prevents physical capture at native/page layers and uses only an explicit original
synthetic PCM fixture. Production signing/notarization/hosting/private activation remain blocked.

Next: final-C native install/update/negative/GUI and full regression verification, independent UI review,
complete evidence matrix, evidence-only R and normal fast-forward main push; STOP AWAITING_REVIEW.
