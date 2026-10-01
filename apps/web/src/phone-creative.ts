/** Offline creative actions use the same encrypted M2 journal/outbox, with local CAS. */
import { PhoneStore, type LocalState, type RecordItem } from "./phone-store";
import {
  type CreativeAdapter,
  type CreativeItem,
  type ExportField,
  type ExportPreview,
} from "./m5-ui";
const hash = async (v: unknown) =>
  Array.from(
    new Uint8Array(
      await crypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(JSON.stringify(v)),
      ),
    ),
    (b) => b.toString(16).padStart(2, "0"),
  ).join("");
function view(r: RecordItem, s: LocalState): CreativeItem {
  const pending = s.outbox.filter(
    (o) => o.entry_id === r.id && o.state !== "MAC_CONFIRMED",
  );
  return {
    ...r.payload,
    id: r.id,
    owner_id: s.device_id,
    type: r.payload.type ?? "creative",
    tags: r.payload.tags ?? [],
    timezone: r.payload.timezone ?? "Europe/Warsaw",
    time_precision: r.payload.time_precision ?? "unknown",
    revision: r.revision + pending.length,
    created_at_utc: r.createdAt ?? null,
    updated_at_utc: r.updatedAt ?? null,
    schema_version: 2,
    privacy_class: "PRIVATE_PERSONAL",
    provenance_type: "USER_REPORTED",
    localFingerprint: JSON.stringify(r),
    blocked: s.repair || r.state === "CONFLICT" || r.deleted,
  };
}
function project(e: CreativeItem, fields: ExportField[]) {
  const m = e.creative_meta ?? { title: "", collections: [], related_ids: [] };
  const values = {
    raw_text: e.raw_text,
    title: m.title ?? "",
    creative_kind: e.creative_kind ?? null,
    tags: e.tags,
    collections: m.collections ?? [],
    related_ids: m.related_ids ?? [],
    timestamps: { created: e.created_at_utc, updated: e.updated_at_utc },
    provenance: {
      source: e.provenance_type,
      entry_id: e.id,
      revision: e.revision,
    },
  };
  return {
    id: e.id,
    revision: e.revision,
    ...Object.fromEntries(fields.map((k) => [k, values[k]])),
  };
}
export function creativeMarkdown(items: any[]) {
  const blocks = [
    "# Вибрана творчість",
    "Локальний файл · приватний авторський матеріал · пов’язані записи не включені.",
  ];
  for (const e of items) {
    blocks.push("## Вибраний запис " + e.id);
    for (const [k, v] of Object.entries(e)) {
      if (k === "id" || k === "revision") continue;
      const text = typeof v === "string" ? v : JSON.stringify(v),
        fence = "`".repeat(
          Math.max(2, ...Array.from(text.matchAll(/`+/g), (m) => m[0].length)) +
            1,
        );
      blocks.push(k + "\n\n" + fence + "text\n" + text + "\n" + fence);
    }
  }
  return blocks.join("\n\n") + "\n";
}
export function phoneCreativeAdapter(
  store: PhoneStore,
  onChanged: (s: LocalState) => void,
): CreativeAdapter {
  async function current() {
    return store.state();
  }
  return {
    list: async (q) => {
      const s = await current();
      const rows = Object.values(s.records)
        .filter(
          (r) =>
            !r.deleted &&
            r.payload.type === "creative" &&
            r.payload.creative_meta?.library &&
            Boolean(r.payload.creative_meta.archived) === q.archived &&
            (!q.kind || r.payload.creative_kind === q.kind) &&
            (!q.tag || r.payload.tags?.includes(q.tag)) &&
            (!q.collection ||
              r.payload.creative_meta.collections?.includes(q.collection)) &&
            (
              r.payload.raw_text + (r.payload.creative_meta.title ?? "")
            ).includes(q.q),
        )
        .sort((a, b) =>
          q.order === "newest"
            ? b.localOrder - a.localOrder
            : (b.updatedAt ?? "").localeCompare(a.updatedAt ?? "") ||
              b.localOrder - a.localOrder,
        );
      return {
        items: rows.slice(q.offset, q.offset + 50).map((r) => view(r, s)),
        next_offset: rows.length > q.offset + 50 ? q.offset + 50 : null,
      };
    },
    unlisted: async () => {
      const s = await current();
      return Object.values(s.records)
        .filter(
          (r) =>
            !r.deleted &&
            r.payload.type === "creative" &&
            !r.payload.creative_meta,
        )
        .map((r) => view(r, s));
    },
    save: async (e, p, mutation) => {
      const s = await current();
      for (const id of p.creative_meta?.related_ids ?? []) {
        if (id === e?.id) throw new Error("CREATIVE_SELF_LINK");
        if (!e?.creative_meta?.related_ids?.includes(id)) {
          const linked = s.records[id];
          if (!linked || linked.deleted || !linked.payload.creative_meta)
            throw new Error("CREATIVE_LINK_REQUIRED");
        }
      }
      onChanged(
        await store.capture(
          e ? "edit" : "create",
          e?.id ?? mutation?.entry_id ?? crypto.randomUUID(),
          p,
          false,
          e?.localFingerprint,
        ),
      );
    },
    remove: async (e) =>
      onChanged(
        await store.capture("delete", e.id, null, false, e.localFingerprint),
      ),
    preview: async (entries, fields) => {
      if (!entries.length || entries.length > 100 || !fields.length)
        throw new Error("SCHEMA_INVALID");
      const s = await current();
      const items = entries.map((e) => {
        const r = s.records[e.id];
        if (
          !r ||
          r.deleted ||
          r.state === "CONFLICT" ||
          JSON.stringify(r) !== e.localFingerprint
        )
          throw new Error("CREATIVE_SELECTION_CHANGED");
        return project(view(r, s), fields);
      });
      const content = {
        fields,
        items,
        include_related: false,
        destination: "local_file",
      };
      if (new TextEncoder().encode(JSON.stringify(content)).length > 2097152)
        throw new Error("CREATIVE_EXPORT_SIZE_LIMIT");
      return {
        plan_id: crypto.randomUUID(),
        content_hash: await hash(content),
        content,
        markdown: creativeMarkdown(items),
        warning:
          "Приватний авторський матеріал. Перевірте точний вміст. Це локальна копія телефона; Mac може ще не підтвердити sync.",
      };
    },
    download: async (p: ExportPreview, format) => {
      if ((await hash(p.content)) !== p.content_hash)
        throw new Error("EXPORT_CHANGED");
      const s = await current();
      const items = p.content.items.map((e) => {
        const r = s.records[e.id];
        if (
          !r ||
          r.deleted ||
          !r.payload.creative_meta ||
          r.state === "CONFLICT"
        )
          throw new Error("EXPORT_CHANGED");
        const current = view(r, s);
        if (current.revision !== e.revision) throw new Error("EXPORT_CHANGED");
        return project(current, p.content.fields);
      });
      const content = { ...p.content, items };
      if ((await hash(content)) !== p.content_hash)
        throw new Error("EXPORT_CHANGED");
      return new Blob(
        [
          format === "markdown"
            ? creativeMarkdown(items)
            : JSON.stringify(
                {
                  content,
                  content_hash: p.content_hash,
                  exported_at_utc: new Date().toISOString(),
                },
                null,
                2,
              ),
        ],
        { type: format === "markdown" ? "text/markdown" : "application/json" },
      );
    },
  };
}
