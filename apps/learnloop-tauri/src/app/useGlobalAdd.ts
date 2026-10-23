// Add from anywhere (docs/specs/ux_learnloop_v1.md §6.2, keys §5.4): Ctrl+O
// chooses files; Ctrl+V with no text field focused adds the link on the
// clipboard. Plain prose on the clipboard is left alone.

import { useEffect, useRef } from "react";
import { isTypingTarget } from "./keyboard";
import { ADD_FILES_CHORD, matchesChord } from "./keymap";

const ARXIV_ID = /^(arxiv:)?\d{4}\.\d{4,5}(v\d+)?$/i;
const LOCAL_FILE = /^(~|\/|[A-Za-z]:\\).+\.(pdf|md|markdown|txt|html?|vtt|srt|mp3|wav|m4a|flac|ogg|oga|opus|aac)$/i;

/** Whether pasted text names something Add can open (a link, an arXiv id or a file path). */
export function looksLikeSource(text: string): boolean {
  const value = (text || "").trim();
  if (!value || /\s/.test(value)) return false;
  return /^https?:\/\/\S+$/i.test(value) || ARXIV_ID.test(value) || LOCAL_FILE.test(value);
}

export function useGlobalAdd({
  enabled,
  onPickFiles,
  onLink
}: {
  enabled: boolean;
  onPickFiles: () => void;
  onLink: (source: string) => void;
}) {
  const handlers = useRef({ onPickFiles, onLink });
  handlers.current = { onPickFiles, onLink };

  useEffect(() => {
    if (!enabled) return;
    const onKey = (event: KeyboardEvent) => {
      // The chord is the shared key map's (UX Phase 2, app/keymap.ts).
      if (matchesChord(ADD_FILES_CHORD, event) && !event.altKey && !event.shiftKey) {
        event.preventDefault();
        handlers.current.onPickFiles();
      }
    };
    const onPaste = (event: Event) => {
      if (isTypingTarget(event.target)) return;
      const clipboard = (event as ClipboardEvent).clipboardData;
      const text = clipboard?.getData("text") ?? clipboard?.getData("text/plain") ?? "";
      if (!looksLikeSource(text)) return;
      event.preventDefault();
      handlers.current.onLink(text.trim());
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("paste", onPaste);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("paste", onPaste);
    };
  }, [enabled]);
}
