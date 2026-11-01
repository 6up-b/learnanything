// Reader CA6 x CA5 at the landing (docs/reviews/reader-ca6-side-by-side.md,
// "Landing onto main"): (i) `s` on a line of CA5's expanded "also in your
// books" list (and *side by side* in its peek) opens side by side with that
// section, through AlsoInBooks' onSideBySide seam; (ii) opening side by side
// from a peek replaces the peek's display-only crumb with side by side's crumb,
// Alt+←/→ walk the return stack (never a peek), and Esc closes only what is
// shown; (iii) each switch alone controls its own UI; (iv) one salience record
// per action (CA5's correspondenceEvents.ts and CA6's records never both fire).
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import type { CorrespondentsDto, SideBySideSectionDto, SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";
import { FIND_COPY } from "./FindSection";
import { SIDE_BY_SIDE_COPY } from "./useSideBySide";
import { ALSO_COPY } from "./AlsoInBooks";
import { flushReaderActivity } from "./activity";

const SPAN_IDS = view.blocks.map((block) => block.spanId!).filter(Boolean);

const { api, plan, state } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerSetMode: vi.fn(), readerCorrespondents: vi.fn(), readerCorrespondentPeek: vi.fn(), readerCorrespondentDismiss: vi.fn(),
    readerSideBySideSection: vi.fn(), readerCapture: vi.fn(), readerSetCorrespondencePreferences: vi.fn(),
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
  correspondence: { enabled: true, findSection: true, alsoInBooks: true, hiddenEverywhere: false, hiddenSources: [] as string[] },
  sideBySide: { enabled: true },
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
    previous: null, next: { sectionId: "ax5b", title: "5.B Eigenvectors" }, exposureEventIds: ["x1"], revisionId: "rev_axler",
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


const JUDGED_LINE = {
  ...HIT, sectionId: "ax7a", title: "7.A Self-adjoint operators", jump: { extractionId: "ext_axler", sectionId: "ax7a", spanId: "a40" },
  treatment: "develops", treatmentWords: "develops it", label: undefined, by: "judge" as const, notation: null, kept: [], alsoLearningObjectIds: [],
};
const ALSO: CorrespondentsDto = {
  ...QUIET, status: "judged",
  learningObjects: [{ learningObjectId: "lo_sym", title: "symmetric matrices", sources: [{ sourceId: "src_axler", sourceTitle: "Axler", sections: [JUDGED_LINE] }] }],
};
const pane = () => document.querySelector<HTMLElement>("[data-side-by-side-pane]");
const rail = () => screen.getByRole("complementary", { hidden: true });
const alsoLine = () => document.querySelector<HTMLButtonElement>("[data-also-collapsed]");
const peekCrumb = () => document.querySelector("[data-detour-peek]");
const strip = () => screen.queryByRole("navigation", { name: "Detour" });
function events(): Array<{ event?: string; payload: Record<string, unknown> }> {
  flushReaderActivity();
  return api.readerLogActivity.mock.calls.flatMap((call) => call[0].events)
    .filter((e: { kind: string }) => e.kind === "reader_action_invoked");
}
const named = (name: string) => events().filter((e) => e.event === name);

async function openAlso() {
  api.readerCorrespondents.mockResolvedValue(ALSO);
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await waitFor(() => expect(alsoLine()).toBeTruthy());
  fireEvent.keyDown(document.body, { key: "x" });
  await waitFor(() => expect(document.activeElement?.hasAttribute("data-also-title")).toBe(true));
  return document.activeElement as HTMLElement;
}

// -- (i) the AlsoInBooks seam -----------------------------------------------------------------------

it("(i) `s` on a line of the expanded also-in-your-books list opens side by side with that section", async () => {
  const title = await openAlso();
  expect(document.querySelector("[data-also-expanded]")!.textContent).toContain(ALSO_COPY.keys.side);
  fireEvent.keyDown(title, { key: "s" });
  await waitFor(() => expect(pane()?.dataset.sideBySidePane).toBe("pane"));
  expect(api.readerSideBySideSection).toHaveBeenCalledWith({ extractionId: "ext_axler", sectionId: "ax7a" });
  expect(await within(pane()!).findByText("Axler says 7.A Self-adjoint operators.")).toBeTruthy();
  // Judged: no "not checked" line; the crumb names the pair.
  expect(within(pane()!).queryByText(SIDE_BY_SIDE_COPY.unchecked)).toBeNull();
  expect(within(strip()!).getByRole("button", { name: "side by side with Axler §7.A" })).toBeTruthy();
  const opened = named("side_by_side_opened");
  expect(opened).toHaveLength(1);
  expect(opened[0].payload).toMatchObject({ via: "also_list", by: "judged", target_section_id: "ax7a" });
});

it("(i) with side by side off, `s` on the also list does nothing and the key bar does not offer it", async () => {
  state.contract = { ...ON, sideBySide: undefined };
  const title = await openAlso();
  expect(document.querySelector("[data-also-expanded]")!.textContent).not.toContain(ALSO_COPY.keys.side);
  fireEvent.keyDown(title, { key: "s" });
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 20)); });
  expect(api.readerSideBySideSection).not.toHaveBeenCalled();
  expect(pane()).toBeNull();
});

