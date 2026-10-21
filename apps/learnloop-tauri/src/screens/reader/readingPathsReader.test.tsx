// RW7a in the Reader (spec §10.1; UX §4.11, Moment 0, W1): with readingPaths
// in the prompt contract the Guide shows the path card in place of the goal
// card, and Orient's "what matters here?" opens it (the Guide tab, the card
// scrolled into view); no model sees the selection for it.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "../ReaderScreen";
import { setAlgoConfig } from "../../app/algoConfig";
import { readerRenderViewFixture as view } from "../../fixtures/readerRenderView";
import { readerIntentContractFixture as intent } from "../../fixtures/readerIntentContract";
import type { ReadingPathDto, SourceLibraryCard } from "../../api/dto";
import { resetReaderActivityForTests } from "./activity";

const { api, plan } = vi.hoisted(() => ({
  api: {
    readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
    readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
    readerLogActivity: vi.fn(), readerRouteIntent: vi.fn(), readerIntentRouting: vi.fn(), readerIntentOutcome: vi.fn(),
    readerSetMode: vi.fn(), readerReadingPath: vi.fn(), readerReadingPathSetDepth: vi.fn(), readerReadingPathOverride: vi.fn(),
  },
  plan: {
    sourceId: "src", extractionId: "ext", personalized: true, selectionBasis: "",
    goalContext: { goalId: "goal_mix", title: "Derive mixture distributions", goldenPathRunId: null, targetContractVersionId: null },
    sections: [], pendingDiagnosisAttemptIds: [],
  },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../api/useCachedQuery", () => ({ useCachedQuery: (key: string[]) => ({ data: key[0] === "reader_prompt_contract" ? CONTRACT : { sources: [source.card] }, error: null }) }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ readGuidePlan: () => Promise.resolve(plan), useGuideDiagnosisRefresh: () => undefined }));
vi.mock("./useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const CONTRACT = {
  readerEnabled: true, inquiryEnabled: true, intent, activeReading: { foldBlocks: 3 },
  readingPaths: { enabled: true, depths: [{ id: "get_the_idea", label: "get the idea" }, { id: "learn_to_use_it", label: "learn to use it" }, { id: "fluency", label: "fluency" }] },
};
const source = { card: { sourceId: view.sourceId, title: "Matrices", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard, spanId: "span_spectral_worked" };
const BOX = "What do you want to do with this?";
const PATH: ReadingPathDto = {
  extractionId: view.extractionId, status: "ready", depth: "learn_to_use_it", depthLabel: "learn to use it", depthOrigin: "guide",
  intent: null, depths: [], goal: { id: "goal_mix", title: "Derive mixture distributions" },
  goalLine: "toward your goal: Derive mixture distributions",
  sections: [{ sectionId: "u1", title: "Symmetric matrices", startSpanId: view.blocks[1].spanId!, label: "core", chip: "core",
    reason: "needed for the spectral theorem", override: null, effectiveLabel: "core", exercise: null, words: 200, learningObjectIds: [] }],
  next: { text: "Next: read Symmetric matrices · about 1 min of reading", sectionId: "u1", spanId: null, exercise: null, minutes: 1 },
};

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
  api.readerReadingPath.mockResolvedValue(PATH);
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); setAlgoConfig(undefined); window.getSelection()?.removeAllRanges(); });

it("the Guide shows the reading path in place of the goal card", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  expect(await screen.findByText("Next: read Symmetric matrices · about 1 min of reading")).toBeTruthy();
  expect(screen.getByText("toward your goal: Derive mixture distributions")).toBeTruthy();
  expect(screen.queryByText("Reading toward your active goal")).toBeNull();
  expect(api.readerReadingPath).toHaveBeenCalledWith({ extractionId: view.extractionId });
});

it("Orient's what matters here? opens the Guide's path without asking a model", async () => {
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findByText(/Next: read Symmetric/);
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  const block = await screen.findByText(view.blocks[1].markdown);
  select(block);
  await screen.findByRole("textbox", { name: BOX });
  fireEvent.keyDown(window, { key: "Tab" });
  const palette = await screen.findByRole("group", { name: "what do you want to do?" });
  const scrolled = (Element.prototype.scrollIntoView as ReturnType<typeof vi.fn>).mock.calls.length;
  await act(async () => { fireEvent.click(within(palette).getByRole("button", { name: "what matters here?" })); });
  await waitFor(() => expect(screen.getByText(/Next: read Symmetric/).closest("[style*='display: none']")).toBeNull());
  expect((Element.prototype.scrollIntoView as ReturnType<typeof vi.fn>).mock.calls.length).toBeGreaterThan(scrolled);
  expect(api.readerRouteIntent).not.toHaveBeenCalled();
});

// Codex review F3: the mounted card follows the learner. After a ready
// answer, coming back to the Guide reads the path again (no remount), so a
// "next" the learner has moved past is replaced.
it("a ready path is read again when the Guide is shown again, without a remount", async () => {
  const later: ReadingPathDto = { ...PATH, next: { ...PATH.next!, text: "Next: read Orthogonal matrices · about 2 min of reading" } };
  let moved = false;
  api.readerReadingPath.mockImplementation(async () => (moved ? later : PATH));
  render(<ReaderScreen initialSource={source} onError={vi.fn()} />);
  await screen.findByText(PATH.next!.text);
  // Let the open's own reads settle (the plan arriving is a refresh signal too).
  await act(async () => { await new Promise((resolve) => setTimeout(resolve, 2600)); });
  expect(screen.getByText(PATH.next!.text)).toBeTruthy();
  const before = api.readerReadingPath.mock.calls.length;
  moved = true; // the learner read on (the server's next line moves)
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  fireEvent.click(screen.getByRole("button", { name: "guide" }));
  expect(await screen.findByText(later.next!.text, undefined, { timeout: 4000 })).toBeTruthy();
  expect(api.readerReadingPath.mock.calls.length).toBe(before + 1);
  expect(screen.queryByText(PATH.next!.text)).toBeNull();
}, 15_000);
