/** Synthetic generated PCM, native WebCrypto, disposable IndexedDB. */
import "fake-indexeddb/auto";
import { afterEach, beforeEach, describe, it, expect, vi } from "vitest";
import { PhoneStore, openPhoneDB } from "../src/phone-store";
import { pcmWav } from "../src/pcm-recorder";
import { audioHash } from "../src/audio-types";
const PASSWORD = "SYNTHETIC controlled audio fixture passphrase";
const stores: PhoneStore[] = [];
const make = () => {
  const s = new PhoneStore();
  stores.push(s);
  return s;
};
const data = (seconds = 1) =>
  pcmWav(
    [
      Float32Array.from(
        { length: 16000 * seconds },
        (_, i) => 0.15 * Math.sin((2 * Math.PI * 330 * i) / 16000),
      ),
    ],
    16000,
  );
async function clear() {
  await new Promise<void>((resolve) => {
    const r = indexedDB.deleteDatabase("personal-companion-synthetic-phone");
    r.onsuccess = () => resolve();
  });
}
async function rows(name: string) {
  const db = await openPhoneDB();
  try {
    return await new Promise<any[]>((resolve) => {
      const r = db.transaction(name).objectStore(name).getAll();
      r.onsuccess = () => resolve(r.result);
    });
  } finally {
    db.close();
  }
}
beforeEach(clear);
afterEach(async () => {
  stores.forEach((s) => s.lock());
  stores.length = 0;
  vi.unstubAllGlobals();
  await clear();
});
describe("M4 encrypted phone audio", () => {
  it("durable encrypted separate chunks reopen without whole-journal rewrite", async () => {
    const s = make();
    await s.create(PASSWORD);
    await s.capture("create", crypto.randomUUID(), {
      raw_text: "SYNTHETIC journal stays separate",
    });
    const before = JSON.stringify(await rows("vault")),
      bytes = data(19),
      item = await s.saveAudio(bytes);
    expect(item.state).toBe("LOCAL_AUDIO_SAVED");
    expect(await rows("audioChunks")).toHaveLength(3);
    expect(JSON.stringify(await rows("vault"))).toBe(before);
    const serialized = JSON.stringify([
      await rows("audio"),
      await rows("audioChunks"),
    ]);
    expect(serialized).not.toContain("audio/wav");
    expect(serialized).not.toContain(item.begin.content_hash);
    expect(serialized).not.toContain(PASSWORD);
    s.lock();
    const other = make();
    await other.unlock(PASSWORD);
    expect((await other.audios())[0].begin.content_hash).toBe(
      await audioHash(bytes),
    );
    expect(await other.audioData(item.begin.audio_id)).toEqual(bytes);
  });
  it("quota/add failure aborts both chunk and metadata and leaves supplied memory bytes", async () => {
    const s = make();
    await s.create(PASSWORD);
    const bytes = data(),
      original = IDBObjectStore.prototype.add;
    IDBObjectStore.prototype.add = function () {
      throw new DOMException("SYNTHETIC quota", "QuotaExceededError");
    };
    try {
      await expect(s.saveAudio(bytes)).rejects.toThrow();
    } finally {
      IDBObjectStore.prototype.add = original;
    }
    expect(await s.audios()).toEqual([]);
    expect(await rows("audioChunks")).toEqual([]);
    expect(bytes.length).toBe(32044);
    const saved = await s.saveAudio(bytes);
    expect(saved.state).toBe("LOCAL_AUDIO_SAVED");
  });
  it("chunk tampering and swapping IDs fail authenticated decryption", async () => {
    const s = make();
    await s.create(PASSWORD);
    const a = await s.saveAudio(data()),
      b = await s.saveAudio(data());
    const db = await openPhoneDB();
    await new Promise<void>((resolve) => {
      const tx = db.transaction("audioChunks", "readwrite"),
        target = tx.objectStore("audioChunks");
      const r = target.get(`${a.begin.audio_id}:0`);
      r.onsuccess = () => target.put(r.result, `${b.begin.audio_id}:0`);
      tx.oncomplete = () => resolve();
    });
    db.close();
    await expect(s.audioData(b.begin.audio_id)).rejects.toThrow(
      "UNLOCK_OR_INTEGRITY_FAILED",
    );
    expect(await s.audioData(a.begin.audio_id)).toEqual(data());
  });
  it("explicit retention requires both durable receipt and confirmed text", async () => {
    const s = make();
    await s.create(PASSWORD);
    const a = await s.saveAudio(data());
    await expect(s.deleteAudio(a.begin.audio_id, true)).rejects.toThrow(
      "AUDIO_RETENTION_GATE",
    );
    expect(await s.audios()).toHaveLength(1);
    await s.deleteAudio(a.begin.audio_id);
    expect(await s.audios()).toEqual([]);
    expect(await rows("audioChunks")).toEqual([]);
  });
  it("encrypted failed-write rescue export has no raw audio or credentials", async () => {
    const s = make();
    await s.create(PASSWORD);
    await s.mutate((x) => {
      x.pairing = {
        credential: "SYNTHETIC fixture auth",
        epoch: "SYNTHETIC epoch",
      };
    });
    const pkg = await s.exportAudioDraft(data());
    expect(pkg.format).toBe("SYNTHETIC_AUDIO_RESCUE_V1");
    expect(JSON.stringify(pkg)).not.toContain("fixture auth");
    expect(JSON.stringify(pkg)).not.toContain("content_hash");
  });
  it("interrupted upload resumes exact chunk and keeps original until explicit deletion", async () => {
    const s = make();
    await s.create(PASSWORD);
    await s.mutate((x) => {
      x.pairing = {
        credential: "SYNTHETIC fixture token",
        epoch: "SYNTHETIC epoch",
      };
    });
    const bytes = data(19),
      item = await s.saveAudio(bytes);
    const received: number[] = [];
    let failed = false;
    let state = "UPLOADING";
    let chunkRequests = 0;
    vi.stubGlobal("fetch", async (url: string, options: any) => {
      const body = options.body ? JSON.parse(options.body) : null;
      expect(url).not.toContain("token");
      expect(options.headers.Authorization).toBe(
        "Bearer SYNTHETIC fixture token",
      );
      let result: any = {};
      if (url.endsWith("/finalize") && !url.includes("/voice/"))
        result = { state: "ACTIVE" };
      else if (url.endsWith("/voice/audio"))
        result = { ...item.begin, state, received_chunks: [...received] };
      else if (url.endsWith("/chunks")) {
        chunkRequests++;
        if (body.index === 1 && !failed) {
          failed = true;
          throw new TypeError("SYNTHETIC connection interrupted");
        }
        received.push(body.index);
        result = {
          audio_id: item.begin.audio_id,
          index: body.index,
          content_hash: body.content_hash,
          state: "CHUNK_DURABLE",
        };
      } else if (url.endsWith("/finalize")) {
        state = "MAC_AUDIO_CONFIRMED";
        result = { ...item.begin, state, transcript: null };
      } else throw new Error("unexpected synthetic route");
      return new Response(JSON.stringify(result), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    await expect(
      s.uploadAudio(
        item.begin.audio_id,
        () => false,
        () => {},
      ),
    ).rejects.toThrow();
    expect((await s.audios())[0].state).toBe("FAILED");
    await s.uploadAudio(
      item.begin.audio_id,
      () => false,
      () => {},
    );
    expect(received).toEqual([0, 1, 2]);
    expect(chunkRequests).toBe(4);
    expect((await s.audios())[0].receipt?.state).toBe("MAC_AUDIO_CONFIRMED");
    expect(await s.audioData(item.begin.audio_id)).toEqual(bytes);
  });
});

// Rescue recovery is explicitly a new local audio copy; credentials never restored.
it("M4 encrypted audio rescue can restore with correct key, rejects tampering and wrong key", async () => {
  const s = make();
  await s.create(PASSWORD);
  const bytes = data();
  const pkg = await s.exportAudioDraft(bytes);
  await expect(
    s.restoreAudioDraft(pkg, "SYNTHETIC wrong audio key"),
  ).rejects.toThrow("UNLOCK_OR_INTEGRITY_FAILED");
  await expect(
    s.restoreAudioDraft(
      { ...pkg, ciphertext: pkg.ciphertext.slice(1) },
      PASSWORD,
    ),
  ).rejects.toThrow("UNLOCK_OR_INTEGRITY_FAILED");
  expect(await s.audios()).toHaveLength(0);
  const copy = await s.restoreAudioDraft(pkg, PASSWORD);
  expect(await s.audioData(copy.begin.audio_id)).toEqual(bytes);
  expect((await s.state()).pairing).toBeNull();
});
it("M4 audio copy after re-pair is explicit and never silently replays old IDs", async () => {
  const s = make();
  await s.create(PASSWORD);
  const old = await s.saveAudio(data());
  await expect(s.copyAudioForRepair(old.begin.audio_id)).rejects.toThrow(
    "REPAIR_REQUIRED",
  );
  await s.mutate((x) => {
    x.pairing = {
      credential: "SYNTHETIC repaired fixture",
      epoch: "SYNTHETIC newer epoch",
    };
  });
  const copy = await s.copyAudioForRepair(old.begin.audio_id);
  expect(copy.begin.audio_id).not.toBe(old.begin.audio_id);
  expect(copy.begin.operation_id).not.toBe(old.begin.operation_id);
  expect(await s.audios()).toHaveLength(2);
});
