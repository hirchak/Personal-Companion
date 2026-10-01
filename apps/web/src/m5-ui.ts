import type { components } from "./api-schema";
export type CreativeMeta = components["schemas"]["CreativeMetadata"];
export type CreativeItem = Omit<
  components["schemas"]["EntryOutput"],
  "created_at_utc" | "updated_at_utc"
> & { created_at_utc: string | null; updated_at_utc: string | null } & {
  localFingerprint?: string;
  blocked?: boolean;
};
export type CreativeQuery = {
  q: string;
  kind: string;
  tag: string;
  collection: string;
  archived: boolean;
  order: string;
  offset: number;
};
export type ExportField =
  | "raw_text"
  | "title"
  | "creative_kind"
  | "tags"
  | "collections"
  | "related_ids"
  | "timestamps"
  | "provenance";
export type ExportPreview = {
  plan_id: string;
  content_hash: string;
  content: {
    fields: ExportField[];
    items: any[];
    include_related: boolean;
    destination: string;
  };
  markdown: string;
  warning: string;
};
export type CreativeAdapter = {
  list: (
    q: CreativeQuery,
  ) => Promise<{ items: CreativeItem[]; next_offset: number | null }>;
  unlisted: () => Promise<CreativeItem[]>;
  save: (
    entry: CreativeItem | null,
    payload: components["schemas"]["EntryInput"],
    mutation?: { operation_id: string; entry_id: string },
  ) => Promise<void>;
  remove: (entry: CreativeItem) => Promise<void>;
  preview: (
    items: CreativeItem[],
    fields: ExportField[],
  ) => Promise<ExportPreview>;
  download: (p: ExportPreview, format: "markdown" | "json") => Promise<Blob>;
};
export async function m5Api(
  path: string,
  csrf: string,
  method = "GET",
  body?: unknown,
) {
  const r = await fetch("/api/v1/" + path, {
    method,
    credentials: "same-origin",
    cache: "no-store",
    headers: {
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(csrf ? { "X-CSRF-Token": csrf } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!r.ok) {
    if (r.status === 401 && typeof window !== "undefined")
      window.dispatchEvent(new Event("m5-vault-locked"));
    const b = await r.json();
    throw new Error(b.code ?? "M5_REQUEST_FAILED");
  }
  return r;
}
export function localDownload(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob),
    a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function m5Error(e: unknown) {
  const code = e instanceof Error ? e.message : "";
  if (
    code.includes("CHANGED") ||
    code.includes("STALE") ||
    code.includes("CONFLICT")
  )
    return "Версія змінилася. Оновіть список і перевірте зміни; чернетку залишено тут.";
  if (code.includes("DELETED") || code === "NOT_FOUND")
    return "Запис уже видалений або недоступний. Оновіть список.";
  if (code === "CREATIVE_EXPORT_SIZE_LIMIT")
    return "Вибірка завелика. Оберіть менше ідей або полів і перегляньте її знову.";
  if (
    code.includes("SCHEMA") ||
    code.includes("LINK") ||
    code.includes("QUERY")
  )
    return "Перевірте поля, кількість тегів, колекцій та доступність пов’язаних ідей.";
  if (code === "FEEDBACK_APPROVAL_REQUIRED")
    return "Потрібен новий точний перегляд і погодження цієї версії.";
  return "Не вдалося завершити дію. Чернетку збережено у відкритій вкладці; оновіть список або повторіть.";
}
export function macCreativeAdapter(
  csrf: string,
  onChanged: () => void,
): CreativeAdapter {
  const json = async (path: string, method = "GET", body?: unknown) =>
    (await m5Api(path, csrf, method, body)).json();
  return {
    list: (q) => {
      const p = new URLSearchParams({
        q: q.q,
        archived: String(q.archived),
        order: q.order,
        offset: String(q.offset),
      });
      for (const k of ["kind", "tag", "collection"] as const)
        if (q[k]) p.set(k, q[k]);
      return json("creative?" + p);
    },
    unlisted: async () => {
      let cursor: string | null = null,
        items: CreativeItem[] = [];
      do {
        const p: { items: CreativeItem[]; next_cursor: string | null } =
          await json(
            "entries?type=creative&limit=100" +
              (cursor ? "&cursor=" + encodeURIComponent(cursor) : ""),
          );
        items.push(...p.items.filter((e) => !e.creative_meta));
        cursor = p.next_cursor;
      } while (cursor && items.length < 1000);
      return items;
    },
    save: async (e, p, mutation) => {
      await json(
        e ? "entries/" + e.id : "entries",
        e ? "PATCH" : "POST",
        e
          ? {
              operation_id: mutation?.operation_id ?? crypto.randomUUID(),
              base_revision: e.revision,
              changes: p,
            }
          : {
              operation_id: mutation?.operation_id ?? crypto.randomUUID(),
              entry_id: mutation?.entry_id ?? crypto.randomUUID(),
              base_revision: 0,
              payload: p,
            },
      );
      onChanged();
    },
    remove: async (e) => {
      await json("entries/" + e.id, "DELETE", {
        operation_id: crypto.randomUUID(),
        base_revision: e.revision,
      });
      onChanged();
    },
    preview: (items, fields) =>
      json("creative/preview", "POST", {
        entries: items.map((e) => ({ id: e.id, revision: e.revision })),
        fields,
        include_related: false,
      }),
    download: async (p, format) =>
      (
        await m5Api("creative/export", csrf, "POST", {
          plan_id: p.plan_id,
          content_hash: p.content_hash,
          format,
        })
      ).blob(),
  };
}
