import React, { useEffect, useRef, useState } from "react";
import {
  PhoneStore,
  StoreError,
  type LocalState,
  type RecordItem,
} from "./phone-store";
import { blank, names, typed, fieldNames, type Draft } from "./journal-ui";
import { PhoneHealthPanel } from "./PhoneHealthPanel";
import { ComposerVoice, VoiceHistory } from "./ComposerVoice";
import { VoicePanel } from "./VoicePanel";
import { CreativePanel } from "./CreativePanel";
import { SpacePanel } from "./SpacePanel";
import { defaultSpace } from "./space-model";
import { phoneCreativeAdapter } from "./phone-creative";
import { EntryEditor } from "./EntryEditor";
import { draftPayload, validatePayload } from "./phone-validation";
const labels: Record<string, string> = {
  QUEUED: "Збережено на телефоні · Очікує Mac",
  SYNCING: "Синхронізація…",
  MAC_CONFIRMED: "На Mac",
  CONFLICT: "Конфлікт",
  FAILED: "Збережено на телефоні · Sync не вдався",
  REVOKED_OR_REPAIR_REQUIRED: "Потрібен re-pair / reconciliation",
};
function errorText(e: unknown) {
  const code =
    e instanceof StoreError ? e.code : e instanceof Error ? e.message : "";
  if (code === "UNLOCK_OR_INTEGRITY_FAILED")
    return "Пароль неправильний або сховище пошкоджене. Дані не перезаписані.";
  if (code === "EMPTY_OR_EVICTED")
    return "Локальне сховище порожнє або очищене. Скористайтеся encrypted recovery.";
  if (code.includes("SCHEMA"))
    return "Непідтримувана версія або неправильні поля. Нічого не перезаписано.";
  if (code === "REPAIR_REQUIRED")
    return "Пристрій відкликаний або epoch змінився. Черга збережена; потрібен re-pair і явне узгодження.";
  if (code === "PASSPHRASE_TOO_SHORT")
    return "Введіть пароль щонайменше з 12 символів.";
  return "Операція не завершилася. Незбережений текст лишається у відкритій сесії; повторіть або експортуйте recovery.";
}
export function PhoneApp() {
  const store = useRef(new PhoneStore());
  const [voiceBusy, setVoiceBusy] = useState(false);
  const [surface, setSurface] = useState("conversation");
  const [data, setData] = useState<LocalState | null>(null),
    [exists, setExists] = useState<boolean | null>(null),
    [pass, setPass] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState(""),
    [online, setOnline] = useState(navigator.onLine);
  const [editing, setEditing] = useState<RecordItem | "new" | null>(null),
    [draft, setDraft] = useState(blank()),
    [q, setQ] = useState(""),
    [filter, setFilter] = useState(""),
    [settings, setSettings] = useState(false),
    [invitation, setInvitation] = useState(""),
    [label, setLabel] = useState("Synthetic phone"),
    [waiting, setWaiting] = useState<ServiceWorker | null>(null),
    [storage, setStorage] = useState(
      "Найкраща спроба браузера; persistence не гарантована.",
    ),
    [merge, setMerge] = useState<Record<string, string>>({});
  const alive = useRef(true),
    last = useRef(Date.now()),
    opened = useRef(Date.now()),
    syncing = useRef(false);
  const unlockGeneration = useRef(0);
  const creativeGeneration = unlockGeneration.current;
  useEffect(() => {
    store.current
      .exists()
      .then(setExists)
      .catch((e) => {
        setExists(false);
        setError(errorText(e));
      });
    navigator.serviceWorker
      ?.register("/phone/sw.js", { scope: "/phone/" })
      .then((reg) => {
        if (reg.waiting) setWaiting(reg.waiting);
        reg.addEventListener("updatefound", () => {
          const w = reg.installing;
          w?.addEventListener("statechange", () => {
            if (w.state === "installed" && reg.waiting) setWaiting(reg.waiting);
          });
        });
      })
      .catch(() =>
        setError(
          "Shell ще не закешований. Перший online запуск потрібний для offline PWA.",
        ),
      );
    const network = () => setOnline(navigator.onLine);
    window.addEventListener("online", network);
    window.addEventListener("offline", network);
    return () => {
      alive.current = false;
      store.current.lock();
      window.removeEventListener("online", network);
      window.removeEventListener("offline", network);
    };
  }, []);
  function lock() {
    unlockGeneration.current++;
    store.current.lock();
    setData(null);
    setVoiceBusy(false);
    setSurface("conversation");
    setPass("");
    setDraft(blank());
    setEditing(null);
    setInvitation("");
    setMerge({});
    setQ("");
    setError("");
    setNotice("");
  }
  useEffect(() => {
    if (!data) return;
    const activity = () => {
      if (
        Date.now() - last.current >= 900000 ||
        Date.now() - opened.current >= 28800000
      ) {
        lock();
        return;
      }
      last.current = Date.now();
    };
    const check = () => {
      if (
        Date.now() - last.current >= 900000 ||
        Date.now() - opened.current >= 28800000
      )
        lock();
    };
    const timer = setInterval(check, 1000);
    window.addEventListener("pointerdown", activity);
    window.addEventListener("keydown", activity);
    window.addEventListener("focus", check);
    document.addEventListener("visibilitychange", check);
    return () => {
      clearInterval(timer);
      window.removeEventListener("pointerdown", activity);
      window.removeEventListener("keydown", activity);
      window.removeEventListener("focus", check);
      document.removeEventListener("visibilitychange", check);
    };
  }, [Boolean(data)]);
  async function unlock(e: React.FormEvent) {
    e.preventDefault();
    const g = unlockGeneration.current;
    setBusy(true);
    setError("");
    try {
      let s: LocalState;
      try {
        s = exists
          ? await store.current.unlock(pass)
          : await store.current.create(pass);
      } catch (e) {
        if (
          e instanceof StoreError &&
          e.code === "LOCAL_MIGRATION_CONFIRMATION_REQUIRED" &&
          confirm(
            "Оновити encrypted storage schema 1→2? Уся pending черга зберігається атомарно; без підтвердження нічого не зміниться.",
          )
        )
          s = await store.current.unlock(pass, true);
        else throw e;
      }
      if (g !== unlockGeneration.current) {
        store.current.lock();
        return;
      }
      setPass("");
      last.current = opened.current = Date.now();
      setExists(true);
      setData(s);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  async function sync() {
    if (syncing.current) return;
    syncing.current = true;
    const g = unlockGeneration.current;
    try {
      setNotice("Синхронізація…");
      const s = await store.current.sync();
      if (g === unlockGeneration.current && alive.current) {
        setData(s);
        setNotice("Синхронізацію перевірено за Mac receipts");
        setError("");
      }
    } catch (e) {
      if (g === unlockGeneration.current) {
        setError(errorText(e));
        try {
          setData(await store.current.state());
        } catch {}
      }
    } finally {
      syncing.current = false;
    }
  }
  useEffect(() => {
    if (data?.pairing && !data.repair && online) void sync();
  }, [online, Boolean(data?.pairing)]);
  function open(r: RecordItem | "new") {
    setError("");
    setNotice("");
    setEditing(r);
    if (r === "new") setDraft(blank());
    else
      setDraft({
        ...blank(),
        ...Object.fromEntries(
          Object.keys(blank()).map((k) => [
            k,
            String((r.payload as any)[k] ?? ""),
          ]),
        ),
        type: r.payload.type ?? "inbox",
        tags: r.payload.tags?.join(", ") ?? "",
      } as Draft);
  }
  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const g = unlockGeneration.current;
    try {
      const payload = draftPayload(draft);
      if (
        draft.type === "creative" &&
        editing &&
        editing !== "new" &&
        editing.payload.type === "creative"
      )
        payload.creative_meta = editing.payload.creative_meta ?? null;
      let confirmType = false;
      if (
        editing &&
        editing !== "new" &&
        editing.payload.type !== draft.type &&
        (typed[editing.payload.type ?? "inbox"].some(
          (k) => (editing.payload as any)[k] != null,
        ) ||
          editing.payload.creative_meta != null)
      ) {
        confirmType = confirm(
          "Прибрати поля " +
            typed[editing.payload.type ?? "inbox"]
              .map((k) => fieldNames[k])
              .join(", ") +
            (editing.payload.creative_meta
              ? " та організацію творчої полиці"
              : "") +
            "? Попередня Mac версія залишиться в історії після sync.",
        );
        if (!confirmType) return;
      }
      const s = await store.current.capture(
        editing === "new" ? "create" : "edit",
        editing === "new" ? crypto.randomUUID() : (editing as RecordItem).id,
        payload,
        confirmType,
      );
      if (g === unlockGeneration.current) {
        setData(s);
        setEditing(null);
        setDraft(blank());
        setNotice("Збережено на телефоні · Очікує Mac");
        if (online && s.pairing && !s.repair) void sync();
      }
    } catch (e) {
      if (g === unlockGeneration.current) setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  async function remove(r: RecordItem) {
    if (!confirm("Видалити локальний запис і поставити delete у чергу?"))
      return;
    try {
      setData(await store.current.capture("delete", r.id, null));
      setNotice("Delete збережено на телефоні · Очікує Mac");
      if (online && data?.pairing) void sync();
    } catch (e) {
      setError(errorText(e));
    }
  }
  async function exportRecovery() {
    try {
      const pkg = await store.current.recovery();
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(pkg)], { type: "application/json" }),
      );
      const a = document.createElement("a");
      a.href = url;
      a.download = "synthetic-phone-recovery.json";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setError(errorText(e));
    }
  }
  async function restore(file: File) {
    setBusy(true);
    try {
      if (file.size > 10 * 1024 * 1024) throw new Error("RECOVERY_TOO_LARGE");
      const s = await store.current.restoreRecovery(
        JSON.parse(await file.text()),
        pass,
      );
      setPass("");
      setExists(true);
      setData(s);
      setNotice(
        "Recovery відкрито локально. Auto replay вимкнено; потрібне явне pairing/узгодження.",
      );
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  if (!data)
    return (
      <main className="unlock">
        <div className="unlock-inner">
          <span className="wordmark">Особистий простір · PWA</span>
          <h1>
            Ваші думки.
            <br />
            Навіть без Mac.
          </h1>
          <p>Синтетичний demo · реальні приватні записи ще не дозволені.</p>
          <p>
            {exists
              ? "Розблокуйте encrypted сховище цього браузера."
              : "Локальне сховище порожнє: новий пристрій або очищені дані. Створіть його чи відкрийте recovery."}
          </p>
          <form onSubmit={unlock}>
            <label>
              Локальний пароль
              <input
                aria-label="Локальний пароль"
                type="password"
                autoComplete="off"
                value={pass}
                onChange={(e) => setPass(e.target.value)}
                minLength={exists ? 1 : 12}
                required
              />
            </label>
            <button className="primary" disabled={busy || exists === null}>
              {exists ? "Розблокувати телефон" : "Створити encrypted сховище"}
            </button>
          </form>
          <label>
            Відкрити encrypted recovery
            <input
              type="file"
              accept="application/json"
              disabled={busy || !pass}
              onChange={(e) => {
                if (e.target.files?.[0]) void restore(e.target.files[0]);
                e.target.value = "";
              }}
            />
          </label>
          {error && <p role="alert">{error}</p>}
          <p className="hint">
            Без пароля відновлення немає. Reload/lock прибирає ключ із
            application memory. Browser storage може бути очищене; це не Android
            Keystore.
          </p>
        </div>
      </main>
    );
  const pending = data.outbox.filter((o) => o.state !== "MAC_CONFIRMED");
  const records = Object.values(data.records)
    .filter(
      (r) =>
        !r.deleted &&
        r.payload.raw_text.includes(q) &&
        (!filter || r.payload.type === filter),
    )
    .sort((a, b) => b.localOrder - a.localOrder);
  return (
    <div className="workspace phone conversation-shell">
      <header className="app-topbar">
        <span className="wordmark">Особистий простір</span>
        <nav aria-label="Основна навігація">
          <button
            disabled={voiceBusy}
            className={surface === "conversation" ? "current" : ""}
            onClick={() => setSurface("conversation")}
          >
            Розмова
          </button>
          <button
            disabled={voiceBusy}
            className={surface === "journal" ? "current" : ""}
            onClick={() => {
              setSurface("journal");
              setFilter("");
            }}
          >
            Щоденник
          </button>
          <button
            disabled={voiceBusy}
            className={surface === "creative" ? "current" : ""}
            onClick={() => setSurface("creative")}
          >
            Творчість
          </button>
          <button
            disabled={voiceBusy}
            className={surface === "more" ? "current" : ""}
            onClick={() => setSurface("more")}
          >
            Більше
          </button>
        </nav>
      </header>
      <main className="journal app-content">
        {surface === "conversation" && (
          <section className="phone-conversation">
            <h1>Розмова</h1>
            <h2>Що у вас сьогодні на думці?</h2>
            <p>
              AI доступний на вашому Mac. Телефонний приватний транспорт ще не
              активовано. Запис голосу працює локально й офлайн.
            </p>
            <ComposerVoice
              phone={store.current}
              onBusy={setVoiceBusy}
              onDraft={() => {}}
            />
            <VoiceHistory phone={store.current} />
          </section>
        )}
        {surface === "more" && (
          <section>
            <h1>Більше</h1>
            <button onClick={() => setSurface("creative")}>
              Творча полиця
            </button>
            <button onClick={() => setSurface("health")}>
              Дані з годинника
            </button>
            <button onClick={() => setSurface("space")}>Мій простір</button>
            <h2>Голосові записи</h2>
            <VoiceHistory phone={store.current} />
            <button
              onClick={() => {
                setSurface("journal");
                setSettings(true);
              }}
            >
              Дані · резервування · налаштування
            </button>
            <button onClick={lock}>Заблокувати телефон</button>
          </section>
        )}

        {(surface === "space" || surface === "creative") && (
          <SpacePanel
            value={data.space ?? { version: 0, state: defaultSpace() }}
            save={async (base, state) => {
              const g = unlockGeneration.current;
              const s = await store.current.updateSpace(base, state);
              if (g === unlockGeneration.current) setData(s);
            }}
          />
        )}
        {surface === "creative" && (
          <CreativePanel
            phone
            adapter={phoneCreativeAdapter(store.current, (s) => {
              if (
                alive.current &&
                creativeGeneration === unlockGeneration.current
              )
                setData(s);
            })}
          />
        )}
        {surface === "health" && (
          <PhoneHealthPanel
            online={online}
            status={() => store.current.healthStatus()}
          />
        )}
        <div hidden={surface !== "journal"}>
          <nav aria-label="Фільтри щоденника">
            <button onClick={() => setFilter("")}>Усі записи</button>
            {Object.entries(names).map(([key, label]) => (
              <button key={key} onClick={() => setFilter(key)}>
                {label}
              </button>
            ))}
          </nav>
          <header>
            <div>
              <h1>Ваш щоденник</h1>
              <p>
                {online
                  ? "Mac може бути недоступний; local save не залежить від sync."
                  : "Офлайн. Записи зберігаються на телефоні; Mac ще не підтвердив чергу."}
              </p>
            </div>
            <button
              className="primary add"
              onClick={() => open("new")}
              disabled={data.repair}
            >
              + Додати запис
            </button>
          </header>
          <details className="voice-disclosure">
            <summary>Голосовий запис</summary>
            <VoicePanel
              phone={store.current}
              onJournalChange={() => {
                void store.current.state().then(setData);
              }}
            />
          </details>
          <div className="actions">
            <button onClick={() => setSettings(!settings)}>
              Налаштування телефону
            </button>
            <button
              disabled={!data.pairing || data.repair || syncing.current}
              onClick={() => void sync()}
            >
              Синхронізувати з Mac
            </button>
            <span>{pending.length} очікують</span>
          </div>
          {waiting && (
            <div className="notice">
              <p>
                Оновлення shell готове. Unsynced черга лишиться encrypted;
                storage schema не змінюється автоматично.
              </p>
              <button
                onClick={() => {
                  if (
                    !confirm(
                      "Оновити shell? Чернетка без local receipt буде втрачена.",
                    )
                  )
                    return;
                  waiting.postMessage({ type: "ACTIVATE_WAITING" });
                  navigator.serviceWorker.addEventListener(
                    "controllerchange",
                    () => location.reload(),
                    { once: true },
                  );
                }}
              >
                Оновити PWA
              </button>
            </div>
          )}
          {settings && (
            <section className="sync-settings">
              <h2>Пристрій і локальна копія</h2>
              <p>{storage}</p>
              <button
                onClick={async () => {
                  const persisted = navigator.storage?.persist
                    ? await navigator.storage.persist()
                    : false;
                  setStorage(
                    persisted
                      ? "Persistence надано браузером. Користувач/OS все одно може видалити дані."
                      : "Persistence не надано. Потрібен encrypted recovery для phone-only даних.",
                  );
                }}
              >
                Запросити persistent storage
              </button>
              <p>
                At-rest encryption — synthetic scope. Hardware/real-data
                security не затверджені.
              </p>
              <label>
                Одноразове запрошення Mac
                <input
                  type="password"
                  autoComplete="off"
                  value={invitation}
                  onChange={(e) => setInvitation(e.target.value)}
                />
              </label>
              <label>
                Назва synthetic пристрою
                <input
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  maxLength={64}
                />
              </label>
              <button
                onClick={async () => {
                  try {
                    const s = await store.current.pair(invitation, label);
                    setInvitation("");
                    setData(s);
                    setNotice("Pairing збережено encrypted.");
                    if (!s.repair) void sync();
                  } catch (e) {
                    setError(errorText(e));
                  }
                }}
              >
                З’єднати з Mac
              </button>
              <p className="hint">
                Якщо локальне збереження pairing не вдалося, Mac залишає зв’язок
                PENDING без доступу до sync. Створіть нове запрошення на Mac і
                повторіть або відкличте pending пристрій. Якщо credential
                збережено, наступна синхронізація повторить підтвердження.
              </p>
              <button onClick={() => void exportRecovery()}>
                Encrypted recovery для unsynced
              </button>
              <p>Це не Mac backup. Відкликання не стирає офлайн копію.</p>
              <button
                onClick={async () => {
                  if (
                    !confirm(
                      "Забути encrypted копію цього браузера? Unsynced записи й аудіо буде втрачено; спочатку експортуйте journal recovery і окремий encrypted audio export.",
                    )
                  )
                    return;
                  try {
                    await store.current.forget();
                    lock();
                    setExists(false);
                  } catch (e) {
                    setError(errorText(e));
                  }
                }}
              >
                Забути цей браузер
              </button>
            </section>
          )}
          {data.repair && (
            <section className="error">
              <h2>Потрібне явне узгодження</h2>
              <p>
                Стара черга не відправляється. Створіть нове запрошення Mac,
                виконайте pairing, потім оберіть варіант.
              </p>
              <button
                onClick={async () => {
                  if (
                    !confirm(
                      "Обрати актуальний Mac і відкинути локальні pending changes?",
                    )
                  )
                    return;
                  try {
                    setData(await store.current.reconcile("mac"));
                  } catch (e) {
                    setError(errorText(e));
                  }
                }}
              >
                Обрати Mac після re-pair
              </button>
              <button
                onClick={async () => {
                  if (
                    !confirm(
                      "Зберегти unsynced живі нотатки окремими новими IDs після re-pair? Старі delete не replay-яться.",
                    )
                  )
                    return;
                  try {
                    setData(await store.current.reconcile("phone_copy"));
                  } catch (e) {
                    setError(errorText(e));
                  }
                }}
              >
                Зберегти локальні новими копіями
              </button>
              <button onClick={() => void exportRecovery()}>
                Encrypted recovery
              </button>
            </section>
          )}
          <label className="search">
            Пошук
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              maxLength={200}
            />
          </label>
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
              change={(k, v) => setDraft((d) => ({ ...d, [k]: v }))}
              save={save}
              cancel={() => {
                setEditing(null);
                setDraft(blank());
              }}
              busy={busy}
              saveLabel="Зберегти на телефоні"
            />
          )}
          <h2 className="list-heading">Записи цього браузера</h2>
          {!records.length && (
            <p>
              Почніть із кількох слів. До Mac receipt єдиною копією може бути
              цей браузер.
            </p>
          )}
          {records.map((r) => (
            <article className="entry" key={r.id}>
              <p className="metadata">
                {names[r.payload.type ?? "inbox"]} · {labels[r.state]}
              </p>
              <p className="entry-text">{r.payload.raw_text}</p>
              <div className="entry-actions">
                <button
                  disabled={r.state === "CONFLICT" || data.repair}
                  onClick={() => open(r)}
                >
                  Редагувати
                </button>
                <button disabled={data.repair} onClick={() => void remove(r)}>
                  Видалити
                </button>
              </div>
              {r.state === "CONFLICT" && (
                <section className="conflict">
                  <h3>Дві версії — потрібен ваш вибір</h3>
                  <p>На телефоні</p>
                  <p className="entry-text">{r.payload.raw_text}</p>
                  <p>
                    {r.current
                      ? "Поточна Mac версія"
                      : "Mac видалив цей ID; повернення під тим самим ID заборонене."}
                  </p>
                  {r.current && (
                    <p className="entry-text">{r.current.raw_text}</p>
                  )}
                  <label>
                    Об’єднаний текст
                    <textarea
                      value={merge[r.id] ?? r.payload.raw_text}
                      onChange={(e) =>
                        setMerge((m) => ({ ...m, [r.id]: e.target.value }))
                      }
                    />
                  </label>
                  <div className="actions">
                    {(["mac", "phone", "manual"] as const).map((choice) => (
                      <button
                        key={choice}
                        onClick={async () => {
                          try {
                            if (choice === "manual")
                              validatePayload({
                                ...r.payload,
                                raw_text: merge[r.id] ?? r.payload.raw_text,
                              });
                            setData(
                              await store.current.resolve(
                                r.id,
                                choice,
                                merge[r.id] ?? r.payload.raw_text,
                              ),
                            );
                            setNotice(
                              "Рішення збережено локально як нова mutation; потрібен sync.",
                            );
                          } catch (e) {
                            setError(errorText(e));
                          }
                        }}
                      >
                        {choice === "mac"
                          ? "Обрати Mac"
                          : choice === "phone"
                            ? r.current
                              ? "Обрати телефон"
                              : "Зберегти новою окремою нотаткою"
                            : "Зберегти об’єднаний текст"}
                      </button>
                    ))}
                  </div>
                </section>
              )}
            </article>
          ))}
          <details className="outbox">
            <summary>Черга: {pending.length} операцій</summary>
            {pending.map((o) => (
              <p key={o.operation_id}>
                {o.operation_type} · {labels[o.state]}
              </p>
            ))}
          </details>
          <footer>
            Phone-only data потребує encrypted recovery. Browser/OS storage
            best-effort; гарантованого background sync немає.
            <br />
            Реальні приватні записи ще не дозволені. Зовнішній AI, реальна
            ASR-модель, health і deploy вимкнено.
          </footer>
        </div>
      </main>
    </div>
  );
}
