import { useState } from "react";
export function MacSyncSettings({ csrf }: { csrf: string }) {
  const [open, setOpen] = useState(false),
    [invitation, setInvitation] = useState(""),
    [devices, setDevices] = useState<any[]>([]),
    [error, setError] = useState("");
  async function call(path: string, body?: unknown) {
    const r = await fetch("/api/v1/sync/" + path, {
      method: body === undefined ? "GET" : "POST",
      cache: "no-store",
      headers:
        body === undefined
          ? {}
          : { "Content-Type": "application/json", "X-CSRF-Token": csrf },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!r.ok) throw new Error((await r.json()).code);
    return r.json();
  }
  async function load() {
    try {
      const d = await call("devices");
      setDevices(d.items);
      setError("");
    } catch {
      setError(
        "Pairing доступний лише в явно запущеному M2 synthetic harness.",
      );
    }
  }
  return (
    <section className="sync-settings">
      <button
        onClick={() => {
          setOpen(!open);
          setInvitation("");
          if (!open) void load();
        }}
      >
        Пристрої та PWA
      </button>
      {open && (
        <div>
          <h2>Синхронізація synthetic пристроїв</h2>
          <p>
            Реальні приватні дані та Android transport gate ще не затверджені.
          </p>
          <a href="/phone/">Відкрити synthetic PWA на цьому браузері</a>
          <div className="actions">
            <button
              onClick={async () => {
                try {
                  const d = await call("invitations", {});
                  setInvitation(d.invitation);
                } catch {
                  setError("Не вдалося створити запрошення.");
                }
              }}
            >
              Створити запрошення
            </button>
          </div>
          {invitation && (
            <div>
              <p>
                Одноразовий код · 5 хвилин. Передайте лише власному synthetic
                клієнту.
              </p>
              <output className="pair-code">{invitation}</output>
              <button onClick={() => setInvitation("")}>Приховати код</button>
            </div>
          )}
          <p>Відкликання блокує новий sync, але не видаляє офлайн копію.</p>
          {devices.map((d) => (
            <article key={d.device_id}>
              <p>
                {d.label} · {d.state}
              </p>
              <button
                disabled={d.state === "REVOKED"}
                onClick={async () => {
                  if (
                    !confirm(
                      "Відкликати доступ? Офлайн копія залишиться на пристрої.",
                    )
                  )
                    return;
                  try {
                    await call("devices/" + d.device_id + "/revoke", {});
                    await load();
                  } catch {
                    setError("Не вдалося відкликати пристрій.");
                  }
                }}
              >
                Відкликати {d.label}
              </button>
            </article>
          ))}
          <button
            onClick={async () => {
              if (
                !confirm(
                  "Змінити sync epoch і відкликати всі зв’язки? Черги потребуватимуть explicit reconciliation/re-pair.",
                )
              )
                return;
              try {
                await call("epoch", {});
                await load();
              } catch {
                setError("Не вдалося змінити epoch.");
              }
            }}
          >
            Змінити sync epoch
          </button>
          {error && <p role="alert">{error}</p>}
        </div>
      )}
    </section>
  );
}
