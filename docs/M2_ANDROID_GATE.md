# M2-A12 — Galaxy S24 Ultra scoped manual gate

Current status: **HARDWARE_UNVERIFIED / NOT_RUN**. Reference phone already known; Watch7/health
not accessed. Desktop mobile viewport or test certificate exception is not Android acceptance.
No real private content until separate hardware/security/privacy gate and data-owner consent.

Before run, owner approves selected private HTTPS route/account/client permissions separately.
Do not install CA/change Keychain/router/expose LAN/use Funnel/deploy as a hidden prerequisite.
Record actual phone OS, Chrome/PWA version, app shell/storage version, route/TLS trust and exact
reviewed code SHA. Use invented SYNTHETIC notes only; sanitize identifiers/screenshots.

1. Open stable private Mac HTTPS origin in Chrome; no certificate warning/bypass. Confirm
   app manifest/install action and standalone launch on home screen. Check LNA/OS prompts.
2. Create local passphrase, pair with owner-issued one-use invitation; invalid/reused invitation
   must fail. Confirm distinct device label, persistence request result and scope warning.
3. Disable phone/Mac route, create/edit/delete multiple typed notes across midnight/DST/zone;
   stop PWA, force-close browser, relaunch/reboot phone, unlock and confirm outbox/text survives.
4. Return route, sync; deliberately lose response/retry using controlled harness, verify one
   server effect/receipt. Check truthful phone-only/pending/Mac states, no background guarantee.
5. Edit same base on phone and Mac/second device. Confirm both variants shown, no silent overwrite;
   choose Mac, phone and manual merge in separate fixtures, verify new revision operations.
6. Mac delete while phone stale; reconnect must not resurrect ID. Offline phone delete + retry
   must remain deleted. Retention/epoch rotation/old-backup restore require re-pair/reconciliation.
7. Install waiting shell update with pending outbox; interrupt network during install, then
   recover and apply explicit update. Confirm encrypted queue intact; incompatible storage/schema
   must refuse without wipe. Test open/upgrade/quota failure and retained unlocked draft.
8. Inspect storage persistence/pressure behavior; clear browser data explicitly after encrypted
   recovery export. Show empty/recovery state, wrong passphrase rejection, no silent Mac merge.
9. Revoke device at Mac; new sync fails, offline copy remains (no remote-erase claim). Forget
   phone copy only after explicit warning/export choice. Lock/wake clears displayed/decrypted state.
10. Audit browser/backend console/network and persisted records/recovery artifact; no note/tag/
    credential plaintext outside allowed metadata, no analytics/provider/cloud requests.

Acceptance evidence: timings, commands/actions, exact SHA, actual hardware environment,
expected/actual state, PASS/FAIL/NOT_RUN per item and sanitized paths. Keystore/OS-level storage,
backup/key recovery, XSS/update trust, passphrase usability and threat model need explicit owner
and accountable security review; synthetic WebCrypto tests do not authorize private rollout.
