// UX Phase 4 (docs/specs/ux_learnloop_v1.md §7.4, §7.5, §10): the kill switch
// and the plain words the practice and feedback surfaces share.
import { afterEach, expect, it } from "vitest";
import { setAlgoConfig } from "./algoConfig";
import {
  FIX_MIX_UP_LABEL,
  feedbackOrigin,
  ORIGIN_LABEL,
  simplePracticeFeedback,
  VERDICT_TEXT,
  verdictOf
} from "./practiceFeedback";

afterEach(() => setAlgoConfig(undefined));

it("is simple by default, before the first snapshot and against an older sidecar", () => {
  setAlgoConfig(undefined);
  expect(simplePracticeFeedback()).toBe(true);
  setAlgoConfig({ practice: { stuckPrompt: true } });
  expect(simplePracticeFeedback()).toBe(true);
});

it("follows [ui] practice_feedback", () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" } });
  expect(simplePracticeFeedback()).toBe(false);
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
  expect(simplePracticeFeedback()).toBe(true);
  // Anything else is not a value the sidecar sends: the default holds.
  setAlgoConfig({ ui: { practiceFeedback: "fancy" } });
  expect(simplePracticeFeedback()).toBe(true);
});

it("says a verdict in words", () => {
  expect(VERDICT_TEXT[verdictOf({ score: 4, max: 4 })]).toBe("Right");
  expect(VERDICT_TEXT[verdictOf({ score: 2, max: 4 })]).toBe("Partly right");
  expect(VERDICT_TEXT[verdictOf({ score: 0, max: 4 })]).toBe("Not yet");
  // The grade's own correctness decides when it is known (criteria a valid
  // route never exercised are out of the grade, not lost points).
  expect(VERDICT_TEXT[verdictOf({ score: 2, max: 4, correctness: 1 })]).toBe("Right");
  expect(VERDICT_TEXT[verdictOf({ score: null, max: 4 })]).toBe("Not yet");
});

it("never turns a held grade into a verdict", () => {
  expect(VERDICT_TEXT[verdictOf({ score: 4, max: 4, held: true })]).toBe("Held for review");
  expect(VERDICT_TEXT[verdictOf({ score: 0, max: 4, held: true })]).toBe("Held for review");
});

it("names repair as one timed step", () => {
  expect(FIX_MIX_UP_LABEL).toBe("Fix this mix-up · about 4 min");
});

it("returns feedback to where the attempt started", () => {
  expect(feedbackOrigin({ fromReader: true, planServing: true })).toBe("reader");
  expect(feedbackOrigin({ fromReader: false, planServing: true })).toBe("plan");
  expect(feedbackOrigin({ fromReader: false, planServing: false })).toBe("today");
  expect(ORIGIN_LABEL.reader).toBe("Back to the book");
  expect(ORIGIN_LABEL.plan).toBe("Today's plan");
  expect(ORIGIN_LABEL.today).toBe("Today");
});
