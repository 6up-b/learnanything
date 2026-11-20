// UX-18 (UX journey audit part 2, expert-1 #68-77): "Check what I already know" on a topic with no question it
// could ask ended at once as "completed · 0 / 4 questions" and "not enough answers to skip it". The shell now says
// what happened instead of opening that empty check; these are its words for each case.
import { describe, expect, it } from "vitest";
import type { CalibrationSessionProgressDto, QuickCheckProgressDto, QuickCheckResultDto } from "../api/dto";
import { findJargon } from "./denyList";
import { quickCheckNothingToAsk } from "./refusals";

function result(title: string, verdict: QuickCheckResultDto["verdict"]): QuickCheckResultDto {
  return { learningObjectId: `lo_${title}`, learningObjectTitle: title, verdict, assumptionId: null, answers: [] };
}

function progress(quickCheck: Partial<QuickCheckProgressDto>, status: CalibrationSessionProgressDto["status"] = "completed"): CalibrationSessionProgressDto {
  return {
    version: 1, calibrationSessionId: "cal1", sessionId: "s1", goalId: null, status,
    timeBudgetMinutes: 8, elapsedMinutes: 0, remainingMinutes: 8, blocksCompleted: 0, blocksPlanned: 0, episodes: [], nextTarget: null,
    quickCheck: { learningObjectIds: [], k: 4, answered: 0, remaining: 4, finished: true, results: [], ...quickCheck }
  };
}

describe("UX-18: a quick check that could ask nothing says why", () => {
  it("a topic with no question left to ask (expert-1 #76)", () => {
    const line = quickCheckNothingToAsk(progress({ results: [result("Construct covariance matrices", "undecided")] }));
    expect(line).toBe("Nothing to ask yet on “Construct covariance matrices”: it has no question you haven't already seen. Nothing was changed.");
    expect(findJargon(line ?? "")).toEqual([]);
  });

  it("a topic already marked as known (expert-1 #68)", () => {
    const line = quickCheckNothingToAsk(progress({ results: [result("Covariance and variance", "already_assumed")] }));
    expect(line).toBe("“Covariance and variance” is already marked as known, so there's nothing to check now. Its first review is the check.");
    expect(findJargon(line ?? "")).toEqual([]);
  });

  it("several topics: names the first and counts the rest; the known ones are left out of the no-question sentence", () => {
    expect(quickCheckNothingToAsk(progress({ results: [result("A", "undecided"), result("B", "learning"), result("C", "undecided")] })))
      .toBe("Nothing to ask yet on “A” and 2 more topics: they have no question you haven't already seen. Nothing was changed.");
    expect(quickCheckNothingToAsk(progress({ results: [result("A", "already_assumed"), result("B", "undecided")] })))
      .toBe("Nothing to ask yet on “B”: it has no question you haven't already seen. Nothing was changed.");
    expect(quickCheckNothingToAsk(progress({ results: [result("A", "already_assumed"), result("B", "already_assumed")] })))
      .toBe("“A” and 1 more topic are already marked as known, so there's nothing to check now. Their first review is the check.");
  });

  it("a check that asked, can still ask, or was stopped is not this case", () => {
    expect(quickCheckNothingToAsk(progress({ answered: 1 }))).toBeNull();
    expect(quickCheckNothingToAsk(progress({ finished: false, results: null }, "active"))).toBeNull();
    expect(quickCheckNothingToAsk(progress({}, "stopped"))).toBeNull();
    const plain = progress({});
    delete plain.quickCheck;
    expect(quickCheckNothingToAsk(plain)).toBeNull();
  });
});
