// RW4b on the Reader (spec §7.4; UX §4.6): the candidate cards inside RW4a's
// "practice this question", with the Reader's two actions wired: "use this
// one" hands the shell the exercise and the source it is in (a learner pick
// the shell opens in the working posture; another book opens as a detour so
// the problem opens beside its own page), and without the workbench a card
// offers only the book. The setup is RW4a's (libraryAsk.test.tsx).
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { LibraryAskDto, LibraryNotesDto, SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerSetMode: vi.fn(), readerSearchSources: vi.fn(),
    readerLibraryAsk: vi.fn(), readerLibraryAskNotes: vi.fn(), readerLibraryCompare: vi.fn(), readerLibraryAskTutor: vi.fn(),
    readerLibraryJob: vi.fn(), readerLibraryJobCancel: vi.fn(),
    findPractice: vi.fn(), recordProposalImpressions: vi.fn(), getSpanView: vi.fn(),
    readerExerciseCandidates: vi.fn(), readerFindExercises: vi.fn(),
  },
  contract: { value: {} as Record<string, unknown> },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? contract.value : { sources: [source.card, other] }, error: null }) }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve({ sections: [] }), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
const other = { sourceId: "src_other", title: "Other Book", canonicalUri: "other.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const BOX = "What do you want to do with this?";

function hit(key: string, sourceId: string, sourceTitle: string, text: string, extra: Record<string, unknown> = {}) {
  const [extractionId, spanId] = key.split(":");
  return { key, extractionId, spanId, sourceId, sourceTitle, section: "Chapter 5", page: 3, text, role: "definition",
    group: "Foundation", expansion: null, learningObjectIds: [], authorship: "source" as const, label: "source-authored", ...extra };
}

const ASK: LibraryAskDto = {
  askId: "la_1", query: "symmetric matrices", entry: "where_else_explained", status: "ok", policy: "reading",
  personalized: true, basis: "keyword + meaning", learningObjectIds: ["lo_spectral"], extractionId: view.extractionId,
  anchorSpanIds: ["span_symmetric_prose"],
  hits: [
    hit("ext_other:o1", "src_other", "Other Book", "A symmetric matrix equals its transpose."),
    hit("ext_symmetric:span_spectral_worked", view.sourceId, "Matrices", "Worked: diagonalize a symmetric matrix.", { role: "worked_example", group: "Worked example" }),
    hit("ext_other:o9", "src_other", "Other Book", "Vectors and their span.", { expansion: "prerequisites", group: "Prerequisite", learningObjectIds: ["lo_vectors"] }),
  ],
  groups: {
    sources: [
      { sourceId: "src_other", sourceTitle: "Other Book", groups: [{ group: "Foundation", keys: ["ext_other:o1"] }] },
      { sourceId: view.sourceId, sourceTitle: "Matrices", groups: [{ group: "Worked example", keys: ["ext_symmetric:span_spectral_worked"] }] },
    ],
    expansions: [{ expansion: "prerequisites", label: "Prerequisite", keys: ["ext_other:o9"] }],
  },
  expansions: [{ expansion: "prerequisites", label: "Prerequisite", learningObjects: [{ learningObjectId: "lo_vectors", title: "Vector lists", demonstrated: false, keys: ["ext_other:o9"] }] }],
  expandGraph: true, sourceCount: 2, passageCount: 3,
};

function notes(extra: Partial<LibraryNotesDto> = {}): LibraryNotesDto {
  return {
    askId: "la_1", status: "judged",
    notes: [
      { key: "ext_other:o1", verdict: "contributes", ledgerId: "lac_1", line: "gives the transpose definition", roles: ["definition"], speaksTo: { id: "gap:1", statement: "why eigenvalues are real" }, label: "LearnLoop's model" },
      { key: "ext_symmetric:span_spectral_worked", verdict: "contributes", ledgerId: "lac_2", line: "works one example through", roles: ["worked_example"], speaksTo: null, label: "LearnLoop's model" },
    ],
    order: ["ext_symmetric:span_spectral_worked", "ext_other:o1", "ext_other:o9"], ...extra,
  };
}

/** A library RPC's job, already done with ``result`` (the sidecar runs each off the request path). */
function done<T>(result: T, kind = "ask") {
  return { jobId: `ljob_${kind}`, kind, askId: "la_1", state: "done" as const, result };
}

/** A job still running: the first read answers pending, then the deferred result lands. */
function pendingJob(kind: string) {
  return { jobId: `ljob_${kind}`, kind, askId: "la_1", state: "pending" as const, result: null };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => { resolve = r; });
  return { promise, resolve };
}

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

