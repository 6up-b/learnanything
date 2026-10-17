// Reader workbench RW2a: the working posture's split (UX S1, W5, W15). The
// workbench takes half the window, resizable and remembered on this device,
// never under 480 px; the book keeps a readable column beside it; below the
// app's 1,040 px breakpoint the sides stack.

export const MIN_WORKBENCH_WIDTH = 480;
/** The narrowest the book's column gets beside the workbench. */
export const MIN_SOURCE_WIDTH = 360;
export const NARROW_BREAKPOINT = 1040;
export const SPLIT_WIDTH_KEY = "ll.workbench.splitWidth";
export const SPLIT_STEP = 24;

export function defaultSplitWidth(windowWidth: number): number {
  return clampSplitWidth(Math.floor(windowWidth / 2), windowWidth);
}

export function clampSplitWidth(width: number, windowWidth: number): number {
  const max = Math.max(MIN_WORKBENCH_WIDTH, windowWidth - MIN_SOURCE_WIDTH);
  return Math.round(Math.min(max, Math.max(MIN_WORKBENCH_WIDTH, width)));
}

export function isNarrow(windowWidth: number): boolean {
  return windowWidth < NARROW_BREAKPOINT;
}

/** The remembered width, or null (storage can be absent or throw). */
export function readSplitWidth(): number | null {
  try {
    const raw = window.localStorage.getItem(SPLIT_WIDTH_KEY);
    const value = raw === null ? Number.NaN : Number(raw);
    return Number.isFinite(value) ? value : null;
  } catch {
    return null;
  }
}

export function writeSplitWidth(width: number): void {
  try {
    window.localStorage.setItem(SPLIT_WIDTH_KEY, String(width));
  } catch {
    // A preference only: the split works without it.
  }
}
