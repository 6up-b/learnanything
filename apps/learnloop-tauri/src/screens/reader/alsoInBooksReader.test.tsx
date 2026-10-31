// Reader CA5 in the Reader (ux_reader_compare_ask_v1 §6.2, §6.3, §6.5, §13):
// with `correspondence.alsoInBooks` in the prompt contract the Guide shows the
// one dim line under the section's progress when the section has judged
// coverage (one quiet read per crossing, shared with CA5a's action, which then
// hides), `x` opens it, a peek puts its crumb in the detour strip, go there is
// the source detour, hiding it is kept, and skim mode shows it. Without the
// key the Guide is exactly as before.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import type { CorrespondentsDto, SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";
import { FIND_COPY } from "./FindSection";
import { ALSO_COPY } from "./AlsoInBooks";

const SPAN_IDS = view.blocks.map((block) => block.spanId!).filter(Boolean);

const { api, plan, state } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerSetMode: vi.fn(), readerCorrespondents: vi.fn(), readerCorrespondentPeek: vi.fn(), readerCorrespondentDismiss: vi.fn(),
    readerSetCorrespondencePreferences: vi.fn(),
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

const ON = {
  readerEnabled: true, inquiryEnabled: true,
  libraryAsk: { expandGraph: false, personalizedDefault: false, compare: true },
  correspondence: { enabled: true, findSection: true, alsoInBooks: true, hiddenEverywhere: false, hiddenSources: [] as string[] },
};
const OFF = { readerEnabled: true, inquiryEnabled: true, libraryAsk: ON.libraryAsk };
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
const JUDGED_LINE = { ...HIT, treatment: "introduces", treatmentWords: "introduces it", by: "judge" as const, label: undefined,
  notation: null, kept: [], alsoLearningObjectIds: [] };
const JUDGED: CorrespondentsDto = {
  ...QUIET, status: "judged",
  learningObjects: [{ learningObjectId: "lo_sym", title: "symmetric matrices", sources: [{ sourceId: "src_axler", sourceTitle: "Axler", sections: [JUDGED_LINE] }] }],
};
const PRESSED: CorrespondentsDto = {
  ...QUIET, status: "unchecked",
  search: { label: "found by search, not checked", correctableLearningObjectIds: ["lo_sym"], sources: [{ sourceId: "src_axler", sourceTitle: "Axler", sections: [HIT] }] },
};

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
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
  api.readerCorrespondents.mockImplementation(async (input: { searchFallback?: boolean }) => (input.searchFallback ? PRESSED : JUDGED));
  api.readerCorrespondentPeek.mockResolvedValue({ peek: {
    extractionId: "ext_axler", sectionId: "ax5a", sourceId: "src_axler", sourceTitle: "Axler", title: "5.A Invariant subspaces",
    jumpSpanId: "a7", page: 3, blocks: [{ spanId: "a7", blockType: "Text", page: 3, text: "Invariant subspaces are…" }], exposureEventIds: ["e1"],
  } });
  api.readerSetCorrespondencePreferences.mockImplementation(async (input: { sourceId?: string; hideSource?: boolean; hideEverywhere?: boolean }) => ({
    enabled: true, hideEverywhere: Boolean(input.hideEverywhere),
    hiddenSources: input.hideSource && input.sourceId ? [{ sourceId: input.sourceId, title: "Strang" }] : [],
  }));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); });

function line() {
  return document.querySelector<HTMLButtonElement>("[data-also-collapsed]");
}

