import { useEffect, useRef, useState } from "react";
import { names, type Kind } from "./journal-ui";

type Ref = { id: string; revision: number };
type Task = "capture_classify" | "organize_selected" | "memory_propose";
type Memory = {
  id: string;
  revision: number;
  content: string;
  status: string;
  provenance: string;
  scope: string;
  sources: Ref[];
  expires_at: number | null;
};
type Job = {
  id: string;
  task: Task;
  state: string;
  error: string | null;
  provider: string;
  model: string;
  attempts: number;
  context_hash: string;
  source_refs: string;
};
type Suggestion = {
  id: string;
  status: string;
  provider: string;
  model: string;
  protocol: string;
  output: {
    task: Task;
    sources: Ref[];
    type?: Kind;
    tags?: string[];
    groups?: Kind[];
    reason: string;
  };
  accepted: unknown;
};
type Status = {
  mode: "OFF" | "MOCK";
  live_provider_calls: false;
  providers: {
    id: string;
    model: string | null;
    destination: string;
    retention_note: string;
    availability: string;
    auth_mode: string;
    quota: string;
    version: string;
  }[];
};
type Preview = {
  id: string;
  context_hash: string;
  approx_bytes: number;
  approx_characters: number;
  creative_included: boolean;
  package: {
    task: Task;
    entries: {
      id: string;
      revision: number;
      type: Kind;
      raw_text: string;
      tags: string[];
    }[];
    memories: { id: string; revision: number; content: string }[];
    expires_at: number;
    provider: Status["providers"][0];
    approval_scope: string;
    consent_ref: string;
  };
};
const tasks: Record<Task, string> = {
  capture_classify: "Запропонувати розділ і теги",
  organize_selected: "Організувати вибрані записи",
  memory_propose: "Запропонувати налаштування пам’яті",
};
const states: Record<string, string> = {
  QUEUED: "У черзі",
  RUNNING: "Виконується",
  DONE: "Пропозиція готова",
  FAILED: "Помилка",
  CANCELLED: "Скасовано",
  PROVIDER_DISABLED: "Provider вимкнено",
  WAITING_PROVIDER: "Provider недоступний",
  PENDING: "Очікує рішення",
  ACCEPTED: "Прийнято",
  REJECTED: "Відхилено",
  IGNORED: "Пропущено",
  STALE: "Застаріло",
  UNDONE: "Скасовано структуру",
  MODEL_SUGGESTED: "Пропозиція mock — ще не підтверджена",
  USER_CONFIRMED: "Підтверджено вами",
  REVIEW_REQUIRED: "Джерело змінилось — перевірте",
};
const errors: Record<string, string> = {
  CONSENT_DENIED:
    "Згода відсутня, відкликана або минули 5 хвилин. Створіть новий перегляд.",
  CONTEXT_STALE: "Вибраний контекст змінився. Створіть новий перегляд.",
  MEMORY_STALE: "Пам’ять змінилась або не підтверджена. Оновіть вибір.",
  MEMORY_SOURCE_STALE:
    "Джерело пам’яті змінилось. Перегляньте й виправте пам’ять.",
  CREATIVE_MEMORY_DENIED:
    "Творчі записи не використовуємо для особистої пам’яті. Оберіть нетворчі записи.",
  FOREGROUND_BUSY: "Уже виконується завдання. Дочекайтесь або скасуйте його.",
  CONTEXT_BUDGET_NARROW_SELECTION: "Контекст завеликий. Звузьте вибір записів.",
  ALREADY_REVIEWED_CHANGE_SOURCE:
    "Цю пропозицію вже переглянуто. Повтор можливий після зміни джерела або версії.",
  INVALID_TRANSITION: "Стан змінився. Оновіть перегляд перед рішенням.",
  PROVIDER_DISABLED: "Зовнішній provider вимкнено; виклик не відбувся.",
  SCHEMA_INVALID: "Перевірте введені поля.",
  TYPE_CHANGE_CONFIRMATION_REQUIRED:
    "Зміна розділу прибере спеціальні поля. Підтвердьте це окремо.",
};

