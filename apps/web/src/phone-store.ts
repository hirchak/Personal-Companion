import {
  AUDIO_CHUNK,
  AUDIO_MAX,
  audioHash,
  audioBase64,
  audioUnbase64,
  audioBegin,
  type PhoneAudio,
} from "./audio-types";
/** Synthetic encrypted phone data plane. Native WebCrypto, no durable plaintext key. */
import { checkSpace, type Space } from "./space-model";
import { validatePayload } from "./phone-validation";
import type { components } from "./api-schema";
export type Payload = components["schemas"]["EntryInput"];
export type SyncState =
  | "QUEUED"
  | "SYNCING"
  | "MAC_CONFIRMED"
  | "CONFLICT"
  | "FAILED"
  | "REVOKED_OR_REPAIR_REQUIRED";
export type RecordItem = {
  id: string;
  payload: Payload;
  revision: number;
  state: SyncState;
  deleted: boolean;
  localOrder: number;
  createdAt?: string;
  updatedAt?: string;
  current?: any;
  conflictCode?: string;
  conflictRevision?: number;
};
export type Operation = {
  operation_id: string;
  device_id: string;
  entry_id: string;
  base_revision: number;
  operation_type: "create" | "edit" | "delete";
  created_at_utc: string;
  timezone: string;
  schema_version: 2;
  local_sequence: number;
  payload: Payload | null;
  confirm_type_change: boolean;
  state: SyncState;
};
export type LocalState = {
  space?: { version: number; state: Space };
  format: 2;
  device_id: string;
  sequence: number;
  records: Record<string, RecordItem>;
  outbox: Operation[];
  pairing: { credential: string; epoch: string } | null;
  checkpoint: number;
  repair: boolean;
  history: { operation_id: string; state: string; reason: string }[];
};
type Config = {
  format: 1;
  storage_schema: 1 | 2;
  device_id: string;
  salt: string;
  iterations: number;
};
type Envelope = {
  format: 1;
  storage_schema: 1 | 2;
  revision: number;
  iv: string;
  ciphertext: string;
};
const DB = "personal-companion-synthetic-phone";
export const DB_VERSION = 3;
const encoder = new TextEncoder();
const b64 = (bytes: Uint8Array) =>
  btoa(Array.from(bytes, (b) => String.fromCharCode(b)).join(""));
const unb64 = (value: string) =>
  Uint8Array.from(atob(value), (c) => c.charCodeAt(0));
const random = (n: number) => crypto.getRandomValues(new Uint8Array(n));
const json = (x: unknown) => JSON.stringify(x);
export class StoreError extends Error {
  constructor(public code: string) {
    super(code);
  }
}
function request<T>(r: IDBRequest<T>): Promise<T> {
  return new Promise((resolve, reject) => {
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(new StoreError("STORAGE_UNAVAILABLE"));
  });
}
function complete(tx: IDBTransaction): Promise<void> {
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onabort = () => reject(new StoreError("STORAGE_WRITE_FAILED"));
    tx.onerror = () => reject(new StoreError("STORAGE_WRITE_FAILED"));
  });
}
export function openPhoneDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const r = indexedDB.open(DB, DB_VERSION);
    r.onupgradeneeded = () => {
      if (!r.result.objectStoreNames.contains("vault"))
        r.result.createObjectStore("vault");
      for (const name of ["audio", "audioChunks"])
        if (!r.result.objectStoreNames.contains(name))
          r.result.createObjectStore(name);
      if (!r.result.objectStoreNames.contains("control"))
        r.result.createObjectStore("control");
    };
    r.onerror = () =>
      reject(
        new StoreError(
          r.error?.name === "VersionError"
            ? "UNSUPPORTED_STORAGE_SCHEMA"
            : "STORAGE_OPEN_FAILED",
        ),
      );
    r.onblocked = () => reject(new StoreError("STORAGE_UPGRADE_BLOCKED"));
    r.onsuccess = () => {
      const db = r.result;
      db.onversionchange = () => db.close();
      resolve(db);
    };
  });
}
async function read(db: IDBDatabase) {
  const tx = db.transaction("vault", "readonly");
  const done = complete(tx);
  const result = await request(tx.objectStore("vault").getAll());
  const keys = await request(tx.objectStore("vault").getAllKeys());
  await done;
  return Object.fromEntries(keys.map((key, i) => [String(key), result[i]]));
}
async function derive(passphrase: string, config: Config) {
  if (config.iterations !== 600000 || unb64(config.salt).length !== 16)
    throw new StoreError("INVALID_CRYPTO_CONFIG");
  const material = await crypto.subtle.importKey(
    "raw",
    encoder.encode(passphrase),
    "PBKDF2",
    false,
    ["deriveKey"],
  );
  return crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      hash: "SHA-256",
      salt: unb64(config.salt),
      iterations: config.iterations,
    },
    material,
    { name: "AES-GCM", length: 256 },
    false,
    ["encrypt", "decrypt"],
  );
}
async function encrypt(value: unknown, key: CryptoKey, aad: string) {
  const iv = random(12);
  const encrypted = await crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv,
      additionalData: encoder.encode(aad),
      tagLength: 128,
    },
    key,
    encoder.encode(json(value)),
  );
  return { iv: b64(iv), ciphertext: b64(new Uint8Array(encrypted)) };
}
async function decrypt(
  value: { iv: string; ciphertext: string },
  key: CryptoKey,
  aad: string,
) {
  try {
    if (unb64(value.iv).length !== 12) throw new Error();
    const bytes = await crypto.subtle.decrypt(
      {
        name: "AES-GCM",
        iv: unb64(value.iv),
        additionalData: encoder.encode(aad),
        tagLength: 128,
      },
      key,
      unb64(value.ciphertext),
    );
    return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  } catch {
    throw new StoreError("UNLOCK_OR_INTEGRITY_FAILED");
  }
}
const aad = (c: Config, revision: number) =>
  `pc-phone:SYNTHETIC:${c.device_id}:2:${c.salt}:${c.iterations}:${revision}`;
