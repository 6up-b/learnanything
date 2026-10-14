// One verb to start: Add (docs/specs/ux_learnloop_v1.md §6.2, wireframes W1 and
// §8.2). Drop a file anywhere, choose files, or paste a link — nothing to fill
// in. Every choice the old flow asked up front lives under "More options".

import { useCallback, useEffect, useRef, useState, type CSSProperties, type KeyboardEvent } from "react";
import { api } from "../api/client";
import type { AddSourceItemDto, AddSourceResultDto } from "../api/dto";
import { plainError } from "../copy/ingestErrors";
import { COLOR, FONT_MONO } from "./term";
import { pickSourceFiles } from "./useSourceFileDrop";

export type AddOptions = {
  pages?: string;
  problemSet?: boolean;
  keepLocal?: boolean;
  textRecognition?: boolean;
};

export const KINDS_LINE = "PDF · image · web page · arXiv · YouTube · Markdown · text · subtitles";

const buttonStyle: CSSProperties = {
  background: "transparent",
  border: `1px solid ${COLOR.borderStrong}`,
  borderRadius: 3,
  color: COLOR.text,
  fontFamily: FONT_MONO,
  fontSize: 12,
  padding: "5px 12px",
  cursor: "pointer"
};

const linkButtonStyle: CSSProperties = {
  background: "none",
  border: "none",
  padding: 0,
  color: COLOR.amberLink,
  fontFamily: FONT_MONO,
  fontSize: 11,
  cursor: "pointer",
  textDecoration: "underline",
  textUnderlineOffset: 2
};

export function AddSourceBox({
  onAdd,
  busy = false,
  message = null,
  size = "compact",
  dragging = false,
  autoFocus = false
}: {
  onAdd: (sources: string[], options: AddOptions) => void;
  busy?: boolean;
  /** One plain line about the last Add (already in your library, can't open this…). */
  message?: string | null;
  /** "hero" is the empty Library's welcome (W1); "compact" the popover and shelf foot. */
  size?: "hero" | "compact";
  dragging?: boolean;
  autoFocus?: boolean;
}) {
  const [link, setLink] = useState("");
  const [moreOpen, setMoreOpen] = useState(false);
  const [pages, setPages] = useState("");
  const [problemSet, setProblemSet] = useState(false);
  const [keepLocal, setKeepLocal] = useState(false);
  const [textRecognition, setTextRecognition] = useState(false);
  const [pickerMessage, setPickerMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (autoFocus) inputRef.current?.focus();
  }, [autoFocus]);

  const options = useCallback((): AddOptions => {
    const chosen: AddOptions = {};
    if (pages.trim()) chosen.pages = pages.trim();
    if (problemSet) chosen.problemSet = true;
    if (keepLocal) chosen.keepLocal = true;
    if (textRecognition) chosen.textRecognition = true;
    return chosen;
  }, [pages, problemSet, keepLocal, textRecognition]);

  const submit = useCallback(
    (sources: string[]) => {
      const cleaned = sources.map((source) => source.trim()).filter(Boolean);
      if (cleaned.length === 0 || busy) return;
      setPickerMessage(null);
      onAdd(cleaned, options());
      setLink("");
    },
    [busy, onAdd, options]
  );

  const choose = async () => {
    try {
      const files = await pickSourceFiles();
      if (files.length > 0) submit(files);
    } catch {
      setPickerMessage("The file chooser didn't open. Paste the file's location instead.");
    }
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      submit([link]);
    }
  };

  const hero = size === "hero";
  const shown = pickerMessage ?? message;
  return (
    <section
      aria-label="Add to your library"
      style={{
        border: `1px ${hero ? "dashed" : "solid"} ${dragging ? COLOR.amber : COLOR.borderStrong}`,
        borderRadius: 4,
        padding: hero ? "34px 36px" : "14px 16px",
        display: "flex",
        flexDirection: "column",
        gap: hero ? 12 : 8,
        alignItems: hero ? "center" : "stretch",
        textAlign: hero ? "center" : "left",
        background: dragging ? COLOR.washAmber : "transparent"
      }}
    >
      <div style={{ fontFamily: FONT_MONO, fontSize: hero ? 16 : 13, color: COLOR.text }}>
        {hero ? "Drop a book, paper or lecture here" : "Add to your library"}
      </div>
      <div style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textFaint }}>{KINDS_LINE}</div>
      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10, justifyContent: hero ? "center" : "flex-start" }}>
        <button type="button" style={buttonStyle} disabled={busy} onClick={() => void choose()}>
          Choose a file…
        </button>
        <span style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>or paste a link</span>
        <input
          ref={inputRef}
          aria-label="Paste a link"
          value={link}
          placeholder="https://… or an arXiv id"
          onChange={(event) => setLink(event.target.value)}
          onKeyDown={onKeyDown}
          style={{
            fontFamily: FONT_MONO,
            fontSize: 12,
            background: COLOR.bgInput,
            border: `1px solid ${COLOR.border}`,
            borderRadius: 3,
            color: COLOR.text,
            padding: "5px 8px",
            minWidth: 220
          }}
        />
        <button type="button" style={buttonStyle} disabled={busy || !link.trim()} onClick={() => submit([link])}>
          {busy ? "Adding…" : "Add"}
        </button>
      </div>
      <div style={{ alignSelf: hero ? "center" : "flex-start" }}>
        <button
          type="button"
          style={linkButtonStyle}
          aria-expanded={moreOpen}
          onClick={() => setMoreOpen((open) => !open)}
        >
          {moreOpen ? "More options ▾" : "More options ▸"}
        </button>
      </div>
      {moreOpen ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 6, alignSelf: "stretch", textAlign: "left", fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
          <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
            Only some pages
            <input
              value={pages}
              placeholder="e.g. 3-27, 31"
              onChange={(event) => setPages(event.target.value)}
              style={{ fontFamily: FONT_MONO, fontSize: 11, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "3px 6px", width: 140 }}
            />
          </label>
          <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input type="checkbox" checked={problemSet} onChange={(event) => setProblemSet(event.target.checked)} />
            This is a past exam or problem set (no reading questions)
          </label>
          <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input type="checkbox" checked={keepLocal} onChange={(event) => setKeepLocal(event.target.checked)} />
            Never send this to an AI
          </label>
          <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input type="checkbox" checked={textRecognition} onChange={(event) => setTextRecognition(event.target.checked)} />
            Read with text recognition
          </label>
        </div>
      ) : null}
      {shown ? (
        <div role="status" style={{ fontFamily: FONT_MONO, fontSize: 11, color: COLOR.textDim }}>
          {shown}
        </div>
      ) : null}
    </section>
  );
}