export function AssistantPanel({
  csrf,
  selected,
  onChanged,
}: {
  csrf: string;
  selected: Set<string>;
  onChanged: () => Promise<void>;
}) {
  const [open, setOpen] = useState(false),
    [status, setStatus] = useState<Status | null>(null);
  const [task, setTask] = useState<Task>("capture_classify"),
    [provider, setProvider] = useState("mock");
  const [memories, setMemories] = useState<Memory[]>([]),
    [jobs, setJobs] = useState<Job[]>([]),
    [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [chosenMemory, setChosenMemory] = useState<Set<string>>(new Set()),
    [preview, setPreview] = useState<Preview | null>(null);
  const [content, setContent] = useState(""),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false);
  const active = useRef(true);
  useEffect(
    () => () => {
      active.current = false;
    },
    [],
  );
  async function request(path: string, method = "GET", body?: unknown) {
    const r = await fetch("/api/v1/ai/" + path, {
      method,
      credentials: "same-origin",
      cache: "no-store",
      headers: {
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        "X-CSRF-Token": csrf,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const result = await r.json();
    if (!r.ok) throw new Error(result.code);
    return result;
  }
  async function refresh() {
    const [s, m, j, p] = await Promise.all([
      request("status"),
      request("memories"),
      request("jobs"),
      request("suggestions"),
    ]);
    if (active.current) {
      setStatus(s);
      setMemories(m.items);
      setJobs(j.items);
      setSuggestions(p.items);
    }
  }
  async function action(run: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await run();
      await refresh();
    } catch (e) {
      if (active.current) {
        const code = e instanceof Error ? e.message : "REQUEST_FAILED";
        setError(
          errors[code] ||
            "Не вдалося виконати дію. Оновіть перегляд і повторіть. (" +
              code +
              ")",
        );
      }
    } finally {
      if (active.current) setBusy(false);
    }
  }
  useEffect(() => {
    void refresh().catch(() => {});
  }, [csrf]);
  const running = jobs.some(
    (j) => j.state === "RUNNING" || j.state === "QUEUED",
  );
  useEffect(() => {
    if (!open || !running) return;
    const timer = setInterval(() => {
      void refresh().catch(() => {});
    }, 500);
    return () => clearInterval(timer);
  }, [open, running]);
  const selectionKey = [...selected].sort().join(",");
  useEffect(() => {
    setPreview(null);
  }, [selectionKey, task, provider]);
  async function buildPreview() {
    const refs = await Promise.all(
      [...selected].sort().map(async (id) => {
        const r = await fetch("/api/v1/entries/" + id, {
          cache: "no-store",
          credentials: "same-origin",
        });
        if (!r.ok) throw new Error("CONTEXT_STALE");
        const e = await r.json();
        return { id: e.id, revision: e.revision };
      }),
    );
    const memoryRefs = [...chosenMemory].map((id) => {
      const m = memories.find((m) => m.id === id);
      if (!m) throw new Error("MEMORY_STALE");
      return { id: m.id, revision: m.revision };
    });
    const p = await request("preview", "POST", {
      task,
      provider,
      entries: refs,
      memories: memoryRefs,
    });
    if (active.current) setPreview(p);
  }
  return (
    <section className="assistant" aria-label="Помічник і пам’ять">
      <div className="assistant-head">
        <p role="status">
          {status?.mode === "MOCK"
            ? "Синтетичний mock · без зовнішніх викликів"
            : "AI вимкнено · записи зберігаються незалежно"}
        </p>
        <button aria-expanded={open} onClick={() => setOpen((v) => !v)}>
          Помічник і пам’ять
        </button>
      </div>
      {open && (
        <div className="assistant-content">
          <h2>Організація без поспіху</h2>
          <p>
            Оберіть записи в щоденнику. Mock створює лише синтетичні пропозиції;
            рішення за вами.
          </p>
          <label className="check">
            <input
              type="checkbox"
              checked={status?.mode === "MOCK"}
              disabled={busy}
              onChange={(e) => {
                const mode = e.target.checked ? "MOCK" : "OFF";
                setStatus((old) => (old ? { ...old, mode } : old));
                void action(async () => {
                  await request("mode", "POST", { mode });
                  setPreview(null);
                });
              }}
            />
            Увімкнути локальний synthetic mock
          </label>
          <div className="field-row">
            <label>
              Завдання
              <select
                aria-label="Завдання"
                value={task}
                onChange={(e) => setTask(e.target.value as Task)}
              >
                {Object.entries(tasks).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Provider
              <select
                aria-label="Provider"
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
              >
                <option value="mock">Локальний mock</option>
                <option value="codex-disabled">
                  Codex — вимкнено, не перевірено
                </option>
              </select>
            </label>
          </div>
          <p>
            {selected.size} вибраних записів. Згода діє 5 хвилин для одного
            завдання й точного контексту.
          </p>
          <fieldset>
            <legend>Пам’ять для цього контексту — лише за вибором</legend>
            {memories.filter((m) => m.status === "USER_CONFIRMED").length ===
              0 && <p>Підтвердженої пам’яті поки немає.</p>}
            {memories
              .filter((m) => m.status === "USER_CONFIRMED")
              .map((m) => (
                <label className="check" key={m.id}>
                  <input
                    type="checkbox"
                    checked={chosenMemory.has(m.id)}
                    onChange={(e) => {
                      setChosenMemory((old) => {
                        const next = new Set(old);
                        e.target.checked ? next.add(m.id) : next.delete(m.id);
                        return next;
                      });
                      setPreview(null);
                    }}
                  />
                  {m.content}
                </label>
              ))}
          </fieldset>
          <button
            disabled={
              busy ||
              !selected.size ||
              (task === "capture_classify" && selected.size !== 1)
            }
            onClick={() => void action(buildPreview)}
          >
            Переглянути точний контекст
          </button>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          {notice && (
            <p className="notice" role="status">
              {notice}
            </p>
          )}
          {preview && (
            <section className="context-preview" aria-label="Точний контекст">
              <h3>Що отримає provider</h3>
              <p>
                {tasks[preview.package.task]} ·{" "}
                {preview.package.provider.model || "Модель не перевірено"}
              </p>
              <p>
                Призначення: {preview.package.provider.destination}.{" "}
                {preview.package.provider.retention_note}
              </p>
              <p>
                {preview.approx_bytes} bytes / {preview.approx_characters}{" "}
                символів приблизного контексту; кількість provider tokens
                невідома. Творчий вміст:{" "}
                {preview.creative_included ? "так" : "ні"}.
              </p>
              {preview.package.entries.map((e) => (
                <article key={e.id}>
                  <p>
                    {names[e.type]} ·{" "}
                    <span className="source-ref">
                      {e.id} / r{e.revision}
                    </span>
                  </p>
                  <p className="entry-text">{e.raw_text}</p>
                  <p>Теги: {e.tags.join(", ") || "немає"}</p>
                </article>
              ))}
              {preview.package.memories.map((m) => (
                <p key={m.id}>
                  {m.content} ·{" "}
                  <span className="source-ref">
                    {m.id} / r{m.revision}
                  </span>
                </p>
              ))}
              <p>
                До{" "}
                {new Date(preview.package.expires_at * 1000).toLocaleTimeString(
                  "uk-UA",
                )}
                . Hash:{" "}
                <span className="source-ref">{preview.context_hash}</span>
              </p>
              <details>
                <summary>Повний пакет: усі поля та обмеження</summary>
                <pre>{JSON.stringify(preview.package, null, 2)}</pre>
              </details>
              <div className="actions">
                <button
                  className="primary"
                  disabled={busy || status?.mode !== "MOCK"}
                  onClick={() =>
                    void action(async () => {
                      await request(
                        "consents/" + preview.id + "/approve",
                        "POST",
                        { context_hash: preview.context_hash },
                      );
                      const job = await request("jobs", "POST", {
                        consent_id: preview.id,
                        operation_id: crypto.randomUUID(),
                      });
                      setNotice(states[job.state] || job.state);
                    })
                  }
                >
                  Погодити цей контекст і створити завдання
                </button>
                <button
                  disabled={busy}
                  onClick={() =>
                    void action(async () => {
                      await request(
                        "consents/" + preview.id + "/revoke",
                        "POST",
                        {},
                      );
                      setPreview(null);
                      setNotice("Згоду відкликано");
                    })
                  }
                >
                  Відкликати згоду
                </button>
                <button onClick={() => setPreview(null)}>
                  Закрити перегляд
                </button>
              </div>
            </section>
          )}
          <details>
            <summary>Provider та межі runtime</summary>
            {status?.providers.map((p) => (
              <p key={p.id}>
                {p.id} · {p.model || "модель невідома"} · {p.availability} ·
                auth: {p.auth_mode} · quota: {p.quota}
                <br />
                {p.retention_note}
              </p>
            ))}
            <p>
              Live AI: OFF. Клінічні протоколи: OFF. Телефон зберігає й
              синхронізує записи без AI.
            </p>
          </details>
          <h3>Завдання</h3>
          {!jobs.length && <p>Завдань ще немає.</p>}
          {jobs.map((j) => (
            <article className="runtime-row" key={j.id}>
              <p>
                {tasks[j.task]} · {states[j.state] || j.state}
                <br />
                <small>
                  {j.provider} / {j.model || "невідомо"} · спроб: {j.attempts}
                  {j.error ? " · " + j.error : ""}
                </small>
              </p>
              {["QUEUED", "RUNNING"].includes(j.state) && (
                <button
                  disabled={busy}
                  onClick={() =>
                    void action(() =>
                      request("jobs/" + j.id + "/cancel", "POST", {}),
                    )
                  }
                >
                  Скасувати завдання
                </button>
              )}
            </article>
          ))}
          <h3>Пропозиції організації</h3>
          {!suggestions.filter((s) => s.output.task !== "memory_propose")
            .length && (
            <p>Пропозицій ще немає. Оригінали записів зберігаються окремо.</p>
          )}
          {suggestions
            .filter((s) => s.output.task !== "memory_propose")
            .map((s) => (
              <SuggestionRow
                key={s.id}
                suggestion={s}
                busy={busy}
                change={(body) =>
                  action(async () => {
                    await request("suggestions/" + s.id, "POST", body);
                    await onChanged();
                  })
                }
              />
            ))}
          <h2>Що система пам’ятає</h2>
          <p>
            Тут лише вибрані налаштування й підтверджені вами записи. Пропозиція
            mock ще не є фактом.
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void action(async () => {
                await request("memories", "POST", {
                  content,
                  scope: "preferences",
                });
                setContent("");
                setPreview(null);
              });
            }}
          >
            <label>
              Додати власне налаштування
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                maxLength={500}
                required
                rows={2}
              />
            </label>
            <button disabled={busy || !content.trim()}>Зберегти пам’ять</button>
          </form>
          {!memories.length && <p>Пам’ять порожня.</p>}
          {memories.map((m) => (
            <MemoryRow
              key={m.id + ":" + m.revision}
              memory={m}
              busy={busy}
              change={(body) =>
                action(async () => {
                  await request("memories/" + m.id, "POST", {
                    ...body,
                    revision: m.revision,
                  });
                  setPreview(null);
                })
              }
            />
          ))}
          <button disabled={busy} onClick={() => void action(refresh)}>
            Оновити перегляд
          </button>
        </div>
      )}
    </section>
  );
}
function MemoryRow({
  memory: m,
  busy,
  change,
}: {
  memory: Memory;
  busy: boolean;
  change: (body: { action: string; content?: string }) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false),
    [value, setValue] = useState(m.content);
  return (
    <article className="memory-row">
      <p>{m.content}</p>
      <p className="hint">
        {states[m.status] || m.status} · {m.provenance} · {m.scope}
        <br />
        <span className="source-ref">
          {m.id} / r{m.revision}
        </span>
        {m.sources.map((r) => (
          <span className="source-ref" key={r.id}>
            {" "}
            · джерело {r.id} / r{r.revision}
          </span>
        ))}
      </p>
      {editing ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void change({ action: "edit", content: value });
            setEditing(false);
          }}
        >
          <label>
            Виправити пам’ять
            <textarea
              value={value}
              onChange={(e) => setValue(e.target.value)}
              required
              maxLength={500}
            />
          </label>
          <button disabled={busy || !value.trim()}>Зберегти виправлення</button>
          <button type="button" onClick={() => setEditing(false)}>
            Скасувати редагування
          </button>
        </form>
      ) : (
        <div className="actions">
          {m.status === "MODEL_SUGGESTED" && (
            <button
              disabled={busy}
              onClick={() => void change({ action: "confirm" })}
            >
              Підтвердити пам’ять
            </button>
          )}
          <button onClick={() => setEditing(true)}>Редагувати пам’ять</button>
          {!["REJECTED", "USER_CONFIRMED"].includes(m.status) && (
            <button
              disabled={busy}
              onClick={() => void change({ action: "reject" })}
            >
              Відхилити пам’ять
            </button>
          )}
          <button
            disabled={busy}
            onClick={() => {
              if (
                window.confirm(
                  "Видалити пам’ять? Залежні контексти та завдання стануть недійсними.",
                )
              )
                void change({ action: "delete" });
            }}
          >
            Видалити пам’ять
          </button>
        </div>
      )}
    </article>
  );
}
function SuggestionRow({
  suggestion: s,
  busy,
  change,
}: {
  suggestion: Suggestion;
  busy: boolean;
  change: (body: unknown) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false),
    [kind, setKind] = useState<Kind>(s.output.type || "inbox"),
    [tags, setTags] = useState(s.output.tags || []),
    [confirm, setConfirm] = useState(false);
  return (
    <article className="suggestion-row">
      <p>Synthetic mock · {states[s.status] || s.status}</p>
      <p>
        {s.output.task === "capture_classify"
          ? names[s.output.type!] + " · " + s.output.tags!.join(", ")
          : "Вибрані розділи: " +
            s.output.groups!.map((k) => names[k]).join(", ")}
      </p>
      <p className="hint">
        Причина:{" "}
        {s.output.task === "capture_classify"
          ? "організація вибраного запису"
          : "явний вибір записів"}
        . {s.provider} / {s.model} / {s.protocol}
      </p>
      {s.output.sources.map((r) => (
        <p className="source-ref" key={r.id}>
          Джерело {r.id} / r{r.revision}
        </p>
      ))}
      {s.status === "PENDING" && (
        <>
          {editing && (
            <div>
              <label>
                Розділ пропозиції
                <select
                  aria-label="Розділ пропозиції"
                  value={kind}
                  onChange={(e) => setKind(e.target.value as Kind)}
                >
                  {Object.entries(names).map(([k, v]) => (
                    <option key={k} value={k}>
                      {v}
                    </option>
                  ))}
                </select>
              </label>
              <fieldset>
                <legend>Теги пропозиції</legend>
                {["нотатка", "ідея", "план", "щоденник"].map((t) => (
                  <label key={t} className="check">
                    <input
                      type="checkbox"
                      checked={tags.includes(t)}
                      onChange={(e) =>
                        setTags((old) =>
                          e.target.checked
                            ? [...old, t]
                            : old.filter((x) => x !== t),
                        )
                      }
                    />
                    {t}
                  </label>
                ))}
              </fieldset>
            </div>
          )}
          {s.output.task === "capture_classify" && (
            <label className="check">
              <input
                type="checkbox"
                checked={confirm}
                onChange={(e) => setConfirm(e.target.checked)}
              />
              Підтверджую видалення спеціальних полів, якщо змінюється розділ;
              історія залишиться.
            </label>
          )}
          <div className="actions">
            <button
              disabled={busy}
              onClick={() =>
                void change({
                  action: editing ? "edit" : "accept",
                  ...(editing ? { type: kind, tags } : {}),
                  confirm_type_change: confirm,
                })
              }
            >
              {editing
                ? "Прийняти виправлену структуру"
                : "Прийняти пропозицію"}
            </button>
            {s.output.task === "capture_classify" && (
              <button onClick={() => setEditing((v) => !v)}>
                {editing ? "Завершити редагування" : "Редагувати пропозицію"}
              </button>
            )}
            <button
              disabled={busy}
              onClick={() => void change({ action: "reject" })}
            >
              Відхилити пропозицію
            </button>
            <button
              disabled={busy}
              onClick={() => void change({ action: "ignore" })}
            >
              Пропустити
            </button>
          </div>
        </>
      )}
      {s.status === "ACCEPTED" && s.output.task === "capture_classify" && (
        <button disabled={busy} onClick={() => void change({ action: "undo" })}>
          Повернути попередню структуру
        </button>
      )}
    </article>
  );
}