it("the line sits under the section's progress, from one shared quiet read; CA5a's action hides", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await waitFor(() => expect(line()).toBeTruthy());
  expect(line()!.textContent).toBe("also in Axler §5.A ▸");
  // Directly under the section's progress bar, in the section's card.
  const bar = screen.getByRole("progressbar", { name: "Read of this section" });
  expect(bar.parentElement!.contains(line())).toBe(true);
  expect(bar.compareDocumentPosition(line()!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  const quiet = api.readerCorrespondents.mock.calls.filter((call) => call[0].sectionId === "u1" && call[0].searchFallback === false);
  expect(quiet).toHaveLength(1);
  expect(api.readerCorrespondents).not.toHaveBeenCalledWith(expect.objectContaining({ searchFallback: true }));
  expect(screen.queryByRole("button", { name: FIND_COPY.action })).toBeNull();
  expect(screen.getByText("also in your books")).toBeTruthy();
});

it("x opens the list at its first line; the key bar offers it while the line is there", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await waitFor(() => expect(line()).toBeTruthy());
  fireEvent.keyDown(document.body, { key: "x" });
  await waitFor(() => expect(document.querySelector("[data-also-expanded]")).toBeTruthy());
  await waitFor(() => expect(document.activeElement?.hasAttribute("data-also-title")).toBe(true));
  expect(screen.getByText("introduces it")).toBeTruthy();
});

it("x typed in a text field is the field's", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await waitFor(() => expect(line()).toBeTruthy());
  const field = document.createElement("input");
  document.body.appendChild(field);
  field.focus();
  fireEvent.keyDown(field, { key: "x" });
  await act(async () => { await Promise.resolve(); });
  expect(document.querySelector("[data-also-expanded]")).toBeNull();
  field.remove();
});

it("a peek puts its crumb in the detour strip, and the crumb closes it", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await waitFor(() => expect(line()).toBeTruthy());
  fireEvent.click(line()!);
  fireEvent.click(await screen.findByTitle("Axler · 5.A Invariant subspaces"));
  await screen.findByText("Invariant subspaces are…");
  expect(api.readerCorrespondentPeek).toHaveBeenCalledWith({ extractionId: "ext_axler", sectionId: "ax5a" });
  const strip = screen.getByRole("navigation", { name: "Detour" });
  expect(strip.textContent).toContain("peek Axler §5.A");
  fireEvent.click(screen.getByRole("button", { name: "close peek" }));
  await waitFor(() => expect(screen.queryByText("Invariant subspaces are…")).toBeNull());
  expect(screen.queryByRole("navigation", { name: "Detour" })).toBeNull();
});

it("go there opens the other book as a detour", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await waitFor(() => expect(line()).toBeTruthy());
  fireEvent.click(line()!);
  const before = api.readerRenderView.mock.calls.length;
  fireEvent.click(await screen.findByRole("button", { name: "go there: Axler 5.A Invariant subspaces" }));
  await waitFor(() => expect(api.readerRenderView.mock.calls.length).toBeGreaterThan(before));
  expect(api.readerRenderView.mock.calls.slice(before).map((call) => call[0])).toContainEqual(expect.objectContaining({ extractionId: "src_axler" }));
});

it("hide for this book is kept through the sidecar and leaves nothing behind", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await waitFor(() => expect(line()).toBeTruthy());
  fireEvent.click(screen.getByRole("button", { name: `${ALSO_COPY.title}: more` }));
  fireEvent.click(screen.getByRole("menuitem", { name: ALSO_COPY.hideBook }));
  await waitFor(() => expect(line()).toBeNull());
  expect(api.readerSetCorrespondencePreferences).toHaveBeenCalledWith({ sourceId: view.sourceId, hideSource: true });
  expect(document.querySelector("[data-also-in-books]")).toBeNull();
  // x does nothing once it is hidden.
  fireEvent.keyDown(document.body, { key: "x" });
  expect(document.querySelector("[data-also-expanded]")).toBeNull();
});

it("hidden for this book or everywhere in the contract, nothing shows", async () => {
  for (const correspondence of [{ ...ON.correspondence, hiddenSources: [view.sourceId] }, { ...ON.correspondence, hiddenEverywhere: true }]) {
    state.contract = { ...ON, correspondence };
    render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
    await screen.findAllByText("6.1 Symmetric matrices");
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 30)); });
    expect(line()).toBeNull();
    cleanup();
  }
});

