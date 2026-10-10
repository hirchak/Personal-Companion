# M8F C11 — documentation preservation recheck

Implementation: `23bcb16a0d33e4d86377ad60c4fcce216f8c808d`.
Previous documented UI: C10 `af24526d1a5703dbbb197c5b8487360714c5d92b`.
Classification: **ordinary extension / preserve and refine**, Mode Operate.
Result: **incumbent design preserved in the inspected integration**.

Перевірено clean source tree і exact HEAD C11. Прочитано повний C10→C11 source diff:
`ComposerVoice.tsx` і `VoicePanel.tsx` отримали невізуальні Boolean
`data-native-unsaved` attributes; `PersonalCompanion.swift` враховує їх перед update.
Початок запису, RECORDING/SAVING та memory draft тепер утримують заборону оновлення.
Додано browser regression test; palette, styles, component composition, typography,
runtime/store, maintenance і failure UI у цьому forward diff не змінені.
Diff C10→C11 для `docs/PRODUCT.md`, `docs/DESIGN.md`, stylesheet, `main.tsx` і
`native-macos.ts` порожній (exit 0). Попередній documentation check прочитано повторно.

Відкрито всі шість наданих C11 screenshots у `generated/m8f/ui/`:
`voice-guard-C11.png`, `wrong-signer-C11.png`, `error-settled-C11.png`,
`update-confirm-C11.png`, `update-busy-C11.png`, `post-update-C11.png`.
Guard показує чинний AppKit alert із дією збереження чернетки/завершення запису;
wrong-signer — failure/recovery alert; settled error залишається у native bar.
Update підтверджується однією кнопкою; busy має spinner і disabled open, web content
навмисно прихований; після relaunch видно incumbent locked paper/sage/Georgia surface.
Назви станів узгоджуються з відкритими зображеннями. Pixels самі по собі не доводять
signer rejection, source identity, ASR або update data preservation.

## П'ять рядків системи

1. Palette: теплий paper, темний ink і muted sage; AppKit blue залишається платформним accent.
2. Type: успадковані Georgia headings/system body та системні AppKit dialogs/menu.
3. Layout: центрований lock surface, компактна native status/action bar, окремий content host.
4. Components: incumbent web actions і стандартні NSAlert/NSButton/NSProgressIndicator.
5. Rules: local-first, explicit consent/send/update, truthful recovery, protected unsaved state і locked relaunch.

## Межі

Файли PRODUCT/DESIGN збережено. Новий світ/system change відсутній, sidecar/brief
не створено. На початку M8F наявний prose-only DESIGN без нового token frontmatter,
missing root `.impeccable/design.json` та separate native surface brief залишаються
pre-existing drift; жоден дефект або одноразовий статус не канонізовано.
Це documentation preservation check; C10 finish verdict **ship** стосувався вузької
native integration й двох C9 fixes. Цей recheck не є новим whole-product acceptance.

Executor повідомив targeted browser 21/21, actual C11 Finder/DMG A101→B102 і packaged
ASR PASS. Цей pass їх не запускав і не видає screenshots за незалежну перевірку
цих результатів. Початковий synthetic GUI-start був stuck/canceled, **не PASS**.
Legacy voice panel прихований у PRIVATE_LOCAL за заданим scope; screenshot guard
не доводить фізичний microphone capture або human ASR quality.
Minimum-window responsive, keyboard/focus/VoiceOver, production LocalAuthentication,
physical microphone, production signing/notarization/distribution залишаються
UNVERIFIED/NOT_RUN у цьому pass.
Немає GUI дій, pilot/vault reads, provider calls, detector/rebuild/polish чи source edits.
Єдиний write цього recheck — цей файл; C10 documentation evidence не перезаписано.
