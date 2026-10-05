import "fake-indexeddb/auto";
import { expect, it, vi } from "vitest";
import { PhoneStore, openPhoneDB } from "../src/phone-store";
import { audioHash } from "../src/audio-types";
it("M8E offline encrypted voice survives reload; internet never grants private transport", async () => {
  const password = "ORIGINAL SYNTHETIC private queue passphrase";
  const store = new PhoneStore();
  await store.create(password);
  const fetch = vi.fn(() => {
    throw new Error("NO_APPROVED_PRIVATE_TRANSPORT");
  });
  vi.stubGlobal("fetch", fetch);
  const bytes = new Uint8Array(32044).fill(29);
  const item = await store.saveAudio(bytes);
  expect(item.state).toBe("LOCAL_AUDIO_SAVED");
  expect(fetch).not.toHaveBeenCalled();
  const db = await openPhoneDB();
  const rows = await new Promise<unknown[]>((resolve) => {
    const r = db.transaction("audio").objectStore("audio").getAll();
    r.onsuccess = () => resolve(r.result);
  });
  db.close();
  expect(JSON.stringify(rows)).not.toContain("audio/wav");
  expect(JSON.stringify(rows)).not.toContain(item.begin.content_hash);
  store.lock();
  const reopened = new PhoneStore();
  await reopened.unlock(password);
  expect((await reopened.audios())[0].state).toBe("LOCAL_AUDIO_SAVED");
  expect(await audioHash(await reopened.audioData(item.begin.audio_id))).toBe(
    item.begin.content_hash,
  );
  await expect(
    reopened.uploadAudio(
      item.begin.audio_id,
      () => false,
      () => {},
    ),
  ).rejects.toThrow();
  expect(fetch).not.toHaveBeenCalled();
  await reopened.deleteAudio(item.begin.audio_id);
  expect(await reopened.audios()).toEqual([]);
  reopened.lock();
  vi.unstubAllGlobals();
});
