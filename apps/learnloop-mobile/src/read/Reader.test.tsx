// Mobile v2 V4's Reader journeys through the fake host (§7.3): a book from the Read tab, a section's text with
// its math, a held-out passage that never arrives, the next section prefetched and read offline, progress and
// the end of a section through the outbox (each under its own key), the dose offer, and a plan's reading.
import { vi } from "vitest";
import {
  answers, App, beforeEach, called, calls, describe, expect, fakeFetch, fireEvent, installFakeHost, it, render, screen, waitFor
} from "../test/fakeHost";
import { getSection } from "../store/displayCache";
import { listReaderIntents } from "../store/outbox";

installFakeHost();

const guide = {
  version: 1, sourceId: "src1", extractionId: "ext1", personalized: false, selectionBasis: "x", goalContext: null,
  sections: [
    { id: "u1", label: "1 Vectors", startSpanId: "b0", endSpanId: "b2", spanIds: ["b0", "b1", "b2"], question: null, suggestedPassages: [] },
    { id: "u2", label: "2 Spans", startSpanId: "b3", endSpanId: "b4", spanIds: ["b3", "b4"], question: null, suggestedPassages: [] }
  ]
};
const block = (span: string, markdown: string, extra: Record<string, unknown> = {}) => ({
  displayNodeId: `node-${span}`, spanId: span, blockType: "Text", markdown, sanitized: false, katexNodes: [], assets: [],
  health: { status: "ok", recommendedView: "derived", reasonFlags: [] }, page: 0, ...extra
});
// The protection is the whole reading's, whatever the section (the host's ranged reply says so).
const READING_PROTECTION = { withheld: false, heldOutSpanIds: ["b4"], message: "held out" };
const section = (sectionId: string, blocks: unknown[], protection = READING_PROTECTION) => ({
  version: 1, renderViewId: "rv1", extractionId: "ext1", revisionId: "rev1", sourceId: "src1", renderer: "r", rendererVersion: "1",
  contentHash: "c1", status: "ok", blocks, layers: {}, protection,
  range: { sectionId, fromSpanId: null, toSpanId: null, blockCount: 5 }
});
const SECTIONS: Record<string, unknown> = {
  u1: section("u1", [block("b0", "# 1 Vectors"), block("b1", "Addition commutes: $u + v = v + u$."), block("b2", "Every space has a zero.")]),
  u2: section("u2", [block("b3", "# 2 Spans"), block("b4", "", { withheld: true })])
};

beforeEach(() => {
  Object.assign(answers, {
    get_source_library: { sources: [{ sourceId: "src1", title: "Linear Algebra Done Right", extractionId: "ext1", readerEnabled: true }] },
    "reader.guide_plan": guide,
    "reader.render_view": (call: { params: Record<string, unknown> }) => SECTIONS[String(call.params.sectionId)],
    "reader.get_progress": { version: 1, extractionId: "ext1", sections: [] },
    "reader.mark_section_progress": { progress: {}, enqueuedGeneration: false, batchId: null },
    "reader.log_activity": { recorded: 1 },
    "reader.dose_offer": { version: 1, eligible: false, reason: "switch_off", drawId: null, offer: null }
  });
});

async function openBook() {
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Read" }));
  fireEvent.click(await screen.findByRole("button", { name: /Linear Algebra Done Right/ }));
  await screen.findByText("Every space has a zero.");
}

