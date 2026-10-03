import { useEffect, useRef, useState } from "react";
import {
  ReflectionGoals,
  DeepContext,
  type ReflectionGoal,
} from "./ReflectionGoals";
import { Sheet } from "./Sheet";
import { VoicePanel } from "./VoicePanel";
import { InferencePanel } from "./InferencePanel";
import { JournalPoint } from "./JournalPoint";
import {
  chatError,
  validChatText,
  sendShortcut,
  type Conversation,
  type ConversationPage,
  type ConversationStatus,
  type VoiceReference,
} from "./conversation-model";

export function ConversationHome({
  csrf,
  onPractice,
}: {
  csrf: string;
  onPractice: () => void;
}) {
  const [status, setStatus] = useState<ConversationStatus | null>(null),
    [page, setPage] = useState<ConversationPage | null>(null),
    [text, setText] = useState(""),
    [source, setSource] = useState<VoiceReference | null>(null);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [historyOpen, setHistoryOpen] = useState(false),
    [history, setHistory] = useState<Conversation[]>([]),
    [archived, setArchived] = useState(false),
    [nextOffset, setNextOffset] = useState<number | null>(null),
    [deleteTarget, setDeleteTarget] = useState<Conversation | null>(null),
    [voice, setVoice] = useState<"idle" | "record" | null>(null);
  const [goalsOpen, setGoalsOpen] = useState(false);
  const [goalRefresh, setGoalRefresh] = useState(0);
  const [goalPreset, setGoalPreset] = useState("");
  const [journalOpen, setJournalOpen] = useState(false);
  const alive = useRef(true),
    working = useRef(false),
    generation = useRef(0),
    composer = useRef<HTMLTextAreaElement>(null),
    messages = useRef<HTMLDivElement>(null);
  const creating = useRef<string | null>(null),
    pending = useRef<{ signature: string; operation_id: string } | null>(null);
  const pendingAction = useRef<{ signature: string; id: string } | null>(null);
  const deepCreating = useRef<{ signature: string; id: string } | null>(null);
  const stored = "personal-companion-conversation-selection-v1";
  async function api(path: string, body?: unknown) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8000);
    try {
      const r = await fetch("/api/v1/conversations" + path, {
        method: body ? "POST" : "GET",
        credentials: "same-origin",
        cache: "no-store",
        headers: body
          ? { "Content-Type": "application/json", "X-CSRF-Token": csrf }
          : {},
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });
      if (!r.ok) {
        const d = await r.json();
        throw new Error(d.code);
      }
      return await r.json();
    } finally {
      clearTimeout(timer);
    }
  }
  function selection(p: ConversationPage | null) {
    setPage(p);
    try {
      p
        ? localStorage.setItem(stored, p.conversation.id)
        : localStorage.removeItem(stored);
    } catch {}
  }
  async function load(id: string) {
    let data: ConversationPage = await api("/" + id);
    let after = data.next_after;
    while (after !== null) {
      const next = await api("/" + id + "?after=" + after);
      data.messages.push(...next.messages);
      after = next.next_after;
      if (data.messages.length >= 2000) break;
    }
    return data;
  }
  useEffect(() => {
    alive.current = true;
    const seq = ++generation.current;
    void (async () => {
      const s = await api("/status");
      if (!alive.current) return;
      setStatus(s);
      let id = null;
      try {
        id = localStorage.getItem(stored);
      } catch {}
      if (id) {
        try {
          const p = await load(id);
          if (alive.current && seq === generation.current) selection(p);
        } catch {
          if (alive.current) selection(null);
        }
      }
    })().catch(() => {
      if (alive.current)
        setError(
          "Розмова зараз недоступна. Щоденник можна відкрити незалежно.",
        );
    });
    return () => {
      alive.current = false;
      generation.current++;
    };
  }, []);
  useEffect(() => {
    messages.current?.scrollTo({ top: messages.current.scrollHeight });
  }, [page?.messages.length]);
  useEffect(() => {
    const v = window.visualViewport;
    const update = () =>
      document.documentElement.style.setProperty(
        "--conversation-viewport",
        `${v?.height ?? window.innerHeight}px`,
      );
    const header = document.querySelector(".app-topbar") as HTMLElement | null;
    document.documentElement.style.setProperty(
      "--app-header-height",
      `${header?.getBoundingClientRect().height ?? 80}px`,
    );
    const measured = () => {
      update();
      document.documentElement.style.setProperty(
        "--app-header-height",
        `${header?.getBoundingClientRect().height ?? 80}px`,
      );
    };
    measured();
    window.addEventListener("resize", measured);
    v?.addEventListener("resize", update);
    return () => {
      v?.removeEventListener("resize", update);
      window.removeEventListener("resize", measured);
      document.documentElement.style.removeProperty("--conversation-viewport");
    };
  }, []);
  async function recent(more = false) {
    const h = await api(
      `?archived=${archived}&offset=${more ? (nextOffset ?? 0) : 0}`,
    );
    if (alive.current) {
      setHistory((old) => (more ? [...old, ...h.items] : h.items));
      setNextOffset(h.next_offset);
    }
  }
  useEffect(() => {
    if (historyOpen)
      void recent().catch(() =>
        setError("Не вдалося відкрити історію. Спробуйте ще раз."),
      );
  }, [historyOpen, archived]);
  async function open(id: string) {
    if (working.current) return;
    working.current = true;
    setBusy(true);
    setError("");
    const seq = ++generation.current;
    try {
      const p = await load(id);
      if (alive.current && seq === generation.current) {
        selection(p);
        setText("");
        setSource(null);
        setHistoryOpen(false);
      }
    } catch (e) {
      if (alive.current) setError(chatError((e as Error).message));
    } finally {
      working.current = false;
      if (alive.current) setBusy(false);
    }
  }
  async function send(
    purpose: "REFLECT" | "GOAL_PROPOSAL" | "CLOSURE" = "REFLECT",
    override?: string,
  ) {
    const input = override ?? text;
    if (working.current || !validChatText(input)) return;
    working.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    const seq = ++generation.current;
    const sent = input;
    try {
      let current = page;
      if (!current) {
        creating.current ??= crypto.randomUUID();
        current = await api("", { operation_id: creating.current });
        creating.current = null;
        if (alive.current && seq === generation.current) selection(current);
      }
      const body = {
        base_revision: current!.conversation.revision,
        text: sent,
        source_reference: source,
        ...(status?.mode ? { purpose, synthetic_test_ack: true } : {}),
      };
      const signature = JSON.stringify({ id: current!.conversation.id, body });
      if (pending.current?.signature !== signature)
        pending.current = { signature, operation_id: crypto.randomUUID() };
      const result = await api(
        "/" +
          current!.conversation.id +
          (status?.mode ? "/inference" : "/messages"),
        {
          ...body,
          operation_id: pending.current.operation_id,
        },
      );
      const fresh =
        result.next_after !== null
          ? await load(current!.conversation.id)
          : result;
      if (alive.current && seq === generation.current) {
        selection(fresh);
        setText("");
        setSource(null);
        setGoalsOpen(false);
        pending.current = null;
        if (status?.responder === "OFF")
          setNotice(
            "Повідомлення збережено лише в цій розмові. AI-відповіді зараз недоступні.",
          );
        composer.current?.focus();
      }
    } catch (e) {
      if (alive.current && seq === generation.current) {
        const code = (e as Error).message;
        setError(chatError(code));
        if (code === "REVISION_CONFLICT" && page) {
          try {
            const p = await load(page.conversation.id);
            if (alive.current) {
              selection(p);
              pending.current = null;
            }
          } catch {}
        }
      }
    } finally {
      working.current = false;
      if (alive.current) setBusy(false);
    }
  }
  async function action(
    c: Conversation,
    name: "archive" | "unarchive" | "delete",
  ) {
    if (working.current) return;
    working.current = true;
    setBusy(true);
    setError("");
    try {
      const signature = JSON.stringify({
        id: c.id,
        revision: c.revision,
        name,
      });
      if (pendingAction.current?.signature !== signature)
        pendingAction.current = { signature, id: crypto.randomUUID() };
      await api("/" + c.id + "/actions", {
        operation_id: pendingAction.current.id,
        base_revision: c.revision,
        action: name,
      });
      if (alive.current) {
        pendingAction.current = null;
        if (page?.conversation.id === c.id) selection(null);
        setDeleteTarget(null);
        setNotice(
          name === "delete" ? "Розмову видалено." : "Стан розмови змінено.",
        );
        await recent();
      }
    } catch (e) {
      if (alive.current) setError(chatError((e as Error).message));
    } finally {
      working.current = false;
      if (alive.current) setBusy(false);
    }
  }
  async function startDeep(g: ReflectionGoal) {
    if (working.current) return;
    working.current = true;
    setBusy(true);
    setError("");
    try {
      const signature = g.id + ":" + g.revision;
      if (deepCreating.current?.signature !== signature)
        deepCreating.current = { signature, id: crypto.randomUUID() };
      const p = await api("", {
        operation_id: deepCreating.current.id,
        goal_id: g.id,
        goal_revision: g.revision,
      });
      if (alive.current) {
        selection(p);
        setText("");
        setSource(null);
        setGoalsOpen(false);
        deepCreating.current = null;
      }
    } catch {
      if (alive.current)
        setError(
          "Не вдалося почати глибоку розмову. Перевірте актуальну ціль.",
        );
    } finally {
      working.current = false;
      if (alive.current) setBusy(false);
    }
  }
  function reset() {
    if (working.current) return;
    generation.current++;
    selection(null);
    setText("");
    setSource(null);
    pending.current = null;
    creating.current = null;
    setHistoryOpen(false);
    setError("");
    setNotice("");
    composer.current?.focus();
  }
  const hasMessages = !!page?.messages.length;
  const inferenceActive =
    !!page?.inference_job &&
    ["QUEUED", "RUNNING"].includes(page.inference_job.state);
  return (
    <section className="conversation-home" aria-label="Розмова">
      <div className="conversation-thread">
        <header className="conversation-toolbar">
          <h1>
            {page?.conversation.mode === "DEEP" ? "Глибока розмова" : "Розмова"}
          </h1>
          <div>
            <button onClick={() => setGoalsOpen(true)}>Цілі</button>
            {status?.mode &&
              page?.conversation.mode === "DEEP" &&
              hasMessages && (
                <button
                  disabled={busy || inferenceActive}
                  onClick={() =>
                    void send(
                      "CLOSURE",
                      "ORIGINAL SYNTHETIC · Явно прошу підсумувати цю сесію.",
                    )
                  }
                >
                  Підсумувати
                </button>
              )}
            <button onClick={() => setHistoryOpen(true)}>Розмови</button>
            <button disabled={busy} onClick={reset}>
              Нова розмова
            </button>
          </div>
        </header>
        {page?.conversation.mode === "DEEP" &&
          page.conversation.goal_binding && (
            <DeepContext
              key={page.conversation.id}
              csrf={csrf}
              conversationId={page.conversation.id}
              binding={page.conversation.goal_binding}
              syntheticDemo={status?.synthetic_demo ?? false}
              refreshVersion={goalRefresh}
            />
          )}
        {status?.synthetic_demo && (
          <p className="demo-status">
            {status.mode === "LIVE_SYNTHETIC"
              ? "Тест із вигаданими даними · помічник доступний"
              : status.mode === "OFF"
                ? "Тест із вигаданими даними · помічник вимкнений"
                : status.mode === "OFFLINE_FIXTURE"
                  ? "Демо · тестова відповідь без зовнішнього AI"
                  : "Демо · тестові відповіді без AI"}
          </p>
        )}
        {error && <p role="alert">{error}</p>}
        {notice && <p role="status">{notice}</p>}
        <div
          className="conversation-messages"
          ref={messages}
          aria-label="Повідомлення розмови"
          aria-live="polite"
          aria-relevant="additions"
        >
          {!hasMessages ? (
            <div className="conversation-empty">
              <h2>Про що хочеться поговорити?</h2>
              <p>
                Можна просто записати те, що на думці. Ви вирішуєте, що
                зберігати й коли повертатися.
              </p>
              <div className="conversation-intents">
                {[
                  "Просто виговоритися",
                  "Розібрати думку",
                  "Подивитися з іншого боку",
                ].map((intent) => (
                  <button
                    key={intent}
                    onClick={() => {
                      setText(intent + "\n");
                      composer.current?.focus();
                    }}
                  >
                    {intent}
                  </button>
                ))}
                <button onClick={onPractice}>Практики</button>
              </div>
            </div>
          ) : (
            <>
              {page!.messages.map((m) => (
                <article
                  key={m.id}
                  className={
                    "conversation-message message-" + m.role.toLowerCase()
                  }
                  aria-label={
                    m.role === "USER"
                      ? "Ваше повідомлення"
                      : m.provenance === "MODEL_GENERATED"
                        ? "Відповідь помічника"
                        : "Демо-відповідь помічника"
                  }
                >
                  <span className="message-role">
                    {m.role === "USER"
                      ? "Ви"
                      : m.provenance === "MODEL_GENERATED"
                        ? "Помічник"
                        : "Помічник · демо"}
                  </span>
                  <p>{m.raw_text}</p>
                </article>
              ))}
            </>
          )}
        </div>
        {page?.inference_job && (
          <InferencePanel
            key={page.inference_job.id}
            csrf={csrf}
            conversationId={page.conversation.id}
            job={page.inference_job}
            onChanged={(job, final) => {
              setPage((old) => (old ? { ...old, inference_job: job } : old));
              if (final)
                void load(page.conversation.id)
                  .then((p) => {
                    if (alive.current) selection(p);
                  })
                  .catch(() => setError("Не вдалося оновити розмову."));
            }}
            onGoal={(value) => {
              setGoalPreset(value);
              setGoalsOpen(true);
            }}
            onClose={() => void action(page.conversation, "archive")}
            onJournal={() => setJournalOpen(true)}
          />
        )}
      </div>
      <form
        className="conversation-composer"
        aria-label="Нове повідомлення"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        {!status?.synthetic_demo && status && (
          <p className="composer-privacy">
            Помічник поки недоступний. Ваш текст можна залишити в цій розмові
            локально.
          </p>
        )}
        {status?.synthetic_demo && (
          <p className="composer-privacy">
            {status.mode === "LIVE_SYNTHETIC"
              ? "Лише вигадані дані. Помічник отримує текст після надсилання."
              : status.mode === "OFF"
                ? "Лише вигадані дані. Помічник вимкнений; текст зберігається локально."
                : "Лише вигадані дані. Відповіді — локальні демонстраційні приклади."}
          </p>
        )}
        <label htmlFor="conversation-text" className="sr-only">
          Повідомлення
        </label>
        <textarea
          id="conversation-text"
          ref={composer}
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={
            busy || inferenceActive || page?.conversation.state === "ARCHIVED"
          }
          rows={3}
          maxLength={12000}
          placeholder="Напишіть кілька слів…"
          onKeyDown={(e) => {
            if (sendShortcut(e.nativeEvent)) {
              e.preventDefault();
              void send();
            }
          }}
        />
        <div className="composer-actions">
          <button
            type="button"
            aria-label="Записати голосом"
            aria-haspopup="dialog"
            disabled={busy}
            onClick={() => setVoice("record")}
          >
            <svg
              viewBox="0 0 24 24"
              width="20"
              height="20"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              aria-hidden="true"
            >
              <rect x="9" y="2" width="6" height="13" rx="3" />
              <path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8" />
            </svg>
          </button>
          <button type="button" onClick={() => setVoice("idle")}>
            Голосові записи
          </button>
          <button type="button" onClick={onPractice}>
            Практики
          </button>
          <span className="hint">Ctrl / ⌘ + Enter</span>
          <button
            className="primary"
            disabled={
              busy ||
              inferenceActive ||
              !validChatText(text) ||
              page?.conversation.state === "ARCHIVED"
            }
          >
            {busy
              ? "Зберігаємо…"
              : status?.synthetic_demo
                ? "Надіслати"
                : "Зберегти у розмові"}
          </button>
        </div>
        {page?.conversation.state === "ARCHIVED" && (
          <p>Розмова в архіві. Відкрийте її з «Розмови» або почніть нову.</p>
        )}
      </form>
      {goalsOpen && (
        <Sheet title="Цілі" onClose={() => setGoalsOpen(false)} wide>
          <ReflectionGoals
            csrf={csrf}
            initialText={goalPreset}
            onPropose={
              status?.mode && status.responder !== "OFF"
                ? (intent) => void send("GOAL_PROPOSAL", intent)
                : undefined
            }
            onStart={(g) => void startDeep(g)}
            onChanged={() => {
              setGoalRefresh((n) => n + 1);
            }}
          />
        </Sheet>
      )}
      {historyOpen && (
        <Sheet title="Розмови" onClose={() => setHistoryOpen(false)}>
          <button className="primary" disabled={busy} onClick={reset}>
            Нова розмова
          </button>
          <label className="check">
            <input
              type="checkbox"
              checked={archived}
              onChange={(e) => setArchived(e.target.checked)}
            />
            Архів
          </label>
          <ul className="conversation-history">
            {history.map((c) => (
              <li key={c.id}>
                <button
                  className="conversation-history-open"
                  disabled={busy}
                  onClick={() => void open(c.id)}
                >
                  {c.title}
                  <span>{new Date(c.updated_utc).toLocaleString("uk-UA")}</span>
                </button>
                <details>
                  <summary aria-label={"Дії: " + c.title}>Дії</summary>
                  <button
                    disabled={busy}
                    onClick={() =>
                      void action(
                        c,
                        c.state === "ARCHIVED" ? "unarchive" : "archive",
                      )
                    }
                  >
                    {c.state === "ARCHIVED" ? "Повернути з архіву" : "В архів"}
                  </button>
                  <button disabled={busy} onClick={() => setDeleteTarget(c)}>
                    Видалити розмову
                  </button>
                </details>
              </li>
            ))}
          </ul>
          {history.length === 0 && <p>Розмов ще немає.</p>}
          {nextOffset !== null && (
            <button onClick={() => void recent(true)}>Старші розмови</button>
          )}
          {deleteTarget && (
            <div role="group" aria-label="Підтвердження видалення розмови">
              <p>
                Видалити розмову та всі її повідомлення? Щоденник не зміниться.
                Старі резервні копії можуть містити попередні версії.
              </p>
              <button
                disabled={busy}
                onClick={() => void action(deleteTarget, "delete")}
              >
                Так, видалити розмову
              </button>
              <button onClick={() => setDeleteTarget(null)}>Залишити</button>
            </div>
          )}
        </Sheet>
      )}
      {journalOpen && page && (
        <JournalPoint csrf={csrf} conversationId={page.conversation.id} messages={page.messages} onClose={() => setJournalOpen(false)} />
      )}
      {voice && (
        <Sheet title="Голосовий ввід" onClose={() => setVoice(null)} wide>
          <VoicePanel
            csrf={csrf}
            autoStart={voice === "record"}
            allowSyntheticAsr={status?.synthetic_demo ?? false}
            onInsert={(value, ref) => {
              setText((old) => (old.trim() ? old + "\n" + value : value));
              setSource(ref);
              setVoice(null);
              composer.current?.focus();
            }}
          />
        </Sheet>
      )}
    </section>
  );
}