/** Add's state: call the sidecar, open what can be opened, say the rest in one line. */
export function useAddSource({
  onOpened
}: {
  onOpened: (item: AddSourceItemDto, result: AddSourceResultDto) => void;
  /** Kept for callers that report elsewhere; Add itself never raises a toast. */
  onError?: (message: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const openedRef = useRef(onOpened);
  openedRef.current = onOpened;

  const add = useCallback(async (sources: string[], options: AddOptions = {}): Promise<AddSourceResultDto | null> => {
    setBusy(true);
    setMessage(null);
    try {
      const result = await api.addSource({ sources, ...options });
      const unsupported = result.items.find((item) => item.status === "unsupported" && item.message);
      const existing = result.items.find((item) => item.status === "existing" && item.message);
      // An add that went ahead without something asked for (text recognition
      // that isn't set up) says so plainly (review F9).
      const added = result.items.find((item) => (item.status === "added" || item.status === "queued") && item.message);
      setMessage(unsupported?.message ?? existing?.message ?? added?.message ?? null);
      if (result.opened) openedRef.current(result.opened, result);
      return result;
    } catch (error) {
      setMessage(plainError(error, "LearnLoop couldn't add that.").line);
      return null;
    } finally {
      setBusy(false);
    }
  }, []);

  return { add, busy, message, clearMessage: () => setMessage(null) };
}

/** The small Add panel behind the header's "+ Add" (§8.2). */
export function AddPopover({
  onClose,
  onAdd,
  busy,
  message
}: {
  onClose: () => void;
  onAdd: (sources: string[], options: AddOptions) => void;
  busy: boolean;
  message: string | null;
}) {
  useEffect(() => {
    const onKey = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div
      role="dialog"
      aria-label="Add to your library"
      style={{ position: "fixed", inset: 0, zIndex: 60 }}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 56,
          right: 24,
          width: 460,
          maxWidth: "calc(100vw - 48px)",
          background: COLOR.bgElev,
          border: `1px solid ${COLOR.borderStrong}`,
          borderRadius: 4,
          boxShadow: "0 12px 32px rgba(0,0,0,0.35)"
        }}
      >
        <AddSourceBox onAdd={onAdd} busy={busy} message={message} autoFocus />
      </div>
    </div>
  );
}

/** The full-window drop target while a file is dragged over LearnLoop. */
export function DropOverlay() {
  return (
    <div
      aria-hidden="true"
      style={{
        position: "fixed",
        inset: 12,
        zIndex: 70,
        border: `2px dashed ${COLOR.amber}`,
        borderRadius: 6,
        background: COLOR.washAmber,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        pointerEvents: "none",
        fontFamily: FONT_MONO,
        fontSize: 16,
        color: COLOR.text
      }}
    >
      Drop to add to your library
    </div>
  );
}
