// Stands in for @tauri-apps/api/window. A browser tab has no native window:
// focus, resize and visibility come from the page's own events; minimize and
// maximize are recorded and change nothing; close runs the close-requested
// handlers the way Tauri does and, when none holds it, tells the bridge the
// window closed (the driver says so in the next observation).
import { note } from "./bridge";
import type { UnlistenFn } from "./event";

type CloseRequestedEvent = { preventDefault: () => void; isPreventDefault: () => boolean };
type CloseHandler = (event: CloseRequestedEvent) => void | Promise<void>;

function windowListener(names: string[], callback: () => void): Promise<UnlistenFn> {
  for (const name of names) window.addEventListener(name, callback);
  return Promise.resolve(() => {
    for (const name of names) window.removeEventListener(name, callback);
  });
}

class BrowserWindow {
  readonly label = "main";
  private closeHandlers = new Set<CloseHandler>();
  private closed = false;

  async isMaximized(): Promise<boolean> {
    return false;
  }
  async isMinimized(): Promise<boolean> {
    return document.visibilityState === "hidden";
  }
  async isVisible(): Promise<boolean> {
    return document.visibilityState !== "hidden";
  }
  async isFocused(): Promise<boolean> {
    return document.hasFocus();
  }
  onResized(callback: () => void): Promise<UnlistenFn> {
    return windowListener(["resize"], callback);
  }
  onScaleChanged(): Promise<UnlistenFn> {
    return Promise.resolve(() => undefined);
  }
  onFocusChanged(callback: (event: { payload: boolean }) => void): Promise<UnlistenFn> {
    const focus = () => callback({ payload: true });
    const blur = () => callback({ payload: false });
    window.addEventListener("focus", focus);
    window.addEventListener("blur", blur);
    return Promise.resolve(() => {
      window.removeEventListener("focus", focus);
      window.removeEventListener("blur", blur);
    });
  }
  onCloseRequested(handler: CloseHandler): Promise<UnlistenFn> {
    this.closeHandlers.add(handler);
    return Promise.resolve(() => {
      this.closeHandlers.delete(handler);
    });
  }
  async minimize(): Promise<void> {
    note("window", { call: "minimize" });
  }
  async toggleMaximize(): Promise<void> {
    note("window", { call: "toggleMaximize" });
  }
  async maximize(): Promise<void> {
    note("window", { call: "maximize" });
  }
  async close(): Promise<void> {
    let prevented = false;
    const event: CloseRequestedEvent = {
      preventDefault: () => {
        prevented = true;
      },
      isPreventDefault: () => prevented,
    };
    await Promise.all([...this.closeHandlers].map((handler) => handler(event)));
    if (!prevented) await this.destroy();
  }
  async destroy(): Promise<void> {
    if (this.closed) return;
    this.closed = true;
    note("window", { call: "destroy" });
  }
}

const current = new BrowserWindow();

export function getCurrentWindow(): BrowserWindow {
  return current;
}
