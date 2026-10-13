// RW1a: continuing a Reader question from Today's queue keeps its thread. With
// reader_inquiry on (the history carries question ids) the overlay's Ask
// continues the span's newest exchange, then its own answers; switched off,
// the request is exactly today's (no parentExchangeId).
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { AskOverlay } from "./AskOverlay";

const { api } = vi.hoisted(() => ({ api: { getTutorTranscript: vi.fn(), readerAsk: vi.fn(), readerAskHistory: vi.fn() } }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: () => null }));
vi.mock("./OpenInSource", () => ({ OpenInSource: () => null }));

const answer = (id: string, parent: string | null | undefined) => ({
  version: 1, eventId: `q-${id}`, readerAnswerEventId: id, ...(parent === undefined ? {} : { parentExchangeId: parent }),
  answerMd: "An answer.", answerMode: "answer_directly", citations: [], manifest: {}, warmedSurfaceIds: [],
  burnedSurfaceIds: [], hintEquivalent: false, remaining: 4,
});

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.getTutorTranscript.mockResolvedValue({ events: [], remaining: 5 });
});
afterEach(() => cleanup());

async function send(text: string) {
  const input = screen.getByPlaceholderText("ask a question — enter sends");
  fireEvent.change(input, { target: { value: text } });
  fireEvent.keyDown(input, { key: "Enter" });
}

it("with branches on, continues the span's newest exchange, then its own answers", async () => {
  api.readerAskHistory.mockResolvedValue({ exchanges: [
    { eventId: "newest", spanId: "s12", questionEventId: "q-newest" },
    { eventId: "older", spanId: "s12", questionEventId: "q-older" },
    { eventId: "elsewhere", spanId: "s99", questionEventId: "q-elsewhere" },
  ] });
  api.readerAsk.mockResolvedValueOnce(answer("first", "newest")).mockResolvedValueOnce(answer("second", "first"));
  render(<AskOverlay target={{ context: "reader", extractionId: "ext_book", spanId: "s12" }} onClose={vi.fn()} onToast={vi.fn()} />);
  await waitFor(() => expect(api.getTutorTranscript).toHaveBeenCalledOnce());
  await send("Why?");
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(1));
  expect(api.readerAsk.mock.calls[0][0].parentExchangeId).toBe("newest");
  await send("And then?");
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(2));
  expect(api.readerAsk.mock.calls[1][0].parentExchangeId).toBe("first");
});

it("switched off (no question ids in the history), the request is today's", async () => {
  api.readerAskHistory.mockResolvedValue({ exchanges: [{ eventId: "newest", spanId: "s12" }] });
  api.readerAsk.mockResolvedValue(answer("first", undefined));
  render(<AskOverlay target={{ context: "reader", extractionId: "ext_book", spanId: "s12" }} onClose={vi.fn()} onToast={vi.fn()} />);
  await waitFor(() => expect(api.getTutorTranscript).toHaveBeenCalledOnce());
  await send("Why?");
  await waitFor(() => expect(api.readerAsk).toHaveBeenCalledTimes(1));
  expect("parentExchangeId" in api.readerAsk.mock.calls[0][0]).toBe(false);
});
