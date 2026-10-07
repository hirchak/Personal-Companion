import { describe, expect, it } from "vitest";
import { pilotErrorMessage, safePilotErrorCode } from "./private-pilot-errors";

describe("private pilot activation errors", () => {
  it("maps safe activation codes to recovery instructions", () => {
    expect(pilotErrorMessage("EXISTING_CHATGPT_AUTH_REQUIRED")).toContain(
      "Перевірте вхід у Codex",
    );
    expect(pilotErrorMessage("LOCAL_ASR_ASSET_UNAVAILABLE")).toContain(
      "Запис збережено",
    );
  });

  it("keeps unknown stable codes while suppressing raw exception data", () => {
    expect(safePilotErrorCode("PROVIDER_CAPABILITY_MISSING")).toBe(
      "PROVIDER_CAPABILITY_MISSING",
    );
    expect(
      safePilotErrorCode(
        "/private/Users/sentinel/.codex/auth.json account=ORIGINAL_SYNTHETIC",
      ),
    ).toBe("LOCAL_SERVICE_UNAVAILABLE");
    expect(pilotErrorMessage("PROVIDER_CAPABILITY_MISSING")).not.toContain(
      "auth.json",
    );
  });
});
