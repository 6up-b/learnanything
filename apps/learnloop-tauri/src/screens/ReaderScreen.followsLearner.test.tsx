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
  marks: [] as Array<Record<string, unknown>>,
  // Progress saves fail while true (the database is busy, the sidecar is gone).
  failMarks: false
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
      if (backend.failMarks) throw { code: "database_busy", message: "database is locked", retryable: true };
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
  backend.failMarks = false;
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
  // The learner's own wheel moves the page (round 2: only that is reading).
  fireEvent.wheel(body, { deltaY: 100 });
  fireEvent.scroll(body);
  await settle(50);
}

// Longer than the Reader's settling after an open or a resume (1.5 s).
const SETTLED_MS = 2_000;

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
  // The learner reads on once the resumed page has settled (a resume is not
  // reading: finishing pass, re-test #2).
  await settle(SETTLED_MS);
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
  await settle(SETTLED_MS);
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

// ---------------------------------------------------------------------------
// UX Phase 1 usability round 2 (docs/reviews/ux-phase1.md, "Usability round 2
// fixes"): the re-test with the same two personas.
// ---------------------------------------------------------------------------

it("R3: a book with reading history but no saved place reopens after the furthest section read", async () => {
  // Months of reading before places were saved: Contents ticks these sections.
  backend.progress = [
    { extractionId: EXTRACTION_ID, sectionId: "u2", spansSeen: 0, spanCount: 1, revealedAt: null, completedAt: "2026-07-27T17:00:00Z", generationBatchId: null },
    { extractionId: EXTRACTION_ID, sectionId: "u3", spansSeen: 0, spanCount: 2, revealedAt: null, completedAt: "2026-07-27T17:58:33Z", generationBatchId: null }
  ];

  await openReader();

  // u4 "Sample spaces and Pebble World" starts on page 4.
  expect(pane.scrollToPage).toHaveBeenCalledWith(4, 0);
  expect(within(contentsEntry("Sample spaces and Pebble World")).queryByText("◐")).not.toBeNull();
});

it("R3: a place saved by the Reader still wins over the older history", async () => {
  backend.progress = [
    { extractionId: EXTRACTION_ID, sectionId: "u3", spansSeen: 0, spanCount: 2, revealedAt: null, completedAt: "2026-07-27T17:58:33Z", generationBatchId: null }
  ];
  window.localStorage.setItem(`learnloop.reader.position.${SOURCE_ID}`, "s2");

  await openReader();

  expect(pane.scrollToPage).toHaveBeenCalledWith(1, expect.any(Number));
  expect(pane.scrollToPage).not.toHaveBeenCalledWith(4, expect.any(Number));
});

it("writes no quick check for a section before the learner has read in it", async () => {
  await openReader();
  // The page settles (images load, the view re-lays out) without the learner
  // moving: the reading marker is already far down the first, short section.
  fireEvent.scroll(screen.getByTestId("pdf-pane").parentElement!);
  await settle(3_000);

  expect(invoke.mock.calls.some(([command]) => command === "reader_author_section_question")).toBe(false);
  // Nor does the guide say the learner is near a section break they never read to.
  expect(screen.queryByText(/near the section break/)).toBeNull();

  // Reading on does ask for one, for the section actually read.
  await scrollTo(2900);
  await settle(1_000);
  const asked = invoke.mock.calls.filter(([command]) => command === "reader_author_section_question");
  expect(asked.length).toBeGreaterThan(0);
  expect(asked[asked.length - 1][1]).toMatchObject({ input: { sectionId: "u3" } });
});

it("after the learner compares, the guide no longer says the check is waiting", async () => {
  backend.withCheck = true;
  window.localStorage.setItem(`learnloop.reader.position.${SOURCE_ID}`, "s4");
  await openReader();
  await settle(SETTLED_MS);
  await scrollTo(2900);
  expect(screen.getByText("A quick check on this section is ready, just below.")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "quick check →" }));
  await settle();
  fireEvent.change(screen.getByPlaceholderText("Answer in your own words…"), { target: { value: "Uncertainty is everywhere." } });
  fireEvent.click(screen.getByRole("button", { name: /compare with the source/ }));
  await settle();

  expect(screen.queryByText("A quick check on this section is ready, just below.")).toBeNull();
  expect(screen.getByText("You answered this section's quick check: compare below, then keep reading.")).toBeTruthy();
  // Nor does the Guide tab still count it as a check waiting.
  expect(screen.queryByRole("button", { name: /quick check ready/ })).toBeNull();
  expect(screen.getByRole("button", { name: "guide" })).toBeTruthy();
});

