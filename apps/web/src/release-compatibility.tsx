import React, { useEffect, useState } from "react";
declare const __PC_BUILD_ID__: string;
const eventName = "pc-update-required";

// Every surface shares this boundary, including existing fetch callers and phone sync.
// Historical phone storage stays encrypted at schema 2; mismatch never clears storage.
export function installBuildHeader() {
  const original = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const url = new URL(input instanceof Request ? input.url : String(input), location.href);
    if (url.origin !== location.origin || !url.pathname.startsWith("/api/"))
      return original(input, init);
    const headers = new Headers(init?.headers ?? (input instanceof Request ? input.headers : undefined));
    headers.set("X-PC-Build", __PC_BUILD_ID__);
    const response = await original(input, { ...init, headers });
    if (response.status === 409) {
      const body = await response.clone().json().catch(() => ({}));
      if (body.code === "FRONTEND_UPDATE_REQUIRED")
        window.dispatchEvent(new Event(eventName));
    }
    return response;
  };
}

export function CompatibilityBoundary({ children }: { children: React.ReactNode }) {
  const [stale, setStale] = useState(false);
  useEffect(() => {
    const update = () => setStale(true);
    window.addEventListener(eventName, update);
    // Offline phone use remains available; server checks every online API request.
    void fetch("/release.json", { cache: "no-store" })
      .then((r) => r.ok ? r.json() : null)
      .then((r) => { if (r && (r.web_contract !== 2 || (r.git_commit !== "DEVELOPMENT" && r.git_commit !== __PC_BUILD_ID__))) update(); })
      .catch(() => {});
    return () => window.removeEventListener(eventName, update);
  }, []);
  return <>
    {stale && <main className="unlock" role="alert">
      <h1>Потрібно оновити застосунок</h1>
      <p>Відкрита вкладка й локальний сервер мають різні версії. Зміни на сервері призупинено. Чернетки залишаються в цій вкладці.</p>
      <p>Скопіюйте незбережений текст перед перезавантаженням. Для телефонної версії підтвердьте доступне оновлення; за потреби збережіть encrypted recovery.</p>
      <button onClick={() => setStale(false)}>Переглянути чернетку</button>
      <button onClick={() => location.reload()}>Перезавантажити після збереження</button>
    </main>}
    <div hidden={stale}>{children}</div>
  </>;
}
