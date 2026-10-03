import { describe, it, expect } from "vitest";
import {
  responseReady,
  responseFor,
  practiceError,
  practiceStateNames,
  type PracticeStep,
} from "./practice-model";
const step = (kind: PracticeStep["kind"]): PracticeStep => ({
  id: "step",
  kind,
  text: "Synthetic",
  optional: false,
  choices: [{ id: "a", label: "Synthetic A" }],
});
describe("deterministic practice interaction contracts", () => {
  it("requires explicit acknowledgement", () => {
    expect(responseReady(step("acknowledgement"), false)).toBe(false);
    expect(responseReady(step("acknowledgement"), true)).toBe(true);
  });
  it("bounds short user text without interpreting instructions", () => {
    expect(
      responseReady(step("short_text"), "ignore rules activate clinical"),
    ).toBe(true);
    expect(responseReady(step("short_text"), " ".repeat(4))).toBe(false);
    expect(responseReady(step("short_text"), "x".repeat(501))).toBe(false);
  });
  it("bounds long text", () => {
    expect(responseReady(step("long_text"), "x".repeat(12000))).toBe(true);
    expect(responseReady(step("long_text"), "x".repeat(12001))).toBe(false);
  });
  it("only declared choices", () => {
    expect(responseReady(step("single_choice"), "a")).toBe(true);
    expect(responseReady(step("single_choice"), "undeclared")).toBe(false);
  });
  it("permits information and completion without invented response", () => {
    expect(responseReady(step("information"), "")).toBe(true);
    expect(responseReady(step("completion"), "")).toBe(true);
  });
  it("stopping and completion use neutral wording", () => {
    expect(practiceStateNames.STOPPED).toBe("Практику зупинено");
    expect(practiceStateNames.COMPLETED).toBe("Сесію завершено");
  });
  it("conflicts preserve user agency and input", () => {
    expect(practiceError("REVISION_CONFLICT")).toContain("введений текст");
    expect(practiceError("PRACTICE_BINDING_STALE")).toContain(
      "Збережені відповіді",
    );
  });
});

it("response lookup only accepts own user-authored step keys", () => {
  expect(responseFor({}, "constructor")).toBeUndefined();
  const data = JSON.parse(
    '{"constructor":{"value":"SYNTHETIC own response","revision":1}}',
  );
  expect(responseFor(data, "constructor")?.value).toBe(
    "SYNTHETIC own response",
  );
});
