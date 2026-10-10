import { useEffect, useRef, useState } from "react";
import { Sheet } from "./Sheet";
import { nativeShell } from "./native-macos";
import {
  PilotCallError,
  pilotErrorMessage,
  safePilotErrorCode,
} from "./private-pilot-errors";

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
  let response: Response;
  try {
    response = await fetch("/api/v1/private-pilot/" + path, {
      method: body !== undefined ? "POST" : "GET",
      credentials: "same-origin",
      cache: "no-store",
      headers:
        body !== undefined
          ? { "Content-Type": "application/json", "X-CSRF-Token": csrf }
          : {},
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new PilotCallError("LOCAL_SERVICE_UNAVAILABLE");
  }
  let result: unknown;
  try {
    result = await response.json();
  } catch {
    throw new PilotCallError("LOCAL_SERVICE_UNAVAILABLE");
  }
  if (!response.ok) {
    throw new PilotCallError(
      safePilotErrorCode(
        typeof result === "object" && result !== null && "code" in result
          ? (result as { code?: unknown }).code
          : undefined,
      ),
    );
  }
  return result as PilotState;
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
    [failure, setFailure] = useState<{ code: string; message: string } | null>(
      null,
    );
  const onChangedRef = useRef(onChanged);
  onChangedRef.current = onChanged;

  function changed(next: PilotState) {
    setState(next);
    onChanged?.(next);
  }

  function reportFailure(error: unknown) {
    const code = safePilotErrorCode(error);
    setFailure({ code, message: pilotErrorMessage(code) });
  }

  useEffect(() => {
    let alive = true;
    void pilotCall(csrf, "status")
      .then((next) => {
        if (alive) {
          setState(next);
          onChangedRef.current?.(next);
        }
      })
      .catch((error: unknown) => {
        if (alive) {
          const code = safePilotErrorCode(error);
          setFailure({ code, message: pilotErrorMessage(code) });
        }
      });
    return () => {
      alive = false;
    };
  }, [csrf]);

  async function action(path: string, body: unknown) {
    setBusy(true);
    setFailure(null);
    try {
      changed(await pilotCall(csrf, path, body));
      setOpen(false);
    } catch (error) {
      reportFailure(error);
      if (path === "consent") {
        // Consent is durable even when the bounded provider readiness check fails.
        setOpen(false);
        try {
          changed(await pilotCall(csrf, "status"));
        } catch {
          // Keep the original sanitized activation reason visible.
        }
      }
    } finally {
      setBusy(false);
    }
  }

  const active = state?.state === "PRIVATE_AI_OWNER_CONSENTED";
  const profileLabel =
    mode === "DEEP"
      ? (deepProfile ?? state?.deep_profile) === "DEEP_ECONOMICAL"
        ? "Deep · Luna Max"
        : "Deep · Sol 6.1 High"
      : "Luna · High";
  const disclosure = (
    <>
      <p>
        AI може надсилати підтверджений текст і вибраний контекст до OpenAI.
        Аудіо з мікрофона залишається локально. Щоденник не додається
        автоматично.
      </p>
      <p>
        Згода зберігається на цьому пристрої. Нульове зберігання провайдером не
        гарантоване; автоматичної заміни провайдера немає.
      </p>
    </>
  );

  return (
    <div className={compact ? "ai-compact" : "privacy-settings"}>
      {compact ? (
        <button
          type="button"
          className="quiet"
          disabled={busy || !state}
          aria-pressed={!!active}
          aria-label={active ? "Вимкнути AI" : "Увімкнути AI"}
          onClick={() => {
            if (active) void action("disable", {});
            else if (state?.consent) void action("resume", {});
            else if (state) setOpen(true);
          }}
        >
          {active ? profileLabel : "AI вимкнено"}
        </button>
      ) : (
        <>
          <h2>AI & Privacy</h2>
          {disclosure}
          <p>
            Зовнішні налаштування OpenAI/Codex застосунок не перевіряє. Перед
            використанням перегляньте їх у ChatGPT та Codex; їхній стан
            залишається непідтвердженим.
          </p>
          <p>
            {state?.consent
              ? `Локальну згоду прийнято ${new Date(state.consent.accepted_at).toLocaleDateString("uk-UA")}. Версія ${state.consent_version}.`
              : "Локальної згоди ще немає для поточної версії."}
          </p>
          <div className="actions">
            <button
              disabled={busy || !state || !!active}
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
            Sol 6.1 / High. Стелі: Luna ≤ Max/Sol ≤ High. PAYG і fallback
            вимкнені.
          </p>
          <h2>Локальний голос</h2>
          <p>
            Мікрофон працює незалежно від AI. Аудіо залишається на цьому
            пристрої; локальне whisper.cpp запускається з мікрофона. {state?.local_voice === "ON"
              ? "Розпізнавання підготовлено."
              : "Якщо локальні моделі недоступні, запис усе одно збережеться для повторної спроби."}{" "}
            Перед надсиланням текст можна перевірити й відредагувати.
          </p>
        </>
      )}
      {failure && (
        <p role="alert">
          {failure.message} {!nativeShell() && <small>Код: {failure.code}</small>}
        </p>
      )}
      {open && state && (
        <Sheet title="Приватність розмови" onClose={() => setOpen(false)}>
          {disclosure}
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
            Увімкнути AI
          </button>
        </Sheet>
      )}
    </div>
  );
}
