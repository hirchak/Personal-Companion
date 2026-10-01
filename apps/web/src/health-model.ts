export type HealthType = "sleep" | "steps" | "exercise";
export type HealthStatus = {
  connection: string;
  permissions: Record<HealthType, string>;
  availability: Record<HealthType, string>;
  last_import: string | null;
  generation: string;
  steps_aggregate: "UNRESOLVED";
  read_only: boolean;
};
export const healthNames: Record<HealthType, string> = {
  sleep: "Сон",
  steps: "Кроки",
  exercise: "Активності",
};
export const healthLabels: Record<string, string> = {
  GRANTED: "Читання дозволено",
  PERMISSION_DENIED: "Читання не дозволено",
  READ_FAILED: "Читання не завершено",
  NOT_REQUESTED: "Дозвіл не запитано",
  NOT_AVAILABLE: "Недоступно",
  VALUE: "Дані доступні",
  MISSING: "Немає доступних записів",
  UNKNOWN: "Доступність невідома",
  CONNECTED: "Локальну копію оновлено",
  PARTIAL_OR_DENIED: "Частковий доступ",
  SOURCE_RECONNECT_REQUIRED: "Потрібне явне підключення",
  SOURCE_DELETED: "Видалено в джерелі",
};
export function healthLabel(code: string) {
  return healthLabels[code] ?? "Стан невідомий";
}
export async function readHealthFile(file: Pick<File, "size" | "text">) {
  if (file.size > 1000000) throw new Error("HEALTH_BATCH_LIMIT");
  const parsed: unknown = JSON.parse(await file.text());
  // The authoritative strict schema is server-side; never treat file data as instructions.
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed))
    throw new Error("HEALTH_SCHEMA_INVALID");
  return parsed;
}
