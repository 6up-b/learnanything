// What comes next, dated: the words for every state of the sidecar's summary. EVENING is
// tests/next_practice_helpers.py's EXPECTED as the sidecar sends it (camel case): Saturday 31 October 2026 in New
// York, the night daylight saving ends.
import { describe, expect, it } from "vitest";
import type { NextPracticeDto } from "../api/dto";
import { dayName, daysFrom, nextPracticeLines, nextPracticeRowWhy } from "./nextPractice";
import { findJargon } from "../copy/denyList";

const EVENING: NextPracticeDto = {
  asOf: "2026-10-31T23:00:00Z",
  calendar: { zone: "EDT", today: "2026-10-31", tomorrow: "2026-11-01", nextDayStartsAt: "2026-11-01T04:00:00Z" },
  reviews: [
    { date: "2026-11-01", count: 2, itemIds: ["pi_dst", "pi_tomorrow"], learningObjectIds: ["lo_tomorrow"], minutes: 3.0 },
    { date: "2026-11-04", count: 1, itemIds: ["pi_held"], learningObjectIds: ["lo_held"], minutes: 1.5 },
    { date: "2026-11-05", count: 1, itemIds: ["pi_fallback"], learningObjectIds: ["lo_fallback"], minutes: null },
    { date: "2026-11-09", count: 1, itemIds: ["pi_nine"], learningObjectIds: ["lo_nine"], minutes: 2.5 }
  ],
  checks: [{ date: "2026-11-14", count: 1, itemIds: ["pi_checked"], learningObjectIds: ["lo_checked"], kinds: ["cold_retry"] }],
  nextReviewDate: "2026-11-01",
  writing: { topicCount: 3, learningObjectIds: ["lo_b", "lo_c", "lo_d"] },
  waiting: { sectionCount: 0 },
  held: { topicCount: 1, learningObjectIds: ["lo_g"] }
};

/** The evening with nothing due tomorrow: the nearest later day is Wednesday. */
const NOTHING_TOMORROW: NextPracticeDto = { ...EVENING, reviews: EVENING.reviews.slice(1), nextReviewDate: "2026-11-04" };

describe("days, in the plan's calendar", () => {
  it("counts plain dates, across the 25-hour Sunday and a month's end", () => {
    expect(daysFrom("2026-10-31", "2026-11-01")).toBe(1);
    expect(daysFrom("2026-10-31", "2026-11-02")).toBe(2);
    expect(daysFrom("2026-03-07", "2026-03-09")).toBe(2); // the spring change's 23-hour Sunday between
    expect(daysFrom("2026-10-31", "not a date")).toBeNull();
  });

  it("names today, tomorrow, the weekdays of the next six days and a date after them", () => {
    const today = "2026-10-31"; // a Saturday
    expect(dayName("2026-10-31", today)).toBe("today");
    expect(dayName("2026-11-01", today)).toBe("tomorrow");
    expect(dayName("2026-11-02", today)).toBe("Monday");
    expect(dayName("2026-11-06", today)).toBe("Friday");
    expect(dayName("2026-11-07", today)).toBe("7 November"); // seven days on: a date, not "Saturday" (today's name)
    expect(dayName("2026-11-14", today)).toBe("14 November");
    expect(dayName("2027-01-04", "2026-12-30")).toBe("Monday"); // within the week across the year's end
    expect(dayName("2027-01-08", "2026-12-30")).toBe("8 January 2027");
  });
});

