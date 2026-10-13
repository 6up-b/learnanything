// UX Phase 1, usability round 1 (docs/reviews/ux-phase1.md): the original PDF
// follows the learner. Two personas read a textbook whose text came from the
// text-only extractor (one passage per page, no boxes): clicking a section in
// Contents left them on the title page and ticked the sections they skipped,
// scrolling was never tracked so no quick check ever came in the original,
// coming back opened the title page again, and the quick check the section
// break offered was hidden below the whole Contents list.
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { forwardRef, useImperativeHandle } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderGuidePlanDto, ReaderRenderViewDto, ReaderSectionQuestionDto, SourceLibraryCard } from "../api/dto";
import { clear } from "../api/queryCache";
import { ReaderScreen } from "./ReaderScreen";

const { invoke, pane } = vi.hoisted(() => ({
  invoke: vi.fn(),
  pane: { scrollToPage: vi.fn(), scrollToSegment: vi.fn() }
}));
vi.mock("@tauri-apps/api/core", () => ({ invoke, convertFileSrc: (path: string) => path }));
// The original PDF: five laid-out pages, and the pane's scroll handle.
vi.mock("../components/PdfReaderPane", () => ({
  PdfReaderPane: forwardRef(function FakePane(_props: unknown, ref) {
    useImperativeHandle(ref, () => pane);
    return (
      <div data-testid="pdf-pane">
        {[0, 1, 2, 3, 4].map((page) => (
          <div key={page} data-pdf-page={page} data-width-points="612" />
        ))}
      </div>
    );
  })
}));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

const SOURCE_ID = "src_prob";
const EXTRACTION_ID = "ext_prob";
// One passage per page, as the text-only extractor writes them.
const PAGES: Array<[string, number]> = [["s1", 0], ["s2", 1], ["s3", 2], ["s4", 3], ["s5", 4]];

const VIEW: ReaderRenderViewDto = {
  renderViewId: "rv_prob",
  extractionId: EXTRACTION_ID,
  revisionId: "rev_prob",
  sourceId: SOURCE_ID,
  renderer: "marker_markdown",
  rendererVersion: "1",
  contentHash: "sha256:prob",
  status: "ready",
  layers: {},
  blocks: PAGES.map(([spanId]) => ({
    displayNodeId: `node-${spanId}`,
    spanId,
    blockType: "Text",
    markdown: `Text of ${spanId}.`,
    sanitized: false,
    katexNodes: [],
    assets: [],
    health: { status: "ok", recommendedView: "derived", reasonFlags: [] }
  }))
};

const CARD: SourceLibraryCard = {
  sourceId: SOURCE_ID,
  title: "Introduction to Probability",
  acquisitionKind: "pdf",
  canonicalUri: null,
  workId: null,
  currentRevisionId: "rev_prob",
  revisionCount: 1,
  readiness: "ready",
  unitCount: 4,
  blockCount: PAGES.length,
  extractionStatus: "completed",
  suggestedRole: null,
  readerEnabled: true,
  updateAvailable: false
};

const QUICK_CHECK: ReaderSectionQuestionDto = {
  practiceItemId: null,
  learningObjectId: null,
  learningObjectTitle: null,
  prompt: "What is the main point of 'Why study probability?'",
  reason: "Written from this section's text.",
  learnerSignal: "auto_authored",
  goalId: null,
  goalTitle: null,
  goldenPathRunId: null,
  targetContractVersionId: null,
  readingPhase: "after_section",
  pattern: null,
  placementEventId: null,
  blueprintVersionId: null,
  placement: "auto_authored",
  authoredQuestionId: "raq_1",
  expectedAnswer: "Probability is the logic of uncertainty.",
  spanIds: ["s3"],
  escalationLearningObjectId: null
};

const backend = {
  withCheck: false,
  progress: [] as Array<Record<string, unknown>>,
  marks: [] as Array<Record<string, unknown>>
};

function plan(): ReaderGuidePlanDto {
  const section = (id: string, label: string, spanIds: string[], question: ReaderSectionQuestionDto | null = null) => ({
    id, label, startSpanId: spanIds[0], endSpanId: spanIds[spanIds.length - 1], spanIds, question, suggestedPassages: []
  });
  return {
    version: 1,
    sourceId: SOURCE_ID,
    extractionId: EXTRACTION_ID,
    personalized: false,
    selectionBasis: "",
    goalContext: null,
    pendingDiagnosisAttemptIds: [],
    sections: [
      section("u1", "Table of Contents", ["s1"]),
      section("u2", "Probability and counting", ["s2"]),
      section("u3", "Why study probability?", ["s3", "s4"], backend.withCheck ? QUICK_CHECK : null),
      section("u4", "Sample spaces and Pebble World", ["s5"])
    ]
  } as ReaderGuidePlanDto;
}

