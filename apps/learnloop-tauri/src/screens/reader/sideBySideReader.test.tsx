// Reader CA6 in the Reader (ux_reader_compare_ask_v1 §6.4, X9, K14, §13): the
// entry points (`s` and *side by side* on a line of CA5a's list, *read side by
// side* in a peek's header, Ctrl+\ from reading), the crumb and its return,
// the rail folded to its gutter, F6 between the panes, Esc and Ctrl+\ closing
// the second pane, the narrow window's peek, CA3's selection verb naming the
// other pane's book, and the switch off (the Reader exactly as before).
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import type { CorrespondentsDto, SideBySideSectionDto, SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";
import { FIND_COPY } from "./FindSection";
import { SIDE_BY_SIDE_COPY } from "./useSideBySide";

const SPAN_IDS = view.blocks.map((block) => block.spanId!).filter(Boolean);

const { api, plan, state } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerSetMode: vi.fn(), readerCorrespondents: vi.fn(), readerCorrespondentPeek: vi.fn(), readerCorrespondentDismiss: vi.fn(),
    readerSideBySideSection: vi.fn(),
    getSpanView: vi.fn(), readerLibraryAsk: vi.fn(), readerLibraryAskNotes: vi.fn(), readerLibraryCompare: vi.fn(),
    readerLibraryJob: vi.fn(), readerLibraryJobCancel: vi.fn(), readerSaveProgress: vi.fn(),
  },
  plan: {
    sourceId: "src", extractionId: "ext", personalized: true, selectionBasis: "", goalContext: null,
    sections: [] as unknown[], pendingDiagnosisAttemptIds: [],
  },
  state: { contract: {} as Record<string, unknown> },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../api/useCachedQuery", () => ({
  useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? state.contract : { sources: [source.card, AXLER] }, error: null }),
}));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve(plan), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const LIBRARY = { expandGraph: false, personalizedDefault: false, compare: true };
const ON = {
  readerEnabled: true, inquiryEnabled: true, libraryAsk: LIBRARY,
  correspondence: { enabled: true, findSection: true }, sideBySide: { enabled: true },
};
const OFF = { readerEnabled: true, inquiryEnabled: true, libraryAsk: LIBRARY, correspondence: { enabled: true, findSection: true } };
const source = { card: { sourceId: view.sourceId, title: "Strang", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: SPAN_IDS[1] };
const AXLER = { sourceId: "src_axler", title: "Axler", canonicalUri: "axler.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;

const HIT = {
  extractionId: "ext_axler", sectionId: "ax5a", title: "5.A Invariant subspaces", sourceId: "src_axler", sourceTitle: "Axler",
  read: false, jump: { extractionId: "ext_axler", sectionId: "ax5a", spanId: "a7" }, treatment: null,
  label: "found by search, not checked", by: "search" as const,
};
const QUIET: CorrespondentsDto = {
  extractionId: view.extractionId, sectionId: "u1", status: "none", learningObjects: [], search: null, checkableLearningObjectIds: ["lo_sym"],
};
const PRESSED: CorrespondentsDto = {
  ...QUIET, status: "unchecked",
  search: { label: "found by search, not checked", correctableLearningObjectIds: ["lo_sym"], sources: [{ sourceId: "src_axler", sourceTitle: "Axler", sections: [HIT] }] },
};
const JUDGED: CorrespondentsDto = {
  ...QUIET, status: "judged",
  learningObjects: [{ learningObjectId: "lo_sym", title: "symmetric matrices", sources: [{ sourceId: "src_axler", sourceTitle: "Axler", sections: [{
    ...HIT, sectionId: "ax7a", title: "7.A Self-adjoint operators", jump: { extractionId: "ext_axler", sectionId: "ax7a", spanId: "a40" }, treatment: "develops", label: undefined, by: "judge" as const,
  }] }] }],
};
function section(sectionId: string, title: string): SideBySideSectionDto {
  return {
    extractionId: "ext_axler", sectionId, sourceId: "src_axler", sourceTitle: "Axler", title, jumpSpanId: `${sectionId}_1`, page: 120,
    blocks: [{ spanId: `${sectionId}_1`, blockType: "Text", page: 120, text: `Axler says ${title}.` }],
    previous: null, next: { sectionId: "ax5b", title: "5.B Eigenvectors" }, exposureEventIds: ["x1"],
  };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 1400 });
  plan.extractionId = view.extractionId;
  plan.sourceId = view.sourceId;
  plan.sections = [{ id: "u1", label: "6.1 Symmetric matrices", startSpanId: SPAN_IDS[0], endSpanId: SPAN_IDS[SPAN_IDS.length - 1],
    spanIds: SPAN_IDS, question: null, suggestedPassages: [] }];
  state.contract = ON;
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerSetMode.mockResolvedValue({ mode: "read" });
  api.readerSaveProgress.mockResolvedValue({});
  api.readerCorrespondents.mockImplementation(async (input: { searchFallback?: boolean }) => (input.searchFallback ? PRESSED : QUIET));
  api.readerCorrespondentPeek.mockResolvedValue({ peek: { ...section("ax5a", "5.A Invariant subspaces"), blocks: [{ spanId: "a7", blockType: "Text", page: 120, text: "peek text" }] } });
  api.readerSideBySideSection.mockImplementation(async (input: { sectionId: string }) => ({
    section: section(input.sectionId, input.sectionId === "ax7a" ? "7.A Self-adjoint operators" : "5.A Invariant subspaces"),
  }));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); });

