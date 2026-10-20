// Reader workbench RW4b: exercises from my sources (spec §7.4; UX §4.5, §4.6).
//
// The Reader's view of the sources service's textbook-exercise candidates.
// Everything here is display: the candidates come from `find_practice` (S1's
// own kind) or, when nothing fits and the fallback is on, from
// `reader.find_exercises`; which ones may be shown and how each is offered
// come from the server (`reader.exercise_candidates`: the sources service's
// exposure rule, held-out material left out). "Use this one" is a learner
// pick that opens the workbench at once on the verbatim statement while the
// import runs; an exposed exercise opens as practice beside the book, never
// as a check on your own.
import type {
  SourceToolRunDto,
  ExerciseCandidatesDto,
  ExerciseExposureDto,
  FindExercisesDto,
  FindPracticeResultDto,
  ReaderImportExerciseInput,
  WorkbenchEntry,
} from "../../api/dto";

export const EXERCISE_COPY = {
  heading: "from your books",
  verbatim: "from your book · verbatim",
  modelAnswer: "answer completed by LearnLoop's model",
  beforeUse: "checked when you use it",
  use: "use this one",
  openInBook: "open in the book",
  practiceNotCheck: "practice beside the book, not a check on your own",
  nothing: "Nothing in practice fits yet.",
  find: "find an exercise in my sources",
  finding: "looking for exercises in your books",
  foundNone: "No exercise in your books fits this yet.",
  unavailable: "Couldn't load the exercises from your books.",
} as const;

/** One textbook exercise as the Reader shows it, whichever path found it. */
export interface ExerciseCandidate {
  key: string;
  /** "proposal": S1's candidate in a find_practice proposal (the sources
   *  service's import); "fallback": found by "find an exercise in my sources"
   *  (the Reader's own import). */
  origin: "proposal" | "fallback";
  proposalId: string | null;
  extractionId: string;
  spanIds: string[];
  sourceId: string | null;
  sourceTitle: string | null;
  page: number | null;
  label: string | null;
  /** The exercise's own words, verbatim; never its solution. */
  statement: string;
  exposure: ExerciseExposureDto;
  importRequest?: ReaderImportExerciseInput;
}

/** What "use this one" asks the workbench to open. */
export interface ReaderWorkbenchExercise {
  key: string;
  sourceId: string | null;
  extractionId: string;
  spanIds: string[];
  stemMd: string;
  /** An unexposed exercise is your own attempt (book hidden); an exposed one
   *  is practice beside the book (§7.4: never offered as a check on your own). */
  entry: Extract<WorkbenchEntry, "practice_this" | "work_through">;
  proposalId: string | null;
  sourceExercise?: { proposalId: string; extractionId: string; spanIds: string[] };
  importRequest?: ReaderImportExerciseInput;
}

/** The keys to ask `reader.exercise_candidates` about, in proposal order. */
export function proposalKeys(result: FindPracticeResultDto): Array<{ extractionId: string; spanIds: string[] }> {
  return (result.sourceExercises ?? []).map((exercise) => ({ extractionId: exercise.extractionId, spanIds: exercise.spanIds }));
}

/** The proposal's exercises the server let through, in proposal order. One the
 *  server left out (held-out material) or never answered about is not shown. */
export function fromProposal(result: FindPracticeResultDto, view: ExerciseCandidatesDto | null): ExerciseCandidate[] {
  if (!view || !result.proposalId || view.proposalId !== result.proposalId) return [];
  const viewed = new Map(view.candidates.map((candidate) => [candidate.key, candidate]));
  const shown: ExerciseCandidate[] = [];
  for (const exercise of result.sourceExercises ?? []) {
    const seen = viewed.get(exercise.key);
    if (!seen) continue;
    shown.push({
      key: exercise.key,
      origin: "proposal",
      proposalId: result.proposalId,
      extractionId: exercise.extractionId,
      spanIds: exercise.spanIds,
      sourceId: exercise.sourceId ?? seen.sourceId ?? null,
      sourceTitle: exercise.sourceTitle,
      page: exercise.page,
      label: exercise.label,
      statement: exercise.statement,
      exposure: seen.exposure,
    });
  }
  return shown;
}

