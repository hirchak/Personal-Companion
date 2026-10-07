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

  it("allows only explicitly displayable codes", () => {
    expect(safePilotErrorCode("EXISTING_CHATGPT_AUTH_REQUIRED")).toBe(
      "EXISTING_CHATGPT_AUTH_REQUIRED",
    );
    expect(safePilotErrorCode("PROVIDER_CAPABILITY_MISSING")).toBe(
      "LOCAL_SERVICE_UNAVAILABLE",
    );
    expect(safePilotErrorCode("SYNTHETIC_SECRET_TOKEN_ABC123")).toBe(
      "LOCAL_SERVICE_UNAVAILABLE",
    );
    expect(
      safePilotErrorCode(
        "/private/Users/sentinel/.codex/auth.json account=ORIGINAL_SYNTHETIC",
      ),
    ).toBe("LOCAL_SERVICE_UNAVAILABLE");
    expect(pilotErrorMessage("PROVIDER_CAPABILITY_MISSING")).not.toContain(
      "PROVIDER_CAPABILITY_MISSING",
    );
    expect(pilotErrorMessage("SYNTHETIC_SECRET_TOKEN_ABC123")).not.toContain(
      "SYNTHETIC_SECRET_TOKEN_ABC123",
    );
  });
});