// -- (ii) peek crumb vs side by side crumb ----------------------------------------------------------

it("(ii) side by side from an also-list peek replaces the peek crumb; Alt+←/→ walk the stack; no peek comes back", async () => {
  await openAlso();
  fireEvent.click(await screen.findByTitle("Axler · 7.A Self-adjoint operators"));
  await waitFor(() => expect(peekCrumb()).toBeTruthy());
  expect(strip()!.textContent).toContain("peek Axler §7.A");
  fireEvent.click(await screen.findByRole("button", { name: `${ALSO_COPY.sideBySide} (s)` }));
  await waitFor(() => expect(pane()?.dataset.sideBySidePane).toBe("pane"));
  await waitFor(() => expect(peekCrumb()).toBeNull());
  expect(within(strip()!).getByRole("button", { name: "side by side with Axler §7.A" })).toBeTruthy();
  expect(within(strip()!).queryByText(/peek Axler/)).toBeNull();
  // Alt+← walks back to where the learner was (the pane closes, no peek reopens); Alt+→ forward again.
  fireEvent.keyDown(document.body, { key: "ArrowLeft", altKey: true });
  await waitFor(() => expect(pane()).toBeNull());
  expect(peekCrumb()).toBeNull();
  fireEvent.keyDown(document.body, { key: "ArrowRight", altKey: true });
  await waitFor(() => expect(pane()?.dataset.sideBySidePane).toBe("pane"));
  expect(peekCrumb()).toBeNull();
});

it("(ii) side by side from a find-list peek replaces the peek crumb too", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: FIND_COPY.action }));
  fireEvent.click(await screen.findByRole("button", { name: "peek at Axler 5.A Invariant subspaces" }));
  await waitFor(() => expect(peekCrumb()).toBeTruthy());
  fireEvent.click(await screen.findByRole("button", { name: FIND_COPY.readSideBySide }));
  await waitFor(() => expect(pane()?.dataset.sideBySidePane).toBe("pane"));
  await waitFor(() => expect(peekCrumb()).toBeNull());
  expect(within(strip()!).getByRole("button", { name: "side by side with Axler §5.A" })).toBeTruthy();
});

it("(ii) Esc closes only what is shown: a peek in the rail overlay first, then the second pane", async () => {
  const title = await openAlso();
  fireEvent.keyDown(title, { key: "s" });
  await waitFor(() => expect(pane()?.dataset.sideBySidePane).toBe("pane"));
  // \ opens the rail as an overlay; x reopens the list there; a peek in it.
  fireEvent.keyDown(document.body, { key: "\\" });
  await waitFor(() => expect(rail().style.display).not.toBe("none"));
  fireEvent.keyDown(document.body, { key: "x" });
  await waitFor(() => expect(document.activeElement?.hasAttribute("data-also-title")).toBe(true));
  const line = document.activeElement as HTMLElement;
  fireEvent.keyDown(line, { key: " " });
  await waitFor(() => expect(peekCrumb()).toBeTruthy());
  fireEvent.keyDown(document.activeElement ?? line, { key: "Escape" });
  await waitFor(() => expect(peekCrumb()).toBeNull());
  expect(pane()?.dataset.sideBySidePane).toBe("pane");
  // Esc in the second pane closes it (and only it).
  fireEvent.keyDown(pane()!.querySelector("[data-sbs-body]")!, { key: "Escape" });
  await waitFor(() => expect(pane()).toBeNull());
  expect(strip()).toBeNull();
});