it("Contents says in words which sections have a quick check, and never a bare '?'", async () => {
  backend.withCheck = true;
  await openReader();

  const entry = contentsEntry("Why study probability?");
  expect(within(entry).queryByText("?")).toBeNull();
  expect(within(entry).getByText("quick check")).toBeTruthy();
  // A finished check needs no marker next to its tick.
  backend.progress = [
    { extractionId: EXTRACTION_ID, sectionId: "u3", spansSeen: 2, spanCount: 2, revealedAt: null, completedAt: "2026-10-13T10:00:00Z", generationBatchId: null }
  ];
  cleanup();
  clear();
  await openReader();
  const done = contentsEntry("Why study probability?");
  expect(within(done).queryByText("✓")).not.toBeNull();
  expect(within(done).queryByText("quick check")).toBeNull();
});

it("Ask shows each question once, and its answer style in words", async () => {
  const askHistory = {
    version: 1,
    exchanges: [{
      eventId: "ev_1", spanId: "s3", questionMd: "When does the naive definition fail?",
      answerMd: "When outcomes are not equally likely.", answerMode: "answer_directly", createdAt: "2026-10-13T09:47:21Z"
    }]
  };
  invoke.mockImplementation(async (command: string, args?: { input?: Record<string, unknown> }) =>
    command === "reader_ask_history" ? askHistory : sidecar(command, args)
  );
  await openReader();
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  await settle();
  fireEvent.click(screen.getByRole("button", { name: /When does the naive definition fail\?/ }));
  await settle();

  expect(screen.getAllByText("When does the naive definition fail?")).toHaveLength(1);
  expect(screen.queryByText("answer_directly")).toBeNull();
  expect(screen.getByText("answer directly")).toBeTruthy();
});

it("opening a book shows that book opening, not a second list of books", async () => {
  let release: (value: unknown) => void = () => undefined;
  invoke.mockImplementation(async (command: string, args?: { input?: Record<string, unknown> }) => {
    if (command === "reader_render_view") return new Promise((resolve) => { release = resolve; });
    return sidecar(command, args);
  });
  render(<ReaderScreen onError={() => undefined} initialSource={{ card: CARD, spanId: null }} />);
  await settle(200);

  expect(screen.queryByText(/Pick up where you left off/)).toBeNull();
  expect(screen.getByText(/Opening Introduction to Probability/)).toBeTruthy();

  release(VIEW);
  await settle(2_000);
  expect(screen.getByTestId("pdf-pane")).toBeTruthy();
});

it("with no book open, the Reader shows the Library's own shelf, not a second list (spec K5)", async () => {
  render(<ReaderScreen onError={() => undefined} shelf={<div data-testid="the-shelf">the one shelf</div>} />);
  await settle(2_000);

  expect(screen.getByTestId("the-shelf")).toBeTruthy();
  expect(screen.queryByText(/READER · LIBRARY/)).toBeNull();
  // Its own cards are gone; searching every book's text stays.
  expect(screen.queryByText("Introduction to Probability")).toBeNull();
  expect(screen.getByPlaceholderText("search all sources…")).toBeTruthy();
  expect(screen.getByText("Pick a book to read, or search them all.")).toBeTruthy();
});

