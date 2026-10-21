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
