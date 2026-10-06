# M8E existing-owner preflight diagnosis

This is a bounded follow-up within the externally accepted M8E product scope, not a new milestone.

## Goal

Diagnose the previously reported exact-C4 `private-preflight` result `INVALID_METADATA` without bypassing any gate or exposing private values. Run synthetic reproduction first. If the failure does not reproduce synthetically, use only the owner's explicit read-only structural/integrity authorization for the existing PRIVATE_LOCAL root and its verified protected backup.

## Privacy and activation boundaries

- Read only receipts, release metadata, SQLite schema/integrity metadata, and typed-validator results required by the existing preflight. Private rows may be parsed in memory by those validators only.
- Diagnostic output may contain only fixed stage labels, stable error codes, schema/journal-mode values, and WAL/SHM presence. Never emit private values, IDs, paths, receipts, hashes, record-derived filenames, exception messages, or raw SQL results.
- Do not call providers, inspect conversations, create real conversations/messages, record audio, change account settings, enable phone/Health/clinical features, or alter the protected backup.
- Do not run the existing-vault upgrade as part of diagnosis. Preserve the exact fail-closed preflight and all typed validators.

## Current checkpoint

The exact accepted C4 preflight now passes on the existing root and on the verified backup snapshot. The root is in WAL mode with WAL/SHM sidecars. The earlier `INVALID_METADATA` result did not reproduce; its original cause is unconfirmed. Sanitized stage callbacks and synthetic regressions are available in the current candidate. Existing-owner activation remains blocked pending independent review; do not upgrade until that review accepts the diagnostic candidate and activation is separately resumed.
