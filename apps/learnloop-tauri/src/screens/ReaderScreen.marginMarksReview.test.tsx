// RW3a Codex review (reader-hook-rw3a), on the real screen with the real Guide
// plan module (its diagnosis refresh included):
//   F1  Alt+↓ to a mark that is already drawn is a placement, not reading:
//       after ordinary reading it credits no passage it passes, saves no
//       count for them and writes no check;
//   F2  a diagnosis that lands while the book is open reaches the mark's
//       popover, as it reaches the rail (the margin and the rail agree);
//   F3  a check me, or a plan re-read, answered after the learner opened
//       another book is dropped: no practice, and the open book keeps its plan;
//   F4  "not relevant" keeps its undo through unrelated changes (the density,
//       another mark set aside) until the learner leaves the book.
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ReaderScreen } from "./ReaderScreen";
import { readerRenderViewFixture } from "../fixtures/readerRenderView";
import type {
  CueDensity, ReaderCueActionDto, ReaderCueDto, ReaderGuidePlanDto, ReaderRenderViewDto, SourceLibraryCard,
} from "../api/dto";
import { clear as clearQueryCache } from "../api/queryCache";
import { resetReaderActivityForTests } from "./reader/activity";
import { GUIDE_DIAGNOSIS_POLL_MS } from "./reader/guidePlan";

