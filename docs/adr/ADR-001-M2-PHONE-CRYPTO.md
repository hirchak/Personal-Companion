# ADR-001 — synthetic phone store encryption

Status: implementation decision inside M2; **real data NOT_APPROVED / HARDWARE_SECURITY_UNVERIFIED**.

Use native WebCrypto PBKDF2-HMAC-SHA256 (600,000 iterations), 128-bit random salt and
nonextractable AES-256-GCM CryptoKey. Per encryption 96-bit cryptographically random IV,
128-bit authentication tag; no Math.random, no hardcoded passphrase/key. Passphrase minimum
12 characters, supplied locally. Salt/KDF/schema/random device identity are public metadata.
AAD binds format/schema/device/revision and dedicated recovery purpose. IndexedDB stores only
metadata + ciphertext/IV; notes/tags/outbox/credential live inside ciphertext. Derived key and
cleartext live only in unlocked memory. Every mutation reads latest state and writes encrypted
entry+operation atomically with revision CAS; cross-tab races cannot silently overwrite.

Lock/reload discards key/decrypted UI. Lost passphrase has no bypass/recovery escrow: require
saved encrypted recovery artifact plus its passphrase, otherwise forget/re-pair with explicit
loss warning. Recovery contains unsynced records only and excludes credential; import is explicit,
creates an unpaired recovery state and never automatically merges/replays to Mac.

Limitations: browser XSS/unlocked JS, malicious same-origin update, compromised OS, passphrase
entropy, memory copies, best-effort IDB/cache eviction and rollback of whole browser storage are
not solved by application encryption. No Android Keystore/hardware-backed claim. Native/hardware
review, lock/wake, backups, entropy/usability and authenticated transport are separate real-data gates.

Primary references (checked 2026-10-01): [WebCrypto Recommendation](https://www.w3.org/TR/2017/REC-WebCryptoAPI-20170126/),
[OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html),
[IndexedDB](https://www.w3.org/TR/IndexedDB/). PBKDF2 choice uses available native primitive;
this is no claim that a browser-only passphrase meets Android hardware-secure storage acceptance.