it("R3: a book with block geometry reaches the passage's page even before the document is laid out", async () => {
  // Axler in the three-month library: boxes for every passage. The resume
  // asked the pane to centre a block on a page that did not exist yet, and
  // the pane silently stayed on the chapter's first page.
  const blocks = PAGES.map(([spanId, page]) => ({ spanId, page, bbox: [50, 100, 550, 300], blockType: "Text" }));
  invoke.mockImplementation(async (command: string, args?: { input?: Record<string, unknown> }) =>
    command === "reader_pdf_view"
      ? { version: 1, available: true, fileName: "sha256-prob", extractionId: EXTRACTION_ID, sourceId: SOURCE_ID, revisionId: "rev_prob", blocks, pageSpans: [] }
      : sidecar(command, args)
  );
  backend.progress = [
    { extractionId: EXTRACTION_ID, sectionId: "u3", spansSeen: 0, spanCount: 2, revealedAt: null, completedAt: "2026-07-27T17:58:33Z", generationBatchId: null }
  ];

  await openReader();

  // The passage itself, which the pane keeps until its page is laid out and
  // drawn (round-2 review F4; PdfReaderPane.scroll.test.tsx), at the top of
  // the view: the place to read on from (finishing pass, re-test #2).
  expect(pane.scrollToSegment).toHaveBeenCalledWith(4, "s5", "start");
});

it("watching a video is reading: playback still earns the section's quick check", async () => {
  const video: SourceLibraryCard = { ...CARD, sourceId: "src_vid", canonicalUri: "https://www.youtube.com/watch?v=abcdefghijk" };
  const cues = ["v1", "v2", "v3", "v4", "v5"];
  const view: ReaderRenderViewDto = {
    ...VIEW,
    sourceId: "src_vid",
    blocks: cues.map((spanId, index) => ({
      ...VIEW.blocks[0],
      displayNodeId: `node-${spanId}`,
      spanId,
      extractorBlockId: `t=${index * 10}-${index * 10 + 10}`,
      markdown: `Caption ${spanId}.`
    }))
  };
  const videoPlan = {
    version: 1, sourceId: "src_vid", extractionId: EXTRACTION_ID, personalized: false, selectionBasis: "", goalContext: null,
    pendingDiagnosisAttemptIds: [],
    sections: [{ id: "u1", label: "The lecture", startSpanId: "v1", endSpanId: "v5", spanIds: cues, question: null, suggestedPassages: [] }]
  };
  invoke.mockImplementation(async (command: string, args?: { input?: Record<string, unknown> }) => {
    if (command === "reader_render_view") return view;
    if (command === "reader_guide_plan") return videoPlan;
    if (command === "reader_watch_plan") return { version: 1, sourceId: "src_vid", videoId: "abcdefghijk", embedUrl: "https://www.youtube-nocookie.com/embed/abcdefghijk", pausePoints: [] };
    return sidecar(command, args);
  });
  // jsdom has no smooth scrolling; the transcript follows playback with it.
  Element.prototype.scrollTo = vi.fn();
  render(<ReaderScreen onError={() => undefined} initialSource={{ card: video, spanId: null }} />);
  await settle(2_000);
  fireEvent.load(document.querySelector("iframe")!);
  await settle(100);

  for (const seconds of [2, 12, 22, 32, 42]) {
    window.dispatchEvent(new MessageEvent("message", {
      origin: "https://www.youtube-nocookie.com",
      data: JSON.stringify({ event: "infoDelivery", info: { currentTime: seconds } })
    }));
    await settle(100);
  }

  const asked = invoke.mock.calls.filter(([command]) => command === "reader_author_section_question");
  expect(asked.length).toBeGreaterThan(0);
});

// ---------------------------------------------------------------------------
// Codex review of usability round 2 (docs/reviews/ux-phase1-round2-codex-review.md)
// ---------------------------------------------------------------------------

function marksFor(sectionId: string) {
  return backend.marks.filter((mark) => mark.sectionId === sectionId);
}

it("F3: a progress save that failed is sent again when the learner leaves the Reader", async () => {
  backend.failMarks = true;
  await openReader();
  await scrollTo(1500);
  await scrollTo(2900);
  // Long enough for the save and every retry to fail.
  await settle(30_000);
  expect(marksFor("u3")).toEqual([]);

  backend.failMarks = false;
  cleanup();
  await settle();

  expect(marksFor("u3").length).toBeGreaterThan(0);
  expect(Number(marksFor("u3")[0].spansSeen)).toBeGreaterThanOrEqual(1);
});

