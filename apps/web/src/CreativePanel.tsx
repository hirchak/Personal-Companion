import React, { useEffect, useRef, useState } from "react";
import { creativeNames } from "./journal-ui";
import {
  localDownload,
  m5Error,
  type CreativeAdapter,
  type CreativeItem,
  type CreativeQuery,
  type ExportField,
  type ExportPreview,
} from "./m5-ui";
import { fromMac, type Payload } from "./phone-store";
const fields: Record<ExportField, string> = {
  raw_text: "Оригінальний текст",
  title: "Назва",
  creative_kind: "Вид ідеї",
  tags: "Теги",
  collections: "Колекції",
  related_ids: "IDs зв’язків (без тексту)",
  timestamps: "Дати",
  provenance: "Походження",
};
const emptyQuery = (): CreativeQuery => ({
  q: "",
  kind: "",
  tag: "",
  collection: "",
  archived: false,
  order: "recent",
  offset: 0,
});
export function CreativePanel({
  adapter,
  onSelection,
  phone = false,
}: {
  adapter: CreativeAdapter;
  onSelection?: (s: Set<string>) => void;
  phone?: boolean;
}) {
  const [query, setQuery] = useState(emptyQuery),
    [items, setItems] = useState<CreativeItem[]>([]),
    [next, setNext] = useState<number | null>(null),
    [sources, setSources] = useState<CreativeItem[]>([]),
    [promoting, setPromoting] = useState(false);
  const [editing, setEditing] = useState<CreativeItem | "new" | null>(null),
    [text, setText] = useState(""),
    [title, setTitle] = useState(""),
    [kind, setKind] = useState("idea"),
    [tags, setTags] = useState(""),
    [collections, setCollections] = useState(""),
    [related, setRelated] = useState<string[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set()),
    [included, setIncluded] = useState<ExportField[]>([
      "raw_text",
      "title",
      "creative_kind",
    ]),
    [plan, setPlan] = useState<ExportPreview | null>(null),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true);
  const mutation = useRef<{
    entry_id: string;
    operation_id: string;
    fingerprint: string;
  } | null>(null);
  const requestGeneration = useRef(0),
    alive = useRef(true);
  useEffect(
    () => () => {
      alive.current = false;
      requestGeneration.current++;
    },
    [],
  );
  async function load(more = false) {
    const generation = ++requestGeneration.current;
    setLoading(true);
    try {
      const page = await adapter.list({
        ...query,
        offset: more ? (next ?? 0) : 0,
      });
      if (generation !== requestGeneration.current || !alive.current) return;
      setItems((old) => (more ? [...old, ...page.items] : page.items));
      setNext(page.next_offset);
      if (!more) {
        setSelected(new Set());
        onSelection?.(new Set());
        setPlan(null);
      }
    } catch (e) {
      if (alive.current) setError(m5Error(e));
    } finally {
      if (generation === requestGeneration.current) setLoading(false);
    }
  }
  useEffect(() => {
    const timer = setTimeout(() => void load(), 150);
    return () => clearTimeout(timer);
  }, [
    query.q,
    query.kind,
    query.tag,
    query.collection,
    query.archived,
    query.order,
  ]);
  async function action(fn: () => Promise<void>) {
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
  function edit(e: CreativeItem | "new") {
    mutation.current = {
      entry_id: e === "new" ? crypto.randomUUID() : e.id,
      operation_id: crypto.randomUUID(),
      fingerprint: "",
    };
    setEditing(e);
    setPlan(null);
    setNotice("");
    setText(e === "new" ? "" : e.raw_text);
    setTitle(e === "new" ? "" : (e.creative_meta?.title ?? ""));
    setKind(e === "new" ? "idea" : (e.creative_kind ?? "idea"));
    setTags(e === "new" ? "" : (e.tags?.join(", ") ?? ""));
    setCollections(
      e === "new" ? "" : (e.creative_meta?.collections?.join(", ") ?? ""),
    );
    setRelated(e === "new" ? [] : (e.creative_meta?.related_ids ?? []));
  }
  const parts = (s: string) =>
    s.trim() ? s.split(",").map((x) => x.trim()) : [];
  async function save(ev: React.FormEvent) {
    ev.preventDefault();
    await action(async () => {
      const e = editing === "new" ? null : editing;
      if (!e && editing !== "new") return;
      const p: Payload = {
        ...(e
          ? fromMac(e)
          : { timezone: "Europe/Warsaw", time_precision: "unknown" as const }),
        type: "creative",
        raw_text: text,
        creative_kind: kind as Payload["creative_kind"],
        tags: parts(tags),
        creative_meta: {
          library: true,
          title,
          collections: parts(collections),
          related_ids: related,
          archived: e?.creative_meta?.archived ?? false,
        },
      };
      const fingerprint = JSON.stringify({
        id: e?.id,
        revision: e?.revision,
        payload: p,
      });
      if (!mutation.current)
        mutation.current = {
          entry_id: e?.id ?? crypto.randomUUID(),
          operation_id: crypto.randomUUID(),
          fingerprint,
        };
      else if (mutation.current.fingerprint !== fingerprint)
        mutation.current = {
          ...mutation.current,
          operation_id: crypto.randomUUID(),
          fingerprint,
        };
      await adapter.save(e, p, mutation.current);
      if (alive.current) {
        setEditing(null);
        setNotice(
          phone
            ? "Ідею збережено на телефоні. Mac підтвердить її після sync."
            : "Ідею збережено на Mac.",
        );
        await load();
      }
    });
  }
  async function metadata(e: CreativeItem, remove = false) {
    await action(async () => {
      await adapter.save(e, {
        ...fromMac(e),
        creative_meta: remove
          ? null
          : {
              title: e.creative_meta?.title ?? "",
              collections: e.creative_meta?.collections ?? [],
              related_ids: e.creative_meta?.related_ids ?? [],
              library: true,
              archived: !e.creative_meta?.archived,
            },
      });
      if (alive.current) {
        setNotice(
          remove
            ? "Прибрано з полиці. Оригінал залишається у щоденнику."
            : "Стан архіву змінено.",
        );
        await load();
      }
    });
  }
  return (
    <section className="m5-surface" aria-label="Творча полиця">
      <fieldset className="m5-action-surface" disabled={busy}>
        <header>
          <div>
            <h1>Творча полиця</h1>
            <p>
              Зберіть сцени, фрази й задуми. Оригінал завжди залишається вашим.
            </p>
          </div>
          <button className="primary" onClick={() => edit("new")}>
            Нова творча ідея
          </button>
        </header>
        <div className="actions">
          <button
            onClick={() =>
              void action(async () => {
                setSources(await adapter.unlisted());
                setPromoting(true);
              })
            }
          >
            Додати зі щоденника
          </button>
          <button onClick={() => void load()}>Оновити полицю</button>
        </div>
        {promoting && (
          <section className="m5-inset">
            <h2>Творчі записи поза полицею</h2>
            <p>Додавання змінить лише організацію того самого оригіналу.</p>
            {!sources.length && <p>Немає записів для додавання.</p>}
            {sources.map((e) => (
              <article className="entry" key={e.id}>
                <p className="entry-text">{e.raw_text}</p>
                <button
                  disabled={busy || e.blocked}
                  onClick={() =>
                    void action(async () => {
                      await adapter.save(e, {
                        ...fromMac(e),
                        creative_meta: {
                          library: true,
                          title: "",
                          collections: [],
                          related_ids: [],
                          archived: false,
                        },
                      });
                      setSources((old) => old.filter((x) => x.id !== e.id));
                      await load();
                    })
                  }
                >
                  На творчу полицю
                </button>
              </article>
            ))}
            <button onClick={() => setPromoting(false)}>
              Закрити список щоденника
            </button>
          </section>
        )}
        <div className="m5-filters">
          <label>
            Пошук творчих ідей
            <input
              type="search"
              maxLength={200}
              value={query.q}
              onChange={(e) => setQuery({ ...query, q: e.target.value })}
            />
          </label>
          <label>
            Вид творчості
            <select
              value={query.kind}
              onChange={(e) => setQuery({ ...query, kind: e.target.value })}
            >
              <option value="">Усі види</option>
              {Object.entries(creativeNames).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
          </label>
          <label>
            Тег полиці
            <input
              maxLength={64}
              value={query.tag}
              onChange={(e) => setQuery({ ...query, tag: e.target.value })}
            />
          </label>
          <label>
            Колекція
            <input
              maxLength={64}
              value={query.collection}
              onChange={(e) =>
                setQuery({ ...query, collection: e.target.value })
              }
            />
          </label>
          <label>
            Стан полиці
            <select
              value={query.archived ? "archived" : "current"}
              onChange={(e) =>
                setQuery({ ...query, archived: e.target.value === "archived" })
              }
            >
              <option value="current">Поточні</option>
              <option value="archived">Архів</option>
            </select>
          </label>
          <label>
            Порядок
            <select
              value={query.order}
              onChange={(e) => setQuery({ ...query, order: e.target.value })}
            >
              <option value="recent">Нещодавно змінені</option>
              <option value="newest">Нові спочатку</option>
            </select>
          </label>
        </div>
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
        {editing && (
          <form
            className="editor"
            aria-label="Редактор творчої ідеї"
            onSubmit={save}
          >
            <h2>
              {editing === "new"
                ? "Нова ідея"
                : "Редагувати оригінал та організацію"}
            </h2>
            <label>
              Назва ідеї
              <input
                autoFocus
                maxLength={160}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </label>
            <label>
              Оригінальний творчий текст
              <textarea
                required
                maxLength={100000}
                rows={6}
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
            </label>
            <label>
              Вид ідеї
              <select
                aria-label="Вид ідеї"
                value={kind}
                onChange={(e) => setKind(e.target.value)}
              >
                {Object.entries(creativeNames).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </label>
            <details open>
              <summary>Організація ідеї</summary>
              <label>
                Теги ідеї через кому
                <input value={tags} onChange={(e) => setTags(e.target.value)} />
              </label>
              <label>
                Колекції через кому
                <input
                  value={collections}
                  onChange={(e) => setCollections(e.target.value)}
                />
              </label>
              <p className="hint">
                До 20 тегів і 8 колекцій, до 64 символів у назві. Щоб прибрати з
                колекції, видаліть її назву.
              </p>
              <label>
                Пов’язані ідеї (до 8)
                <select
                  multiple
                  value={related}
                  onChange={(e) =>
                    setRelated(
                      Array.from(e.target.selectedOptions, (x) => x.value),
                    )
                  }
                >
                  {items
                    .filter((e) => editing === "new" || e.id !== editing.id)
                    .map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.creative_meta?.title || e.raw_text.slice(0, 60)}
                      </option>
                    ))}
                  {related
                    .filter((id) => !items.some((e) => e.id === id))
                    .map((id) => (
                      <option key={id} value={id}>
                        Поза цим списком або недоступна · {id}
                      </option>
                    ))}
                </select>
              </label>
            </details>
            <div className="actions">
              <button className="primary" disabled={busy}>
                {busy ? "Зберігаємо…" : "Зберегти творчу ідею"}
              </button>
              <button type="button" onClick={() => setEditing(null)}>
                Скасувати редагування ідеї
              </button>
            </div>
          </form>
        )}
        {loading && <p role="status">Завантажуємо ідеї…</p>}
        {!loading && !items.length && (
          <p className="m5-empty">
            Тут буде місце для ваших задумів. Запишіть ідею або додайте творчу
            нотатку зі щоденника.
          </p>
        )}
        {items.map((e) => (
          <article className="entry creative-item" key={e.id}>
            <div className="creative-heading">
              <label className="check">
                <input
                  type="checkbox"
                  aria-label={"Обрати ідею " + (e.creative_meta?.title || e.id)}
                  checked={selected.has(e.id)}
                  onChange={(ev) => {
                    const s = new Set(selected);
                    if (ev.target.checked) s.add(e.id);
                    else s.delete(e.id);
                    setSelected(s);
                    onSelection?.(s);
                    setPlan(null);
                  }}
                />
                Обрати
              </label>
              <p className="metadata">
                {creativeNames[e.creative_kind ?? "idea"]} ·{" "}
                {e.provenance_type === "USER_REPORTED"
                  ? "Ваш оригінал"
                  : "Оригінал"}{" "}
                · {phone ? "На телефоні" : "На Mac"}
              </p>
            </div>
            {e.creative_meta?.title && <h2>{e.creative_meta.title}</h2>}
            <p className="entry-text">{e.raw_text}</p>
            <p className="m5-wrap">
              {e.tags?.map((t) => "#" + t).join(" · ")}
              {(e.creative_meta?.collections ?? []).length > 0 &&
                " · Колекції: " + e.creative_meta?.collections?.join(", ")}
            </p>
            {!!e.creative_meta?.related_ids?.length && (
              <details>
                <summary>Пов’язані ідеї</summary>
                {e.creative_meta.related_ids.map((id) => {
                  const linked = items.find((x) => x.id === id);
                  return (
                    <p key={id}>
                      {linked ? (
                        <button onClick={() => edit(linked)}>
                          {linked.creative_meta?.title ||
                            linked.raw_text.slice(0, 60)}
                        </button>
                      ) : (
                        "Ідея поза цим списком або недоступна; оригінал не змінено."
                      )}
                    </p>
                  );
                })}
              </details>
            )}
            <div className="entry-actions">
              <button disabled={e.blocked || busy} onClick={() => edit(e)}>
                Редагувати ідею
              </button>
              <button
                disabled={e.blocked || busy}
                onClick={() => void metadata(e)}
              >
                {e.creative_meta?.archived
                  ? "Повернути з архіву"
                  : "Архівувати ідею"}
              </button>
              <button
                disabled={e.blocked || busy}
                onClick={() => void metadata(e, true)}
              >
                Прибрати з полиці
              </button>
              <button
                disabled={e.blocked || busy}
                onClick={() => {
                  if (
                    confirm(
                      "Видалити сам оригінал і його історію? Це також прибере ідею зі щоденника.",
                    )
                  )
                    void action(async () => {
                      await adapter.remove(e);
                      await load();
                    });
                }}
              >
                Видалити оригінал
              </button>
            </div>
            {e.blocked && (
              <p>
                Є конфлікт або потрібне узгодження. Перейдіть у щоденник для
                вибору версії.
              </p>
            )}
          </article>
        ))}
        {next !== null && (
          <button disabled={loading} onClick={() => void load(true)}>
            Ще ідеї
          </button>
        )}
        {selected.size > 0 && (
          <section className="m5-inset" aria-label="Вибраний творчий експорт">
            <h2>Експорт {selected.size} вибраних ідей</h2>
            <p>Місце: локальний файл. Пов’язані записи не додаються.</p>
            <div className="m5-fields">
              {Object.entries(fields).map(([k, v]) => (
                <label className="check" key={k}>
                  <input
                    type="checkbox"
                    checked={included.includes(k as ExportField)}
                    onChange={(e) => {
                      setIncluded((old) =>
                        e.target.checked
                          ? [...old, k as ExportField]
                          : old.filter((x) => x !== k),
                      );
                      setPlan(null);
                    }}
                  />
                  {v}
                </label>
              ))}
            </div>
            <button
              disabled={busy || !included.length || selected.size > 100}
              onClick={() =>
                void action(async () =>
                  setPlan(
                    await adapter.preview(
                      items.filter((e) => selected.has(e.id)),
                      included,
                    ),
                  ),
                )
              }
            >
              Точний перегляд творчого експорту
            </button>
            {plan && (
              <div className="m5-preview">
                <p>{plan.warning}</p>
                <p>
                  Поля: {plan.content.fields.map((k) => fields[k]).join(", ")} ·
                  Вибрано: {plan.content.items.length}
                </p>
                <pre tabIndex={0}>{plan.markdown}</pre>
                <div className="actions">
                  {(["markdown", "json"] as const).map((format) => (
                    <button
                      key={format}
                      disabled={busy}
                      onClick={() =>
                        void action(async () => {
                          localDownload(
                            await adapter.download(plan, format),
                            "selected-creative." +
                              (format === "markdown" ? "md" : "json"),
                          );
                          setNotice(
                            "Локальний файл створено. Нічого не опубліковано.",
                          );
                        })
                      }
                    >
                      Зберегти творчість{" "}
                      {format === "markdown" ? "Markdown" : "JSON"}
                    </button>
                  ))}
                  <button onClick={() => setPlan(null)}>
                    Скасувати творчий експорт
                  </button>
                </div>
              </div>
            )}
          </section>
        )}
      </fieldset>
    </section>
  );
}
