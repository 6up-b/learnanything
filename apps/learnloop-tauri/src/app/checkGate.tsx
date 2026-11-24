// The app's side of an inline check (spec §12.6; RD7): while a check is open on the desks, every other place (the old
// Reader, Today, the library, every tool) gives way to a plain choice, go back to the check or set it aside, instead of
// showing material the desks' veils hold. Before the app knows whether a check is open it shows nothing of those places
// either (fail closed); a failed read says so and offers to read again.
import { useSyncExternalStore } from "react";
import type { CheckDesk } from "../screens/desks/checks/controller";

export type CheckGateState = "pending" | "failed" | "open";

/** What the app shows instead of a place: nothing (null) when no check holds it, or the desks are in view. */
export function checkGateOf(checks: CheckDesk | null, onDesks: boolean): CheckGateState | null {
  if (!checks || onDesks) return null;
  const recovery = checks.recovery();
  if (recovery === "pending") return "pending";
  if (recovery === "failed") return "failed";
  return checks.holding() ? "open" : null;
}

export function CheckOpenGate({ state, checks, onBack }: { state: CheckGateState; checks: CheckDesk; onBack: () => void }) {
  useSyncExternalStore(checks.subscribe, checks.getVersion);
  const open = checks.open();
  if (state === "pending") {
    return <div className="placeholder-screen" role="status" data-check-gate="pending">◐ Checking whether a check is open on your desks…</div>;
  }
  if (state === "failed") {
    return (
      <div className="placeholder-screen" role="alert" data-check-gate="failed">
        <div>Couldn't tell whether a check is open on your desks, so nothing is shown yet.</div>
        <button type="button" className="queue-row" style={{ marginTop: 10 }} onClick={() => checks.retryRecovery()}>try again</button>
      </div>
    );
  }
  return (
    <div className="placeholder-screen" role="dialog" aria-label="a check is open" data-check-gate="open">
      <div>A check is open on your desks. Answer it there, or set it aside (it stays due).</div>
      {open?.error ? <div role="alert" style={{ marginTop: 6 }}>{open.error}</div> : null}
      <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
        <button type="button" className="queue-row" onClick={onBack}>back to the check</button>
        <button type="button" className="queue-row" disabled={open?.phase !== "open"} onClick={() => void checks.abandon()}>not now</button>
      </div>
    </div>
  );
}
