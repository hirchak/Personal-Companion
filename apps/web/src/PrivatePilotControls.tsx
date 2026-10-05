import { useEffect, useState } from "react";
import { Sheet } from "./Sheet";
export type PilotState = {
  state: "PRIVATE_AI_OFF" | "PRIVATE_AI_OWNER_CONSENTED";
  local_voice: "OFF" | "ON";
  deep_profile: "DEEP_ECONOMICAL" | "DEEP_QUALITY";
  consent: {
    accepted_at: string;
    ai_enabled: boolean;
    voice_enabled: boolean;
  } | null;
  consent_version: number;
  privacy_version: string;
};
export async function pilotCall(
  csrf: string,
  path: string,
  body?: unknown,
): Promise<PilotState> {
  const r = await fetch("/api/v1/private-pilot/" + path, {
    method: body !== undefined ? "POST" : "GET",
    credentials: "same-origin",
    cache: "no-store",
    headers:
      body !== undefined
        ? { "Content-Type": "application/json", "X-CSRF-Token": csrf }
        : {},
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) throw new Error((await r.json()).code);
  return r.json();
}
export function PrivatePilotControls({
  csrf,
  onChanged,
  compact = false,
  mode = "FREE",
  deepProfile,
}: {
  csrf: string;
  onChanged?: (state: PilotState) => void;
  compact?: boolean;
  mode?: "FREE" | "DEEP";
  deepProfile?: PilotState["deep_profile"];
}) {
  const [state, setState] = useState<PilotState | null>(null),
    [open, setOpen] = useState(false),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  function changed(s: PilotState) {
    setState(s);
    onChanged?.(s);
  }
  useEffect(() => {
    let alive = true;
    void pilotCall(csrf, "status")
      .then(async (s) => {
        if (s.consent?.ai_enabled && s.state === "PRIVATE_AI_OFF")
          s = await pilotCall(csrf, "resume", {});
        if (alive) changed(s);
      })
      .catch(() => {
        if (alive)
          setError(
            "AI недоступний. Перевірте локальний сервіс і повторіть увімкнення.",
          );
      });
    return () => {
      alive = false;
    };
  }, []);
  async function action(path: string, body: unknown) {
    setBusy(true);
    setError("");
    try {
      changed(await pilotCall(csrf, path, body));
      setOpen(false);
    } catch {
      setError(
        "Дію не виконано. Перевірте локальний сервіс. Автоматичної заміни провайдера немає.",
      );
    } finally {
      setBusy(false);
    }
  }
  const active = state?.state === "PRIVATE_AI_OWNER_CONSENTED";
  const privacy = (
    <>
      <p>
        Підтверджений текст і обмежений контекст цієї розмови обробляє OpenAI
        через наявну підписку ChatGPT.
      </p>
      <p>
        Мікрофонне аудіо залишається локально. Щоденник не додається
        автоматично. Нульове зберігання провайдером не гарантоване.
        Автоматичного переходу до іншої моделі чи провайдера немає.
      </p>
      <p>
        Перед наступним приватним AI використанням перевірте зовнішні
        налаштування:
      </p>
      <ul>
        <li>ChatGPT: Improve the model for everyone = OFF</li>
        <li>Codex: Include environments = OFF</li>
      </ul>
      <p>
        Цими Data Controls керуєте ви. Застосунок їх не перевіряв і не
        підтверджує їхній стан.
      </p>
      <p>
        Згода зберігається лише на цьому пристрої. Зміна приватності або
        адресата потребуватиме нової згоди. Аудіо зберігається до вашого
        видалення; повне стирання резервних копій не гарантоване.
      </p>
    </>
  );
  return (
    <div className={compact ? "ai-compact" : "privacy-settings"}>
      {compact ? (
        <button
          type="button"
          className="quiet"
          disabled={busy}
          onClick={() =>
            state?.consent ? void action("resume", {}) : setOpen(true)
          }
        >
          {active
            ? mode === "DEEP"
              ? (deepProfile ?? state?.deep_profile) === "DEEP_ECONOMICAL"
                ? "Deep · Luna Max"
                : "Deep · Sol 6.1 High"
              : "Luna · High"
            : "AI вимкнено · увімкнути"}
        </button>
      ) : (
        <>
          <h2>AI & Privacy</h2>
          {privacy}
          <p>
            {state?.consent
              ? `Локальну згоду прийнято ${new Date(state.consent.accepted_at).toLocaleDateString("uk-UA")}. Версія ${state.consent_version}.`
              : "Локальної згоди ще немає для поточної версії."}
          </p>
          <div className="actions">
            <button
              disabled={busy}
              onClick={() =>
                state?.consent ? void action("resume", {}) : setOpen(true)
              }
            >
              Увімкнути AI
            </button>
            <button
              disabled={busy || !active}
              onClick={() => void action("disable", {})}
            >
              Вимкнути AI
            </button>
            <button
              disabled={busy || !state?.consent}
              onClick={() => void action("revoke", {})}
            >
              Відкликати згоду
            </button>
          </div>
          <h2>Моделі</h2>
          <p>
            Звичайна: Luna / High. Глибока: Економний — Luna / Max; Якісний —
            Sol 6.1 / High. Стелі: Luna ≤ Max; Sol 6.1 ≤ High. PAYG і fallback
            вимкнені.
          </p>
          <h2>Локальний голос</h2>
          <p>
            Лише whisper.cpp.{" "}
            {state?.local_voice === "ON"
              ? "Локальне розпізнавання доступне."
              : "Розпізнавання наразі недоступне; збережені записи можна повторити пізніше."}{" "}
            Хмарного ASR немає. Перевірте й відредагуйте текст перед
            надсиланням. Аудіо зберігається локально до вашого видалення.
          </p>
          <button
            disabled={busy || state?.local_voice === "ON"}
            onClick={() =>
              void action("local-voice", {
                local_audio_only: true,
                review_before_send: true,
                manual_audio_deletion_understood: true,
              })
            }
          >
            Увімкнути локальне розпізнавання
          </button>
        </>
      )}
      {error && <p role="alert">{error}</p>}
      {open && state && (
        <Sheet title="Приватність розмови" onClose={() => setOpen(false)}>
          {privacy}
          <button
            className="primary"
            disabled={busy}
            onClick={() =>
              void action("consent", {
                version: state.consent_version,
                privacy_version: state.privacy_version,
                accepted: true,
              })
            }
          >
            Приймаю · увімкнути AI та локальний голос
          </button>
        </Sheet>
      )}
    </div>
  );
}
