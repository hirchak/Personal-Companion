/** Explicit mono PCM16 WAV capture, no codec binary or cloud speech service. */
export function pcmWav(chunks: Float32Array[], sourceRate: number): Uint8Array {
  const total = chunks.reduce((n, c) => n + c.length, 0),
    source = new Float32Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    source.set(chunk, offset);
    offset += chunk.length;
  }
  const rate = 16000,
    count = Math.floor((total * rate) / sourceRate),
    bytes = new Uint8Array(44 + count * 2),
    view = new DataView(bytes.buffer);
  const text = (at: number, s: string) => {
    for (let i = 0; i < s.length; i++) view.setUint8(at + i, s.charCodeAt(i));
  };
  text(0, "RIFF");
  view.setUint32(4, bytes.length - 8, true);
  text(8, "WAVE");
  text(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, rate, true);
  view.setUint32(28, rate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  text(36, "data");
  view.setUint32(40, count * 2, true);
  for (let i = 0; i < count; i++) {
    const at = (i * sourceRate) / rate,
      a = Math.floor(at),
      weight = at - a;
    const value = Math.max(
      -1,
      Math.min(
        1,
        source[a] * (1 - weight) +
          (source[Math.min(a + 1, total - 1)] ?? 0) * weight,
      ),
    );
    view.setInt16(
      44 + i * 2,
      Math.round(value * (value < 0 ? 32768 : 32767)),
      true,
    );
  }
  return bytes;
}
// A person can still answer a normal macOS permission prompt. Cancellation is
// immediate; 45 seconds bounds even a WebKit promise that never settles.
export const PCM_START_TIMEOUT_MS = 45_000;
type CaptureAttempt = {
  context: AudioContext | null;
  stream: MediaStream | null;
  source: MediaStreamAudioSourceNode | null;
  processor: ScriptProcessorNode | null;
  gain: GainNode | null;
  active: boolean;
  abort: () => void;
};
export class PCMRecorder {
  private attempt: CaptureAttempt | null = null;
  private chunks: Float32Array[] = [];
  private frames = 0;
  private paused = false;
  constructor(
    private stopped: (audio: Uint8Array, reason: string) => void,
    private interrupted: (reason: string) => void,
  ) {}
  async start() {
    this.cancel();
    const a: CaptureAttempt = {
      context: null,
      stream: null,
      source: null,
      processor: null,
      gain: null,
      active: false,
      abort: () => {},
    };
    this.attempt = a;
    const cancelled = new Promise<never>((_, reject) => {
      a.abort = () =>
        reject(new DOMException("Capture cancelled", "AbortError"));
    });
    let timer: ReturnType<typeof setTimeout> | undefined;
    const deadline = new Promise<never>((_, reject) => {
      timer = setTimeout(
        () =>
          reject(new DOMException("Capture start timed out", "TimeoutError")),
        PCM_START_TIMEOUT_MS,
      );
    });
    const current = () => this.attempt === a;
    try {
      if (!navigator.mediaDevices?.getUserMedia)
        throw new DOMException("Microphone unavailable", "NotSupportedError");
      // Activate the context synchronously in the explicit record gesture,
      // before waiting for a permission prompt or the synthetic fixture.
      a.context = new AudioContext();
      const resumed = a.context.resume();
      const media = navigator.mediaDevices
        .getUserMedia({
          audio: {
            channelCount: 1,
            echoCancellation: false,
            noiseSuppression: false,
            autoGainControl: false,
          },
          video: false,
        })
        .then((stream) => {
          if (!current()) {
            stream.getTracks().forEach((t) => t.stop());
            return null;
          }
          a.stream = stream;
          return stream;
        });
      await Promise.race([Promise.all([resumed, media]), cancelled, deadline]);
      if (!current()) return false;
      const context = a.context,
        stream = a.stream;
      if (!stream || context.state !== "running")
        throw new DOMException(
          "Audio context unavailable",
          "NotSupportedError",
        );
      a.source = context.createMediaStreamSource(stream);
      a.processor = context.createScriptProcessor(4096, 1, 1);
      a.gain = context.createGain();
      a.gain.gain.value = 0;
      this.chunks = [];
      this.frames = 0;
      this.paused = false;
      a.active = true;
      a.processor.onaudioprocess = (e) => {
        if (!current() || !a.active || this.paused) return;
        const input = e.inputBuffer.getChannelData(0),
          remaining = Math.max(0, context.sampleRate * 120 - this.frames);
        const part = new Float32Array(
          input.subarray(0, Math.min(input.length, remaining)),
        );
        if (part.length) {
          this.chunks.push(part);
          this.frames += part.length;
        }
        if (this.frames >= context.sampleRate * 120) this.stop("LIMIT");
      };
      a.source.connect(a.processor);
      a.processor.connect(a.gain);
      a.gain.connect(context.destination);
      stream.getAudioTracks().forEach((track) => {
        track.onended = () => {
          if (current() && a.active) this.stop("TRACK_ENDED");
        };
      });
      context.onstatechange = () => {
        if (current() && a.active && context.state !== "running")
          this.stop("CONTEXT_INTERRUPTED");
      };
      return true;
    } catch (error) {
      if (current()) this.attempt = null;
      this.dispose(a);
      if (error instanceof DOMException && error.name === "AbortError")
        return false;
      throw error;
    } finally {
      clearTimeout(timer);
    }
  }
  pause() {
    this.paused = !this.paused;
    return this.paused;
  }
  elapsed() {
    return this.attempt?.context
      ? this.frames / this.attempt.context.sampleRate
      : 0;
  }
  stop(reason = "USER_STOP") {
    const a = this.attempt;
    if (!a?.active || !a.context) return;
    const bytes = pcmWav(this.chunks, a.context.sampleRate);
    this.attempt = null;
    this.chunks = [];
    this.dispose(a);
    if (reason !== "USER_STOP") this.interrupted(reason);
    this.stopped(bytes, reason);
  }
  cancel() {
    const a = this.attempt;
    this.attempt = null;
    this.chunks = [];
    if (a) {
      a.abort();
      this.dispose(a);
    }
  }
  private dispose(a: CaptureAttempt) {
    a.active = false;
    if (a.processor) {
      a.processor.onaudioprocess = null;
      a.processor.disconnect();
    }
    a.source?.disconnect();
    a.gain?.disconnect();
    a.stream?.getTracks().forEach((t) => {
      t.onended = null;
      t.stop();
    });
    if (a.context) {
      a.context.onstatechange = null;
      void a.context.close().catch(() => {});
    }
    a.context = null;
    a.stream = null;
    a.processor = null;
    a.source = null;
    a.gain = null;
  }
}
