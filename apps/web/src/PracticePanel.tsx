import { useEffect, useRef, useState } from "react";
import {
  practiceError,
  practiceStateNames,
  responseReady,
  responseFor,
  type Catalog,
  type PracticeItem,
  type PracticeHistory,
  type PracticeSession,
} from "./practice-model";

export function PracticePanel({
  csrf,
  onLeave,
}: {
  csrf: string;
  onLeave: () => void;
}) {
  const [catalog, setCatalog] = useState<Catalog | null>(null),
    [history, setHistory] = useState<PracticeHistory[]>([]),
    [nextOffset, setNextOffset] = useState<number | null>(null),
    [session, setSession] = useState<PracticeSession | null>(null);
  const [input, setInput] = useState<string | boolean>(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [confirmDelete, setConfirmDelete] = useState(false),
    [showResponses, setShowResponses] = useState(false);
  const live = useRef(true),
    inflight = useRef(false),
    sequence = useRef(0),
    heading = useRef<HTMLHeadingElement>(null);
  const pending = useRef<{ signature: string; operation_id: string } | null>(
    null,
  );
  async function request(path: string, method = "GET", body?: unknown) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 6000);
    try {
      const r = await fetch("/api/v1/practices/" + path, {
        method,
        credentials: "same-origin",
        cache: "no-store",
        signal: controller.signal,
        headers: {
          ...(body
            ? { "Content-Type": "application/json", "X-CSRF-Token": csrf }
            : {}),
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!r.ok) {
        const d = await r.json();
        throw new Error(d.code || "FAILED");
      }
      return r.json();
    } finally {
      clearTimeout(timeout);
    }
  }
  async function refresh() {
    const [c, h] = await Promise.all([request("catalog"), request("sessions")]);
    if (live.current) {
      setCatalog(c);
      setHistory(h.items);
      setNextOffset(h.next_offset);
    }
  }
  useEffect(() => {
    live.current = true;
    void refresh().catch(() => {
      if (live.current)
        setError("Практики зараз недоступні. Інші розділи працюють незалежно.");
    });
    return () => {
      live.current = false;
      sequence.current++;
    };
  }, []);
  useEffect(() => {
    heading.current?.focus();
  }, [session?.id, session?.current_step, session?.state]);
  function show(s: PracticeSession) {
    setSession(s);
    setInput(responseFor(s.responses, s.current_step)?.value ?? "");
    setShowResponses(false);
    setConfirmDelete(false);
  }
  async function open(id: string) {
    if (inflight.current) return;
    inflight.current = true;
    setBusy(true);
    setError("");
    const seq = ++sequence.current;
    try {
      const s = await request("sessions/" + id);
      if (live.current && seq === sequence.current) show(s);
    } catch (e) {
      if (live.current) setError(practiceError((e as Error).message));
    } finally {
      inflight.current = false;
      if (live.current) setBusy(false);
    }
  }
  async function mutate(
    path: string,
    body: Record<string, unknown>,
    message = "",
    keepInput = false,
  ) {
    if (inflight.current) return;
    inflight.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const seq = ++sequence.current;
    const signature = JSON.stringify({ path, body });
    if (pending.current?.signature !== signature)
      pending.current = { signature, operation_id: crypto.randomUUID() };
    try {
      const s = await request(path, "POST", {
        ...body,
        operation_id: pending.current.operation_id,
      });
      if (live.current && seq === sequence.current) {
        pending.current = null;
        if (s.state === "DELETED") {
          setSession(null);
          setInput("");
          setShowResponses(false);
          setConfirmDelete(false);
        } else {
          setSession(s);
          if (!keepInput)
            setInput(responseFor(s.responses, s.current_step)?.value ?? "");
        }
        setNotice(message);
        await refresh();
      }
    } catch (e) {
      if (live.current && seq === sequence.current) {
        const code = (e as Error).message;
        setError(practiceError(code));
        if (code === "REVISION_CONFLICT" && session) {
          try {
            const s = await request("sessions/" + session.id);
            if (live.current && seq === sequence.current) {
              setSession(s);
              if (s.state === "BLOCKED_BY_ADMISSION")
                setError(practiceError("PRACTICE_BINDING_STALE"));
              pending.current = null;
            }
          } catch {
            /* Preserve input and the recoverable error if the refresh also fails. */
          }
        }
      }
    } finally {
      inflight.current = false;
      if (live.current) setBusy(false);
    }
  }
  function action(name: string, save = false) {
    if (!session) return;
    return mutate(
      "sessions/" + session.id + "/actions",
      {
        base_revision: session.revision,
        action: name,
        ...(["save", "next", "skip", "complete"].includes(name)
          ? { step_id: session.current_step }
          : {}),
        ...(save ? { response: input } : {}),
      },
      name === "save"
        ? "Відповідь збережено локально."
        : name === "delete"
          ? "Сесію видалено."
          : "",
      save,
    );
  }
  function start(item: PracticeItem) {
    void mutate("sessions", {
      module_id: item.module_id,
      module_version: item.module_version,
      content_hash: item.content_hash,
    });
  }
  function leave() {
    sequence.current++;
    onLeave();
  }
  const step = session?.current_step_definition;
  const terminal =
    session &&
    ["STOPPED", "COMPLETED", "BLOCKED_BY_ADMISSION"].includes(session.state);
  const changed =
    !!step &&
    input !==
      ((session && responseFor(session.responses, step.id)?.value) ?? "");
  const saved =
    !!step && !!session && !!responseFor(session.responses, step.id);
  return (
    <section className="practice-panel" aria-labelledby="practice-title">
      <header className="practice-header">
        <h1 id="practice-title">Практики</h1>
        <button onClick={leave}>До щоденника</button>
      </header>
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      {!catalog && !error && <p role="status">Відкриваємо практики…</p>}
      {!session ? (
        <>
          {catalog && (
            <div className="practice-catalog">
              {catalog.synthetic_demo && (
                <p className="practice-demo-badge">Демо · лише вигадані дані</p>
              )}
              {catalog.items
                .filter((x) => x.available)
                .map((item) => (
                  <article className="practice-offer" key={item.module_id}>
                    <h2>{item.title}</h2>
                    <p>{item.description}</p>
                    <button
                      className="primary"
                      disabled={busy}
                      onClick={() => start(item)}
                    >
                      Почати демо
                    </button>
                  </article>
                ))}
              <h2>Перевірені практики ще готуються</h2>
              <p>
                Зараз немає доступних перевірених практик. Щоденник та інші
                розділи можна використовувати незалежно.
              </p>
              <details>
                <summary>Чому вони недоступні?</summary>
                <p>
                  Зміст і дозволи мають пройти окрему перевірку. Демо показує
                  лише роботу інтерфейсу.
                </p>
                <p>
                  Доступних клінічних практик:{" "}
                  {catalog.production_active_clinical}.
                </p>
              </details>
            </div>
          )}
          <section
            aria-labelledby="practice-history-title"
            className="practice-history"
          >
            <h2 id="practice-history-title">Історія сесій</h2>
            {history.length === 0 ? (
              <p>Тут з’являться сесії, які ви вирішите розпочати.</p>
            ) : (
              <ol>
                {history.map((s) => (
                  <li key={s.id}>
                    <div>
                      <strong>{s.title}</strong>
                      <p>
                        <time dateTime={s.started_utc}>
                          {new Date(s.started_utc).toLocaleString("uk-UA")}
                        </time>{" "}
                        · Версія {s.module_version}
                      </p>
                      <span>{practiceStateNames[s.state]}</span>
                    </div>
                    <button disabled={busy} onClick={() => void open(s.id)}>
                      {s.state === "ACTIVE" || s.state === "PAUSED"
                        ? "Повернутися до сесії"
                        : "Переглянути сесію"}
                    </button>
                  </li>
                ))}
              </ol>
            )}
            {nextOffset !== null && (
              <button
                disabled={busy}
                onClick={() => {
                  if (inflight.current) return;
                  inflight.current = true;
                  setBusy(true);
                  void request("sessions?offset=" + nextOffset)
                    .then((h) => {
                      if (live.current) {
                        setHistory((old) => [...old, ...h.items]);
                        setNextOffset(h.next_offset);
                      }
                    })
                    .catch(() => {
                      if (live.current)
                        setError(
                          "Не вдалося відкрити старші сесії. Спробуйте ще раз.",
                        );
                    })
                    .finally(() => {
                      inflight.current = false;
                      if (live.current) setBusy(false);
                    });
                }}
              >
                Старші сесії
              </button>
            )}
          </section>
        </>
      ) : (
        <article className="practice-session">
          <p className="practice-demo-badge">
            {session.title} · версія {session.module_version}
          </p>
          <h2 ref={heading} tabIndex={-1}>
            {practiceStateNames[session.state]}
          </h2>
          {session.step_number && (
            <p className="practice-progress">
              Крок {session.step_number} із {session.step_count}
            </p>
          )}
          {session.state === "ACTIVE" && step && (
            <>
              <p className="practice-step-text">{step.text}</p>
              {step.kind === "acknowledgement" && (
                <label className="practice-checkbox">
                  <input
                    type="checkbox"
                    checked={input === true}
                    onChange={(e) => setInput(e.target.checked)}
                    disabled={busy}
                  />
                  Використовую лише вигадані дані
                </label>
              )}
              {(step.kind === "short_text" || step.kind === "long_text") && (
                <label htmlFor="practice-response">
                  Тестовий текст
                  <textarea
                    id="practice-response"
                    rows={step.kind === "short_text" ? 4 : 8}
                    maxLength={step.kind === "short_text" ? 500 : 12000}
                    value={typeof input === "string" ? input : ""}
                    onChange={(e) => setInput(e.target.value)}
                    disabled={busy}
                    aria-describedby="practice-response-hint"
                  />
                </label>
              )}
              {(step.kind === "short_text" || step.kind === "long_text") && (
                <p className="hint" id="practice-response-hint">
                  Відповідь залишається в цій сесії. До щоденника її не буде
                  додано.
                </p>
              )}
              {step.kind === "single_choice" && (
                <fieldset>
                  <legend>Необов’язковий вибір</legend>
                  {step.choices.map((c) => (
                    <label className="practice-choice" key={c.id}>
                      <input
                        type="radio"
                        name="practice-choice"
                        value={c.id}
                        checked={input === c.id}
                        onChange={() => setInput(c.id)}
                        disabled={busy}
                      />
                      {c.label}
                    </label>
                  ))}
                </fieldset>
              )}
              <div className="practice-actions">
                {!["information", "completion"].includes(step.kind) && (
                  <button
                    disabled={
                      busy || !responseReady(step, input) || (!changed && saved)
                    }
                    onClick={() => void action("save", true)}
                  >
                    Зберегти відповідь
                  </button>
                )}
                {step.kind === "completion" ? (
                  <button
                    className="primary"
                    disabled={busy}
                    onClick={() => void action("complete")}
                  >
                    Завершити сесію
                  </button>
                ) : (
                  <button
                    className="primary"
                    disabled={
                      busy ||
                      (step.kind !== "information" && (!saved || changed))
                    }
                    onClick={() => void action("next")}
                  >
                    Далі
                  </button>
                )}
                {step.optional && (
                  <button disabled={busy} onClick={() => void action("skip")}>
                    Пропустити крок
                  </button>
                )}
              </div>
            </>
          )}
          {session.state === "PAUSED" && (
            <>
              <p>
                Ваші відповіді збережені. Продовжити можна тоді, коли ви
                вирішите.
              </p>
              <button
                className="primary"
                disabled={busy}
                onClick={() => void action("resume")}
              >
                Продовжити практику
              </button>
            </>
          )}
          {session.state === "BLOCKED_BY_ADMISSION" && (
            <p>
              Дозвіл або версія змінилися. Цю сесію не можна продовжити.
              Збережені відповіді можна переглянути або видалити.
            </p>
          )}
          {session.state === "STOPPED" && (
            <p>Сесія залишилася в історії. Можна повернутися до інших справ.</p>
          )}
          {session.state === "COMPLETED" && (
            <p>
              Сесію завершено. Відповіді залишаються в історії, доки ви їх не
              видалите.
            </p>
          )}
          <div className="practice-controls">
            {session.state === "ACTIVE" && (
              <button disabled={busy} onClick={() => void action("pause")}>
                Призупинити
              </button>
            )}
            {!["STOPPED", "COMPLETED"].includes(session.state) && (
              <button disabled={busy} onClick={() => void action("stop")}>
                Зупинити практику
              </button>
            )}
            <button
              onClick={() => {
                sequence.current++;
                setSession(null);
                setConfirmDelete(false);
                setShowResponses(false);
                setNotice("");
                void refresh();
              }}
            >
              До каталогу
            </button>
          </div>
          {terminal && (
            <p className="hint">
              Щоб почати знову, поверніться до каталогу — буде створено окрему
              сесію.
            </p>
          )}
          <button
            aria-expanded={showResponses}
            onClick={() => setShowResponses((x) => !x)}
          >
            Збережені відповіді
          </button>
          {showResponses && (
            <dl className="practice-responses">
              {Object.entries(session.responses).map(([id, r]) => (
                <div key={id}>
                  <dt>Збережена відповідь · редакція {r.revision}</dt>
                  <dd>
                    {r.value === true
                      ? "Підтверджено"
                      : r.value === false
                        ? "Не підтверджено"
                        : r.value}
                  </dd>
                </div>
              ))}
              {Object.keys(session.responses).length === 0 && (
                <p>Збережених відповідей ще немає.</p>
              )}
            </dl>
          )}
          <div className="practice-delete">
            {!confirmDelete ? (
              <button disabled={busy} onClick={() => setConfirmDelete(true)}>
                Видалити сесію
              </button>
            ) : (
              <>
                <p>
                  Видалити сесію та всі її відповіді? Записи щоденника
                  залишаться. Старі резервні копії можуть містити попередні
                  версії.
                </p>
                <button disabled={busy} onClick={() => void action("delete")}>
                  Так, видалити сесію
                </button>
                <button disabled={busy} onClick={() => setConfirmDelete(false)}>
                  Залишити сесію
                </button>
              </>
            )}
          </div>
        </article>
      )}
    </section>
  );
}
