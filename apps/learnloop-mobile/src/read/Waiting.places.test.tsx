// "Waiting you can see" on the phone (docs/reviews/ux-waiting.md), the rest of the inventory in the
// same pattern: app start (today's plan, or today's list with the plan off), the Read tab's books,
// opening a book's section, and the plan's other options. Each: nothing before the indicator's
// delay, the line after it, gone when what was read is there. From the tap (or the start) on, only
// the timers are fake (IndexedDB's setImmediate stays real).
import { vi } from "vitest";
import {
  act, answers, App, describe, expect, fakeFetch, fireEvent, installFakeHost, it, render, screen
} from "../test/fakeHost";
import { afterEach, beforeEach } from "vitest";

installFakeHost();
afterEach(() => { vi.useRealTimers(); });

function hold(method: string): () => void {
  let release!: () => void;
  const gate = new Promise<void>((done) => { release = done; });
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    if (String(input) === "/rpc" && JSON.parse(init?.body as string).method === method) await gate;
    return fakeFetch(input, init);
  }));
  return release;
}
function fakeTimers() {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval"] });
}
async function advance(ms: number) {
  await act(async () => { await vi.advanceTimersByTimeAsync(ms); });
}
async function until(seen: () => unknown) {
  for (let turn = 0; turn < 200 && !seen(); turn += 1) await advance(0);
  expect(seen()).toBeTruthy();
}
async function settle(seen: () => unknown) {
  for (let turn = 0; turn < 100 && !seen(); turn += 1) await advance(250);
  expect(seen()).toBeTruthy();
}
/** The shared check: the region is there and empty until the delay, then says `line`. */
async function saysAfterTheDelay(testId: string, line: string) {
  await until(() => screen.queryByTestId(testId));
  await advance(349);
  expect(screen.getByTestId(testId).textContent).toBe("");
  await advance(1);
  expect(screen.getByTestId(testId).textContent).toBe(`◐ ${line}`);
}

const block = {
  id: "b1", ordinal: 1, lane: "maintain", action: "maintain", subtype: null, chosenBy: "lane_quota", why: "These are due today.",
  whyKind: null, whyDetails: null, fallback: false, estMinutes: 5, status: "current", startedAt: null, endedAt: null, outcome: null,
  reading: null, learningObjectTitles: ["Topic i1"], displacedCount: 0,
  items: [{ practiceItemId: "i1", learningObjectId: "lo", learningObjectTitle: "Topic i1", practiceMode: null, promptPreview: "", lane: "maintain",
    estMinutes: 2.5, state: "planned", origin: "chooser", servedAt: null, doneAt: null }]
};
const reply = (rest: Record<string, unknown> = {}) => ({
  version: 1, enabled: true, headlineEnabled: false, localDate: "2026-11-08",
  plan: {
    id: "p1", localDate: "2026-11-08", kind: "normal", status: "open", stopReason: null, parentPlanId: null, minutesBudget: 25, rememberedMinutes: 25,
    minutesSource: "carried", minuteChoices: [10, 25, 40], minutesLeft: 25,
    split: { rule: "r", line: "", lanesAllowed: ["maintain"], requestedMinutes: 0, lanes: [] }, admission: {}, blocks: [block],
    currentBlockId: "b1", deciding: false, waiting: null, projected: [], blockCountEstimate: 1, firstBlock: null, nextStep: null,
    totals: {}, reentry: null, source: "s", chooser: "c", estimatorVersion: "e", algorithmVersion: "a"
  },
  day: { plans: 1, kinds: ["normal"], complete: false, actualMinutes: 0, plannedItems: 1, readingBlocks: 0 }, streak: null,
  device: { surface: "phone_plan", deferredCount: 0, readingsWaiting: 0 }, ...rest
});

describe("app start", () => {
  it("today's plan: 'Reading today's plan…' after the delay, gone when the plan is there", async () => {
    answers.get_daily_plan = reply();
    const release = hold("get_daily_plan");
    fakeTimers();
    render(<App />);
    await saysAfterTheDelay("plan-wait", "Reading today's plan…");
    release();
    await settle(() => screen.queryByRole("button", { name: "Begin" }));
    expect(screen.queryByTestId("plan-wait")).toBeNull();
  });

  it("with the plan off, today's list once the minutes are chosen: 'Reading today's list…', gone when the list is there", async () => {
    render(<App />);
    const minutes = await screen.findByRole("button", { name: "15 min" });
    const release = hold("get_today_queue");
    fakeTimers();
    fireEvent.click(minutes);
    await saysAfterTheDelay("list-wait", "Reading today's list…");
    release();
    await settle(() => screen.queryByRole("button", { name: /^Next: Topic i1/ }));
    expect(screen.queryByTestId("list-wait")).toBeNull();
  });
});

