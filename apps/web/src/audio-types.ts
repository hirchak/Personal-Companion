export const AUDIO_CHUNK = 256 * 1024;
export const AUDIO_MAX = 8 * 1024 * 1024;
export type Transcript = {
  id: string;
  audio_id: string;
  audio_hash: string;
  engine: string;
  model: string | null;
  candidate: string | null;
  edited: string | null;
  state: string;
  revision: number;
  entry_id: string | null;
  entry_revision: number | null;
  error: string | null;
};
export type AudioBegin = {
  audio_id: string;
  operation_id: string;
  content_hash: string;
  byte_size: number;
  mime: "audio/wav";
  created_at_utc: string;
  timezone: string;
  local_date: string;
  linked_entry_id: string | null;
};
export type PhoneAudio = {
  begin: AudioBegin;
  state:
    | "LOCAL_AUDIO_SAVED"
    | "UPLOADING"
    | "MAC_AUDIO_CONFIRMED"
    | "MAC_AUDIO_DELETED"
    | "FAILED"
    | "CANCELLED";
  uploaded: number;
  retention: "KEEP" | "DELETE_AFTER_CONFIRM";
  transcript: Transcript | null;
  receipt: {
    content_hash: string;
    byte_size: number;
    state: "MAC_AUDIO_CONFIRMED";
  } | null;
  revision: number;
  cancelPending: boolean;
};
export const audioHash = async (data: Uint8Array) =>
  Array.from(
    new Uint8Array(await crypto.subtle.digest("SHA-256", data as BufferSource)),
    (b) => b.toString(16).padStart(2, "0"),
  ).join("");
export const audioBase64 = (bytes: Uint8Array) => {
  let text = "";
  for (let i = 0; i < bytes.length; i += 8192)
    text += String.fromCharCode(...bytes.subarray(i, i + 8192));
  return btoa(text);
};
export const audioUnbase64 = (text: string) =>
  Uint8Array.from(atob(text), (c) => c.charCodeAt(0));
export function audioBegin(data: Uint8Array): Omit<AudioBegin, "content_hash"> {
  const date = new Date();
  const zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const local = new Intl.DateTimeFormat("en-CA", {
    timeZone: zone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  const field = (k: string) => local.find((x) => x.type === k)?.value;
  return {
    audio_id: crypto.randomUUID(),
    operation_id: crypto.randomUUID(),
    byte_size: data.length,
    mime: "audio/wav",
    created_at_utc: date.toISOString(),
    timezone: zone,
    local_date: `${field("year")}-${field("month")}-${field("day")}`,
    linked_entry_id: null,
  };
}
