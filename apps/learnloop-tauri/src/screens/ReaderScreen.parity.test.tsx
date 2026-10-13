// RW1a on every source kind the Reader opens (G51): a video transcript and the
// learner's own text notes get the same inquiry model -- branches, the detour
// strip, Alt+← back and the inline reconnect line under the passage. Plus the
// return stack's restart rule (G57: a restart restores only the root) and the
// Reader-wide keys ([ ] tabs, \ rail).
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "./ReaderScreen";
import { readerRenderViewFixture } from "../fixtures/readerRenderView";
import type { ReaderRenderViewDto, SourceLibraryCard } from "../api/dto";
import { resetReaderActivityForTests } from "./reader/activity";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerLogActivity: vi.fn(), readerRestoreSource: vi.fn(), readerWatchPlan: vi.fn(),
}));
const source = vi.hoisted(() => ({ card: null as unknown }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: [source.card] }, error: null }) }));
vi.mock("./reader/readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./reader/guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./reader/useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const transcript: ReaderRenderViewDto = {
  ...readerRenderViewFixture,
  sourceId: "src_video",
  extractionId: "ext_video",
  blocks: [
    ["s1", "t=0.0-4.0", "A mixture picks a component, then samples from it."],
    ["s2", "t=4.0-9.0", "So the density is weighted by the chance of each component."],
    ["s3", "t=9.0-14.0", "Conditioning on the coin flip gives the CDF directly."],
  ].map(([spanId, locator, text]) => ({
    displayNodeId: `node-${spanId}`, spanId, blockType: "Caption", extractorBlockId: locator, markdown: text,
    sanitized: false, katexNodes: [], assets: [], health: { status: "ok", recommendedView: "derived", reasonFlags: [] },
  })),
};
const notes: ReaderRenderViewDto = {
  ...readerRenderViewFixture,
  sourceId: "src_notes",
  extractionId: "ext_notes",
  blocks: [
    { ...readerRenderViewFixture.blocks[0], spanId: "n0", displayNodeId: "node-n0", markdown: "## My mixture notes" },
    { ...readerRenderViewFixture.blocks[1], spanId: "n1", displayNodeId: "node-n1", markdown: "F_X(x) = p F_Y(x) + (1 - p) F_Z(x): condition on the component." },
  ],
};

function exchange(view: ReaderRenderViewDto, spanId: string) {
  return {
    eventId: "root", parentExchangeId: null, extractionId: view.extractionId, spanId, questionMd: "Why weighted?",
    answerMd: "Saved answer", answerMode: "answer_directly", citations: [], selectionSpanIds: [spanId],
    selectionQuoteMd: null, createdAt: null, questionEventId: "q_root", resolution: "open",
  };
}

function setSource(view: ReaderRenderViewDto, kind: "video" | "notes") {
  source.card = {
    sourceId: view.sourceId, title: kind === "video" ? "Mixtures, explained" : "My mixture notes",
    canonicalUri: kind === "video" ? "https://www.youtube.com/watch?v=hvjkcmzfix8" : "file:///notes/mixtures.md",
    acquisitionKind: kind === "video" ? "youtube" : "textfile", readiness: "ready", readerEnabled: true,
  } as SourceLibraryCard;
  api.readerRenderView.mockResolvedValue(view);
}

beforeEach(() => {
  vi.resetAllMocks();
  resetReaderActivityForTests();
  Element.prototype.scrollIntoView = vi.fn();
  Element.prototype.scrollTo = vi.fn() as unknown as typeof Element.prototype.scrollTo;
  // jsdom's storage is shadowed in this Node; give the Reader a real one.
  const store = new Map<string, string>();
  Object.defineProperty(window, "localStorage", {
    configurable: true,
    value: {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, String(v)),
      removeItem: (k: string) => void store.delete(k),
      clear: () => store.clear(),
    },
  });
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerRestoreSource.mockResolvedValue({ eventId: "restored" });
  api.readerWatchPlan.mockResolvedValue({ sourceId: "src_video", videoId: "hvjkcmzfix8", embedUrl: "about:blank", pausePoints: [] });
});
afterEach(cleanup);

function altLeft() {
  act(() => {
    fireEvent.keyDown(window, { key: "Alt", altKey: true });
    fireEvent.keyDown(window, { key: "ArrowLeft", altKey: true });
    fireEvent.keyUp(window, { key: "ArrowLeft", altKey: true });
    fireEvent.keyUp(window, { key: "Alt" });
  });
}

