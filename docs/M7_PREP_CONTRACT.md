# M7_PREP_EVIDENCE_ADMISSION — preparation contract

Owner goal: prompts/M7_PREP_EVIDENCE_ADMISSION.md, base `7516c9487346d8c3f0cc0b6224bdfe7354f5153a`.
Одна bounded goal: offline registry/schemas/validator/tests/docs; M7 runtime і M8 NOT_STARTED.
Зовнішній report прочитано повністю, manifest 11 payloads перевірено до intake.
Plan Mode OFF. Робота не змінює application/runtime або permissions.

Canonical [registry](../research/admission/registry.json), [guide](../research/admission/README.md),
[зовнішні findings](../research/admission/external/REVIEW_FINDINGS.json),
[source ledger](../research/admission/external/PRIMARY_SOURCE_CHECKS.json).
Це receipt metadata, corrections і admission drafts; не reviewed clinical corpus.

## Review boundaries

16/16 RECEIVED_EXTERNALLY/native-extracted у ChatGPT. На цьому Mac originals не отримані
та їх байти не перевірені; RAW immutable і не входять у Git. Scope/consistency screen усіх
16 завершений зовні; primary checks вибіркові, full evidence review NOT_COMPLETED,
rights NOT_CLEARED_AS_A_WHOLE, content NOT_APPROVED, qualified clinical/legal review NOT_PERFORMED.
Source ledger передано без нових factual claims і без нового web/primary-source review.

27 findings збережено дослівно з raw locators та scope як external input. 27 derived decisions
інтегровано; content closed=0, OPEN=27. Підготовка не надає clinical activation.

## Corrections

| Finding | Packets | Derived decision / unresolved action |
|---|---|---|
| RG-01 | R01, R02, R03, R04, R05, R06, R07, R08, R09, R10, R11, R12, R13, R14, R15, R16 | Зберігати claimed_status окремо від reviewed_status, rights_status, content_status, technical_status і activation_status. |
| RG-02 | R09 | Методологію зберегти дослівно в оригіналі; у похідному реєстрі позначити search_execution/full_text_access як UNVERIFIED, доки немає перевірюваного evidence. |
| RG-03 | R16 | Перенести як requirements без execution PASS; evidence брати тільки з конкретних C/R tests та наступних фактичних перевірок. |
| RG-04 | R01, R03 | IRT лишити кандидатним, не активним. Не оголошувати всі vivid dreams показанням. Для обраного варіанта потрібні fidelity, safety, content/qualified review. |
| RG-05 | R03 | Окремі versioned guideline claims із population/outcome; не називати розбіжність доведеною різницею лише цивільні/військові. |
| RG-06 | R03 | Не присвоювати ефект trial нашій адаптації; описати її як новий кандидат зі своїм content/safety testing. |
| RG-07 | R03 | Стабільні source IDs за DOI/PMID/version. Не виправляти номер глобальним replace; звірити кожний claim. Superscript ref не є частиною DOI. |
| RG-08 | R02 | WASO лишається null; TST/SE лише за достатніх явно визначених inputs. Інтервал між часами показувати як інтервал, не виміряну тривалість сну. No silent imputation. |
| RG-09 | R01, R04 | Залишити sleep restriction/compression/titration OFF у V1; scripted stimulus-control призначення OFF. Освітній кандидат та будь-який поріг розглядати окремо, без висновку «нижче/вище порога — безпечно». |
| RG-10 | R05 | Залишити structured reflection draft; обмеження кількості запитань — product configuration, не клінічний cutoff. Позначити необхідність перевірити citation16. |
| RG-11 | R08 | Створити окремі source records; PMR claim перевірити за PMR-specific evidence. Не переносити pooled d у коротку вправу застосунку. |
| RG-12 | R08 | Позначити ці quantitative claims NEEDS_VERIFICATION; не називати змінену дозу дослідженою, не видавати physiological mechanism за гарантований ефект. |
| RG-13 | R06, R08 | Не називати exact 5-4-3-2-1 чи 3-2-1 validated treatment. Простий добровільний orientation flow — кандидат із власним wording і stop path після content review. |
| RG-14 | R07 | Зберегти optional user-chosen next step/rest/just-save як нейтральний UX-кандидат. BA, CMT і психодіагностика — окремі неактивні content кандидати. |
| RG-15 | R09 | Замінити цей висновок у похідному рішенні: human support не виключений архітектурою; він не є автоматично реалізованою функцією або permission на передачу даних. |
| RG-16 | R10 | Перший analytics scope — описові результати з coverage/provenance. Correlation/N-of-1 engine DEFER. Причини abstention повинні посилатись на перевірні властивості даних, не на прихований діагноз. |
| RG-17 | R05, R06, R07, R11 | Не писати ані «генеративна допомога доведено не працює», ані «інший бот пройшов trial — наш валідований». Зберегти model/intervention/population/comparator окремо. |
| RG-18 | R11, R16 | Не міняти provider, billing чи auth. Відкрити route-specific gate із plan/terms/data flow/consent/tool isolation. MiniMax Token Plan окремо UNVERIFIED. |
| RG-19 | R11, R16 | Account approval UNKNOWN; endpoint retention UNKNOWN до окремої перевірки. API не активувати як нібито автоматично приватніший fallback. |
| RG-20 | R02, R05, R06, R07, R16 | Реєстр на рівні exact instrument/version/language/use; policy checked ≠ license granted ≠ clinically validated. RRS chain-of-rights UNVERIFIED, не присвоювати іншого власника навмання. |
| RG-21 | R16 | Прибрати автоматичний exemption/CE-verdict у derived gate. Intended purpose і фактичний release scope описати; остаточний legal review позначити NOT_PERFORMED. |
| RG-22 | R16 | Підготувати карту data flows, не видавати blanket household exemption, controller або processor verdict. No account/legal/permission mutation. |
| RG-23 | R12 | Зберегти обидві provenance: research-author did not test; repo early hardware evidence існує. Не додавати HR/SpO2/history/background або health-to-AI context. |
| RG-24 | R13 | Окремий ADR/тести перед зміною accepted M1–M6. Наявність ignore/sandbox/HTTPS не дає абсолютного no-leak PASS; потрібні явний threat model та межі перевірки. |
| RG-25 | R14 | Engine/model licence та checksum перевіряти окремо; окремий authorized benchmark перед вибором. Ніяких downloads, cloud fallback або recorder/storage rewrite у M7_PREP. |
| RG-26 | R15, R01, R11 | Не сканувати creative vault для психологічного профілю. Відрізняти персонажа від користувача; обробляти явний user intent у поточній взаємодії. Видалення охоплює похідні дані згідно з existing retention contract. |
| RG-27 | R01, R02, R03, R04, R05, R06, R07, R08, R09, R10, R11, R12, R13, R14, R15, R16 | Зберігати proposed_expected; незалежно reviewed_expected з rationale. Клінічні labels/gold cases не підписувати як validated; mechanical gate cases можна тестувати окремо. |