const api = vi.hoisted(() => ({
  readerRenderView: vi.fn(), readerGuidePlan: vi.fn(), readerGetProgress: vi.fn(), readerPdfView: vi.fn(),
  readerDrainOutbox: vi.fn(), readerSourceAnnotations: vi.fn(), readerAskHistory: vi.fn(), readerAsk: vi.fn(),
  readerLogActivity: vi.fn(), readerSetMode: vi.fn(), readerCueAction: vi.fn(), readerSetCuePreferences: vi.fn(),
  readerNoteReadingProgress: vi.fn(), readerAuthorSectionQuestion: vi.fn(), readerMarkSectionProgress: vi.fn(),
  readerRestoreSource: vi.fn(),
}));
const library = vi.hoisted(() => ({ sources: [] as unknown[] }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../api/useCachedQuery", () => ({
  useCachedQuery: (key: string[]) => ({
    data: key[0] === "reader_prompt_contract" ? { readerEnabled: true, inquiryEnabled: true } : { sources: library.sources },
    error: null,
  }),
}));
vi.mock("./reader/readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./reader/useReaderRequests", () => ({
  useReaderRequests: () => ({ requests: [], proposalCount: 0, synthesizedObjects: new Map(), openProposalIds: new Set(), loadError: null, refresh: () => Promise.resolve() }),
  parseRequestError: () => null, parseRequestResult: () => ({}),
}));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const SPANS = ["b0", "b1", "b2", "b3", "b4", "b5"];
const view: ReaderRenderViewDto = {
  ...readerRenderViewFixture,
  blocks: SPANS.map((spanId, index) => ({
    ...readerRenderViewFixture.blocks[1], spanId, displayNodeId: `node-${spanId}`,
    markdown: `Passage ${index}: the density of a mixture.`,
  })),
};
const viewB: ReaderRenderViewDto = {
  ...readerRenderViewFixture, sourceId: "src_b", extractionId: "ext_b",
  blocks: [{ ...readerRenderViewFixture.blocks[1], spanId: "c1", displayNodeId: "node-c1", markdown: "Book B explains densities another way." }],
};
const cardA = { sourceId: view.sourceId, title: "Probability", canonicalUri: "book.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const cardB = { sourceId: "src_b", title: "Book B", canonicalUri: "b.pdf", readiness: "ready", readerEnabled: true } as SourceLibraryCard;
const STATEMENT = "The learner reads a density value as a probability.";

// The sidecar's state: the learner's density, the cues set aside, and whether
// the cited answer's diagnosis is still being written.
const backend = { density: "normal" as CueDensity, dismissed: new Set<string>(), diagnosisPending: false };

function cue(spanId: string, rank: number): ReaderCueDto {
  const note = "Connects to something you worked on: Densities.";
  const because = "Because: your answer on 2 Oct · from the Guide's citations";
  return {
    cueId: `cue_${spanId}`, kind: "revisit", spanId, sectionId: "u1", learningObjectId: "lo_density",
    learningObjectTitle: "Densities", targetId: "err_1", rank, sectionRank: rank, note, because,
    label: `Note on this paragraph: ${note} ${because}`,
    earlier: {
      attemptId: "att_1", practiceItemId: "pi_density", prompt: "Is f(0.5) = 2 a probability?", answer: "Yes, twice as likely.",
      answeredAt: "2026-10-02T09:00:00Z", answeredOn: "2 Oct",
      statement: backend.diagnosisPending ? null : STATEMENT, statementPending: backend.diagnosisPending,
    },
  };
}

function planA(): ReaderGuidePlanDto {
  const reason = backend.diagnosisPending ? "Revisit this to resolve: conceptual slip" : `Revisit this to resolve: ${STATEMENT}`;
  const passages = ["b1", "b4"].map((spanId) => ({
    spanId, quote: `Passage ${SPANS.indexOf(spanId)}`, reason, learningObjectId: "lo_density",
    learningObjectTitle: "Densities", learnerSignal: "recent_misunderstanding",
  }));
  const marks = [cue("b1", 0), cue("b4", 1)].filter((entry) => !backend.dismissed.has(entry.cueId));
  return {
    version: 1, sourceId: view.sourceId, extractionId: view.extractionId, personalized: true, selectionBasis: "",
    goalContext: null, pendingDiagnosisAttemptIds: backend.diagnosisPending ? ["att_1"] : [],
    sections: [{ id: "u1", label: "Mixture densities", startSpanId: "b0", endSpanId: "b5", spanIds: SPANS, question: null, suggestedPassages: passages }],
    cues: {
      version: "rw3a-guide-cues-v1", density: backend.density, budgetPerSection: 2, onePerViewport: true,
      sourceOff: false, marks: backend.density === "off" ? [] : marks, withheld: {},
    },
  } as ReaderGuidePlanDto;
}

function planB(): ReaderGuidePlanDto {
  return {
    version: 1, sourceId: viewB.sourceId, extractionId: viewB.extractionId, personalized: true, selectionBasis: "",
    goalContext: null, pendingDiagnosisAttemptIds: [],
    sections: [{ id: "v1", label: "Book B basics", startSpanId: "c1", endSpanId: "c1", spanIds: ["c1"], question: null, suggestedPassages: [] }],
    cues: { version: "rw3a-guide-cues-v1", density: backend.density, budgetPerSection: 2, onePerViewport: true, sourceOff: false, marks: [], withheld: {} },
  } as ReaderGuidePlanDto;
}

function tapResult(input: { cueId: string; action: string }): ReaderCueActionDto {
  return { cueId: input.cueId, action: input.action as ReaderCueActionDto["action"], eventId: "ev", verdict: "same", ledgerId: null, check: null };
}

// jsdom has no layout: each passage of book A sits TOPS[span] - scroll.y from
// the reading area's top; the reading area is 600px tall, its marker 420px down.
const TOPS: Record<string, number> = { b0: 400, b1: 500, b2: 700, b3: 900, b4: 1500, b5: 1700 };
const scroll = { y: 0 };

function rect(top: number, height: number): DOMRect {
  return { top, bottom: top + height, left: 0, right: 500, width: 500, height, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
}

beforeEach(() => {
  vi.useFakeTimers({
    toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "Date", "requestAnimationFrame", "cancelAnimationFrame"],
  });
  vi.resetAllMocks();
  clearQueryCache();
  resetReaderActivityForTests();
  library.sources = [cardA, cardB];
  backend.density = "normal";
  backend.dismissed = new Set();
  backend.diagnosisPending = false;
  scroll.y = 0;
  Element.prototype.scrollIntoView = vi.fn();
  api.readerRenderView.mockImplementation(async (input: { extractionId: string }) => (input.extractionId === "src_b" ? viewB : view));
  api.readerGuidePlan.mockImplementation(async (input: { extractionId: string }) => (input.extractionId === viewB.extractionId ? planB() : planA()));
  api.readerGetProgress.mockResolvedValue({ sections: [] });
  api.readerPdfView.mockResolvedValue({ available: false });
  api.readerDrainOutbox.mockResolvedValue({ failed: [], drained: [] });
  api.readerSourceAnnotations.mockResolvedValue({ annotations: [] });
  api.readerAskHistory.mockResolvedValue({ exchanges: [] });
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerSetMode.mockResolvedValue({ mode: "skim" });
  api.readerNoteReadingProgress.mockResolvedValue({});
  api.readerMarkSectionProgress.mockResolvedValue({});
  api.readerAuthorSectionQuestion.mockResolvedValue({ status: "queued", question: null });
  api.readerRestoreSource.mockResolvedValue({ eventId: "restored" });
  api.readerCueAction.mockImplementation(async (input: { cueId: string; action: string }) => {
    if (input.action === "not_relevant") backend.dismissed.add(input.cueId);
    if (input.action === "not_relevant_undone") backend.dismissed.delete(input.cueId);
    return tapResult(input);
  });
  api.readerSetCuePreferences.mockImplementation(async (input: { density?: CueDensity | null }) => {
    if (input.density) backend.density = input.density;
    return { enabled: true, density: backend.density, budgetPerSection: 2, onePerViewport: true, sourceOff: false, offSourceCount: 0 };
  });
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
    const element = this as HTMLElement;
    if (element.getAttribute("role") === "main") return rect(0, 600);
    const spanId = element.dataset?.spanId;
    if (spanId && spanId in TOPS) return rect(TOPS[spanId] - scroll.y, 40);
    return rect(0, 0);
  });
  Object.defineProperty(HTMLElement.prototype, "clientHeight", {
    configurable: true,
    get(this: HTMLElement) {
      return this.getAttribute("role") === "main" ? 600 : 0;
    },
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.useRealTimers();
  // @ts-expect-error -- restore jsdom's own (prototype chain) getter
  delete HTMLElement.prototype.clientHeight;
});

/** Let ``ms`` pass in small steps, so React commits between timers (as it does
 *  in the app), then a few more frames. */
async function settle(ms = 0) {
  for (let elapsed = 0; elapsed < ms + 160; elapsed += 40) {
    await act(async () => {
      await vi.advanceTimersByTimeAsync(40);
    });
  }
}

// Longer than the Reader's settling after an open, a resume or a jump (1.5 s).
const SETTLED_MS = 2_000;

function openReader(props: { onCheckMe?: (request: unknown) => void } = {}) {
  return render(<ReaderScreen initialSource={{ card: cardA, spanId: null }} onError={vi.fn()} onCheckMe={props.onCheckMe} />);
}

const markFor = (spanId: string) => document.querySelector<HTMLButtonElement>(`[data-cue-span="${spanId}"]`);
const popover = () => screen.getByRole("group", { name: "this margin note" });

async function openBookB() {
  fireEvent.click(screen.getByText("← Library"));
  await settle(100);
  fireEvent.click(screen.getByText("Book B"));
  await settle(100);
  expect(screen.getAllByText("Book B explains densities another way.").length).toBeGreaterThan(0);
}

async function setAside(spanId: string) {
  fireEvent.click(markFor(spanId) as HTMLButtonElement);
  fireEvent.click(within(popover()).getByRole("button", { name: "not relevant…" }));
  fireEvent.click(within(popover()).getByRole("button", { name: "send" }));
  await settle(100);
}

it("F1: Alt+↓ to a mark already drawn is a placement -- after ordinary reading it credits no passage and writes no check", async () => {
  openReader();
  await settle(SETTLED_MS);
  expect(markFor("b1")).not.toBeNull();
  expect(markFor("b4")).not.toBeNull();
  const main = screen.getByRole("main");
  // Ordinary reading: the learner's wheel brings b1 under the reading marker.
  scroll.y = 80;
  fireEvent.wheel(main);
  fireEvent.scroll(main);
  await settle(SETTLED_MS);
  const seen = () => api.readerNoteReadingProgress.mock.calls.map(([input]) => (input as { spansSeen: number }).spansSeen);
  expect(seen()).toEqual([2]); // b0 and b1 of the section's six
  // Alt+↓: the mark at the reading position; Alt+↓ again: the far one, already drawn.
  fireEvent.keyDown(window, { key: "ArrowDown", altKey: true });
  expect(document.activeElement).toBe(markFor("b1"));
  await settle(100);
  fireEvent.keyDown(document.activeElement as Element, { key: "ArrowDown", altKey: true });
  expect(document.activeElement).toBe(markFor("b4"));
  // The webview scrolls the focused mark into view (jsdom does not): b4 is
  // now under the marker, three unread passages above it.
  scroll.y = 1080;
  fireEvent.scroll(main);
  await settle(3 * SETTLED_MS);
  expect(Math.max(...seen())).toBe(2);
  expect(api.readerAuthorSectionQuestion).not.toHaveBeenCalled();
});

it("F2: a diagnosis that lands while the book is open reaches the mark's popover, as it reaches the rail", async () => {
  backend.diagnosisPending = true;
  openReader();
  await settle(100);
  // The rail's passages, revealed: their reason names the error type for now.
  fireEvent.click(screen.getByRole("button", { name: /show 2 passages I may have missed/ }));
  await settle(100);
  expect(screen.getAllByText("Revisit this to resolve: conceptual slip")).toHaveLength(2);
  fireEvent.click(markFor("b1") as HTMLButtonElement);
  fireEvent.click(within(popover()).getByRole("button", { name: "open · what you worked on" }));
  expect(within(popover()).getByText("LearnLoop's model is still reading that answer.")).toBeTruthy();
  expect(popover().querySelector("[data-voice='model']")).toBeNull();
  // The diagnosis lands; the Reader's own refresh re-reads the plan.
  backend.diagnosisPending = false;
  await settle(GUIDE_DIAGNOSIS_POLL_MS + 100);
  expect(screen.getAllByText(`Revisit this to resolve: ${STATEMENT}`)).toHaveLength(2);
  expect(popover().querySelector("[data-voice='model']")?.textContent).toContain(STATEMENT);
  expect(within(popover()).queryByText("LearnLoop's model is still reading that answer.")).toBeNull();
  // A resize keeps the marks where they are and keeps them current.
  act(() => {
    window.dispatchEvent(new Event("resize"));
  });
  await settle(100);
  expect(popover().querySelector("[data-voice='model']")?.textContent).toContain(STATEMENT);
});

it("F3: a check me answered after the learner opened another book is dropped -- no practice, the book stays", async () => {
  let release: (value: ReaderCueActionDto) => void = () => undefined;
  api.readerCueAction.mockImplementation((input: { cueId: string; action: string }) => (
    input.action === "check_me"
      ? new Promise<ReaderCueActionDto>((resolve) => {
        release = resolve;
      })
      : Promise.resolve(tapResult(input))
  ));
  const onCheckMe = vi.fn();
  openReader({ onCheckMe });
  await settle(100);
  fireEvent.click(markFor("b1") as HTMLButtonElement);
  fireEvent.click(within(popover()).getByRole("button", { name: /^check me ·/ }));
  await openBookB();
  await act(async () => {
    release({
      ...tapResult({ cueId: "cue_b1", action: "check_me" }),
      check: { status: "found", practiceItemId: "pi_density_2", proposalId: "pp_1" },
    });
  });
  await settle(100);
  expect(onCheckMe).not.toHaveBeenCalled();
  expect(screen.getAllByText("Book B explains densities another way.").length).toBeGreaterThan(0);
});

it("F3: a plan re-read for the book the learner left never replaces the open book's plan", async () => {
  openReader();
  await settle(100);
  expect(screen.getAllByText("Mixture densities").length).toBeGreaterThan(0);
  // Not relevant on book A: the tap lands, and its plan re-read is held back.
  let releasePlan: () => void = () => undefined;
  api.readerGuidePlan.mockImplementation((input: { extractionId: string }) => (
    input.extractionId === view.extractionId
      ? new Promise<ReaderGuidePlanDto>((resolve) => {
        releasePlan = () => resolve(planA());
      })
      : Promise.resolve(planB())
  ));
  await setAside("b1");
  await openBookB();
  expect(screen.getAllByText("Book B basics").length).toBeGreaterThan(0);
  await act(async () => {
    releasePlan();
  });
  await settle(100);
  expect(screen.getAllByText("Book B basics").length).toBeGreaterThan(0);
  expect(screen.queryAllByText("Mixture densities")).toEqual([]);
  // Book A's receipt never follows the learner into book B.
  expect(screen.queryByText("Marked not relevant.")).toBeNull();
});

it("F4: not relevant keeps its undo through the density and another mark set aside, until the learner leaves the book", async () => {
  openReader();
  await settle(100);
  await setAside("b1");
  expect(markFor("b1")).toBeNull();
  expect(screen.getAllByText("Marked not relevant.")).toHaveLength(1);
  // An unrelated change: the density, from the Guide's footer.
  fireEvent.click(within(screen.getByRole("group", { name: "margin marks" })).getByRole("button", { name: "more" }));
  await settle(100);
  expect(api.readerSetCuePreferences).toHaveBeenLastCalledWith(expect.objectContaining({ density: "more", via: "footer" }));
  expect(screen.getAllByText("Marked not relevant.")).toHaveLength(1);
  // Another mark set aside: each keeps its own undo.
  await setAside("b4");
  expect(screen.getAllByText("Marked not relevant.")).toHaveLength(2);
  const undos = screen.getAllByRole("button", { name: "undo" });
  expect(undos).toHaveLength(2);
  fireEvent.click(undos[0]);
  await settle(100);
  expect(api.readerCueAction).toHaveBeenLastCalledWith({
    extractionId: view.extractionId, cueId: "cue_b1", action: "not_relevant_undone", text: null,
  });
  expect(markFor("b1")).not.toBeNull();
  expect(screen.getAllByText("Marked not relevant.")).toHaveLength(1);
  // Leaving the book ends the undo window.
  await openBookB();
  expect(screen.queryByText("Marked not relevant.")).toBeNull();
});
