import React from "react";
import { names, typed, fieldNames, type Draft } from "./journal-ui";
export function EntryEditor({
  title,
  draft,
  change,
  save,
  cancel,
  busy,
  saveLabel,
  onRefresh,
}: {
  title: string;
  draft: Draft;
  change: (key: keyof Draft, value: string) => void;
  save: (e: React.FormEvent) => void;
  cancel: () => void;
  busy: boolean;
  saveLabel: string;
  onRefresh?: () => void;
}) {
  return (
    <section className="editor" aria-label="Редактор запису">
      <h2>{title}</h2>
      <form onSubmit={save}>
        <label>
          Текст
          <textarea
            aria-label="Текст"
            autoFocus
            rows={5}
            value={draft.raw_text}
            onChange={(e) => change("raw_text", e.target.value)}
            required
            maxLength={100000}
            placeholder="Що хочеться записати?"
          />
        </label>
        <label>
          Розділ
          <select
            aria-label="Розділ"
            value={draft.type}
            onChange={(e) => change("type", e.target.value)}
          >
            {Object.entries(names).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
        <details open={draft.type !== "inbox"}>
          <summary>Деталі запису</summary>
          <label>
            Теги через кому
            <input
              value={draft.tags}
              onChange={(e) => change("tags", e.target.value)}
            />
          </label>
          <label>
            Часовий пояс IANA
            <input
              value={draft.timezone}
              onChange={(e) => change("timezone", e.target.value)}
            />
          </label>
          <label>
            Точність часу
            <select
              aria-label="Точність часу"
              value={draft.time_precision}
              onChange={(e) => {
                change("time_precision", e.target.value);
                change("occurred_at_utc", "");
                change("local_date", "");
              }}
            >
              <option value="unknown">Час невідомий</option>
              <option value="date">Лише дата</option>
              <option value="instant">Точний час зі зсувом</option>
            </select>
          </label>
          {draft.time_precision !== "unknown" && (
            <label>
              Дата події
              <input
                type="date"
                value={draft.local_date}
                onChange={(e) => change("local_date", e.target.value)}
              />
            </label>
          )}
          {draft.time_precision === "instant" && (
            <label>
              Час ISO з UTC-зсувом
              <input
                value={draft.occurred_at_utc}
                onChange={(e) => change("occurred_at_utc", e.target.value)}
                placeholder="2026-09-30T12:00:00+02:00"
              />
            </label>
          )}
          {typed[draft.type].map((key) => (
            <label key={key}>
              {fieldNames[key]}
              {key === "creative_kind" ? (
                <select
                  aria-label="Вид ідеї"
                  value={draft.creative_kind}
                  onChange={(e) => change("creative_kind", e.target.value)}
                >
                  <option value="">Не визначено</option>
                  {[
                    ["idea", "Ідея"],
                    ["scene", "Сцена"],
                    ["character", "Персонаж"],
                    ["theme", "Тема"],
                    ["phrase", "Фраза / діалог"],
                    ["shot", "Кадр"],
                    ["list", "Список"],
                    ["reference", "Референс"],
                    ["other", "Інше"],
                  ].map(([k, v]) => (
                    <option key={k} value={k}>
                      {v}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={
                    key.endsWith("rating") || key === "sleep_quality"
                      ? "number"
                      : "text"
                  }
                  min={0}
                  max={10}
                  step={1}
                  value={draft[key as keyof Draft]}
                  onChange={(e) => change(key as keyof Draft, e.target.value)}
                  placeholder={
                    key.endsWith("_utc")
                      ? "2026-09-30T07:00:00+02:00"
                      : "Невідомо · можна пропустити"
                  }
                />
              )}
            </label>
          ))}
          {draft.type === "sleep" && (
            <p className="hint">
              Час — ваша оцінка. Інтервал між початком і пробудженням не вимірює
              фактичний сон. Дата запису визначається за пробудженням, якщо час
              відомий.
            </p>
          )}
        </details>
        <div className="actions">
          <button className="primary" disabled={busy}>
            {busy ? "Зберігаємо…" : saveLabel}
          </button>
          <button type="button" onClick={cancel}>
            Скасувати
          </button>
          {onRefresh && (
            <button type="button" onClick={onRefresh}>
              Завантажити актуальну версію
            </button>
          )}
        </div>
      </form>
    </section>
  );
}
