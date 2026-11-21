// UX Phase 3: Today's words (docs/specs/ux_learnloop_v1.md §7.1, §4.2 rules
// 9-10). The helpers format what the plan DTO carries and decide nothing.
import { afterEach, describe, expect, it, vi } from "vitest";
import type { DailyPlanBodyDto, PlanBlockDto, ScheduledItemDto } from "../api/dto";

const { api } = vi.hoisted(() => ({ api: { getDailyPlan: vi.fn(), getStartSummary: vi.fn() } }));
vi.mock("../api/client", () => ({ api }));

import {
  dayPhrase,
  doneLine,
  fullListWhy,
  implicitSessionMinutes,
  onYourOwnWhy,
  planSentence,
  problemThread,
  reentrySentence,
  splitWhy,
  streakLine,
  todayRows,
  todayThreads
} from "./todayPlan";

afterEach(() => vi.resetAllMocks());

function block(overrides: Partial<PlanBlockDto>): PlanBlockDto {
  return {
    id: "b",
    ordinal: 1,
    lane: "maintain",
    action: "practice",
    subtype: null,
    chosenBy: "lane_quota",
    why: "",
    whyKind: null,
    fallback: false,
    estMinutes: 5,
    status: "current",
    startedAt: null,
    endedAt: null,
    outcome: null,
    reading: null,
    learningObjectTitles: ["Sets"],
    items: [{ practiceItemId: "p", learningObjectId: "l", learningObjectTitle: "Sets", practiceMode: null, promptPreview: "", lane: "maintain", estMinutes: 5, state: "planned", origin: "chooser", servedAt: null, doneAt: null }],
    displacedCount: 0,
    ...overrides
  };
}

function plan(overrides: Partial<DailyPlanBodyDto>): DailyPlanBodyDto {
  return {
    id: "plan",
    localDate: "2026-10-26",
    kind: "normal",
    status: "open",
    stopReason: null,
    parentPlanId: null,
    minutesBudget: 25,
    rememberedMinutes: 25,
    minutesSource: "carried",
    minuteChoices: [10, 15, 25],
    minutesLeft: 25,
    split: { rule: null, line: "", lanesAllowed: [], requestedMinutes: 0, lanes: [] },
    admission: { admittedCount: 0, exemptRequests: 0, stoppedBy: null, floorApplied: false, reviewLoadPerDay: null, ceilingMinutes: null, override: null },
    blocks: [],
    currentBlockId: null,
    projected: [],
    blockCountEstimate: 1,
    firstBlock: null,
    nextStep: null,
    totals: { plannedMinutes: 0, plannedItems: 0, doneItems: 0, skippedItems: 0, displacedItems: 0, readingBlocks: 0, readingBlocksEnded: 0, estMinutesDone: 0, actualMinutes: 0 },
    reentry: null,
    source: null,
    chooser: null,
    ...overrides
  };
}

describe("dayPhrase", () => {
  it("names the weekday and the part of the day", () => {
    expect(dayPhrase(new Date(2026, 9, 27, 8))).toBe("Tuesday morning");
    expect(dayPhrase(new Date(2026, 9, 27, 14))).toBe("Tuesday afternoon");
    expect(dayPhrase(new Date(2026, 9, 27, 19))).toBe("Tuesday evening");
    expect(dayPhrase(new Date(2026, 9, 27, 23))).toBe("Tuesday night");
  });
});

describe("planSentence", () => {
  it("describes each lane by what it does, never by its name", () => {
    const sentence = planSentence(
      plan({
        blocks: [block({ id: "b1", lane: "new", learningObjectTitles: ["Mixtures"] })],
        currentBlockId: "b1",
        projected: [
          { ordinal: 2, lane: "push", estMinutes: 4, itemCount: 1, learningObjectTitles: ["Convolutions"], readingTitle: null, why: "" },
          { ordinal: 3, lane: "maintain", estMinutes: 6, itemCount: 1, learningObjectTitles: ["Sets"], readingTitle: null, why: "" }
        ]
      })
    );
    expect(sentence).toBe("Up to 25 minutes today. Planned so far: new: Mixtures, then a step further on Convolutions and 1 short question from earlier days.");
    expect(sentence).not.toMatch(/maintain|repair|push|lane/);
  });

  it("says the minutes left once the plan has begun, and names a learner pick", () => {
    const sentence = planSentence(
      plan({
        minutesLeft: 11.6,
        blocks: [block({ id: "b0", status: "done" }), block({ id: "b1", chosenBy: "learner_pick", learningObjectTitles: ["Bayes"], startedAt: "2026-10-26T10:00:00Z" })],
        currentBlockId: "b1"
      })
    );
    expect(sentence).toBe("Room for about 12 more minutes today. Next: your pick, Bayes.");
  });

  it("is null when nothing is planned", () => {
    expect(planSentence(plan({}))).toBeNull();
  });

  it("says the plan's minutes are a suggestion under the router objective (RO4), and the minutes past them", () => {
    const current = block({ id: "b1", learningObjectTitles: ["Bayes"] });
    expect(planSentence(plan({ minutesAreASuggestion: true, blocks: [current], currentBlockId: "b1" }))).toBe(
      "About 25 minutes suggested today. Planned so far: 1 short question from earlier days."
    );
    const begun = [block({ id: "b0", status: "done" }), block({ id: "b1", startedAt: "2026-10-26T10:00:00Z" })];
    expect(planSentence(plan({ minutesAreASuggestion: true, minutesLeft: -6, minutesPastPlan: 6, blocks: begun, currentBlockId: "b1" }))).toBe(
      "About 6 minutes planned past today's suggested time. Next: 1 short question from earlier days."
    );
    expect(planSentence(plan({ minutesAreASuggestion: true, minutesLeft: 8, minutesPastPlan: 0, blocks: begun, currentBlockId: "b1" }))).toBe(
      "Room for about 8 more minutes of today's suggested time. Next: 1 short question from earlier days."
    );
  });

  it("lists the remaining blocks as rows, without the finished ones", () => {
    const rows = todayRows(plan({ blocks: [block({ id: "b0", status: "done" }), block({ id: "b1", lane: "repair", learningObjectTitles: ["A", "B", "C"] })], currentBlockId: "b1" }));
    expect(rows.map((row) => [row.text, row.minutes, row.current])).toEqual([["Fix a mix-up · A, B and more", "about 5 min", true]]);
  });
});

