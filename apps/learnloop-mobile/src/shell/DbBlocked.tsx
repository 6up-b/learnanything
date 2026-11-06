// The phone's database is being upgraded and another LearnLoop tab still holds the old version
// open (Codex review of V1, F2). The upgrade waits for that tab: it finishes by itself once the tab
// closes, and Retry reloads this one.
import { useSyncExternalStore } from "react";
import { dbBlocked, subscribeDbBlocked } from "../store/db";
import { reloader } from "./freshness";

export const BLOCKED_LINE = "LearnLoop is open in another tab. Close the other LearnLoop tabs to continue.";

export function useDbBlocked(): boolean {
  return useSyncExternalStore(subscribeDbBlocked, dbBlocked, dbBlocked);
}

export function DbBlockedScreen() {
  return (
    <div className="shell">
      <main className="frame">
        <div className="screen">
          <p role="status">{BLOCKED_LINE}</p>
          <div className="actions">
            <button className="primary block" type="button" onClick={() => reloader.reload()}>Retry</button>
          </div>
        </div>
      </main>
    </div>
  );
}