describe("the phone Reader (mobile v2 §3)", () => {
  it("opens a book at its first section, by section, with its math, and prefetches the next", async () => {
    await openBook();
    expect(document.querySelector(".katex")).not.toBeNull();
    expect(called("reader.render_view").map((call) => call.params)).toEqual([
      { extractionId: "ext1", sectionId: "u1" }, { extractionId: "ext1", sectionId: "u2" }
    ]);
    expect(window.location.hash).toBe("#/read/ext1/u1");
    // The Reader covers the tab bar; Back is the book list.
    expect(screen.queryByRole("navigation")).toBeNull();
    expect(screen.getByRole("button", { name: "Back to your books" })).toBeTruthy();
  });

  it("a held-out passage arrives with no text and says so; its page is never asked for", async () => {
    await openBook();
    fireEvent.click(screen.getByRole("button", { name: "Next section" }));
    expect(await screen.findByText("A passage held out for your exam. It isn't shown here.")).toBeTruthy();
    expect(screen.getAllByRole("button", { name: "View the page" })).toHaveLength(1); // the heading's, not the held one's
  });

  it("the end of a section is the desktop's progress write, through the outbox, then the dose arm's draw", async () => {
    await openBook();
    fireEvent.click(screen.getByRole("button", { name: "Next section" }));
    await screen.findByText(/held out for your exam/);
    await waitFor(() => expect(called("reader.mark_section_progress")).toHaveLength(1));
    const [progress] = called("reader.mark_section_progress");
    expect(progress.params).toEqual({ extractionId: "ext1", sectionId: "u1", spansSeen: 3, spanCount: 3, completed: true });
    expect(progress.requestId).toMatch(/^[0-9A-Z]{26}$/);
    expect(called("reader.dose_offer")[0].params).toMatchObject({ extractionId: "ext1", sectionId: "u1" });
    // Activity carries its own time, so a late send keeps it.
    const opened = called("reader.log_activity")[0];
    expect((opened.params.events as Array<Record<string, unknown>>)[0]).toMatchObject({ kind: "reader_view_opened" });
    expect((opened.params.events as Array<Record<string, unknown>>)[0].occurredAt).toEqual(expect.any(String));
    await waitFor(async () => expect(await listReaderIntents()).toEqual([]));
  });

  it("offline, the opened section and the next stay readable, and progress waits in the outbox", async () => {
    await openBook();
    await waitFor(() => expect(called("reader.render_view")).toHaveLength(2));
    // The next section is on the phone before the signal goes.
    await waitFor(async () => expect(await getSection({ extractionId: "ext1", revision: "rv1", sectionId: "u2" })).not.toBeNull());
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("airplane mode"); }));
    fireEvent.click(screen.getByRole("button", { name: "Next section" }));
    expect(await screen.findByText(/held out for your exam/)).toBeTruthy();
    expect(screen.getByText("· the copy on this phone")).toBeTruthy();
    await waitFor(async () => {
      const waiting = await listReaderIntents();
      expect(waiting.some((one) => one.method === "reader.mark_section_progress" && one.params.completed === true)).toBe(true);
    });
    // Back in reach: the outbox sends it, under the key it was queued with.
    const queued = (await listReaderIntents()).find((one) => one.method === "reader.mark_section_progress")!;
    vi.stubGlobal("fetch", vi.fn(fakeFetch));
    window.dispatchEvent(new Event("online"));
    await waitFor(() => expect(called("reader.mark_section_progress").some((call) => call.requestId === queued.id)).toBe(true));
  });

  it("a dose offer shows the desktop's words and its why, and its events are queued under their own keys", async () => {
    answers["reader.dose_offer"] = {
      version: 1, eligible: true, reason: null, drawId: "draw_1",
      offer: { drawId: "draw_1", variant: "extra_worked_example", text: "One more worked example on this?", why: "Offered at random, to learn how much of this helps you", content: { extractionId: "ext1", spanId: "b3" } }
    };
    answers["reader.dose_offer_event"] = { recorded: true };
    await openBook();
    fireEvent.click(screen.getByRole("button", { name: "Next section" }));
    expect(await screen.findByText("One more worked example on this?")).toBeTruthy();
    expect(screen.getByText("Offered at random, to learn how much of this helps you")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Show me" }));
    await waitFor(() => expect(called("reader.dose_offer_event").map((call) => call.params.event)).toEqual(["delivered", "taken"]));
    const keys = called("reader.dose_offer_event").map((call) => call.requestId);
    expect(new Set(keys).size).toBe(2);
  });
});