it("(ii) in a narrow window side by side from a peek is the sheet: no crumb of either kind is left", async () => {
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 900 });
  await openAlso();
  fireEvent.click(await screen.findByTitle("Axler · 7.A Self-adjoint operators"));
  await waitFor(() => expect(peekCrumb()).toBeTruthy());
  fireEvent.click(await screen.findByRole("button", { name: `${ALSO_COPY.sideBySide} (s)` }));
  await waitFor(() => expect(pane()?.dataset.sideBySidePane).toBe("sheet"));
  await waitFor(() => expect(strip()).toBeNull());
});

// -- (iii) the switch matrix (frontend half; the contract half is tests/test_reader_ca6_side_by_side.py) --

it("(iii) correspondence off, side by side on: no also line or find action; Ctrl+\\ still opens side by side", async () => {
  state.contract = { ...ON, correspondence: undefined };
  api.readerCorrespondents.mockImplementation(async (input: { searchFallback?: boolean }) => (input.searchFallback ? ALSO : QUIET));
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findAllByText("6.1 Symmetric matrices");
  expect(alsoLine()).toBeNull();
  expect(screen.queryByRole("button", { name: FIND_COPY.action })).toBeNull();
  await act(async () => { fireEvent.keyDown(document.body, { key: "\\", ctrlKey: true }); });
  await waitFor(() => expect(api.readerSideBySideSection).toHaveBeenCalledWith({ extractionId: "ext_axler", sectionId: "ax7a" }));
});

it("(iii) also-in-your-books off (CA5a's find on), side by side on: the find list keeps `s`", async () => {
  state.contract = { ...ON, correspondence: { enabled: true, findSection: true } };
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  fireEvent.click(await screen.findByRole("button", { name: FIND_COPY.action }));
  await screen.findByRole("button", { name: "side by side with Axler 5.A Invariant subspaces" });
  expect(alsoLine()).toBeNull();
});

it("(iii) all off: no also line, no find action, no side by side, Ctrl+\\ and x read nothing", async () => {
  state.contract = { readerEnabled: true, inquiryEnabled: true, libraryAsk: LIBRARY };
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findAllByText("6.1 Symmetric matrices");
  await act(async () => { fireEvent.keyDown(document.body, { key: "\\", ctrlKey: true }); });
  fireEvent.keyDown(document.body, { key: "x" });
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 20)); });
  expect(alsoLine()).toBeNull();
  expect(screen.queryByRole("button", { name: FIND_COPY.action })).toBeNull();
  expect(api.readerCorrespondents).not.toHaveBeenCalled();
  expect(api.readerSideBySideSection).not.toHaveBeenCalled();
  expect(pane()).toBeNull();
});

// -- (iv) one record per action ----------------------------------------------------------------------

it("(iv) peek, side by side and go there each record once, with CA5's payload keys", async () => {
  await openAlso();
  fireEvent.click(await screen.findByTitle("Axler · 7.A Self-adjoint operators"));
  await waitFor(() => expect(peekCrumb()).toBeTruthy());
  fireEvent.click(await screen.findByRole("button", { name: `${ALSO_COPY.sideBySide} (s)` }));
  await waitFor(() => expect(pane()?.dataset.sideBySidePane).toBe("pane"));
  expect(named("corresponding_section_peeked")).toHaveLength(1);
  expect(named("side_by_side_opened")).toHaveLength(1);
  expect(named("corresponding_section_opened")).toHaveLength(0);
  const peeked = named("corresponding_section_peeked")[0].payload;
  expect(Object.keys(peeked).sort()).toEqual(["by", "extraction_id", "section_id", "target_extraction_id", "target_section_id", "target_source_id", "target_span_id", "via"]);
});

it("(iv) the narrow window's sheet records corresponding_section_peeked once, with CA5's keys (plus the visit)", async () => {
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 900 });
  const title = await openAlso();
  fireEvent.keyDown(title, { key: "s" });
  await waitFor(() => expect(pane()?.dataset.sideBySidePane).toBe("sheet"));
  const peeked = named("corresponding_section_peeked");
  expect(peeked).toHaveLength(1);
  expect(named("side_by_side_opened")).toHaveLength(0);
  expect(peeked[0].payload).toMatchObject({
    extraction_id: view.extractionId, section_id: "u1", target_source_id: "src_axler", target_extraction_id: "ext_axler",
    target_section_id: "ax7a", target_span_id: "a40", by: "judged", via: "also_list",
  });
});
