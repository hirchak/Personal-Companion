# M8F C10 — documentation check

Implementation: `af24526d1a5703dbbb197c5b8487360714c5d92b`; incumbent base: `f32038f62e276400c41fb21c76ce753316b7aaa7`.
Classification: **ordinary extension / preserve and refine**, Mode Operate.
Result: **incumbent system preserved within the inspected native integration**.

Перевірено shipped Impeccable `reference/document.md`, definition `impeccable_documenter`,
`docs/PRODUCT.md`, `docs/DESIGN.md`, `docs/M8F_CONTRACT.md`, поточну goal,
`apps/macos/PersonalCompanion.swift`, `apps/web/src/style.css`, native branches у
`apps/web/src/main.tsx` і `apps/web/src/native-macos.ts`.
Git на початку pass: clean `main`, exact C10. Diff base→C10 для PRODUCT, DESIGN та
web stylesheet порожній (exit 0). На завершення цього pass source/system edits відсутні.

## Перевірені докази

Відкрито сім наданих C10 screenshots у `generated/m8f/ui/`: consent, update-confirm,
update-busy, backup-completed, update-error, update-error-settled, post-update.
Перші та error/confirmation captures показують стандартні AppKit alerts;
settled backup/error і post-update — успадкований web lock surface.
Busy capture має навмисно прихований приватний web content, видимі назву перевірки,
spinner та disabled open. Screenshot є доказом стану, а не responsive/interaction test.
Finish verdict `generated/m8f/ui-verdict-C10.md` — **ship** для вузької native інтеграції
та двох C9 fixes; документаційний pass не розширює його на весь продукт.

| Incumbent rule | Реалізація C10 / preserve evidence |
|---|---|
| Quiet paper / ink / sage | Незмінний stylesheet: background `#f7f7f0`, lock ground `#e9eee2`, ink `#28372f`, accent `#335945`, paper `#fffef9`; lock surface повторно видно після backup/update/failure. |
| Georgia invitation + system body | Web heading збережено; native welcome використовує Georgia 32 і system body 16. NSAlert та menu залишають стандартну AppKit типографіку. |
| Зрозуміла локальна дія | Native branch змінює спосіб підтвердження доступу й пояснення, зберігаючи incumbent lock composition та primary action. Bridge передає лише дію `unlock`. |
| Платформні affordances | Resizable NSWindow, стандартні rounded NSButton, NSAlert, NSMenu та NSProgressIndicator; системний blue alert action не переноситься до palette вебчастини. |
| Явний consent і recovery | Consent перед empty-root creation; одна «Оновити» перед prepare/install; помилка й доступ до папки копій явні, failure message зберігається після alert; relaunch заблокований. |

## П'ять рядків системи

1. Palette: теплий paper, темний ink, muted sage; стандартний AppKit accent лише у native controls.
2. Type ramp: system body 16; Georgia web heading 32–48, native welcome 32; dialog/menu type системний.
3. Layout: incumbent центрований lock surface; компактна native status/action bar і окремий content host.
4. Shapes/depth: web buttons 8px і minimum 44px; native controls/sheets використовують AppKit materials.
5. Rules retained: local-first, explicit consent/send/update, quiet hierarchy, visible status, protected locked state.

## Межі та pre-existing drift

`docs/DESIGN.md` містить історичну prose guidance без нового token frontmatter;
root `.impeccable/design.json` і окремий `m8f-native-shell` surface brief відсутні.
Це наявний documentation/schema drift; за заданою межею він лише зафіксований.
Новий світ або approved system change не виконувались: PRODUCT/DESIGN збережено,
sidecar/brief не створено, native blue чи одноразові maintenance values не канонізовано
як нові web tokens. Візуальний scope визначають чинний DESIGN і M8F contract.

Minimum 760×600, інтерактивні keyboard/focus/VoiceOver, production LocalAuthentication,
physical microphone/human ASR, усі unlocked web стани C10, production signing/notarization,
hosting/distribution лишаються UNVERIFIED/NOT_RUN у цьому pass.
Backup busy pixels окремо не надані; worker/source evidence не замінює їх.
Consent screenshot не доводить production owner consent чи authentication.
Немає GUI дій, provider calls, pilot/vault reads, detector/rebuild або source edits.
Цей файл є єдиним write документаційного pass.