it("F3: a progress save that failed once is retried without leaving", async () => {
  let failures = 1;
  invoke.mockImplementation(async (command: string, args?: { input?: Record<string, unknown> }) => {
    if (command === "reader_mark_section_progress" && failures > 0) {
      failures -= 1;
      throw { code: "database_busy", message: "database is locked", retryable: true };
    }
    return sidecar(command, args);
  });
  await openReader();
  await scrollTo(1500);
  await scrollTo(2900);
  await settle(3_000);
  await settle(5_000);

  expect(marksFor("u3").length).toBeGreaterThan(0);
});

it("F3: a save the backend acknowledged is not sent again on leaving", async () => {
  await openReader();
  await scrollTo(1500);
  await scrollTo(2900);
  await settle(3_000);
  const sent = marksFor("u3").length;
  expect(sent).toBeGreaterThan(0);

  cleanup();
  await settle();

  expect(marksFor("u3").length).toBe(sent);
});

it("F3: leaving a book inside the Reader saves what was just read, before the gathering moment ends", async () => {
  // The Reader's own way back to its shelf (no Library place to go to): the
  // book's state is reset, which used to drop the gathered counts unsent.
  await openReader();
  await scrollTo(1500);
  await scrollTo(2900);

  fireEvent.click(screen.getByRole("button", { name: "← Library" }));
  await settle();

  expect(marksFor("u3").length).toBeGreaterThan(0);
});

it("F7: a retry still waiting when the learner leaves the book saves the newest count, not the one that failed first", async () => {
  // Re-review F7: the save of 1 fails and a retry is set; the learner reads on
  // to 2 and leaves through the Reader's own shelf, whose save fails too. The
  // retry used to resend the first failure's 1 and nothing ever sent the 2.
  backend.failMarks = true;
  await openReader();
  await scrollTo(1500);
  await scrollTo(2900); // u3: one of its two passages read
  await settle(1_600); // the gathered save of 1 fails; a retry waits
  expect(marksFor("u3")).toEqual([]);
  await scrollTo(3200); // u3: read through its last page (2 of 2)

  fireEvent.click(screen.getByRole("button", { name: "← Library" })); // this save of 2 fails as well
  await settle();
  backend.failMarks = false;
  await settle(30_000);

  const saved = marksFor("u3").map((mark) => Number(mark.spansSeen));
  expect(saved.length).toBeGreaterThan(0);
  expect(Math.max(...saved)).toBe(2);
});

it("F7: the newest count of a book left behind is still sent when the Reader closes", async () => {
  // Every timed retry fails too: the book's newest count waits for the Reader
  // to close, though the learner went back to the shelf in between.
  backend.failMarks = true;
  await openReader();
  await scrollTo(1500);
  await scrollTo(2900);
  await settle(1_600);
  await scrollTo(3200);
  fireEvent.click(screen.getByRole("button", { name: "← Library" }));
  await settle(60_000);
  expect(marksFor("u3")).toEqual([]);

  backend.failMarks = false;
  cleanup();
  await settle();

  expect(marksFor("u3").map((mark) => Number(mark.spansSeen))).toEqual([2]);
});

function videoFixture() {
  const video: SourceLibraryCard = { ...CARD, sourceId: "src_vid", canonicalUri: "https://www.youtube.com/watch?v=abcdefghijk" };
  const cues = ["v1", "v2", "v3", "v4", "v5"];
  const videoView: ReaderRenderViewDto = {
    ...VIEW,
    sourceId: "src_vid",
    blocks: cues.map((spanId, index) => ({
      ...VIEW.blocks[0],
      displayNodeId: `node-${spanId}`,
      spanId,
      extractorBlockId: `t=${index * 10}-${index * 10 + 10}`,
      markdown: `Caption ${spanId}.`
    }))
  };
  // A long first part and a short last one: landing on it is most of it.
  const videoPlan = {
    version: 1, sourceId: "src_vid", extractionId: EXTRACTION_ID, personalized: false, selectionBasis: "", goalContext: null,
    pendingDiagnosisAttemptIds: [],
    sections: [
      { id: "u1", label: "The lecture", startSpanId: "v1", endSpanId: "v4", spanIds: ["v1", "v2", "v3", "v4"], question: null, suggestedPassages: [] },
      { id: "u2", label: "Summary", startSpanId: "v5", endSpanId: "v5", spanIds: ["v5"], question: null, suggestedPassages: [] }
    ]
  };
  invoke.mockImplementation(async (command: string, args?: { input?: Record<string, unknown> }) => {
    if (command === "reader_render_view") return videoView;
    if (command === "reader_guide_plan") return videoPlan;
    if (command === "reader_watch_plan") return { version: 1, sourceId: "src_vid", videoId: "abcdefghijk", embedUrl: "https://www.youtube-nocookie.com/embed/abcdefghijk", pausePoints: [] };
    return sidecar(command, args);
  });
  Element.prototype.scrollTo = vi.fn();
  return video;
}

