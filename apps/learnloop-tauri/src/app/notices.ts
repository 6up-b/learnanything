// The shell's notices (UX Phase 2, docs/specs/ux_learnloop_v1.md §7.9, §10 2.3).
//
// Two kinds (errors.ts `MessageKind`): an error is red, says one sentence and
// offers Try again when the failed action can be retried; a notice is
// neutral, small, at the bottom edge, and leaves by itself a few seconds after
// it is first shown. A notice can name what resolves it ("a session began"),
// and it leaves the moment that happens, shown or not: a notice is true only
// until the thing is done (UX Phase 1 usability round 2: "Begin today's plan
// on Start first." stayed over the Reader and Today after the plan had begun).
// While the Reader has a book open, no notice shows: it is held, unaged, and
// delivered at the next destination (Reader doc S11). Errors still show.
// At most three rows show at once; the list keeps the rest until their turn.
//
// This replaces Phase 1's stopgap. `noticeAfterSessionBegins` is that
// stopgap, kept for `ui.shell = "classic"`, whose single red toast stays
// exactly as it was.
import type { MessageKind } from "../errors";

export const NEEDS_SESSION = {
  plan: "Begin today's plan on Start first.",
  practice: "Start a session before opening practice.",
  redo: "Start a session to begin the redo.",
  quickCheck: "Start a session first: the quick check runs inside a practice session.",
  primed: "Start a session to practice the primed item — it will open automatically.",
  checkMe: "Start a session to take this check on your own — it will open automatically.",
  exercise: "Start a session to work on this exercise — it will open automatically."
} as const;

const SESSION_NOTICES: ReadonlySet<string> = new Set(Object.values(NEEDS_SESSION));

/** Classic shell: the notice to keep once a session has begun (a
 *  session-first notice is resolved). */
export function noticeAfterSessionBegins(current: string | null): string | null {
  return current !== null && SESSION_NOTICES.has(current) ? null : current;
}

// ── The simple shell's notice list ──────────────────────────────────────

/** What can resolve a notice. */
export type NoticeCondition = "session";

export interface ShellNotice {
  id: string;
  kind: MessageKind;
  /** One sentence. */
  text: string;
  /** The sidecar's error code, shown under details. */
  code?: string | null;
  /** Present only when the action can be retried (the error was `retryable`
   *  and the shell knows the action). */
  retry?: (() => void) | null;
  resolvedBy?: NoticeCondition | null;
  /** When it was first on screen (null while held or not yet drawn). */
  shownAt: number | null;
}

export type NoticeInput = Omit<ShellNotice, "id" | "shownAt">;

/** How long a notice stays once it is on screen. Errors stay until dismissed. */
export const NOTICE_TTL_MS = 5000;
/** At most this many rows on screen at once. The list itself keeps every
 *  unresolved error and every notice not yet delivered (Codex review F2: a
 *  cap on the list dropped an error and its Try again, and dropped held
 *  notices before they were ever shown); the rest wait their turn. */
export const MAX_VISIBLE_NOTICES = 3;

let nextId = 0;

export function addNotice(list: ShellNotice[], input: NoticeInput): ShellNotice[] {
  nextId += 1;
  const notice: ShellNotice = { ...input, id: `notice-${nextId}`, shownAt: null };
  // A repeated message shows once, as fresh.
  const rest = list.filter((existing) => !(existing.kind === notice.kind && existing.text === notice.text));
  return [...rest, notice];
}

export function dismissNotice(list: ShellNotice[], id: string): ShellNotice[] {
  return list.filter((notice) => notice.id !== id);
}

/** Drop every notice the condition resolves, held or shown. */
export function resolveNotices(list: ShellNotice[], condition: NoticeCondition): ShellNotice[] {
  const next = list.filter((notice) => notice.resolvedBy !== condition);
  return next.length === list.length ? list : next;
}

/** What is on screen, at most `MAX_VISIBLE_NOTICES` rows in the list's order:
 *  errors first (oldest first), then notices (oldest first) in the rows left;
 *  notices only when not held. Whatever does not fit waits in the list. */
export function visibleNotices(list: ShellNotice[], holding: boolean): ShellNotice[] {
  const errors = list.filter((notice) => notice.kind === "error").slice(0, MAX_VISIBLE_NOTICES);
  const room = MAX_VISIBLE_NOTICES - errors.length;
  const notices = holding || room <= 0 ? [] : list.filter((notice) => notice.kind !== "error").slice(0, room);
  const chosen = new Set([...errors, ...notices].map((notice) => notice.id));
  return list.filter((notice) => chosen.has(notice.id));
}

/** A notice's few seconds run only while it is on screen (Codex review F7:
 *  a notice shown, then held while reading, came back already expired).
 *  Any notice that has left the screen without expiring (held in the
 *  Reader, or pushed off by an error) starts its time again when it
 *  returns. Errors keep their stamp; they never expire by themselves. */
export function restartHidden(list: ShellNotice[], visibleIds: string[]): ShellNotice[] {
  let changed = false;
  const next = list.map((notice) => {
    if (notice.kind === "error" || notice.shownAt === null || visibleIds.includes(notice.id)) return notice;
    changed = true;
    return { ...notice, shownAt: null };
  });
  return changed ? next : list;
}

/** Stamp the first time each of these was on screen. */
export function markShown(list: ShellNotice[], ids: string[], now: number): ShellNotice[] {
  let changed = false;
  const next = list.map((notice) => {
    if (notice.shownAt !== null || !ids.includes(notice.id)) return notice;
    changed = true;
    return { ...notice, shownAt: now };
  });
  return changed ? next : list;
}

/** Drop the notices that have been on screen for their time. A held notice
 *  has not started its time; an error never expires by itself. */
export function expireNotices(list: ShellNotice[], now: number, ttlMs: number = NOTICE_TTL_MS): ShellNotice[] {
  const next = list.filter((notice) => notice.kind === "error" || notice.shownAt === null || now - notice.shownAt < ttlMs);
  return next.length === list.length ? list : next;
}

/** A session-first notice: neutral, and resolved once a session begins. */
export function sessionNotice(need: keyof typeof NEEDS_SESSION): NoticeInput {
  return { kind: "notice", text: NEEDS_SESSION[need], resolvedBy: "session" };
}