describe("the lines", () => {
  it("the evening: tomorrow's questions and minutes, the check's first day, what is being written", () => {
    expect(nextPracticeLines(EVENING)).toEqual([
      "Tomorrow: 2 questions due · about 3 minutes.",
      "A check on your own is available from 14 November.",
      "Questions on 3 more topics are still being written."
    ]);
  });

  it("nothing due tomorrow names the nearest later day, by weekday within the week and by date after it", () => {
    expect(nextPracticeLines(NOTHING_TOMORROW, { writing: false })).toEqual([
      "Nothing is due tomorrow. Your next question is due Wednesday.",
      "A check on your own is available from 14 November."
    ]);
    const nine = { ...EVENING, reviews: EVENING.reviews.slice(3), nextReviewDate: "2026-11-09", checks: [], writing: { topicCount: 0, learningObjectIds: [] } };
    expect(nextPracticeLines(nine)).toEqual(["Nothing is due tomorrow. Your next question is due on 9 November."]);
    const two = { ...nine, reviews: [{ ...nine.reviews[0], count: 2, itemIds: ["a", "b"] }], nextReviewDate: "2026-11-02" };
    expect(nextPracticeLines({ ...two, reviews: [{ ...two.reviews[0], date: "2026-11-02" }] })).toEqual([
      "Nothing is due tomorrow. Your next questions are due Monday."
    ]);
  });

  it("names no minutes where no estimate supports them, and one question in the singular", () => {
    const one = { ...EVENING, reviews: [{ ...EVENING.reviews[0], count: 1, itemIds: ["pi_tomorrow"], minutes: null }] };
    expect(nextPracticeLines(one, { writing: false })[0]).toBe("Tomorrow: 1 question due.");
    const short = { ...EVENING, reviews: [{ ...EVENING.reviews[0], minutes: 0.4 }] };
    expect(nextPracticeLines(short, { writing: false })[0]).toBe("Tomorrow: 2 questions due · about 1 minute.");
  });

  it("a check available tomorrow, and several checks on one day", () => {
    const soon = { ...EVENING, checks: [{ ...EVENING.checks[0], date: "2026-11-01" }] };
    expect(nextPracticeLines(soon, { writing: false })).toContain("A check on your own is available from tomorrow.");
    const two = { ...EVENING, checks: [{ ...EVENING.checks[0], date: "2026-11-07", count: 2, itemIds: ["a", "b"] }] };
    expect(nextPracticeLines(two, { writing: false })).toContain("2 checks on your own are available from 7 November.");
  });

  it("the finish also says what is still due today and a check open now; with those, tomorrow's are 'more'", () => {
    const today = {
      ...EVENING,
      reviews: [{ date: "2026-10-31", count: 2, itemIds: ["a", "b"], learningObjectIds: ["lo_a"], minutes: 4 }, ...EVENING.reviews],
      checks: [{ date: "2026-10-31", count: 1, itemIds: ["c"], learningObjectIds: ["lo_c"], kinds: ["cold_retry"] }, ...EVENING.checks]
    };
    expect(nextPracticeLines(today, { finish: true })).toEqual([
      "Still due today: 2 questions · about 4 minutes.",
      "Tomorrow: 2 more questions due · about 3 minutes.",
      "A check on your own is available now.",
      "A check on your own is available from 14 November.",
      "Questions on 3 more topics are still being written."
    ]);
    // Today's own plan and list say what is due today: Today's lines start at tomorrow.
    expect(nextPracticeLines(today)[0]).toBe("Tomorrow: 2 more questions due · about 3 minutes.");
    const onlyToday = { ...today, reviews: today.reviews.slice(0, 1), nextReviewDate: null, checks: [], writing: { topicCount: 0, learningObjectIds: [] } };
    expect(nextPracticeLines(onlyToday, { finish: true })).toEqual(["Still due today: 2 questions · about 4 minutes.", "Nothing more is due tomorrow."]);
  });

  it("questions still being written get no day, and Today can leave them to its own line", () => {
    const writingOnly = { ...EVENING, reviews: [], checks: [], nextReviewDate: null, writing: { topicCount: 1, learningObjectIds: ["lo_b"] } };
    expect(nextPracticeLines(writingOnly)).toEqual(["Nothing is due tomorrow.", "Questions on 1 more topic are still being written."]);
    expect(nextPracticeLines(writingOnly, { writing: false })).toEqual([]);
  });

  it("says nothing with nothing dated and nothing under way, or with no summary", () => {
    const empty = { ...EVENING, reviews: [], checks: [], nextReviewDate: null, writing: { topicCount: 0, learningObjectIds: [] }, held: { topicCount: 0, learningObjectIds: [] } };
    expect(nextPracticeLines(empty)).toEqual([]);
    expect(nextPracticeLines(null)).toEqual([]);
    expect(nextPracticeLines(undefined)).toEqual([]);
  });

  it("every line is in plain words", () => {
    const today = { ...EVENING, reviews: [{ date: "2026-10-31", count: 1, itemIds: ["a"], learningObjectIds: ["lo_a"], minutes: 2 }, ...EVENING.reviews],
      checks: [{ date: "2026-10-31", count: 2, itemIds: ["c", "d"], learningObjectIds: ["lo_c"], kinds: ["certification_cold_probe"] }, ...EVENING.checks] };
    for (const next of [EVENING, NOTHING_TOMORROW, today]) {
      for (const line of nextPracticeLines(next, { finish: true })) expect(findJargon(line), line).toEqual([]);
    }
    for (const id of ["pi_dst", "pi_held", "pi_nine", "pi_checked"]) {
      const why = nextPracticeRowWhy(EVENING, { practiceItemId: id })!;
      expect(findJargon(why), why).toEqual([]);
    }
  });
});

describe("the full list's rows", () => {
  it("says the day a row comes back, by its effective due, and a kept question's check day", () => {
    expect(nextPracticeRowWhy(EVENING, { practiceItemId: "pi_dst" })).toBe("comes back tomorrow");
    expect(nextPracticeRowWhy(EVENING, { practiceItemId: "pi_held" })).toBe("comes back Wednesday");
    expect(nextPracticeRowWhy(EVENING, { practiceItemId: "pi_nine" })).toBe("comes back on 9 November");
    expect(nextPracticeRowWhy(EVENING, { practiceItemId: "pi_checked" })).toBe("a check on your own from 14 November");
    expect(nextPracticeRowWhy(EVENING, { practiceItemId: "pi_new" })).toBeNull();
    expect(nextPracticeRowWhy(null, { practiceItemId: "pi_dst" })).toBeNull();
  });
});
