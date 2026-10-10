import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PCMRecorder, PCM_START_TIMEOUT_MS } from "./pcm-recorder";

const deferred = <T>() => {
  let resolve!: (value: T) => void, reject!: (reason: unknown) => void;
  const promise = new Promise<T>((a, b) => {
    resolve = a;
    reject = b;
  });
  return { promise, resolve, reject };
};
let contexts: FakeContext[];
let resume: () => Promise<void>;
class FakeContext {
  state = "running";
  sampleRate = 16000;
  onstatechange: (() => void) | null = null;
  destination = {};
  close = vi.fn(async () => {
    this.state = "closed";
  });
  processor = {
    connect: vi.fn(),
    disconnect: vi.fn(),
    onaudioprocess: null as ((e: any) => void) | null,
  };
  constructor() {
    contexts.push(this);
  }
  resume() {
    return resume();
  }
  createMediaStreamSource() {
    return { connect: vi.fn(), disconnect: vi.fn() };
  }
  createScriptProcessor() {
    return this.processor;
  }
  createGain() {
    return { connect: vi.fn(), disconnect: vi.fn(), gain: { value: 1 } };
  }
}
const media = () => {
  const track = { stop: vi.fn(), onended: null as (() => void) | null };
  return {
    track,
    stream: {
      getTracks: () => [track],
      getAudioTracks: () => [track],
    } as unknown as MediaStream,
  };
};
const setup = (capture: () => Promise<MediaStream>) => {
  vi.stubGlobal("navigator", {
    mediaDevices: { getUserMedia: vi.fn(capture) },
  });
  const saved = vi.fn(),
    interrupted = vi.fn();
  return { rec: new PCMRecorder(saved, interrupted), saved, interrupted };
};
beforeEach(() => {
  contexts = [];
  resume = () => Promise.resolve();
  vi.stubGlobal("AudioContext", FakeContext);
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});
describe("bounded capture ownership", () => {
  it("activates audio inside the gesture before waiting for media", async () => {
    const m = media();
    const x = setup(async () => {
      expect(contexts).toHaveLength(1);
      return m.stream;
    });
    expect(await x.rec.start()).toBe(true);
    contexts[0].processor.onaudioprocess!({
      inputBuffer: { getChannelData: () => new Float32Array([0.1, 0.2]) },
    });
    x.rec.stop();
    expect(x.saved).toHaveBeenCalledOnce();
    expect(m.track.stop).toHaveBeenCalledOnce();
    expect(
      new DataView(x.saved.mock.calls[0][0].buffer).getUint32(40, true),
    ).toBe(4);
  });
  it("cancel settles never-ending permission immediately and stops its late stream", async () => {
    const d = deferred<MediaStream>();
    const x = setup(() => d.promise);
    const start = x.rec.start();
    x.rec.cancel();
    expect(await start).toBe(false);
    expect(contexts[0].close).toHaveBeenCalledOnce();
    const late = media();
    d.resolve(late.stream);
    await Promise.resolve();
    expect(late.track.stop).toHaveBeenCalledOnce();
    expect(x.saved).not.toHaveBeenCalled();
  });
  it("a stale stream and resume cannot dispose or save a newer attempt", async () => {
    const d = deferred<MediaStream>(),
      r = deferred<void>();
    resume = () => r.promise;
    let n = 0;
    const fresh = media();
    const x = setup(() =>
      ++n === 1 ? d.promise : Promise.resolve(fresh.stream),
    );
    const old = x.rec.start();
    x.rec.cancel();
    resume = () => Promise.resolve();
    expect(await x.rec.start()).toBe(true);
    const late = media();
    d.resolve(late.stream);
    r.resolve();
    expect(await old).toBe(false);
    expect(fresh.track.stop).not.toHaveBeenCalled();
    expect(contexts[1].close).not.toHaveBeenCalled();
    x.rec.stop();
    expect(x.saved).toHaveBeenCalledOnce();
    expect(late.track.stop).toHaveBeenCalledOnce();
  });
  it.each(["media", "resume"])(
    "bounds never-settled %s without stale capture",
    async (stage) => {
      vi.useFakeTimers();
      const d = deferred<MediaStream>();
      const m = media();
      if (stage === "resume") resume = () => new Promise(() => {});
      const x = setup(() =>
        stage === "media" ? d.promise : Promise.resolve(m.stream),
      );
      const start = x.rec.start();
      const result = expect(start).rejects.toMatchObject({
        name: "TimeoutError",
      });
      await vi.advanceTimersByTimeAsync(PCM_START_TIMEOUT_MS);
      await result;
      if (stage === "media") {
        d.resolve(m.stream);
        await Promise.resolve();
      }
      expect(m.track.stop).toHaveBeenCalledOnce();
      expect(x.saved).not.toHaveBeenCalled();
    },
  );
  it.each(["deny", "missing", "context"])(
    "cleans %s failure and allows retry",
    async (stage) => {
      const m = media();
      const x = setup(async () => {
        if (stage === "deny")
          throw new DOMException("Denied", "NotAllowedError");
        return m.stream;
      });
      if (stage === "missing") vi.stubGlobal("navigator", {});
      if (stage === "context")
        resume = () => Promise.reject(new Error("Context failed"));
      await expect(x.rec.start()).rejects.toBeDefined();
      expect(x.saved).not.toHaveBeenCalled();
      resume = () => Promise.resolve();
      vi.stubGlobal("navigator", {
        mediaDevices: { getUserMedia: async () => media().stream },
      });
      expect(await x.rec.start()).toBe(true);
      x.rec.cancel();
    },
  );
  it("interruption saves captured part exactly once; stale PCM callback is inert", async () => {
    const m = media(),
      x = setup(async () => m.stream);
    await x.rec.start();
    const callback = contexts[0].processor.onaudioprocess!;
    callback({
      inputBuffer: { getChannelData: () => new Float32Array([0.2]) },
    });
    m.track.onended!();
    callback({
      inputBuffer: { getChannelData: () => new Float32Array([0.3]) },
    });
    expect(x.saved).toHaveBeenCalledOnce();
    expect(x.interrupted).toHaveBeenCalledWith("TRACK_ENDED");
  });
});
