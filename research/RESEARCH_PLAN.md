# План deep research — 16 пакетів

Кількість пакетів не дорівнює кількості агентів. Це окремі дослідницькі питання з
перевірюваним виходом. **R01–R16 RECEIVED_EXTERNALLY у ChatGPT та scope/consistency screened.** Локально originals
не отримані; primary checks partial, content/clinical approval NOT_PERFORMED.
Canonical metadata: [admission registry](admission/README.md); bulk active promotion FIX_REQUIRED.

## Пріоритет

Почати R01, R02, R11, R13 та public-rights частину R16. Паралельно можна будувати M1
на нейтральних формах/синтетичних даних, не активуючи клінічні claims.
Після них R03–R10. Hardware/voice/creative research R12/R14/R15 не блокують базовий journal.
M7 підключає лише ті протоколи, для яких виконані всі потрібні content/evidence gates.

| ID | Тема | Пріоритет | Для чого |
|---|---|---|---|
| R01 | [Межі самодопомоги, первинна орієнтація й безпека](prompts/R01.md) | P0 | M7 activation; базові межі M1/M3 |
| R02 | [Щоденники сну, стану та мінімальні вимірювання](prompts/R02.md) | P0 | M1 data contract; M7 content |
| R03 | [Imagery Rehearsal Therapy: придатність і fidelity](prompts/R03.md) | P1 | M7 dream_irt |
| R04 | [CBT-I: складові та межі цифрової самодопомоги](prompts/R04.md) | P1 | M7 sleep education; restricted components OFF |
| R05 | [КПТ-запис думок і альтернативні погляди](prompts/R05.md) | P1 | M7 thought_record |
| R06 | [Тривожні думки, worry і rumination](prompts/R06.md) | P1 | M7 worry_rumination |
| R07 | [Низький настрій, прокрастинація, самокритика й посильні дії](prompts/R07.md) | P1 | M7 activity_self_kindness |
| R08 | [Заземлення, релаксація та вечірня напруга](prompts/R08.md) | P1 | M7 grounding_relaxation |
| R09 | [Навантага, домашні завдання, нагадування й м’яка гра](prompts/R09.md) | P1 | M5/M7 UX |
| R10 | [Персональна аналітика та обережні N-of-1 гіпотези](prompts/R10.md) | P1 | M7 weekly_review |
| R11 | [Безпека розмовного AI, пам’яті та зміни моделі](prompts/R11.md) | P0 | M3/M7 |
| R12 | [Samsung wearable: доступ, якість і обмеження показників](prompts/R12.md) | P2 | M6 |
| R13 | [Local-first, приватність, PWA sync і переносимість](prompts/R13.md) | P0 | M0/M1/M2 |
| R14 | [Локальне голосове введення українською](prompts/R14.md) | P2 | M4 |
| R15 | [Творчий щоденник, capture і повсякденна увага](prompts/R15.md) | P2 | M3/M5; пізніші routines |
| R16 | [Права, приватні дані та майбутня комерціалізація](prompts/R16.md) | P0 для public repo; P2 для SaaS | До публікації матеріалів/публічного продукту |

## Метод дослідження

Спершу прочитати `MASTER_RESEARCH_PROMPT.md`, потім конкретний `prompts/Rxx.md`.
Шукати не підтвердження бажаної ідеї, а придатність методу, обмеження й негативні результати.
Для technical тем — офіційна документація/код і вимірювання; для клінічних — guidelines,
systematic reviews та primary studies. Статті блогерів/AI-конспект не є primary evidence.

У кожного ключового claim: джерело/DOI або стабільний URL, точний розділ/сторінка,
досліджена популяція й формат, outcome/effect/uncertainty, обмеження, licensing status.
Розділити guided therapy, self-help, validated digital protocol і generative AI adaptation.
Для невідомого — `NOT_VERIFIED`; не вигадувати дані, дози або протипоказання.

## Вихід пакета

```text
research/reviewed/Rxx/            # тільки після rights/sensitivity gate
  README.md                     # рішення для продукту, не великий переказ
  evidence.tsv                  # studies/claims matrix
  sources.json                  # бібліографія, retrieved_at, local locator
  protocol_draft.json            # лише для content-пакетів; не активний протокол
  safety.md
  uncertainties.md
  eval_cases.jsonl
  rights.md
  review.md                     # reviewer/status/scope, не самопризначене APPROVED
```

У technical пакеті замість protocol_draft — `design_candidate.md` і reproduction/test plan.
Raw PDF/DOCX/images і чужі книги спочатку у quarantine поза Git. Public repo може містити
посилання та власний допустимий синтез; файли лише після підтвердження прав.
Не завантажувати особисті щоденники в Gemini/NotebookLM для дослідження загальних методів.

## Ingestion і статус

RECEIVED → QUARANTINED → RIGHTS_CHECKED → MAPPED → EVIDENCE_REVIEWED → CONTENT_REVIEWED.
Наукове review не виконує permission/clinical activation автоматично.
Кожна нова версія має change summary, file hashes і claims affected. Citation drift після
зміни джерел — причина re-review. Зберігати незгоди між джерелами, не маскувати їх.

Критерій достатності — відповідь на потрібне продуктове питання з доказами й межами,
а не формальна кількість робіт або мегабайтів. Остаточне рішення про clinically sensitive
self-help candidate переглядає відповідний фахівець, не лише research-модель.
