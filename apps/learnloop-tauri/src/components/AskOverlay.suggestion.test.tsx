import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { AskOverlay } from "./AskOverlay";
import { suggestionLine } from "./askSuggestions";

const { api } = vi.hoisted(() => ({ api: { getTutorTranscript: vi.fn(), readerAsk: vi.fn() } }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: () => null }));
vi.mock("./OpenInSource", () => ({ OpenInSource: () => null }));

const answer = {
  version: 1, eventId: "event-1", readerAnswerEventId: "rae-1", answerMd: "Look at the dot product.",
  answerMode: "answer_directly", citations: [], manifest: {}, warmedSurfaceIds: [], burnedSurfaceIds: [],
  hintEquivalent: false, remaining: 4
};

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.getTutorTranscript.mockResolvedValue({ events: [], remaining: 5 });
});
afterEach(() => cleanup());

async function askReader() {
  render(<AskOverlay target={{ context: "reader", extractionId: "ext_book", spanId: "s12" }}
    onClose={vi.fn()} onToast={vi.fn()} />);
  await waitFor(() => expect(api.getTutorTranscript).toHaveBeenCalledOnce());
  const input = screen.getByPlaceholderText("ask a question — enter sends");
  fireEvent.change(input, { target: { value: "What makes two vectors orthogonal?" } });
  fireEvent.keyDown(input, { key: "Enter" });
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledOnce());
}

it("shows a reader answer's nearest-LO suggestion, labelled as one", async () => {
  api.readerAsk.mockResolvedValue({
    ...answer,
    suggestedLearningObjects: [
      { learningObjectId: "lo_inner", title: "Inner products", label: "suggestion", basis: ["keyword"] }
    ]
  });
  await askReader();
  expect(
    await screen.findByText("Nearest learning object (a suggestion, not a source link): Inner products")
  ).toBeTruthy();
});

it("shows nothing when the span has provenance (no suggestion field)", async () => {
  api.readerAsk.mockResolvedValue(answer);
  await askReader();
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledOnce());
  expect(screen.queryByText(/a suggestion, not a source link/)).toBeNull();
});

it("joins several suggestions and ignores an empty list", () => {
  expect(suggestionLine(undefined)).toBeNull();
  expect(suggestionLine([])).toBeNull();
  expect(
    suggestionLine([
      { learningObjectId: "a", title: "A", label: "suggestion", basis: [] },
      { learningObjectId: "b", title: "B", label: "suggestion", basis: [] }
    ])
  ).toBe("Nearest learning objects (a suggestion, not a source link): A · B");
});
