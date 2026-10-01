import validateSchema from "./entry-schema-validator.js";
import type { Payload } from "./phone-store";
import { typed, type Kind, type Draft } from "./journal-ui";
export function validatePayload(p: Payload) {
  if (!validateSchema(p)) throw new Error("SCHEMA_INVALID");
  const type = p.type ?? "inbox";
  if (!(type in typed)) throw new Error("SCHEMA_INVALID");
  if (type !== "creative" && "creative_meta" in p)
    throw new Error("SCHEMA_INVALID");
  if (p.creative_meta) {
    const m = p.creative_meta;
    if (
      new Set(m.collections ?? []).size !== (m.collections ?? []).length ||
      (m.collections ?? []).some((x) => !x.trim()) ||
      new Set(m.related_ids ?? []).size !== (m.related_ids ?? []).length
    )
      throw new Error("SCHEMA_INVALID");
    for (const value of [m.title ?? "", ...(m.collections ?? [])])
      for (const ch of value)
        if (
          ch.length === 1 &&
          ch.charCodeAt(0) >= 0xd800 &&
          ch.charCodeAt(0) <= 0xdfff
        )
          throw new Error("SCHEMA_INVALID");
  }
  const text = p.raw_text;
  if (typeof text !== "string" || !text.trim() || [...text].length > 100000)
    throw new Error("SCHEMA_INVALID");
  for (const ch of text)
    if (
      ch.charCodeAt(0) >= 0xd800 &&
      ch.charCodeAt(0) <= 0xdfff &&
      ch.length === 1
    )
      throw new Error("SCHEMA_INVALID");
  const tags = p.tags ?? [];
  if (
    tags.length > 20 ||
    new Set(tags).size !== tags.length ||
    tags.some(
      (t) =>
        !t.trim() ||
        [...t].length > 64 ||
        [...t].some(
          (ch) =>
            ch.length === 1 &&
            ch.charCodeAt(0) >= 0xd800 &&
            ch.charCodeAt(0) <= 0xdfff,
        ),
    )
  )
    throw new Error("SCHEMA_INVALID");
  new Intl.DateTimeFormat("en", { timeZone: p.timezone ?? "Europe/Warsaw" });
  for (const [kind, fields] of Object.entries(typed))
    for (const f of fields)
      if (kind !== type && f in p) throw new Error("SCHEMA_INVALID");
  for (const k of ["mood_rating", "energy_rating", "sleep_quality"]) {
    const v = (p as any)[k];
    if (v != null && (!Number.isInteger(v) || v < 0 || v > 10))
      throw new Error("SCHEMA_INVALID");
  }
  for (const k of ["occurred_at_utc", "sleep_start_utc", "wake_at_utc"]) {
    const v = (p as any)[k];
    if (
      v != null &&
      (!/(Z|[+-]\d\d:\d\d)$/.test(v) || Number.isNaN(Date.parse(v)))
    )
      throw new Error("SCHEMA_INVALID");
  }
  if (
    p.type === "sleep" &&
    p.wake_at_utc &&
    p.occurred_at_utc !== p.wake_at_utc
  )
    throw new Error("SCHEMA_INVALID");
  if (
    p.sleep_start_utc &&
    p.wake_at_utc &&
    Date.parse(p.wake_at_utc) < Date.parse(p.sleep_start_utc)
  )
    throw new Error("SCHEMA_INVALID");
  const precision = p.time_precision ?? "unknown";
  if (
    precision === "unknown" &&
    (p.occurred_at_utc != null || p.local_date != null)
  )
    throw new Error("SCHEMA_INVALID");
  if (precision === "date" && (!p.local_date || p.occurred_at_utc != null))
    throw new Error("SCHEMA_INVALID");
  if (precision === "instant") {
    if (
      !p.occurred_at_utc ||
      p.local_date !==
        new Intl.DateTimeFormat("en-CA", {
          timeZone: p.timezone ?? "Europe/Warsaw",
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
        }).format(new Date(p.occurred_at_utc))
    )
      throw new Error("SCHEMA_INVALID");
  }
  return p;
}
export function draftPayload(d: Draft) {
  const p: any = {
    type: d.type,
    raw_text: d.raw_text,
    tags: d.tags ? d.tags.split(",").map((t) => t.trim()) : [],
    timezone: d.timezone,
    time_precision: d.time_precision,
    local_date: d.local_date || null,
    occurred_at_utc: d.occurred_at_utc || null,
  };
  for (const k of typed[d.type]) {
    const v = (d as any)[k];
    p[k] =
      k.endsWith("rating") || k === "sleep_quality"
        ? v === ""
          ? null
          : Number(v)
        : v || null;
  }
  if (d.type === "sleep" && d.wake_at_utc) {
    p.occurred_at_utc = d.wake_at_utc;
    p.time_precision = "instant";
    p.local_date = new Intl.DateTimeFormat("en-CA", {
      timeZone: d.timezone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(new Date(d.wake_at_utc));
  }
  return validatePayload(p);
}
