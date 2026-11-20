// "Waiting you can see" on the phone (docs/reviews/ux-waiting.md), through the fake host: the
// owner's case 1 (Today's Begin and Next to the question) and case 2 (Submit to the feedback),
// in the desktop's words. Each wait: nothing before the indicator's delay, the line after it,
// gone when the next screen is there. The screen is reached on real timers; from the tap on,
// only the timers are fake (IndexedDB's setImmediate stays real, so the app's storage runs).
import { CAN_LEAVE, WAIT_LATER_MS } from "../components/Waiting";
import {
  act, answers, App, beginSession, describe, expect, fakeFetch, fireEvent, installFakeHost, it, render, screen, vi
} from "../test/fakeHost";
import { afterEach } from "vitest";

installFakeHost();
afterEach(() => { vi.useRealTimers(); });

/** Holds every `/rpc` call to `method` until released; everything else answers at once. */
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

/** Lets the app's promises and storage run, without moving the fake clock, until `seen` holds. */
async function until(seen: () => unknown) {
  for (let turn = 0; turn < 200 && !seen(); turn += 1) await advance(0);
  expect(seen()).toBeTruthy();
}

async function openQuestion() {
  await beginSession();
  fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
  await screen.findByText("Define it.");
  const editor = screen.getByRole("textbox", { name: "Your answer" });
  editor.textContent = "My answer";
  fireEvent.input(editor);
}

const block = () => ({
  id: "b1", ordinal: 1, lane: "maintain", action: "maintain", subtype: null, chosenBy: "lane_quota", why: "These are due today.",
  whyKind: null, whyDetails: null, fallback: false, estMinutes: 5, status: "current", startedAt: null, endedAt: null, outcome: null,
  reading: null, learningObjectTitles: ["Topic i1"], displacedCount: 0,
  items: [{ practiceItemId: "i1", learningObjectId: "lo", learningObjectTitle: "Topic i1", practiceMode: null, promptPreview: "", lane: "maintain",
    estMinutes: 2.5, state: "planned", origin: "chooser", servedAt: null, doneAt: null }]
});
const reply = (rest: Record<string, unknown> = {}) => ({
  version: 1, enabled: true, headlineEnabled: false, localDate: "2026-11-06",
  plan: {
    id: "p1", localDate: "2026-11-06", kind: "normal", status: "open", stopReason: null, parentPlanId: null, minutesBudget: 25, rememberedMinutes: 25,
    minutesSource: "carried", minuteChoices: [10, 25, 40], minutesLeft: 25,
    split: { rule: "r", line: "", lanesAllowed: ["maintain"], requestedMinutes: 0, lanes: [] }, admission: {}, blocks: [block()],
    currentBlockId: "b1", deciding: false, waiting: null, projected: [], blockCountEstimate: 1, firstBlock: null, nextStep: null,
    totals: {}, reentry: null, source: "s", chooser: "c", estimatorVersion: "e", algorithmVersion: "a"
  },
  day: { plans: 1, kinds: ["normal"], complete: false, actualMinutes: 0, plannedItems: 1, readingBlocks: 0 }, streak: null,
  device: { surface: "phone_plan", deferredCount: 0, readingsWaiting: 0 }, ...rest
});
const itemStep = (id = "i1") => ({
  kind: "item", planId: "p1", blockId: "b1", practiceItemId: id, learningObjectId: "lo", learningObjectTitle: `Topic ${id}`, origin: "chooser",
  schedulerCandidateId: `cand_${id}`, presentationId: `pp_${id}`, boundary: false
});

describe("case 1: Today to the question", () => {
  it("the plan's Begin: 'Choosing what's next…' after the delay, gone when the question is on screen", async () => {
    answers.get_daily_plan = reply();
    answers.next_plan_item = reply({ step: itemStep() });
    render(<App />);
    const begin = await screen.findByRole("button", { name: "Begin" });
    const release = hold("next_plan_item");
    fakeTimers();
    fireEvent.click(begin);
    await until(() => screen.queryByTestId("choosing-wait"));
    await advance(349);
    expect(screen.getByTestId("choosing-wait").textContent).toBe("");
    await advance(1);
    expect(screen.getByTestId("choosing-wait").textContent).toBe("◐ Choosing what's next…");
    release();
    await until(() => screen.queryByText("Define it."));
    expect(screen.queryByTestId("choosing-wait")).toBeNull();
  });

  it("Next on today's list: 'Opening the question…' while the question is read", async () => {
    await beginSession();
    const release = hold("get_practice_item");
    fakeTimers();
    fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
    await until(() => screen.queryByTestId("question-wait"));
    await advance(349);
    expect(screen.queryByText(/Opening the question…/)).toBeNull();
    await advance(1);
    const line = screen.getByTestId("question-wait");
    expect(line.getAttribute("role")).toBe("status");
    expect(line.textContent).toBe("◐ Opening the question…");
    release();
    await until(() => screen.queryByText("Define it."));
    expect(screen.queryByTestId("question-wait")).toBeNull();
  });
});

describe("case 2: the question to the feedback", () => {
  it("Submit: 'Checking your answer…', then what is normal and that the learner can leave, gone when the grade shows", async () => {
    await openQuestion();
    const release = hold("submit_attempt");
    fakeTimers();
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await until(() => screen.queryByTestId("grading-wait"));
    await advance(349);
    expect(screen.queryByText(/Checking your answer…/)).toBeNull();
    await advance(1);
    expect(screen.getByTestId("grading-wait").textContent).toBe("◐ Checking your answer…");
    await advance(WAIT_LATER_MS);
    expect(screen.getByTestId("grading-wait-later").textContent).toBe(`This can take a minute. ${CAN_LEAVE}`);
    release();
    await until(() => screen.queryByText("3 / 4"));
    expect(screen.queryByTestId("grading-wait")).toBeNull();
  });

  it("the feedback's read: 'Opening your feedback…' after the delay, gone when the feedback shows", async () => {
    await openQuestion();
    const release = hold("get_feedback");
    fakeTimers();
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await until(() => screen.queryByTestId("feedback-wait"));
    await advance(349);
    expect(screen.queryByText(/Opening your feedback…/)).toBeNull();
    await advance(1);
    expect(screen.getByTestId("feedback-wait").textContent).toBe("◐ Opening your feedback…");
    release();
    await until(() => screen.queryByText("3 / 4"));
    expect(screen.queryByTestId("feedback-wait")).toBeNull();
  });

  it("Next on the feedback under the plan: 'Choosing what's next…', gone when the next question is on screen", async () => {
    answers.get_daily_plan = reply();
    answers.next_plan_item = reply({ step: itemStep() });
    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Begin" }));
    await screen.findByText("Define it.");
    const editor = screen.getByRole("textbox", { name: "Your answer" });
    editor.textContent = "My answer";
    fireEvent.input(editor);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("3 / 4");
    answers.next_plan_item = reply({ step: itemStep("i2") });
    answers.get_practice_item = { ...(answers.get_practice_item as object), id: "i2" };
    const release = hold("next_plan_item");
    fakeTimers();
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await until(() => screen.queryByTestId("choosing-wait"));
    await advance(349);
    expect(screen.queryByText(/Choosing what's next…/)).toBeNull();
    await advance(1);
    expect(screen.getByTestId("choosing-wait").textContent).toBe("◐ Choosing what's next…");
    release();
    await until(() => !screen.queryByText("3 / 4"));
    expect(screen.queryByTestId("choosing-wait")).toBeNull();
  });
});