describe("the Codex review of V4 (docs/reviews/phone-v4-codex-review.md)", () => {
  const extraQuestion = {
    version: 1, eligible: true, reason: null, drawId: "draw_q",
    offer: {
      drawId: "draw_q", variant: "extra_question", text: "One quick question on this?", why: "Offered at random, to learn how much of this helps you",
      content: { extractionId: "ext1", questionId: "aq_1" },
      question: { questionId: "aq_1", sectionId: "u1", prompt: "What does addition do with order?", expectedAnswer: "It commutes.", spanIds: ["b1"] }
    }
  };

  it("F8: a visit closes with its active and idle seconds, on the desktop's clock", async () => {
    const real = Date.now.bind(Date);
    let offset = 0;
    const clock = vi.spyOn(Date, "now").mockImplementation(() => real() + offset);
    try {
      await openBook();
      const opened = (called("reader.log_activity")[0].params.events as Array<Record<string, any>>)[0];
      expect(opened.payload).toMatchObject({ surface: "text", sourceId: "src1", initiator: "learner", askAvailable: true });
      offset = 45_000;
      fireEvent.click(screen.getByRole("button", { name: "Back to your books" }));
      await waitFor(() => expect(called("reader.log_activity").some((call) =>
        (call.params.events as Array<Record<string, any>>)[0].kind === "reader_view_closed")).toBe(true));
      const closed = called("reader.log_activity").map((call) => (call.params.events as Array<Record<string, any>>)[0])
        .find((event) => event.kind === "reader_view_closed")!;
      expect(closed.payload).toEqual({ visitId: opened.payload.visitId, extractionId: "ext1", activeSeconds: 45, idleSeconds: 0 });
    } finally {
      clock.mockRestore();
    }
  });

  it("F9: an extra question is offered first, and declining it shows nothing of it", async () => {
    answers["reader.dose_offer"] = extraQuestion;
    answers["reader.dose_offer_event"] = { recorded: true };
    await openBook();
    fireEvent.click(screen.getByRole("button", { name: "Next section" }));
    expect(await screen.findByText("One quick question on this?")).toBeTruthy();
    expect(screen.queryByText("What does addition do with order?")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Not now" }));
    await waitFor(() => expect(called("reader.dose_offer_event").map((call) => call.params.event)).toEqual(["delivered", "dismissed"]));
    expect(screen.queryByText("What does addition do with order?")).toBeNull();
    expect(called("reader.authored_question_action")).toEqual([]);
  });

  it("F9: a taken extra question is answered in the learner's words, recorded as the desktop's card records it", async () => {
    answers["reader.dose_offer"] = extraQuestion;
    answers["reader.dose_offer_event"] = { recorded: true };
    answers["reader.authored_question_action"] = { question: { questionId: "aq_1", status: "answered" } };
    await openBook();
    fireEvent.click(screen.getByRole("button", { name: "Next section" }));
    fireEvent.click(await screen.findByRole("button", { name: "Try it" }));
    expect(await screen.findByText("What does addition do with order?")).toBeTruthy();
    expect(screen.queryByText("It commutes.")).toBeNull();
    fireEvent.change(screen.getByRole("textbox", { name: "Your answer" }), { target: { value: "Order doesn't matter." } });
    fireEvent.click(screen.getByRole("button", { name: "Compare with the source" }));
    expect(await screen.findByText("It commutes.")).toBeTruthy();
    expect(called("reader.authored_question_action").map((call) => call.params)).toEqual([
      { questionId: "aq_1", action: "answered", response: "Order doesn't matter." }
    ]);
    await waitFor(() => expect(called("reader.dose_offer_event").map((call) => call.params.event)).toEqual(["delivered", "taken"]));
  });
});

const readingBlock = {
  id: "blk1", ordinal: 1, lane: "new", action: "read", subtype: null, chosenBy: "lane_quota", why: "Read on.", whyKind: null, whyDetails: null,
  fallback: false, estMinutes: 8, status: "current", startedAt: null, endedAt: null, outcome: null, learningObjectTitles: [], displacedCount: 0,
  items: [], reading: { sourceId: "src1", extractionId: "ext1", sectionId: "u1", sectionTitle: "1 Vectors", wordsLeft: 900, partial: false, fullMinutes: 8 }
};
const planReply = (step: unknown = null) => ({
  version: 1, enabled: true, headlineEnabled: false, localDate: "2026-11-07", streak: null,
  plan: {
    id: "p1", localDate: "2026-11-07", kind: "normal", status: "open", stopReason: null, parentPlanId: null, minutesBudget: 10,
    rememberedMinutes: 10, minutesSource: "carried", minuteChoices: [10, 25], minutesLeft: 10,
    split: { rule: "r", line: "", lanesAllowed: ["new"], requestedMinutes: 0, lanes: [] }, admission: {}, blocks: [readingBlock],
    currentBlockId: "blk1", deciding: false, waiting: null, projected: [], blockCountEstimate: 1, firstBlock: null, nextStep: null,
    totals: {}, reentry: null, source: "s", chooser: "c", estimatorVersion: "e", algorithmVersion: "a"
  },
  day: { plans: 1, kinds: ["normal"], complete: false, actualMinutes: 0, plannedItems: 0, readingBlocks: 1 },
  device: { surface: "phone_plan", deferredCount: 0, readingsWaiting: 0 },
  ...(step ? { step } : {})
});

describe("a plan's reading on the phone (V4 lifts V2's hold)", () => {
  it("Next opens the reading in the Reader with the desktop's banner, and Back to today's plan ends it", async () => {
    answers.get_daily_plan = planReply();
    answers.next_plan_item = planReply({
      kind: "reading", planId: "p1", blockId: "blk1", blockOrdinal: 1, boundary: true, estMinutes: 8,
      reading: { sourceId: "src1", extractionId: "ext1", sectionId: "u1", sectionTitle: "1 Vectors", wordsLeft: 900, partial: false, startSpanId: "b0", fullMinutes: 8 }
    });
    answers.plan_reading_ended = planReply();
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Begin" }));
    expect(await screen.findByText(/Reading for today's plan · 1 Vectors/)).toBeTruthy();
    expect(await screen.findByText("Every space has a zero.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Back to today's plan" }));
    await waitFor(() => expect(called("plan_reading_ended").map((call) => call.params)).toEqual([{ outcome: "left_reader", sessionId: "s1" }]));
    expect(calls.some((call) => call.method === "reader.render_view")).toBe(true);
  });
});
