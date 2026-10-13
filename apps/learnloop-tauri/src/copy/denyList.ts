// The jargon deny-list (docs/specs/ux_learnloop_v1.md §9). Internal terms stay
// in code, specs, Under the hood and the CLI; a learner surface uses the plain
// words of the glossary, or nothing. A test renders every learner surface and
// fails on any match. A term is allowed in a component only through a named
// exemption with a reason: `findJargon(text, { ingest: "why" })`.

export interface DenyTerm {
  /** The internal term, as reported. */
  term: string;
  pattern: RegExp;
  /** What the learner sees instead (glossary right column). */
  plain: string;
}

function term(name: string, plain: string, pattern?: RegExp): DenyTerm {
  return { term: name, plain, pattern: pattern ?? new RegExp(`\\b${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`, "i") };
}

export const DENY_TERMS: readonly DenyTerm[] = [
  term("vault", "library"),
  term("canonical", "book, paper, video, article"),
  term("learning object", "topic"),
  term("LO", "topic", /\bLOs?\b/),
  term("facet", "skill"),
  term("study map", "your map / questions for this book"),
  term("practice item", "question / problem"),
  term("extraction", "getting this book ready"),
  term("extract", "getting this book ready", /\bextract(?!ion)\w*/i),
  term("ingest", "add"),
  term("inventory", "(hidden)"),
  term("synthesis", "(hidden)", /\bsynthes[ie]s\b|\bsynthesi[sz]e/i),
  term("source set", "(hidden)"),
  term("outline & select", "(hidden)", /outline\s*&\s*select/i),
  term("shard", "(hidden)"),
  term("bootstrap", "(hidden)"),
  term("proposal", "AI-written · undo / changes need a look"),
  term("AI inbox", "(hidden)"),
  term("auto_apply", "(hidden)", /auto_apply|review_required/i),
  term("primary_textbook", "main text", /primary_textbook|alternate_explanation|problem_set\b/i),
  term("token", "(hidden)"),
  term("consent", "what leaves this computer"),
  term("registry", "(hidden)"),
  term("probe", "a quick question"),
  term("EVSI", "(hidden)", /\b(EVSI|VOI|EIG)\b/),
  term("entropy", "(hidden)"),
  term("posterior", "(hidden)"),
  term("Brier", "(hidden)"),
  term("calibration", "Check what I already know", /\bcalibrat/i),
  term("mastery", "likely to recall"),
  term("certified", "on your own", /\bcertif/i),
  term("primed", "with help"),
  term("cold check", "a check on your own"),
  term("system debt", "(hidden)", /\b(system|content) debt\b/i),
  term("misconception", "a mix-up"),
  term("hypothesis", "possible causes", /\bhypothes[ie]s\b/i),
  term("rubric", "what the grader looked for"),
  term("blueprint", "problems like this"),
  term("scheduler", "today's plan"),
  term("overdue", "(never)"),
  term("provenance", "from p. N / from §N"),
  term("bbox", "(hidden)"),
  term("manifest", "(hidden)"),
  term("sidecar", "LearnLoop's background service"),
  term("codex", "the provider's product name, in Settings only"),
  term("mvp-0", "(hidden)", /\bmvp-0/i),
  term("adjudication", "(hidden)", /\badjudicat/i),
  term("marker", "text recognition", /\bmarker\b|\bpypdf\b/i),
  term("OCR", "text recognition", /\bOCR\b/)
];

/** The internal terms ``text`` shows, in deny-list order, minus exemptions. */
export function findJargon(text: string, exemptions: Record<string, string> = {}): string[] {
  const allowed = new Set(Object.keys(exemptions).map((name) => name.toLowerCase()));
  return DENY_TERMS.filter((entry) => !allowed.has(entry.term.toLowerCase()) && entry.pattern.test(text)).map(
    (entry) => entry.term
  );
}
