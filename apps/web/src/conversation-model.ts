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
  provenance: "USER_AUTHORED" | "MOCK_SYNTHETIC" | "MODEL_GENERATED";
  synthetic: boolean;
};
export type ConversationPage = {
  conversation: Conversation;
  messages: ChatMessage[];
  next_after: number | null;
  inference_job?: InferenceJob | null;
  responder:
    | "OFF"
    | "MOCK_SYNTHETIC"
    | "LIVE_SYNTHETIC"
    | "OFFLINE_FIXTURE"
    | "PRIVATE_OWNER_CONSENTED";
};
export type ConversationStatus = {
  synthetic_demo: boolean;
  responder:
    | "OFF"
    | "MOCK_SYNTHETIC"
    | "LIVE_SYNTHETIC"
    | "OFFLINE_FIXTURE"
    | "PRIVATE_OWNER_CONSENTED";
  actual_asr: string;
  clinical_active: 0;
  live_provider_calls: boolean;
  mode?:
    | "OFF"
    | "LIVE_SYNTHETIC"
    | "OFFLINE_FIXTURE"
    | "PRIVATE_OWNER_CONSENTED";
  provider?: { route: string; model: string; live: boolean };
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
  if (code === "JOURNAL_SELECTION_CHANGED")
    return "Вибраний запис змінився. Оновіть вибрані записи й підтвердьте новий контекст. Повідомлення не надіслано.";
  if (code === "GOAL_REVISION_CHANGED")
    return "Мета має нову редакцію. Почніть глибоку розмову з актуальною метою.";
  if (code === "REVISION_CONFLICT")
    return "Розмова змінилася в іншому вікні. Перегляньте актуальні повідомлення; ваш текст залишився в полі.";
  if (code === "CONVERSATION_DELETED")
    return "Цю розмову вже видалено. Почніть нову.";
  if (
    [
      "PREVIEW_CHANGED",
      "CONTEXT_CHANGED",
      "MAP_CHANGED",
      "SESSION_CHANGED",
      "CONTEXT_PREVIEW_REQUIRED",
      "SOURCE_CHANGED",
    ].includes(code)
  )
    return "Контекст або карта змінилися. Перегляньте їх ще раз; повідомлення лишилося в полі.";
  if (code === "SESSION_NOT_OPEN")
    return "Сесію призупинено або закрито. Поверніться до неї чи почніть наступну.";
  if (code.includes("VOICE_SOURCE") || code.includes("SYNTHETIC_SOURCE"))
    return "Транскрипт змінився або недоступний у цьому режимі. Перевірте його ще раз; текст залишився в полі.";
  return "Не вдалося завершити дію. Текст залишився тут; перевірте локальний сервер і повторіть.";
}

export type InferenceJob = {
  id: string;
  conversation_id: string;
  state: "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED";
  revision: number;
  purpose: string;
  error: string | null;
  partial_candidate?: string | null;
  release_status?: "GENERATING" | "AWAITING_VALIDATION" | "RELEASED" | "FAILED" | "CANCELLED";
  candidate: {
    assistant_text: string;
    source_refs: string[];
    goal_suggestion: string | null;
    closure: {
      discussed: string[];
      clearer: string;
      unresolved: string;
      possible_steps: string[];
    } | null;
    topics: string[];
  } | null;
  request_metadata: {
    provider_route: string;
    provider_model: string;
    retrieval_receipt_id: string;
  };
};