async function openList() {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: FIND_COPY.action }));
  return screen.findByRole("button", { name: "side by side with Axler 5.A Invariant subspaces" });
}
const pane = () => document.querySelector<HTMLElement>("[data-side-by-side-pane]");
const rail = () => screen.getByRole("complementary", { hidden: true });

it("`side by side` on a line opens the second pane, pushes the crumb and folds the rail to its gutter", async () => {
  fireEvent.click(await openList());
  await waitFor(() => expect(pane()?.dataset.sideBySidePane).toBe("pane"));
  expect(api.readerSideBySideSection).toHaveBeenCalledWith({ extractionId: "ext_axler", sectionId: "ax5a" });
  expect(await within(pane()!).findByText("Axler says 5.A Invariant subspaces.")).toBeTruthy();
  // The crumb: ↩ (where I was) › side by side with Axler §5.A.
  const strip = screen.getByRole("navigation", { name: "Detour" });
  expect(within(strip).getByRole("button", { name: "side by side with Axler §5.A" })).toBeTruthy();
  // An unchecked hit says so in its pane; the rail is folded to its gutter.
  expect(within(pane()!).getByText(SIDE_BY_SIDE_COPY.unchecked)).toBeTruthy();
  expect(rail().style.display).toBe("none");
  expect(screen.getByRole("button", { name: "expand the rail (\\)" })).toBeTruthy();
  // Follow along is on, and the main pane leads (the learner was reading it).
  expect(within(pane()!).getByRole("button", { name: /follow along ●/ }).getAttribute("aria-pressed")).toBe("true");
  expect(document.querySelector("[data-sbs-main-header] [data-sbs-lead]")).toBeTruthy();
});

it("`s` on a focused line opens side by side; `\\` reopens the rail as an overlay", async () => {
  await openList();
  const title = await screen.findByRole("button", { name: "§ 5.A Invariant subspaces" });
  title.focus();
  fireEvent.keyDown(title, { key: "s" });
  await waitFor(() => expect(pane()).toBeTruthy());
  fireEvent.keyDown(document.body, { key: "\\" });
  await waitFor(() => expect(rail().style.display).not.toBe("none"));
  expect(rail().style.position).toBe("absolute");
});

it("read side by side in a peek's header opens it too", async () => {
  await openList();
  fireEvent.click(screen.getByRole("button", { name: "peek at Axler 5.A Invariant subspaces" }));
  fireEvent.click(await screen.findByRole("button", { name: FIND_COPY.readSideBySide }));
  await waitFor(() => expect(pane()?.dataset.sideBySidePane).toBe("pane"));
});

it("the crumb returns: walking back to the origin closes the second pane", async () => {
  fireEvent.click(await openList());
  await waitFor(() => expect(pane()).toBeTruthy());
  const strip = screen.getByRole("navigation", { name: "Detour" });
  fireEvent.click(within(strip).getAllByRole("button")[0]);
  await waitFor(() => expect(pane()).toBeNull());
  expect(rail().style.display).not.toBe("none");
});

it("Ctrl+\\ opens the first correspondent in the API's order; Ctrl+\\ again closes it and the crumb goes", async () => {
  api.readerCorrespondents.mockImplementation(async (input: { searchFallback?: boolean }) => (input.searchFallback ? JUDGED : QUIET));
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findAllByText("6.1 Symmetric matrices");
  await act(async () => { fireEvent.keyDown(document.body, { key: "\\", ctrlKey: true }); });
  await waitFor(() => expect(api.readerSideBySideSection).toHaveBeenCalledWith({ extractionId: "ext_axler", sectionId: "ax7a" }));
  expect(api.readerCorrespondents).toHaveBeenCalledWith({ extractionId: view.extractionId, sectionId: "u1", searchFallback: true });
  await waitFor(() => expect(within(pane()!).getByText("Axler says 7.A Self-adjoint operators.")).toBeTruthy());
  // Judged: no "not checked" line.
  expect(within(pane()!).queryByText(SIDE_BY_SIDE_COPY.unchecked)).toBeNull();
  expect(screen.getByRole("button", { name: "side by side with Axler §7.A" })).toBeTruthy();
  fireEvent.keyDown(document.body, { key: "\\", ctrlKey: true });
  await waitFor(() => expect(pane()).toBeNull());
  expect(screen.queryByRole("navigation", { name: "Detour" })).toBeNull();
});

