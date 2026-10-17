// RW6a Codex review fixes at the hook and component level
// (docs/reviews/reader-rw6a-codex-review.md): F7 wrap_up_opened is recorded
// only once the lists are shown (and a failed write leaves them shown), in the
// Reader and where the learner lands; F6 the opening reveals the Guide first;
// F9 skim withholds the rail's offer and folds the card; F8 an abandoned
// problem reads "set aside" with a reopen.
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderRecapCardDto, ReaderWrapUpDto } from "../../api/dto";
import { setAlgoConfig } from "../../app/algoConfig";
import { RecapCard } from "./RecapCard";
import { WrapUpOffer } from "./WrapUpOffer";
import { useReaderRecap } from "./useReaderRecap";

const api = vi.hoisted(() => ({
  readerRecap: vi.fn(), readerRecapEvent: vi.fn(), readerWrapUp: vi.fn(), readerWrapUpOffer: vi.fn(),
  readerSetInquiryStatus: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));

const SESSION = { sessionId: "v1", extractionId: "ext1", visitIds: ["v1"], startedAt: "2026-10-14T21:10:00Z", endedAt: "2026-10-14T21:50:00Z", minutes: 40 };
const WRAP: ReaderWrapUpDto = {
  version: 1, wrapUpVersion: "rw6a-wrap-up-v1", available: true, extractionId: "ext1", session: SESSION,
  resolved: [], stillOpen: [], worthReinforcing: [{ kind: "with_help", marker: "◌", sessionId: "wb1", title: "Exercise 5.14", status: "submitted", helpLine: "help so far: the book" }],
} as ReaderWrapUpDto;

function hookProps(overrides: Record<string, unknown> = {}) {
  return { enabled: false, wrapUpEnabled: true, extractionId: "ext1", visitId: () => "v1", readingMoved: false,
           activityKey: "0", onError: vi.fn(), ...overrides };
}

beforeEach(() => { vi.resetAllMocks(); setAlgoConfig(undefined); });
afterEach(() => { cleanup(); setAlgoConfig(undefined); });

it("F7: a failed wrap-up read shows nothing and records no opening", async () => {
  api.readerWrapUp.mockResolvedValueOnce(WRAP).mockRejectedValueOnce(new Error("sidecar busy"));
  api.readerRecapEvent.mockResolvedValue({ version: 1, eventId: "ev", event: "wrap_up_opened" });
  const onError = vi.fn();
  const { result } = renderHook((props) => useReaderRecap(props), { initialProps: hookProps({ onError }) });
  await waitFor(() => expect(result.current.wrapUpAvailable).toBe(true));
  await act(async () => { await result.current.openWrapUp(); });
  expect(result.current.wrapUpOpen).toBeNull();
  expect(onError).toHaveBeenCalled();
  expect(api.readerRecapEvent).not.toHaveBeenCalled();
});

it("F7: a failed event write leaves the loaded lists shown", async () => {
  api.readerWrapUp.mockResolvedValue(WRAP);
  api.readerRecapEvent.mockRejectedValue(new Error("write failed"));
  const onError = vi.fn();
  const { result } = renderHook((props) => useReaderRecap(props), { initialProps: hookProps({ onError }) });
  await waitFor(() => expect(result.current.wrapUpAvailable).toBe(true));
  await act(async () => { await result.current.openWrapUp(); });
  expect(result.current.wrapUpOpen).not.toBeNull();
  await waitFor(() => expect(api.readerRecapEvent).toHaveBeenCalledWith({ extractionId: "ext1", visitId: "v1", event: "wrap_up_opened" }));
});

it("F7: where the learner lands, a failed read records no opening and the line stays", async () => {
  setAlgoConfig({ recap: { enabled: true, wrapUpEnabled: true } });
  api.readerWrapUpOffer.mockResolvedValue({ version: 1, offer: { extractionId: "ext1", sourceId: "src1", session: SESSION } });
  api.readerWrapUp.mockRejectedValueOnce(new Error("sidecar busy")).mockResolvedValueOnce(WRAP);
  api.readerRecapEvent.mockResolvedValue({ version: 1, eventId: "ev", event: "wrap_up_opened" });
  render(<WrapUpOffer armed onError={vi.fn()} />);
  const line = await screen.findByRole("button", { name: /Reading wrap-up ready/ });
  await act(async () => { fireEvent.click(line); });
  expect(screen.queryByRole("region", { name: "Wrap up" })).toBeNull();
  expect(api.readerRecapEvent).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: /Reading wrap-up ready/ }));
  await screen.findByRole("region", { name: "Wrap up" });
  await waitFor(() => expect(api.readerRecapEvent).toHaveBeenCalledWith({ extractionId: "ext1", event: "wrap_up_opened" }));
});

it("F6: the opening reveals the Guide before anything is recorded", async () => {
  api.readerWrapUp.mockResolvedValue(WRAP);
  api.readerRecapEvent.mockResolvedValue({ version: 1, eventId: "ev", event: "wrap_up_opened" });
  const order: string[] = [];
  const reveal = vi.fn(() => { order.push("reveal"); });
  api.readerRecapEvent.mockImplementation(async () => { order.push("recorded"); return { version: 1, eventId: "ev", event: "wrap_up_opened" }; });
  const { result } = renderHook((props) => useReaderRecap(props), { initialProps: hookProps({ reveal }) });
  await waitFor(() => expect(result.current.wrapUpAvailable).toBe(true));
  await act(async () => { fireEvent.keyDown(window, { key: "w" }); });
  await waitFor(() => expect(order).toEqual(["reveal", "recorded"]));
  expect(result.current.wrapUpOpen).not.toBeNull();
});

it("F9: muted by skim, the rail's offer is withheld and the card folds", async () => {
  api.readerWrapUp.mockResolvedValue(WRAP);
  const { result, rerender } = renderHook((props) => useReaderRecap(props), { initialProps: hookProps() });
  await waitFor(() => expect(result.current.wrapUpOffered).toBe(true));
  rerender(hookProps({ muted: true }));
  expect(result.current.wrapUpOffered).toBe(false);
  expect(result.current.wrapUpAvailable).toBe(true);
  expect(result.current.collapsed).toBe(true);
});

it("F8: an abandoned problem reads set aside, with a reopen through resume", () => {
  const onResume = vi.fn();
  const recap = {
    recapVersion: "rw6a-recap-v1", extractionId: "ext1", session: SESSION, continueAt: null, stillOpen: [],
    unfinished: [{ sessionId: "wb_gone", status: "abandoned", title: "Exercise 5.14", stepCount: 3,
      help: { bookCounted: true, hints: 0 }, helpLine: "help so far: the book", unfinished: false, spanIds: ["s1"], updatedAt: "2026-10-14T21:40:00Z" }],
    worthASecondLook: [], sinceLastTime: { demonstrated: [], checksRetired: [] },
  } as unknown as ReaderRecapCardDto;
  render(<RecapCard recap={recap} collapsed={false} onExpand={vi.fn()} onContinue={vi.fn()} onDismiss={vi.fn()}
    onOpenInquiry={vi.fn()} onSetStatus={vi.fn()} onResume={onResume} />);
  const card = screen.getByRole("region", { name: "Last time here" });
  expect(card.textContent).toContain("Exercise 5.14 · 3 steps · help so far: the book · set aside");
  fireEvent.click(screen.getByRole("button", { name: "Reopen this problem ▸" }));
  expect(onResume).toHaveBeenCalledWith("wb_gone");
});
