# ADR-002 — HTTPS/private-origin candidate, not activation

Status: **candidate chosen; real transport OFF / HARDWARE_UNVERIFIED**. Sources checked
2026-10-01. No system CA, Keychain change, router port, account, tunnel, daemon or deploy done.
Galaxy S24 Ultra/Chrome actual test NOT_RUN. Backend default still binds 127.0.0.1.

| Candidate | Trust/TLS and Android | Dependencies/cost/privacy/revocation | Offline/operations |
|---|---|---|---|
| Private DNS + local CA leaf | Owner-managed CA/renewal; Android certificate trust/installability must be tested, not assume warning bypass | Router/private DNS and owner device trust changes required; no mandatory cloud, own operational cost; rotate/remove CA and pairing credentials | Installed shell offline; local API only while route/valid TLS works; highest manual certificate burden |
| Private DNS + public CA DNS-01 leaf | Publicly trusted leaf on owned domain, split DNS/private address; test Android/browser LNA and WebAPK | Domain/DNS administration and ACME renewal permissions; public CT/name disclosure, recurring domain/account dependency; revoke leaf/pairing, rotate DNS | Cached shell offline; local network routing and certificate lifecycle need monitoring |
| **Tailscale Serve + MagicDNS HTTPS** | Private tailnet origin, automatic HTTPS provisioning; Android Tailscale client + valid Chrome/PWA TLS must be verified | Owner-approved account/client installation/HTTPS settings required; published Personal tier can be free subject to eligibility/limits, actual entitlement not checked; metadata/CT disclosure, VPN/control/relay dependency; device/pairing/access-policy revocation | Cached PWA works offline; sync requires reachable Mac and permitted tailnet route; certificate/service lifecycle is simpler but provider-dependent |

Candidate for next scoped hardware gate: **private tailnet Serve HTTPS**, after permission and
eligibility review. Serve and Funnel differ: Funnel is public and is not this candidate.
No executable setup command is prescribed here before owner grants the required route/account/
client/system permissions. Future route must retain exact origin/Host, bearer/device/epoch auth,
CSP and revocation; present implementation intentionally accepts only loopback harness origin.

Public Vercel shell is not an equivalent: remote JS gains access to unlocked browser data/key,
adds cross-origin credential/CORS/CSP/update trust, and may need Local Network Access permission.
Plain LAN HTTP is not an acceptable phone secure-context/HTTPS replacement. A private IP alone
establishes neither TLS trust nor authenticated local API access.

Synthetic test harness uses generated short-lived localhost certificate/private key under an
ignored dedicated path and ephemeral browser test flags only. This does not install trust and
is never an Android/private-transport acceptance. No browser security bypass instructions for
actual users. Same-origin localhost HTTP smoke is also a browser secure-context testing exception,
not a phone-to-Mac route: localhost on the phone means the phone itself.

Primary references: [Tailscale Serve](https://tailscale.com/docs/features/tailscale-serve),
[HTTPS/CT lifecycle](https://tailscale.com/docs/how-to/set-up-https-certificates),
[pricing](https://tailscale.com/pricing), [Chrome Local Network Access](https://developer.chrome.com/blog/local-network-access),
[secure contexts](https://www.w3.org/TR/secure-contexts/),
[Android network security configuration](https://developer.android.com/privacy-and-security/security-config),
[ACME challenge types](https://letsencrypt.org/docs/challenge-types/).
Each candidate still needs real Chrome/version/router/account verification. No S24 timing/security claim.
