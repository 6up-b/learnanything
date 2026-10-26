// Reader CA2 (docs/specs/ux_reader_compare_ask_v1.md §7.1, §15 Q6): the Ask
// panel docked beside the question and the learner's draft, so both stay in
// view while asking. A column at the right, 360 px, resizable and remembered
// (a per-viewer convenience); below 1,040 px a sheet over the lower half, the
// question pinned above. Never a modal over the learner's work.
import { useEffect, useState, type ReactNode } from "react";
import { COLOR } from "./term";

const WIDTH_KEY = "learnloop.askPanelWidth";
const DEFAULT_WIDTH = 360;
const MIN_WIDTH = 280;
const STEP = 24;
/** The shell's narrow breakpoint (UX §3.1), shared with the Reader's split. */
const NARROW_BELOW = 1040;

function storedWidth(): number {
  try {
    const value = Number(window.localStorage.getItem(WIDTH_KEY));
    return Number.isFinite(value) && value >= MIN_WIDTH ? value : DEFAULT_WIDTH;
  } catch {
    return DEFAULT_WIDTH;
  }
}

function remember(width: number): void {
  try {
    window.localStorage.setItem(WIDTH_KEY, String(Math.round(width)));
  } catch {
    // A convenience only: the default width comes back next time.
  }
}

function clamp(width: number): number {
  // Leave the question at least half the window.
  const max = Math.max(MIN_WIDTH, Math.floor(window.innerWidth / 2));
  return Math.min(max, Math.max(MIN_WIDTH, width));
}

export function DockedAsk({ panel, children }: { panel: ReactNode | null; children: ReactNode }) {
  const [width, setWidth] = useState(() => clamp(storedWidth()));
  const [narrow, setNarrow] = useState(() => window.innerWidth < NARROW_BELOW);
  useEffect(() => {
    const onResize = () => {
      setNarrow(window.innerWidth < NARROW_BELOW);
      setWidth((current) => clamp(current));
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  if (!panel) return <>{children}</>;
  const resize = (next: number) => {
    const clamped = clamp(next);
    setWidth(clamped);
    remember(clamped);
  };
  if (narrow) {
    return (
      <>
        <div style={{ flex: "1 1 50%", minHeight: 0, display: "flex", flexDirection: "column" }}>{children}</div>
        <div data-testid="ask-dock" data-layout="sheet"
          style={{ flex: "0 0 50%", minHeight: 0, borderTop: `1px solid ${COLOR.borderStrong}`, background: COLOR.bg }}>
          {panel}
        </div>
      </>
    );
  }
  return (
    <div style={{ flex: 1, minHeight: 0, display: "flex" }}>
      <div style={{ flex: 1, minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column" }}>{children}</div>
      <div
        role="separator"
        aria-orientation="vertical"
        aria-label="resize ask"
        aria-valuenow={width}
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
            event.preventDefault();
            // The panel is on the right: the edge moving left widens it.
            resize(width + (event.key === "ArrowLeft" ? STEP : -STEP));
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
        style={{ width: 5, flexShrink: 0, cursor: "col-resize", borderLeft: `1px solid ${COLOR.border}` }}
      />
      <div data-testid="ask-dock" data-layout="column" style={{ width, flexShrink: 0, minHeight: 0 }}>{panel}</div>
    </div>
  );
}