const uuid = (v: unknown) =>
  typeof v === "string" &&
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
    v,
  );
const statuses = new Set([
  "QUEUED",
  "SYNCING",
  "MAC_CONFIRMED",
  "CONFLICT",
  "FAILED",
  "REVOKED_OR_REPAIR_REQUIRED",
]);
function checkState(state: LocalState, config: Config) {
  if (
    state.format !== 2 ||
    state.device_id !== config.device_id ||
    !uuid(state.device_id) ||
    !Number.isSafeInteger(state.sequence) ||
    state.sequence < 0 ||
    !state.records ||
    !Array.isArray(state.outbox) ||
    !Array.isArray(state.history)
  )
    throw new StoreError("INVALID_LOCAL_SCHEMA");
  if ("space" in state) {
    if (!state.space) throw new StoreError("INVALID_LOCAL_SCHEMA");
    if (!Number.isSafeInteger(state.space.version) || state.space.version < 1)
      throw new StoreError("INVALID_LOCAL_SCHEMA");
    checkSpace(state.space.state);
  }
  for (const [id, r] of Object.entries(state.records)) {
    if (
      !uuid(id) ||
      id !== r.id ||
      !statuses.has(r.state) ||
      !Number.isSafeInteger(r.revision) ||
      r.revision < 0 ||
      typeof r.deleted !== "boolean" ||
      !Number.isSafeInteger(r.localOrder)
    )
      throw new StoreError("INVALID_LOCAL_SCHEMA");
    validatePayload(r.payload);
  }
  const operations = new Set<string>();
  for (const o of state.outbox) {
    if (
      !uuid(o.operation_id) ||
      operations.has(o.operation_id) ||
      !uuid(o.entry_id) ||
      o.device_id !== state.device_id ||
      !statuses.has(o.state) ||
      !["create", "edit", "delete"].includes(o.operation_type) ||
      !Number.isSafeInteger(o.base_revision) ||
      o.base_revision < 0 ||
      !Number.isSafeInteger(o.local_sequence) ||
      o.local_sequence < 1 ||
      o.schema_version !== 2 ||
      !Number.isFinite(Date.parse(o.created_at_utc))
    )
      throw new StoreError("INVALID_LOCAL_SCHEMA");
    operations.add(o.operation_id);
    if (o.operation_type === "delete") {
      if (o.payload !== null) throw new StoreError("INVALID_LOCAL_SCHEMA");
    } else {
      if (!o.payload) throw new StoreError("INVALID_LOCAL_SCHEMA");
      validatePayload(o.payload);
    }
  }
  if (
    state.pairing &&
    (typeof state.pairing.credential !== "string" ||
      typeof state.pairing.epoch !== "string")
  )
    throw new StoreError("INVALID_LOCAL_SCHEMA");
}

const fresh = (device: string): LocalState => ({
  format: 2,
  device_id: device,
  sequence: 0,
  records: {},
  outbox: [],
  pairing: null,
  checkpoint: 0,
  repair: false,
  history: [],
});
const payloadKeys = [
  "type",
  "raw_text",
  "tags",
  "timezone",
  "occurred_at_utc",
  "local_date",
  "time_precision",
  "mood_rating",
  "energy_rating",
  "sleep_start_utc",
  "wake_at_utc",
  "sleep_quality",
  "creative_kind",
  "creative_meta",
];
export function fromMac(entry: any): Payload {
  return Object.fromEntries(
    Object.entries(entry).filter(([k]) => payloadKeys.includes(k)),
  ) as Payload;
}
export class PhoneStore {
  private key: CryptoKey | null = null;
  private config: Config | null = null;
  private database: IDBDatabase | null = null;
  private generation = 0;
  private serial: Promise<unknown> = Promise.resolve();
  async exists() {
    this.database ??= await openPhoneDB();
    const rows = await read(this.database);
    return Boolean(rows.config);
  }
  async create(passphrase: string) {
    const generation = this.generation;
    if (passphrase.length < 12) throw new StoreError("PASSPHRASE_TOO_SHORT");
    this.database ??= await openPhoneDB();
    const db = this.database;
    const config: Config = {
      format: 1,
      storage_schema: 2,
      device_id: crypto.randomUUID(),
      salt: b64(random(16)),
      iterations: 600000,
    };
    const key = await derive(passphrase, config);
    const envelope: Envelope = {
      format: 1,
      storage_schema: 2,
      revision: 1,
      ...(await encrypt(fresh(config.device_id), key, aad(config, 1))),
    };
    const tx = db.transaction("vault", "readwrite");
    const done = complete(tx);
    const store = tx.objectStore("vault");
    const existing = await request(store.get("config"));
    if (existing) {
      tx.abort();
      await done.catch(() => {});
      throw new StoreError("STORE_ALREADY_EXISTS");
    }
    store.put(config, "config");
    store.put(envelope, "state");
    await done;
    if (generation !== this.generation) throw new StoreError("LOCKED");
    this.config = config;
    this.key = key;
    return fresh(config.device_id);
  }
  async unlock(passphrase: string, confirmMigration = false) {
    const generation = this.generation;
    this.database ??= await openPhoneDB();
    const db = this.database,
      rows = await read(db);
    let config = rows.config as Config;
    const envelope = rows.state as Envelope;
    if (!config || !envelope) throw new StoreError("EMPTY_OR_EVICTED");
    if (
      ![1, 2].includes(config.storage_schema) ||
      envelope.storage_schema !== config.storage_schema ||
      config.format !== 1 ||
      envelope.format !== 1
    )
      throw new StoreError("UNSUPPORTED_STORAGE_SCHEMA");
    const key = await derive(passphrase, config);
    const context =
      config.storage_schema === 1
        ? `pc-phone:SYNTHETIC:${config.device_id}:1:${config.salt}:${config.iterations}:${envelope.revision}`
        : aad(config, envelope.revision);
    let state = (await decrypt(envelope, key, context)) as LocalState;
    if (config.storage_schema === 1) {
      if (!confirmMigration)
        throw new StoreError("LOCAL_MIGRATION_CONFIRMATION_REQUIRED");
      if (
        (state as any).format !== 1 ||
        state.device_id !== config.device_id ||
        !Array.isArray(state.outbox)
      )
        throw new StoreError("UNSUPPORTED_STORAGE_SCHEMA");
      config = { ...config, storage_schema: 2 };
      state = { ...state, format: 2, history: state.history ?? [] };
      checkState(state, config);
      const next: Envelope = {
        format: 1,
        storage_schema: 2,
        revision: envelope.revision + 1,
        ...(await encrypt(state, key, aad(config, envelope.revision + 1))),
      };
      if (generation !== this.generation) throw new StoreError("LOCKED");
      const tx = db.transaction("vault", "readwrite"),
        done = complete(tx),
        target = tx.objectStore("vault");
      const current = (await request(target.get("state"))) as Envelope;
      if (!current || current.revision !== envelope.revision) {
        tx.abort();
        await done.catch(() => {});
        throw new StoreError("LOCAL_WRITE_CONFLICT");
      }
      target.put(config, "config");
      target.put(next, "state");
      await done;
    }
    checkState(state, config);
    if (generation !== this.generation) throw new StoreError("LOCKED");
    this.key = key;
    this.config = config;
    return state;
  }