function player(info: Record<string, unknown>) {
  window.dispatchEvent(new MessageEvent("message", {
    origin: "https://www.youtube-nocookie.com",
    data: JSON.stringify({ event: "infoDelivery", info })
  }));
}

function authoredFor(sectionId: string) {
  return invoke.mock.calls.filter(
    ([command, args]) => command === "reader_author_section_question" && (args as { input?: { sectionId?: string } })?.input?.sectionId === sectionId
  );
}

it("F5: jumping a paused video to a short section is not watching it", async () => {
  const video = videoFixture();
  render(<ReaderScreen onError={() => undefined} initialSource={{ card: video, spanId: null }} />);
  await settle(2_000);
  fireEvent.load(document.querySelector("iframe")!);
  await settle(100);
  // Paused at the start.
  player({ playerState: 2, currentTime: 2 });
  await settle(100);

  fireEvent.click(contentsEntry("Summary"));
  await settle(100);
  // The player reports the time it was taken to (and a late report of where it was).
  player({ currentTime: 2 });
  await settle(100);
  player({ currentTime: 40 });
  await settle(3_000);

  expect(authoredFor("u2")).toEqual([]);
  expect(within(contentsEntry("Summary")).queryByText("✓")).toBeNull();
});

it("F5: playing on after a jump is watching", async () => {
  const video = videoFixture();
  render(<ReaderScreen onError={() => undefined} initialSource={{ card: video, spanId: null }} />);
  await settle(2_000);
  fireEvent.load(document.querySelector("iframe")!);
  await settle(100);
  player({ playerState: 2, currentTime: 2 });
  await settle(100);
  fireEvent.click(contentsEntry("The lecture"));
  await settle(2_000);

  player({ playerState: 1 });
  for (const seconds of [2, 12, 22, 32]) {
    player({ currentTime: seconds });
    await settle(100);
  }

  expect(authoredFor("u1").length).toBeGreaterThan(0);
});


// ---------------------------------------------------------------------------
// UX Phase 1 finishing pass: the persona re-test's Reader minors.
// ---------------------------------------------------------------------------

/** The guide's bar under the current section's name, as a width. */
function sectionBarWidth(): string {
  // The Guide's current-section card: its "section" pill, then the bar below.
  const card = screen.getAllByText("section")[0].parentElement!.parentElement!;
  const fill = card.querySelector<HTMLElement>('div[style*="height: 3px"] > div');
  return fill?.style.width ?? "";
}

it("#7: the guide's section bar is empty on arriving at a section not read yet, and fills as it is read", async () => {
  await openReader();
  // A one-page section: the reading marker lands on its only passage.
  fireEvent.click(contentsEntry("Probability and counting"));
  await settle(SETTLED_MS);
  expect(screen.getAllByText("Probability and counting").length).toBeGreaterThan(1);
  expect(sectionBarWidth()).toBe("0%");
  expect(screen.getByRole("progressbar", { name: "Read of this section" }).getAttribute("aria-valuenow")).toBe("0");

  // Into section 1.1 (pages 2-3): nothing of it read on arrival, then a page
  // counts once the reading marker is past most of it.
  await scrollTo(1500);
  expect(screen.getAllByText("Why study probability?").length).toBeGreaterThan(1);
  expect(sectionBarWidth()).toBe("0%");
  await scrollTo(2200);
  expect(sectionBarWidth()).toBe("50%");
  await scrollTo(3200);
  expect(sectionBarWidth()).toBe("100%");
});

