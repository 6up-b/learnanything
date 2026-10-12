import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { AskOverlay } from "./AskOverlay";

const { api } = vi.hoisted(() => ({ api: {
  getTutorTranscript: vi.fn(), askTutorQuestion: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: () => null }));
vi.mock("./OpenInSource", () => ({ OpenInSource: () => null }));
const target = { context: "library" as const, initialQuestion: "Why?", captureId: "capture", subjectId: "subject" };
beforeEach(() => {
  vi.clearAllMocks();
  let sequence = 0;
  api.askTutorQuestion.mockImplementation(async () => ({ eventId: `event-${++sequence}`, answerMd: "Because", questionType: "mechanism",
    hintEquivalent: false, citations: [], remaining: 7, noteId: "note_capture" }));
});
afterEach(cleanup);

it("prefills without sending, then routes only the first successful question and anchors followups", async () => {
  render(<AskOverlay target={target} onClose={vi.fn()} onToast={vi.fn()} />);
  expect(screen.getByDisplayValue("Why?")).toBeTruthy();
  expect(api.askTutorQuestion).not.toHaveBeenCalled();
  expect(api.getTutorTranscript).not.toHaveBeenCalled();
  await act(async () => { fireEvent.keyDown(screen.getByRole("textbox"), { key: "Enter" }); });
  expect(api.askTutorQuestion.mock.calls[0][0]).toMatchObject({ captureId: "capture", subjectId: "subject", question: "Why?" });
  fireEvent.change(screen.getByRole("textbox"), { target: { value: "And then?" } });
  await act(async () => { fireEvent.keyDown(screen.getByRole("textbox"), { key: "Enter" }); });
  expect(api.askTutorQuestion.mock.calls[1][0]).toMatchObject({ captureId: undefined, noteId: "note_capture", question: "And then?" });
});

it("keeps capture attribution and the question when a send fails", async () => {
  api.askTutorQuestion.mockRejectedValueOnce({ code: "provider_unavailable", message: "Unavailable" });
  render(<AskOverlay target={target} onClose={vi.fn()} onToast={vi.fn()} />);
  await act(async () => { fireEvent.keyDown(screen.getByRole("textbox"), { key: "Enter" }); });
  await waitFor(() => expect(screen.getByDisplayValue("Why?")).toBeTruthy());
  await act(async () => { fireEvent.keyDown(screen.getByRole("textbox"), { key: "Enter" }); });
  expect(api.askTutorQuestion.mock.calls[1][0].captureId).toBe("capture");
});
