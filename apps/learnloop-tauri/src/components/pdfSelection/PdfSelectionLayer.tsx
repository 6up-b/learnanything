// One page's selection and highlight paint on the original PDF
// (reader-pdf-selection). Everything is drawn from the selection model's
// boxes in PDF points times the page's scale, so it follows zoom and resize
// and never depends on where the page happened to be on screen. Static by
// design: nothing here animates (the Reader's attention budget, UX §4.12).
// Only pages near the view mount a layer.

import { memo, type KeyboardEvent as ReactKeyboardEvent } from "react";
import { COLOR, FONT_MONO } from "../term";
import { chipRect, highlightAriaLabel, kindLabel, stateLabel, type HighlightOnPage, type PdfHighlight } from "./highlights";
import type { Box } from "./model";

/** Highlights multiply over the white page like a marker pen: amber for a
 *  plain highlight, violet for every other kind (asks, marks, presets). */
const WASH: Record<"highlight" | "other", { wash: string; strong: string; edge: string }> = {
  highlight: { wash: "rgba(245, 166, 35, 0.24)", strong: "rgba(245, 166, 35, 0.40)", edge: "rgba(215, 135, 15, 0.85)" },
  other: { wash: "rgba(147, 112, 219, 0.20)", strong: "rgba(147, 112, 219, 0.34)", edge: "rgba(120, 85, 200, 0.8)" },
};
const SELECTION_WASH = "rgba(64, 132, 214, 0.28)";

export interface PdfSelectionLayerProps {
  page: number;
  scale: number;
  /** The selection painted on this page (live or held), PDF points. */
  selectionRects: readonly Box[];
  /** Where Shift+arrows extend from after a click on text. */
  caret: Box | null;
  highlights: readonly HighlightOnPage[];
  /** Labels for the highlights by id (kind, state, quote, note). */
  details: ReadonlyMap<string, PdfHighlight>;
  hovered: string | null;
  /** The highlight opened by a click or focused by Tab: lit wherever it is
   *  drawn. */
  active: string | null;
  /** Where its chip shows when that is on this page: the point clicked in it
   *  (PDF points), or null for its first part here (reached by Tab). */
  chip: { id: string; at: { x: number; y: number } | null } | null;
  marqueeRects: readonly number[][];
  marqueeDraft: number[] | null;
  /** A highlight's keyboard stop on this page took the focus (or gave it up). */
  onHighlightFocus: (id: string | null, page: number) => void;
  onHighlightOpen?: (id: string) => void;
  onHighlightRemove?: (id: string) => void;
}

function boxStyle(rect: readonly number[], scale: number, pad = 0) {
  return {
    position: "absolute" as const,
    left: rect[0] * scale - pad,
    top: rect[1] * scale - pad,
    width: Math.max(1, (rect[2] - rect[0]) * scale + 2 * pad),
    height: Math.max(1, (rect[3] - rect[1]) * scale + 2 * pad),
    pointerEvents: "none" as const,
  };
}

