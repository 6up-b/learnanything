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
      if (disposed || closing) return;
      event.preventDefault();
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