describe("the plan's other options", () => {
  it("'Looking at what the plan could do…' after the delay, gone when the options are there", async () => {
    answers.get_daily_plan = reply({ somethingElse: true });
    answers.next_plan_item = reply({ somethingElse: true, step: { kind: "item", planId: "p1", blockId: "b1", practiceItemId: "i1", learningObjectId: "lo",
      learningObjectTitle: "Topic i1", origin: "chooser", schedulerCandidateId: "cand_i1", presentationId: "pp_i1", boundary: false } });
    answers.plan_something_else_options = { version: 1, enabled: true, drawn: false, decisionId: null, device: "phone",
      options: [{ kind: "question", ref: "cand_q", label: "Another question", minutes: 5, propensity: null, plansPick: false, servable: true }] };
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Begin" }));
    await screen.findByText("Define it.");
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "My answer";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("3 / 4");
    const link = await screen.findByRole("button", { name: "Something else would help" });
    const release = hold("plan_something_else_options");
    fakeTimers();
    fireEvent.click(link);
    await saysAfterTheDelay("options-wait", "Looking at what the plan could do…");
    release();
    await settle(() => screen.queryByText("Another question", { exact: false }));
    expect(screen.queryByTestId("options-wait")).toBeNull();
  });
});

describe("the Reader", () => {
  beforeEach(() => {
    Object.assign(answers, {
      get_source_library: { sources: [{ sourceId: "src1", title: "Linear Algebra Done Right", extractionId: "ext1", readerEnabled: true }] },
      "reader.guide_plan": { version: 1, sourceId: "src1", extractionId: "ext1", personalized: false, selectionBasis: "x", goalContext: null,
        sections: [{ id: "u1", label: "1 Vectors", startSpanId: "b0", endSpanId: "b0", spanIds: ["b0"], question: null, suggestedPassages: [] }] },
      "reader.render_view": { version: 1, renderViewId: "rv1", extractionId: "ext1", revisionId: "rev1", sourceId: "src1", renderer: "r",
        rendererVersion: "1", contentHash: "c1", status: "ok", layers: {}, protection: { withheld: false, heldOutSpanIds: [], message: null },
        range: { sectionId: "u1", fromSpanId: null, toSpanId: null, blockCount: 1 },
        blocks: [{ displayNodeId: "node-b0", spanId: "b0", blockType: "Text", markdown: "Every space has a zero.", sanitized: false, katexNodes: [],
          assets: [], health: { status: "ok", recommendedView: "derived", reasonFlags: [] }, page: 0 }] },
      "reader.get_progress": { version: 1, extractionId: "ext1", sections: [] },
      "reader.mark_section_progress": { progress: {}, enqueuedGeneration: false, batchId: null },
      "reader.log_activity": { recorded: 1 },
      "reader.dose_offer": { version: 1, eligible: false, reason: "switch_off", drawId: null, offer: null }
    });
  });

  it("the Read tab: 'Reading your books…' after the delay, gone when the books are listed", async () => {
    render(<App />);
    const read = await screen.findByRole("button", { name: "Read" });
    const release = hold("get_source_library");
    fakeTimers();
    fireEvent.click(read);
    await saysAfterTheDelay("books-wait", "Reading your books…");
    release();
    await settle(() => screen.queryByRole("button", { name: /Linear Algebra Done Right/ }));
    expect(screen.queryByTestId("books-wait")).toBeNull();
  });

  it("opening a book: 'Opening the section…' after the delay, gone when its text is there", async () => {
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Read" }));
    const book = await screen.findByRole("button", { name: /Linear Algebra Done Right/ });
    const release = hold("reader.render_view");
    fakeTimers();
    fireEvent.click(book);
    await saysAfterTheDelay("section-wait", "Opening the section…");
    release();
    await settle(() => screen.queryByText("Every space has a zero."));
    expect(screen.queryByTestId("section-wait")).toBeNull();
  });
});
