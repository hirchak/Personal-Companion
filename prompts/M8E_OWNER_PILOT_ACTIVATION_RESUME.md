# M8E existing-owner pilot activation resume

This resumes the already authorized M8E owner-pilot activation after independent acceptance of the diagnostic follow-up. It is not a new milestone.

## Accepted identities

- Product runtime: exact M8E C4 `55b4d3d82e887f59ea4dcf1f8f167aea52d39b1d`.
- Product review: `519bac8f77965ae7165ff536391dd75f19af284b`.
- Preflight diagnostic candidate: C `1edacfb4749205cf1ccdc22f0601b5dac43a0d27`, R `d7de88f33db77c6dbb86971fce1d2b4c514e0eb1`; independent verdict ACCEPT for sanitized diagnostics only.
- The earlier `INVALID_METADATA` cause remains unconfirmed.

## Required sequence

1. Use only the accepted bounded metadata mechanism to locate the existing managed PRIVATE_LOCAL installation. Never expose its paths or IDs.
2. Use the accepted diagnostic candidate for read-only validation of the existing root; require `PASS` / `COMPLETE`.
3. Reuse or reproduce the exact C4 package only from a verified exact C4 build identity. Never build the owner runtime from moving `main`.
4. Run exact-C4 private-preflight once immediately before upgrade. If it is not PASS, stop without retry or bypass.
5. Upgrade only the existing root using the exact C4 manager and a new target inside the already approved protected backup directory. Preserve earlier backups and let the manager perform its own preflight and verified backup.
6. Verify root identity, schema/integrity, active C4 release, content-free preservation, static Conversation/Free/Deep/profile/journal/creative/local-ASR capabilities, and OFF defaults for provider, phone, clinical and Health.
7. Start only on `127.0.0.1:8765` and open the local page if supported. Leave all unlock, AI consent, message, and microphone actions to the owner.

## Boundaries

Do not inspect or print private content, send messages, create real conversations, record audio, make live provider calls, inspect/change external account controls, configure phone/Health/clinical, install packages, deploy, tag, or release. Preserve external controls as `NOT_YET_EXTERNALLY_VERIFIED_BY_OWNER`, phone transport OFF, clinical OFF, Health OFF, and HUMAN_UA_ASR `PARTIAL_OWNER_PILOT / OPEN`. Keep the original `INVALID_METADATA` cause marked unconfirmed.