describe("re-entry and done", () => {
  it("a re-entry is a short plan in minutes, with nothing owed", () => {
    const text = reentrySentence(plan({ kind: "reentry", reentry: { gapDays: 9, solidCount: 3, slippedCount: 4, slippedNames: ["A"], namedBy: "x", target: 0.85, planMinutes: 12.4, planItems: 5 } }));
    expect(text).toBe("Welcome back. A short catch-up today: 12 minutes of the most useful questions. Nothing else is waiting on you.");
    expect(text).not.toMatch(/\b(4|5|9)\b|slipped/);
  });

  it("done says the time spent", () => {
    expect(doneLine({ version: 1, enabled: true, plan: null, day: { plans: 1, kinds: [], complete: true, plannedMinutes: 0, plannedItems: 3, doneItems: 3, skippedItems: 0, displacedItems: 0, readingBlocks: 0, readingBlocksEnded: 0, estMinutesDone: 0, actualMinutes: 1 } })).toBe("Done for today · 1 minute spent answering.");
    expect(doneLine({ version: 1, enabled: true, plan: null })).toBe("Done for today.");
  });
});

describe("splitWhy", () => {
  it("names each part of the split by what it is for, requests first", () => {
    const lines = splitWhy(
      plan({
        split: {
          rule: null,
          line: "",
          lanesAllowed: [],
          requestedMinutes: 3,
          lanes: [
            { lane: "maintain", minutes: 10, displayMinutes: 10, load: null, cap: null, reason: null },
            { lane: "new", minutes: 0, displayMinutes: 0, load: null, cap: null, reason: null }
          ]
        }
      })
    );
    expect(lines).toEqual(["about 3 min for what you asked for, first", "about 10 min for keeping what you know"]);
  });
});

describe("streakLine", () => {
  it("is quiet: days in a row, and the best when it is longer (a bare '1 day' said nothing of what it counts)", () => {
    expect(streakLine({ current: 4, activeToday: true, longest: 9 })).toBe("4 days in a row · best 9");
    expect(streakLine({ current: 1, activeToday: true, longest: 1 })).toBe("1 day in a row");
    expect(streakLine({ current: 0, activeToday: false, longest: 3 })).toBeNull();
    expect(streakLine(null)).toBeNull();
  });
});

describe("the full list's words", () => {
  const item = (overrides: Partial<ScheduledItemDto>) => ({ isFollowup: false, followupKind: null, isProbe: false, dueStatus: "due", ...overrides }) as ScheduledItemDto;
  it("says why in a few words, and a check on your own as one", () => {
    expect(fullListWhy(item({ isFollowup: true, followupKind: "cold_retry" }))).toBe("on your own · no hints");
    expect(fullListWhy(item({ isFollowup: true, followupKind: "certification_cold_probe" }))).toBe("on your own · no hints");
    expect(fullListWhy(item({ isFollowup: true, followupKind: "intervention_followup" }))).toBe("after a fix, once more");
    expect(fullListWhy(item({ isProbe: true }))).toBe("to see what you know");
    // A later row with no due time is a question never answered (UX-44c).
    expect(fullListWhy(item({ dueStatus: "later" }))).toBe("not answered yet");
    expect(onYourOwnWhy(item({ isFollowup: true, followupKind: "cold_retry" }))).toContain("To see whether last week's fix held.");
    expect(onYourOwnWhy(item({}))).toBeNull();
  });
});