function sidecar(command: string, args?: { input?: Record<string, unknown> }): unknown {
  switch (command) {
    case "reader_prompt_contract":
      return {
        version: "1", context: "reader", readerEnabled: true, notSocraticByDefault: true,
        defaultAnswerMode: "answer_directly", answerModes: ["answer_directly"], mayReveal: [],
        manifestIncludes: [], manifestNeverIncludes: [], citations: "", exposureOnCommit: ""
      };
    case "get_source_library":
      return { version: 1, sources: [CARD] };
    case "reader_render_view":
      return VIEW;
    case "reader_guide_plan":
      return plan();
    case "reader_get_progress":
      return { version: 1, extractionId: EXTRACTION_ID, sections: backend.progress };
    case "reader_pdf_view":
      return {
        version: 1, available: true, fileName: "sha256-prob", extractionId: EXTRACTION_ID, sourceId: SOURCE_ID,
        revisionId: "rev_prob", blocks: [], pageSpans: PAGES.map(([spanId, page]) => ({ spanId, page }))
      };
    case "reader_mark_section_progress":
      backend.marks.push(args?.input ?? {});
      return { version: 1, progress: {}, enqueuedGeneration: false, batchId: null };
    case "reader_author_section_question":
      return { version: 1, status: "queued", batchId: "b1", question: null };
    case "reader_authored_question_action":
      return { version: 1, question: {} };
    case "reader_ask_history":
      return { version: 1, exchanges: [] };
    case "reader_source_annotations":
      return { version: 1, annotations: [] };
    case "reader_source_requests":
      return { version: 1, requests: [] };
    case "reader_source_objects":
      return { version: 1, sourceObjects: [] };
    case "reader_proposal_inbox":
      return { version: 1, proposals: [] };
    case "reader_drain_outbox":
      return { version: 1, drained: [], failed: [] };
    default:
      throw { code: "not_mocked", message: `${command} is not mocked`, retryable: false };
  }
}

function memoryStorage(): Storage {
  const values = new Map<string, string>();
  return {
    get length() {
      return values.size;
    },
    clear: () => values.clear(),
    getItem: (key: string) => values.get(key) ?? null,
    key: (index: number) => Array.from(values.keys())[index] ?? null,
    removeItem: (key: string) => void values.delete(key),
    setItem: (key: string, value: string) => void values.set(key, String(value))
  };
}

// jsdom has no layout: each page is 1000px tall, the reading area 1000px, and
// `view.scrollY` is how far the learner has scrolled.
const view = { scrollY: 0 };
const PAGE = 1000;

function rect(top: number, height: number): DOMRect {
  return { top, bottom: top + height, height, width: 600, left: 0, right: 600, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
}

beforeEach(() => {
  // Animation frames too: the Reader follows the learner on the next frame.
  vi.useFakeTimers({
    toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "Date", "requestAnimationFrame", "cancelAnimationFrame"]
  });
  clear();
  backend.withCheck = false;
  backend.progress = [];
  backend.marks = [];
  view.scrollY = 0;
  pane.scrollToPage.mockReset();
  pane.scrollToSegment.mockReset();
  vi.stubGlobal("localStorage", memoryStorage());
  Element.prototype.scrollIntoView = vi.fn();
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
    const page = (this as HTMLElement).dataset?.pdfPage;
    if (page !== undefined) return rect(Number(page) * PAGE - view.scrollY, PAGE);
    return rect(0, PAGE);
  });
  invoke.mockReset().mockImplementation(async (command: string, args?: { input?: Record<string, unknown> }) => sidecar(command, args));
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

async function settle(ms = 0) {
  // A frame's worth each round: chained reads resolve, then their frames run.
  for (let i = 0; i < 8; i += 1) {
    await act(async () => {
      await vi.advanceTimersByTimeAsync(i === 0 ? ms : 20);
    });
  }
}

async function openReader(props: Partial<Parameters<typeof ReaderScreen>[0]> = {}) {
  const result = render(<ReaderScreen onError={() => undefined} initialSource={{ card: CARD, spanId: null }} {...props} />);
  await settle(2_000);
  return result;
}

/** The learner scrolls the original so that ``scrollY`` px are above the view. */
async function scrollTo(scrollY: number) {
  view.scrollY = scrollY;
  const body = screen.getByTestId("pdf-pane").parentElement!;
  fireEvent.scroll(body);
  await settle(50);
}

