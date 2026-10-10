import { useEffect, useRef, useState } from "react";
import { PCMRecorder } from "./pcm-recorder";
import {
  AUDIO_CHUNK,
  audioBase64,
  audioBegin,
  audioHash,
  type AudioBegin,
  type Transcript,
} from "./audio-types";
import type { PhoneStore } from "./phone-store";
import type { VoiceReference } from "./conversation-model";
import { PilotCallError, pilotErrorMessage, safePilotErrorCode } from "./private-pilot-errors";
export type VoiceItem = {
  id: string;
  state: string;
  ux_state?: string;
  content_hash: string;
  byte_size: number;
  duration?: number;
  created?: string;
  transcript: Transcript | null;
};
export async function voiceCall(csrf: string, path: string, body?: unknown) {
  const r = await fetch("/api/v1/voice" + path, {
    method: body === undefined ? "GET" : "POST",
    credentials: "same-origin",
    cache: "no-store",
    headers: {
      "X-CSRF-Token": csrf,
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!r.ok) {
    let code: unknown;
    try {
      code = (await r.json()).code;
    } catch {
      code = undefined;
    }
    throw new PilotCallError(safePilotErrorCode(code));
  }
  return r.json();
}
async function list(csrf: string, phone?: PhoneStore): Promise<VoiceItem[]> {
  if (phone)
    return (await phone.audios()).map((x) => ({
      id: x.begin.audio_id,
      state: x.state,
      ux_state: "WAITING_FOR_LOCAL_ASR",
      content_hash: x.begin.content_hash,
      byte_size: x.begin.byte_size,
      created: x.begin.created_at_utc,
      transcript: x.transcript,
    }));
  return (await voiceCall(csrf, "/audio")).items;
}
export async function voiceReference(item: VoiceItem): Promise<VoiceReference> {
  const t = item.transcript!;
  return {
    kind: "VOICE_TRANSCRIPT",
    transcript_id: t.id,
    revision: t.revision,
    audio_hash: item.content_hash,
    text_hash: await audioHash(
      new TextEncoder().encode(t.edited ?? t.candidate ?? ""),
    ),
  };
}
export function ComposerVoice({
  csrf = "",
  phone,
  onDraft,
  onBusy,
  onStart,
  available = true,
  resetVersion = 0,
}: {
  csrf?: string;
  phone?: PhoneStore;
  available?: boolean;
  resetVersion?: number;
  onDraft: (text: string, source: VoiceReference | null) => void;
  onBusy?: (value: boolean) => void;
  onStart?: () => void;
}) {
  const [state, setState] = useState("IDLE"),
    [seconds, setSeconds] = useState(0),
    [message, setMessage] = useState(""),
    [draft, setDraft] = useState<Uint8Array | null>(null);
  const rec = useRef<PCMRecorder | null>(null),
    alive = useRef(true),
    begin = useRef<AudioBegin | null>(null),
    working = useRef(false);
  const callback = useRef(onDraft);
  callback.current = onDraft;
  const busyCallback = useRef(onBusy);
  busyCallback.current = onBusy;
  useEffect(() => {
    if (
      resetVersion > 0 &&
      ["DRAFT_READY", "REVIEW_REQUIRED"].includes(state)
    ) {
      setState("IDLE");
      setMessage("");
    }
  }, [resetVersion]);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      rec.current?.cancel();
    };
  }, []);
  useEffect(() => {
    busyCallback.current?.(
      ["RECORDING", "STARTING", "TRANSCRIBING", "SAVING"].includes(state) ||
        !!draft,
    );
  }, [state, draft]);
  useEffect(() => {
    if (state !== "RECORDING") return;
    const timer = setInterval(
      () => setSeconds(rec.current?.elapsed() ?? 0),
      150,
    );
    const hidden = () => {
      if (document.hidden) rec.current?.stop("BACKGROUND_INTERRUPTION");
    };
    document.addEventListener("visibilitychange", hidden);
    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", hidden);
    };
  }, [state]);
  useEffect(() => {
    const warn = (e: BeforeUnloadEvent) => {
      if (draft || ["RECORDING", "STARTING", "SAVING"].includes(state)) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [draft, state]);
  async function transcribe(id: string) {
    if (phone) {
      setState("WAITING_FOR_LOCAL_ASR");
      setMessage(
        "Запис збережено зашифровано. Очікує схваленого приватного зв’язку з Mac.",
      );
      return;
    }
    setState("TRANSCRIBING");
    setMessage("Розпізнаю…");
    try {
      await voiceCall(csrf, `/audio/${id}/transcribe`, {
        mode: "LOCAL",
        language: "uk",
      });
      for (let i = 0; i < 180 && alive.current; i++) {
        await new Promise((r) => setTimeout(r, 600));
        const item: VoiceItem = await voiceCall(csrf, `/audio/${id}`),
          t = item.transcript;
        if (t && ["TRANSCRIPT_READY", "REVIEW_REQUIRED"].includes(t.state)) {
          const value = t.edited ?? t.candidate ?? "";
          callback.current(value, await voiceReference(item));
          setState(
            t.state === "REVIEW_REQUIRED" ? "REVIEW_REQUIRED" : "DRAFT_READY",
          );
          setMessage(
            t.state === "REVIEW_REQUIRED"
              ? "Мовлення непевне. Перевірте текст перед надсиланням."
              : "Перевірте текст. Надсилання — лише за вашим рішенням.",
          );
          return;
        }
        if (t && ["FAILED", "CANCELLED"].includes(t.state))
          throw new Error(t.error ?? t.state);
      }
      if (alive.current) throw new Error("ASR_TIMEOUT");
    } catch (error) {
      if (alive.current) {
        setState("WAITING_FOR_LOCAL_ASR");
        const code = safePilotErrorCode(error);
        setMessage(
          code === "LOCAL_SERVICE_UNAVAILABLE"
            ? "Запис збережено. Перевірте локальний сервіс і повторіть у «Голосові записи»."
            : pilotErrorMessage(code),
        );
      }
    }
  }
  async function save(bytes: Uint8Array) {
    if (working.current) return;
    working.current = true;
    setState("SAVING");
    setMessage("Зберігаю запис…");
    try {
      let id: string;
      if (phone) {
        id = (await phone.saveAudio(bytes)).begin.audio_id;
      } else {
        const b = begin.current ?? {
          ...audioBegin(bytes),
          content_hash: await audioHash(bytes),
        };
        begin.current = b;
        id = b.audio_id;
        const old = await voiceCall(csrf, "/audio", b);
        if (old.state !== "MAC_AUDIO_CONFIRMED") {
          for (let index = 0; index * AUDIO_CHUNK < bytes.length; index++)
            if (!old.received_chunks.includes(index)) {
              const part = bytes.slice(
                index * AUDIO_CHUNK,
                (index + 1) * AUDIO_CHUNK,
              );
              await voiceCall(csrf, `/audio/${id}/chunks`, {
                index,
                content_hash: await audioHash(part),
                data: audioBase64(part),
              });
            }
          const receipt = await voiceCall(csrf, `/audio/${id}/finalize`, {});
          if (
            receipt.state !== "MAC_AUDIO_CONFIRMED" ||
            receipt.content_hash !== b.content_hash
          )
            throw new Error("INVALID_RECEIPT");
        }
      }
      if (alive.current) {
        setDraft(null);
        begin.current = null;
        setState("LOCAL_AUDIO_SAVED");
        await transcribe(id);
      }
    } catch {
      if (alive.current) {
        setState("FAILED");
        setMessage(
          "Сервіс недоступний. Аудіо ще у цій вкладці — повторіть збереження перед закриттям.",
        );
      }
    } finally {
      working.current = false;
    }
  }
  async function start() {
    if (working.current || ["STARTING", "RECORDING"].includes(state)) return;
    setMessage("");
    setSeconds(0);
    setState("STARTING");
    begin.current = null;
    const recorder = new PCMRecorder(
      (bytes) => {
        if (alive.current) {
          setDraft(bytes);
          void save(bytes);
        }
      },
      () => setMessage("Запис перервано; зберігаю доступну частину."),
    );
    rec.current = recorder;
    onStart?.();
    try {
      if ((await recorder.start()) && alive.current) setState("RECORDING");
    } catch {
      if (alive.current) {
        setState("IDLE");
        setMessage("Дозвольте доступ до мікрофона й повторіть запис.");
      }
    }
  }
  const recording = state === "RECORDING",
    pending = state === "STARTING";
  return (
    <div
      className={"composer-voice voice-" + state.toLowerCase()}
      data-voice-state={state}
      data-native-unsaved={
        state === "STARTING" || state === "RECORDING" || state === "SAVING" || Boolean(draft)
      }
    >
      {recording || pending ? (
        <div className="recording-strip">
          <div className="voice-wave" aria-hidden="true">
            {Array.from({ length: 15 }, (_, i) => (
              <i
                key={i}
                style={{
                  animationDelay: `${i * 61}ms`,
                  height: `${12 + ((i * 13) % 25)}px`,
                }}
              />
            ))}
          </div>
          <span role="status">
            {pending
              ? "Мікрофон…"
              : `Запис · ${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`}
          </span>
          <button
            type="button"
            onClick={() => {
              rec.current?.cancel();
              setState("CANCELLED");
              setMessage("Запис скасовано.");
            }}
          >
            Скасувати
          </button>
          {recording && (
            <button
              className="primary"
              type="button"
              onClick={() => rec.current?.stop()}
            >
              Завершити
            </button>
          )}
        </div>
      ) : (
        <button
          type="button"
          className="mic-action"
          aria-label="Записати голосом"
          disabled={!available || working.current || !!draft}
          onClick={() => void start()}
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
            <rect x="9" y="2" width="6" height="13" rx="3" />
            <path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8" />
          </svg>
        </button>
      )}
      {message && (
        <p className="voice-inline-status" role="status">
          {message}
        </p>
      )}
      {draft && state === "FAILED" && (
        <button type="button" onClick={() => void save(draft)}>
          Повторити збереження аудіо
        </button>
      )}
    </div>
  );
}
const labels: Record<string, string> = {
  WAITING_FOR_LOCAL_ASR: "Очікує розпізнавання",
  LOCAL_AUDIO_SAVED: "Записано",
  MAC_AUDIO_CONFIRMED: "Записано",
  TRANSCRIPTION_QUEUED: "Очікує розпізнавання",
  TRANSCRIBING: "Розпізнається",
  TRANSCRIPT_READY: "Готово",
  REVIEW_REQUIRED: "Потрібна перевірка",
  FAILED: "Помилка",
  CANCELLED: "Скасовано",
};
export function VoiceHistory({
  csrf = "",
  phone,
  onInsert,
}: {
  csrf?: string;
  phone?: PhoneStore;
  onInsert?: (text: string, source: VoiceReference | null) => void;
}) {
  const [items, setItems] = useState<VoiceItem[]>([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function refresh() {
    setItems(await list(csrf, phone));
  }
  useEffect(() => {
    let alive = true;
    const refreshSafe = () =>
      void list(csrf, phone)
        .then((rows) => {
          if (alive) setItems(rows);
        })
        .catch(() => {
          if (alive)
            setError("Не вдалося відкрити записи. Перевірте локальний сервіс.");
        });
    refreshSafe();
    const timer = setInterval(refreshSafe, 1000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);
  async function action(fn: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await fn();
      await refresh();
    } catch (error) {
      const code = safePilotErrorCode(error);
      setError(
        code === "LOCAL_SERVICE_UNAVAILABLE"
          ? "Запис збережено. Перевірте локальний сервіс і повторіть."
          : pilotErrorMessage(code),
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="voice-history" aria-label="Історія голосових записів">
      <p>
        Аудіо залишається локально.{" "}
        {phone
          ? "Черга очікує схваленого приватного транспорту до Mac. Інтернет сам по собі не запускає передавання."
          : "Повторіть розпізнавання, коли локальний whisper.cpp доступний."}
      </p>
      {items.length === 0 && <p>Голосових записів ще немає.</p>}
      {items.map((item) => {
        const t = item.transcript,
          value = t?.edited ?? t?.candidate;
        const state = t?.state ?? item.ux_state ?? item.state;
        return (
          <article key={item.id} className="voice-history-item">
            <p>
              <strong>{labels[state] ?? "Записано"}</strong> ·{" "}
              {new Date(item.created ?? "").toLocaleString("uk-UA")} ·{" "}
              {Math.round(item.duration ?? (item.byte_size - 44) / 32000)} с
            </p>
            {value && <p className="preserve-text">{value}</p>}
            <div className="actions">
              {!phone &&
                ![
                  "TRANSCRIBING",
                  "TRANSCRIPTION_QUEUED",
                  "TRANSCRIPT_READY",
                  "REVIEW_REQUIRED",
                ].includes(t?.state ?? "") && (
                  <button
                    disabled={busy}
                    onClick={() =>
                      void action(() =>
                        voiceCall(csrf, `/audio/${item.id}/transcribe`, {
                          mode: "LOCAL",
                          language: "uk",
                        }),
                      )
                    }
                  >
                    Повторити розпізнавання
                  </button>
                )}
              {value &&
                onInsert &&
                ["TRANSCRIPT_READY", "REVIEW_REQUIRED"].includes(
                  t?.state ?? "",
                ) && (
                  <button
                    disabled={busy}
                    onClick={() =>
                      void action(async () => {
                        onInsert(value, await voiceReference(item));
                      })
                    }
                  >
                    Використати текст
                  </button>
                )}
              <button
                disabled={busy}
                onClick={() => {
                  if (
                    confirm(
                      "Видалити локальний аудіозапис? Старі резервні копії можуть його зберігати.",
                    )
                  )
                    void action(() =>
                      phone
                        ? phone.deleteAudio(item.id)
                        : voiceCall(csrf, `/audio/${item.id}/delete`, {
                            confirm: true,
                          }),
                    );
                }}
              >
                Видалити аудіо
              </button>
            </div>
          </article>
        );
      })}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
