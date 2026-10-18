// Reader workbench RW2b: the help ladder's pure parts (spec §5.2-5.5; UX
// §4.10, §5.4-5.8, §5.11). Every fixed line the check column, the ladder,
// the hints under their steps, the feedback box and the stuck box show, the
// "where this goes" table, and the ladder's choose/take state. Honest
// labels, no jargon, never a judgment of the learner (G-H12's lint reads
// these too).
import type { CheckViewDto, HelpSuggestionDto, LadderRungDto, WorkbenchHintViewDto } from "../../api/dto";

export const HELP_COPY = {
  check: "check my work · counts as a hint",
  checkKey: "ctrl+k",
  checking: "reading your steps",
  help: "help",
  helpKey: "ctrl+h",
  ladderTitle: "help · every level is yours",
  suggested: "suggested",
  why: "why?",
  chooseTake: "↑↓ / 1–5 choose · ↵ take · esc close",
  writing: "writing a hint for your work…",
  bridging: "finding the matching step in the book…",
  smallerStep: "a smaller step toward this goal ▸",
  smallerStepKey: "ctrl+shift+h",
  doesntConnect: "this doesn't connect to my work…",
  doesntConnectTitle: "tells LearnLoop the hint missed — the next one adjusts",
  bookWay: "show me the book's way",
  aboutStep: "about step:",
  sayMore: "say more (optional)",
  nextHint: "↵ next hint",
  sameRung: "the next hint stays on this rung · it moves, shrinks, keeps your route or your symbols",
  notGraded: "not graded · counts as a hint",
  answer: "↵ answer",
  skip: "skip to a hint",
  answerBox: "your answer to this question",
  assumptions: "assumptions this uses:",
  editedSinceCheck: "edited since check",
  methodLine: "sympy, with a negative control",
  noSandbox: "symbolic checks aren't available here, so every marker is the model's reading",
  styleLabel: "help:",
  styleThisProblem: "for this problem",
  confidence: "how sure are you? (optional)",
  confidenceSkip: "skip",
  whereThisGoes: "ⓘ where this goes",
} as const;

/** The three help styles in the header (UX §5.11), each with its one line. */
export const STYLE_OPTIONS = [
  { value: "let_me_struggle", label: "struggle", line: "offers the lightest help first: questions and goals to aim for" },
  { value: "balanced", label: "balanced", line: "LearnLoop picks from your history" },
  { value: "guide_me", label: "guide", line: "offers more specific help sooner: next steps, then worked steps" },
] as const;

/** The four "doesn't connect" shortcuts, each saying what it does (UX §5.7). */
export const WORKBENCH_SHORTCUTS = [
  { value: "not_where_stuck", label: "that's not where I'm stuck", does: "the next hint moves to the step you pick, starting from what stands before it" },
  { value: "too_big", label: "too big a jump", does: "the next hint takes a smaller step: a nearer goal, or the next step itself" },
  { value: "learner_route", label: "I'm using a different approach", does: "the next hint stays on your route and says which of your steps it builds on" },
  { value: "notation", label: "the notation", does: "the next hint says the same thing again in your symbols" },
] as const;

/** UX §4.10: what each free-text box's *where this goes* says, and where the
 *  box's text is routed (the learner-text source kind; G62's table test). */
export const WHERE_THIS_GOES = {
  stuck: {
    line: "Kept with this problem. LearnLoop's model may read it to name a gap, such as a prerequisite to look at — never to grade you.",
    routedTo: "workbench_text",
  },
  doesntConnect: {
    line: "Kept with this problem. LearnLoop's model may read it to name a gap, such as a prerequisite to look at — never to grade you.",
    routedTo: "workbench_text",
  },
  discriminating: {
    line: "Kept with this problem. LearnLoop's model may read it to name a gap, such as a prerequisite to look at — never to grade you.",
    routedTo: "workbench_text",
  },
} as const;
export type WhereThisGoesBox = keyof typeof WHERE_THIS_GOES;

/** The five rungs before the chooser answers (UX §5.5): every one takeable. */
export const DEFAULT_RUNGS: LadderRungDto[] = [
  { level: 1, label: "a question about your approach", consequence: "hint", workedHelp: false, discriminating: false },
  { level: 2, label: "point to the first step that doesn't hold yet", consequence: "hint", workedHelp: false, discriminating: false },
  { level: 3, label: "a hint on your step — a goal to aim for, a plan, the next step…", consequence: "hint", workedHelp: false, discriminating: false },
  { level: 4, label: "work a piece of it for me, in my notation", consequence: "worked help ◌", workedHelp: true, discriminating: false },
  { level: 5, label: "walk me through the rest, keeping my route", consequence: "worked help ◌", workedHelp: true, discriminating: false },
];

