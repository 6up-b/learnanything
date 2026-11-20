// A control the Reader brings into view in its rail lands clear of the rail's
// sticky tab bar, so the first click or keystroke reaches it (student-3 #73,
// expert-2 #34: "ask follow-up", then typing into the follow-up box, landed on
// the bar). jsdom lays nothing out: the rail, its bar and the follow-up box are
// placed here by hand, with the rail's own styles (its 18 px padding, the bar's
// `position: sticky; top: -18px`) read from the real Reader.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
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

const RAIL_TOP = 200;
const RAIL_HEIGHT = 600;
const BAR_HEIGHT = 52;
const COMPOSER = "ask about this passage…";
const scrollTops = new WeakMap<Element, number>();
const scrolledAt = new WeakMap<Element, number>();

const isRail = (element: Element) => element.classList.contains("ll-scroll") && element.querySelector("button[aria-pressed]") !== null;
const isBar = (element: Element) => element instanceof HTMLElement && element.style.position === "sticky" && element.parentElement !== null && isRail(element.parentElement);
const isComposer = (element: Element) => element.getAttribute("placeholder") === COMPOSER;

/** Where each element sits in the window, given how far the rail has moved since the follow-up box was placed. */
function rect(element: Element): DOMRect {
  let top = 1400;
  let height = 20;
  if (isRail(element)) [top, height] = [RAIL_TOP, RAIL_HEIGHT];
  else if (isBar(element)) [top, height] = [RAIL_TOP, BAR_HEIGHT];
  else if (isComposer(element)) {
    // Above the rail's view: the box sits over the thread the learner scrolled down to.
    const rail = element.closest(".ll-scroll");
    const moved = rail ? (scrollTops.get(rail) ?? 0) - (scrolledAt.get(rail) ?? 0) : 0;
    [top, height] = [120 - moved, 60];
  }
  return { top, bottom: top + height, height, width: 300, left: 0, right: 300, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
}

beforeEach(() => {
  vi.resetAllMocks();
  resetReaderActivityForTests();
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) { return rect(this); });
  for (const [name, value] of [["clientHeight", RAIL_HEIGHT], ["scrollHeight", 4000]] as const) {
    Object.defineProperty(HTMLElement.prototype, name, { configurable: true, get(this: HTMLElement) { return isRail(this) ? value : 0; } });
  }
  Object.defineProperty(HTMLElement.prototype, "scrollTop", {
    configurable: true,
    get(this: HTMLElement) { return scrollTops.get(this) ?? 0; },
    set(this: HTMLElement, value: number) { scrollTops.set(this, value); },
  });
  HTMLElement.prototype.scrollTo = function (this: HTMLElement, options?: ScrollToOptions | number) {
    if (typeof options === "object" && options.top !== undefined) this.scrollTop = options.top;
  } as typeof HTMLElement.prototype.scrollTo;
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [root] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  for (const name of ["clientHeight", "scrollHeight", "scrollTop"]) delete (HTMLElement.prototype as unknown as Record<string, unknown>)[name];
});

async function frames() {
  for (let i = 0; i < 3; i += 1) {
    await act(async () => { await new Promise((resolve) => window.requestAnimationFrame(() => resolve(null))); });
  }
}

it("ask follow-up brings the follow-up box below the rail's tab bar, where a click reaches it (student-3 #73, expert-2 #34)", async () => {
  render(<ReaderScreen initialSource={initialSource} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: "ask" }));
  fireEvent.click(await screen.findByRole("button", { name: /▸ Why weighted by p\?/ }));
  await frames();
  const rail = screen.getByRole("button", { name: "guide" }).closest(".ll-scroll") as HTMLElement;
  expect(rail).toBeTruthy();
  // The learner has scrolled the rail down to the thread.
  rail.scrollTop = 900;
  scrolledAt.set(rail, 900);
  fireEvent.click(screen.getByRole("button", { name: "ask follow-up" }));
  await frames();
  const composer = screen.getByPlaceholderText(COMPOSER);
  expect(document.activeElement).toBe(composer);
  const bar = Array.from(rail.children).find(isBar) as HTMLElement;
  // The bar sticks 18 px above the rail's 18 px padding: it covers the rail's first BAR_HEIGHT px.
  expect([bar.style.top, getComputedStyle(rail).paddingTop]).toEqual(["-18px", "18px"]);
  const barBottom = RAIL_TOP + BAR_HEIGHT;
  const box = composer.getBoundingClientRect();
  expect(box.top).toBeGreaterThanOrEqual(barBottom);
  expect(box.bottom).toBeLessThanOrEqual(RAIL_TOP + RAIL_HEIGHT);
});