it("Esc in the second pane closes it; ✕ does too", async () => {
  fireEvent.click(await openList());
  await waitFor(() => expect(pane()).toBeTruthy());
  fireEvent.keyDown(pane()!.querySelector("[data-sbs-body]")!, { key: "Escape" });
  await waitFor(() => expect(pane()).toBeNull());
  fireEvent.click(await screen.findByRole("button", { name: "side by side with Axler 5.A Invariant subspaces" }));
  await waitFor(() => expect(pane()).toBeTruthy());
  fireEvent.click(within(pane()!).getByRole("button", { name: SIDE_BY_SIDE_COPY.close }));
  await waitFor(() => expect(pane()).toBeNull());
});

it("F6 moves focus between the panes", async () => {
  fireEvent.click(await openList());
  await waitFor(() => expect(pane()).toBeTruthy());
  const main = document.querySelector<HTMLElement>("[data-sbs-main]")!;
  main.focus();
  fireEvent.keyDown(main, { key: "F6" });
  expect(document.activeElement).toBe(pane()!.querySelector("[data-sbs-body]"));
  fireEvent.keyDown(document.activeElement!, { key: "F6" });
  expect(document.activeElement).toBe(main);
});

it("Ctrl+Shift+L turns follow along off and on; scrolling the second pane makes it lead", async () => {
  fireEvent.click(await openList());
  await waitFor(() => expect(pane()).toBeTruthy());
  fireEvent.keyDown(document.body, { key: "L", ctrlKey: true, shiftKey: true });
  expect(within(pane()!).getByRole("button", { name: /follow along ○/ }).getAttribute("aria-pressed")).toBe("false");
  fireEvent.keyDown(document.body, { key: "L", ctrlKey: true, shiftKey: true });
  expect(within(pane()!).getByRole("button", { name: /follow along ●/ })).toBeTruthy();
  fireEvent.wheel(pane()!.querySelector("[data-sbs-body]")!);
  await waitFor(() => expect(pane()!.querySelector("[data-sbs-lead]")).toBeTruthy());
  expect(document.querySelector("[data-sbs-main-header] [data-sbs-lead]")).toBeNull();
});

it("in a narrow window `side by side` peeks instead, with one dim line and no crumb", async () => {
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 900 });
  fireEvent.click(await openList());
  await waitFor(() => expect(pane()?.dataset.sideBySidePane).toBe("sheet"));
  expect(within(pane()!).getByText(SIDE_BY_SIDE_COPY.narrow)).toBeTruthy();
  expect(SIDE_BY_SIDE_COPY.narrow).toBe("side by side needs a wider window");
  expect(screen.queryByRole("navigation", { name: "Detour" })).toBeNull();
  // The rail stays as it was; no follow toggle in a peek.
  expect(rail().style.display).not.toBe("none");
  expect(within(pane()!).queryByRole("button", { name: /follow along/ })).toBeNull();
});

it("switched off: no side by side on the list, Ctrl+\\ reads nothing, the Reader as before", async () => {
  state.contract = OFF;
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: FIND_COPY.action }));
  await screen.findByRole("button", { name: "go there: Axler 5.A Invariant subspaces" });
  expect(screen.queryByRole("button", { name: "side by side with Axler 5.A Invariant subspaces" })).toBeNull();
  expect(screen.getByText(FIND_COPY.keys)).toBeTruthy();
  const title = screen.getByRole("button", { name: "§ 5.A Invariant subspaces" });
  title.focus();
  fireEvent.keyDown(title, { key: "s" });
  const reads = api.readerCorrespondents.mock.calls.length;
  await act(async () => { fireEvent.keyDown(document.body, { key: "\\", ctrlKey: true }); });
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 20)); });
  expect(api.readerCorrespondents.mock.calls.length).toBe(reads);
  expect(api.readerSideBySideSection).not.toHaveBeenCalled();
  expect(pane()).toBeNull();
});

it("CA3's selection verb in the second pane anchors there and names the main pane's book", async () => {
  state.contract = { ...ON, libraryAsk: { ...LIBRARY, compareScope: true } };
  api.readerLibraryCompare.mockResolvedValue({ jobId: "j_cmp", kind: "compare", askId: "la_c", state: "done",
    result: { askId: "la_c", status: "ok", comparisonId: null, rows: [], alsoDiscussedIn: [], unverifiedSources: [], droppedPins: [],
      droppedLineCount: 0, header: "", verification: { status: null, stopped: null, verifiedSources: null }, exposureEventIds: [], library: [] } });
  fireEvent.click(await openList());
  const text = await within(await waitFor(() => pane()!)).findByText("Axler says 5.A Invariant subspaces.");
  const range = document.createRange();
  range.selectNodeContents(text);
  const selection = window.getSelection()!;
  selection.removeAllRanges();
  selection.addRange(range);
  fireEvent.mouseUp(pane()!.querySelector("[data-sbs-body]")!);
  fireEvent.click(await within(pane()!).findByRole("button", { name: "how do my other books treat this?" }));
  await waitFor(() => expect(api.readerLibraryCompare).toHaveBeenCalled());
  expect(api.readerLibraryCompare.mock.calls[0][0]).toMatchObject({
    door: "selection", extractionId: "ext_axler", anchorSpanIds: ["ax5a_1"], sourceIds: [view.sourceId], openSourceId: "src_axler",
    question: "Axler says 5.A Invariant subspaces.",
  });
});
