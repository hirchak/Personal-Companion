import { afterEach, describe, expect, it, vi } from "vitest";
import { installBuildHeader } from "./release-compatibility";

afterEach(() => vi.unstubAllGlobals());
function setup(status = 200, body = {}) {
  const original = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => new Response(JSON.stringify(body), { status }));
  const events = new EventTarget();
  const dispatchEvent = vi.fn((e: Event) => events.dispatchEvent(e));
  const win = { fetch: original, dispatchEvent };
  vi.stubGlobal("window", win);
  vi.stubGlobal("location", { href: "http://127.0.0.1:8765/", origin: "http://127.0.0.1:8765" });
  installBuildHeader();
  return { original, win, dispatchEvent };
}
describe("exact release API header", () => {
  it("binds requests while retaining CSRF, body and credentials", async () => {
    const { win, original } = setup();
    await win.fetch("/api/v1/entries", { method: "POST", headers: { "X-CSRF-Token": "ORIGINAL_SYNTHETIC" }, body: "{}", credentials: "same-origin" });
    const init = original.mock.calls[0][1] as RequestInit;
    expect(new Headers(init.headers).get("X-PC-Build")).toBe("DEVELOPMENT");
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("ORIGINAL_SYNTHETIC");
    expect(init.body).toBe("{}");
  });
  it("signals stale requests with a recoverable event", async () => {
    const { win, dispatchEvent } = setup(409, { code: "FRONTEND_UPDATE_REQUIRED" });
    const response = await win.fetch("/api/v1/status");
    expect((await response.json()).code).toBe("FRONTEND_UPDATE_REQUIRED");
    expect(dispatchEvent.mock.calls[0][0].type).toBe("pc-update-required");
  });
  it("does not mistake a domain conflict for release mismatch", async () => {
    const { win, dispatchEvent } = setup(409, { code: "REVISION_CONFLICT" });
    await win.fetch("/api/v1/entries");
    expect(dispatchEvent).not.toHaveBeenCalled();
  });
  it("does not add release header to assets or an external origin", async () => {
    const { win, original } = setup();
    await win.fetch("/release.json");
    await win.fetch("https://example.invalid/api/v1/test");
    expect(original.mock.calls.every((c) => c[1] === undefined)).toBe(true);
  });
});