export function fromFallback(found: FindExercisesDto | null): ExerciseCandidate[] {
  return (found?.candidates ?? []).map((candidate) => ({
    key: candidate.key,
    origin: "fallback" as const,
    proposalId: null,
    extractionId: candidate.extractionId,
    spanIds: candidate.spanIds,
    sourceId: candidate.sourceId,
    sourceTitle: candidate.sourceTitle,
    page: candidate.page,
    label: candidate.label,
    statement: candidate.statement,
    exposure: candidate.exposure,
    importRequest: candidate.importRequest,
  }));
}

/** "Matrix Theory · p. 9 · Exercise 1" */
export function exerciseLocator(candidate: Pick<ExerciseCandidate, "sourceTitle" | "page" | "label">): string {
  const label = candidate.label && !/p\.\s*\d/.test(candidate.label) ? candidate.label : null;
  return [candidate.sourceTitle, candidate.page != null ? `p. ${candidate.page}` : null, label].filter(Boolean).join(" · ");
}

/** The honest line under an exercise: what is verbatim, who wrote the answer,
 *  and the key's status (the sources service's labels, §7.3). Before "use
 *  this one" no key exists yet. */
export function keyStatusLine(keyStatus?: string | null, keyLabel?: string | null): string {
  const lead = EXERCISE_COPY.verbatim;
  switch (keyStatus ?? null) {
    case null:
    case undefined:
      return `${lead} · ${EXERCISE_COPY.modelAnswer} · ${EXERCISE_COPY.beforeUse}`;
    case "book_solution":
      return `${lead} · answer from the book's solution`;
    case "checked":
    case "panel_agrees":
      return `${lead} · ${EXERCISE_COPY.modelAnswer} · checked ✓ (${(keyLabel || "verified").replace(/^Checked: /, "")})`;
    case "panel_agrees_unconfirmed":
      return `${lead} · ${EXERCISE_COPY.modelAnswer} · not verified: ${keyLabel || "the symbolic check couldn't run here"}`;
    case "checking":
      return `${lead} · ${EXERCISE_COPY.modelAnswer} · being checked`;
    case "model_answer":
      return `${lead} · ${EXERCISE_COPY.modelAnswer} · not checked`;
    case "disputed":
      return `${lead} · ${EXERCISE_COPY.modelAnswer} · LearnLoop's check disagrees with this answer key`;
    case "changed_since_check":
      return `${lead} · answer key changed since it was checked`;
    default:
      return `${lead} · ${EXERCISE_COPY.modelAnswer}${keyLabel ? ` · ${keyLabel}` : ""}`;
  }
}

/** What "use this one" opens: the verbatim stem at once, the import behind it. */
export function exerciseOpenRequest(candidate: ExerciseCandidate): ReaderWorkbenchExercise {
  const entry = candidate.exposure.exposed ? "work_through" : "practice_this";
  const base = {
    key: candidate.key,
    sourceId: candidate.sourceId,
    extractionId: candidate.extractionId,
    spanIds: candidate.spanIds,
    stemMd: candidate.statement,
    entry,
    proposalId: candidate.proposalId,
  } as const;
  if (candidate.origin === "proposal" && candidate.proposalId) {
    return {
      ...base,
      sourceExercise: { proposalId: candidate.proposalId, extractionId: candidate.extractionId, spanIds: candidate.spanIds },
    };
  }
  return { ...base, importRequest: candidate.importRequest };
}

/** A tutor tool request's find_practice run as the proposal it is (for RW1c's
 *  offers: its exercises carry span keys, "extraction:span"). */
export function practiceFromToolRun(run: SourceToolRunDto): FindPracticeResultDto {
  return {
    version: run.version,
    status: run.result.status ?? "ok",
    proposalId: run.result.proposalId,
    items: [],
    sourceExercises: (run.result.sourceExercises ?? []).map((exercise) => {
      const [extractionId] = exercise.spanKeys[0]?.split(":") ?? [""];
      return {
        kind: "source_exercise" as const,
        key: exercise.key,
        extractionId,
        spanIds: exercise.spanKeys.map((spanKey) => spanKey.slice(spanKey.indexOf(":") + 1)),
        sourceTitle: exercise.sourceLabel,
        label: null,
        page: exercise.page,
        statement: exercise.statement,
        rationale: exercise.rationale,
        labelLine: exercise.sourceLabel ?? "",
      };
    }),
  };
}
