export type PracticeState =
  | "ACTIVE"
  | "PAUSED"
  | "COMPLETED"
  | "STOPPED"
  | "BLOCKED_BY_ADMISSION";
export type PracticeItem = {
  module_id: string;
  module_version?: string;
  content_hash?: string;
  title: string;
  description?: string;
  available: boolean;
  synthetic: boolean;
};
export type Catalog = {
  items: PracticeItem[];
  synthetic_demo: boolean;
  synthetic_runnable: number;
  production_active_clinical: number;
  admission_valid: boolean;
};
export type PracticeStep = {
  id: string;
  kind:
    | "information"
    | "acknowledgement"
    | "short_text"
    | "long_text"
    | "single_choice"
    | "completion";
  text: string;
  optional: boolean;
  choices: { id: string; label: string }[];
};
export type PracticeHistory = {
  id: string;
  title: string;
  module_version: string;
  state: PracticeState;
  revision: number;
  started_utc: string;
  provenance: string;
};
export type PracticeSession = PracticeHistory & {
  current_step: string;
  step_number: number | null;
  step_count: number | null;
  current_step_definition: PracticeStep | null;
  responses: Record<string, { value: string | boolean; revision: number }>;
};
export const practiceStateNames: Record<PracticeState, string> = {
  ACTIVE: "Сесію відкрито",
  PAUSED: "Практику призупинено",
  COMPLETED: "Сесію завершено",
  STOPPED: "Практику зупинено",
  BLOCKED_BY_ADMISSION: "Ця версія зараз недоступна",
};
export function responseReady(
  step: PracticeStep,
  value: string | boolean,
): boolean {
  if (step.kind === "information" || step.kind === "completion") return true;
  if (step.kind === "acknowledgement") return value === true;
  if (step.kind === "single_choice")
    return (
      typeof value === "string" && step.choices.some((x) => x.id === value)
    );
  return (
    typeof value === "string" &&
    value.trim().length > 0 &&
    value.length <= (step.kind === "short_text" ? 500 : 12000)
  );
}
export function practiceError(code: string) {
  if (code === "REVISION_CONFLICT")
    return "Сесія змінилася в іншому вікні. Перегляньте актуальний стан; введений текст збережено в цьому полі.";
  if (code === "PRACTICE_DELETED")
    return "Цю сесію вже видалено. Поверніться до каталогу.";
  if (
    code.includes("ADMISSION") ||
    code.includes("BINDING") ||
    code.includes("RECEIPT")
  )
    return "Ця версія зараз недоступна. Збережені відповіді залишаються у вашій історії.";
  if (code === "PRACTICE_RESPONSE_INVALID")
    return "Перевірте відповідь і спробуйте ще раз.";
  return "Операцію не завершено. Введений текст залишається тут; перевірте локальний сервер і повторіть.";
}

export function responseFor(
  responses: PracticeSession["responses"],
  stepId: string,
) {
  return Object.hasOwn(responses, stepId) ? responses[stepId] : undefined;
}
