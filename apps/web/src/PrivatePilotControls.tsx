import { useEffect, useState } from "react";
export type PilotState = {
  state: "PRIVATE_AI_OFF" | "PRIVATE_AI_OWNER_CONSENTED";
  local_voice: "OFF" | "ON";
  deep_profile: "DEEP_ECONOMICAL" | "DEEP_QUALITY";
};
const acknowledgements = [
  ["text_leaves_mac_for_openai", "Текст надсилається з Mac до OpenAI через мою наявну підписку ChatGPT."],
  ["raw_audio_not_sent", "Аудіо залишається локально; до AI надсилається лише підтверджений текст."],
  ["only_exact_approved_context", "Перед кожним надсиланням я переглядаю точний текст і вибраний контекст."],
  ["retention_not_zero_certified", "Цей маршрут не гарантує нульового зберігання даних провайдером."],
  ["no_provider_fallback", "Автоматичного fallback, PAYG і купівлі credits немає."],
  ["chatgpt_training_off_confirmed", "У ChatGPT Improve the model for everyone вимкнено."],
  ["codex_environments_off_confirmed", "У Codex Include environments вимкнено."],
] as const;
const voiceAcknowledgements = [
  ["local_audio_only", "Лише локальний whisper.cpp; аудіо не завантажується до провайдера."],
  ["review_before_send", "Я перевіряю й за потреби редагую транскрипт перед явним надсиланням."],
  ["manual_audio_deletion_understood", "Аудіозаписи зберігаються локально до мого видалення. Secure erase не гарантується."],
] as const;
export function PrivatePilotControls({csrf,onChanged}:{csrf:string;onChanged:(state:PilotState)=>void}) {
  const [state,setState]=useState<PilotState|null>(null), [checked,setChecked]=useState<Record<string,boolean>>({}), [busy,setBusy]=useState(false), [error,setError]=useState("");
  async function call(path:string,body?:unknown) {
    const r=await fetch("/api/v1/private-pilot/"+path,{method:body?"POST":"GET",credentials:"same-origin",cache:"no-store",headers:body?{"Content-Type":"application/json","X-CSRF-Token":csrf}:{},body:body?JSON.stringify(body):undefined});
    if (!r.ok) throw new Error((await r.json()).code);
    const s=await r.json();setState(s);onChanged(s);return s;
  }
  useEffect(()=>{void call("status").catch(()=>setError("Не вдалося перевірити пілот. Оновіть сторінку."));},[]);
  async function action(path:string,body:unknown) {
    setBusy(true);setError("");try {await call(path,body);}catch {setError("Дію не виконано. Перевірте локальний сервер і точний профіль; автоматичної заміни немає.");}finally {setBusy(false);}
  }
  function checklist(items:typeof acknowledgements|typeof voiceAcknowledgements) {
    return items.map(([key,label])=><label key={key}><input type="checkbox" checked={!!checked[key]} onChange={e=>setChecked(old=>({...old,[key]:e.target.checked}))}/>{label}</label>);
  }
  return <details className="private-pilot-controls">
    <summary>AI {state?.state==="PRIVATE_AI_OWNER_CONSENTED"?"увімкнено для цієї сесії":"вимкнено"} · локальний голос {state?.local_voice==="ON"?"увімкнено":"вимкнено"}</summary>
    <p>Розблокування, перезапуск або відновлення резервної копії не вмикають AI автоматично. Clinical, практики, Health і телефон залишаються вимкненими.</p>
    {state?.state!=="PRIVATE_AI_OWNER_CONSENTED" ? <fieldset disabled={busy}><legend>Моя явна згода на приватний AI</legend>{checklist(acknowledgements)}<button disabled={!acknowledgements.every(([k])=>checked[k])} onClick={()=>void action("acknowledge",{profile_id:"MAC_PRIVATE_AI_VOICE_PILOT_V1",...Object.fromEntries(acknowledgements.map(([k])=>[k,checked[k]]))})}>Увімкнути AI для цієї сесії</button></fieldset> : <label>Профіль глибокої розмови<select disabled={busy} value={state.deep_profile} onChange={e=>void action("deep-profile",{profile:e.target.value})}><option value="DEEP_ECONOMICAL">Економний · Luna / Max</option><option value="DEEP_QUALITY">Якість · Sol 6.1 / High</option></select></label>}
    <p>Звичайна розмова: Luna / High. Для Sol стеля — High. Профіль DEEP обирається явно; автоматичного fallback немає.</p>
    {state?.local_voice!=="ON" && <fieldset disabled={busy}><legend>Локальний голос</legend>{checklist(voiceAcknowledgements)}<button disabled={!voiceAcknowledgements.every(([k])=>checked[k])} onClick={()=>void action("local-voice",Object.fromEntries(voiceAcknowledgements.map(([k])=>[k,checked[k]])))}>Увімкнути локальний голос</button></fieldset>}
    <button disabled={busy||!state||(state.state==="PRIVATE_AI_OFF"&&state.local_voice==="OFF")} onClick={()=>void action("disable",{})}>Вимкнути AI та голос</button>
    {error&&<p role="alert">{error}</p>}
  </details>;
}
