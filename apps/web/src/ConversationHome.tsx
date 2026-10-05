import { useEffect, useRef, useState } from "react";
import { audioHash } from "./audio-types";
import { ComposerVoice, VoiceHistory, voiceCall } from "./ComposerVoice";
import {
  PrivatePilotControls,
  pilotCall,
  type PilotState,
} from "./PrivatePilotControls";
import {
  ReflectionGoals,
  DeepContext,
  type ReflectionGoal,
} from "./ReflectionGoals";
import { Sheet } from "./Sheet";
import { InferencePanel } from "./InferencePanel";
import {
  DeepSessionPanel,
  deepCall,
  type ContextSelection,
  type DeepPreview,
} from "./DeepSessionPanel";
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
  privateLocal = false,
  initialVoice,
  onVoiceConsumed,
}: {
  csrf: string;
  onPractice: () => void;
  privateLocal?: boolean;
  initialVoice?: { text: string; source: VoiceReference | null } | null;
  onVoiceConsumed?: () => void;
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
    [historyLoading, setHistoryLoading] = useState(false),
    [archived, setArchived] = useState(false),
    [nextOffset, setNextOffset] = useState<number | null>(null),
    [deleteTarget, setDeleteTarget] = useState<Conversation | null>(null),
    [voiceReset, setVoiceReset] = useState(0);
  const [voiceBusy, setVoiceBusy] = useState(false);
  const [scope, setScope] = useState<{
    scope_hash: string;
    goal_text: string;
    focus: string;
    phase: string;
    selection: ContextSelection;
    working_map: unknown;
  } | null>(null);
  const [inspect, setInspect] = useState(false);
  const [pilot, setPilot] = useState<PilotState | null>(null);
  type PrivatePreview = {
    receipt_id: string;
    context_hash: string;
    preview_hash: string;
    context: Array<{ kind: string; text: string }>;
    reflection_state: unknown;
    provider_profile: { model: string; effort: string };
    purpose: "REFLECT" | "GOAL_PROPOSAL" | "CLOSURE";
    draft: string;
  };
  const [privatePreview, setPrivatePreview] = useState<PrivatePreview | null>(
    null,
  );
  const [journalChoices, setJournalChoices] = useState<Array<{
    id: string;
    revision: number;
    raw_text: string;
    type: string;
  }> | null>(null);
  const [journalPickerOpen, setJournalPickerOpen] = useState(false);
  const [journalSelection, setJournalSelection] = useState<
    Record<string, boolean>
  >({});
  const privateAI =
    privateLocal && pilot?.state === "PRIVATE_AI_OWNER_CONSENTED";
  const [goalsOpen, setGoalsOpen] = useState(false);
  const [goalRefresh, setGoalRefresh] = useState(0);
  const [goalPreset, setGoalPreset] = useState("");
  const [journalOpen, setJournalOpen] = useState(false);
  const [contextSelection, setContextSelection] = useState<ContextSelection>({
    type: "GOAL_START",
    timezone:
      Intl.DateTimeFormat().resolvedOptions().timeZone || "Europe/Warsaw",
  });
  const [contextPreview, setContextPreview] = useState<DeepPreview | null>(
    null,
  );
  const [sessionBlocked, setSessionBlocked] = useState(false);
  const alive = useRef(true),
    working = useRef(false),
    generation = useRef(0),
    composer = useRef<HTMLTextAreaElement>(null),
    messages = useRef<HTMLDivElement>(null);
  const creating = useRef<string | null>(null),
    pending = useRef<{ signature: string; operation_id: string } | null>(null);
  const pendingAction = useRef<{ signature: string; id: string } | null>(null);
  const deepCreating = useRef<{ signature: string; id: string } | null>(null);
  useEffect(() => {
    if (initialVoice) {
      setText(initialVoice.text);
      setSource(initialVoice.source);
      voiceReviewPending.current = !!initialVoice.source;
      onVoiceConsumed?.();
    }
  }, [initialVoice]);
  const voiceReviewPending = useRef(false);
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
    if (p?.conversation.id !== page?.conversation.id) {
      setContextPreview(null);
      setSessionBlocked(false);
    }
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
    messages.current?.scrollTo({
      top: page?.messages.length ? messages.current.scrollHeight : 0,
    });
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
    setHistoryLoading(true);
    const h = await api(
      `?archived=${archived}&offset=${more ? (nextOffset ?? 0) : 0}`,
    );
    if (alive.current) {
      setHistoryLoading(false);
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
  useEffect(() => {
    if (goalsOpen)
      void api("?archived=false")
        .then((h) => setHistory(h.items))
        .catch(() => setError("Історія недоступна."));
  }, [goalsOpen]);
  async function open(id: string) {
    if (working.current || voiceBusy) return;
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
        setGoalsOpen(false);
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
    privateApproved = false,
  ) {
    const input = override ?? text;
    if (working.current || voiceBusy || sessionBlocked || !validChatText(input))
      return;
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
      let voiceSource = source;
      if (
        voiceSource &&
        (voiceReviewPending.current ||
          voiceSource.text_hash !==
            (await audioHash(new TextEncoder().encode(sent))))
      ) {
        const edited = await voiceCall(
          csrf,
          "/transcripts/" + voiceSource.transcript_id + "/edit",
          { revision: voiceSource.revision, text: sent },
        );
        voiceSource = {
          ...voiceSource,
          revision: edited.revision,
          text_hash: await audioHash(new TextEncoder().encode(sent)),
        };
        setSource(voiceSource);
        voiceReviewPending.current = false;
      }
      let binding = null;
      if (privateAI) {
        if (
          !privateApproved &&
          (inspect || Object.values(journalSelection).some(Boolean))
        ) {
          const preview = await api(
            "/" + current!.conversation.id + "/private-context/preview",
            {
              operation_id: crypto.randomUUID(),
              base_revision: current!.conversation.revision,
              text: sent,
              purpose,
              selection: contextSelection,
              journal_entries: (journalChoices ?? [])
                .filter((e) => journalSelection[e.id])
                .map((e) => ({ id: e.id, revision: e.revision })),
            },
          );
          setPrivatePreview({ ...preview, draft: sent });
          setInspect(false);
          return;
        }
        if (privateApproved) {
          if (
            !privatePreview ||
            privatePreview.draft !== sent ||
            privatePreview.purpose !== purpose
          )
            throw new Error("PRIVATE_PREVIEW_CHANGED");
          binding = {
            receipt_id: privatePreview.receipt_id,
            context_hash: privatePreview.context_hash,
            preview_hash: privatePreview.preview_hash,
          };
        }
      }
      if (
        !privateLocal &&
        status?.mode &&
        current!.conversation.mode === "DEEP"
      ) {
        const preview =
          (override ? null : contextPreview) ??
          (await deepCall(csrf, current!.conversation.id, "context-preview", {
            operation_id: crypto.randomUUID(),
            base_revision: current!.conversation.revision,
            text: sent,
            selection: contextSelection,
          }));
        binding = {
          receipt_id: preview.receipt_id,
          context_hash: preview.context_hash,
          preview_hash: preview.preview_hash,
        };
      }
      const body = {
        ...(binding ? { context_binding: binding } : {}),
        base_revision: current!.conversation.revision,
        text: sent,
        source_reference: voiceSource,
        ...(privateAI
          ? {
              purpose,
              owner_approved_external_text: true,
              ...(!binding
                ? { standard_send: true, selection: contextSelection }
                : {}),
            }
          : !privateLocal && status?.mode
            ? { purpose, synthetic_test_ack: true }
            : {}),
      };
      const signature = JSON.stringify({ id: current!.conversation.id, body });
      if (pending.current?.signature !== signature)
        pending.current = { signature, operation_id: crypto.randomUUID() };
      const result = await api(
        "/" +
          current!.conversation.id +
          (privateAI
            ? "/private-infer"
            : !privateLocal && status?.mode
              ? "/inference"
              : "/messages"),
        {
          ...body,
          operation_id: pending.current.operation_id,
        },
      );
      setPrivatePreview(null);
      const fresh =
        result.next_after !== null
          ? await load(current!.conversation.id)
          : result;
      if (alive.current && seq === generation.current) {
        selection(fresh);
        setText("");
        setSource(null);
        setVoiceReset((v) => v + 1);
        setJournalSelection({});
        setJournalChoices(null);
        setContextPreview(null);
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
        if (code === "DEEP_SCOPE_APPROVAL_REQUIRED" && page) {
          try {
            setScope(
              await api(
                "/" + page.conversation.id + "/private-scope",
                contextSelection,
              ),
            );
            setError("");
          } catch {
            setError("Сфера сесії змінилася. Відкрийте її ще раз.");
          }
        }
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
    if (working.current || voiceBusy) return;
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
  async function chooseJournals() {
    try {
      const r = await fetch("/api/v1/entries", {
        credentials: "same-origin",
        cache: "no-store",
      });
      if (!r.ok) throw new Error();
      const data = await r.json();
      const choices = data.items.filter(
        (e: { type: string }) => e.type !== "creative",
      );
      setJournalChoices(choices);
      setJournalSelection((old) =>
        Object.fromEntries(
          choices.map((e: { id: string }) => [e.id, !!old[e.id]]),
        ),
      );
      setPrivatePreview(null);
      setJournalPickerOpen(true);
      setError("");
    } catch {
      setError("Не вдалося оновити записи. Збережений текст залишається тут.");
    }
  }
  async function refreshScope() {
    if (!page) return;
    try {
      setScope(
        await api(
          "/" + page.conversation.id + "/private-scope",
          contextSelection,
        ),
      );
      setError("");
    } catch (e) {
      setError(chatError((e as Error).message));
    }
  }
  async function chooseDeep(profile: string) {
    setBusy(true);
    try {
      setPilot(await pilotCall(csrf, "deep-profile", { profile }));
      setPrivatePreview(null);
    } catch {
      setError("Профіль недоступний; заміни немає.");
    } finally {
      setBusy(false);
    }
  }
  async function startDeep(g: ReflectionGoal) {
    if (working.current || voiceBusy) return;
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
        if (privateAI)
          setScope(
            await api(
              "/" + p.conversation.id + "/private-scope",
              contextSelection,
            ),
          );
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
    if (working.current || voiceBusy) return;
    generation.current++;
    selection(null);
    setText("");
    setSource(null);
    setPrivatePreview(null);
    setJournalSelection({});
    setJournalChoices(null);
    setScope(null);
    pending.current = null;
    creating.current = null;
    setHistoryOpen(false);
    setError("");
    setNotice("");
    composer.current?.focus();
  }
  useEffect(() => {
    if (inspect && validChatText(text)) void send();
  }, [inspect]);
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
            <div
              className="mode-switch"
              role="group"
              aria-label="Режим розмови"
            >
              <button
                aria-pressed={page?.conversation.mode !== "DEEP"}
                disabled={busy || voiceBusy}
                onClick={() => {
                  if (page?.conversation.mode === "DEEP") reset();
                }}
              >
                Звичайна
              </button>
              <button
                aria-pressed={page?.conversation.mode === "DEEP"}
                disabled={busy || voiceBusy}
                onClick={() => setGoalsOpen(true)}
              >
                Глибока
              </button>
            </div>
            {privateAI && page?.conversation.mode === "DEEP" && (
              <select
                disabled={busy || voiceBusy || inferenceActive}
                aria-label="Модель глибокої розмови"
                value={pilot?.deep_profile}
                onChange={(e) => void chooseDeep(e.target.value)}
              >
                <option value="DEEP_ECONOMICAL">Економний · Luna Max</option>
                <option value="DEEP_QUALITY">Якісний · Sol 6.1 High</option>
              </select>
            )}
            {status?.mode &&
              page?.conversation.mode === "DEEP" &&
              hasMessages && (
                <button
                  disabled={busy || inferenceActive || sessionBlocked}
                  onClick={() =>
                    void send(
                      "CLOSURE",
                      privateLocal
                        ? "Явно прошу підсумувати цю сесію."
                        : "ORIGINAL SYNTHETIC · Явно прошу підсумувати цю сесію.",
                    )
                  }
                >
                  Підсумувати
                </button>
              )}
            <button disabled={voiceBusy} onClick={() => setHistoryOpen(true)}>
              Розмови
            </button>
            <button
              disabled={busy || voiceBusy}
              onClick={() =>
                page?.conversation.mode === "DEEP"
                  ? setGoalsOpen(true)
                  : reset()
              }
            >
              Нова розмова
            </button>
          </div>
        </header>
        {page?.conversation.mode === "DEEP" &&
          page.conversation.goal_binding &&
          !status?.mode &&
          !privateLocal && (
            <DeepContext
              key={page.conversation.id}
              csrf={csrf}
              conversationId={page.conversation.id}
              binding={page.conversation.goal_binding}
              syntheticDemo={status?.synthetic_demo ?? false}
              refreshVersion={goalRefresh}
            />
          )}
        {(status?.mode || privateLocal) &&
          page?.conversation.mode === "DEEP" && (
            <DeepSessionPanel
              key={page.conversation.id}
              csrf={csrf}
              id={page.conversation.id}
              revision={page.conversation.revision}
              draft={text}
              selection={contextSelection}
              onSelection={setContextSelection}
              preview={contextPreview}
              onPreview={setContextPreview}
              onSession={(s) =>
                setSessionBlocked(["CLOSED", "PAUSED"].includes(s.phase))
              }
              onNext={() => setGoalsOpen(true)}
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
          {!hasMessages && page?.conversation.mode === "DEEP" ? (
            <p className="deep-empty">З чого хочеться почати цю тему?</p>
          ) : !hasMessages ? (
            <div className="conversation-empty">
              <h2>Що у вас сьогодні на думці?</h2>
              <p>
                Можна просто записати те, що на думці. Ви вирішуєте, що
                зберігати й коли повертатися.
              </p>
              <div className="conversation-intents">
                {[
                  "Просто поговорити",
                  "Розібрати думку",
                  "Подумати над рішенням",
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
            onClose={() => {
              if (page.conversation.mode === "DEEP")
                void deepCall(csrf, page.conversation.id, "deep-session")
                  .then((d) =>
                    deepCall(
                      csrf,
                      page.conversation.id,
                      "deep-session/actions",
                      {
                        operation_id: crypto.randomUUID(),
                        base_revision: d.session.revision,
                        action: "close",
                      },
                    ),
                  )
                  .then(() => {
                    setSessionBlocked(true);
                    setGoalRefresh((v) => v + 1);
                    return action(page.conversation, "archive");
                  })
                  .catch(() =>
                    setError("Сесію не закрито. Перевірте карту й повторіть."),
                  );
              else void action(page.conversation, "archive");
            }}
            onJournal={() => setJournalOpen(true)}
          />
        )}
      </div>
      {journalPickerOpen && journalChoices && (
        <Sheet
          title="Додати записи до розмови"
          onClose={() => setJournalPickerOpen(false)}
        >
          <p>
            Щоденник вимкнений за замовчуванням. Виберіть до 10 записів. Перед
            надсиланням ви підтвердите їх окремо.
          </p>
          {journalChoices.map((e) => (
            <label className="journal-choice" key={e.id}>
              <input
                type="checkbox"
                checked={!!journalSelection[e.id]}
                disabled={
                  !journalSelection[e.id] &&
                  Object.values(journalSelection).filter(Boolean).length >= 10
                }
                onChange={(event) => {
                  setJournalSelection((old) => ({
                    ...old,
                    [e.id]: event.target.checked,
                  }));
                  setPrivatePreview(null);
                }}
              />
              {e.raw_text}
            </label>
          ))}
          <button onClick={() => setJournalPickerOpen(false)}>Готово</button>
        </Sheet>
      )}
      {privatePreview && (
        <Sheet
          title={
            Object.values(journalSelection).some(Boolean)
              ? `Додати ${Object.values(journalSelection).filter(Boolean).length} записів щоденника?`
              : "Що буде надіслано"
          }
          onClose={() => setPrivatePreview(null)}
          wide
        >
          <p>
            {privatePreview.provider_profile.model} /{" "}
            {privatePreview.provider_profile.effort}. Через наявну підписку
            ChatGPT. Нульове зберігання не гарантоване. Аудіо не надсилається.
          </p>
          {privatePreview.context.map((part, index) => (
            <section key={index}>
              <h3>
                {part.kind === "CURRENT_TURN"
                  ? "Ваше повідомлення"
                  : part.kind === "JOURNAL_SELECTED"
                    ? "Вибраний запис щоденника"
                    : "Погоджений контекст"}
              </h3>
              <p className="preserve-text">{part.text}</p>
            </section>
          ))}
          {privatePreview.reflection_state !== null && (
            <details>
              <summary>Мета, фокус і карта глибокої розмови</summary>
              <pre>
                {JSON.stringify(privatePreview.reflection_state, null, 2)}
              </pre>
            </details>
          )}
          {error && (
            <>
              <p role="alert">{error}</p>
              <button disabled={busy} onClick={() => void chooseJournals()}>
                Оновити вибрані записи
              </button>
            </>
          )}
          <button
            className="primary"
            disabled={busy}
            onClick={() =>
              void send(privatePreview.purpose, privatePreview.draft, true)
            }
          >
            Підтвердити й надіслати
          </button>
        </Sheet>
      )}
      <form
        className="conversation-composer"
        aria-label="Нове повідомлення"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        {privateLocal && (
          <PrivatePilotControls
            mode={page?.conversation.mode ?? "FREE"}
            deepProfile={pilot?.deep_profile}
            compact
            csrf={csrf}
            onChanged={(s) => {
              setPilot(s);
              setPrivatePreview(null);
              void api("/status")
                .then(setStatus)
                .catch(() => setError("Не вдалося оновити статус."));
            }}
          />
        )}
        {!status?.synthetic_demo && status && !privateAI && (
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
          onChange={(e) => {
            setText(e.target.value);
            setContextPreview(null);
            setPrivatePreview(null);
          }}
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
          {privateAI && (
            <button
              type="button"
              aria-label="Додати контекст щоденника"
              onClick={() => void chooseJournals()}
            >
              <svg
                viewBox="0 0 24 24"
                width="22"
                height="22"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
                aria-hidden="true"
              >
                <path d="M12 4v16M4 12h16" />
              </svg>
            </button>
          )}
          <ComposerVoice
            resetVersion={voiceReset}
            available={
              !privateLocal || !!pilot?.consent || pilot?.local_voice === "ON"
            }
            csrf={csrf}
            onBusy={(value) => {
              setVoiceBusy(value);
              window.dispatchEvent(
                new CustomEvent("pc-voice-busy", { detail: value }),
              );
            }}
            onDraft={(value, ref) => {
              setText((old) => (old.trim() ? old + "\n" + value : value));
              setSource(ref);
              voiceReviewPending.current = !!ref;
              setPrivatePreview(null);
              composer.current?.focus();
            }}
          />
          {privateAI && (
            <button
              type="button"
              className="context-inspect"
              disabled={!validChatText(text) || busy || voiceBusy}
              onClick={() => {
                setInspect(true);
              }}
            >
              Що буде надіслано
            </button>
          )}
          {!privateLocal && (
            <button type="button" onClick={onPractice}>
              Практики
            </button>
          )}
          <span className="hint">Ctrl / ⌘ + Enter</span>
          <button
            className="primary"
            disabled={
              busy ||
              voiceBusy ||
              sessionBlocked ||
              inferenceActive ||
              !validChatText(text) ||
              page?.conversation.state === "ARCHIVED"
            }
          >
            {busy
              ? "Зберігаємо…"
              : privateAI
                ? "Надіслати"
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
        <Sheet
          title="Глибока розмова · оберіть мету"
          onClose={() => setGoalsOpen(false)}
          wide
        >
          {history
            .filter((c) => c.mode === "DEEP" && c.state === "ACTIVE")
            .map((c) => (
              <button key={c.id} onClick={() => void open(c.id)}>
                Продовжити · {c.title}
              </button>
            ))}
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
                  <small>{c.mode === "DEEP" ? "Глибока" : "Звичайна"}</small>
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
          {historyLoading ? (
            <p role="status">Відкриваю розмови…</p>
          ) : (
            history.length === 0 && <p>Розмов ще немає.</p>
          )}
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
        <JournalPoint
          csrf={csrf}
          conversationId={page.conversation.id}
          messages={page.messages}
          onClose={() => setJournalOpen(false)}
        />
      )}
      {scope && page && (
        <Sheet title="Сфера глибокої розмови" onClose={() => setScope(null)}>
          <p>
            <strong>Мета:</strong> {scope.goal_text}
          </p>
          <p>
            <strong>Фокус:</strong>{" "}
            {scope.focus || "Можна уточнити під час розмови"}
          </p>
          <p>
            Ця розмова, погоджена редакція мети, її робоча карта та попередні
            завершення. Щоденник і сторонні розмови не додаються. Діапазон:{" "}
            {scope.selection.type === "GOAL_START"
              ? "від початку мети"
              : scope.selection.type}
            .
          </p>
          {error && (
            <>
              <p role="alert">{error}</p>
              <button disabled={busy} onClick={() => void refreshScope()}>
                Оновити сферу сесії
              </button>
            </>
          )}
          <button
            className="primary"
            onClick={() =>
              void api("/" + page.conversation.id + "/private-scope/approve", {
                selection: contextSelection,
                scope_hash: scope.scope_hash,
                accepted: true,
              })
                .then(() => setScope(null))
                .catch(() => setError("Сфера змінилася. Перевірте її знову."))
            }
          >
            Погоджую сферу сесії
          </button>
        </Sheet>
      )}
    </section>
  );
}
