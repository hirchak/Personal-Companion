export type VoiceReference = {
  kind: "VOICE_TRANSCRIPT";
  transcript_id: string;
  revision: number;
  audio_hash: string;
  text_hash: string;
};
export type Conversation = {
  id: string;
  title: string;
  state: "ACTIVE" | "ARCHIVED";
  revision: number;
  created_utc: string;
  updated_utc: string;
  synthetic: boolean;
  privacy_class: "PRIVATE_PERSONAL";
  mode: "FREE" | "DEEP";
  goal_binding: { id: string; revision: number } | null;
};
export type ChatMessage = {
  id: string;
  conversation_id: string;
  role: "USER" | "ASSISTANT";
  raw_text: string;
  created_utc: string;
  revision: number;
  provenance: "USER_AUTHORED" | "MOCK_SYNTHETIC";
  synthetic: boolean;
};
export type ConversationPage = {
  conversation: Conversation;
  messages: ChatMessage[];
  next_after: number | null;
  responder: "OFF" | "MOCK_SYNTHETIC";
};
export type ConversationStatus = {
  synthetic_demo: boolean;
  responder: "OFF" | "MOCK_SYNTHETIC";
  actual_asr: string;
  clinical_active: 0;
  live_provider_calls: false;
};
export function validChatText(text: string) {
  return text.trim().length > 0 && text.length <= 12000 && !text.includes("\0");
}
export function sendShortcut(e: {
  key: string;
  ctrlKey: boolean;
  metaKey: boolean;
  isComposing: boolean;
}) {
  return e.key === "Enter" && (e.ctrlKey || e.metaKey) && !e.isComposing;
}
export function chatError(code: string) {
  if (code === "REVISION_CONFLICT")
    return "Розмова змінилася в іншому вікні. Перегляньте актуальні повідомлення; ваш текст залишився в полі.";
  if (code === "CONVERSATION_DELETED")
    return "Цю розмову вже видалено. Почніть нову.";
  if (code.includes("VOICE_SOURCE") || code.includes("SYNTHETIC_SOURCE"))
    return "Транскрипт змінився або недоступний у цьому режимі. Перевірте його ще раз; текст залишився в полі.";
  return "Не вдалося завершити дію. Текст залишився тут; перевірте локальний сервер і повторіть.";
}
