# M8E accepted implementation — existing private pilot activation

Owner goal for M8E only. M8E is externally ACCEPTED for implementation C4
`55b4d3d82e887f59ea4dcf1f8f167aea52d39b1` and review publication R2
`519bac8f77965ae7165ff536391dd75f19af284b`. The exact R2 `main` head was verified before work. Per owner, C4
differs from C3 only by a browser-test locator; C4 remains the exact accepted build identity.

## Authorized work

- Record external ACCEPT in the durable review/state/handoff/roadmap records.
- Stop the existing Personal Companion process cleanly if one is running.
- Run the accepted PRIVATE_LOCAL security preflight against the existing pilot roots.
- Make the accepted protected pre-upgrade backup and upgrade only the existing app/vault to exact C4.
- Verify content-free vault/schema/integrity preservation and the requested static local product/profile/asset
  capabilities; start the accepted foreground app on `127.0.0.1` and open its local page if supported.

Build or reuse only package `M8D-55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d` with a manifest that binds Git C4.
Build only from an exact clean C4 checkout and existing dependencies. Do not substitute the moving `main` SHA.

## Hard boundaries

Never initialize/create a vault, replace/restore to a new root, or inspect, print, export, summarize, or search
private records, conversations, audio, transcripts, or messages. Keep local root paths, receipts, unlock codes,
backup metadata, and content out of Git, reports, tool output, and assistant context. Use only the accepted
metadata-only private preflight/backup/upgrade/preservation/ASR checks.

Do not send an AI message, create a conversation, record microphone audio, or make live provider calls. Do not
configure phone transport, alter OpenAI account settings, install packages, deploy, tag, or publish a GitHub
Release. External training/environment controls remain `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`; never claim or
change that state. Phone transport remains OFF; clinical and Health remain OFF. Human Ukrainian ASR remains
`PARTIAL_OWNER_PILOT / OPEN`.

The owner manually chooses any runtime disclosure, AI/voice consent, model profile, message, or recording.
Conversation must be the default landing; Free/Deep and journal/creative/history capabilities remain present.

## Completion report

Report only the requested sanitized activation fields. Distinguish PASS, FAIL, NOT_RUN and UNVERIFIED honestly.
Do not call this a new milestone or infer acceptance for phone, clinical, Health, account controls, or human ASR.
Stop after the activation report.
