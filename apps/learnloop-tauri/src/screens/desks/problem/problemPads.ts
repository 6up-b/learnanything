// An RW2 problem on a pad (spec §15.2, §21.1 "Workbench (RW2a–d): problem pads"): the workbench session a source
// window opened, handed to the desk's problem pad that shows it. The session itself is the workbench's (its steps in
// `workbench_steps`, its help ladder and checks unchanged); this module only carries what the opening knew (the
// session as it came back, the serve it answers, the book it is on) from the window that opened it to the pad that
// hosts it, and what the pad's workbench said since (set aside, abandoned, submitted).
import type { SourceLibraryCard, WorkbenchSessionDto } from "../../../api/dto";

export interface ProblemHandoff {
  session: WorkbenchSessionDto;
  /** A submitted problem, shown with its steps and what it recorded (back from feedback). */
  readOnly: boolean;
  /** Opened by the learner just now: step 1 takes the caret. */
  autoFocus: boolean;
  /** The serve a "check me" answers, kept for the submit. */
  schedulerCandidateId?: string | null;
  planPresentationId?: string | null;
  /** The book the problem is on, and its passage: where the submit's way back returns. */
  card: SourceLibraryCard | null;
  spanId: string | null;
  /** Left for now or abandoned on the pad (the steps are kept either way). */
  away?: "left" | "abandoned" | null;
}

const handed = new Map<string, ProblemHandoff>();
const listeners = new Set<() => void>();

function emit(): void {
  for (const listener of listeners) listener();
}

export function subscribeProblems(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** What the pad of this workbench session shows, or null when nothing was handed over (a pad read after a reload). */
export function problemOf(sessionId: string): ProblemHandoff | null {
  return handed.get(sessionId) ?? null;
}

/** A window opened (or resumed) this problem: its pad shows it. */
export function handOver(handoff: ProblemHandoff): void {
  handed.set(handoff.session.sessionId, { ...handoff, away: null });
  emit();
}

/** The pad's workbench said something of its problem (a newer session, set aside, submitted). */
export function noteProblem(sessionId: string, change: Partial<ProblemHandoff>): void {
  const now = handed.get(sessionId);
  if (!now) return;
  handed.set(sessionId, { ...now, ...change });
  emit();
}

/** Tests only. */
export function resetProblemsForTests(): void {
  handed.clear();
  emit();
}
