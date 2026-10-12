import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { AskOverlay, type AskTarget } from "./AskOverlay";

const { api } = vi.hoisted(() => ({ api: {
  getTutorTranscript: vi.fn(), askTutorQuestion: vi.fn(), previewTutorOpening: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: () => null }));
vi.mock("./OpenInSource", () => ({ OpenInSource: () => null }));

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.getTutorTranscript.mockResolvedValue({ events: [], remaining: 3 });
  api.askTutorQuestion.mockResolvedValue({
    version: 1, eventId: "event-1", answerMd: "Start from the definition.", questionType: "strategy",
    facets: [], hintEquivalent: true, leakSuspected: false, citations: [], remaining: 2
  });
});
afterEach(() => { cleanup(); vi.useRealTimers(); });

async function ask(target: AskTarget) {
  render(<AskOverlay target={target} onClose={vi.fn()} onToast={vi.fn()} />);
  await waitFor(() => expect(api.getTutorTranscript).toHaveBeenCalledOnce());
  const input = screen.getByPlaceholderText("ask a question — enter sends");
  fireEvent.change(input, { target: { value: "Where do I even start?" } });
  fireEvent.keyDown(input, { key: "Enter" });
  await waitFor(() => expect(api.askTutorQuestion).toHaveBeenCalledOnce());
  return api.askTutorQuestion.mock.calls[0][0];
}

// Re-review F5: elapsed time is fractional, so "help before any work" travels
// as the explicit draft state. tests/test_field_signal_production_paths.py
// replays this payload through the sidecar and the learner-field loader.
it("sends the practice screen's no-work-yet marker with the fractional elapsed time", async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(10_000);
  const payload = await ask({
    context: "practice", practiceItemId: "pi_svd_define_001", sessionId: "session-1",
    openedAtMs: 10_000 - 2_537, attemptProgress: "no_draft"
  });
  expect(payload).toEqual({
    context: "practice", question: "Where do I even start?", practiceItemId: "pi_svd_define_001",
    attemptId: undefined, noteId: undefined, sessionId: "session-1",
    secondsIntoAttempt: 2.537, attemptProgress: "no_draft"
  });
});

it("keeps the draft state off other contexts", async () => {
  const payload = await ask({ context: "feedback", attemptId: "attempt-1", attemptProgress: "no_draft" });
  expect(payload).not.toHaveProperty("attemptProgress");
  expect(payload).not.toHaveProperty("secondsIntoAttempt");
});
