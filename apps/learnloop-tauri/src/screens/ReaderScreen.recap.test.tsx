// RW6a in the Reader (spec §9.1; UX §3.1 "returning", W1, W12): the card at
// the head of the Guide on opening a source read before, recap_shown once,
// nothing focused; "continue" folds it to "last time ▸"; dismiss removes it;
// the rail footer's "Wrap up (under a minute)" after activity, opening the
// three lists in the rail, never a modal.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "./ReaderScreen";
import { setAlgoConfig } from "../app/algoConfig";
import { readerRenderViewFixture as view } from "../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../api/dto";
import { resetReaderActivityForTests } from "./reader/activity";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerLogActivity: vi.fn(), readerRecap: vi.fn(), readerRecapEvent: vi.fn(), readerWrapUp: vi.fn(),
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: [source.card] }, error: null }) }));
vi.mock("./reader/readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./reader/guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./reader/useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };

const RECAP = {
  recapVersion: "rw6a-recap-v1", extractionId: view.extractionId,
  session: { sessionId: "v1", extractionId: view.extractionId, visitIds: ["v1"], startedAt: "2026-10-09T20:00:00Z", endedAt: "2026-10-09T20:40:00Z", minutes: 40 },
  continueAt: { sectionId: "u1", label: "Symmetric matrices" },
  stillOpen: [{ rootExchangeId: "r1", questionEventId: "q1", questionMd: "why are eigenvectors orthogonal?", spanId: "span_symmetric_prose", anchorSpanIds: ["span_symmetric_prose"], openedAt: "2026-10-09T20:05:00Z" }],
  unfinished: [], worthASecondLook: [], sinceLastTime: { demonstrated: [], checksRetired: [] },
};

beforeEach(() => {
  vi.resetAllMocks();
  resetReaderActivityForTests();
  setAlgoConfig({ recap: { enabled: true, wrapUpEnabled: true } });
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerRecap.mockResolvedValue({ version: 1, recap: RECAP, dismissed: false });
  api.readerRecapEvent.mockResolvedValue({ version: 1, eventId: "ev", event: "recap_shown" });
  api.readerWrapUp.mockResolvedValue({ version: 1, wrapUpVersion: "rw6a-wrap-up-v1", available: false, extractionId: view.extractionId, session: null, resolved: [], stillOpen: [], worthReinforcing: [] });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); });

it("opens a source read before with the card at the head of the Guide, recording recap_shown", async () => {
  const outside = document.createElement("button");
  document.body.appendChild(outside);
  outside.focus();
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const card = await screen.findByRole("region", { name: "Last time here" });
  const guide = screen.getByRole("complementary", { name: "Reading guide" });
  expect(guide.contains(card)).toBe(true);
  expect(card.textContent).toContain("why are eigenvectors orthogonal?");
  await waitFor(() => expect(api.readerRecapEvent).toHaveBeenCalledWith(expect.objectContaining({ extractionId: view.extractionId, event: "recap_shown" })));
  expect(api.readerRecapEvent).toHaveBeenCalledTimes(1);
  expect(document.activeElement).toBe(outside);
  expect(screen.queryByRole("dialog")).toBeNull();
  outside.remove();
});

it("continue folds it to last time, which reopens it; dismiss removes it", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const card = await screen.findByRole("region", { name: "Last time here" });
  fireEvent.click(within(card).getByRole("button", { name: "continue" }));
  await waitFor(() => expect(screen.queryByRole("region", { name: "Last time here" })).toBeNull());
  fireEvent.click(screen.getByRole("button", { name: /last time ▸/ }));
  const again = await screen.findByRole("region", { name: "Last time here" });
  api.readerRecapEvent.mockResolvedValue({ version: 1, eventId: "ev2", event: "recap_dismissed" });
  fireEvent.click(within(again).getByRole("button", { name: "dismiss" }));
  await waitFor(() => expect(screen.queryByRole("region", { name: "Last time here" })).toBeNull());
  expect(screen.queryByRole("button", { name: /last time ▸/ })).toBeNull();
  expect(api.readerRecapEvent).toHaveBeenCalledWith(expect.objectContaining({ event: "recap_dismissed" }));
});

it("the rail footer offers Wrap up after activity and opens the three lists in the rail", async () => {
  api.readerWrapUp.mockResolvedValue({
    version: 1, wrapUpVersion: "rw6a-wrap-up-v1", available: true, extractionId: view.extractionId,
    session: RECAP.session, resolved: [], worthReinforcing: [],
    stillOpen: [{ rootExchangeId: "r1", questionMd: "why are eigenvectors orthogonal?", spanIds: ["span_symmetric_prose"], actions: [{ action: "keep_open" }] }],
  });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  const offer = await screen.findByRole("button", { name: "Wrap up (under a minute)" });
  fireEvent.click(offer);
  const panel = await screen.findByRole("region", { name: "Wrap up" });
  expect(screen.getByRole("complementary", { name: "Reading guide" }).contains(panel)).toBe(true);
  expect(screen.queryByRole("dialog")).toBeNull();
  fireEvent.keyDown(window, { key: "Escape" });
  await waitFor(() => expect(screen.queryByRole("region", { name: "Wrap up" })).toBeNull());
});

it("no card, no last time and no Wrap up on a first visit", async () => {
  api.readerRecap.mockResolvedValue({ version: 1, recap: null, dismissed: false });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findAllByText(/symmetric/i);
  await waitFor(() => expect(api.readerRecap).toHaveBeenCalled());
  expect(screen.queryByRole("region", { name: "Last time here" })).toBeNull();
  expect(screen.queryByRole("button", { name: /last time ▸/ })).toBeNull();
  expect(screen.queryByRole("button", { name: "Wrap up (under a minute)" })).toBeNull();
  expect(api.readerRecapEvent).not.toHaveBeenCalled();
});
