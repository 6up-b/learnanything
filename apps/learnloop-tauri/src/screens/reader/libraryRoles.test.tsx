// Reader workbench RW4e (spec §7.1, §7.9; UX §4.5; G44): a library answer
// labels a passage with the instructional role LearnLoop's model proposed,
// "counterexample (model's label)", only where the sidecar sent one
// (roles.positive_filter_enabled, an ordinary-prose passage); every other
// passage keeps RW4a's label (its group), so with the switch off the answer
// renders exactly as before.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { LibraryAskDto, LibraryNotesDto, SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";
import { hitRoleLabel, MODEL_LABEL } from "./roleLabel";

const { api, contract } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerSetMode: vi.fn(), readerSearchSources: vi.fn(),
    readerLibraryAsk: vi.fn(), readerLibraryAskNotes: vi.fn(), readerLibraryCompare: vi.fn(), readerLibraryAskTutor: vi.fn(),
    readerLibraryJob: vi.fn(), readerLibraryJobCancel: vi.fn(),
    findPractice: vi.fn(), recordProposalImpressions: vi.fn(), getSpanView: vi.fn(),
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

function hit(key: string, text: string, extra: Record<string, unknown> = {}) {
  const [extractionId, spanId] = key.split(":");
  return { key, extractionId, spanId, sourceId: "src_other", sourceTitle: "Other Book", section: "Chapter 5", page: 3, text,
    role: "ordinary_prose", group: "Explanation", expansion: null, learningObjectIds: [], authorship: "source" as const,
    label: "source-authored", ...extra };
}

const PROPOSED = { role: "counterexample", confidence: "high" as const, judges: ["passage_cue_judge"], label: MODEL_LABEL };

const ASK: LibraryAskDto = {
  askId: "la_1", query: "independence and covariance", entry: "where_else_explained", status: "ok", policy: "reading",
  personalized: true, basis: "keyword", learningObjectIds: [], extractionId: view.extractionId,
  anchorSpanIds: ["span_symmetric_prose"],
  hits: [
    hit("ext_other:o1", "Zero covariance does not imply independence.", { group: "Contrast", proposedRole: PROPOSED }),
    hit("ext_other:o2", "Covariance measures linear association."),
  ],
  groups: {
    sources: [{ sourceId: "src_other", sourceTitle: "Other Book", groups: [
      { group: "Explanation", keys: ["ext_other:o2"] }, { group: "Contrast", keys: ["ext_other:o1"] }] }],
    expansions: [],
  },
  expansions: [], expandGraph: true, sourceCount: 1, passageCount: 2,
};

const NOTES: LibraryNotesDto = { askId: "la_1", status: "judged", notes: [], order: [] } as unknown as LibraryNotesDto;

function select(block: HTMLElement): void {
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  contract.value = { readerEnabled: true, inquiryEnabled: true, intent, activeReading: { foldBlocks: 3 },
    libraryAsk: { expandGraph: true, personalizedDefault: true, compare: true } };
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
  api.readerLibraryAsk.mockResolvedValue({ jobId: "ljob_ask", kind: "ask", askId: "la_1", state: "done", result: ASK });
  api.readerLibraryAskNotes.mockResolvedValue({ jobId: "ljob_notes", kind: "notes", askId: "la_1", state: "done", result: NOTES });
  api.recordProposalImpressions.mockResolvedValue({ recorded: 1 });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

it("labels a proposed role as the model's and leaves every other passage's label as RW4a's", () => {
  expect(hitRoleLabel({ group: "Contrast", proposedRole: PROPOSED })).toBe("counterexample (model's label)");
  expect(hitRoleLabel({ group: "Explanation", proposedRole: { ...PROPOSED, role: "alternative_treatment" } }))
    .toBe("alternative treatment (model's label)");
  expect(hitRoleLabel({ group: "Worked example" })).toBe("worked example");
  expect(hitRoleLabel({ group: "Explanation", proposedRole: null })).toBe("explanation");
});

it("a library answer shows the model's label on the proposed passage only (UX §4.5)", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} onCheckMe={vi.fn()} />);
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "where else is this explained?" }));
  await waitFor(() => expect(api.readerLibraryAsk).toHaveBeenCalledTimes(1));
  const pane = await screen.findByRole("region", { name: "ask your library" });
  const proposed = await within(pane).findByLabelText(/Other Book, counterexample \(model's label\) · Chapter 5 · p\.3/);
  expect(proposed.getAttribute("data-library-hit")).toBe("ext_other:o1");
  const plain = within(pane).getByLabelText(/Other Book, explanation · Chapter 5 · p\.3/);
  expect(plain.getAttribute("data-library-hit")).toBe("ext_other:o2");
  expect(within(pane).getAllByText(/model's label/).length).toBeGreaterThan(0);
});
