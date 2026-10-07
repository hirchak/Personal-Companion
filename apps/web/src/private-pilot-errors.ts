export class PilotCallError extends Error {
  readonly code: string;

  constructor(code: string) {
    super(code);
    this.name = "PilotCallError";
    this.code = code;
  }
}

export function safePilotErrorCode(value: unknown): string {
  const candidate =
    typeof value === "string"
      ? value
      : value instanceof PilotCallError
      ? value.code
      : value instanceof Error
        ? value.message
        : typeof value === "object" && value !== null && "code" in value
          ? (value as { code?: unknown }).code
          : undefined;
  return typeof candidate === "string" && DISPLAYABLE_CODES.has(candidate)
    ? candidate
    : "LOCAL_SERVICE_UNAVAILABLE";
}

const MESSAGES = {
  DURABLE_CONSENT_REQUIRED:
    "Для цього пристрою потрібна згода. Перегляньте коротке повідомлення й увімкніть AI.",
  PRIVATE_PROVIDER_ROUTE_UNAVAILABLE:
    "Локальний маршрут AI недоступний. Перевірте, чи працює Codex, і повторіть спробу.",
  EXISTING_CHATGPT_AUTH_REQUIRED:
    "У Codex немає доступу до наявного ChatGPT акаунта. Перевірте вхід у Codex і повторіть спробу.",
  PRIVATE_PROVIDER_PROFILE_UNVERIFIED:
    "Профіль AI не вдалося підтвердити. AI залишився вимкненим.",
  PROVIDER_EFFORT_UNSUPPORTED:
    "Наявний маршрут не підтримує потрібний рівень роботи. AI залишився вимкненим.",
  OWNER_SESSION_REQUIRED:
    "Сесію застосунку завершено. Розблокуйте її й повторіть спробу.",
  OWNER_SESSION_CHANGED:
    "Сесія застосунку змінилася. Оновіть сторінку й повторіть спробу.",
  LOCAL_ASR_ASSET_UNAVAILABLE:
    "Локальне розпізнавання недоступне. Запис збережено на пристрої; можна повторити пізніше.",
  LOCAL_ASR_PROFILE_UNVERIFIED:
    "Локальне розпізнавання не пройшло перевірку. Запис збережено на пристрої.",
  CONSENT_VERSION_CHANGED:
    "Умови приватності змінилися. Перегляньте повідомлення й підтвердьте згоду знову.",
  LOCAL_SERVICE_UNAVAILABLE:
    "Локальний сервіс недоступний. Перевірте його стан і повторіть дію.",
} as const;

const DISPLAYABLE_CODES: ReadonlySet<string> = new Set(Object.keys(MESSAGES));

export function pilotErrorMessage(code: string): string {
  return (
    MESSAGES[code as keyof typeof MESSAGES] ??
    "Дію не виконано. Перевірте локальний сервіс і повторіть спробу."
  );
}