async function askFromSelection() {
  const onCheckMe = vi.fn();
  const onUseExercise = vi.fn();
  render(<ReaderScreen initialSource={source} onError={vi.fn()} onCheckMe={onCheckMe} onUseExercise={onUseExercise} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "where else is this explained?" }));
  return { onCheckMe, onUseExercise, block };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  contract.value = { readerEnabled: true, inquiryEnabled: true, intent, activeReading: { foldBlocks: 3 },
    libraryAsk: { expandGraph: true, personalizedDefault: true, compare: true }, libraryExercises: { fallback: false } };
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
  api.readerRenderView.mockResolvedValue(view);
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerIntentOutcome.mockResolvedValue({ routingId: "r", recorded: true });
  api.readerSetMode.mockResolvedValue({ mode: "read" });
  api.readerLibraryAsk.mockResolvedValue(done(ASK));
  api.readerLibraryAskNotes.mockResolvedValue(done(notes(), "notes"));
  api.readerLibraryJobCancel.mockResolvedValue({ jobId: "ljob_x", kind: "notes", askId: "la_1", state: "cancelled", result: null });
  api.recordProposalImpressions.mockResolvedValue({ recorded: 1 });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });


function exercise(key: string, sourceId: string, extractionId: string, span: string, statement: string) {
  return { kind: "source_exercise", key, extractionId, spanIds: [span], sourceId, revisionId: "rev", sourceTitle: sourceId === "src_other" ? "Other Book" : "Matrices",
    label: "Exercise 1", page: 4, statement, rationale: null, labelLine: "From the book · not yet in your practice" };
}
const fresh = { exposed: false, reasons: [], label: null, note: null, offeredAs: "check_on_your_own", exposureRuleVersion: "reading_exposure_v1" };

it("use this one hands the shell the exercise and its source, opening another book as a detour (RW4b)", async () => {
  setAlgoConfig({ workbench: { enabled: true } } as never);
  const here = exercise("srcex:here", view.sourceId, view.extractionId, "span_spectral_worked", "Diagonalize [[2,1],[1,2]].");
  const there = exercise("srcex:there", "src_other", "ext_other", "o5", "1. Show a symmetric matrix has real eigenvalues.");
  api.findPractice.mockResolvedValue({ version: 1, status: "ok", proposalId: "pp_1", items: [], sourceExercises: [here, there] });
  api.readerExerciseCandidates.mockResolvedValue(done({ version: 1, proposalId: "pp_1", withheld: 0, candidates: [
    { key: "srcex:here", extractionId: view.extractionId, spanIds: [], sourceId: view.sourceId, revisionId: "rev", exposure: fresh },
    { key: "srcex:there", extractionId: "ext_other", spanIds: [], sourceId: "src_other", revisionId: "rev", exposure: fresh },
  ] }, "exercise_candidates"));
  const { onUseExercise } = await askFromSelection();
  const pane = await screen.findByRole("region", { name: "ask your library" });
  await within(pane).findByText("gives the transpose definition");
  fireEvent.click(within(pane).getByRole("button", { name: /practice this question/ }));
  const cards = await within(pane).findAllByTestId("exercise-candidate");
  expect(cards).toHaveLength(2);
  const renders = api.readerRenderView.mock.calls.length;
  fireEvent.click(within(cards[0]).getByRole("button", { name: /use this one/ }));
  expect(onUseExercise).toHaveBeenLastCalledWith(expect.objectContaining({
    key: "srcex:here", entry: "practice_this", stemMd: "Diagonalize [[2,1],[1,2]].", sourceId: view.sourceId,
    sourceExercise: { proposalId: "pp_1", extractionId: view.extractionId, spanIds: ["span_spectral_worked"] },
    card: expect.objectContaining({ sourceId: view.sourceId }),
  }));
  expect(api.readerRenderView.mock.calls.length).toBe(renders); // its own book is open: no detour
  fireEvent.click(within(cards[1]).getByRole("button", { name: /use this one/ }));
  expect(onUseExercise).toHaveBeenLastCalledWith(expect.objectContaining({ key: "srcex:there", card: expect.objectContaining({ sourceId: "src_other" }) }));
  await waitFor(() => expect(api.readerRenderView.mock.calls.length).toBeGreaterThan(renders)); // the other book opens as a detour
});

it("without the workbench a card offers only the book (RW4b)", async () => {
  const here = exercise("srcex:here", view.sourceId, view.extractionId, "span_spectral_worked", "Diagonalize [[2,1],[1,2]].");
  api.findPractice.mockResolvedValue({ version: 1, status: "ok", proposalId: "pp_1", items: [], sourceExercises: [here] });
  api.readerExerciseCandidates.mockResolvedValue(done({ version: 1, proposalId: "pp_1", withheld: 0, candidates: [
    { key: "srcex:here", extractionId: view.extractionId, spanIds: [], sourceId: view.sourceId, revisionId: "rev", exposure: fresh },
  ] }, "exercise_candidates"));
  await askFromSelection();
  const pane = await screen.findByRole("region", { name: "ask your library" });
  await within(pane).findByText("gives the transpose definition");
  fireEvent.click(within(pane).getByRole("button", { name: /practice this question/ }));
  const card = await within(pane).findByTestId("exercise-candidate");
  expect(within(card).queryByRole("button", { name: /use this one/ })).toBeNull();
  expect(within(card).getByRole("button", { name: /open in the book/ })).toBeTruthy();
});
