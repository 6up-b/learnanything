// Deliverable curriculum C0b: the Guide's slice of a deliverable's path (spec §7.5),
// its overrides (§7.3) and "Am I ready?" (§8.5).
//
// Display only: the server decides every label (code keeps "already shown" honest)
// and every check; this module only words the choices and decides when to read again.
import type { DeliverableLineDto, DeliverableSliceDto } from "../../api/dto";

export const DELIVERABLE_COPY = {
  heading: "YOUR PATH",
  forGoal: (title: string) => `for ${title}`,
  ask: "How deep for this?",
  askNote: "Asked once for this deliverable; change it any time.",
  change: "change",
  scope: "what it covers",
  thisBookAlone: "this book alone",
  backToDeliverable: "back to your deliverable",
  judging: "◐ choosing a path across your books…",
  updating: "◐ updating your path…",
  covering: "◐ checking where your books treat these topics…",
  tryAgain: "try again ↵",
  why: "why",
  modelsReading: "model's reading",
  anotherWay: "another way:",
  useInstead: "use this one instead",
  readAnyway: "read it anyway",
  skip: "skip it",
  checkLater: "I know this — check me later",
  undo: "undo",
  skipping: "you're skipping it · nothing is marked as known",
  readingAnyway: "you chose to read it",
  checkWaiting: "a check on your own is waiting · off your path until then",
  usingInstead: "your choice",
  onPathIn: (title: string, book: string, section: string) => `${title}: on your path in ${book} ${section} ▸`,
  notInBooks: "not in your books yet:",
  notNeededToggle: (count: number) => (count === 1 ? "1 section not needed here" : `${count} sections not needed here`),
  notWhatINeed: "not what I need…",
  notWhatINeedPlaceholder: "say what you need instead",
  send: "send ↵",
  ready: "Am I ready?",
  readyChecks: "add a check on your own for each one not shown yet",
  readyNote: "Readiness is only checks on your own, later: reading never counts.",
} as const;

/** How often the Guide reads a slice being chosen or covered again (the server never waits). */
export const DELIVERABLE_POLL_MS = 1500;

/** Whether the slice should be read again soon: a judgment or coverage is running, or about to. */
export function shouldPollSlice(slice: DeliverableSliceDto | null): boolean {
  if (slice === null) return false;
  return slice.status === "judging" || slice.status === "pending" || Boolean(slice.covering);
}

/** Whether the slice takes the Guide's path card (else RW7a's card shows, today's Guide). */
export function sliceShown(slice: DeliverableSliceDto | null): boolean {
  return slice !== null && slice.status !== "none";
}

/** "for your midterm · learn to use it" */
export function sliceHeading(slice: DeliverableSliceDto): string {
  const title = slice.goal ? DELIVERABLE_COPY.forGoal(slice.goal.title) : "";
  return slice.depthLabel ? `${title} · ${slice.depthLabel}` : title;
}

/** The choice a line offers when the learner has made none: skipping what is on the path,
 *  reading what is off it. Already shown and assumed lines offer "read it anyway". */
export function offeredChoices(line: DeliverableLineDto): Array<"read_anyway" | "skip" | "check_later"> {
  if (line.override) return [];
  if (line.effectiveLabel === "core" || line.effectiveLabel === "prerequisite") return ["skip", "check_later"];
  if (line.effectiveLabel === "already_shown" || line.effectiveLabel === "assumed") return ["read_anyway"];
  return [];
}

/** A section's marker as the learner reads it: "§6.1 Eigenvectors". */
export function sectionMarker(title: string): string {
  return /^\d/.test(title) ? `§${title}` : title;
}

/** The section ref an override names (``extraction_id/section_id``). */
export function sectionRef(section: { extractionId: string; sectionId: string }): string {
  return `${section.extractionId}/${section.sectionId}`;
}
