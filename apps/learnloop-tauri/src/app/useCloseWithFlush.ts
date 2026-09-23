import { useEffect } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { errorMessage } from "../errors";

/** Save the mounted screen's draft before closing its window. */
export function useCloseWithFlush(flushDraft: () => Promise<unknown>, onError: (message: string) => void) {
  useEffect(() => {
    const appWindow = getCurrentWindow();
    let disposed = false;
    let unlisten: (() => void) | undefined;
    let closing = false;
    appWindow.onCloseRequested(async (event) => {
      // A listener whose screen has unmounted has no draft to save; let the window close.
      if (disposed) return;
      // Tauri destroys the window after any handler that does not prevent the close, so a
      // repeated close request must also be prevented while the first flush is still pending.
      event.preventDefault();
      if (closing) return;
      closing = true;
      try {
        await flushDraft();
      } catch (error) {
        onError(errorMessage(error, "Could not save the practice draft before closing."));
      } finally {
        await appWindow.destroy();
      }
    }).then((listener) => {
      if (disposed) listener();
      else unlisten = listener;
    }).catch((error) => {
      if (!disposed) onError(errorMessage(error, "Could not register the close handler."));
    });
    return () => { disposed = true; unlisten?.(); };
  }, [flushDraft, onError]);
}
