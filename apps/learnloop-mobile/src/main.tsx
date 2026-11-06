import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { applyTheme, readThemeChoice } from "./shell/theme";
import { pickUpFragmentToken } from "./store/credential";
import { dbBlocked, subscribeDbBlocked } from "./store/db";
import "./styles.css";

async function start(): Promise<void> {
  // Before the first paint, so a manual light or dark choice never flashes the other one.
  applyTheme(readThemeChoice());
  // A pairing link's token is saved before the first render, unless the database is waiting on
  // another tab: then the App says so at once, and the save lands when that tab closes (F2).
  await new Promise<void>((resolve) => {
    const stop = subscribeDbBlocked(() => {
      if (dbBlocked()) done();
    });
    function done() {
      stop();
      resolve();
    }
    void pickUpFragmentToken()
      .catch(() => false)
      .then(done);
  });
  createRoot(document.getElementById("root") as HTMLElement).render(
    <StrictMode>
      <App />
    </StrictMode>
  );
  // The shell works with the desktop asleep (§7). A browser without service workers still runs.
  if (import.meta.env.PROD && "serviceWorker" in navigator) {
    void navigator.serviceWorker.register("/app/sw.js", { scope: "/app/" }).catch(() => undefined);
  }
}

void start();
