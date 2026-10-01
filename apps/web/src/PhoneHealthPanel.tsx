import React, { useEffect, useRef, useState } from "react";
import {
  healthLabel,
  healthNames,
  type HealthStatus,
  type HealthType,
} from "./health-model";
export function PhoneHealthPanel({
  status,
  online,
}: {
  status: () => Promise<HealthStatus>;
  online: boolean;
}) {
  const [data, setData] = useState<HealthStatus | null>(null),
    [error, setError] = useState("");
  const alive = useRef(true),
    requestGeneration = useRef(0);
  async function refresh() {
    const current = ++requestGeneration.current;
    setError("");
    try {
      const s = await status();
      if (alive.current && current === requestGeneration.current) setData(s);
    } catch {
      if (alive.current && current === requestGeneration.current) {
        setData(null);
        setError(
          "Локальна копія на Mac недоступна. Щоденник на телефоні працює далі.",
        );
      }
    }
  }
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      requestGeneration.current++;
    };
  }, []);
  useEffect(() => {
    requestGeneration.current++;
    if (!online) setData(null);
  }, [online]);
  return (
    <section
      className="m5-surface health-panel"
      aria-labelledby="phone-health-title"
    >
      <h1 id="phone-health-title">Дані з Health Connect</h1>
      <p>
        PWA сама не читає Health Connect. Відкрийте Personal Companion Health на
        Galaxy для ручного читання Сну, Кроків та Активностей і локального USB
        handoff на Mac.
      </p>
      <p>
        Без запису в Health Connect, геолокації, фонового читання чи AI.
        Імпортовані копії відділені від записаного вами.
      </p>
      <button
        disabled={!online}
        onClick={() => {
          void refresh();
        }}
      >
        Перевірити стан копії на Mac
      </button>
      {!online && (
        <p role="status">
          Офлайн: стан джерела невідомий. Це не означає відсутність записів.
        </p>
      )}
      {error && <p role="status">{error}</p>}
      {data && (
        <>
          <p>{healthLabel(data.connection)}</p>
          <dl className="health-status">
            {(Object.keys(healthNames) as HealthType[]).map((k) => (
              <div key={k}>
                <dt>{healthNames[k]}</dt>
                <dd>
                  {healthLabel(data.permissions[k])} ·{" "}
                  {healthLabel(data.availability[k])}
                </dd>
              </div>
            ))}
          </dl>
          <p>
            Останній імпорт:{" "}
            {data.last_import
              ? new Date(data.last_import).toLocaleString("uk-UA")
              : "Ще не було"}
          </p>
        </>
      )}
      <details>
        <summary>Дозволи й видалення</summary>
        <p>
          Відкликати читання: Health Connect → Дозволи додатків → Personal
          Companion Health. Для видалення імпортованої копії на Mac відкрийте
          «Дані з годинника» → «Видалити імпортовану копію». Оригінали Health
          Connect і власні нотатки залишаться.
        </p>
      </details>
    </section>
  );
}