Ці рішення не переписують RAW. R09 simulated provenance лишається UNVERIFIED; R16 [x]
не є exact-C execution. R03 citation20 collision потребує explicit per-claim mapping.
Claim-to-source linkage представляє review findings, а не вигаданий full RAW bibliography.
Missing WASO лишається null, interval не measured TST/SE; user confirmation не causal evidence.
Local-first не виключає voluntary human consultation й не дозволяє hidden sharing.

## Source checks

Namespaced IDs у цьому layer не змінюють старі project Sxx джерела.
Усі записи: external reviewer, checked 2026-10-03, local primary recheck NOT_RUN,
source bytes hash null. Нижче точні access extents; limits і locators у canonical ledger.

| Source | External access extent |
|---|---|
| gate:S01 | PUBLISHER_ABSTRACT_AND_POSITION_STATEMENTS |
| gate:S02 | OFFICIAL_PDF_TARGETED_TEXT_AND_PAGE_IMAGES |
| gate:S03 | PUBLISHER_FULL_TEXT_TARGETED_SECTIONS |
| gate:S04 | INDEXED_PRIMARY_ABSTRACT_METADATA |
| gate:S05 | PUBLISHER_AND_AUTHOR_REPOSITORY_ABSTRACT |
| gate:S06 | PUBLISHER_INDEXED_ABSTRACT |
| gate:S07 | PUBLISHER_ABSTRACT_METHODS_RESULTS |
| gate:S08 | RIGHTSHOLDER_PUBLIC_STATEMENT |
| gate:S09 | RIGHTSHOLDER_CURRENT_POLICY_PAGE |
| gate:S10 | OFFICIAL_GUIDANCE_PAGE |
| gate:S11 | OFFICIAL_STATUTORY_EXCERPT |
| gate:S12 | OFFICIAL_PDF_TARGETED_TEXT_AND_PAGE_IMAGE |
| gate:S13 | OFFICIAL_CURRENT_DOCUMENTATION |
| gate:S14 | OFFICIAL_CURRENT_DOCUMENTATION |
| gate:S15 | OFFICIAL_CURRENT_POLICY |
| gate:S16 | OFFICIAL_LANDING_METADATA_ONLY |

## Module dependency gates

Всі 16 — DRAFT_NOT_RUNTIME/OFF; жодного owner runtime consent/qualified signature.
Canonical missing_gates містить computed mechanical gates і всі finding dependencies.
Для кожного потрібні exact content/hash, applicability/rights, accountable content review,
technical evidence і separate activation permission. EXCLUDED_V1 та DEFERRED не є планом реалізації.

