// Stands in for @tauri-apps/plugin-opener. The app hands a URL to the system
// browser; a walk has none, so the bridge records the URL and the next
// observation says which address would have opened.
import { post } from "./bridge";

export async function openUrl(url: string): Promise<void> {
  await post("/open-url", { url });
}

export async function openPath(path: string): Promise<void> {
  await post("/open-url", { url: path });
}
