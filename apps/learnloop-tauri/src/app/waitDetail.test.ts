// An honest wait (the first evening, step 6): the words for each state of a build and of question writing, from the
// sidecar's recorded facts only. Nothing here is a percentage, a time left, an unmeasured estimate or a "stalled".
import { describe, expect, it } from "vitest";
import type { BuildDetailDto, WaitDeliveryDto, WritingDetailDto } from "../api/dto";
import { findJargon } from "../copy/denyList";
import { FIRST_QUESTIONS_TIME, buildWaitWords, replyGrew, writingWaitWords } from "./waitDetail";

const AS_OF = "2026-11-21T18:10:00Z";
const ago = (seconds: number) => new Date(Date.parse(AS_OF) - seconds * 1000).toISOString().replace(".000Z", "Z");

function delivery(overrides: Partial<WaitDeliveryDto> = {}): WaitDeliveryDto {
  return { requestSentAt: null, replyReceivedAt: null, outputPieces: 0, lastOutputAt: null, ...overrides };
}

function build(overrides: Partial<BuildDetailDto> = {}): BuildDetailDto {
  return { asOf: AS_OF, startedAt: ago(130), stage: "planning", retry: false, delivery: delivery({ requestSentAt: ago(40) }),
    measured: null, synthesis: { part: 1, parts: 1, pass: "plan" }, ...overrides };
}

function writing(overrides: Partial<WritingDetailDto> = {}): WritingDetailDto {
  return { asOf: AS_OF, startedAt: ago(200), queued: false, retry: false, topic: { title: "Spectral theorem", index: 1, total: 4 },
    topicStartedAt: ago(75), delivery: delivery({ requestSentAt: ago(75) }), measured: null, ...overrides };
}

const words = (detail: BuildDetailDto, grew = false) => buildWaitWords(detail, { clock: "ago", grew });
const said = (value: { lines: string[]; details: string[] }) => [...value.lines, ...value.details].join(" | ");

/** Every number the words say must be one of the facts' own: nothing computed beyond whole seconds or minutes. */
function assertNothingInvented(text: string) {
  expect(text).not.toMatch(/%|percent|left|remaining|stall|estimat|almost|nearly|soon/i);
  expect(findJargon(text)).toEqual([]);
}

describe("a book being got ready", () => {
  it("no reply yet: the part, how long ago it started and was asked, and that no time is measured", () => {
    const result = words(build());
    expect(result.lines).toEqual(["Planning questions · part 1 of 1", "Started 2 minutes ago · asked 40 seconds ago, no reply yet"]);
    expect(result.details).toEqual(["No book has finished getting ready in this library yet, so no time is given."]);
    assertNothingInvented(said(result));
  });

  it("a reply arriving: still writing only when it grew since the last read; otherwise when its last part came", () => {
    const arriving = build({ delivery: delivery({ requestSentAt: ago(40), outputPieces: 12, lastOutputAt: ago(8) }) });
    expect(words(arriving, true).lines[1]).toBe("Started 2 minutes ago · still writing");
    expect(words(arriving, false).lines[1]).toBe("Started 2 minutes ago · reply arriving, last part 8 seconds ago");
  });

  it("a long silence: the time of the last part, counted honestly, and no word that it stalled", () => {
    const silent = build({ delivery: delivery({ requestSentAt: ago(400), outputPieces: 30, lastOutputAt: ago(190) }) });
    const result = words(silent);
    expect(result.lines[1]).toBe("Started 2 minutes ago · reply arriving, last part 3 minutes ago");
    assertNothingInvented(said(result));
  });

  it("a retry says it is one", () => {
    const result = words(build({ retry: true, stage: "reading", inventory: { done: 0, total: 1, reused: null } }));
    expect(result.lines[0]).toBe("Trying again · Reading the text · 0 of 1 part read");
    expect(result.details[0]).toBe("An earlier try stopped; this one picks up from what was kept.");
  });

  it("a reply received, nothing in flight", () => {
    const result = words(build({ delivery: delivery({ replyReceivedAt: ago(12) }) }));
    expect(result.lines[1]).toBe("Started 2 minutes ago · reply received 12 seconds ago");
  });

  it("a connection that does not stream: asked, no reply yet, at every read (never still writing)", () => {
    const quiet = build({ delivery: delivery({ requestSentAt: ago(100) }) });
    expect(words(quiet, true).lines[1]).toBe("Started 2 minutes ago · asked 1 minute ago, no reply yet");
    expect(replyGrew(quiet.delivery, quiet.delivery)).toBe(false);
  });

  it("parts read before are said in the details, not as work done now", () => {
    const result = words(build({ stage: "reading", inventory: { done: 1, total: 3, reused: 2 }, synthesis: undefined }));
    expect(result.lines[0]).toBe("Reading the text · 1 of 3 parts read");
    expect(result.details).toContain("2 parts were read before and are not read again.");
  });

  it("a further pass with the passages the plan asked for is named, and the part count stays the part count", () => {
    const result = words(build({ synthesis: { part: 1, parts: 2, pass: "evidence" } }));
    expect(result.lines[0]).toBe("Planning questions · part 1 of 2 · looking at the passages it asked for");
    expect(result.details).toContain("A part can take a second look, with the passages it asked to see.");
    expect(words(build({ synthesis: { part: 1, parts: 2, pass: "plan_reused" } })).lines[0]).toBe("Planning questions · part 1 of 2 · kept from before");
  });

  it("topics are counted only once a whole plan was read; before that, the step alone", () => {
    expect(words(build({ stage: "checking", synthesis: undefined, draftedTopics: 8 })).lines[0]).toBe("8 topics drafted · checking them");
    expect(words(build({ stage: "checking", synthesis: undefined })).lines[0]).toBe("Checking the plan");
    expect(words(build({ stage: "organizing", synthesis: undefined })).lines[0]).toBe("Organizing the topics");
    expect(words(build({ stage: "saving", synthesis: undefined })).lines[0]).toBe("Saving the plan");
    expect(words(build({ stage: "queued", synthesis: undefined, delivery: null })).lines).toEqual(["Waiting to start", "Started 2 minutes ago"]);
    expect(said(words(build()))).not.toMatch(/topic/);
  });

  it("a measured time says how many builds it rests on", () => {
    expect(words(build({ measured: { minutes: 4.2, samples: 3 } })).details).toContain(
      "Earlier builds in this library took about 4 minutes for a book this size (from 3 builds).");
    expect(words(build({ measured: { minutes: 0.4, samples: 1 } })).details).toContain(
      "Earlier builds in this library took under a minute for a book this size (from 1 build).");
  });

  it("on the phone, clock times instead of ages", () => {
    const result = buildWaitWords(build(), { clock: "at", grew: false });
    expect(result.lines[1]).toMatch(/^Started at \d{1,2}:\d{2}(\s?[AP]M)? · asked at \d{1,2}:\d{2}(\s?[AP]M)?, no reply yet$/);
    expect(result.lines[1]).not.toMatch(/ago/);
  });
});

