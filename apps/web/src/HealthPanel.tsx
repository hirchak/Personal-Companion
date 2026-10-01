import React, { useEffect, useRef, useState } from "react";
import {
  healthNames,
  healthLabel,
  readHealthFile,
  type HealthStatus,
  type HealthType,
} from "./health-model";
export function HealthPanel({ csrf }: { csrf: string }) {
  const [state, setState] = useState<HealthStatus | null>(null);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [selected, setSelected] = useState<File | null>(null),
    [reconnect, setReconnect] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const alive = useRef(true),
    generation = useRef(0),
    fileInput = useRef<HTMLInputElement>(null);
  const [records, setRecords] = useState<
    Array<{
      local_id: string;
      type: HealthType;
      status: string;
      start?: string;
      end?: string;
      fields?: {
        count?: number;
        exercise_type?: number;
        stages_state?: string;
      };
    }>
  >([]);
  async function request(path: string, body?: unknown) {
    const r = await fetch("/api/v1/health/" + path, {
      credentials: "same-origin",
      cache: "no-store",
      method: body === undefined ? "GET" : "POST",
      headers:
        body === undefined
          ? {}
          : { "Content-Type": "application/json", "X-CSRF-Token": csrf },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!r.ok) throw new Error("HEALTH_OPERATION_FAILED");
    return r.json();
  }
  async function refresh() {
    const current = generation.current;
    const result = await request("status");
    if (alive.current && current === generation.current) setState(result);
  }
  useEffect(() => {
    alive.current = true;
    void refresh().catch(() => {
      if (alive.current)
        setError("Не вдалося перевірити локальну копію. Спробуйте ще раз.");
    });
    return () => {
      alive.current = false;
      generation.current++;
    };
  }, [csrf]);
  async function mutate(action: "import" | "delete" | "disconnect") {
    if (!state || busy) return;
    setBusy(true);
    setError("");
    setNotice("");
    const current = ++generation.current;
    try {
      const batch =
        action === "import" && selected ? await readHealthFile(selected) : null;
      if (action === "import" && !batch) throw new Error("FILE_REQUIRED");
      const result = await request(
        action,
        action === "import"
          ? { batch, generation: state.generation, reconnect }
          : { generation: state.generation },
      );
      if (!alive.current || current !== generation.current) return;
      setState(result.status ?? result);
      setRecords([]);
      setConfirmDelete(false);
      setSelected(null);
      if (fileInput.current) fileInput.current.value = "";
      setNotice(
        action === "import"
          ? "Локальну копію імпортовано. Ваші записи не змінено."
          : action === "delete"
            ? "Імпортовану копію видалено. Оригінали Health Connect і ваш щоденник збережено."
            : "Передавання від’єднано. Імпортовані копії збережено.",
      );
    } catch {
      if (alive.current && current === generation.current)
        setError(
          "Операцію не завершено. Перевірте файл і актуальний стан; нічого не надіслано в AI.",
        );
    } finally {
      if (alive.current && current === generation.current) setBusy(false);
    }
  }
  return (
    <section
      className="m5-surface health-panel"
      aria-labelledby="health-title"
      aria-busy={busy}
    >
      <header>
        <div>
          <h1 id="health-title">Дані з Health Connect</h1>
          <p>
            Імпортовано з Health Connect · окремо від того, що записано вами.
          </p>
        </div>
      </header>
      <p>
        Це оцінки пристрою, без клінічних висновків. Лише читання сну, кроків та
        активностей. Без геолокації, фонового читання й розширеної історії. Дані
        залишаються локально, AI їх не отримує.
      </p>
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      {state && (
        <>
          <p className="sync-note">{healthLabel(state.connection)}</p>
          <dl className="health-status">
            {(Object.keys(healthNames) as HealthType[]).map((type) => (
              <div key={type}>
                <dt>{healthNames[type]}</dt>
                <dd>
                  {healthLabel(state.permissions[type])} ·{" "}
                  {healthLabel(state.availability[type])}
                </dd>
              </div>
            ))}
          </dl>
          <p>
            Останній імпорт:{" "}
            {state.last_import
              ? new Date(state.last_import).toLocaleString("uk-UA")
              : "Ще не було"}
          </p>
        </>
      )}
      <p>
        Кроки з різних джерел зберігаються окремо. Загальну суму не обчислюємо
        без підтвердженого правила перекриття.
      </p>
      <details>
        <summary>Як підключити телефон</summary>
        <p>
          Відкрийте Personal Companion Health на Galaxy, особисто дозвольте лише
          Сон, Кроки та Активності й натисніть «Перевірити доступ /
          імпортувати». USB handoff виконується локально за інструкцією bridge.
          PWA сама не читає Health Connect.
        </p>
        <p>
          Відкликати доступ: Health Connect → Дозволи додатків → Personal
          Companion Health. Нове читання припиниться; локальна копія залишиться
          до вашого видалення.
        </p>
      </details>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void mutate("import");
        }}
      >
        <label>
          Локальний файл передавання
          <input
            ref={fileInput}
            type="file"
            accept="application/json,.json"
            disabled={busy}
            onChange={(e) => setSelected(e.target.files?.[0] ?? null)}
          />
        </label>
        <p>
          Файл може містити приватні дані здоров’я. Вибирайте лише файл
          локального передавання; не публікуйте його й не надсилайте в AI.
        </p>
        <label className="check">
          <input
            type="checkbox"
            checked={reconnect}
            disabled={busy}
            onChange={(e) => setReconnect(e.target.checked)}
          />
          Явно підключити джерело / повторно імпортувати після видалення копії
        </label>
        <button className="primary" disabled={busy || !state || !selected}>
          Імпортувати локальну копію
        </button>
      </form>
      <div className="button-row">
        <button
          disabled={busy}
          onClick={() => {
            void refresh().catch(() => setError("Не вдалося оновити стан."));
          }}
        >
          Оновити стан
        </button>
        <button
          disabled={busy || !state}
          onClick={() => {
            void mutate("disconnect");
          }}
        >
          Від’єднати передавання
        </button>
        <button
          disabled={busy || !state}
          onClick={() => setConfirmDelete(true)}
        >
          Видалити імпортовану копію
        </button>
      </div>
      {confirmDelete && (
        <div role="group" aria-label="Підтвердження видалення health копії">
          <p>
            Видалити лише локальні імпортовані дані? Оригінали Health Connect /
            Samsung Health та власні нотатки залишаться. Повторний імпорт
            потребуватиме явної дії.
          </p>
          <button
            disabled={busy}
            onClick={() => {
              void mutate("delete");
            }}
          >
            Так, видалити лише копію
          </button>
          <button disabled={busy} onClick={() => setConfirmDelete(false)}>
            Скасувати
          </button>
        </div>
      )}
      <details
        onToggle={(e) => {
          if (e.currentTarget.open) {
            const current = generation.current;
            void request("records")
              .then((r) => {
                if (alive.current && current === generation.current)
                  setRecords(r.items);
              })
              .catch(() => {
                if (alive.current)
                  setError("Не вдалося відкрити імпортовану копію.");
              });
          }
        }}
      >
        <summary>Переглянути окремі імпортовані записи</summary>
        <p>
          Без зміни вашої власної оцінки. Невідомий код типу зберігається як код
          джерела.
        </p>
        <ul>
          {records.map((r) => (
            <li key={r.local_id}>
              <strong>{healthNames[r.type]}</strong> · {healthLabel(r.status)}
              {r.status === "VALUE" && (
                <>
                  <p>
                    {r.start} — {r.end}
                  </p>
                  {r.type === "steps" ? (
                    <p>{r.fields?.count} кроків · окремий запис джерела</p>
                  ) : r.type === "exercise" ? (
                    <p>Код джерела: {r.fields?.exercise_type}</p>
                  ) : (
                    <p>
                      Стадії: {healthLabel(r.fields?.stages_state ?? "UNKNOWN")}
                    </p>
                  )}
                </>
              )}
            </li>
          ))}
        </ul>
      </details>
    </section>
  );
}
