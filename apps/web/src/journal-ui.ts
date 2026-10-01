import type { components } from "./api-schema";
export type Kind = "inbox" | "daily" | "sleep" | "creative";
export type Entry = components["schemas"]["EntryOutput"] & {
  type: Kind;
  tags: string[];
  timezone: string;
  time_precision: "instant" | "date" | "unknown";
};
export const names: Record<Kind, string> = {
  inbox: "Думки",
  daily: "День",
  sleep: "Сон",
  creative: "Творчість",
};
export const typed: Record<Kind, string[]> = {
  inbox: [],
  daily: ["mood_rating", "energy_rating"],
  sleep: ["sleep_start_utc", "wake_at_utc", "sleep_quality"],
  creative: ["creative_kind"],
};
export const blank = () => ({
  type: "inbox" as Kind,
  raw_text: "",
  tags: "",
  timezone: "Europe/Warsaw",
  local_date: "",
  occurred_at_utc: "",
  time_precision: "unknown",
  mood_rating: "",
  energy_rating: "",
  sleep_quality: "",
  sleep_start_utc: "",
  wake_at_utc: "",
  creative_kind: "",
});
export type Draft = ReturnType<typeof blank>;
export const creativeNames: Record<string, string> = {
  idea: "Ідея",
  scene: "Сцена",
  theme: "Тема",
  phrase: "Фраза / діалог",
  shot: "Кадр",
  list: "Список",
  character: "Персонаж",
  reference: "Референс",
  other: "Інше",
};
export const fieldNames: Record<string, string> = {
  mood_rating: "Настрій",
  energy_rating: "Енергія",
  sleep_quality: "Якість відпочинку",
  sleep_start_utc: "Початок за вашою оцінкою",
  wake_at_utc: "Пробудження за вашою оцінкою",
  creative_kind: "Вид ідеї",
};