function contentsEntry(label: string): HTMLElement {
  return screen.getByRole("button", { name: new RegExp(label.replace(/[?]/g, "\\?")) });
}

it("Contents takes the original PDF to the section's page and ticks nothing it skipped", async () => {
  await openReader();

  fireEvent.click(contentsEntry("Why study probability?"));
  await settle();

  expect(pane.scrollToPage).toHaveBeenCalledWith(2, 0);
  expect(within(contentsEntry("Table of Contents")).queryByText("✓")).toBeNull();
  expect(within(contentsEntry("Probability and counting")).queryByText("✓")).toBeNull();
});

it("follows the reading position through the original and saves how far each section was read", async () => {
  await openReader();

  // The reading marker sits 700px down the view: 1500 puts it 20% into page 2
  // (section 1.1's first page), 2900 90% into page 3 (its last).
  await scrollTo(1500);
  await scrollTo(2900);
  await settle(3_000);

  // The Guide's current section moved with the learner...
  expect(screen.getAllByText("Why study probability?").length).toBeGreaterThan(0);
  expect(within(contentsEntry("Why study probability?")).queryByText("◐")).not.toBeNull();
  // ...and how far into it they read is saved, so Today and a restart know.
  const marks = backend.marks.filter((mark) => mark.sectionId === "u3");
  expect(marks.length).toBeGreaterThan(0);
  expect(marks[marks.length - 1]).toMatchObject({ extractionId: EXTRACTION_ID, spanCount: 2 });
  expect(Number(marks[marks.length - 1].spansSeen)).toBeGreaterThanOrEqual(1);
});

it("a section read through to its end is ticked, now and after a restart", async () => {
  backend.progress = [{
    extractionId: EXTRACTION_ID, sectionId: "u3", spansSeen: 2, spanCount: 2,
    revealedAt: null, completedAt: null, generationBatchId: null
  }];
  await openReader();

  expect(within(contentsEntry("Why study probability?")).queryByText("✓")).not.toBeNull();
  expect(within(contentsEntry("Probability and counting")).queryByText("✓")).toBeNull();
});

it("reopens the original where the learner left off", async () => {
  window.localStorage.setItem(`learnloop.reader.position.${SOURCE_ID}`, "s4");

  await openReader();

  expect(pane.scrollToPage).toHaveBeenCalledWith(3, expect.any(Number));
});

it("the section break's quick check opens the check, above the Contents, ready to answer", async () => {
  backend.withCheck = true;
  window.localStorage.setItem(`learnloop.reader.position.${SOURCE_ID}`, "s4");
  await openReader();
  await scrollTo(2900); // the end of section 1.1

  // The original PDF has a section-break offer of its own.
  fireEvent.click(screen.getByRole("button", { name: "quick check →" }));
  await settle();

  const answer = screen.getByPlaceholderText("Answer in your own words…");
  expect(document.activeElement).toBe(answer);
  // The check sits above the Contents list, not under it.
  const contentsHeader = screen.getByText("Contents");
  expect(answer.compareDocumentPosition(contentsHeader) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});

it("keeps the learner's answer beside the intended answer, and the button names the real shortcut", async () => {
  backend.withCheck = true;
  window.localStorage.setItem(`learnloop.reader.position.${SOURCE_ID}`, "s4");
  await openReader();
  await scrollTo(2900);
  fireEvent.click(screen.getByRole("button", { name: "quick check →" }));
  await settle();

  const answer = screen.getByPlaceholderText("Answer in your own words…");
  fireEvent.change(answer, { target: { value: "Because uncertainty is everywhere in science." } });
  const compare = screen.getByRole("button", { name: /compare with the source/ });
  expect(compare.textContent).toMatch(/ctrl\+↵/);
  fireEvent.keyDown(answer, { key: "Enter", ctrlKey: true });
  await settle();

  expect(screen.getByText("Because uncertainty is everywhere in science.")).toBeTruthy();
  expect(screen.getByText("Probability is the logic of uncertainty.")).toBeTruthy();
});

it("← Library goes to the Library, and the demo chapter is not on the main path", async () => {
  const onOpenLibrary = vi.fn();
  await openReader({ onOpenLibrary });

  fireEvent.click(screen.getByRole("button", { name: "← Library" }));

  expect(onOpenLibrary).toHaveBeenCalledTimes(1);
});

it("the Reader's own book list offers no demo chapter while LearnLoop is running", async () => {
  render(<ReaderScreen onError={() => undefined} />);
  await settle(2_000);

  expect(screen.getByText("Introduction to Probability")).toBeTruthy();
  expect(screen.queryByText(/demo chapter/)).toBeNull();
});
