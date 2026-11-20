// "Waiting you can see" (docs/reviews/ux-waiting.md, the owner's case 3): the
// tutor's reply being written says so through the shared waiting line (it
// arrives whole, so the line stays until it lands), with what is normal for a
// long wait; in the Reader the mark is still (G54).
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import { AskOverlay, type AskTarget } from "./AskOverlay";
import { WAIT_LATER_MS } from "./Waiting";

const { api } = vi.hoisted(() => ({ api: {
  getTutorTranscript: vi.fn(), askTutorQuestion: vi.fn(), previewTutorOpening: vi.fn(),
  getLearnerTextGap: vi.fn(), reverseLearnerTextGap: vi.fn(), setHelpStyle: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("./OpenInSource", () => ({ OpenInSource: () => null }));

const PRACTICE: AskTarget = {
  context: "practice", practiceItemId: "pi_1", sessionId: "s1", submissionId: "serve-2",
  attemptProgress: "draft_started", readDraft: () => "my draft now", itemLabel: "Exercise 6.1.12"
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}
async function advance(ms: number) {
  await act(async () => { await vi.advanceTimersByTimeAsync(ms); });
}

beforeEach(() => {
  vi.useFakeTimers();
  for (const mock of Object.values(api)) mock.mockReset();
  setAlgoConfig({ ask: { panelEnabled: true, helpStyle: "balanced" } });
  api.getTutorTranscript.mockResolvedValue({ events: [], remaining: 3, earlier: [], earlierCountsAsHint: true, cold: false, helpStyle: "balanced" });
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  setAlgoConfig({});
});

it("the panel's question: nothing before the delay, 'Writing a reply…', then what is normal, gone when the answer lands", async () => {
  const reply = deferred<unknown>();
  api.askTutorQuestion.mockReturnValue(reply.promise);
  render(<AskOverlay variant="docked" target={PRACTICE} onClose={vi.fn()} onToast={vi.fn()} />);
  await advance(0);
  const input = screen.getByLabelText("ask in your words");
  fireEvent.change(input, { target: { value: "What does V mean?" } });
  fireEvent.keyDown(input, { key: "Enter" });
  await advance(300);
  expect(screen.queryByText("Writing a reply…")).toBeNull();
  await advance(100);
  const line = screen.getByTestId("ask-writing");
  expect(line.getAttribute("role")).toBe("status");
  expect(line.textContent).toBe("◐ Writing a reply…");
  expect(screen.getByText("◐").getAttribute("data-motion")).toBe("moving");
  await advance(WAIT_LATER_MS);
  expect(screen.getByTestId("ask-writing-later").textContent).toBe("This can take a minute.");
  reply.resolve({ version: 1, eventId: "event-1", answerMd: "Look at the definition.", questionType: "clarification", facets: [],
                  hintEquivalent: false, leakSuspected: false, citations: [], remaining: 2, answerMode: "help_me_reason" });
  await advance(0);
  expect(screen.getByText("Look at the definition.")).toBeTruthy();
  expect(screen.queryByTestId("ask-writing")).toBeNull();
});
