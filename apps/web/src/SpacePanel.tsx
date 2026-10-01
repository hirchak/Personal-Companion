import React, { useState } from "react";
import { m5Error } from "./m5-ui";
import type { Space, ObjectId } from "./space-model";
const labels: Record<ObjectId, string> = {
  books: "Книги",
  vase: "Ваза",
  print: "Геометричний принт",
};
export function SpacePanel({
  value,
  save,
}: {
  value: { version: number; state: Space };
  save: (base: number, state: Space) => Promise<void>;
}) {
  const [pending, setPending] = useState<Space | null>(null);
  const displayed = pending ?? value.state;
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function change(state: Space) {
    setPending(state);
    setBusy(true);
    setError("");
    try {
      await save(value.version, state);
    } catch (e) {
      setError(m5Error(e));
    } finally {
      setPending(null);
      setBusy(false);
    }
  }
  return (
    <section className="space-panel" aria-label="Особистий простір">
      <div className="space-toggle">
        <label className="check">
          <input
            type="checkbox"
            checked={displayed.enabled}
            disabled={busy}
            onChange={(e) =>
              void change({ ...displayed, enabled: e.target.checked })
            }
          />
          Особистий простір {displayed.enabled ? "ON" : "OFF"}
        </label>
        <p className="hint">
          Декорації лише на цьому пристрої. Усі функції доступні без них.
        </p>
      </div>
      {busy && <p role="status">Зберігаємо вигляд на цьому пристрої…</p>}
      {error && <p role="alert">{error}</p>}
      {displayed.enabled && (
        <details open>
          <summary>Моя маленька студія</summary>
          <div
            className={"studio studio-" + displayed.theme}
            role="img"
            aria-label="Оригінальна геометрична полиця з книгами, вазою та принтом"
          >
            <div className="studio-shelf">
              {displayed.layout.map((id) => (
                <div
                  key={id}
                  className={"studio-object object-" + id}
                  aria-hidden="true"
                >
                  {id === "print" && (
                    <svg viewBox="0 0 80 80">
                      <circle cx="25" cy="26" r="13" />
                      <path d="M15 65 L65 65 L45 32 Z" />
                    </svg>
                  )}
                  {id === "books" && (
                    <>
                      <i />
                      <i />
                      <i />
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>
          <div className="field-row">
            <label>
              Колір студії
              <select
                disabled={busy}
                value={displayed.theme}
                onChange={(e) =>
                  void change({
                    ...displayed,
                    theme: e.target.value as Space["theme"],
                  })
                }
              >
                <option value="paper">Теплий папір</option>
                <option value="sage">Шавлія</option>
                <option value="clay">Глина</option>
              </select>
            </label>
            <label>
              Об’єкт ліворуч
              <select
                disabled={busy}
                value={displayed.layout[0]}
                onChange={(e) => {
                  const id = e.target.value as ObjectId;
                  void change({
                    ...displayed,
                    layout: [id, ...displayed.layout.filter((x) => x !== id)],
                  });
                }}
              >
                {Object.entries(labels).map(([id, label]) => (
                  <option key={id} value={id}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <p className="hint">
            Усі декорації доступні відразу. Тут немає балів, серій чи нагадувань
            про відсутність. Вимкнення збереже обраний вигляд.
          </p>
        </details>
      )}
    </section>
  );
}
