// Stands in for @tauri-apps/api/webview. Dropping a file from the desktop onto
// the window is a native drag the browser tab never receives with a path, so
// the listener registers and never fires; a walk names files with `upload`.
import type { UnlistenFn } from "./event";

class BrowserWebview {
  readonly label = "main";
  onDragDropEvent(): Promise<UnlistenFn> {
    return Promise.resolve(() => undefined);
  }
}

const current = new BrowserWebview();

export function getCurrentWebview(): BrowserWebview {
  return current;
}