async function followUpAndReturn(view: ReaderRenderViewDto) {
  api.readerAsk.mockResolvedValue({
    eventId: "q_child", readerAnswerEventId: "child", parentExchangeId: "root", answerMd: "Follow-up answer",
    answerMode: "answer_directly", citations: [], manifest: { version: "p3-reader-branches-v1" },
  });
  fireEvent.click(await screen.findByRole("button", { name: "ask" }));
  fireEvent.click(await screen.findByRole("button", { name: /▸ Why weighted\?/ }));
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up" }));
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "And the bounds?" } });
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up · ctrl+↵" }));
  await screen.findByText("Follow-up answer");
  expect(await screen.findByRole("navigation", { name: "Detour" })).toBeTruthy();
  altLeft();
  altLeft();
  await waitFor(() => expect(api.readerRestoreSource).toHaveBeenCalledWith(expect.objectContaining({ extractionId: view.extractionId })));
}

it("a video transcript: the reconnect line sits under the transcript passage", async () => {
  setSource(transcript, "video");
  api.readerAskHistory.mockResolvedValue({ exchanges: [exchange(transcript, "s2")] });
  render(<ReaderScreen initialSource={{ card: source.card as SourceLibraryCard, spanId: null }} onError={vi.fn()} />);
  await screen.findByTitle("watch hvjkcmzfix8");
  await followUpAndReturn(transcript);
  const inline = await screen.findAllByRole("group", { name: "Does this make sense now?" });
  const inTranscript = inline.find((line) => line.getAttribute("data-reconnect") === "inline");
  expect(inTranscript).toBeTruthy();
  expect(inTranscript!.closest('[aria-label^="Transcript from"]')).toBeTruthy();
});

it("the learner's text notes: the same branches, strip and inline reconnect", async () => {
  setSource(notes, "notes");
  api.readerAskHistory.mockResolvedValue({ exchanges: [exchange(notes, "n1")] });
  render(<ReaderScreen initialSource={{ card: source.card as SourceLibraryCard, spanId: "n1" }} onError={vi.fn()} />);
  await screen.findAllByText(notes.blocks[1].markdown);
  await followUpAndReturn(notes);
  const lines = await screen.findAllByRole("group", { name: "Does this make sense now?" });
  expect(lines.map((line) => line.getAttribute("data-reconnect")).sort()).toEqual(["inline", "rail"]);
});

it("while a detour is open, the saved reading position stays at its root (a restart restores only the root)", async () => {
  setSource(readerRenderViewFixture, "notes");
  api.readerAskHistory.mockResolvedValue({ exchanges: [exchange(readerRenderViewFixture, "span_symmetric_prose")] });
  render(<ReaderScreen initialSource={{ card: source.card as SourceLibraryCard, spanId: "span_spectral_worked" }} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: "ask" }));
  fireEvent.click(await screen.findByRole("button", { name: /▸ Why weighted\?/ }));
  const key = `learnloop.reader.position.${readerRenderViewFixture.sourceId}`;
  const before = window.localStorage.getItem(key);
  fireEvent.click(screen.getByRole("button", { name: "show passage" }));
  const strip = await screen.findByRole("navigation", { name: "Detour" });
  expect(within(strip).getAllByRole("button")).toHaveLength(2);
  await waitFor(() => expect(window.localStorage.getItem(key)).toBe(before));
  expect(window.localStorage.getItem(key)).not.toBe("span_symmetric_prose");
});

it("[ and ] move between rail tabs, and \\ collapses and expands the rail", async () => {
  setSource(readerRenderViewFixture, "notes");
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  render(<ReaderScreen initialSource={{ card: source.card as SourceLibraryCard, spanId: null }} onError={vi.fn()} />);
  const guideTab = await screen.findByRole("button", { name: "guide" });
  expect(guideTab.getAttribute("aria-pressed")).toBe("true");
  fireEvent.keyDown(window, { key: "]" });
  expect(screen.getByRole("button", { name: "ask" }).getAttribute("aria-pressed")).toBe("true");
  fireEvent.keyDown(window, { key: "[" });
  expect(screen.getByRole("button", { name: "guide" }).getAttribute("aria-pressed")).toBe("true");
  fireEvent.keyDown(window, { key: "\\" });
  expect(screen.getByRole("button", { name: "expand the rail (\\)" })).toBeTruthy();
  fireEvent.keyDown(window, { key: "\\" });
  expect(screen.queryByRole("button", { name: "expand the rail (\\)" })).toBeNull();
});
