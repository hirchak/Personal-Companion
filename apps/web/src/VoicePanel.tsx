import React, { useEffect, useRef, useState } from "react";
import { PCMRecorder } from "./pcm-recorder";
import {
  AUDIO_CHUNK,
  audioHash,
  audioBase64,
  audioBegin,
  type AudioBegin,
  type Transcript,
} from "./audio-types";
import type { PhoneStore } from "./phone-store";
import type { VoiceReference } from "./conversation-model";
type Item = {
  id: string;
  state: string;
  content_hash: string;
  byte_size: number;
  transcript: Transcript | null;
  retention: string;
  uploaded?: number;
};
const states: Record<string, string> = {
  LOCAL_AUDIO_SAVED: "Аудіо збережено на телефоні · очікує Mac",
  UPLOADING: "Передаємо на Mac",
  MAC_AUDIO_CONFIRMED: "Аудіо збережено на Mac",
  MAC_AUDIO_DELETED: "Mac видалив аудіо · телефонна копія збережена",
  FAILED: "Потрібна повторна спроба",
  CANCELLED: "Передавання скасовано · телефонна копія збережена",
  TRANSCRIPTION_QUEUED: "Очікує транскрипції",
  TRANSCRIBING: "Розпізнаємо локально",
  TRANSCRIPT_READY: "Кандидат · перевірте текст",
  CONFIRMED: "Текст підтверджено",
  DELETED: "Аудіо видалено",
};
function failure(e: unknown) {
  const code = e instanceof Error ? e.message : "";
  if (
    code.includes("NotAllowed") ||
    code.includes("Permission") ||
    code.includes("permission")
  )
    return "Доступ до мікрофона не надано. Дозвольте його для цього сайту й повторіть.";
  if (code === "CANCELLED")
    return "Передавання скасовано. Телефонна копія збережена; стан Mac можна перевірити окремо.";
  if (code.includes("NOTHING_RECOGNIZED"))
    return "Нічого не розпізнано. Перевірте запис або запишіть ще раз.";
  if (code.includes("LOCAL_ASR_BACKEND"))
    return "Локальна модель ще не встановлена. Аудіо збережене; доступний лише явно обраний synthetic тест.";
  if (code.includes("REPAIR_REQUIRED"))
    return "Потрібне повторне з’єднання й узгодження з Mac. Телефонна копія збережена.";
  if (code.includes("AUDIO_OPERATION_REUSE"))
    return "Це передавання вже скасоване. Збережену копію можна експортувати або видалити.";
  if (code.includes("DURATION"))
    return "Запис надто короткий або перерваний. Чернетка лишилася тут; повторіть запис.";
  return "Операція не завершилася. Незбережене аудіо лишається лише в пам’яті цієї вкладки: повторіть, експортуйте або відкиньте.";
}
function download(value: Blob, name: string) {
  const url = URL.createObjectURL(value);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function VoicePanel({
  csrf = "",
  phone,
  onJournalChange,
  onInsert,
  allowSyntheticAsr = true,
  autoStart = false,
}: {
  csrf?: string;
  phone?: PhoneStore;
  onJournalChange?: () => void;
  onInsert?: (text: string, source: VoiceReference) => void;
  allowSyntheticAsr?: boolean;
  autoStart?: boolean;
}) {
  const [items, setItems] = useState<Item[]>([]),
    [recording, setRecording] = useState(false),
    [starting, setStarting] = useState(false),
    [paused, setPaused] = useState(false);
  const [elapsed, setElapsed] = useState(0),
    [draft, setDraft] = useState<Uint8Array | null>(null),
    [busy, setBusy] = useState(""),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [fake, setFake] = useState(false),
    [text, setText] = useState<Record<string, string>>({}),
    [retention, setRetention] = useState<Record<string, string>>({});
  const [rescuePassword, setRescuePassword] = useState("");
  const [localAvailable, setLocalAvailable] = useState(false);
  const recorder = useRef<PCMRecorder | null>(null),
    alive = useRef(true),
    cancelled = useRef(false),
    savedBegin = useRef<AudioBegin | null>(null),
    working = useRef(false);
  const pending = useRef(false);
  const autoTriggered = useRef(false);
  useEffect(() => {
    if (autoStart && !autoTriggered.current) {
      autoTriggered.current = true;
      void start();
    }
  }, []);
  const confirmations = useRef<
    Record<string, { operation_id: string; entry_id: string }>
  >({});
  async function call(path: string, body?: unknown) {
    if (phone)
      return phone.voiceCall(path, body === undefined ? "GET" : "POST", body);
    const response = await fetch("/api/v1/voice" + path, {
      method: body === undefined ? "GET" : "POST",
      credentials: "same-origin",
      cache: "no-store",
      headers: {
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        "X-CSRF-Token": csrf,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!response.ok) {
      const e = await response.json();
      throw new Error(e.code);
    }
    return response.json();
  }
  async function refresh() {
    const rows: Item[] = phone
      ? (await phone.audios()).map((a) => ({
          id: a.begin.audio_id,
          state: a.state,
          content_hash: a.begin.content_hash,
          byte_size: a.begin.byte_size,
          transcript: a.transcript,
          retention: a.retention,
          uploaded: a.uploaded,
        }))
      : await (async () => {
          const data = await call("/audio");
          if (alive.current)
            setLocalAvailable(data.actual_backend?.available === true);
          return data.items;
        })();
    if (alive.current) setItems(rows);
    return rows;
  }
  useEffect(() => {
    alive.current = true;
    void refresh().catch((e) => setError(failure(e)));
    return () => {
      alive.current = false;
      cancelled.current = true;
      recorder.current?.cancel();
    };
  }, []);
  useEffect(() => {
    if (!recording) return;
    const timer = setInterval(
      () => setElapsed(recorder.current?.elapsed() ?? 0),
      200,
    );
    const hidden = () => {
      if (document.hidden) recorder.current?.stop("BACKGROUND_INTERRUPTION");
    };
    document.addEventListener("visibilitychange", hidden);
    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", hidden);
    };
  }, [recording]);
  useEffect(() => {
    pending.current = recording || starting || Boolean(draft);
  }, [recording, starting, draft]);
  useEffect(() => {
    const unload = (e: BeforeUnloadEvent) => {
      if (pending.current) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", unload);
    return () => window.removeEventListener("beforeunload", unload);
  }, []);
  useEffect(() => {
    if (
      !items.some((x) =>
        ["TRANSCRIPTION_QUEUED", "TRANSCRIBING"].includes(
          x.transcript?.state ?? "",
        ),
      )
    )
      return;
    const timer = setInterval(() => {
      void (async () => {
        if (phone)
          for (const x of items)
            if (
              x.transcript &&
              ["TRANSCRIPTION_QUEUED", "TRANSCRIBING"].includes(
                x.transcript.state,
              )
            )
              await phone.refreshAudio(x.id);
        await refresh();
      })().catch((e) => setError(failure(e)));
    }, 700);
    return () => clearInterval(timer);
  }, [items]);
  async function action(id: string, fn: () => Promise<unknown>) {
    if (working.current) return;
    working.current = true;
    setBusy(id);
    setError("");
    try {
      await fn();
      if (alive.current) await refresh();
    } catch (e) {
      if (alive.current) setError(failure(e));
    } finally {
      working.current = false;
      if (alive.current) setBusy("");
    }
  }
  async function save(bytes: Uint8Array) {
    await action("capture", async () => {
      if (phone) {
        await phone.saveAudio(bytes);
        setNotice("Аудіо збережено на телефоні. Ще немає копії на Mac.");
      } else {
        const begin = savedBegin.current ?? {
          ...audioBegin(bytes),
          content_hash: await audioHash(bytes),
        };
        savedBegin.current = begin;
        const remote = await call("/audio", begin);
        setNotice("Зберігаємо аудіо на Mac…");
        if (remote.state !== "MAC_AUDIO_CONFIRMED")
          for (let index = 0; index * AUDIO_CHUNK < bytes.length; index++) {
            const part = bytes.slice(
              index * AUDIO_CHUNK,
              (index + 1) * AUDIO_CHUNK,
            );
            if (!remote.received_chunks.includes(index))
              await call(`/audio/${begin.audio_id}/chunks`, {
                index,
                content_hash: await audioHash(part),
                data: audioBase64(part),
              });
          }
        const receipt = await call(`/audio/${begin.audio_id}/finalize`, {});
        if (
          receipt.state !== "MAC_AUDIO_CONFIRMED" ||
          receipt.content_hash !== begin.content_hash
        )
          throw new Error("INVALID_MAC_RECEIPT");
        setNotice("Аудіо збережено на Mac.");
      }
      if (alive.current) {
        setDraft(null);
        savedBegin.current = null;
      }
    });
  }
  async function start() {
    setError("");
    setNotice("");
    setStarting(true);
    setElapsed(0);
    setPaused(false);
    savedBegin.current = null;
    const rec = new PCMRecorder(
      (bytes) => {
        if (!alive.current) return;
        setRecording(false);
        setDraft(bytes);
        void save(bytes);
      },
      () =>
        setNotice(
          "Запис перервано. Зберігаємо доступну частину; перевірте результат.",
        ),
    );
    recorder.current = rec;
    try {
      const started = await rec.start();
      if (alive.current && started && recorder.current === rec)
        setRecording(true);
    } catch (e) {
      if (alive.current) setError(failure(e));
    } finally {
      if (alive.current && recorder.current === rec) setStarting(false);
    }
  }
  async function upload(id: string) {
    if (!phone) return;
    cancelled.current = false;
    await action(id, async () => {
      await phone.uploadAudio(
        id,
        () => cancelled.current,
        () => {
          void refresh();
        },
      );
      setNotice("Mac підтвердив durable копію аудіо.");
    });
  }
  async function transcribe(item: Item) {
    await action(item.id, async () => {
      const result = await call(`/audio/${item.id}/transcribe`, {
        mode:
          fake && allowSyntheticAsr
            ? "FAKE"
            : localAvailable
              ? "LOCAL"
              : "DISABLED",
        language: "uk",
      });
      if (phone)
        await phone.mutateAudio(item.id, (x) => {
          x.transcript = {
            id: result.transcript_id,
            audio_id: item.id,
            audio_hash: item.content_hash,
            engine: "",
            model: null,
            candidate: null,
            edited: null,
            state: result.state,
            revision: 1,
            entry_id: null,
            entry_revision: null,
            error: null,
          };
        });
    });
  }
  async function editTranscript(item: Item) {
    const t = item.transcript!;
    await action(item.id, async () => {
      await call(`/transcripts/${t.id}/edit`, {
        revision: t.revision,
        text: text[t.id] ?? t.edited ?? t.candidate ?? "",
      });
      if (phone) await phone.refreshAudio(item.id);
      setNotice("Виправлення транскрипту збережено. Це ще не запис щоденника.");
    });
  }
  async function insertTranscript(item: Item) {
    const t = item.transcript!;
    await action(item.id, async () => {
      const changed = text[t.id] ?? t.edited ?? t.candidate ?? "";
      let revision = t.revision;
      if (changed !== (t.edited ?? t.candidate ?? "")) {
        const saved = await call(`/transcripts/${t.id}/edit`, {
          revision,
          text: changed,
        });
        revision = saved.revision;
      }
      onInsert?.(changed, {
        kind: "VOICE_TRANSCRIPT",
        transcript_id: t.id,
        revision,
        audio_hash: item.content_hash,
        text_hash: await audioHash(new TextEncoder().encode(changed)),
      });
      setNotice(
        "Текст вставлено в поле розмови. Повідомлення ще не надіслане.",
      );
    });
  }
  async function confirmTranscript(item: Item) {
    const t = item.transcript!;
    await action(item.id, async () => {
      const changed = text[t.id] ?? t.edited ?? t.candidate ?? "";
      let revision = t.revision;
      if (changed !== (t.edited ?? t.candidate ?? "")) {
        const edited = await call(`/transcripts/${t.id}/edit`, {
          revision,
          text: changed,
        });
        revision = edited.revision;
      }
      const ids = (confirmations.current[t.id] ??= {
        operation_id: crypto.randomUUID(),
        entry_id: crypto.randomUUID(),
      });
      await call(`/transcripts/${t.id}/confirm`, {
        revision,
        ...ids,
        base_revision: 0,
        retention: retention[item.id] ?? "KEEP",
      });
      if (phone) {
        await phone.refreshAudio(item.id);
        if (retention[item.id] === "DELETE_AFTER_CONFIRM")
          await phone.deleteAudio(item.id, true);
        await phone.pull();
      }
      setNotice("Перевірений текст збережено в щоденнику. AI не запускався.");
      onJournalChange?.();
    });
  }
  return (
    <section className="voice-panel" aria-label="Голосові записи">
      <h2>Записати голосом</h2>
      <p>
        {onInsert
          ? "Аудіо залишається локально. Перевірте текст, вставте в поле й надішліть лише коли вирішите."
          : "Аудіо лишається локально. Текст потрапить у щоденник після вашого підтвердження."}
      </p>
      {!recording && !starting && !draft && (
        <button
          onClick={() => void start()}
          disabled={Boolean(busy)}
          aria-label="Почати голосовий запис"
        >
          <svg
            viewBox="0 0 24 24"
            width="20"
            height="20"
            aria-hidden="true"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.7"
          >
            <rect x="9" y="2" width="6" height="13" rx="3" />
            <path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8" />
          </svg>{" "}
          Мікрофон
        </button>
      )}
      {starting && (
        <div>
          <p role="status">Очікуємо доступ до мікрофона…</p>
          <button
            onClick={() => {
              recorder.current?.cancel();
              setStarting(false);
            }}
          >
            Скасувати доступ до мікрофона
          </button>
        </div>
      )}
      {recording && (
        <div className="voice-recording">
          <p role="status">
            {paused ? "Пауза" : "Записуємо"} · {Math.floor(elapsed / 60)}:
            {String(Math.floor(elapsed % 60)).padStart(2, "0")}
          </p>
          <div className="actions">
            <button onClick={() => setPaused(recorder.current!.pause())}>
              {paused ? "Продовжити запис" : "Пауза запису"}
            </button>
            <button onClick={() => recorder.current?.stop()}>
              Зупинити й зберегти аудіо
            </button>
            <button
              onClick={() => {
                recorder.current?.cancel();
                setRecording(false);
                setNotice("Незбережений запис відкинуто.");
              }}
            >
              Скасувати запис
            </button>
          </div>
        </div>
      )}
      {notice && <p role="status">{notice}</p>}
      {error && <p role="alert">{error}</p>}
      {draft && (
        <div className="voice-draft">
          <p>
            Аудіочернетка у пам’яті вкладки · {Math.ceil(draft.length / 1024)}{" "}
            KiB. Закриття або crash може її втратити.
          </p>
          <div className="actions">
            <button disabled={Boolean(busy)} onClick={() => void save(draft)}>
              Повторити збереження аудіо
            </button>
            <button
              onClick={() =>
                void (async () => {
                  if (phone)
                    download(
                      new Blob(
                        [JSON.stringify(await phone.exportAudioDraft(draft))],
                        { type: "application/json" },
                      ),
                      "synthetic-audio-encrypted-rescue.json",
                    );
                  else if (
                    confirm(
                      "Експортувати аудіочернетку як незашифрований локальний WAV?",
                    )
                  )
                    download(
                      new Blob([draft as BlobPart], { type: "audio/wav" }),
                      "synthetic-audio-draft.wav",
                    );
                })().catch((e) => setError(failure(e)))
              }
            >
              Експортувати аудіочернетку
            </button>
            <button
              disabled={Boolean(busy)}
              onClick={() => {
                setDraft(null);
                savedBegin.current = null;
                setNotice("Аудіочернетку відкинуто.");
              }}
            >
              Відкинути аудіочернетку
            </button>
          </div>
        </div>
      )}
      <details>
        <summary>Локальне розпізнавання</summary>
        <p>
          Локальне розпізнавання ще не налаштовано. Реальна ASR-модель: не
          запущена. Немає cloud fallback. Synthetic тест не вимірює точність
          українського мовлення.
        </p>
        {allowSyntheticAsr && (
          <label className="check">
            <input
              type="checkbox"
              checked={fake}
              onChange={(e) => setFake(e.target.checked)}
            />
            Використати synthetic fake ASR
          </label>
        )}
      </details>
      {phone && (
        <details>
          <summary>Відновити encrypted аудіо</summary>
          <p>
            Імпорт створить нову аудіокопію в цьому unlocked браузері. Journal
            recovery і аудіо відновлюються окремо.
          </p>
          <label>
            Пароль аудіоекспорту
            <input
              type="password"
              autoComplete="off"
              value={rescuePassword}
              onChange={(e) => setRescuePassword(e.target.value)}
            />
          </label>
          <label>
            Encrypted аудіофайл
            <input
              type="file"
              accept="application/json,.json"
              disabled={Boolean(busy) || !rescuePassword}
              onChange={(e) => {
                const file = e.target.files?.[0];
                e.target.value = "";
                if (!file) return;
                void action("recovery", async () => {
                  if (file.size > 20 * 1024 * 1024)
                    throw new Error("AUDIO_SIZE_LIMIT");
                  const pkg = JSON.parse(await file.text());
                  await phone.restoreAudioDraft(pkg, rescuePassword);
                  setRescuePassword("");
                  setNotice(
                    "Аудіокопію відновлено encrypted у цьому браузері.",
                  );
                });
              }}
            />
          </label>
        </details>
      )}
      {items.map((item) => {
        const t = item.transcript;
        return (
          <article
            className="voice-item"
            key={item.id}
            aria-label="Збережений голосовий запис"
          >
            <p className="metadata">
              {states[item.state] ?? item.state} ·{" "}
              {Math.ceil(item.byte_size / 1024)} KiB
            </p>
            {item.state === "UPLOADING" && (
              <progress
                aria-label="Передавання аудіо"
                max={item.byte_size}
                value={item.uploaded ?? 0}
              />
            )}
            {t && (
              <p role="status">
                {states[t.state] ?? t.state}
                {t.error === "NOTHING_RECOGNIZED"
                  ? " · Нічого не розпізнано. Перевірте запис."
                  : t.error
                    ? " · Повторіть локальне розпізнавання."
                    : ""}
              </p>
            )}
            <div className="actions">
              {phone &&
                ["LOCAL_AUDIO_SAVED", "FAILED", "UPLOADING"].includes(
                  item.state,
                ) && (
                  <button
                    disabled={Boolean(busy)}
                    onClick={() => void upload(item.id)}
                  >
                    Передати аудіо на Mac
                  </button>
                )}
              {phone && busy === item.id && item.state === "UPLOADING" && (
                <button
                  onClick={() => {
                    cancelled.current = true;
                    void phone
                      .cancelAudio(item.id)
                      .then(refresh)
                      .catch((e) => setError(failure(e)));
                  }}
                >
                  Скасувати передавання
                </button>
              )}
              {item.state === "MAC_AUDIO_CONFIRMED" &&
                (!t || ["FAILED", "CANCELLED"].includes(t.state)) && (
                  <button
                    disabled={Boolean(busy)}
                    onClick={() => void transcribe(item)}
                  >
                    {t ? "Повторити транскрипцію" : "Розпізнати локально"}
                  </button>
                )}
              {t &&
                [
                  "TRANSCRIPTION_QUEUED",
                  "TRANSCRIBING",
                  "TRANSCRIPT_READY",
                ].includes(t.state) && (
                  <button
                    disabled={Boolean(busy)}
                    onClick={() =>
                      void action(item.id, async () => {
                        await call(`/transcripts/${t.id}/cancel`, {});
                        if (phone) await phone.refreshAudio(item.id);
                      })
                    }
                  >
                    Скасувати транскрипт
                  </button>
                )}
            </div>
            {phone && (
              <details>
                <summary>Відновлення зв’язку для цього аудіо</summary>
                <p>
                  Після re-pair і узгодження журналу можна створити нову
                  аудіокопію для передавання. Попередня локальна копія лишиться
                  до явного видалення.
                </p>
                <button
                  disabled={Boolean(busy)}
                  onClick={() => {
                    if (
                      window.confirm(
                        "Створити нову аудіокопію після re-pair? Старе передавання не буде відновлене, попередня копія збережеться.",
                      )
                    )
                      void action(item.id, () =>
                        phone.copyAudioForRepair(item.id),
                      );
                  }}
                >
                  Створити аудіокопію після re-pair
                </button>
              </details>
            )}
            {t?.state === "TRANSCRIPT_READY" && (
              <div className="voice-review">
                <label>
                  Перевірити та виправити транскрипт
                  <textarea
                    value={text[t.id] ?? t.edited ?? t.candidate ?? ""}
                    onChange={(e) =>
                      setText({ ...text, [t.id]: e.target.value })
                    }
                  />
                </label>
                <p className="metadata">
                  Кандидат ASR · {t.engine} · {t.model ?? "модель невідома"}. Це
                  ще не ваш підтверджений запис.
                </p>
                {!onInsert && (
                  <label>
                    Оригінальне аудіо
                    <select
                      value={retention[item.id] ?? "KEEP"}
                      onChange={(e) =>
                        setRetention({
                          ...retention,
                          [item.id]: e.target.value,
                        })
                      }
                    >
                      <option value="KEEP">Зберегти аудіо</option>
                      <option value="DELETE_AFTER_CONFIRM">
                        Видалити після підтвердження тексту
                      </option>
                    </select>
                  </label>
                )}
                <button
                  disabled={Boolean(busy)}
                  onClick={() => void editTranscript(item)}
                >
                  Зберегти виправлення транскрипту
                </button>
                <button
                  disabled={
                    Boolean(busy) ||
                    !(text[t.id] ?? t.edited ?? t.candidate ?? "").trim()
                  }
                  onClick={() =>
                    void (onInsert
                      ? insertTranscript(item)
                      : confirmTranscript(item))
                  }
                >
                  {onInsert
                    ? "Вставити текст у розмову"
                    : "Підтвердити текст у щоденник"}
                </button>
              </div>
            )}
            <div className="actions">
              {phone &&
                ["MAC_AUDIO_CONFIRMED", "FAILED", "CANCELLED"].includes(
                  item.state,
                ) && (
                  <button
                    disabled={Boolean(busy)}
                    onClick={() =>
                      void action(item.id, async () => {
                        await phone.refreshAudio(item.id);
                        await phone.pull();
                        onJournalChange?.();
                      })
                    }
                  >
                    Перевірити стан аудіо на Mac
                  </button>
                )}
              {phone && (
                <button
                  disabled={Boolean(busy)}
                  onClick={() =>
                    void action(item.id, async () => {
                      const bytes = await phone.audioData(item.id);
                      const rescue = await phone.exportAudioDraft(bytes);
                      download(
                        new Blob([JSON.stringify(rescue)], {
                          type: "application/json",
                        }),
                        "synthetic-audio-encrypted-rescue.json",
                      );
                    })
                  }
                >
                  Експортувати encrypted аудіо
                </button>
              )}
              {phone && (
                <button
                  disabled={Boolean(busy)}
                  onClick={() => {
                    if (
                      window.confirm(
                        "Видалити лише телефонну аудіокопію? Unsynced аудіо може бути єдиною копією. Mac, queued ASR та backups не будуть стерті.",
                      )
                    )
                      void action(item.id, () => phone.deleteAudio(item.id));
                  }}
                >
                  Видалити лише телефонну копію
                </button>
              )}
              <button
                disabled={Boolean(busy)}
                onClick={() => {
                  if (
                    confirm(
                      phone
                        ? "Видалити аудіо, транскрипт і локальну телефонну копію? Офлайн копії та backups можуть лишитися."
                        : "Видалити аудіо й транскрипт? Підтверджений запис щоденника збережеться. Backups можуть містити попередні байти.",
                    )
                  )
                    void action(item.id, async () => {
                      if (phone) {
                        if (item.state === "MAC_AUDIO_CONFIRMED" || t)
                          await call(`/audio/${item.id}/delete`, {
                            confirm: true,
                          });
                        else await phone.cancelAudio(item.id);
                        await phone.deleteAudio(item.id);
                      } else
                        await call(`/audio/${item.id}/delete`, {
                          confirm: true,
                        });
                    });
                }}
              >
                Видалити аудіо зараз
              </button>
            </div>
          </article>
        );
      })}
      <p className="voice-limit">
        До 2 хвилин. До завершеного збереження запис живе лише у вкладці.
        Перехід у фон зупиняє запис; фонова робота не гарантована.
        {phone &&
          " Браузер може очистити сховище. Окремий encrypted export аудіо доступний; journal recovery не містить аудіо."}{" "}
        Видалення не гарантує стирання backups чи офлайн пристроїв.
      </p>
    </section>
  );
}