it("skim mode still shows it (a table of contents)", async () => {
  api.readerSetMode.mockResolvedValue({ mode: "skim" });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await waitFor(() => expect(line()).toBeTruthy());
  const [modeSelect] = screen.getAllByRole("combobox");
  fireEvent.keyDown(modeSelect, { key: "Enter" });
  fireEvent.mouseDown(await screen.findByRole("option", { name: "skim quickly" }));
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 30)); });
  expect(line()).toBeTruthy();
});

it("switched off (no alsoInBooks in the contract), the Guide is as before CA5", async () => {
  state.contract = { ...ON, correspondence: { enabled: true, findSection: true } };
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findAllByText("6.1 Symmetric matrices");
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 50)); });
  expect(line()).toBeNull();
  expect(screen.queryByText("also in your books")).toBeNull();
});

it("switched off entirely (no correspondence key), nothing is read", async () => {
  state.contract = OFF;
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findAllByText("6.1 Symmetric matrices");
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 50)); });
  expect(line()).toBeNull();
  expect(api.readerCorrespondents).not.toHaveBeenCalled();
});

// -- Codex review (fix round) ----------------------------------------------------------------------

it("F4: a peek from CA5a's pressed list puts the same crumb in the detour strip, and the crumb closes it", async () => {
  api.readerCorrespondents.mockImplementation(async (input: { searchFallback?: boolean }) => (input.searchFallback ? PRESSED : QUIET));
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: FIND_COPY.action }));
  fireEvent.click(await screen.findByRole("button", { name: "peek at Axler 5.A Invariant subspaces" }));
  await screen.findByText("Invariant subspaces are…");
  const strip = screen.getByRole("navigation", { name: "Detour" });
  expect(strip.textContent).toContain("peek Axler §5.A");
  fireEvent.click(screen.getByRole("button", { name: "close peek" }));
  await waitFor(() => expect(screen.queryByText("Invariant subspaces are…")).toBeNull());
  expect(screen.queryByRole("navigation", { name: "Detour" })).toBeNull();
});

function keyBarOffersX() {
  return Array.from(document.querySelectorAll("span")).some((node) => node.textContent === "x" && node.nextElementSibling?.textContent === "also in your books");
}

it("F5: x is neither offered nor acts while the comparing posture hides the Guide", async () => {
  const ask = {
    askId: "la_1", query: "6.1 Symmetric matrices", entry: "where_else_explained", status: "ok", policy: "reading",
    personalized: false, basis: "keyword", learningObjectIds: [], extractionId: view.extractionId, anchorSpanIds: [], hits: [],
    groups: { sources: [], expansions: [] }, expansions: [], expandGraph: false, sourceCount: 0, passageCount: 0,
  };
  api.readerLibraryAsk.mockResolvedValue({ jobId: "j_ask", kind: "ask", askId: "la_1", state: "done", result: ask });
  api.readerLibraryCompare.mockResolvedValue({ jobId: "j_cmp", kind: "compare", askId: "la_1", state: "done",
    result: { askId: "la_1", status: "ok", rows: [], exposureEventIds: [] } });
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await waitFor(() => expect(line()).toBeTruthy());
  expect(keyBarOffersX()).toBe(true);
  fireEvent.click(line()!);
  const title = await screen.findByTitle("Axler · 5.A Invariant subspaces");
  act(() => { title.focus(); });
  fireEvent.keyDown(title, { key: "c" });
  await waitFor(() => expect(document.querySelector("[data-comparing-pane]")).toBeTruthy());
  // Folded behind the comparison, x neither shows in the key bar nor opens the hidden list.
  fireEvent.click(screen.getByRole("button", { name: `${ALSO_COPY.title}: fold`, hidden: true }));
  await waitFor(() => expect(document.querySelector("[data-also-expanded]")).toBeNull());
  expect(keyBarOffersX()).toBe(false);
  fireEvent.keyDown(document.body, { key: "x" });
  await act(async () => { await Promise.resolve(); });
  expect(document.querySelector("[data-also-expanded]")).toBeNull();
});