it("#8: the original's section break waits for the section's last page", async () => {
  backend.withCheck = true;
  await openReader();
  await settle(SETTLED_MS);

  // Section 1.1 is pages 2-3: on its first page the check is not offered yet.
  await scrollTo(1500);
  await settle(3_000);
  expect(screen.getAllByText("Why study probability?").length).toBeGreaterThan(1);
  expect(screen.queryByRole("button", { name: "quick check →" })).toBeNull();
  expect(screen.queryByText("A quick check on this section is ready, just below.")).toBeNull();
  expect(screen.queryByRole("button", { name: /quick check ready/ })).toBeNull();

  // On its last page it is, and it stays while the learner looks back a page.
  await scrollTo(2900);
  expect(screen.getByRole("button", { name: "quick check →" })).toBeTruthy();
  expect(screen.getByText("A quick check on this section is ready, just below.")).toBeTruthy();
  await scrollTo(1500);
  expect(screen.getByRole("button", { name: "quick check →" })).toBeTruthy();
});

it("#2: a resume into a section offers its leftover check only after the learner reads there", async () => {
  // Axler: reopened on 1.36, whose check was written last time; the section
  // break asked about 1.36 before it was read again.
  backend.withCheck = true;
  window.localStorage.setItem(`learnloop.reader.position.${SOURCE_ID}`, "s4");
  await openReader();
  await settle(SETTLED_MS);

  expect(screen.queryByRole("button", { name: "quick check →" })).toBeNull();
  expect(screen.queryByText("A quick check on this section is ready, just below.")).toBeNull();
  // Contents still says the section has one.
  expect(within(contentsEntry("Why study probability?")).getByText("quick check")).toBeTruthy();

  // Reading there (the learner's own scroll on its last page) offers it.
  await scrollTo(2900);
  expect(screen.getByRole("button", { name: "quick check →" })).toBeTruthy();
});

it("#2: Contents puts a section's start at the top of the view, where the header names it", async () => {
  const blocks = PAGES.map(([spanId, page]) => ({ spanId, page, bbox: [50, 100, 550, 300], blockType: "Text" }));
  invoke.mockImplementation(async (command: string, args?: { input?: Record<string, unknown> }) =>
    command === "reader_pdf_view"
      ? { version: 1, available: true, fileName: "sha256-prob", extractionId: EXTRACTION_ID, sourceId: SOURCE_ID, revisionId: "rev_prob", blocks, pageSpans: [] }
      : sidecar(command, args)
  );
  await openReader();
  fireEvent.click(contentsEntry("Why study probability?"));
  await settle();
  expect(pane.scrollToSegment).toHaveBeenLastCalledWith(2, "s3", "start");
});


it("#4: a new Ask answer is brought into view, not left below the fold", async () => {
  invoke.mockImplementation(async (command: string, args?: { input?: Record<string, unknown> }) =>
    command === "reader_ask"
      ? { readerAnswerEventId: "ev_new", answerMd: "When outcomes are not equally likely.", answerMode: "answer_directly" }
      : sidecar(command, args)
  );
  window.localStorage.setItem(`learnloop.reader.position.${SOURCE_ID}`, "s3");
  await openReader();
  fireEvent.click(screen.getByRole("button", { name: "ask" }));
  await settle();
  const scrolled = vi.mocked(Element.prototype.scrollIntoView);
  scrolled.mockClear();

  const box = screen.getByPlaceholderText("ask about this passage…");
  fireEvent.change(box, { target: { value: "When does the naive definition fail?" } });
  fireEvent.keyDown(box, { key: "Enter", ctrlKey: true });
  await settle();

  expect(screen.getByText("When outcomes are not equally likely.")).toBeTruthy();
  const brought = scrolled.mock.contexts.map((element) => (element as HTMLElement).dataset?.askId);
  expect(brought).toContain("ev_new");
  const call = scrolled.mock.calls[brought.indexOf("ev_new")][0] as ScrollIntoViewOptions;
  expect(call.block).toBe("start");
});
