// Lessons as windows and stack tabs (spec §11.1): the pure part. Where a lesson goes on a desk, what its tab says,
// and the keys a stack's items go by.
//
// A stack's items are its pads (keyed by pad id, as RD4 has them), its lessons (keyed `lesson:<id>`) and lessons
// being opened here (keyed `lesson-opening:<n>`: the opening turn has not returned an id yet, so nothing is stored
// until it has; the tab exists only on this screen meanwhile).
import type { ContentRefDto, DeskOpDto, LessonSummaryDto, LessonViewDto, PadStackEntryDto } from "../../../api/dto";
import { deskById, restampOp, setFocus, type Step, type Workspace } from "../model/workspace";

export const LESSON_KEY = "lesson:";
export const OPENING_KEY = "lesson-opening:";

export function lessonKey(lessonId: string): string {
  return `${LESSON_KEY}${lessonId}`;
}

/** The lesson a stack item is, or null for a pad (an opening has no lesson yet: null too). */
export function lessonOfKey(key: string): string | null {
  return key.startsWith(LESSON_KEY) ? key.slice(LESSON_KEY.length) : null;
}

export function isLessonItem(key: string): boolean {
  return key.startsWith(LESSON_KEY) || key.startsWith(OPENING_KEY);
}

/** A stack's items in order: its own entries (pads and lessons), pads an earlier build added through the view, then
 * the lessons being opened into it here. */
export function stackItemKeys(stack: PadStackEntryDto[], view: Record<string, unknown> | undefined, openings: readonly string[] = []): string[] {
  const own = stack.map((entry) => (entry.kind === "pad" ? entry.padId : lessonKey(entry.lessonId)));
  const added = Array.isArray(view?.addedPads) ? (view?.addedPads as unknown[]).filter((id): id is string => typeof id === "string") : [];
  const shown = [...own, ...added.filter((id) => !own.includes(id))];
  return [...shown, ...openings.filter((key) => !shown.includes(key))];
}

/** "Teacher lesson · <topic>" (spec §11.1). */
export function lessonTabTitle(topic: string | null | undefined): string {
  const words = (topic ?? "").trim();
  return words ? `Teacher lesson · ${words}` : "Teacher lesson";
}

const MADE_FROM: Record<LessonSummaryDto["madeFrom"], string> = {
  selection: "from your selection",
  check: "from your check",
  question: "from your question",
  suggestion: "from today's suggestion",
  topic: "from your topic",
};

function shortDay(iso: string | null | undefined): string {
  if (!iso) return "";
  const date = new Date(iso.length === 10 ? `${iso}T12:00:00` : iso);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

/** "made <date> from your <what>" (spec §11.1), from what the lesson recorded. */
export function lessonTabMeta(summary: Pick<LessonSummaryDto, "openedAt" | "madeFrom"> | null): string {
  if (!summary) return "";
  const day = shortDay(summary.openedAt);
  return `made${day ? ` ${day}` : ""} ${MADE_FROM[summary.madeFrom]}`;
}

export type LessonMode = "lesson" | "additions";

/** The mode buttons (spec §11.1: review and "your additions" in RD9a; redo and extend are not shown until RD9c). An
 * open lesson is not reviewed but taken, so its first button says "lesson". */
export function modeButtons(closed: boolean): Array<{ mode: LessonMode; label: string }> {
  return [{ mode: "lesson", label: closed ? "review" : "lesson" }, { mode: "additions", label: "your additions" }];
}

export function modeLine(mode: LessonMode, closed: boolean): string {
  if (mode === "additions") return "your own notes under this lesson · every pad insert works here; the lesson stays as the teacher made it";
  return closed ? "Your saved answers and lesson feedback" : "the lesson so far · reply, answer its checks, or stop it here";
}

/** Whether a lesson is a notebook (RD9b's frame shows it); otherwise the window shows the lesson itself. */
export function lessonMedium(view: Pick<LessonViewDto, "medium"> | null): "notebook" | "lesson" {
  return view?.medium === "notebook" ? "notebook" : "lesson";
}

/** Where a lesson already is on a desk: a window of its own, or a stack holding it. */
export function findLesson(ws: Workspace, deskId: string, lessonId: string): { windowId: string; inStack: boolean } | null {
  const desk = deskById(ws, deskId);
  if (!desk) return null;
  for (const windowId of desk.slots.flat()) {
    const window = ws.windows[windowId];
    if (window?.content?.kind === "lesson" && window.content.lessonId === lessonId) return { windowId, inStack: false };
  }
  for (const windowId of desk.slots.flat()) {
    const window = ws.windows[windowId];
    if (window?.kind === "pad_stack" && (window.stack ?? []).some((entry) => entry.kind === "lesson" && entry.lessonId === lessonId)) return { windowId, inStack: true };
  }
  return null;
}

/** The desk's stack a lesson lands in: its first stack window, in slot order. */
export function stackWindowOf(ws: Workspace, deskId: string): string | null {
  const desk = deskById(ws, deskId);
  return desk?.slots.flat().find((windowId) => ws.windows[windowId]?.kind === "pad_stack") ?? null;
}

function pushOp(step: Step, op: DeskOpDto): Step {
  const next = restampOp(step.ws, op);
  return { ...step, ws: next.ws, ops: [...step.ops, next.op] };
}

/** A lesson joins a stack (a union by one entry, as a pad's add_to_stack is) and, unless told not to, the stack
 * takes the focus. */
export function addLessonToStack(ws: Workspace, deskId: string, windowId: string, lessonId: string, options: { focus?: boolean } = {}): Step {
  let step: Step = { ws, ops: [] };
  const window = ws.windows[windowId];
  if (!window?.stack?.some((entry) => entry.kind === "lesson" && entry.lessonId === lessonId)) {
    step = pushOp(step, { op: "add_to_stack", deskId, windowId, entry: { kind: "lesson", lessonId } });
  }
  if (options.focus === false) return step;
  const focus = setFocus(step.ws, deskId, windowId);
  return { ws: focus.ws, ops: [...step.ops, ...focus.ops] };
}

/** The stack a lesson window's content stands for: a lesson in its own slot is a stack of one. */
export function lessonStack(content: Extract<ContentRefDto, { kind: "lesson" }>): PadStackEntryDto[] {
  return [{ kind: "lesson", lessonId: content.lessonId }];
}