describe("the full list's words for a question that waits (UX-44c)", () => {
  const item = (overrides: Partial<ScheduledItemDto>) => ({ isFollowup: false, followupKind: null, isProbe: false, dueStatus: "later", dueAt: null, ...overrides }) as ScheduledItemDto;
  const now = new Date(2026, 10, 20, 15, 0).getTime();
  const at = (days: number, hour: number) => new Date(2026, 10, 20 + days, hour, 0).toISOString();
  it("a question never answered is not 'coming back'", () => {
    expect(fullListWhy(item({ dueAt: null }), now)).toBe("not answered yet");
  });
  it("an answered one says when it comes back, by the day", () => {
    expect(fullListWhy(item({ dueAt: at(0, 21) }), now)).toBe("coming back later today");
    expect(fullListWhy(item({ dueAt: at(1, 9) }), now)).toBe("comes back tomorrow");
    // Within the week by its weekday, after it by its date (Friday 20 November is today).
    expect(fullListWhy(item({ dueAt: at(4, 9) }), now)).toBe("comes back Tuesday");
    expect(fullListWhy(item({ dueAt: at(9, 9) }), now)).toBe("comes back on 29 November");
  });
  it("one whose time has come is brought back now", () => {
    expect(fullListWhy(item({ dueAt: at(0, 10) }), now)).toBe("time to bring it back");
  });
});

describe("threads", () => {
  it("lists open questions and open problems newest first, never resolved ones", () => {
    const threads = todayThreads(
      [
        { id: "q1", questionMd: "**Why** a sum?", resolution: "open", createdAt: "2026-10-20T00:00:00Z", sourceCitation: null } as never,
        { id: "q2", questionMd: "done", resolution: "resolved", createdAt: "2026-10-26T00:00:00Z", sourceCitation: null } as never
      ],
      [{ sessionId: "w1", stemMd: "Exercise 5.9", stepCount: 1, updatedAt: "2026-10-22T00:00:00Z" } as never]
    );
    expect(threads.map((thread) => thread.key)).toEqual(["p:w1", "q:q1"]);
    expect(threads[1].text).toBe("“Why a sum?”");
    expect(problemThread({ sessionId: "w2", stemMd: "x", stepCount: 0 } as never)).toMatchObject({ steps: "not started" });
    expect(problemThread({ sessionId: "w3", stemMd: "x", stepCount: 1 } as never)).toMatchObject({ steps: "1 step written" });
  });
});

describe("implicitSessionMinutes", () => {
  it("is the plan's minutes while the plan serves", async () => {
    api.getDailyPlan.mockResolvedValue({ enabled: true, plan: { minutesBudget: 24.6 } });
    expect(await implicitSessionMinutes()).toBe(25);
    expect(api.getStartSummary).not.toHaveBeenCalled();
  });

  it("is the remembered minutes while the plan is off or cannot be read", async () => {
    api.getDailyPlan.mockResolvedValue({ enabled: false, plan: null });
    api.getStartSummary.mockResolvedValue({ rememberedMinutes: 15 });
    expect(await implicitSessionMinutes()).toBe(15);
    api.getDailyPlan.mockRejectedValue(new Error("down"));
    expect(await implicitSessionMinutes()).toBe(15);
  });

  it("is null when neither can be read: nothing is started", async () => {
    api.getDailyPlan.mockRejectedValue(new Error("down"));
    api.getStartSummary.mockRejectedValue(new Error("down"));
    expect(await implicitSessionMinutes()).toBeNull();
  });
});

// UX fix stage 3 (audit F9): one clock. Each duration says what it measures, so
// no two lines read as the same quantity with different values.
describe("UX fix stage 3, F9: each duration says what it measures", () => {
  it("the plan's time is its length, and the rows are what is planned so far, never the same clock", () => {
    const current = block({ id: "b1", learningObjectTitles: ["Bayes"] });
    const ro4 = planSentence(plan({ minutesAreASuggestion: true, blocks: [current], currentBlockId: "b1" }));
    expect(ro4).toMatch(/^About 25 minutes suggested today\. Planned so far: /);
    expect(planSentence(plan({ blocks: [current], currentBlockId: "b1" }))).toMatch(/^Up to 25 minutes today\. Planned so far: /);
  });

  it("once begun, the minutes not yet given to a block are room, not a countdown", () => {
    const begun = [block({ id: "b0", status: "done" }), block({ id: "b1", startedAt: "2026-10-26T10:00:00Z" })];
    const sentence = planSentence(plan({ minutesAreASuggestion: true, minutesLeft: 22, minutesPastPlan: 0, blocks: begun, currentBlockId: "b1" }));
    expect(sentence).toMatch(/^Room for about 22 more minutes of today's suggested time\. Next: /);
    expect(sentence).not.toMatch(/minutes left/);
  });

  it("done says the time spent answering (and reading, when there was reading), not the session's length", () => {
    const day = { plans: 1, kinds: [], complete: true, plannedMinutes: 0, plannedItems: 6, doneItems: 6, skippedItems: 0, displacedItems: 0, readingBlocks: 0, readingBlocksEnded: 0, estMinutesDone: 0, actualMinutes: 2.2 };
    expect(doneLine({ version: 1, enabled: true, plan: null, day })).toBe("Done for today · 2 minutes spent answering.");
    expect(doneLine({ version: 1, enabled: true, plan: null, day: { ...day, readingBlocks: 1, readingBlocksEnded: 1 } })).toBe("Done for today · 2 minutes spent answering and reading.");
  });
});
