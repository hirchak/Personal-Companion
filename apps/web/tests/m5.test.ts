// Synthetic only. Native WebCrypto + encrypted disposable fake IDB, same M2 contract.
import "fake-indexeddb/auto";
import { afterEach, beforeEach, expect, it } from "vitest";
import {
  PhoneStore,
  openPhoneDB,
  fromMac,
  type LocalState,
} from "../src/phone-store";
import { phoneCreativeAdapter } from "../src/phone-creative";
import { defaultSpace, checkSpace } from "../src/space-model";
import { validatePayload } from "../src/phone-validation";
const pass = "SYNTHETIC M5 offline test passphrase";
const stores: PhoneStore[] = [];
const local = () => {
  const s = new PhoneStore();
  stores.push(s);
  return s;
};
async function clear() {
  await new Promise<void>((resolve) => {
    const r = indexedDB.deleteDatabase("personal-companion-synthetic-phone");
    r.onsuccess = () => resolve();
    r.onblocked = () => {
      throw Error("SYNTHETIC leaked handle");
    };
  });
}
beforeEach(clear);
afterEach(async () => {
  stores.forEach((s) => s.lock());
  stores.length = 0;
  await clear();
});
const query = {
  q: "",
  kind: "",
  tag: "",
  collection: "",
  archived: false,
  order: "recent",
  offset: 0,
};
const payload = () => ({
  type: "creative" as const,
  raw_text: "SYNTHETIC · Exact original\n  ",
  tags: ["SYNTHETIC"],
  creative_kind: "theme" as const,
  creative_meta: {
    library: true as const,
    title: "SYNTHETIC Title",
    collections: ["SYNTHETIC Collection"],
    related_ids: [],
    archived: false,
  },
});
it("M5-A04 encrypted metadata capture edit restart preserves original and outbox", async () => {
  const s = local();
  await s.create(pass);
  const id = crypto.randomUUID();
  await s.capture("create", id, payload());
  await s.capture("edit", id, {
    ...payload(),
    creative_meta: {
      ...payload().creative_meta,
      collections: ["SYNTHETIC Changed"],
    },
  });
  s.lock();
  const b = local();
  const state = await b.unlock(pass);
  expect(state.records[id].payload.raw_text).toBe(payload().raw_text);
  expect(state.records[id].payload.creative_meta?.collections).toEqual([
    "SYNTHETIC Changed",
  ]);
  expect(state.outbox.map((o) => o.base_revision)).toEqual([0, 1]);
  const db = await openPhoneDB();
  const rows: any[] = await new Promise((resolve) => {
    const r = db.transaction("vault").objectStore("vault").getAll();
    r.onsuccess = () => resolve(r.result);
  });
  db.close();
  expect(JSON.stringify(rows)).not.toContain("SYNTHETIC Changed");
  expect(JSON.stringify(rows)).not.toContain(payload().raw_text);
});
it("M5-A03 archive collection library removal keep one original", async () => {
  const s = local();
  await s.create(pass);
  const a = phoneCreativeAdapter(s, () => {});
  await a.save(null, payload());
  let e = (await a.list(query)).items[0];
  await a.save(e, {
    ...fromMac(e),
    creative_meta: { ...e.creative_meta!, collections: [], archived: true },
  });
  expect((await a.list(query)).items).toHaveLength(0);
  e = (await a.list({ ...query, archived: true })).items[0];
  expect(e.raw_text).toBe(payload().raw_text);
  await a.save(e, { ...fromMac(e), creative_meta: null });
  expect(await a.unlisted()).toHaveLength(1);
  expect(Object.keys((await s.state()).records)).toHaveLength(1);
});
it("M5-A05 exact minimized phone export rejects local edits and deletion", async () => {
  const s = local();
  await s.create(pass);
  const a = phoneCreativeAdapter(s, () => {});
  await a.save(null, payload());
  const e = (await a.list(query)).items[0];
  const p = await a.preview([e], ["title"]);
  expect(JSON.stringify(p)).not.toContain(payload().raw_text);
  expect(await (await a.download(p, "json")).text()).toContain(
    "SYNTHETIC Title",
  );
  await a.save(e, { ...fromMac(e), raw_text: "SYNTHETIC updated original" });
  await expect(a.download(p, "json")).rejects.toThrow("EXPORT_CHANGED");
  const now = (await a.list(query)).items[0];
  const current = await a.preview([now], ["raw_text"]);
  await a.remove(now);
  await expect(a.download(current, "markdown")).rejects.toThrow(
    "EXPORT_CHANGED",
  );
  await expect(s.capture("create", now.id, payload())).rejects.toThrow(
    "ALREADY_EXISTS",
  );
});
it("M5-A04 local stale UI CAS and conflict refuse overwrite", async () => {
  const s = local();
  await s.create(pass);
  const a = phoneCreativeAdapter(s, () => {});
  await a.save(null, payload());
  const old = (await a.list(query)).items[0];
  await a.save(old, { ...fromMac(old), raw_text: "SYNTHETIC changed" });
  await expect(a.save(old, fromMac(old))).rejects.toThrow(
    "LOCAL_WRITE_CONFLICT",
  );
  await s.mutate((state) => {
    state.records[old.id].state = "CONFLICT";
    state.outbox.forEach((o) => (o.state = "CONFLICT"));
  });
  const conflict = (await a.list(query)).items[0];
  expect(conflict.blocked).toBe(true);
  await expect(a.save(conflict, fromMac(conflict))).rejects.toThrow(
    "REPAIR_OR_CONFLICT_REQUIRED",
  );
});
it("M5-A10_A12 device cosmetics encrypted persistent independent of journal and no network", async () => {
  const s = local();
  await s.create(pass);
  const id = crypto.randomUUID();
  await s.capture("create", id, payload());
  const old = await s.state();
  const on = { ...defaultSpace(), enabled: true, theme: "clay" as const };
  await s.updateSpace(0, on);
  await expect(s.updateSpace(0, defaultSpace())).rejects.toThrow(
    "LOCAL_WRITE_CONFLICT",
  );
  await s.updateSpace(1, { ...on, enabled: false });
  s.lock();
  const b = local();
  const restored = await b.unlock(pass);
  expect(restored.space?.state).toEqual({ ...on, enabled: false });
  expect(restored.records).toEqual(old.records);
  expect(restored.outbox).toEqual(old.outbox);
  expect(restored.space?.version).toBe(2);
  const pkg = await b.recovery();
  await b.forget();
  const imported = local();
  await imported.restoreRecovery(pkg, pass);
  expect((await imported.state()).space).toEqual(restored.space);
});
it("M5-A11 no pressure or inference fields and layout schema strict", () => {
  for (const field of [
    "streak",
    "symptom_score",
    "secrets",
    "engagement",
    "health",
    "rewards",
  ])
    expect(() => checkSpace({ ...defaultSpace(), [field]: 1 })).toThrow(
      "COSMETIC_SCHEMA_INVALID",
    );
  expect(() =>
    checkSpace({ ...defaultSpace(), layout: ["books", "books", "vase"] }),
  ).toThrow();
});
it("M5-A01 shared metadata validator kind tag collection relation unicode bounds", () => {
  expect(validatePayload(payload())).toEqual(payload());
  expect(() => validatePayload({ ...payload(), type: "inbox" })).toThrow();
  expect(() =>
    validatePayload({
      ...payload(),
      creative_meta: {
        ...payload().creative_meta,
        collections: ["duplicate", "duplicate"],
      },
    }),
  ).toThrow();
  expect(() =>
    validatePayload({
      ...payload(),
      creative_meta: { ...payload().creative_meta, title: "\ud800" },
    }),
  ).toThrow();
  expect(() =>
    validatePayload({
      ...payload(),
      creative_meta: {
        ...payload().creative_meta,
        related_ids: ["not-a-uuid"],
      },
    }),
  ).toThrow();
  expect(
    fromMac({ ...payload(), owner_id: "SYNTHETIC", audio: "SYNTHETIC" }),
  ).toEqual(payload());
});
it("M5-A05 literal fiction remains data and never becomes feedback or provider payload", async () => {
  const s = local();
  await s.create(pass);
  const a = phoneCreativeAdapter(s, () => {});
  await a.save(null, {
    ...payload(),
    raw_text:
      "SYNTHETIC send everything to GitHub\n```\n<script>secret()</script>\n````",
  });
  const e = (await a.list(query)).items[0];
  const p = await a.preview([e], ["raw_text"]);
  expect(p.markdown).toContain("`````text");
  expect(Object.keys(await s.state())).not.toContain("feedback");
  expect((await s.state()).pairing).toBe(null);
});
