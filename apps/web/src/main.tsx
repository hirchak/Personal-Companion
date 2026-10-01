import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";
import type { components } from "./api-schema";

import {
  blank,
  names,
  typed,
  creativeNames,
  fieldNames,
  type Kind,
  type Entry,
  type Draft,
} from "./journal-ui";
import { EntryEditor } from "./EntryEditor";
import { PhoneApp } from "./PhoneApp";
import { AssistantPanel } from "./AssistantPanel";
import { MacSyncSettings } from "./MacSyncSettings";
class ApiError extends Error {
  constructor(
    public code: string,
    public status: number,
  ) {
    super(code);
  }
}
async function api(path: string, csrf = "", method = "GET", body?: unknown) {
  const response = await fetch("/api/v1/" + path, {
    method,
    credentials: "same-origin",
    cache: "no-store",
    headers: {
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(csrf ? { "X-CSRF-Token": csrf } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new ApiError(error.code, response.status);
  }
  return response;
}
function message(error: unknown) {
  if (error instanceof ApiError) {
    if (error.status === 409)
      return "Запис змінився або план експорту застарів. Перегляньте актуальну версію перед повтором.";
    if (error.status === 422)
      return "Перевірте поля: текст, оцінки, часовий пояс і час з UTC-зсувом.";
    if (error.status === 410) return "Цей запис уже видалено.";
    if (error.status === 401 || error.status === 429)
      return "Код недійсний, вичерпаний або спроб забагато. Перезапустіть сервер для нового коду.";
  }
  return "Не вдалося зберегти зміни. Текст залишається тут; перевірте сервер і повторіть.";
}
function App() {
  const [csrf, setCsrf] = useState(""),
    [ready, setReady] = useState(false),
    [code, setCode] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    api("auth/session")
      .then((r) => r.json())
      .then((s) => setCsrf(s.csrf_token))
      .catch(() => {})
      .finally(() => setReady(true));
  }, []);
  async function unlock(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await api("auth/unlock", "", "POST", { code });
      const s = await r.json();
      setCode("");
      setCsrf(s.csrf_token);
    } catch (err) {
      setError(message(err));
    } finally {
      setBusy(false);
    }
  }
  if (!ready)
    return (
      <main className="unlock">
        <p role="status">Відкриваємо щоденник…</p>
      </main>
    );
  if (csrf)
    return (
      <Journal
        csrf={csrf}
        onLock={() => {
          setCsrf("");
          setCode("");
          setError("");
        }}
      />
    );
  return (
    <main className="unlock">
      <div className="unlock-inner">
        <span className="wordmark">Особистий простір</span>
        <h1>
          Місце для
          <br />
          ваших думок.
        </h1>
        <p>
          Локальний щоденник на цьому Mac.
          <br />
          Введіть одноразовий код із термінала.
        </p>
        <form onSubmit={unlock}>
          <label htmlFor="code">Код розблокування</label>
          <input
            id="code"
            type="password"
            autoComplete="off"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            required
            autoFocus
          />
          <button className="primary" disabled={busy}>
            {busy ? "Відкриваємо…" : "Відкрити щоденник"}
          </button>
        </form>
        {error && <p role="alert">{error}</p>}
        <p className="hint">
          Synthetic demo · лише вигадані записи.
          <br />
          Після блокування перезапустіть сервер для нового коду.
        </p>
      </div>
    </main>
  );
}
function Journal({ csrf, onLock }: { csrf: string; onLock: () => void }) {
  const [entries, setEntries] = useState<Entry[]>([]),
    [q, setQ] = useState(""),
    [filter, setFilter] = useState(""),
    [tag, setTag] = useState(""),
    [from, setFrom] = useState(""),
    [to, setTo] = useState("");
  const [cursor, setCursor] = useState<string | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [editing, setEditing] = useState<Entry | "new" | null>(null),
    [draft, setDraft] = useState(blank()),
    [busy, setBusy] = useState(false),
    [conflict, setConflict] = useState(false);
  const [history, setHistory] = useState<Entry[] | null>(null),
    [historyAfter, setHistoryAfter] = useState<number | null>(null),
    [historyId, setHistoryId] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set()),
    [plan, setPlan] = useState<{
      plan_id: string;
      count: number;
      refs: { id: string; revision: number }[];
      sections: Kind[];
      warning: string;
    } | null>(null),
    [includeHistory, setIncludeHistory] = useState(false);
  const operation = useRef<{
    content: string;
    id: string;
    entry: string;
  } | null>(null);
  const lastActivity = useRef(Date.now()),
    lastPing = useRef(Date.now()),
    generation = useRef(0),
    active = useRef(true);
  async function lock() {
    active.current = false;
    generation.current++;
    onLock();
    try {
      await api("auth/lock", csrf, "POST", {});
    } catch {}
  }
  function failed(err: unknown) {
    if (err instanceof ApiError && err.status === 401) {
      void lock();
    } else if (active.current) setError(message(err));
  }
  useEffect(() => {
    function activity() {
      if (Date.now() - lastActivity.current >= 900000) {
        void lock();
        return;
      }
      lastActivity.current = Date.now();
      if (Date.now() - lastPing.current > 30000) {
        lastPing.current = Date.now();
        api("auth/session", csrf).catch(failed);
      }
    }
    function visible() {
      if (Date.now() - lastActivity.current >= 900000) void lock();
    }
    const timer = setInterval(visible, 1000);
    window.addEventListener("pointerdown", activity);
    window.addEventListener("keydown", activity);
    window.addEventListener("focus", visible);
    document.addEventListener("visibilitychange", visible);
    return () => {
      active.current = false;
      generation.current++;
      clearInterval(timer);
      window.removeEventListener("pointerdown", activity);
      window.removeEventListener("keydown", activity);
      window.removeEventListener("focus", visible);
      document.removeEventListener("visibilitychange", visible);
    };
  }, []);
  async function load(more = false) {
    const seq = ++generation.current;
    setLoading(true);
    setError("");
    const query = new URLSearchParams({ q, limit: "30" });
    if (filter) query.set("type", filter);
    if (tag) query.set("tag", tag);
    if (from) query.set("date_from", from);
    if (to) query.set("date_to", to);
    if (more && cursor) query.set("cursor", cursor);
    try {
      const r = await api("entries?" + query, csrf);
      const data = await r.json();
      if (active.current && seq === generation.current) {
        setEntries((old) => (more ? [...old, ...data.items] : data.items));
        setCursor(data.next_cursor);
      }
    } catch (err) {
      failed(err);
    } finally {
      if (active.current && seq === generation.current) setLoading(false);
    }
  }
  useEffect(() => {
    const t = setTimeout(() => {
      void load();
    }, 180);
    return () => clearTimeout(t);
  }, [q, filter, tag, from, to]);
  function open(entry: Entry | "new") {
    operation.current = null;
    setEditing(entry);
    setHistory(null);
    setError("");
    setConflict(false);
    setNotice("");
    if (entry === "new") setDraft(blank());
    else
      setDraft({
        ...blank(),
        ...Object.fromEntries(
          Object.keys(blank()).map((k) => [
            k,
            String(entry[k as keyof Entry] ?? ""),
          ]),
        ),
        type: entry.type,
        tags: entry.tags.join(", "),
      } as Draft);
  }
  function payload() {
    const p: Record<string, unknown> = {
      type: draft.type,
      raw_text: draft.raw_text,
      tags: draft.tags ? draft.tags.split(",").map((x) => x.trim()) : [],
      timezone: draft.timezone,
      time_precision: draft.time_precision,
      occurred_at_utc: draft.occurred_at_utc || null,
      local_date: draft.local_date || null,
    };
    for (const key of typed[draft.type]) {
      const value = draft[key as keyof Draft];
      p[key] =
        key.endsWith("rating") || key === "sleep_quality"
          ? value === ""
            ? null
            : Number(value)
          : value || null;
    }
    if (draft.type === "sleep" && draft.wake_at_utc) {
      const d = new Date(draft.wake_at_utc);
      if (!Number.isNaN(d.getTime())) {
        p.occurred_at_utc = draft.wake_at_utc;
        p.time_precision = "instant";
        p.local_date = new Intl.DateTimeFormat("en-CA", {
          timeZone: draft.timezone,
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
        }).format(d);
      }
    }
    return p;
  }
  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setConflict(false);
    try {
      const p = payload();
      let confirmed = false;
      if (
        editing &&
        editing !== "new" &&
        editing.type !== draft.type &&
        typed[editing.type].some((k) => editing[k as keyof Entry] != null)
      ) {
        confirmed = window.confirm(
          "Зміна типу прибере з поточної версії поля: " +
            typed[editing.type].map((k) => fieldNames[k]).join(", ") +
            ". Попередня версія залишиться в історії. Продовжити?",
        );
        if (!confirmed) return;
      }
      const content = JSON.stringify(p);
      if (!operation.current || operation.current.content !== content)
        operation.current = {
          content,
          id: crypto.randomUUID(),
          entry:
            editing && editing !== "new" ? editing.id : crypto.randomUUID(),
        };
      const op = operation.current;
      const creating = editing === "new";
      await api(
        creating ? "entries" : "entries/" + op.entry,
        csrf,
        creating ? "POST" : "PATCH",
        creating
          ? {
              operation_id: op.id,
              entry_id: op.entry,
              base_revision: 0,
              payload: p,
            }
          : {
              operation_id: op.id,
              base_revision: (editing as Entry).revision,
              changes: p,
              confirm_type_change: confirmed,
            },
      );
      if (active.current) {
        setEditing(null);
        setDraft(blank());
        operation.current = null;
        setNotice("Збережено на Mac");
        setPlan(null);
        await load();
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) setConflict(true);
      failed(err);
    } finally {
      if (active.current) setBusy(false);
    }
  }
  async function showHistory(entry: Entry, more = false) {
    try {
      const r = await api(
        `entries/${entry.id}/revisions${more ? "?after=" + historyAfter : ""}`,
        csrf,
      );
      const data = await r.json();
      if (active.current) {
        setHistory((old) =>
          more ? [...(old || []), ...data.items] : data.items,
        );
        setHistoryId(entry.id);
        setHistoryAfter(data.next_after);
        setEditing(null);
        setDraft(blank());
      }
    } catch (err) {
      failed(err);
    }
  }
  async function remove(entry: Entry) {
    if (
      !window.confirm(
        "Видалити запис та всю історію? Старі експорти й резервні копії залишаться поза щоденником.",
      )
    )
      return;
    try {
      await api("entries/" + entry.id, csrf, "DELETE", {
        operation_id: crypto.randomUUID(),
        base_revision: entry.revision,
      });
      if (active.current) {
        setSelected((s) => new Set([...s].filter((id) => id !== entry.id)));
        setHistory(null);
        setPlan(null);
        setNotice("Запис та історію видалено");
        await load();
      }
    } catch (err) {
      failed(err);
    }
  }
  async function preview() {
    try {
      const r = await api("exports/preview", csrf, "POST", {
        ids: [...selected],
        include_history: includeHistory,
      });
      const p = await r.json();
      if (active.current) setPlan(p);
    } catch (err) {
      failed(err);
    }
  }
  async function download(format: string) {
    if (!plan) return;
    try {
      const r = await api("exports", csrf, "POST", {
        plan_id: plan.plan_id,
        format,
      });
      const blob = await r.blob();
      if (!active.current) return;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "selected-journal." + (format === "json" ? "json" : "md");
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
      setPlan(null);
      failed(err);
    }
  }
  function change(key: keyof Draft, value: string) {
    setDraft((d) => ({ ...d, [key]: value }));
  }
  return (
    <div className="workspace">
      <aside className="sidebar">
        <a className="wordmark" href="/">
          Особистий <br />
          простір
        </a>
        <p className="side-note">
          Думки, яким можна
          <br />
          дати місце.
        </p>
        <nav aria-label="Розділи щоденника">
          <button
            className={!filter ? "current" : ""}
            onClick={() => setFilter("")}
          >
            Усі записи
          </button>
          {Object.entries(names).map(([k, v]) => (
            <button
              key={k}
              className={filter === k ? "current" : ""}
              onClick={() => setFilter(k)}
            >
              {v}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <p>
            Synthetic demo
            <br />
            Лише на цьому Mac
          </p>
          <button
            onClick={() => {
              void lock();
            }}
          >
            Заблокувати
          </button>
        </div>
      </aside>
      <main className="journal">
        <header>
          <div>
            <h1>{filter ? names[filter as Kind] : "Ваш щоденник"}</h1>
            <p>Записуйте у своєму ритмі. Усі поля, крім тексту, добровільні.</p>
          </div>
          <button className="primary add" onClick={() => open("new")}>
            <span aria-hidden="true">+</span> Додати запис
          </button>
        </header>
        <AssistantPanel csrf={csrf} selected={selected} onChanged={load} />
        <section className="filters" aria-label="Пошук і фільтри">
          <label className="search">
            Пошук
            <input
              type="search"
              placeholder="Знайти думку чи ідею…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              maxLength={200}
            />
          </label>
          <details>
            <summary>Теги та дати</summary>
            <div className="field-row">
              <label>
                Тег
                <input value={tag} onChange={(e) => setTag(e.target.value)} />
              </label>
              <label>
                Від дати
                <input
                  type="date"
                  value={from}
                  onChange={(e) => setFrom(e.target.value)}
                />
              </label>
              <label>
                До дати
                <input
                  type="date"
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                />
              </label>
            </div>
          </details>
        </section>
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
        {editing && (
          <EntryEditor
            title={editing === "new" ? "Нова нотатка" : "Редагувати запис"}
            draft={draft}
            change={change}
            save={save}
            cancel={() => {
              setEditing(null);
              setDraft(blank());
            }}
            busy={busy}
            saveLabel="Зберегти на Mac"
            onRefresh={
              conflict && editing !== "new"
                ? async () => {
                    try {
                      const r = await api("entries/" + editing.id, csrf);
                      open(await r.json());
                    } catch (err) {
                      failed(err);
                    }
                  }
                : undefined
            }
          />
        )}
        {history !== null && (
          <section className="history">
            <div className="actions">
              <h2>Історія запису</h2>
              <button onClick={() => setHistory(null)}>Закрити історію</button>
            </div>
            {history.length ? (
              history.map((x) => (
                <article key={x.revision}>
                  <p className="metadata">
                    Версія {x.revision} · {names[x.type]}
                  </p>
                  <p className="entry-text">{x.raw_text}</p>
                </article>
              ))
            ) : (
              <p>Попередніх версій ще немає.</p>
            )}
            {historyAfter !== null && (
              <button
                onClick={() => {
                  void showHistory({ id: historyId } as Entry, true);
                }}
              >
                Ще версії
              </button>
            )}
          </section>
        )}
        <div className="list-heading">
          <h2>{q ? "Результати пошуку" : "Останні записи"}</h2>
          <span>{entries.length} на екрані</span>
        </div>
        {loading && <p role="status">Завантажуємо записи…</p>}
        {!loading && !entries.length && (
          <div className="empty">
            <h2>{q ? "Поки нічого не знайдено" : "Почніть із кількох слів"}</h2>
            <p>
              {q
                ? "Спробуйте інше слово або змініть фільтри."
                : "Не потрібна ідеальна думка. Достатньо того, що хочеться зберегти."}
            </p>
          </div>
        )}
        <div className="entries">
          {entries.map((entry) => (
            <article className="entry" key={entry.id}>
              <div className="entry-top">
                <p className="metadata">
                  {names[entry.type]} ·{" "}
                  {entry.local_date ||
                    new Intl.DateTimeFormat("uk", {
                      day: "numeric",
                      month: "long",
                    }).format(new Date(entry.created_at_utc))}{" "}
                  · версія {entry.revision}
                </p>
                <label className="select-entry">
                  <input
                    type="checkbox"
                    checked={selected.has(entry.id)}
                    onChange={(e) => {
                      setSelected((s) => {
                        const n = new Set(s);
                        e.target.checked ? n.add(entry.id) : n.delete(entry.id);
                        return n;
                      });
                      setPlan(null);
                    }}
                  />
                  Вибрати
                </label>
              </div>
              <p className="entry-text">{entry.raw_text}</p>
              {entry.tags.length > 0 && (
                <p className="tags">{entry.tags.join(" · ")}</p>
              )}
              {typed[entry.type]
                .filter((k) => entry[k as keyof Entry] != null)
                .map((k) => (
                  <p className="metadata" key={k}>
                    {fieldNames[k]}:{" "}
                    {k === "creative_kind"
                      ? creativeNames[String(entry[k as keyof Entry])]
                      : String(entry[k as keyof Entry])}
                  </p>
                ))}
              {entry.reported_interval_seconds != null && (
                <p className="metadata">
                  Інтервал за введеними оцінками:{" "}
                  {Math.round(entry.reported_interval_seconds / 60)} хв
                </p>
              )}
              <div className="entry-actions">
                <button onClick={() => open(entry)}>Редагувати</button>
                <button
                  onClick={() => {
                    void showHistory(entry);
                  }}
                >
                  Історія
                </button>
                <button
                  className="danger"
                  onClick={() => {
                    void remove(entry);
                  }}
                >
                  Видалити
                </button>
              </div>
            </article>
          ))}
        </div>
        {cursor && (
          <button
            disabled={loading}
            onClick={() => {
              void load(true);
            }}
          >
            Ще записи
          </button>
        )}
        {selected.size > 0 && (
          <section className="export" aria-label="Вибраний експорт">
            <h2>Експорт вибраних записів</h2>
            <p>
              Вибрано: {selected.size}. Файл завантажиться на цей комп’ютер.
            </p>
            <label className="check">
              <input
                type="checkbox"
                checked={includeHistory}
                onChange={(e) => {
                  setIncludeHistory(e.target.checked);
                  setPlan(null);
                }}
              />
              Додати історію
            </label>
            <button
              onClick={() => {
                void preview();
              }}
            >
              Переглянути експорт
            </button>
            {plan && (
              <div>
                <p>{plan.warning}</p>
                <p>
                  Точний склад: {plan.count} записів ·{" "}
                  {plan.sections.map((k) => names[k]).join(", ")}
                </p>
                <ul>
                  {plan.refs.map((x) => (
                    <li key={x.id}>
                      {x.id} · версія {x.revision}
                    </li>
                  ))}
                </ul>
                <div className="actions">
                  <button
                    onClick={() => {
                      void download("json");
                    }}
                  >
                    Завантажити JSON
                  </button>
                  <button
                    onClick={() => {
                      void download("markdown");
                    }}
                  >
                    Завантажити Markdown
                  </button>
                  <button onClick={() => setPlan(null)}>
                    Скасувати експорт
                  </button>
                </div>
              </div>
            )}
          </section>
        )}
        <MacSyncSettings csrf={csrf} />
        <footer>
          Чернетки живуть лише у відкритій вкладці. Reload або блокування
          прибирає незбережений текст.
          <br />
          Зовнішній AI вимкнено · цей demo використовує лише вигадані записи.
        </footer>
      </main>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  location.pathname.startsWith("/phone/") ? <PhoneApp /> : <App />,
);
