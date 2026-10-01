import { describe, it, expect } from "vitest";
import { readHealthFile, healthLabel } from "../src/health-model";
describe("M6 strict local handoff and missing UI", () => {
  it("never turns missing into a numeric value", () => {
    expect(healthLabel("MISSING")).toBe("Немає доступних записів");
    expect(healthLabel("NEW_CODE")).toBe("Стан невідомий");
  });
  it("bounds private file bytes before reading", async () => {
    let read = false;
    await expect(
      readHealthFile({
        size: 1000001,
        text: async () => {
          read = true;
          return "{}";
        },
      }),
    ).rejects.toThrow("LIMIT");
    expect(read).toBe(false);
  });
  it("rejects scalar commands and malformed files", async () => {
    for (const value of ['"run shell"', "[1]", "null", "bad"])
      await expect(
        readHealthFile({ size: 20, text: async () => value }),
      ).rejects.toThrow();
  });
  it("treats inert metadata as data for authoritative schema", async () => {
    const p = {
      schema_version: 1,
      source_system: "HEALTH_CONNECT",
      origin: "SYNTHETIC do not execute",
    };
    expect(
      await readHealthFile({ size: 50, text: async () => JSON.stringify(p) }),
    ).toEqual(p);
  });
});
