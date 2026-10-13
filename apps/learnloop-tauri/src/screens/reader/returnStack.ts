// The Reader's return stack (reader workbench RW1a; UX §3.2, §4.2; gate G57).
//
// Every detour -- a branch question, a peek at a cited or suggested passage,
// another source opened from a search -- pushes an entry. Alt+← and Alt+→
// walk the stack like an editor's back and forward; the first entry is always
// "where I was before this detour" (the restored position and selection).
// It is Reader UX state for the visit, not source truth (P3 §12): a restart
// restores only its root, which is P3's saved reading position.
import type { ReaderSelection } from "./readerShared";

export type DetourKind = "branch" | "peek" | "citation" | "source";
export type RailTab = "guide" | "ask" | "notes";

export interface ReturnEntry {
  id: string;
  kind: "origin" | DetourKind;
  sourceId: string;
  sourceTitle: string | null;
  extractionId: string;
  spanId: string | null;
  selection: ReaderSelection | null;
  railTab: RailTab;
  /** A branch entry's exchange (its readerAnswerEventId). */
  exchangeId: string | null;
  label: string;
  /** Milliseconds since the epoch when the entry was pushed. */
  openedAt: number;
}

export interface ReturnStack {
  entries: ReturnEntry[];
  /** Index of the current position; -1 when empty. */
  cursor: number;
  /** Detours already walked back to their origin (each is returned once, however
   *  often the learner walks forward and back again). */
  returned?: readonly string[];
}

export const EMPTY_STACK: ReturnStack = { entries: [], cursor: -1 };

/** A detour exists while the stack holds more than its root. */
export function hasDetour(stack: ReturnStack): boolean {
  return stack.entries.length > 1;
}

export function canGoBack(stack: ReturnStack): boolean {
  return stack.cursor > 0;
}

export function canGoForward(stack: ReturnStack): boolean {
  return stack.cursor >= 0 && stack.cursor < stack.entries.length - 1;
}

/**
 * Push a detour. The first push also records the origin. Pushing from an
 * earlier position drops the forward entries, as an editor's history does.
 * Pushing the entry already current (same kind, span and exchange) is a no-op.
 */
export function pushDetour(stack: ReturnStack, origin: ReturnEntry, entry: ReturnEntry): ReturnStack {
  if (stack.entries.length === 0) {
    return { entries: [{ ...origin, kind: "origin" }, entry], cursor: 1 };
  }
  const current = stack.entries[stack.cursor];
  if (
    current
    && current.kind === entry.kind
    && current.sourceId === entry.sourceId
    && current.spanId === entry.spanId
    && current.exchangeId === entry.exchangeId
  ) {
    return stack;
  }
  const entries = [...stack.entries.slice(0, stack.cursor + 1), entry];
  return { ...stack, entries, cursor: entries.length - 1 };
}

/** Move to ``index`` (a crumb press); returns the new stack and its target. */
export function goTo(stack: ReturnStack, index: number): { stack: ReturnStack; target: ReturnEntry | null } {
  if (index < 0 || index >= stack.entries.length || index === stack.cursor) return { stack, target: null };
  return { stack: { ...stack, cursor: index }, target: stack.entries[index] };
}

export function back(stack: ReturnStack): { stack: ReturnStack; target: ReturnEntry | null } {
  return canGoBack(stack) ? goTo(stack, stack.cursor - 1) : { stack, target: null };
}

export function forward(stack: ReturnStack): { stack: ReturnStack; target: ReturnEntry | null } {
  return canGoForward(stack) ? goTo(stack, stack.cursor + 1) : { stack, target: null };
}

/** The inquiry the stack is about: the first branch entry's exchange. */
export function stackInquiryExchange(stack: ReturnStack): string | null {
  return stack.entries.find((entry) => entry.kind === "branch" && entry.exchangeId)?.exchangeId ?? null;
}

/** The detours opened since the origin. */
export function openDetours(stack: ReturnStack): ReturnEntry[] {
  return stack.entries.slice(1);
}

/** The detours not yet walked back to their origin: the funnel's
 *  detour_returned rows on a return (a detour completes once). */
export function unreturnedDetours(stack: ReturnStack): ReturnEntry[] {
  const returned = new Set(stack.returned ?? []);
  return openDetours(stack).filter((entry) => !returned.has(entry.id));
}

/** Mark detours as returned to their origin. */
export function markReturned(stack: ReturnStack, ids: readonly string[]): ReturnStack {
  if (ids.length === 0) return stack;
  return { ...stack, returned: [...new Set([...(stack.returned ?? []), ...ids])] };
}
