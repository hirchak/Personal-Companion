# Goal card: <milestone>/<task>

Model: <перевірений ID або label>
Reasoning: <підтримуваний effort>
Plan Mode: <ON лише planning / OFF execution>
Baseline: <repo/ref/base SHA>
Implementation scope: <одна узгоджена ціль>

## Результат
<Що має працювати для користувачки або розробки після цієї цілі.>

## Inputs / authority
<Конкретні specs, ADR, report, approved protocol IDs.>

## Межі
<Що не змінювати, які системи/дані/інтеграції не торкати.>

## Дозволи
<Local edits/tests/commit; scope дозволеного push; кількість/обсяг live calls якщо дозволено;
конкретний deploy target або OFF. Без невизначеного «роби все».>

## Definition of Done
<Сценарії, тести, evidence, documents. Результати, не мікроменеджмент команд.>

## Hard stops
<Зміна приватності/клінічної authority, додаткові витрати, незворотні операції,
невідомий dirty worktree або boundary change.>

## Повернути
Один звіт за шаблоном, STATE/HANDOFF/devlog, C/R SHA, push/CI status.
Не приймати власну роботу і не починати наступний milestone.

## Короткий запуск
/goal Виконай <task> за <path>. Дотримуйся AGENTS.md і меж ТЗ; завершення — review-ready evidence, не автоматичний наступний етап.
