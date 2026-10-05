import { useEffect, useRef, useState } from "react";
import { Sheet } from "./Sheet";
export type ContextSelection = {
  type: "GOAL_START" | "LAST_7_DAYS" | "LAST_30_DAYS" | "CUSTOM";
  timezone: string;
  window_start?: string;
  window_end?: string;
};
export type DeepPreview = {
  receipt_id: string;
  context_hash: string;
  preview_hash: string;
  text_hash: string;
  conversation_revision: number;
  context: { kind: string; text: string }[];
  selection: ContextSelection;
};
type MapItem = {
  id: string;
  kind: string;
  text: string;
  provenance: string;
  state: string;
  sources: { id: string; revision: number }[];
};
type WorkingMap = { version: number; items: MapItem[]; created_at: string };
type Session = {
  revision: number;
  focus: string;
  phase: string;
  created_at: string;
  goal: { id: string; revision: number };
};
type DeepData = {
  goal: { text: string; revision: number };
  session: Session;
  map: WorkingMap | null;
  history: WorkingMap[];
  sessions: Session[];
};
export async function deepCall(
  csrf: string,
  id: string,
  path: string,
  body?: unknown,
) {
  const r = await fetch(`/api/v1/conversations/${id}/${path}`, {
    method: body ? "POST" : "GET",
    credentials: "same-origin",
    cache: "no-store",
    headers: body
      ? { "Content-Type": "application/json", "X-CSRF-Token": csrf }
      : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) {
    const d = await r.json();
    throw new Error(d.code);
  }
  return r.json();
}
const labels: Record<string, string> = {
  USER_STATED: "Ви сказали",
  USER_CONFIRMED: "Ви підтвердили",
  MODEL_HYPOTHESIS: "Припущення помічника",
  MODEL_DERIVED_SUMMARY: "Підсумок помічника",
  COMPUTED: "Обчислено",
  CURRENT: "Актуально",
  REJECTED: "Відхилено вами",
  STALE: "Джерело змінилося · потрібен перегляд",
  IRRELEVANT: "Більше не актуально",
};
const phaseLabels: Record<string, string> = {
  OPEN: "Відкрита",
  AGREE_FOCUS: "Уточнення фокусу",
  EXPLORE: "Дослідження",
  SYNTHESIZE: "Підсумовування",
  NEXT_STEP: "Можливі кроки",
  CLOSING: "Завершення",
  CLOSED: "Закрита на сьогодні",
  PAUSED: "На паузі",
};
export function DeepSessionPanel({
  csrf,
  id,
  revision,
  draft,
  selection,
  onSelection,
  preview,
  onPreview,
  onSession,
  onNext,
}: {
  csrf: string;
  id: string;
  revision: number;
  draft: string;
  selection: ContextSelection;
  onSelection: (s: ContextSelection) => void;
  preview: DeepPreview | null;
  onPreview: (p: DeepPreview | null) => void;
  onSession: (s: Session) => void;
  onNext: () => void;
}) {
  const [data, setData] = useState<DeepData | null>(null),
    [focus, setFocus] = useState(""),
    [open, setOpen] = useState(false),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [edit, setEdit] = useState<{ id: string; text: string } | null>(null),
    [previewOpen, setPreviewOpen] = useState(false);
  const alive = useRef(true),
    working = useRef(false);
  const sessionCallback = useRef(onSession);
  sessionCallback.current = onSession;
  async function refresh() {
    const d: DeepData = await deepCall(csrf, id, "deep-session");
    if (alive.current) {
      setData(d);
      setFocus(d.session.focus);
      sessionCallback.current(d.session);
    }
  }
  useEffect(() => {
    alive.current = true;
    void refresh().catch(() =>
      setError("Карта зараз недоступна. Відкрийте сесію ще раз."),
    );
    return () => {
      alive.current = false;
    };
  }, [id, revision]);
  async function session(action: string, extra: object = {}) {
    if (!data || working.current) return;
    working.current = true;
    setBusy(true);
    setError("");
    try {
      await deepCall(csrf, id, "deep-session/actions", {
        operation_id: crypto.randomUUID(),
        base_revision: data.session.revision,
        action,
        ...extra,
      });
      await refresh();
    } catch {
      setError("Сесія змінилася. Оновіть карту; ваш фокус лишився в полі.");
    } finally {
      working.current = false;
      if (alive.current) setBusy(false);
    }
  }
  async function mapAction(item: MapItem, action: string, text?: string) {
    if (!data?.map || working.current) return;
    working.current = true;
    setBusy(true);
    setError("");
    try {
      await deepCall(csrf, id, "working-map/actions", {
        operation_id: crypto.randomUUID(),
        base_version: data.map.version,
        item_id: item.id,
        action,
        user_confirmed: true,
        ...(text ? { text } : {}),
      });
      setEdit(null);
      await refresh();
    } catch {
      setError("Карта або джерело змінилися. Оновіть карту й перевірте запис.");
    } finally {
      working.current = false;
      if (alive.current) setBusy(false);
    }
  }
  async function prepare() {
    if (!draft.trim() || working.current) return;
    working.current = true;
    setBusy(true);
    setError("");
    try {
      const d = await deepCall(csrf, id, "context-preview", {
        operation_id: crypto.randomUUID(),
        base_revision: revision,
        text: draft,
        selection,
      });
      if (alive.current) {
        onPreview(d);
        setPreviewOpen(true);
      }
    } catch {
      setError(
        "Не вдалося підготувати цей діапазон. Перевірте дати й стан сесії.",
      );
    } finally {
      working.current = false;
      if (alive.current) setBusy(false);
    }
  }
  const closed = data?.session.phase === "CLOSED",
    paused = data?.session.phase === "PAUSED";
  function range(type: ContextSelection["type"]) {
    onPreview(null);
    onSelection({
      type,
      timezone: selection.timezone,
      ...(type === "CUSTOM"
        ? {
            window_start: new Date(Date.now() - 7 * 86400000).toISOString(),
            window_end: new Date().toISOString(),
          }
        : {}),
    });
  }
  return (
    <aside className="deep-session-panel" aria-label="Поточна сесія">
      <p className="session-goal" title={data?.goal.text}>
        Мета · {data?.goal.text}
      </p>
      <p className="hint">
        {phaseLabels[data?.session.phase ?? "OPEN"]} · ціль лишається окремою
      </p>
      <p className="session-focus-text">
        {data?.session.focus || "Фокус ще можна уточнити"}
      </p>
      <p className="hint">
        Контекст:{" "}
        {
          {
            GOAL_START: "від початку цілі",
            LAST_7_DAYS: "останні 7 днів",
            LAST_30_DAYS: "останні 30 днів",
            CUSTOM: "власний діапазон",
          }[selection.type]
        }
      </p>
      <button disabled={busy} onClick={() => setOpen(true)}>
        Карта сесії
      </button>
      <details>
        <summary>Змінити фокус і контекст</summary>
        <p className="entry-text">
          Ціль · редакція {data?.goal.revision}: {data?.goal.text}
        </p>
        <label>
          Фокус цієї сесії
          <input
            value={focus}
            maxLength={800}
            disabled={busy || closed}
            onChange={(e) => setFocus(e.target.value)}
          />
        </label>
        <div className="actions">
          <button
            disabled={
              busy || closed || !focus.trim() || focus === data?.session.focus
            }
            onClick={() => void session("focus", { focus })}
          >
            Зберегти фокус
          </button>
          {closed ? (
            <button onClick={onNext}>Наступна сесія</button>
          ) : (
            <button
              disabled={busy}
              onClick={() => void session(paused ? "resume" : "pause")}
            >
              {paused ? "Повернутися до сесії" : "Пауза"}
            </button>
          )}
        </div>
        <label>
          Контекст
          <select
            aria-label="Контекст"
            value={selection.type}
            disabled={busy || closed || paused}
            onChange={(e) => range(e.target.value as ContextSelection["type"])}
          >
            <option value="GOAL_START">Від початку цілі</option>
            <option value="LAST_7_DAYS">Останні 7 днів</option>
            <option value="LAST_30_DAYS">Останні 30 днів</option>
            <option value="CUSTOM">Власний діапазон</option>
          </select>
        </label>
        {selection.type === "CUSTOM" && (
          <div className="context-dates">
            {(["window_start", "window_end"] as const).map((key, i) => (
              <label key={key}>
                {i === 0 ? "Від" : "До"}
                <input
                  type="datetime-local"
                  value={
                    selection[key]
                      ? new Date(
                          new Date(selection[key]!).getTime() -
                            new Date(selection[key]!).getTimezoneOffset() *
                              60000,
                        )
                          .toISOString()
                          .slice(0, 16)
                      : ""
                  }
                  onChange={(e) => {
                    onPreview(null);
                    onSelection({
                      ...selection,
                      [key]: e.target.value
                        ? new Date(e.target.value).toISOString()
                        : undefined,
                    });
                  }}
                />
              </label>
            ))}
          </div>
        )}
        <button
          disabled={busy || closed || paused || !draft.trim()}
          onClick={() => void prepare()}
        >
          Переглянути контекст перед відправленням
        </button>
      </details>
      {preview && (
        <p className="hint">
          Контекст підготовлено для поточного повідомлення.
        </p>
      )}
      {error && <p role="alert">{error}</p>}
      {previewOpen && preview && (
        <Sheet
          title="Контекст цього повідомлення"
          onClose={() => setPreviewOpen(false)}
        >
          <p>
            Саме ці попередні джерела та карта використаються разом із вашим
            повідомленням. Якщо щось змінилося, запит потребуватиме нового
            перегляду.
          </p>
          {preview.context.map((p, i) => (
            <p key={i} className="entry-text">
              {p.text}
            </p>
          ))}
          <details>
            <summary>Технічні прив’язки</summary>
            <p className="metadata">
              {preview.receipt_id} · {preview.context_hash}
            </p>
          </details>
        </Sheet>
      )}
      {open && (
        <Sheet title="Карта сесії" onClose={() => setOpen(false)}>
          <p>
            Поточне розуміння можна уточнювати. Припущення й підсумки помічника
            ще не є вашими підтвердженими висновками.
          </p>
          {!data?.map ? (
            <p>Карта з’явиться після глибокої розмови.</p>
          ) : (
            data.map.items.map((item) => (
              <article className="map-item" key={item.id}>
                <p className="hint">
                  {labels[item.provenance]} · {labels[item.state]}
                </p>
                <p className="entry-text">{item.text}</p>
                {item.state === "CURRENT" && (
                  <div className="actions">
                    {item.kind === "HYPOTHESIS" ? (
                      <button
                        disabled={busy}
                        onClick={() => void mapAction(item, "reject")}
                      >
                        Відхилити припущення
                      </button>
                    ) : (
                      <button
                        disabled={busy}
                        onClick={() =>
                          setEdit({ id: item.id, text: item.text })
                        }
                      >
                        {item.provenance === "USER_CONFIRMED"
                          ? "Уточнити висновок"
                          : "Переглянути й підтвердити"}
                      </button>
                    )}
                    <button
                      disabled={busy}
                      onClick={() => void mapAction(item, "irrelevant")}
                    >
                      Більше не актуально
                    </button>
                  </div>
                )}
                {edit?.id === item.id && (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      void mapAction(
                        item,
                        item.provenance === "USER_CONFIRMED"
                          ? "clarify"
                          : "confirm",
                        edit.text,
                      );
                    }}
                  >
                    <label>
                      Мій висновок
                      <textarea
                        value={edit.text}
                        maxLength={800}
                        onChange={(e) =>
                          setEdit({ ...edit, text: e.target.value })
                        }
                      />
                    </label>
                    <button disabled={busy || !edit.text.trim()}>
                      Підтвердити мій висновок
                    </button>
                    <button type="button" onClick={() => setEdit(null)}>
                      Скасувати
                    </button>
                  </form>
                )}
                <details>
                  <summary>Джерела</summary>
                  {item.sources.map((r) => (
                    <p className="metadata" key={r.id}>
                      {r.id} · редакція {r.revision}
                    </p>
                  ))}
                </details>
              </article>
            ))
          )}
          <button
            disabled={busy}
            onClick={() =>
              void refresh().catch(() => setError("Не вдалося оновити карту."))
            }
          >
            Оновити карту
          </button>
          {error && <p role="alert">{error}</p>}
          <details>
            <summary>Що змінилося між версіями</summary>
            {data?.history.map((m, index) => (
              <article key={m.version}>
                <h3>Версія {m.version}</h3>
                {m.items
                  .filter((i) => {
                    const previous = data.history[index + 1]?.items.find(
                      (p) => p.id === i.id,
                    );
                    return (
                      !previous ||
                      previous.text !== i.text ||
                      previous.state !== i.state ||
                      previous.provenance !== i.provenance
                    );
                  })
                  .map((i) => (
                    <p key={i.id}>
                      {labels[i.state]}: {i.text}
                    </p>
                  ))}
              </article>
            ))}
          </details>
          <details>
            <summary>Сесії цієї цілі</summary>
            {data?.sessions.map((s, i) => (
              <p key={i}>
                {new Date(s.created_at).toLocaleDateString("uk-UA")} · редакція
                цілі {s.goal.revision} · {s.focus || "Фокус ще не уточнений"} ·{" "}
                {phaseLabels[s.phase]}
              </p>
            ))}
          </details>
          <details>
            <summary>Спеціалізовані навички · очікують перевірки</summary>
            <p>
              Робота з думками, хвилюванням, сном, сновидіннями та заземленням
              недоступна. Усі п’ять кандидатів вимкнені до окремого
              content/evidence/rights review.
            </p>
          </details>
          {!closed && (
            <div className="actions">
              <label>
                Етап розмови
                <select
                  value={data?.session.phase ?? "OPEN"}
                  disabled={busy || paused}
                  onChange={(e) =>
                    void session("phase", { phase: e.target.value })
                  }
                >
                  <option value="OPEN" disabled>
                    Відкрита
                  </option>
                  <option value="AGREE_FOCUS">Уточнити фокус</option>
                  <option value="EXPLORE">Дослідити</option>
                  <option value="SYNTHESIZE">Підсумувати розуміння</option>
                  <option value="NEXT_STEP">Обрати можливий крок</option>
                  <option value="CLOSING">Завершення</option>
                  <option value="PAUSED" disabled>
                    На паузі
                  </option>
                </select>
              </label>
              <button disabled={busy} onClick={() => void session("close")}>
                Закрити сесію на сьогодні
              </button>
            </div>
          )}
        </Sheet>
      )}
    </aside>
  );
}
