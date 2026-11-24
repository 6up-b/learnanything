// A Reader scroll request moves the Reader's own panes, never the application
// around it: the top bar and the place tabs stay in the window.
//
// jsdom lays nothing out and has no `scrollIntoView`, so these tests model the
// one rule that matters: a browser's `scrollIntoView` (or `focus()`) may move
// EVERY scrolling box between the element and the window, a box with
// `overflow: hidden` included, and the window itself. Under that model a
// request that reaches the native call can move the shell; the Reader's own
// scrolls must reach only boxes the learner can scroll (overflow auto or
// scroll). Whether a given move happens, and by how much, needs the real
// window (WebKitGTK); that the shell is not among the boxes that can move is
// what is checked here.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ScopedSource } from "../desks/source/ScopedSource";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import type { SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerLogActivity: vi.fn(), readerRestoreSource: vi.fn(), readerSetInquiryStatus: vi.fn(),
  readerReconnectAnswer: vi.fn(), readerInquiryQuestion: vi.fn(), readerInquiryQuestionAction: vi.fn(),
  resolveQuestionEvent: vi.fn(), readerInvokePreset: vi.fn(), readerEscalateAuthoredQuestion: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: [initialSource.card] }, error: null }) }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const root = {
  eventId: "root", parentExchangeId: null, extractionId: view.extractionId, spanId: "span_symmetric_prose",
  questionMd: "Why weighted by p?", answerMd: "Saved answer", answerMode: "answer_directly", citations: [],
  selectionSpanIds: ["span_symmetric_prose"], selectionQuoteMd: "Saved exact selection", createdAt: null,
  questionEventId: "q_root", resolution: "open",
};
const initialSource = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };

// Every box a scroll request could move, with how it was asked.
const moved: { box: Element | Document; how: string }[] = [];
const userScrollable = (element: Element) => /^(auto|scroll|overlay)$/.test(window.getComputedStyle(element).overflowY);

function browserScrollIntoView(this: Element) {
  // The browser's rule: every ancestor whose overflow is not visible is a
  // scrolling box (hidden ones too), and the window is the last one.
  for (let node = this.parentElement; node; node = node.parentElement) {
    const style = window.getComputedStyle(node);
    if (style.overflowY !== "visible" || style.overflowX !== "visible") moved.push({ box: node, how: "scrollIntoView" });
  }
  moved.push({ box: document, how: "scrollIntoView" });
}

beforeEach(() => {
  vi.resetAllMocks();
  resetReaderActivityForTests();
  moved.length = 0;
  Element.prototype.scrollIntoView = browserScrollIntoView;
  HTMLElement.prototype.scrollTo = function (this: HTMLElement) { moved.push({ box: this, how: "scrollTo" }); } as typeof HTMLElement.prototype.scrollTo;
  const focus = HTMLElement.prototype.focus;
  vi.spyOn(HTMLElement.prototype, "focus").mockImplementation(function (this: HTMLElement, options?: FocusOptions) {
    if (!options?.preventScroll) browserScrollIntoView.call(this);
    focus.call(this, options);
  });
  // Each pane is a 300 px box at the top of the window; everything in it sits
  // below what it shows, so bringing it into view needs a scroll.
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
    const top = userScrollable(this) ? 0 : 900;
    return { top, bottom: top + 20, height: 20, width: 300, left: 0, right: 300, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
  });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [root] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerAsk.mockResolvedValue({
    eventId: "q_child", readerAnswerEventId: "child", parentExchangeId: "root", answerMd: "Follow-up answer",
    answerMode: "answer_directly", citations: [], manifest: { version: "p3-reader-branches-v1" }, model: "stub-model",
  });
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

async function frames() {
  for (let i = 0; i < 3; i += 1) {
    await act(async () => { await new Promise((resolve) => window.requestAnimationFrame(() => resolve(null))); });
  }
}

function renderInShell() {
  // The shell's frame: a full-window box with hidden overflow, as
  // `.terminal-frame` and `#root` are.
  return render(
    <div data-testid="shell" style={{ overflow: "hidden", height: "100%" }}>
      <ScopedSource initialSource={initialSource} onError={vi.fn()} />
    </div>,
  );
}

function outsideTheReadersPanes() {
  return moved.filter(({ box }) => !(box instanceof Element) || !userScrollable(box));
}

it("opening at the reading place scrolls the Reader's text, and nothing around it", async () => {
  renderInShell();
  await screen.findByText(view.blocks[2].markdown);
  await frames();
  expect(moved.length).toBeGreaterThan(0);
  expect(moved.map(({ box }) => box)).not.toContain(screen.getByTestId("shell"));
  expect(outsideTheReadersPanes()).toEqual([]);
});

it("a follow-up brings its question box into view inside the rail, never the shell (student-2 #83-88)", async () => {
  renderInShell();
  fireEvent.click(await screen.findByRole("button", { name: "ask" }));
  fireEvent.click(await screen.findByRole("button", { name: /▸ Why weighted by p\?/ }));
  await frames();
  moved.length = 0;
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up" }));
  await frames();
  expect(document.activeElement).toBe(screen.getByPlaceholderText("ask about this passage…"));
  expect(moved.length).toBeGreaterThan(0);
  expect(moved.map(({ box }) => box)).not.toContain(screen.getByTestId("shell"));
  expect(outsideTheReadersPanes()).toEqual([]);
});

it("the answer to a follow-up is brought into view inside the rail, never the shell", async () => {
  renderInShell();
  fireEvent.click(await screen.findByRole("button", { name: "ask" }));
  fireEvent.click(await screen.findByRole("button", { name: /▸ Why weighted by p\?/ }));
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up" }));
  await frames();
  moved.length = 0;
  fireEvent.change(screen.getByPlaceholderText("ask about this passage…"), { target: { value: "Why does conditioning work?" } });
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up · ctrl+↵" }));
  await screen.findByText("Follow-up answer");
  await frames();
  expect(moved.map(({ box }) => box)).not.toContain(screen.getByTestId("shell"));
  expect(outsideTheReadersPanes()).toEqual([]);
});

// Every module of the Reader and the panes it opens, as text: a native
// `scrollIntoView` there can move the application (see the top of this file).
const READER_MODULES = import.meta.glob(
  ["./**/*.{ts,tsx}", "!./**/*.test.{ts,tsx}", "../desks/source/ScopedSource.tsx", "../../components/PdfReaderPane.tsx"],
  { query: "?raw", import: "default", eager: true },
) as Record<string, string>;

it("no module of the Reader asks the browser to scroll an element into view itself", () => {
  expect(Object.keys(READER_MODULES)).toEqual(expect.arrayContaining(["../desks/source/ScopedSource.tsx", "../../components/PdfReaderPane.tsx", "./AskRail.tsx"]));
  const calls = Object.entries(READER_MODULES).flatMap(([file, text]) =>
    text.split("\n").flatMap((line, index) => (/\.scrollIntoView\??\.?\(/.test(line) ? [`${file}:${index + 1}`] : [])));
  expect(calls).toEqual([]);
});

