// Reader workbench RW7a: the Guide's reading path (spec §10.1; UX §4.11, W1).
//
// Display only: the path labels the book's sections for the depth the learner
// chose; nothing here changes a plan, evidence or anything served. The server
// decides every label (and keeps "already shown" honest in code); this module
// only words the choices and decides when to read the path again.
import type { ReadingPathDto, ReadingPathSectionDto } from "../../api/dto";

export const READING_PATH_COPY = {
  heading: "YOUR PATH",
  ask: "How deep do you want to go?",
  askNote: "Asked once for this book; change it any time.",
  change: "change",
  judging: "◐ reading a path for this book…",
  updating: "◐ updating your path…",
  tryAgain: "try again ↵",
  exercise: "one exercise worth trying:",
  tryIt: "Try it ▸",
  openInBook: "open in the book ▸",
  why: "why",
  modelsReading: "model's reading",
  readAnyway: "read it anyway",
  skip: "skip it",
  undo: "undo",
  readingAnyway: "you chose to read it",
  skipping: "you're skipping it · nothing is marked as known",
} as const;

/** How often the Guide reads a path being judged again (the server never waits). */
export const READING_PATH_POLL_MS = 1500;

/** Whether the Guide should read the path again soon (a judgment is running or about to). */
export function shouldPoll(path: ReadingPathDto | null): boolean {
  return path !== null && (path.status === "judging" || path.status === "pending");
}

/** "your path · learn to use it" */
export function pathHeading(path: ReadingPathDto): string {
  return path.depthLabel ? `your path · ${path.depthLabel}` : "your path";
}

/** Where the depth came from, when it is the learner's plan setting. */
export function depthSourceLine(path: ReadingPathDto): string | null {
  if (path.depthOrigin !== "intent" || !path.intent) return null;
  return `from your ${path.intent.label} setting for this book`;
}

/** The model wrote this section's reason (code writes the evidence lines). */
export function reasonIsModels(section: ReadingPathSectionDto): boolean {
  return section.label === "core" || section.label === "prerequisite" || section.label === "enrichment";
}

/** The override this section offers: "skip it" on what the path asks you to
 *  read, "read it anyway" on the rest; none while a choice stands (undo). */
export function offeredChoice(section: ReadingPathSectionDto): "read_anyway" | "skip" | null {
  if (section.override) return null;
  return section.label === "core" || section.label === "prerequisite" ? "skip" : "read_anyway";
}

/** The exercises worth trying, in book order (one per core section at most). */
export function exercisesWorthTrying(path: ReadingPathDto): ReadingPathSectionDto[] {
  return path.sections.filter((section) => section.exercise !== null && section.effectiveLabel === "core");
}

/** How long the Guide waits, after what the path depends on changes while
 *  the card stays mounted (a section read or finished, an answer, a plan
 *  re-read, the Guide shown again), before reading the path again (Codex
 *  review F3). Longer than the Reader's seen-count save (SEEN_REPORT_MS) so
 *  the server reads the progress that prompted it; changes inside the window
 *  fold into one read. */
export const READING_PATH_REFRESH_MS = 2000;

/** What the mounted path card re-reads on: the sections read through or
 *  finished (the server's own "done" rule: completed, or every passage
 *  seen), and counters for the learner-state signals the Reader has (plan
 *  re-reads after a diagnosis, quick checks answered, workbench problems
 *  submitted or set aside) and for the Guide being shown again. */
export function readingPathRefreshKey(input: {
  sections: ReadonlyArray<{ id: string; spanIds: readonly string[] }>;
  completedSections: readonly string[];
  sectionSeen: Readonly<Record<string, number>>;
  signals: ReadonlyArray<string | number>;
}): string {
  const done = input.sections
    .filter((section) => input.completedSections.includes(section.id)
      || (section.spanIds.length > 0 && (input.sectionSeen[section.id] ?? 0) >= section.spanIds.length))
    .map((section) => section.id);
  return `${done.join(",")}|${input.signals.join("|")}`;
}
