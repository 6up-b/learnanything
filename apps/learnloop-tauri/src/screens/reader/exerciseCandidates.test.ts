// RW4b's candidate model (spec §7.4; UX §4.6): which of a proposal's textbook
// exercises the Reader shows (only those the server let through, in proposal
// order), the honest line for each key status, and how "use this one" opens
// one (an exposed exercise as practice beside the book, never as a check on
// your own; a proposal's through the sources service's import, a fallback's
// through the Reader's own).
import { describe, expect, it } from "vitest";
import type { ExerciseCandidatesDto, ExerciseExposureDto, FindExercisesDto, FindPracticeResultDto } from "../../api/dto";
import { exerciseLocator, exerciseOpenRequest, fromFallback, fromProposal, keyStatusLine, practiceFromToolRun, proposalKeys } from "./exerciseCandidates";

const fresh: ExerciseExposureDto = { exposed: false, reasons: [], label: null, note: null, offeredAs: "check_on_your_own", exposureRuleVersion: "reading_exposure_v1" };
const seen: ExerciseExposureDto = { exposed: true, reasons: ["source_exposed"], label: "you've recently seen this page or its solution", note: null, offeredAs: "practice", exposureRuleVersion: "reading_exposure_v1" };

function exercise(key: string, spans: string[], extra: Record<string, unknown> = {}) {
  return { kind: "source_exercise" as const, key, extractionId: "ext_text", spanIds: spans, sourceId: "src_text", revisionId: "rev_text",
    sourceTitle: "Matrix Theory", label: "Exercise 1", page: 9, statement: `${key} statement`, rationale: null, labelLine: "From Matrix Theory, p. 9 · not yet in your practice", ...extra };
}

const result: FindPracticeResultDto = {
  version: 1, status: "ok", proposalId: "pp_1", items: [],
  sourceExercises: [exercise("srcex:a", ["t6"]), exercise("srcex:b", ["t7"]), exercise("srcex:c", ["t8"])],
};

function view(keys: string[], exposures: Record<string, ExerciseExposureDto> = {}): ExerciseCandidatesDto {
  return { version: 1, proposalId: "pp_1", withheld: 3 - keys.length,
    candidates: keys.map((key) => ({ key, extractionId: "ext_text", spanIds: [], sourceId: "src_text", revisionId: "rev_text", exposure: exposures[key] ?? fresh })) };
}

describe("the proposal's exercises", () => {
  it("asks about every proposed exercise and shows only those the server let through, in proposal order", () => {
    expect(proposalKeys(result)).toEqual([{ extractionId: "ext_text", spanIds: ["t6"] }, { extractionId: "ext_text", spanIds: ["t7"] }, { extractionId: "ext_text", spanIds: ["t8"] }]);
    const shown = fromProposal(result, view(["srcex:c", "srcex:a"]));
    expect(shown.map((c) => c.key)).toEqual(["srcex:a", "srcex:c"]); // b was held out
    expect(shown[0]).toMatchObject({ origin: "proposal", proposalId: "pp_1", statement: "srcex:a statement", sourceId: "src_text" });
  });

  it("fails closed: no answer, or an answer about another proposal, shows none", () => {
    expect(fromProposal(result, null)).toEqual([]);
    expect(fromProposal(result, { ...view(["srcex:a"]), proposalId: "pp_other" })).toEqual([]);
  });
});