| Module / disposition | Research dependencies | Найменший наступний крок |
|---|---|---|
| journal_capture / NEUTRAL_EXISTING_SCOPE | R01, R02, R15 | У межах окремої goal визначити лише нейтральний capture scope та перевірити stop/edit/delete. |
| creative_organization / NEUTRAL_EXISTING_SCOPE | R11, R15 | Уточнити selection та fiction/user-intent boundaries без психологічного профілю. |
| sleep_education / CONTENT_REVIEW_REQUIRED | R01, R02, R04 | Підготувати exact UA educational draft без персональних sleep windows для content reviewer. |
| thought_record / EVIDENCE_AND_CONTENT_REVIEW_REQUIRED | R05, R06, R11 | Звірити R05 citation16 і сформувати exact добровільний draft для фахового review. |
| worry_rumination / EVIDENCE_AND_CONTENT_REVIEW_REQUIRED | R06, R09, R11 | Зіставити exact grounding claims і stop/skip wording, не створюючи diagnosis rule. |
| activity_self_kindness / EVIDENCE_AND_CONTENT_REVIEW_REQUIRED | R07, R09 | Відокремити нейтральну дію/rest від BA та перевірити claims обраного draft. |
| grounding_relaxation / EVIDENCE_AND_CONTENT_REVIEW_REQUIRED | R01, R08, R09 | Спершу розділити PMR/autogenic/mixed sources; обрати одну exact technique/dose. |
| dream_irt / QUALIFIED_CONTENT_REVIEW_REQUIRED | R01, R03, R11 | Розв’язати R03 citation20 collision, визначити fidelity/population/guidance перед qualified review. |
| weekly_descriptive_review / ANALYTICS_CONTRACT_AND_CONTENT_REVIEW_REQUIRED | R02, R10, R11, R12 | Визначити deterministic coverage/missing-data contract; health-to-AI потребує окремого дозволу. |
| exploratory_n_of_1 / DEFERRED | R10 | Залишити DEFERRED; перед окремою goal визначити hypotheses/coverage/confounding contract. |
| questionnaires / EXACT_RIGHTS_AND_CONTENT_REVIEW_REQUIRED | R02, R05, R06, R07, R16 | Вибрати exact instrument/version/UA translation/use; записати застосовну license/public permission або потрібний grant. |
| clinical_sleep_window / EXCLUDED_V1 | R01, R04 | Залишити EXCLUDED_V1; не створювати autonomous titration. |
| trauma_processing_diagnosis_medication / EXCLUDED_V1 | R01, R04, R05, R06, R07, R11 | Залишити EXCLUDED_V1; не реалізовувати autonomous clinical decisions. |
| live_ai_provider / SEPARATE_PERMISSION_AND_ROUTE_GATE | R11, R16 | Окремо описати route/plan/endpoint/consent/retention, потім отримати scoped runtime permission. |
| local_asr_real_model / SEPARATE_PERMISSION_AND_BENCHMARK_GATE | R14 | Окрема goal із exact engine/model/version/license/checksum та synthetic UA benchmark дозволом. |
| expanded_health_access / SEPARATE_PERMISSION_GATE | R12 | Залишити чинні 3 reads; перед private pilot виконати дозволений exact 0.6.1 smoke M6-N01. |

Pending claim блокує тільки залежний майбутній модуль. Existing accepted neutral journal/
creative functions не вимикаються. Clinical sensitive modules require QUALIFIED_CLINICAL_REVIEWER;
нейтральний content scope має окремого accountable CONTENT_REVIEWER. Нікого не призначено.

## Validation and invalidation

```sh
.venv/bin/python scripts/m7_admission.py
.venv/bin/python -m pytest -q tests/test_m7_admission.py tests/test_doc_tools.py tests/test_privacy_tools.py
.venv/bin/python scripts/check_docs.py --json
.venv/bin/python scripts/build_chatgpt_context.py
.venv/bin/python scripts/check_privacy.py --include-generated
```

CLI structural_status/exit code окремо від unresolved та active count. OFF/NOT_REVIEWED
не ховають malformed fields. Exact IDs/version/content, source/claim hash bindings, rights
scope/language, reviewer/date/role/scope й exact technical receipt обов’язкові; drift — fail closed.
Applicable public permission/license може закривати exact rights без redundant individual grant.
Approval shadow validation не є clinical sign-off або runtime activation.

Tests охоплюють G01–G24 як mechanical cases з independently contract-derived assertions,
не імпортують RAW responses як clinical gold. Інструменти offline; untrusted text — data.
Permissions збігаються з .project/project.json; live AI/deploy/clinical/general real data OFF.

M6 зовнішній ACCEPT лише engineering + bounded early 0.6.0 hardware; M6-N01 OPEN,
final 0.6.1 hardware NOT_RUN. Деталі: [запис review](../reports/M6_ARCHITECT_REVIEW.md).
Немає ADR deviation, змін journal/health schemas, recorder/crypto/storage/transport/provider.

C → exact-C relevant checks → evidence-only R → privacy/staged review → normal fast-forward
main push → origin/main==R. Preparation завершується AWAITING_REVIEW без власного ACCEPT.
Browser/web/Android/full application rerun NOT_RUN: жодного application change.
