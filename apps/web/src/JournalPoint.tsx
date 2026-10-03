import { useRef, useState } from "react";
import { Sheet } from "./Sheet";
import type { ChatMessage } from "./conversation-model";

type Preview = {
  message_id: string;
  source_revision: number;
  created_utc: string;
  raw_text: string;
  preview_hash: string;
};

export function JournalPoint({ csrf, conversationId, messages, onClose }: {
  csrf: string;
  conversationId: string;
  messages: ChatMessage[];
  onClose: () => void;
}) {
  const sources = messages.filter((m) => m.role === "USER" && m.provenance === "USER_AUTHORED");
  const [selected, setSelected] = useState(""), [preview, setPreview] = useState<Preview | null>(null);
  const [agreed, setAgreed] = useState(false), [busy, setBusy] = useState(false);
  const [error, setError] = useState(""), [saved, setSaved] = useState(false);
  const operation = useRef(crypto.randomUUID());
  async function request(action: "preview" | "confirm") {
    if (busy) return;
    const source = sources.find((m) => m.id === selected);
    if (!source || (action === "confirm" && (!preview || !agreed))) return;
    setBusy(true); setError("");
    try {
      const body = action === "preview"
        ? { message_id: source.id, source_revision: source.revision }
        : { message_id: preview!.message_id, source_revision: preview!.source_revision,
            operation_id: operation.current, preview_hash: preview!.preview_hash, user_confirmed: true };
      const r = await fetch(`/api/v1/conversations/${conversationId}/journal-point/${action}`, {
        method: "POST", credentials: "same-origin", cache: "no-store",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf }, body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error();
      if (action === "preview") { setPreview(await r.json()); setAgreed(false); }
      else setSaved(true);
    } catch { setError("Дію не завершено. Перегляньте актуальне повідомлення й повторіть."); }
    finally { setBusy(false); }
  }
  return <Sheet title="Власна думка у щоденник" onClose={onClose}>
    {saved ? <p role="status">Вашу думку збережено у щоденник.</p> : <>
      <p>Оберіть своє повідомлення. Підсумок помічника не буде скопійовано.</p>
      <fieldset disabled={busy}><legend>Ваші повідомлення</legend>
        {sources.map((m) => <label key={m.id} className="journal-point-choice">
          <input type="radio" name="journal-point" value={m.id} checked={selected === m.id}
            onChange={() => { setSelected(m.id); setPreview(null); setAgreed(false); operation.current = crypto.randomUUID(); }} />
          <span>{m.raw_text}</span>
        </label>)}
      </fieldset>
      <button disabled={!selected || busy} onClick={() => void request("preview")}>Переглянути запис</button>
      {preview && <div aria-label="Перегляд запису у щоденник">
        <p className="entry-text">{preview.raw_text}</p>
        <p className="hint">Ваше повідомлення · {new Date(preview.created_utc).toLocaleString("uk-UA")}</p>
        <label><input type="checkbox" checked={agreed} disabled={busy} onChange={(e) => setAgreed(e.target.checked)} /> Я хочу додати саме цей текст у щоденник</label>
        <button disabled={!agreed || busy} onClick={() => void request("confirm")}>Підтвердити запис у щоденник</button>
      </div>}
    </>}
    {error && <p role="alert">{error}</p>}
  </Sheet>;
}