describe("the honest line", () => {
  it("before use, no key exists: the model completes it and it is checked when used", () => {
    expect(keyStatusLine(null)).toBe("from your book · verbatim · answer completed by LearnLoop's model · checked when you use it");
  });

  it("says each key status as the sources service labels it", () => {
    expect(keyStatusLine("book_solution", "Answer from the book's solution")).toBe("from your book · verbatim · answer from the book's solution");
    expect(keyStatusLine("checked", "Checked: independent solvers and a symbolic check agree")).toBe(
      "from your book · verbatim · answer completed by LearnLoop's model · checked ✓ (independent solvers and a symbolic check agree)");
    expect(keyStatusLine("panel_agrees", "Independent model solvers agree")).toContain("checked ✓ (Independent model solvers agree)");
    expect(keyStatusLine("panel_agrees_unconfirmed", "Independent model solvers agree; the symbolic check couldn't run here")).toContain("not verified");
    expect(keyStatusLine("model_answer", "Model's answer, not checked")).toBe("from your book · verbatim · answer completed by LearnLoop's model · not checked");
    expect(keyStatusLine("checking")).toContain("being checked");
    expect(keyStatusLine("disputed")).toContain("LearnLoop's check disagrees with this answer key");
    expect(keyStatusLine("changed_since_check")).toContain("answer key changed since it was checked");
  });

  it("names source, page and the exercise without repeating the page", () => {
    expect(exerciseLocator({ sourceTitle: "Matrix Theory", page: 9, label: "Exercise 1" })).toBe("Matrix Theory · p. 9 · Exercise 1");
    expect(exerciseLocator({ sourceTitle: "Matrix Theory", page: 9, label: "Exercise 2, p. 9" })).toBe("Matrix Theory · p. 9");
  });
});

describe("use this one", () => {
  it("opens an unexposed exercise as your own attempt and an exposed one as practice beside the book", () => {
    const [a, c] = fromProposal(result, view(["srcex:a", "srcex:c"], { "srcex:c": seen }));
    expect(exerciseOpenRequest(a)).toMatchObject({
      entry: "practice_this", stemMd: "srcex:a statement", proposalId: "pp_1",
      sourceExercise: { proposalId: "pp_1", extractionId: "ext_text", spanIds: ["t6"] },
    });
    expect(exerciseOpenRequest(a).importRequest).toBeUndefined();
    expect(exerciseOpenRequest(c).entry).toBe("work_through");
  });

  it("opens a fallback exercise with the Reader's own import request", () => {
    const found: FindExercisesDto = { version: 1, status: "ok", policy: "reading", dropped: {}, candidates: [{
      key: "srcex:ext_text:t6", extractionId: "ext_text", spanIds: ["t6"], sourceId: "src_text", revisionId: "rev_text",
      sourceTitle: "Matrix Theory", page: 9, label: "Exercise 1, p. 9", statement: "1. Solve 3x + 5 = 20.", exposure: fresh,
      importRequest: { extractionId: "ext_text", sourceId: "src_text", revisionId: "rev_text", rawSelection: { nodes: [{ spanId: "t6", start: 0, end: 20 }] } },
    }] };
    const [candidate] = fromFallback(found);
    const request = exerciseOpenRequest(candidate);
    expect(request).toMatchObject({ entry: "practice_this", proposalId: null, importRequest: found.candidates[0].importRequest });
    expect(request.sourceExercise).toBeUndefined();
  });
});

describe("a tutor tool request's run (RW1c's offers, at the landing)", () => {
  it("is the proposal it ran, its exercises keyed as find_practice keys them", () => {
    const practice = practiceFromToolRun({
      version: 1, tool: "find_practice", policy: "reading", toolCallId: "stc_1", runId: "r1",
      result: { proposalId: "pp_9", items: [], sourceExercises: [
        { key: "srcex:ext_text:t6,t7", spanKeys: ["ext_text:t6", "ext_text:t7"], sourceLabel: "From Matrix Theory, p. 9", page: 9, statement: "1. Solve it.", rationale: null },
      ] },
    });
    expect(practice.proposalId).toBe("pp_9");
    expect(proposalKeys(practice)).toEqual([{ extractionId: "ext_text", spanIds: ["t6", "t7"] }]);
    expect(practice.sourceExercises?.[0]).toMatchObject({ key: "srcex:ext_text:t6,t7", statement: "1. Solve it.", page: 9 });
  });
});