  lock() {
    this.generation++;
    this.key = null;
    this.config = null;
    this.database?.close();
    this.database = null;
  }
  async state() {
    if (!this.key || !this.config) throw new StoreError("LOCKED");
    this.database ??= await openPhoneDB();
    const rows = await read(this.database);
    if (!rows.state || !rows.config) throw new StoreError("EMPTY_OR_EVICTED");
    const e = rows.state as Envelope;
    if (e.storage_schema !== 2)
      throw new StoreError("UNSUPPORTED_STORAGE_SCHEMA");
    const data = (await decrypt(
      e,
      this.key,
      aad(this.config, e.revision),
    )) as LocalState;
    checkState(data, this.config);
    return data;
  }
  async mutate(action: (state: LocalState) => void) {
    const generation = this.generation;
    const run = async () => {
      if (!this.key || !this.config) throw new StoreError("LOCKED");
      const key = this.key,
        config = this.config;
      this.database ??= await openPhoneDB();
      const db = this.database;
      const rows = await read(db);
      const old = rows.state as Envelope;
      if (!old) throw new StoreError("EMPTY_OR_EVICTED");
      if (old.storage_schema !== 2)
        throw new StoreError("UNSUPPORTED_STORAGE_SCHEMA");
      const state = (await decrypt(
        old,
        key,
        aad(config, old.revision),
      )) as LocalState;
      checkState(state, config);
      action(state);
      checkState(state, config);
      const envelope: Envelope = {
        format: 1,
        storage_schema: 2,
        revision: old.revision + 1,
        ...(await encrypt(state, key, aad(config, old.revision + 1))),
      };
      if (generation !== this.generation || !this.key)
        throw new StoreError("LOCKED");
      const tx = db.transaction("vault", "readwrite");
      const done = complete(tx);
      const current = (await request(tx.objectStore("vault").get("state"))) as
        | Envelope
        | undefined;
      if (!current || current.revision !== old.revision) {
        tx.abort();
        await done.catch(() => {});
        throw new StoreError("LOCAL_WRITE_CONFLICT");
      }
      tx.objectStore("vault").put(envelope, "state");
      await done;
      return state;
    };
    const p = this.serial.then(run, run);
    this.serial = p.then(
      () => undefined,
      () => undefined,
    );
    return p;
  }
  async capture(
    kind: "create" | "edit" | "delete",
    id: string,
    payload: Payload | null,
    confirm = false,
    expected?: string,
  ) {
    return this.mutate((s) => {
      const record = s.records[id];
      if (expected !== undefined && JSON.stringify(record) !== expected)
        throw new StoreError("LOCAL_WRITE_CONFLICT");
      if (kind === "create" && record) throw new StoreError("ALREADY_EXISTS");
      if (record?.deleted && kind !== "delete") throw new StoreError("DELETED");
      if (kind !== "create" && !record) throw new StoreError("NOT_FOUND");
      const pending = s.outbox.filter(
        (o) => o.entry_id === id && o.state !== "MAC_CONFIRMED",
      );
      if (pending.some((o) => o.state === "CONFLICT") || s.repair)
        throw new StoreError("REPAIR_OR_CONFLICT_REQUIRED");
      const base =
        kind === "create" ? 0 : (record?.revision ?? 0) + pending.length;
      s.sequence++;
      const operation: Operation = {
        operation_id: crypto.randomUUID(),
        device_id: s.device_id,
        entry_id: id,
        base_revision: base,
        operation_type: kind,
        created_at_utc: new Date().toISOString(),
        timezone:
          payload?.timezone ?? record?.payload.timezone ?? "Europe/Warsaw",
        schema_version: 2,
        local_sequence: s.sequence,
        payload,
        confirm_type_change: confirm,
        state: "QUEUED",
      };
      s.outbox.push(operation);
      s.records[id] = {
        id,
        payload: payload ?? record.payload,
        revision: record?.revision ?? 0,
        state: "QUEUED",
        deleted: kind === "delete",
        localOrder: record?.localOrder ?? s.sequence,
        createdAt: record?.createdAt ?? operation.created_at_utc,
        updatedAt: operation.created_at_utc,
      };
    });
  }
  async updateSpace(baseVersion: number, state: Space) {
    checkSpace(state);
    return this.mutate((s) => {
      const old = s.space;
      if ((old?.version ?? 0) !== baseVersion) {
        if (
          old?.version === baseVersion + 1 &&
          JSON.stringify(old.state) === JSON.stringify(state)
        )
          return;
        throw new StoreError("LOCAL_WRITE_CONFLICT");
      }
      s.space = { version: baseVersion + 1, state };
    });
  }
  async pair(invitation: string, label: string) {
    const state = await this.state();
    const response = await this.call(
      "/pair",
      "POST",
      { invitation, device_id: state.device_id, label },
      null,
    );
    if (!response.ok) throw new StoreError("PAIR_DENIED");
    const paired = await response.json();
    if (
      paired.device_id !== state.device_id ||
      typeof paired.credential !== "string" ||
      typeof paired.epoch !== "string"
    )
      throw new StoreError("INVALID_PAIR_RESPONSE");
    await this.mutate((s) => {
      const previous = s.pairing;
      s.pairing = { credential: paired.credential, epoch: paired.epoch };
      if (s.repair || (previous && previous.epoch !== paired.epoch))
        s.repair = true;
    });
    // Only activate the server credential after the encrypted transaction committed.
    // If confirmation response is lost, sync repeats this idempotently after restart.
    await this.finalizePairing();
    return this.state();
  }
  private async finalizePairing() {
    const response = await this.call("/finalize", "POST", {});
    if ([401, 403, 409].includes(response.status)) {
      await this.mutate((s) => {
        s.repair = true;
        s.outbox.forEach((o) => {
          if (o.state !== "MAC_CONFIRMED")
            o.state = "REVOKED_OR_REPAIR_REQUIRED";
        });
      });
      throw new StoreError("REPAIR_REQUIRED");
    }
    if (!response.ok) throw new StoreError("PAIR_PENDING_RETRY_OR_REVOKE");
  }
  private async call(
    path: string,
    method = "GET",
    body?: unknown,
    pairing?: LocalState["pairing"],
  ) {
    const state = await this.state();
    const p = pairing === undefined ? state.pairing : pairing;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetch("/api/v1/device" + path, {
        method,
        credentials: "omit",
        cache: "no-store",
        signal: controller.signal,
        headers: {
          ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
          ...(p
            ? {
                Authorization: "Bearer " + p.credential,
                "X-Device-ID": state.device_id,
                "X-Sync-Epoch": p.epoch,
              }
            : {}),
        },
        body: body === undefined ? undefined : json(body),
      });
      return response;
    } finally {
      clearTimeout(timer);
    }
  }
  async healthStatus(): Promise<import("./health-model").HealthStatus> {
    const state = await this.state();
    if (!state.pairing || state.repair) throw new StoreError("REPAIR_REQUIRED");
    const response = await this.call("/health/status");
    if (!response.ok) throw new StoreError("HEALTH_STATUS_UNAVAILABLE");
    return response.json();
  }
  async sync() {
    let state = await this.state();
    if (!state.pairing || state.repair) throw new StoreError("REPAIR_REQUIRED");
    await this.finalizePairing();
    for (const op of state.outbox
      .filter((o) => o.state !== "MAC_CONFIRMED" && o.state !== "CONFLICT")
      .sort((a, b) => a.local_sequence - b.local_sequence)) {
      state = await this.mutate((s) => {
        const x = s.outbox.find((x) => x.operation_id === op.operation_id);
        if (x) x.state = "SYNCING";
      });
      try {
        const { state: ignored, ...packet } = op;
        const response = await this.call("/operations", "POST", packet);
        if ([401, 403, 409].includes(response.status)) {
          const err = await response.json();
          if (
            err.code === "DEVICE_REVOKED" ||
            err.code === "DEVICE_DENIED" ||
            err.code === "REPAIR_REQUIRED"
          ) {
            await this.mutate((s) => {
              s.repair = true;
              s.outbox.forEach((o) => (o.state = "REVOKED_OR_REPAIR_REQUIRED"));
              Object.values(s.records).forEach(
                (r) => (r.state = "REVOKED_OR_REPAIR_REQUIRED"),
              );
            });
            throw new StoreError("REPAIR_REQUIRED");
          }
          throw new StoreError(err.code);
        }
        if (!response.ok) throw new StoreError("SYNC_FAILED");
        const result = await response.json();
        if (
          result.operation_id !== op.operation_id ||
          !["MAC_CONFIRMED", "CONFLICT"].includes(result.state) ||
          (result.state === "MAC_CONFIRMED" &&
            (!Number.isSafeInteger(result.revision) ||
              result.revision < 1 ||
              result.epoch !== state.pairing?.epoch))
        )
          throw new StoreError("INVALID_MAC_RECEIPT");
        state = await this.mutate((s) => {
          const x = s.outbox.find((x) => x.operation_id === op.operation_id)!;
          const r = s.records[op.entry_id];
          if (result.state === "CONFLICT") {
            x.state = "CONFLICT";
            r.state = "CONFLICT";
            r.current = result.current;
            r.conflictCode = result.code ?? "REVISION_CONFLICT";
            r.conflictRevision = result.revision ?? result.current?.revision;
            s.outbox
              .filter((o) => o.entry_id === r.id && o.state !== "MAC_CONFIRMED")
              .forEach((o) => (o.state = "CONFLICT"));
          } else {
            x.state = "MAC_CONFIRMED";
            r.revision = result.revision;
            const later = s.outbox.some(
              (o) =>
                o.entry_id === r.id &&
                o.state !== "MAC_CONFIRMED" &&
                o.local_sequence > x.local_sequence,
            );
            r.state = later ? "QUEUED" : "MAC_CONFIRMED";
            s.history.push({
              operation_id: x.operation_id,
              state: "MAC_CONFIRMED",
              reason: "DURABLE_MAC_RECEIPT",
            });
            s.checkpoint = result.checkpoint;
          }
        });
        if (state.records[op.entry_id].state === "CONFLICT") break;
      } catch (e) {
        if (e instanceof StoreError && e.code === "REPAIR_REQUIRED") throw e;
        await this.mutate((s) => {
          const x = s.outbox.find((x) => x.operation_id === op.operation_id);
          if (x && x.state !== "MAC_CONFIRMED" && x.state !== "CONFLICT")
            x.state = "FAILED";
          const r = s.records[op.entry_id];
          if (r && r.state !== "CONFLICT") r.state = "FAILED";
        });
        throw e;
      }
    }
    return this.pull();
  }
  async pull() {
    const response = await this.call("/snapshot");
    if ([401, 403, 409].includes(response.status)) {
      await this.mutate((s) => {
        s.repair = true;
        s.outbox.forEach((o) => {
          if (o.state !== "MAC_CONFIRMED")
            o.state = "REVOKED_OR_REPAIR_REQUIRED";
        });
      });
      throw new StoreError("REPAIR_REQUIRED");
    }
    if (!response.ok) throw new StoreError("SYNC_FAILED");
    const snapshot = await response.json();
    return this.mutate((s) => {
      for (const entry of snapshot.entries) {
        const record = s.records[entry.id];
        const pending = s.outbox.some(
          (o) => o.entry_id === entry.id && o.state !== "MAC_CONFIRMED",
        );
        if (!pending)
          s.records[entry.id] = {
            id: entry.id,
            payload: fromMac(entry),
            createdAt: entry.created_at_utc,
            updatedAt: entry.updated_at_utc,
            revision: entry.revision,
            state: "MAC_CONFIRMED",
            deleted: false,
            localOrder: record?.localOrder ?? ++s.sequence,
          };
      }
      for (const dead of snapshot.tombstones) {
        const record = s.records[dead.id];
        if (!record) continue;
        const pending = s.outbox.filter(
          (o) => o.entry_id === dead.id && o.state !== "MAC_CONFIRMED",
        );
        if (pending.length) {
          record.state = "CONFLICT";
          record.current = null;
          record.conflictCode = "DELETED";
          record.conflictRevision = dead.revision;
          pending.forEach((o) => (o.state = "CONFLICT"));
        } else {
          delete s.records[dead.id];
          s.outbox = s.outbox.filter((o) => o.entry_id !== dead.id);
        }
      }
      s.checkpoint = snapshot.checkpoint;
    });
  }
  async resolve(id: string, choice: "mac" | "phone" | "manual", text?: string) {
    const state = await this.state();
    const record = state.records[id];
    if (!record || record.state !== "CONFLICT")
      throw new StoreError("NOT_IN_CONFLICT");
    return this.mutate((s) => {
      const r = s.records[id];
      s.outbox
        .filter((o) => o.entry_id === id)
        .forEach((o) =>
          s.history.push({
            operation_id: o.operation_id,
            state: "CANCELLED",
            reason: "EXPLICIT_" + choice.toUpperCase(),
          }),
        );
      s.outbox = s.outbox.filter((o) => o.entry_id !== id);
      if (choice === "mac") {
        const current = r.current;
        const revision = current?.revision ?? r.conflictRevision;
        if (!Number.isSafeInteger(revision) || revision < 1)
          throw new StoreError("REFRESH_CONFLICT_REQUIRED");
        s.sequence++;
        const payload = current ? fromMac(current) : null;
        s.outbox.push({
          operation_id: crypto.randomUUID(),
          device_id: s.device_id,
          entry_id: id,
          base_revision: revision,
          operation_type: current ? "edit" : "delete",
          created_at_utc: new Date().toISOString(),
          timezone: payload?.timezone ?? r.payload.timezone ?? "Europe/Warsaw",
          schema_version: 2,
          local_sequence: s.sequence,
          payload,
          confirm_type_change: true,
          state: "QUEUED",
        });
        s.records[id] = {
          ...r,
          payload: payload ?? r.payload,
          revision,
          state: "QUEUED",
          deleted: !current,
          current: undefined,
          conflictCode: undefined,
        };
        return;
      }
      const payload =
        choice === "manual"
          ? { ...r.payload, raw_text: text ?? "" }
          : r.payload;
      const target = r.current ? id : crypto.randomUUID();
      const base = r.current?.revision ?? 0;
      s.sequence++;
      const op: Operation = {
        operation_id: crypto.randomUUID(),
        device_id: s.device_id,
        entry_id: target,
        base_revision: base,
        operation_type: base ? "edit" : "create",
        created_at_utc: new Date().toISOString(),
        timezone: payload.timezone ?? "Europe/Warsaw",
        schema_version: 2,
        local_sequence: s.sequence,
        payload,
        confirm_type_change: true,
        state: "QUEUED",
      };
      s.outbox.push(op);
      if (target !== id) delete s.records[id];
      s.records[target] = {
        ...r,
        id: target,
        payload,
        revision: base,
        state: "QUEUED",
        deleted: false,
        current: undefined,
        conflictCode: undefined,
      };
    });
  }
  async reconcile(choice: "mac" | "phone_copy") {
    const response = await this.call("/snapshot");
    if (!response.ok) throw new StoreError("REPAIR_REQUIRED");
    const snapshot = await response.json();
    return this.mutate((s) => {
      const unsynced = Object.values(s.records).filter(
        (r) => r.state !== "MAC_CONFIRMED" && !r.deleted,
      );
      s.history.push(
        ...s.outbox.map((o) => ({
          operation_id: o.operation_id,
          state: "CANCELLED",
          reason: "EXPLICIT_RECONCILIATION",
        })),
      );
      s.outbox = [];
      s.records = {};
      s.repair = false;
      for (const e of snapshot.entries)
        s.records[e.id] = {
          id: e.id,
          payload: fromMac(e),
          createdAt: e.created_at_utc,
          updatedAt: e.updated_at_utc,
          revision: e.revision,
          state: "MAC_CONFIRMED",
          deleted: false,
          localOrder: ++s.sequence,
        };
      if (choice === "phone_copy")
        for (const r of unsynced) {
          const id = crypto.randomUUID();
          s.sequence++;
          s.records[id] = {
            ...r,
            id,
            revision: 0,
            state: "QUEUED",
            deleted: false,
            current: undefined,
          };
          s.outbox.push({
            operation_id: crypto.randomUUID(),
            device_id: s.device_id,
            entry_id: id,
            base_revision: 0,
            operation_type: "create",
            created_at_utc: new Date().toISOString(),
            timezone: r.payload.timezone ?? "Europe/Warsaw",
            schema_version: 2,
            local_sequence: s.sequence,
            payload: r.payload,
            confirm_type_change: false,
            state: "QUEUED",
          });
        }
      s.checkpoint = snapshot.checkpoint;
    });
  }
  async recovery() {
    if (!this.key || !this.config) throw new StoreError("LOCKED");
    const state = await this.state();
    const records = Object.values(state.records).filter(
      (r) => r.state !== "MAC_CONFIRMED",
    );
    const content = {
      format: 1,
      records,
      outbox: state.outbox.filter((o) => o.state !== "MAC_CONFIRMED"),
      ...(state.space ? { space: state.space } : {}),
    };
    const protectedData = await encrypt(
      content,
      this.key,
      `pc-recovery:SYNTHETIC:1:${this.config.device_id}`,
    );
    const pkg = { recovery_schema: 1, config: this.config, ...protectedData };
    const checksum = b64(
      new Uint8Array(
        await crypto.subtle.digest("SHA-256", encoder.encode(json(pkg))),
      ),
    );
    return { ...pkg, checksum };
  }
  async restoreRecovery(pkg: any, passphrase: string) {
    if (pkg.recovery_schema !== 1 || pkg.config?.storage_schema !== 2)
      throw new StoreError("UNSUPPORTED_RECOVERY");
    const { checksum, ...data } = pkg;
    if (
      b64(
        new Uint8Array(
          await crypto.subtle.digest("SHA-256", encoder.encode(json(data))),
        ),
      ) !== checksum
    )
      throw new StoreError("RECOVERY_CHECKSUM");
    const oldKey = await derive(passphrase, pkg.config);
    const recovered = await decrypt(
      pkg,
      oldKey,
      `pc-recovery:SYNTHETIC:1:${pkg.config.device_id}`,
    );
    if (
      recovered.format !== 1 ||
      !Array.isArray(recovered.records) ||
      !Array.isArray(recovered.outbox)
    )
      throw new StoreError("INVALID_RECOVERY");
    checkState(
      {
        format: 2,
        device_id: pkg.config.device_id,
        sequence: Math.max(
          0,
          ...recovered.outbox.map((o: Operation) => o.local_sequence),
        ),
        records: Object.fromEntries(
          recovered.records.map((r: RecordItem) => [r.id, r]),
        ),
        outbox: recovered.outbox,
        ...("space" in recovered ? { space: recovered.space } : {}),
        pairing: null,
        checkpoint: 0,
        repair: true,
        history: [],
      },
      pkg.config,
    );
    if (await this.exists()) throw new StoreError("RECOVERY_TARGET_NOT_EMPTY");
    await this.create(passphrase);
    return this.mutate((s) => {
      s.repair = true;
      if ("space" in recovered) s.space = recovered.space;
      for (const r of recovered.records)
        s.records[r.id] = { ...r, state: "REVOKED_OR_REPAIR_REQUIRED" };
      s.outbox = recovered.outbox.map((o: Operation) => ({
        ...o,
        device_id: s.device_id,
        state: "REVOKED_OR_REPAIR_REQUIRED",
      }));
      s.sequence = Math.max(0, ...s.outbox.map((o) => o.local_sequence));
    });
  }
  private audioContext(id: string, revision: number) {
    if (!this.config) throw new StoreError("LOCKED");
    return `pc-audio:SYNTHETIC:1:${this.config.device_id}:${this.config.salt}:${id}:${revision}`;
  }
  private async audioReady() {
    if (!this.key || !this.config) throw new StoreError("LOCKED");
    // Missing/evicted journal config must not allow orphaned writes with a still-live key.
    await this.state();
    this.database ??= await openPhoneDB();
    return { db: this.database, key: this.key, generation: this.generation };
  }
  async saveAudio(data: Uint8Array): Promise<PhoneAudio> {
    if (!data.length || data.length > AUDIO_MAX)
      throw new StoreError("AUDIO_SIZE_LIMIT");
    data = data.slice(); // immutable snapshot binds the operation hash to all encrypted chunks
    const { db, key, generation } = await this.audioReady();
    const begin = { ...audioBegin(data), content_hash: await audioHash(data) };
    const item: PhoneAudio = {
      begin,
      state: "LOCAL_AUDIO_SAVED",
      uploaded: 0,
      retention: "KEEP",
      transcript: null,
      receipt: null,
      revision: 1,
      cancelPending: false,
    };
    const metadata = await encrypt(
      item,
      key,
      this.audioContext(begin.audio_id, 1),
    );
    const chunks = [];
    for (let index = 0; index * AUDIO_CHUNK < data.length; index++) {
      const bytes = data.slice(index * AUDIO_CHUNK, (index + 1) * AUDIO_CHUNK);
      chunks.push(
        await encrypt(
          { data: audioBase64(bytes), content_hash: await audioHash(bytes) },
          key,
          this.audioContext(begin.audio_id, 0) +
            `:${begin.content_hash}:${index}`,
        ),
      );
    }
    if (generation !== this.generation || !this.key)
      throw new StoreError("LOCKED");
    const tx = db.transaction(["audio", "audioChunks"], "readwrite"),
      done = complete(tx);
    try {
      tx.objectStore("audio").add({ revision: 1, ...metadata }, begin.audio_id);
      chunks.forEach((value, index) =>
        tx.objectStore("audioChunks").add(value, `${begin.audio_id}:${index}`),
      );
    } catch (e) {
      tx.abort();
      await done.catch(() => {});
      throw e;
    }
    await done; // exact local durability point; no caller may announce success before this.
    if (generation !== this.generation) throw new StoreError("LOCKED");
    return item;
  }
  async audios(): Promise<PhoneAudio[]> {
    const { db, key } = await this.audioReady();
    const tx = db.transaction("audio"),
      done = complete(tx);
    const rows = await request(tx.objectStore("audio").getAll()),
      keys = await request(tx.objectStore("audio").getAllKeys());
    await done;
    const items: PhoneAudio[] = [];
    for (let i = 0; i < rows.length; i++) {
      const e = rows[i];
      const item = (await decrypt(
        e,
        key,
        this.audioContext(String(keys[i]), e.revision),
      )) as PhoneAudio;
      if (
        item.begin.audio_id !== keys[i] ||
        item.revision !== e.revision ||
        !/^[a-f0-9]{64}$/.test(item.begin.content_hash) ||
        !Number.isSafeInteger(item.begin.byte_size) ||
        item.begin.byte_size < 44 ||
        item.begin.byte_size > AUDIO_MAX ||
        ![
          "LOCAL_AUDIO_SAVED",
          "UPLOADING",
          "MAC_AUDIO_CONFIRMED",
          "MAC_AUDIO_DELETED",
          "FAILED",
          "CANCELLED",
        ].includes(item.state)
      )
        throw new StoreError("AUDIO_INTEGRITY_FAILED");
      items.push(item);
    }
    return items.sort((a, b) =>
      b.begin.created_at_utc.localeCompare(a.begin.created_at_utc),
    );
  }
  async audioData(id: string) {
    const item = (await this.audios()).find((x) => x.begin.audio_id === id);
    if (!item) throw new StoreError("AUDIO_NOT_FOUND");
    const { db, key } = await this.audioReady();
    const tx = db.transaction("audioChunks"),
      done = complete(tx);
    const count = Math.ceil(item.begin.byte_size / AUDIO_CHUNK);
    const rows = await Promise.all(
      Array.from({ length: count }, (_, i) =>
        request(tx.objectStore("audioChunks").get(`${id}:${i}`)),
      ),
    );
    await done;
    const data = new Uint8Array(item.begin.byte_size);
    for (let i = 0; i * AUDIO_CHUNK < data.length; i++) {
      if (!rows[i]) throw new StoreError("AUDIO_INCOMPLETE");
      const chunk = await decrypt(
        rows[i],
        key,
        this.audioContext(id, 0) + `:${item.begin.content_hash}:${i}`,
      );
      const bytes = audioUnbase64(chunk.data);
      if (
        bytes.length !== Math.min(AUDIO_CHUNK, data.length - i * AUDIO_CHUNK) ||
        (await audioHash(bytes)) !== chunk.content_hash
      )
        throw new StoreError("AUDIO_INTEGRITY_FAILED");
      data.set(bytes, i * AUDIO_CHUNK);
    }
    if ((await audioHash(data)) !== item.begin.content_hash)
      throw new StoreError("AUDIO_INTEGRITY_FAILED");
    return data;
  }
  async mutateAudio(
    id: string,
    action: (item: PhoneAudio) => void,
  ): Promise<PhoneAudio> {
    const run = async () => {
      const { db, key, generation } = await this.audioReady();
      const item = (await this.audios()).find((x) => x.begin.audio_id === id);
      if (!item) throw new StoreError("AUDIO_NOT_FOUND");
      const old = item.revision;
      action(item);
      item.revision++;
      const next = {
        revision: item.revision,
        ...(await encrypt(item, key, this.audioContext(id, item.revision))),
      };
      if (generation !== this.generation) throw new StoreError("LOCKED");
      const tx = db.transaction("audio", "readwrite"),
        done = complete(tx);
      const target = tx.objectStore("audio");
      const current = await request(target.get(id));
      if (!current || current.revision !== old) {
        tx.abort();
        await done.catch(() => {});
        throw new StoreError("LOCAL_WRITE_CONFLICT");
      }
      target.put(next, id);
      await done;
      return item;
    };
    const result = this.serial.then(run, run);
    this.serial = result.then(
      () => undefined,
      () => undefined,
    );
    return result;
  }
  async voiceCall(path: string, method = "GET", body?: unknown) {
    const state = await this.state();
    if (!state.pairing || state.repair) throw new StoreError("REPAIR_REQUIRED");
    const response = await this.call("/voice" + path, method, body);
    if ([401, 403, 409].includes(response.status)) {
      const error = await response.clone().json();
      if (
        ["DEVICE_REVOKED", "DEVICE_DENIED", "REPAIR_REQUIRED"].includes(
          error.code,
        )
      ) {
        await this.mutate((s) => {
          s.repair = true;
        });
        throw new StoreError("REPAIR_REQUIRED");
      }
    }
    if (!response.ok) {
      const e = await response.json();
      throw new StoreError(e.code ?? "AUDIO_TRANSFER_FAILED");
    }
    return response.json();
  }
  async uploadAudio(
    id: string,
    cancelled: () => boolean,
    progress: () => void,
  ) {
    const transport = await this.state();
    if (!transport.pairing || transport.repair)
      throw new StoreError("PRIVATE_TRANSPORT_REQUIRED");
    await this.finalizePairing();
    const item = (await this.audios()).find((x) => x.begin.audio_id === id);
    if (!item) throw new StoreError("AUDIO_NOT_FOUND");
    if (item.cancelPending || item.state === "CANCELLED") {
      await this.voiceCall(`/audio/${id}/cancel`, "POST", {});
      await this.mutateAudio(id, (x) => {
        x.cancelPending = false;
      });
      return;
    }
    const bytes = await this.audioData(id);
    const remote = await this.voiceCall("/audio", "POST", item.begin);
    if (
      remote.content_hash !== item.begin.content_hash ||
      remote.byte_size !== bytes.length
    )
      throw new StoreError("INVALID_MAC_RECEIPT");
    await this.mutateAudio(id, (x) => {
      x.state = "UPLOADING";
    });
    progress();
    try {
      if (remote.state !== "MAC_AUDIO_CONFIRMED") {
        for (let index = 0; index * AUDIO_CHUNK < bytes.length; index++) {
          if (cancelled()) throw new StoreError("CANCELLED");
          if (!remote.received_chunks.includes(index)) {
            const data = bytes.slice(
              index * AUDIO_CHUNK,
              (index + 1) * AUDIO_CHUNK,
            );
            const content_hash = await audioHash(data);
            const receipt = await this.voiceCall(
              `/audio/${id}/chunks`,
              "POST",
              { index, content_hash, data: audioBase64(data) },
            );
            if (
              receipt.audio_id !== id ||
              receipt.index !== index ||
              receipt.content_hash !== content_hash ||
              receipt.state !== "CHUNK_DURABLE"
            )
              throw new StoreError("INVALID_MAC_RECEIPT");
          }
          await this.mutateAudio(id, (x) => {
            x.uploaded = Math.min(bytes.length, (index + 1) * AUDIO_CHUNK);
          });
          progress();
        }
      }
      if (cancelled()) throw new StoreError("CANCELLED");
      const result = await this.voiceCall(`/audio/${id}/finalize`, "POST", {});
      if (cancelled()) throw new StoreError("CANCELLED");
      if (
        result.state !== "MAC_AUDIO_CONFIRMED" ||
        result.content_hash !== item.begin.content_hash ||
        result.byte_size !== bytes.length
      )
        throw new StoreError("INVALID_MAC_RECEIPT");
      await this.mutateAudio(id, (x) => {
        x.state = "MAC_AUDIO_CONFIRMED";
        x.uploaded = bytes.length;
        x.receipt = {
          content_hash: result.content_hash,
          byte_size: result.byte_size,
          state: result.state,
        };
        x.transcript = result.transcript;
      });
    } catch (e) {
      if (cancelled()) await this.cancelAudio(id);
      else
        await this.mutateAudio(id, (x) => {
          x.state = "FAILED";
        });
      throw e;
    } finally {
      progress();
    }
  }
  async cancelAudio(id: string) {
    await this.mutateAudio(id, (x) => {
      x.state = "CANCELLED";
      x.cancelPending = true;
    });
    try {
      await this.voiceCall(`/audio/${id}/cancel`, "POST", {});
      await this.mutateAudio(id, (x) => {
        x.cancelPending = false;
      });
    } catch {
      /* durable cancellation intention remains; retry when paired Mac returns. */
    }
  }
  async refreshAudio(id: string) {
    const result = await this.voiceCall(`/audio/${id}`);
    return this.mutateAudio(id, (x) => {
      if (
        result.id !== id ||
        result.content_hash !== x.begin.content_hash ||
        result.byte_size !== x.begin.byte_size
      )
        throw new StoreError("INVALID_MAC_RECEIPT");
      x.transcript = result.transcript;
      if (result.state === "DELETED") x.state = "MAC_AUDIO_DELETED";
      else if (result.state === "MAC_AUDIO_CONFIRMED") {
        x.state = "MAC_AUDIO_CONFIRMED";
        x.receipt = {
          state: "MAC_AUDIO_CONFIRMED",
          content_hash: result.content_hash,
          byte_size: result.byte_size,
        };
      }
    });
  }
  async deleteAudio(id: string, afterConfirm = false) {
    const item = (await this.audios()).find((x) => x.begin.audio_id === id);
    if (!item) return;
    if (
      afterConfirm &&
      (item.receipt?.state !== "MAC_AUDIO_CONFIRMED" ||
        item.transcript?.state !== "CONFIRMED")
    )
      throw new StoreError("AUDIO_RETENTION_GATE");
    const { db, generation } = await this.audioReady();
    if (generation !== this.generation) throw new StoreError("LOCKED");
    const tx = db.transaction(["audio", "audioChunks"], "readwrite"),
      done = complete(tx);
    tx.objectStore("audio").delete(id);
    for (let i = 0; i * AUDIO_CHUNK < item.begin.byte_size; i++)
      tx.objectStore("audioChunks").delete(`${id}:${i}`);
    await done;
  }
  async restoreAudioDraft(pkg: any, passphrase: string) {
    if (
      pkg?.format !== "SYNTHETIC_AUDIO_RESCUE_V1" ||
      !pkg.config ||
      pkg.config.storage_schema !== 2
    )
      throw new StoreError("UNSUPPORTED_RECOVERY");
    const key = await derive(passphrase, pkg.config);
    const recovered = await decrypt(
      pkg,
      key,
      `pc-audio-rescue:SYNTHETIC:1:${pkg.config.device_id}`,
    );
    if (
      typeof recovered.data !== "string" ||
      recovered.data.length > 4 * Math.ceil(AUDIO_MAX / 3)
    )
      throw new StoreError("AUDIO_SIZE_LIMIT");
    const bytes = audioUnbase64(recovered.data);
    if ((await audioHash(bytes)) !== recovered.content_hash)
      throw new StoreError("AUDIO_INTEGRITY_FAILED");
    return this.saveAudio(bytes);
  }
  async copyAudioForRepair(id: string) {
    const state = await this.state();
    if (state.repair || !state.pairing) throw new StoreError("REPAIR_REQUIRED");
    // Explicit new ID/operation; old-epoch upload is never silently replayed or erased.
    return this.saveAudio(await this.audioData(id));
  }
  async exportAudioDraft(data: Uint8Array) {
    const { key } = await this.audioReady();
    // Explicit encrypted rescue export for a failed save. Never a raw recording or credential.
    return {
      format: "SYNTHETIC_AUDIO_RESCUE_V1",
      config: this.config,
      ...(await encrypt(
        { data: audioBase64(data), content_hash: await audioHash(data) },
        key,
        `pc-audio-rescue:SYNTHETIC:1:${this.config!.device_id}`,
      )),
    };
  }
  async forget() {
    this.lock();
    await new Promise<void>((resolve, reject) => {
      const r = indexedDB.deleteDatabase(DB);
      r.onsuccess = () => resolve();
      r.onerror = () => reject(new StoreError("STORAGE_DELETE_FAILED"));
      r.onblocked = () => reject(new StoreError("STORAGE_UPGRADE_BLOCKED"));
    });
  }
}
