import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { applyTheme, readThemeChoice } from "./shell/theme";
import { pickUpFragmentToken } from "./store/credential";
import "./styles.css";

async function start(): Promise<void> {
  // Before the first paint, so a manual light or dark choice never flashes the other one.
  applyTheme(readThemeChoice());
  await pickUpFragmentToken().catch(() => false);
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
