import React, { useEffect, useRef, useState } from "react";
import type { components } from "./api-schema";
import { localDownload, m5Api, m5Error } from "./m5-ui";
type Input = components["schemas"]["FeedbackInput"];
type Saved = {
  id: string;
  version: number;
  payload: Input;
  exact_copy: unknown;
  content_hash: string;
  approved: boolean;
  markdown: string;
};
const blank = (): Input => ({
  title: "",
  type: "other",
  expected: "",
  actual: "",
  steps: "",
  description: "",
  visibility: "private",
  destination: "Локальний файл",
  attachments: [],
  references: [],
});
export function FeedbackPanel({ csrf }: { csrf: string }) {
  const [draft, setDraft] = useState<Input>(blank),
    [saved, setSaved] = useState<Saved | null>(null),
    [items, setItems] = useState<Saved[]>([]),
    [preview, setPreview] = useState(false),
    [checked, setChecked] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false);
  const listGeneration = useRef(0);
  const id = useRef<string>(crypto.randomUUID()),
    alive = useRef(true);
  useEffect(
    () => () => {
      alive.current = false;
    },
    [],
  );
  const dirty =
    !saved || JSON.stringify(draft) !== JSON.stringify(saved.payload);
  async function load() {
    const g = ++listGeneration.current;
    const r = await (await m5Api("feedback", csrf)).json();
    if (alive.current && g === listGeneration.current) setItems(r.items);
  }
  async function act(fn: () => Promise<void>) {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      if (alive.current) setError(m5Error(e));
    } finally {
      if (alive.current) setBusy(false);
    }
  }
  useEffect(() => {
    void load().catch((e) => setError(m5Error(e)));
  }, []);
  function choose(s: Saved | null) {
    id.current = s?.id ?? crypto.randomUUID();
    setSaved(s);
    setDraft(s?.payload ?? blank());
    setPreview(false);
    setChecked(false);
    setError("");
    setNotice("");
  }
  function change(k: keyof Input, v: string) {
    setDraft((old) => ({ ...old, [k]: v }));
    setPreview(false);
    setChecked(false);
  }
  async function save(e: React.FormEvent) {
    e.preventDefault();
    await act(async () => {
      const r: Saved = await (
        await m5Api("feedback", csrf, "POST", {
          draft_id: id.current,
          base_version: saved?.version ?? 0,
          payload: draft,
        })
      ).json();
      if (alive.current) {
        setSaved(r);
        setDraft(r.payload);
        setPreview(false);
        setChecked(false);
        setNotice(
          "Приватну чернетку збережено. Вона ще не погоджена для експорту.",
        );
        await load();
      }
    });
  }
  return (
    <section className="m5-surface" aria-label="Відгук про застосунок">
      <fieldset className="m5-action-surface" disabled={busy}>
        <header>
          <div>
            <h1>Відгук про застосунок</h1>
            <p>
              Окрема приватна чернетка. Ви визначаєте її точний вміст і
              отримувача.
            </p>
          </div>
          <button onClick={() => choose(null)}>Новий відгук</button>
        </header>
        <p className="hint">
          Щоденник, творчість, транскрипти й аудіо не додаються. У M5 вкладення
          та посилання на джерела відсутні. Уникайте приватних деталей, ключів і
          локальних шляхів.
        </p>
        <details>
          <summary>Збережені приватні чернетки</summary>
          <button onClick={() => void act(load)}>Оновити чернетки</button>
          {!items.length && <p>Ще немає чернеток.</p>}
          {items.map((s) => (
            <p key={s.id}>
              <button onClick={() => choose(s)}>
                {s.payload.title} · v{s.version} ·{" "}
                {s.approved ? "точно погоджено" : "приватна чернетка"}
              </button>
            </p>
          ))}
        </details>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {notice && (
          <p role="status" className="notice">
            {notice}
          </p>
        )}
        <form
          className="editor"
          aria-label="Приватна чернетка відгуку"
          onSubmit={save}
        >
          <label>
            Назва відгуку
            <input
              required
              maxLength={160}
              value={draft.title}
              onChange={(e) => change("title", e.target.value)}
            />
          </label>
          <label>
            Тип відгуку
            <select
              value={draft.type}
              onChange={(e) => change("type", e.target.value)}
            >
              <option value="bug">Помилка</option>
              <option value="feature">Можливість</option>
              <option value="design">Дизайн</option>
              <option value="other">Інше</option>
            </select>
          </label>
          {(
            [
              ["expected", "Очікуваний результат", 4000],
              ["actual", "Що незручно / фактичний результат", 4000],
              ["steps", "Кроки відтворення", 4000],
              ["description", "Опис відгуку", 12000],
            ] as const
          ).map(([k, label, max]) => (
            <label key={k}>
              {label}
              <textarea
                rows={k === "description" ? 5 : 2}
                maxLength={max}
                value={draft[k]}
                onChange={(e) => change(k, e.target.value)}
              />
            </label>
          ))}
          <div className="field-row">
            <label>
              Видимість відгуку
              <select
                value={draft.visibility}
                onChange={(e) => change("visibility", e.target.value)}
              >
                <option value="private">Приватно</option>
                <option value="intended_share">Для майбутньої передачі</option>
              </select>
            </label>
            <label>
              Запланований отримувач / призначення
              <input
                required
                maxLength={240}
                value={draft.destination}
                onChange={(e) => change("destination", e.target.value)}
              />
            </label>
          </div>
          <p>
            Фактичний напрямок експорту: лише локальний файл. Застосунок нічого
            не надсилає.
          </p>
          <button className="primary" disabled={busy}>
            {busy ? "Зберігаємо…" : "Зберегти приватну чернетку"}
          </button>
        </form>
        {saved && (
          <section className="m5-inset" aria-label="Точне погодження відгуку">
            <h2>Точний перегляд перед експортом</h2>
            <p>
              {dirty
                ? "Є незбережені зміни. Спочатку збережіть чернетку; попереднє погодження не використовується."
                : "Версія " +
                  saved.version +
                  " · " +
                  (saved.approved
                    ? "Погоджена точна копія"
                    : "Потребує погодження")}
            </p>
            <button
              disabled={dirty || busy}
              onClick={() => {
                setPreview(true);
                setChecked(false);
              }}
            >
              Показати точну копію відгуку
            </button>
            {preview && !dirty && (
              <div className="m5-preview">
                <pre tabIndex={0}>{saved.markdown}</pre>
                <details>
                  <summary>Версія та hash точного погодження</summary>
                  <p className="m5-wrap">
                    Draft ID: {saved.id}
                    <br />
                    Версія: {saved.version}
                    <br />
                    SHA-256: {saved.content_hash}
                  </p>
                  <pre>{JSON.stringify(saved.exact_copy, null, 2)}</pre>
                </details>
                <p>
                  Запланований отримувач: {saved.payload.destination} ·
                  Видимість: {saved.payload.visibility} · Вкладення: відсутні.
                </p>
                {!saved.approved && (
                  <>
                    <label className="check">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(e) => setChecked(e.target.checked)}
                      />
                      Погоджую саме показану копію v{saved.version}, цей
                      отримувач і видимість. Дозволяю лише локальний експорт.
                    </label>
                    <button
                      disabled={!checked || busy}
                      onClick={() =>
                        void act(async () => {
                          const r = await (
                            await m5Api(
                              "feedback/" + saved.id + "/approve",
                              csrf,
                              "POST",
                              {
                                version: saved.version,
                                content_hash: saved.content_hash,
                              },
                            )
                          ).json();
                          if (alive.current) {
                            setSaved(r);
                            setNotice(
                              "Точну копію погоджено. Публікацію не виконано.",
                            );
                            await load();
                          }
                        })
                      }
                    >
                      Погодити точну копію для локального експорту
                    </button>
                  </>
                )}
                {saved.approved && (
                  <div className="actions">
                    {(["markdown", "json"] as const).map((format) => (
                      <button
                        key={format}
                        disabled={busy}
                        onClick={() =>
                          void act(async () => {
                            const r = await m5Api(
                              "feedback/" + saved.id + "/export",
                              csrf,
                              "POST",
                              {
                                version: saved.version,
                                content_hash: saved.content_hash,
                                format,
                              },
                            );
                            localDownload(
                              await r.blob(),
                              "approved-feedback." +
                                (format === "markdown" ? "md" : "json"),
                            );
                            if (alive.current)
                              setNotice(
                                "Погоджений відгук збережено локально. Нічого не надіслано й не опубліковано.",
                              );
                          })
                        }
                      >
                        Зберегти відгук{" "}
                        {format === "markdown" ? "Markdown" : "JSON"}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
            <button
              className="m5-delete"
              disabled={busy}
              onClick={() => {
                if (confirm("Видалити цю чернетку та її погодження?"))
                  void act(async () => {
                    await m5Api(
                      "feedback/" + saved.id + "/delete",
                      csrf,
                      "POST",
                      {
                        version: saved.version,
                        content_hash: saved.content_hash,
                      },
                    );
                    choose(null);
                    await load();
                  });
              }}
            >
              Видалити чернетку відгуку
            </button>
          </section>
        )}
      </fieldset>
    </section>
  );
}
