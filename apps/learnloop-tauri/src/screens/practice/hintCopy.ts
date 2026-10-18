// Adaptive hints H2b: every fixed string the practice screen's hint panel
// shows (spec_adaptive_hints_v1 §4.8; the Reader's plain words, UX §5.6, §5.7,
// §5.8, §5.11). One place, so G-H12's wording lint reads them all: honest
// labels, no jargon, never a judgment of the learner. The kind labels
// themselves come from the sidecar (`result.labels`, learnloop.hints.kinds).
import type { HelpStyle, HintShortcut } from "../../api/dto";

export const HINT_COPY = {
  writing: "Writing a hint for your work…",
  authoredInstead: "use the item's hint instead",
  doesntConnect: "this doesn't connect to my work…",
  doesntConnectTitle: "tells LearnLoop the hint missed — the next one adjusts",
  bookWay: "show me the book's way",
  smallerStep: "a smaller step toward this goal",
  pickLines: "the part of your answer you mean (optional):",
  sayMore: "say more (optional)",
  nextHint: "↵ next hint",
  notGraded: "not graded · counts as a hint",
  answerBox: "your answer to this question",
  answer: "↵ answer",
  skip: "skip to a hint",
  menu: "⋯",
  menuLabel: "help style",
  menuNote: "changes only which hint LearnLoop offers first; every hint stays available",
  fromTheItem: "from the item",
  panelLabel: "hints for your work",
} as const;

/** The four "doesn't connect" shortcuts, each saying what it does (UX §5.7). */
export const SHORTCUT_COPY: ReadonlyArray<{ value: HintShortcut; label: string; does: string }> = [
  {
    value: "not_where_stuck",
    label: "that's not where I'm stuck",
    does: "the next hint moves to the part you pick, starting from what stands before it",
  },
  {
    value: "too_big",
    label: "too big a jump",
    does: "the next hint takes a smaller step: a nearer goal, or the next step itself",
  },
  {
    value: "learner_route",
    label: "I'm using a different approach",
    does: "the next hint stays on your route and says which part of your work it builds on",
  },
  {
    value: "notation",
    label: "the notation",
    does: "the next hint says the same thing again in your symbols",
  },
];

/** The help styles, each with its one line (UX §5.11). */
export const HELP_STYLE_COPY: ReadonlyArray<{ value: HelpStyle; label: string; line: string }> = [
  { value: "let_me_struggle", label: "let me struggle", line: "offers the lightest help first: questions and goals to aim for" },
  { value: "balanced", label: "balanced", line: "LearnLoop picks from your history" },
  { value: "guide_me", label: "guide me", line: "offers more specific help sooner: next steps, then worked steps" },
];

/** G-H12: phrases no hint label or line ever uses (mirrors
 *  learnloop.hints.kinds.FORBIDDEN_WORDING). */
export const FORBIDDEN_WORDING = ["you don't understand", "you struggle", "weak"] as const;