export const PdfSelectionLayer = memo(function PdfSelectionLayer({
  page,
  scale,
  selectionRects,
  caret,
  highlights,
  details,
  hovered,
  active,
  chip,
  marqueeRects,
  marqueeDraft,
  onHighlightFocus,
  onHighlightOpen,
  onHighlightRemove,
}: PdfSelectionLayerProps) {
  const onStopKey = (id: string) => (event: ReactKeyboardEvent) => {
    if (event.key === "Delete" || event.key === "Backspace") {
      event.preventDefault();
      event.stopPropagation();
      onHighlightRemove?.(id);
    } else if (event.key === "Enter") {
      event.preventDefault();
      event.stopPropagation();
      onHighlightOpen?.(id);
    } else if (event.key === "Escape") {
      event.stopPropagation();
      (event.currentTarget as HTMLElement).blur();
      onHighlightFocus(null, page);
    }
  };
  return (
    <div data-pdf-layer={page} style={{ position: "absolute", inset: 0, pointerEvents: "none", zIndex: 2 }}>
      {highlights.map((entry) => {
        const tone = WASH[entry.kind === "highlight" ? "highlight" : "other"];
        const lit = entry.id === hovered || entry.id === active;
        return entry.rects.map((rect, index) => (
          <div
            key={`${entry.id}-${index}`}
            data-pdf-highlight={entry.id}
            data-highlight-state={entry.state}
            style={{
              ...boxStyle(rect, scale, entry.state === "flagged" ? 3 : 1),
              background: entry.state === "flagged" ? "transparent" : lit ? tone.strong : tone.wash,
              mixBlendMode: "multiply",
              borderRadius: 2,
              border: entry.state === "flagged" ? `1.5px dashed ${tone.edge}` : undefined,
              borderBottom:
                entry.state === "moved" ? `1.5px dashed ${tone.edge}` : entry.state === "flagged" ? `1.5px dashed ${tone.edge}` : undefined,
              outline: entry.id === active ? `1.5px solid ${tone.edge}` : undefined,
            }}
          />
        ));
      })}
      {selectionRects.map((rect, index) => (
        <div
          key={`sel-${index}`}
          data-pdf-selection-rect=""
          style={{ ...boxStyle(rect, scale, 1), background: SELECTION_WASH, mixBlendMode: "multiply", borderRadius: 2 }}
        />
      ))}
      {caret ? (
        <div
          data-pdf-caret=""
          style={{
            position: "absolute",
            left: caret[0] * scale - 1,
            top: caret[1] * scale,
            width: 1.5,
            height: Math.max(8, (caret[3] - caret[1]) * scale),
            background: "rgba(40, 40, 40, 0.85)",
            pointerEvents: "none",
          }}
        />
      ) : null}
      {marqueeRects.map((rect, index) => (
        <div
          key={`mq-${index}`}
          style={{
            ...boxStyle(rect, scale, 2),
            background: "rgba(245, 166, 35, 0.16)",
            border: "1.5px solid rgba(215, 135, 15, 0.9)",
            borderRadius: 3,
            mixBlendMode: "multiply",
          }}
        />
      ))}
      {marqueeDraft ? (
        <div
          style={{
            ...boxStyle(marqueeDraft, scale, 2),
            background: "rgba(245, 166, 35, 0.10)",
            border: "1.5px dashed rgba(215, 135, 15, 0.8)",
            borderRadius: 3,
            mixBlendMode: "multiply",
          }}
        />
      ) : null}
      {/* A keyboard stop per highlight on every page it is drawn on (a
          highlight running on from the page before has one here too, so it
          is reachable wherever it is in view): Tab reaches it, Enter opens
          it, Delete removes it. Never under the pointer. */}
      {highlights.map((entry) => {
        const detail = details.get(entry.id);
        const first = entry.rects[0];
        return (
          <span
            key={`stop-${entry.id}`}
            role="button"
            tabIndex={0}
            data-pdf-ui=""
            data-highlight-stop={entry.id}
            data-highlight-continued={entry.starts ? undefined : ""}
            className="ll-pdf-highlight-stop"
            aria-label={detail ? highlightAriaLabel(detail, !entry.starts) : kindLabel(entry.kind)}
            onFocus={() => onHighlightFocus(entry.id, page)}
            onKeyDown={onStopKey(entry.id)}
            style={{ ...boxStyle(first, scale, 1), pointerEvents: "none", borderRadius: 2 }}
          />
        );
      })}
      {(() => {
        // The open highlight's chip: what it is, why it sits where it does,
        // and its two actions. Above the part that was clicked (or its first
        // part on this page, reached by Tab), inside the page.
        const entry = chip ? highlights.find((candidate) => candidate.id === chip.id) : undefined;
        const detail = entry ? details.get(entry.id) : undefined;
        const first = entry ? chipRect(entry, chip?.at ?? null) : null;
        if (!entry || !detail || !first) return null;
        const state = stateLabel(entry.state);
        const note = detail.note.trim();
        return (
          <div
            data-pdf-ui=""
            data-highlight-chip={entry.id}
            role="group"
            aria-label={kindLabel(detail.kind)}
            style={{
              position: "absolute",
              left: Math.max(0, first[0] * scale),
              top: Math.max(0, first[1] * scale - 4),
              transform: "translateY(-100%)",
              zIndex: 6,
              pointerEvents: "auto",
              maxWidth: 360,
              display: "flex",
              flexDirection: "column",
              gap: 3,
              padding: "4px 7px",
              background: COLOR.bg,
              border: `1px solid ${COLOR.border}`,
              fontFamily: FONT_MONO,
              fontSize: 11,
              color: COLOR.text,
            }}
          >
            <span>
              {kindLabel(detail.kind)}
              {state ? <span style={{ color: COLOR.amberLink }}> · {state}</span> : null}
            </span>
            {note ? <span style={{ color: COLOR.textDim }}>{note.length > 140 ? `${note.slice(0, 140)}…` : note}</span> : null}
            <span style={{ display: "flex", gap: 10 }}>
              {onHighlightOpen ? (
                <button type="button" className="ll-pdf-chip-button" onClick={() => onHighlightOpen(entry.id)}>
                  open note
                </button>
              ) : null}
              {onHighlightRemove ? (
                <button type="button" className="ll-pdf-chip-button" onClick={() => onHighlightRemove(entry.id)}>
                  remove
                </button>
              ) : null}
            </span>
          </div>
        );
      })()}
    </div>
  );
});
