// The comparing posture (reader workbench RW4a; UX §3.1, §4.5, W9): the
// library answer beside the open source, at half the window, resizable and
// remembered on this device (never under 480 px). Ctrl+Shift+F opens it with
// an ask box (the learner's key, so the box may take focus); Esc peels one
// layer (the peek, then the posture). The source keeps its place.
import { useEffect, useRef, useState } from "react";
import type { LibraryHitDto, ProposedItemDto } from "../../api/dto";
import { COLOR, FONT_MONO } from "../../components/term";
import { MIN_WORKBENCH_WIDTH, SPLIT_STEP, clampSplitWidth } from "../workbench/splitWidth";
import { LibraryAnswer, type LibraryExercisesProps } from "./LibraryAnswer";
import { LIBRARY_COPY, type LibraryAskController } from "./useLibraryAsk";

const WIDTH_KEY = "ll.library.splitWidth";

function readWidth(): number | null {
  try {
    const value = Number(window.localStorage.getItem(WIDTH_KEY) ?? Number.NaN);
    return Number.isFinite(value) ? value : null;
  } catch {
    return null;
  }
}

function writeWidth(width: number): void {
  try {
    window.localStorage.setItem(WIDTH_KEY, String(width));
  } catch {
    /* a per-device preference; the pane works without it */
  }
}

export function LibraryPane({
  ctl,
  compose,
  onCompose,
  onAsk,
  onOpenHit,
  onPracticePick,
  onClose,
  exercises = null,
}: {
  ctl: LibraryAskController;
  /** The ask box's text while composing (null: an answer is shown). */
  compose: string | null;
  onCompose: (text: string) => void;
  onAsk: (query: string) => void;
  onOpenHit: ((hit: LibraryHitDto) => void) | null;
  onPracticePick: ((item: ProposedItemDto, proposalId: string | null) => void) | null;
  onClose: () => void;
  /** RW4b's candidate view (absent while library_exercises is off). */
  exercises?: LibraryExercisesProps | null;
}) {
  const [width, setWidth] = useState(() => clampSplitWidth(readWidth() ?? Math.floor(window.innerWidth / 2), window.innerWidth));
  const inputRef = useRef<HTMLInputElement | null>(null);
  const composing = compose !== null;
  useEffect(() => {
    // Ctrl+Shift+F was the learner's key: the ask box takes the cursor.
    if (composing) window.requestAnimationFrame(() => inputRef.current?.focus({ preventScroll: true }));
  }, [composing]);
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape" || event.defaultPrevented) return;
      event.preventDefault();
      if (ctl.state?.peek) ctl.closePeek();
      else onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [ctl, onClose]);
  const resize = (next: number) => {
    const clamped = clampSplitWidth(next, window.innerWidth);
    setWidth(clamped);
    writeWidth(clamped);
  };
  return (
    <>
      <div
        role="separator"
        aria-orientation="vertical"
        aria-label="resize the library answer"
        aria-valuemin={MIN_WORKBENCH_WIDTH}
        aria-valuenow={width}
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
            event.preventDefault();
            resize(width + (event.key === "ArrowLeft" ? SPLIT_STEP : -SPLIT_STEP));
          }
        }}
        onMouseDown={(event) => {
          event.preventDefault();
          const startX = event.clientX;
          const startWidth = width;
          const onMove = (move: MouseEvent) => resize(startWidth + (startX - move.clientX));
          const onUp = () => {
            window.removeEventListener("mousemove", onMove);
            window.removeEventListener("mouseup", onUp);
          };
          window.addEventListener("mousemove", onMove);
          window.addEventListener("mouseup", onUp);
        }}
        style={{ width: 6, flexShrink: 0, cursor: "col-resize", borderLeft: `1px solid ${COLOR.border}`, background: COLOR.bg }}
      />
      <div data-comparing-pane="" className="ll-scroll" style={{ width, flexShrink: 0, minHeight: 0, height: "100%", overflowY: "auto" }}>
        {composing ? (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              if (compose.trim()) onAsk(compose.trim());
            }}
            style={{ padding: "16px 18px 0", display: "flex", flexDirection: "column", gap: 6 }}
          >
            <span style={{ fontFamily: FONT_MONO, fontSize: 10, letterSpacing: "0.12em", color: COLOR.textDim }}>{LIBRARY_COPY.title}</span>
            <input
              ref={inputRef}
              value={compose}
              onChange={(event) => onCompose(event.target.value)}
              placeholder={LIBRARY_COPY.placeholder}
              aria-label="ask your library"
              style={{ fontFamily: FONT_MONO, fontSize: 12, background: COLOR.bgInput, border: `1px solid ${COLOR.border}`, color: COLOR.text, padding: "5px 10px" }}
            />
            <span style={{ fontFamily: FONT_MONO, fontSize: 10, color: COLOR.textDim }}>↵ ask · {LIBRARY_COPY.close}</span>
          </form>
        ) : null}
        <LibraryAnswer ctl={ctl} onOpenHit={onOpenHit} onPracticePick={onPracticePick} onClose={onClose} exercises={exercises} />
      </div>
    </>
  );
}
