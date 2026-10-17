import { useEffect } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { errorMessage } from "../errors";

/** Every mounted screen's close save still in flight (the practice screen's
 *  draft and a workbench's steps can both be listening), each resolving to
 *  whether it landed: the window goes only once all of them have landed,
 *  whichever listener finishes first. */
const pendingCloseSaves = new Set<Promise<boolean>>();
/** A close was already held because a save failed: the next one closes
 *  anyway, so the learner, told once, is never trapped in the window. */
let closeHeld = false;

/** What the learner is told when a failed save holds the window open. */
export const CLOSE_HELD_NOTE = "The window stayed open so nothing is lost. Close it again to close anyway.";

/** Save the mounted screen's draft before closing its window. A save that
 *  fails keeps the window open once, with the failure and a way out (RW2a
 *  re-review F8); a second close request closes it. */
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
      // Read before any save settles, so every listener of one request agrees.
      const closeAnyway = closeHeld;
      let ownFailure: string | null = null;
      const save = (async () => {
        try {
          await flushDraft();
          return true;
        } catch (error) {
          ownFailure = errorMessage(error, failureMessage);
          return false;
        }
      })();
      pendingCloseSaves.add(save);
      let landed = false;
      try {
        await save;
        landed = (await Promise.all([...pendingCloseSaves])).every(Boolean);
      } finally {
        pendingCloseSaves.delete(save);
      }
      if (landed || closeAnyway) {
        closeHeld = false;
        await appWindow.destroy();
        return;
      }
      // Something is not saved: the window stays, and this request is over.
      closeHeld = true;
      closing = false;
      if (ownFailure !== null) onError(`${ownFailure} ${CLOSE_HELD_NOTE}`);
    }).then((listener) => {
      if (disposed) listener();
      else unlisten = listener;
    }).catch((error) => {
      if (!disposed) onError(errorMessage(error, "Could not register the close handler."));
    });
    return () => { disposed = true; unlisten?.(); };
  }, [flushDraft, onError, failureMessage]);
}