describe("a section's questions being written", () => {
  it("0 of 4 done and nothing measured: the topic, since when, and that the first can take a few minutes", () => {
    const result = writingWaitWords(writing(), { clock: "ago", grew: false });
    expect(result.lines).toEqual([
      "Writing topic 1 of 4: “Spectral theorem”",
      "Started 1 minute ago · asked 1 minute ago, no reply yet",
      FIRST_QUESTIONS_TIME
    ]);
    expect(result.details).toEqual([]);
    assertNothingInvented(said(result));
  });

  it("0 of 4 done with output advancing: still writing", () => {
    const arriving = writing({ delivery: delivery({ requestSentAt: ago(75), outputPieces: 40, lastOutputAt: ago(2) }) });
    expect(writingWaitWords(arriving, { clock: "ago", grew: true }).lines[1]).toBe("Started 1 minute ago · still writing");
  });

  it("with this library's measured time per topic, and the count it rests on", () => {
    const result = writingWaitWords(writing({ measured: { minutes: 2.3, samples: 3 } }), { clock: "ago", grew: false });
    expect(result.lines[2]).toBe("Here a topic's questions have taken about 2 minutes to write.");
    expect(result.details).toEqual(["Measured on the last 3 topics written in this library."]);
    expect(result.lines).not.toContain(FIRST_QUESTIONS_TIME);
  });

  it("beside other writing, the topic by its name alone (its place would not be among the topics the line counts)", () => {
    const result = writingWaitWords(writing({ topic: { title: "Spectral theorem", index: null, total: null } }), { clock: "ago", grew: false });
    expect(result.lines[0]).toBe("Writing questions on “Spectral theorem”");
  });

  it("waiting its turn, and a retry", () => {
    expect(writingWaitWords(writing({ queued: true, topic: null, delivery: null }), { clock: "ago", grew: false }).lines).toEqual(["Waiting to start", FIRST_QUESTIONS_TIME]);
    const retry = writingWaitWords(writing({ retry: true }), { clock: "ago", grew: false });
    expect(retry.lines[0]).toBe("Trying again · Writing topic 1 of 4: “Spectral theorem”");
    expect(retry.details).toContain("An earlier try stopped; topics already written are kept and not written again.");
  });
});

describe("whether the reply grew since the previous read", () => {
  it("is told only by a later part or more parts, never on a first read", () => {
    const first = delivery({ requestSentAt: ago(40), outputPieces: 3, lastOutputAt: ago(10) });
    expect(replyGrew(first, null)).toBe(false);
    expect(replyGrew(first, first)).toBe(false);
    expect(replyGrew(delivery({ requestSentAt: ago(40), outputPieces: 9, lastOutputAt: ago(1) }), first)).toBe(true);
    expect(replyGrew(delivery({ requestSentAt: ago(40) }), first)).toBe(false);
  });
});
