export type ObjectId = "vase" | "books" | "print";
export type Space = {
  enabled: boolean;
  theme: "paper" | "sage" | "clay";
  owned_ids: ObjectId[];
  layout: ObjectId[];
};
export const defaultSpace = (): Space => ({
  enabled: false,
  theme: "paper",
  owned_ids: ["vase", "books", "print"],
  layout: ["books", "vase", "print"],
});
export function checkSpace(s: Space) {
  if (
    !s ||
    Object.keys(s).sort().join() !== "enabled,layout,owned_ids,theme" ||
    typeof s.enabled !== "boolean" ||
    !["paper", "sage", "clay"].includes(s.theme) ||
    !Array.isArray(s.layout) ||
    !Array.isArray(s.owned_ids) ||
    [...s.layout].sort().join() !== "books,print,vase" ||
    [...s.owned_ids].sort().join() !== "books,print,vase"
  )
    throw new Error("COSMETIC_SCHEMA_INVALID");
  return s;
}
