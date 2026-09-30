# Передача контексту — M0 direct-main finalization

Дата: 2026-09-30. Local branch `main`, на R3
`ca0e1fc3af42bcc31e4038a591f7356713718005` (history derived from the current reviewed M0).
M0 workflow normalization у роботі; M1/application NOT_STARTED.

Owner decision надає standing permission на normal fast-forward push у public `main`
для кожної окремої `/goal` після local checks. `push_main` окремий від merge/deploy/provider/
private-data permissions. Review branch optional; стара `review/m0-bootstrap` лишається
історичною гілкою з C2/R2/R3.

C2/R2/R3 залишаються незміненими. C3 нормалізує .project permissions у schema v2, STATE,
AGENTS/WORKFLOW, README, instructions і synthetic tests. R4 буде evidence-only.
Після privacy scan відправити C3/R4 одним normal fast-forward `git push -u origin main`;
перевірити `origin/main` SHA і actual GitHub default branch `main`.

Немає дозволу на M1, merge, force-push, tag/release, deploy, provider/billing/auth
change, private-data access або clinical activation. Після push — architect review точного
C3/R4 SHA; наступний milestone потребує окремої owner goal.