/** The offered rung's line once the chooser returns (UX §5.5): its kind in
 *  plain words, and for a goal how far ahead it points. */
export function suggestedLine(suggestion: HelpSuggestionDto | null): string | null {
  if (!suggestion) return null;
  const form = [suggestion.kindLabel, suggestion.horizonLabel].filter(Boolean).join(", ");
  return `${HELP_COPY.suggested}: ${suggestion.level}${form ? ` · ${form}` : ""}`;
}

/** The choose/take state of an open ladder: digits and arrows choose, Enter
 *  takes, so a stray key never reveals a worked step (no "are you sure?"). */
export interface LadderChoice {
  chosen: number;
}

export function chooseKey(state: LadderChoice, key: string): LadderChoice | "take" | "close" | null {
  if (/^[1-5]$/.test(key)) return { chosen: Number(key) };
  if (key === "ArrowUp") return { chosen: Math.max(1, state.chosen - 1) };
  if (key === "ArrowDown") return { chosen: Math.min(5, state.chosen + 1) };
  if (key === "Enter") return "take";
  if (key === "Escape") return "close";
  return null;
}

/** The verdict a step shows beside it, or null when it was not checked. */
export function verdictFor(check: CheckViewDto | null, chainId: string) {
  return check?.verdicts.find((verdict) => verdict.chainId === chainId) ?? null;
}

/** The bound the server keeps of a checked step's text (its snapshot). */
export const CHECKED_TEXT_CHARS = 2000;

/** The check as it stands against the steps on screen now (review F6): a
 *  step edited since the check dims its marker and joins the stale line at
 *  once, before any save or model call; a step deleted here is stale too. */
export function withLocalEdits(
  check: CheckViewDto | null,
  steps: readonly { chainId: string | null; body: string }[],
): CheckViewDto | null {
  if (!check) return null;
  const bodies = new Map<string, string>();
  for (const step of steps) if (step.chainId) bodies.set(step.chainId, step.body);
  let moved = false;
  const changed = new Set(check.changedSteps);
  const verdicts = check.verdicts.map((verdict) => {
    if (verdict.editedSinceCheck || verdict.checkedText === undefined) return verdict;
    const body = bodies.get(verdict.chainId);
    const edited = body === undefined || body.slice(0, CHECKED_TEXT_CHARS) !== verdict.checkedText;
    if (!edited) return verdict;
    moved = true;
    if (verdict.number !== null) changed.add(verdict.number);
    return { ...verdict, editedSinceCheck: true, deletedSinceCheck: verdict.deletedSinceCheck || body === undefined };
  });
  if (!moved) return check;
  return { ...check, verdicts, stale: true, changedSteps: [...changed].sort((a, b) => a - b) };
}

/** A hint's claim as shown under it (Reader §5.3, review F14). */
export function claimLine(claim: { statement: string; status: string; label: string }): string {
  const mark = claim.status === "model" ? "≈" : "✓";
  return `${mark} ${claim.statement} — ${claim.label}`;
}

/** "checked your steps as of 21:42 — step 3 has changed since" (UX §5.4). */
export function staleLine(check: CheckViewDto | null): string | null {
  if (!check || !check.stale) return null;
  const at = check.checkedAt ? new Date(check.checkedAt) : null;
  const time = at && !Number.isNaN(at.getTime())
    ? `${String(at.getHours()).padStart(2, "0")}:${String(at.getMinutes()).padStart(2, "0")}`
    : "earlier";
  const changed = check.changedSteps.length
    ? check.changedSteps.length === 1
      ? `step ${check.changedSteps[0]} has changed since`
      : `steps ${check.changedSteps.join(", ")} have changed since`
    : "your steps have changed since";
  return `checked your steps as of ${time} — ${changed}`;
}

/** A hint's label line (UX §5.6): who wrote it, its kind in plain words, how
 *  far ahead a goal is, the rung, the step it is about and continues from. */
export function hintLabel(hint: Pick<WorkbenchHintViewDto, "labels" | "level" | "stepLine" | "kind">): string {
  const parts: string[] = [];
  const labels = hint.labels ?? {};
  if (labels.origin === "AI-written") parts.push("◇ model");
  else if (labels.origin) parts.push(labels.origin);
  if (labels.kind && labels.kind !== labels.origin) parts.push(labels.kind);
  if (labels.horizon) parts.push(labels.horizon);
  if (hint.kind === "discriminating") parts.push(HELP_COPY.notGraded);
  parts.push(`level ${hint.level}`);
  if (labels.workedHelp) parts.push(labels.workedHelp);
  if (hint.stepLine) parts.push(hint.stepLine);
  return parts.join(" · ");
}

export const FORBIDDEN_WORDING = ["you don't understand", "you struggle", "weak"] as const;
