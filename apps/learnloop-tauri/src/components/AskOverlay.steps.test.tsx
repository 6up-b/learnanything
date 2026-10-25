// Owner capture 2026-10-25 (B1): an Ask from "Work in steps" sends the steps
// as the learner's work with every practice question (the answer box's
// draft is still sent only with "Explain this with my work", as before).
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { AskOverlay, type AskTarget } from "./AskOverlay";

const { api } = vi.hoisted(() => ({ api: {
  getTutorTranscript: vi.fn(), askTutorQuestion: vi.fn(), previewTutorOpening: vi.fn(),
  getLearnerTextGap: vi.fn(), reverseLearnerTextGap: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: () => null }));
vi.mock("./OpenInSource", () => ({ OpenInSource: () => null }));

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.getTutorTranscript.mockResolvedValue({ events: [], remaining: 3 });
  api.askTutorQuestion.mockResolvedValue({
    version: 1, eventId: "event-1", answerMd: "Look at step 2.", questionType: "strategy",
    facets: [], hintEquivalent: true, leakSuspected: false, citations: [], remaining: 2
  });
});
afterEach(() => { cleanup(); });

async function ask(target: AskTarget) {
  render(<AskOverlay target={target} onClose={vi.fn()} onToast={vi.fn()} />);
  await waitFor(() => expect(api.getTutorTranscript).toHaveBeenCalledOnce());
  const input = screen.getByPlaceholderText("ask a question — enter sends");
  fireEvent.change(input, { target: { value: "Is step 2 right?" } });
  fireEvent.keyDown(input, { key: "Enter" });
  await waitFor(() => expect(api.askTutorQuestion).toHaveBeenCalledOnce());
  return api.askTutorQuestion.mock.calls[0][0];
}

it("sends the steps as the work with a practice question asked from steps", async () => {
  const payload = await ask({
    context: "practice", practiceItemId: "pi_1", sessionId: "s1", attemptProgress: "draft_started",
    workMd: "1. F(x) = x^2\n2. P = F(1/2) + 1",
  });
  expect(payload.learnerDraftMd).toBe("1. F(x) = x^2\n2. P = F(1/2) + 1");
});

it("an answer-box draft is not sent with an ordinary question (unchanged)", async () => {
  const payload = await ask({ context: "practice", practiceItemId: "pi_1", sessionId: "s1", draftMd: "F(x) = x^2" });
  expect(payload).not.toHaveProperty("learnerDraftMd");
});
