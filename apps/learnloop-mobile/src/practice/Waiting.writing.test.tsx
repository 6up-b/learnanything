// "Waiting you can see" on the phone (docs/reviews/ux-waiting.md), the owner's case 3: a model
// writing while the learner watches. The Reader's Ask ("Writing a reply…", then what is normal),
// a miss being looked into, and a grade looked at again. Each: nothing before the indicator's
// delay, the line after it, gone when the result is there. Reached on real timers; from the tap
// on, only the timers are fake (IndexedDB's setImmediate stays real).
import { WAIT_LATER_MS } from "../components/Waiting";
import { SelectionSheet } from "../read/SelectionSheet";
import {
  act, answers, beginSession, describe, expect, fakeFetch, feedback, fireEvent, installFakeHost, it, render, screen, vi, type Call
} from "../test/fakeHost";
import { afterEach } from "vitest";

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
/** Runs the app's promises and storage without moving the clock, until `seen` holds. */
async function until(seen: () => unknown) {
  for (let turn = 0; turn < 200 && !seen(); turn += 1) await advance(0);
  expect(seen()).toBeTruthy();
}
/** After a release: lets polls and their timers run too. */
async function settle(seen: () => unknown) {
  for (let turn = 0; turn < 100 && !seen(); turn += 1) await advance(250);
  expect(seen()).toBeTruthy();
}
async function submitAnAnswer() {
  await beginSession();
  fireEvent.click(screen.getByRole("button", { name: /^Next: Topic i1/ }));
  await screen.findByText("Define it.");
  const editor = screen.getByRole("textbox", { name: "Your answer" });
  editor.textContent = "My answer";
  fireEvent.input(editor);
}

describe("a model writing while the learner watches", () => {
  it("the Reader's Ask: 'Writing a reply…', then what is normal, gone when the reply is there", async () => {
    answers["reader.ask"] = { eventId: "e1", readerAnswerEventId: "ra1", answerMd: "Because the axioms say so.", answerMode: "explain",
      citations: [], manifest: {}, warmedSurfaceIds: [], burnedSurfaceIds: [], hintEquivalent: false, remaining: 4 };
    const section = {
      version: 1, renderViewId: "rv1", extractionId: "ext1", revisionId: "rev1", sourceId: "src1", renderer: "r", rendererVersion: "1",
      contentHash: "c", status: "ok", blocks: [], layers: {}, protection: { withheld: false, heldOutSpanIds: [], message: null }
    };
    render(<SelectionSheet selection={{ spanIds: ["b1"], quote: "Every vector space has a zero vector." }} section={section as never}
      askOff={false} protectionMessage={null} onClose={() => undefined} onError={() => undefined} />);
    fireEvent.change(screen.getByLabelText("Your question"), { target: { value: "Why is there one?" } });
    const release = hold("reader.ask");
    fakeTimers();
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await until(() => screen.queryByTestId("ask-writing"));
    await advance(349);
    expect(screen.queryByText("Writing a reply…")).toBeNull();
    await advance(1);
    expect(screen.getByTestId("ask-writing").textContent).toBe("◐ Writing a reply…");
    await advance(WAIT_LATER_MS);
    expect(screen.getByTestId("ask-writing-later").textContent).toBe("This can take a minute.");
    release();
    await settle(() => screen.queryByText("Because the axioms say so."));
    expect(screen.queryByTestId("ask-writing")).toBeNull();
  });

  it("a miss being looked into: the phone's own words through the shared line, gone when the look lands", async () => {
    answers.get_feedback = (call: Call) =>
      call.params.recordOpen === false ? { ...feedback(), diagnosisStatus: "done" } : { ...feedback(), diagnosisStatus: "pending" };
    let polls = 0;
    const card = { version: 1, attemptId: "a1", status: "done", cardEnabled: true, responses: [], summaryMd: "You stopped early." };
    answers.diagnosis_status = () => (++polls > 1 ? card : { ...card, status: "pending" });
    await submitAnAnswer();
    fakeTimers();
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await until(() => screen.queryByTestId("diagnosis-wait"));
    await advance(349);
    expect(screen.queryByText("Looking into what happened here…")).toBeNull();
    await advance(1);
    expect(screen.getByTestId("diagnosis-wait").textContent).toBe("◐ Looking into what happened here…");
    await settle(() => screen.queryByText("You stopped early."));
    expect(screen.queryByTestId("diagnosis-wait")).toBeNull();
  });

  it("a grade looked at again: 'Looking again…' after the delay, gone when the answer is back", async () => {
    answers.trigger_regrade = { ...feedback(), contest: { recorded: true, regraded: true, reviewRequested: true } };
    await submitAnAnswer();
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("3 / 4");
    fireEvent.click(screen.getByRole("button", { name: "I think I was right" }));
    fireEvent.change(screen.getByLabelText(/Why do you think you were right/), { target: { value: "The other convention." } });
    const release = hold("trigger_regrade");
    fakeTimers();
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await until(() => screen.queryByTestId("contest-wait"));
    await advance(349);
    expect(screen.queryByText("Looking again…")).toBeNull();
    await advance(1);
    expect(screen.getByTestId("contest-wait").textContent).toBe("◐ Looking again…");
    release();
    await settle(() => screen.queryByText("Noted. The grade will be looked at again."));
    expect(screen.queryByTestId("contest-wait")).toBeNull();
  });
});
