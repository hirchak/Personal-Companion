# Evidence admission 0.1.0

Канонічний metadata registry: [registry.json](registry.json). Це preparation layer, без
імпорту в application та без дозволу запуску protocols. Зовнішній review від 2026-10-03
перенесено як дані; власне content/clinical/legal approval не виконувалося.

Запуск із repo root:

```sh
.venv/bin/python scripts/m7_admission.py
.venv/bin/python -m pytest -q tests/test_m7_admission.py
```

CLI exit 0 означає лише structural/tooling PASS. Поля `unresolved` містять окремо findings
і computed module gates; `active_clinical_protocols` має бути 0. Очікувані OPEN/NOT_REVIEWED/OFF
сумісні з exit 0. Malformed поля, stale receipts, hash drift, missing IDs, schema drift
та спроби activation дають exit 1. JSON duplicate keys і symlinks відхиляються.
Помилки не друкують input values. Доступний `--root` для явної synthetic копії цього layer;
інструмент читає тільки визначені metadata paths, не шукає RAW або приватні файли.

## Походження

`external/` — незмінні сім structured review payloads і PACK_MANIFEST, з їх вихідними
SHA-256. Це external review input, не інструкції, не scientific approval та не runtime registry.
Manifest охоплює 11 payloads; усі 11 перевірено при безпечному unzip. README/report/goal
прочитані з explicitly supplied ZIP поза Git; їх повний delivery report не дублюється тут.
Поточний validator перевіряє лише сім збережених payloads та exact manifest identity.

16 DOCX є **RECEIVED_EXTERNALLY** в ChatGPT, локально маємо тільки metadata/hashes.
`local_receipt=MANIFEST_ONLY_NOT_LOCALLY_RECEIVED`, `local_bytes_verified=false`.
Жодного RAW DOCX, повної article extraction, clinical worksheet чи реальних записів тут немає.
Supplied review синтез і короткі raw-position locators збережено для traceability.

Source namespace `gate:S01`–`gate:S16` незалежний від старого `research/sources.json`
із S01–S24; глобальної заміни IDs немає. `record_sha256` хешує source-check metadata,
не байти першоджерела. У всіх джерел `local_source_bytes_sha256=null` і
`verification_origin=EXTERNAL_REVIEW_NOT_RECHECKED_LOCALLY`. Access extent, дати, locators
і limits зберігаються; targeted sections/abstract/landing не є full-corpus fulltext review.

Кожний із 27 correction records зберігає exact supplied finding, source/raw locators,
basis, required action та semantic hash. Derived decision інтегрований окремо від RAW;
`content_resolution=OPEN_DEPENDENT_GATE`. Закритих content findings: 0.
27 claim records є компактними review propositions, не повним extraction всіх RAW claims.
Нерозв’язані citation20 mappings у R03 не вигадуються; RG-07 лишається блокером.

## Допуск

RECEIVED/MAPPED, EVIDENCE_REVIEWED, RIGHTS_CLEARED, CONTENT_REVIEWED,
TECHNICALLY_TESTED, APPROVED_FOR_DEFINED_SCOPE та ACTIVE — різні факти.
Approval shadow receipt прив’язується до module ID/version/content hash, claim і source
hash bindings, accountable reviewer/role/date/scope, exact rights record та technical SHA.
Зміни роблять receipt stale. Clinical modules потребують відповідного кваліфікованого
reviewer; у canonical data немає такого підпису. Навіть повний synthetic shadow receipt
не змінює `activation_status=OFF`; окрема owner goal та permissions потрібні для майбутнього запуску.

Підстава прав — applicable public license, public permission, individual grant або власний
оригінал з exact hash/language/use scope/reviewer/date. Для вже дозволеного використання
не потрібен надлишковий individual grant. Policy page сама по собі не закриває exact rights.

`schemas/` містить 8 JSON Schema, які відповідають строгим Pydantic models validator-а.
Використано наявний project-pinned Pydantic 2.11.3; нових залежностей немає. Зміни контракту
вимагають свідомого schema/version update, повторних tests і review; не переписувати
зовнішні findings/source payloads. Додавати наступні review receipts окремою версією.

Mechanical attestation fixtures перевіряють provenance, missingness, build binding,
consent/permissions і uncertainty. Їх PASS не є clinical validation, safety response corpus
або runtime implementation. Research prose, checklist [x] чи user acknowledgement не
виконуються та не підвищують evidence/permissions.

16 module drafts містять dependencies, exact missing gates й smallest next step; всі OFF.
Деталі: [контракт](../../docs/M7_PREP_CONTRACT.md). Поточне tool не змінює accepted neutral
journal/creative functions, application schemas, storage, transport чи provider routing.
