import { useState } from "react";
import { saveCredential } from "../store/credential";

/** §4.2. An app on the home screen keeps storage of its own on iOS, so it pairs here with the manual code. */
export function PairScreen({ waiting }: { waiting: number }) {
  const [code, setCode] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function pair(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      const response = await fetch("/pair", {
        method: "POST",
        credentials: "omit",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: code.trim(), device_label: "Phone" })
      });
      if (!response.ok) throw new Error("refused");
      const paired = (await response.json()) as { token: string; device_id: string; scope: string };
      if (paired.scope !== "app") {
        setMessage("That code is for the Shortcut. Run learnloop-mobile pair --scope app on the desktop.");
        return;
      }
      await saveCredential({ token: paired.token, deviceId: paired.device_id, scope: paired.scope });
    } catch {
      setMessage("That didn't pair. Run learnloop-mobile pair --scope app on the desktop and try the new code.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="main">
      <h1>Pair this phone</h1>
      {waiting > 0 ? <p className="banner">Scan a new token to send {waiting} {waiting === 1 ? "capture" : "captures"}.</p> : null}
      <p className="dim">On the desktop, run <code>learnloop-mobile pair --scope app</code>, then enter its manual code.</p>
      <form onSubmit={(event) => void pair(event)}>
        <label htmlFor="pair-code">Manual code</label>
        <input id="pair-code" value={code} onChange={(event) => setCode(event.target.value)} autoComplete="off" autoCapitalize="characters" maxLength={10} />
        <div className="row">
          <button className="primary" type="submit" disabled={busy || code.trim().length === 0}>Pair</button>
        </div>
      </form>
      {message ? <p className="bad" role="status">{message}</p> : null}
    </div>
  );
}
