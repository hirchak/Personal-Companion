import { useEffect, useRef, useState } from "react";
import type { InferenceJob } from "./conversation-model";
export function InferencePanel({
  csrf,
  conversationId,
  job,
  onChanged,
  onGoal,
  onClose,
  onJournal,
}: {
  csrf: string;
  conversationId: string;
  job: InferenceJob;
  onChanged: (job: InferenceJob, final: boolean) => void;
  onGoal: (text: string) => void;
  onClose: () => void;
  onJournal: () => void;
}) {
  const [current, setCurrent] = useState(job),
    [error, setError] = useState("");
  const alive = useRef(true),
    key = useRef<{ signature: string; id: string } | null>(null),
    delivered = useRef("");
  async function call(action?: "cancel" | "retry") {
    const body = action
      ? {
          operation_id: key.current!.id,
          base_revision: current.revision,
          action,
        }
      : undefined;
    const r = await fetch(
      `/api/v1/conversations/${conversationId}/inference/${job.id}${action ? "/actions" : ""}`,
      {
        method: action ? "POST" : "GET",
        credentials: "same-origin",
        cache: "no-store",
        headers: action
          ? { "Content-Type": "application/json", "X-CSRF-Token": csrf }
          : {},
        body: body ? JSON.stringify(body) : undefined,
      },
    );
    if (!r.ok) {
      const d = await r.json();
      throw new Error(d.code);
    }
    return r.json() as Promise<InferenceJob>;
  }
  useEffect(() => {
    setCurrent(job);
  }, [job.id, job.revision]);
  useEffect(() => {
    alive.current = true;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const d = await call();
        if (!alive.current) return;
        setCurrent(d);
        const final = !["QUEUED", "RUNNING"].includes(d.state);
        const signature = d.id + ":" + d.revision;
        if (signature !== delivered.current) {
          delivered.current = signature;
          onChanged(d, final);
        }
        if (!final) timer = setTimeout(() => void poll(), 350);
      } catch {
        if (alive.current) {
          setError(
            "Не вдалося перевірити відповідь. Повідомлення збережене; спробуйте відкрити розмову ще раз.",
          );
          timer = setTimeout(() => void poll(), 1500);
        }
      }
    }
    if (["QUEUED", "RUNNING"].includes(job.state)) void poll();
    else if(delivered.current!==job.id+":"+job.revision){delivered.current=job.id+":"+job.revision;onChanged(job,true)}
    return () => {
      alive.current = false;
      clearTimeout(timer);
    };
  }, [job.id, job.state]);
  async function action(name: "cancel" | "retry") {
    setError("");
    const signature = current.id + ":" + current.revision + ":" + name;
    if (key.current?.signature !== signature)
      key.current = { signature, id: crypto.randomUUID() };
    try {
      const d = await call(name);
      if (alive.current) {
        key.current = null;
        setCurrent(d);
        onChanged(d, !["QUEUED", "RUNNING"].includes(d.state));
      }
    } catch (e) {
      if (alive.current)
        setError(
          (e as Error).message === "INFERENCE_STOPPING"
            ? "Попередній запит ще зупиняється. Повторіть за мить."
            : "Дію не завершено. Інший помічник автоматично не підключається.",
        );
    }
  }
  const active = ["QUEUED", "RUNNING"].includes(current.state);
  if (
    current.state === "COMPLETED" &&
    !current.candidate?.goal_suggestion &&
    !current.candidate?.closure
  )
    return null;
  return (
    <section className="inference-panel" aria-label="Стан відповіді">
      {active && (
        <>
          <p role="status">
            {current.state === "QUEUED"
              ? "Готуємо відповідь…"
              : "Помічник відповідає…"}
          </p>
          {current.partial_candidate && (
            <article aria-label="Чернетка відповіді">
              <p className="hint">Чернетка · ще не збережена відповідь</p>
              <p className="entry-text">{current.partial_candidate}</p>
            </article>
          )}
          <button onClick={() => void action("cancel")}>
            Скасувати відповідь
          </button>
        </>
      )}
      {current.state === "FAILED" && (
        <p role="alert">
          Відповідь недоступна. Ваше повідомлення збережено.
          {current.error === "CONVERSATION_CHANGED" ||
          current.error === "SOURCE_CHANGED"
            ? " Контекст змінився; надішліть новий запит."
            : ""}
        </p>
      )}
      {current.state === "CANCELLED" && (
        <p role="status">
          Запит скасовано. Незавершена відповідь не збережена.
        </p>
      )}
      {["FAILED", "CANCELLED"].includes(current.state) && (
        <button onClick={() => void action("retry")}>
          Повторити цей запит
        </button>
      )}
      {error && <p role="alert">{error}</p>}
      {current.candidate?.goal_suggestion && (
        <div>
          <h3>Можливе формулювання цілі</h3>
          <p>{current.candidate.goal_suggestion}</p>
          <p className="hint">
            Це пропозиція. Ви можете змінити її та окремо погодити.
          </p>
          <button onClick={() => onGoal(current.candidate!.goal_suggestion!)}>
            Переглянути формулювання
          </button>
        </div>
      )}
      {current.candidate?.closure && (
        <div aria-label="Кандидат підсумку">
          <h3>Підсумок для перегляду</h3>
          <ul>
            {current.candidate.closure.discussed.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
          <p>{current.candidate.closure.clearer}</p>
          <p>{current.candidate.closure.unresolved}</p>
          <ul>
            {current.candidate.closure.possible_steps.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
          <p className="hint">
            Нічого не додано в щоденник чи пам’ять. Можна продовжити розмову або
            завершити на сьогодні.
          </p>
          <button onClick={onClose}>Завершити на сьогодні</button>
          <button onClick={onJournal}>Зберегти свою думку</button>
        </div>
      )}
      <details>
        <summary>Діагностика запиту</summary>
        <p className="metadata">
          {current.request_metadata.provider_route} ·{" "}
          {current.request_metadata.provider_model} · {current.state}
        </p>
        <p className="metadata">
          Прив’язки контексту й редакції збережені локально.
        </p>
      </details>
    </section>
  );
}
