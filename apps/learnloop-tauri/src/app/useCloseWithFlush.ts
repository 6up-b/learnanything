import { useEffect } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { errorMessage } from "../errors";

/** Every mounted screen's close save still in flight (the practice screen's
 *  draft and a workbench's steps can both be listening): the window goes only
 *  once all of them have landed, whichever listener finishes first. */
const pendingCloseSaves = new Set<Promise<void>>();

/** Save the mounted screen's draft before closing its window. */
export function useCloseWithFlush(
  flushDraft: () => Promise<unknown>,
  onError: (message: string) => void,
  failureMessage = "Could not save the practice draft before closing.",
) {
  useEffect(() => {
    let appWindow: ReturnType<typeof getCurrentWindow>;
    try {
      appWindow = getCurrentWindow();
    } catch {
      // Not in a Tauri window (a browser preview): there is no close to hold.
      return undefined;
    }
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
      const save = (async () => {
        try {
          await flushDraft();
        } catch (error) {
          onError(errorMessage(error, failureMessage));
        }
      })();
      pendingCloseSaves.add(save);
      try {
        await save;
        await Promise.allSettled([...pendingCloseSaves]);
      } finally {
        pendingCloseSaves.delete(save);
        await appWindow.destroy();
      }
    }).then((listener) => {
      if (disposed) listener();
      else unlisten = listener;
    }).catch((error) => {
      if (!disposed) onError(errorMessage(error, "Could not register the close handler."));
    });
    return () => { disposed = true; unlisten?.(); };
  }, [flushDraft, onError, failureMessage]);
}
