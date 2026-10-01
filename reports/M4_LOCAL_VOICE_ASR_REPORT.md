# M4 — local voice and editable ASR engineering report

Status: IN_PROGRESS; exact final-C verification and evidence-only R pending.
Base: `40b33a05248353b910acf733db99e21242ee0bd2`. Final C/R: pending. Push/CI: NOT_RUN.
M3 external synthetic ACCEPT: [durable record](M3_ARCHITECT_REVIEW.md).
Full owner scope: [29-section goal](../prompts/M4_LOCAL_VOICE.md).

Implementation: bounded local PCM/WAV capture, separate AES-GCM phone chunks/operation metadata,
private Mac staged/fsynced/hash-verified attachment/recovery, M2 paired bounded resumable transfer,
disabled/fake/hash-pinned process ASR, separate candidate/edit/explicit note confirmation, retention,
encrypted rescue recovery and attachment-aware backup/restore. Existing journal and M3 remain independent.

Pre-final checkpoints: 257 Python (18 actual-browser, including 8 M4 fake-microphone scenarios),
21 web tests and build passed. Latest changed test/measurement/documentation checks still pending;
these checkpoint results are not final exact-C evidence. Raw audio generated only in temp directories.

Real local engine/model: LOCAL_ASR_BACKEND_NOT_RUN; REAL_LOCAL_ASR_MODEL NOT_RUN/PERMISSION_REQUIRED.
No actual speech model executed; no engine/model/hash or Ukrainian accuracy claim. HUMAN_UA_QUALITY NOT_RUN.
Galaxy S24 Ultra: HARDWARE_UNVERIFIED / NOT_RUN. Provider/cloud/clinical/Health/M5+ remain OFF.
Runbooks: [local ASR](../docs/M4_LOCAL_ASR_RUNBOOK.md), [Galaxy](../docs/M4_ANDROID_MIC_GATE.md).

This draft will be replaced with final exact-C evidence in the evidence-only R after implementation C.
Historical specification-receipt blocker is resolved by the owner's final sections 21–29;
[receipt report](M4_BLOCKER_REPORT.md) is retained as historical evidence only.
