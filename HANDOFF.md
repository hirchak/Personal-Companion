# Передача контексту — M0 corrective

Дата: 2026-09-30. M0 corrective in progress; M1/app NOT_STARTED.
Repository https://github.com/hirchak/Personal-Companion.git підтверджений public,
default `main`; write permission доступний. Локальна branch `review/m0-bootstrap`;
push branch дозволений. Main merge, deploy, provider calls, real data — OFF.

## Відновлення

Прочитати AGENTS/STATE, canonical `.project/project.json`, `docs/WORKFLOW.md`,
потім M0 report та `docs/M1_CONTRACT.md`. Перевірити branch/HEAD/status/diff.

## Canonical source recovery

Із owner ZIP вибірково прочитано тільки `.gitignore`, `.project/context_map.json`
і `.project/project.json`. Перші два hashes збігаються з наданими очікуваннями;
canonical project schema, authority/snapshot_policy збережено, застосовані лише
owner-specified repo/default/review/permissions. Canonical snapshot names відновлено.
В архіві не було DOCX; raw research content не відкривався і не додавався.
Evidence: `reports/evidence/M0/CANONICAL_STARTER_VERIFY.json`.

## Межі і наступний крок

M1 contract лишається proposal; окрема goal обов’язкова. App/real vault/research
source documents/provider runtime/merge/deploy не чіпали. Після C2 пройти всі checks,
створити evidence-only R2 і normal push тільки `review/m0-bootstrap`; перевірити remote
ref. Історію не переписувати, main не створювати.
