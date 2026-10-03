import { useEffect, useRef, useState } from "react";
export type ReflectionGoal = {
  id: string;
  text: string;
  state: "ACTIVE" | "PAUSED" | "COMPLETED";
  revision: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
};
export async function reflectionCall(
  csrf: string,
  path: string,
  body?: unknown,
) {
  const r = await fetch("/api/v1/reflection/" + path, {
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
export function ReflectionGoals({
  csrf,
  onStart,
  onChanged,
}: {
  csrf: string;
  onStart: (g: ReflectionGoal) => void;
  onChanged: () => void;
}) {
  const [goals, setGoals] = useState<ReflectionGoal[]>([]),
    [editing, setEditing] = useState<ReflectionGoal | null>(null),
    [text, setText] = useState(""),
    [agreed, setAgreed] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [history, setHistory] = useState<ReflectionGoal[] | null>(null);
  const alive = useRef(true),
    key = useRef<{ signature: string; id: string } | null>(null),
    working = useRef(false);
  async function refresh() {
    const d = await reflectionCall(csrf, "goals");
    if (alive.current) setGoals(d.items);
  }
  useEffect(() => {
    alive.current = true;
    void refresh().catch(() => {
      if (alive.current) setError("Цілі зараз недоступні.");
    });
    return () => {
      alive.current = false;
    };
  }, []);
  async function save(state?: ReflectionGoal["state"]) {
    if (working.current) return;
    working.current = true;
    setBusy(true);
    setError("");
    const body = editing
      ? {
          base_revision: editing.revision,
          user_agreed: true,
          ...(state ? { state } : { text }),
        }
      : { text, user_agreed: true };
    const path = editing ? "goals/" + editing.id : "goals";
    const signature = JSON.stringify({ path, body });
    if (key.current?.signature !== signature)
      key.current = { signature, id: crypto.randomUUID() };
    try {
      await reflectionCall(csrf, path, {
        ...body,
        operation_id: key.current.id,
      });
      if (alive.current) {
        key.current = null;
        setEditing(null);
        setText("");
        setAgreed(false);
        setHistory(null);
        await refresh();
        onChanged();
      }
    } catch (e) {
      if (alive.current)
        setError(
          (e as Error).message === "REVISION_CONFLICT"
            ? "Ціль змінилася. Оновіть список; введений текст залишається тут."
            : "Не вдалося зберегти ціль. Текст залишився в полі.",
        );
    } finally {
      working.current = false;
      if (alive.current) setBusy(false);
    }
  }
  return (
    <section className="reflection-goals" aria-label="Погоджені цілі">
      <p>Ціль задаєте й погоджуєте ви. Це не оцінка вашого стану.</p>
      {error && <p role="alert">{error}</p>}
      <form
        aria-label={editing ? "Редагування цілі" : "Нова ціль"}
        onSubmit={(e) => {
          e.preventDefault();
          void save();
        }}
      >
        <label>
          Текст цілі
          <textarea
            aria-label="Текст цілі"
            value={text}
            maxLength={2000}
            rows={4}
            disabled={busy}
            onChange={(e) => setText(e.target.value)}
          />
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={agreed}
            onChange={(e) => setAgreed(e.target.checked)}
          />
          Це моя погоджена ціль
        </label>
        <button className="primary" disabled={busy || !agreed || !text.trim()}>
          {editing ? "Зберегти нову редакцію" : "Створити ціль"}
        </button>
        {editing && (
          <button
            type="button"
            onClick={() => {
              setEditing(null);
              setText("");
              setAgreed(false);
            }}
          >
            Нова ціль
          </button>
        )}
      </form>
      <ul>
        {goals.map((g) => (
          <li key={g.id}>
            <p className="goal-text">{g.text}</p>
            <p className="metadata">
              {g.state === "ACTIVE"
                ? "Активна"
                : g.state === "PAUSED"
                  ? "Призупинена"
                  : "Завершена"}{" "}
              · редакція {g.revision}
            </p>
            <div className="actions">
              <button
                disabled={busy || g.state !== "ACTIVE"}
                onClick={() => onStart(g)}
              >
                Почати глибоку розмову
              </button>
              <button
                disabled={busy}
                onClick={() => {
                  setEditing(g);
                  setText(g.text);
                  setAgreed(false);
                  setHistory(null);
                }}
              >
                Редагувати ціль
              </button>
              <button
                disabled={busy}
                onClick={() =>
                  void reflectionCall(csrf, "goals/" + g.id)
                    .then(
                      (d) =>
                        alive.current && setHistory([...d.history, d.goal]),
                    )
                    .catch(() => {
                      if (alive.current)
                        setError(
                          "Не вдалося відкрити історію цілі. Спробуйте ще раз.",
                        );
                    })
                }
              >
                Історія цілі
              </button>
            </div>
            {editing?.id === g.id && (
              <div className="actions">
                <button
                  disabled={busy}
                  onClick={() =>
                    void save(g.state === "PAUSED" ? "ACTIVE" : "PAUSED")
                  }
                >
                  {g.state === "PAUSED"
                    ? "Продовжити ціль"
                    : "Призупинити ціль"}
                </button>
                <button disabled={busy} onClick={() => void save("COMPLETED")}>
                  Завершити ціль
                </button>
              </div>
            )}
          </li>
        ))}
      </ul>
      {history && (
        <section aria-label="Історія цілі">
          <h3>Історія цілі</h3>
          {history.map((g) => (
            <article key={g.revision}>
              <p>
                Редакція {g.revision} ·{" "}
                {new Date(g.updated_at).toLocaleString("uk-UA")}
              </p>
              <p>{g.text}</p>
            </article>
          ))}
        </section>
      )}
    </section>
  );
}
export function DeepContext({
  csrf,
  conversationId,
  binding,
  syntheticDemo,
  refreshVersion,
}: {
  csrf: string;
  conversationId: string;
  binding: { id: string; revision: number };
  syntheticDemo: boolean;
  refreshVersion: number;
}) {
  const [data, setData] = useState<{
      goal: ReflectionGoal;
      history: ReflectionGoal[];
    } | null>(null),
    [query, setQuery] = useState(""),
    [start, setStart] = useState(""),
    [end, setEnd] = useState(""),
    [budget, setBudget] = useState(2000),
    [result, setResult] = useState<any>(null),
    [expanded, setExpanded] = useState<any[]>([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    let live = true;
    void reflectionCall(csrf, "goals/" + binding.id)
      .then((d) => {
        if (live) setData(d);
      })
      .catch(() => {
        if (live)
          setError("Не вдалося завантажити ціль. Відкрийте розмову ще раз.");
      });
    return () => {
      live = false;
    };
  }, [binding.id, binding.revision, refreshVersion]);
  const pinned =
    data?.goal.revision === binding.revision
      ? data.goal
      : data?.history.find((g) => g.revision === binding.revision);
  async function build() {
    setBusy(true);
    setError("");
    try {
      const d = await reflectionCall(csrf, "context", {
        operation_id: crypto.randomUUID(),
        goal: binding,
        conversation_id: conversationId,
        window_start: start ? new Date(start).toISOString() : null,
        window_end: end ? new Date(end).toISOString() : null,
        query,
        token_budget: budget,
        byte_budget: 8000,
        max_sources: 16,
        prepare_synthetic_digests: syntheticDemo,
        confirmed_memories: [],
        memory_scope: null,
      });
      setResult(d);
      setExpanded([]);
    } catch {
      setError(
        "Не вдалося підготувати контекст у цьому діапазоні чи бюджеті. Журнал і вільна розмова залишаються незалежними.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <aside className="deep-context" aria-label="Глибока розмова">
      <h2>Погоджена ціль · редакція {binding.revision}</h2>
      <p>{pinned?.text ?? "Завантажуємо погоджену редакцію…"}</p>
      {data && data.goal.revision !== binding.revision && (
        <p className="hint">
          Ціль має нову редакцію {data.goal.revision}. Ця розмова зберігає
          прив’язку до редакції {binding.revision}; для нової почніть окрему
          розмову.
        </p>
      )}
      <details>
        <summary>Минулий контекст</summary>
        <p>
          Вибірковий локальний контекст. Похідні дайджести не замінюють
          оригінальні повідомлення.
        </p>
        <label>
          Пошук у попередніх розмовах
          <input
            value={query}
            maxLength={200}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
        <div className="field-row">
          <label>
            Контекст від
            <input
              type="datetime-local"
              value={start}
              onChange={(e) => setStart(e.target.value)}
            />
          </label>
          <label>
            Контекст до
            <input
              type="datetime-local"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
            />
          </label>
        </div>
        <label>
          Бюджет контексту
          <input
            type="number"
            min={128}
            max={12000}
            value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
          />
        </label>
        <button disabled={busy} onClick={() => void build()}>
          {syntheticDemo ? "Підготувати демо-контекст" : "Підготувати контекст"}
        </button>
        {error && <p role="alert">{error}</p>}
        {result && (
          <>
            <p>
              Вибрано джерел: {result.receipt.sources.length} · бюджет{" "}
              {result.receipt.used_tokens_upper_bound}/
              {result.receipt.token_budget} (консервативна оцінка).
            </p>
            {result.context.map((p: any, i: number) => (
              <article key={i}>
                <h3>
                  {p.kind === "GOAL_REVISION"
                    ? "Погоджена редакція цілі"
                    : p.kind === "CURRENT_TURN"
                      ? "Поточна розмова"
                      : p.kind.endsWith("DIGEST")
                        ? "Похідний демо-дайджест"
                        : "Вибране минуле повідомлення"}
                </h3>
                <p>{p.text}</p>
              </article>
            ))}
            {result.receipt.sources.slice(0, 8).map((s: any) => (
              <button
                key={s.id}
                onClick={() =>
                  void reflectionCall(csrf, "expand", {
                    receipt_id: result.receipt.id,
                    sources: [s],
                    token_budget: 2000,
                    byte_budget: 8000,
                  })
                    .then((d) => setExpanded(d.messages))
                    .catch(() =>
                      setError("Джерело змінилося. Побудуйте контекст ще раз."),
                    )
                }
              >
                Відкрити оригінал · редакція {s.revision}
              </button>
            ))}
            {expanded.map((m) => (
              <p key={m.id}>{m.raw_text}</p>
            ))}
          </>
        )}
      </details>
    </aside>
  );
}
