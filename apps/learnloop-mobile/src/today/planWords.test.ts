// UX fix stage 4 (audit F9 on the phone; phone-2 #22-54, "About 8 minutes left" that never moved): each of the
// phone's durations says what it measures, in the desktop's words since stage 3 (`ux-fix-stage-3.md`, item 3), so
// the plan's length, the room left in it and the time spent never read as one clock. Nothing computed changes.
import { describe, expect, it } from "vitest";
import type { DailyPlanBodyDto } from "@desktop/api/dto";
import { findJargon } from "@desktop/copy/denyList";
import type { PhonePlanDto } from "../api/phone";
import { doneLine, planSentence } from "./planWords";

const block = (extra: Record<string, unknown> = {}) => ({
  id: "b1", ordinal: 1, lane: "maintain", chosenBy: "lane_quota", status: "current", startedAt: null, reading: null,
  learningObjectTitles: ["Topic i1"],
  items: [{ practiceItemId: "i1", state: "planned" }, { practiceItemId: "i2", state: "planned" }, { practiceItemId: "i3", state: "planned" }],
  ...extra
});
const plan = (extra: Record<string, unknown> = {}) =>
  ({ blocks: [block()], currentBlockId: "b1", projected: [], minutesBudget: 25, minutesLeft: 25, minutesAreASuggestion: false, ...extra }) as unknown as DailyPlanBodyDto;
const begun = { blocks: [block({ id: "b0", status: "done" }), block()], minutesLeft: 18 };

describe("UX fix stage 4, F9 on the phone: each duration says what it measures", () => {
  it("before the plan is begun, its number is the plan's length, an upper bound, and the block is the first planned", () => {
    expect(planSentence(plan())).toBe("Up to 25 minutes today. First: 3 short questions from earlier days.");
  });

  it("once begun, the minutes not yet given to a block are room, not a countdown", () => {
    expect(planSentence(plan(begun))).toBe("Room for about 18 more minutes today. Next: 3 short questions from earlier days.");
    expect(planSentence(plan({ ...begun, minutesLeft: 0.6 }))).toBe("Room for about 1 more minute today. Next: 3 short questions from earlier days.");
  });

  it("the router objective's suggestion says it is one, before, during and past it", () => {
    expect(planSentence(plan({ minutesAreASuggestion: true }))).toBe("About 25 minutes suggested today. First: 3 short questions from earlier days.");
    expect(planSentence(plan({ ...begun, minutesAreASuggestion: true }))).toBe(
      "Room for about 18 more minutes of today's suggested time. Next: 3 short questions from earlier days."
    );
    expect(planSentence(plan({ ...begun, minutesAreASuggestion: true, minutesPastPlan: 6 }))).toBe(
      "About 6 minutes planned past today's suggested time. Next: 3 short questions from earlier days."
    );
  });

  it("with no block chosen yet, the rest is said to be chosen as the plan goes", () => {
    expect(planSentence(plan({ blocks: [], currentBlockId: null, projected: [{ lane: "maintain" }] }))).toBe(
      "Up to 25 minutes today. The rest is chosen as you go."
    );
  });

  it("done says the time spent answering (and reading, when there was reading), not the session's length", () => {
    const done = (day: Record<string, unknown>) => ({ day }) as unknown as PhonePlanDto;
    expect(doneLine(done({ actualMinutes: 26, readingBlocks: 0 }))).toBe("Done for today · 26 minutes spent answering.");
    expect(doneLine(done({ actualMinutes: 1, readingBlocks: 2 }))).toBe("Done for today · 1 minute spent answering and reading.");
    expect(doneLine(done({ actualMinutes: 0, readingBlocks: 0 }))).toBe("Done for today.");
  });

  it("every one of these sentences is in plain words", () => {
    const sentences = [
      planSentence(plan()),
      planSentence(plan(begun)),
      planSentence(plan({ minutesAreASuggestion: true })),
      planSentence(plan({ ...begun, minutesAreASuggestion: true })),
      planSentence(plan({ ...begun, minutesAreASuggestion: true, minutesPastPlan: 6 })),
      planSentence(plan({ blocks: [], currentBlockId: null, projected: [{ lane: "maintain" }] })),
      doneLine({ day: { actualMinutes: 26, readingBlocks: 1 } } as unknown as PhonePlanDto)
    ];
    for (const sentence of sentences) expect(findJargon(sentence ?? ""), sentence ?? "").toEqual([]);
  });
});
