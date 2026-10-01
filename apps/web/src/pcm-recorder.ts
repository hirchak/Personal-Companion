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
export class PCMRecorder {
  private stream: MediaStream | null = null;
  private context: AudioContext | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private processor: ScriptProcessorNode | null = null;
  private gain: GainNode | null = null;
  private chunks: Float32Array[] = [];
  private frames = 0;
  private paused = false;
  private active = false;
  private generation = 0;
  constructor(
    private stopped: (audio: Uint8Array, reason: string) => void,
    private interrupted: (reason: string) => void,
  ) {}
  async start() {
    const generation = ++this.generation;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
        video: false,
      });
      if (generation !== this.generation) {
        stream.getTracks().forEach((t) => t.stop());
        return false;
      }
      this.stream = stream;
      this.context = new AudioContext();
      await this.context.resume();
      if (generation !== this.generation) {
        this.dispose();
        return false;
      }
      this.source = this.context.createMediaStreamSource(stream);
      this.processor = this.context.createScriptProcessor(4096, 1, 1);
      this.gain = this.context.createGain();
      this.gain.gain.value = 0;
      this.chunks = [];
      this.frames = 0;
      this.paused = false;
      this.active = true;
      this.processor.onaudioprocess = (e) => {
        if (!this.active || this.paused) return;
        const input = e.inputBuffer.getChannelData(0),
          remaining = Math.max(0, this.context!.sampleRate * 120 - this.frames);
        const part = new Float32Array(
          input.subarray(0, Math.min(input.length, remaining)),
        );
        if (part.length) {
          this.chunks.push(part);
          this.frames += part.length;
        }
        if (this.frames >= this.context!.sampleRate * 120) this.stop("LIMIT");
      };
      this.source.connect(this.processor);
      this.processor.connect(this.gain);
      this.gain.connect(this.context.destination);
      stream.getAudioTracks().forEach(
        (track) =>
          (track.onended = () => {
            if (this.active) this.stop("TRACK_ENDED");
          }),
      );
      return true;
    } catch (e) {
      this.dispose();
      throw e;
    }
  }
  pause() {
    this.paused = !this.paused;
    return this.paused;
  }
  elapsed() {
    return this.context ? this.frames / this.context.sampleRate : 0;
  }
  stop(reason = "USER_STOP") {
    if (!this.active) return;
    const bytes = pcmWav(this.chunks, this.context!.sampleRate);
    this.active = false;
    this.dispose();
    if (reason !== "USER_STOP") this.interrupted(reason);
    this.stopped(bytes, reason);
  }
  cancel() {
    this.generation++;
    this.active = false;
    this.chunks = [];
    this.dispose();
  }
  private dispose() {
    this.active = false;
    this.processor?.disconnect();
    this.source?.disconnect();
    this.gain?.disconnect();
    this.stream?.getTracks().forEach((t) => {
      t.onended = null;
      t.stop();
    });
    if (this.context) void this.context.close().catch(() => {});
    this.stream = null;
    this.context = null;
    this.processor = null;
    this.source = null;
    this.gain = null;
  }
}
