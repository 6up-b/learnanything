// Reading-hardening, part 2: ONE check-offer rule in the Reader
// (screens/reader/checkOffer.ts), driven through every offer path of the real
// screen. Codex's verify of the finishing pass (F2, reopened) found paths that
// offered a section's leftover check on a resume before the learner read:
//   * the text view's section-break button rendered "quick check →" while the
//     original PDF's manifest was still pending;
//   * a manifest that failed or was unavailable fell back to the text view's
//     70 % rule, which pinned the resumed check;
//   * the text surface opened an existing auto-authored check at once.
// Each path is tested in both response orders (the guide first, the original
// first) and with the manifest failing and unavailable. The rule: a resumed
// check after a section needs the learner's own reading in this visit; a
// section reached by reading follows the normal rules.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { forwardRef, useImperativeHandle } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReaderGuidePlanDto, ReaderRenderViewDto, ReaderSectionQuestionDto, SourceLibraryCard } from "../api/dto";
import { clear } from "../api/queryCache";
import { ReaderScreen } from "./ReaderScreen";

const { invoke, pane } = vi.hoisted(() => ({
  invoke: vi.fn(),
  pane: { scrollToPage: vi.fn(), scrollToSegment: vi.fn() }
}));
vi.mock("@tauri-apps/api/core", () => ({ invoke, convertFileSrc: (path: string) => path }));
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
// One passage per page: u1 = s1, u2 = s2, u3 = s3-s4, u4 = s5.
const PAGES: Array<[string, number]> = [["s1", 0], ["s2", 1], ["s3", 2], ["s4", 3], ["s5", 4]];
const SPAN_INDEX = new Map(PAGES.map(([spanId], index) => [spanId, index]));

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

const AUTO_CHECK: ReaderSectionQuestionDto = {
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

// An after-section check the owner's placement put on Ch. 1's section.
const PLACED_CHECK: ReaderSectionQuestionDto = {
  ...AUTO_CHECK,
  prompt: "How many outcomes does the naive definition count?",
  learnerSignal: "goal_frontier",
  placement: "owner_reviewed",
  placementEventId: "pe_1",
  learningObjectId: "lo_counting",
  learningObjectTitle: "Counting",
  authoredQuestionId: undefined,
  expectedAnswer: undefined,
};

const backend = {
  checks: {} as Record<string, ReaderSectionQuestionDto>,
  pdf: "ok" as "ok" | "error" | "unavailable",
};

function plan(): ReaderGuidePlanDto {
  const section = (id: string, label: string, spanIds: string[]) => ({
    id, label, startSpanId: spanIds[0], endSpanId: spanIds[spanIds.length - 1], spanIds,
    question: backend.checks[id] ?? null, suggestedPassages: []
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
      section("u3", "Why study probability?", ["s3", "s4"]),
      section("u4", "Sample spaces and Pebble World", ["s5"])
    ]
  } as ReaderGuidePlanDto;
}

function sidecar(command: string): unknown {
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
      return { version: 1, extractionId: EXTRACTION_ID, sections: [] };
    case "reader_pdf_view":
      if (backend.pdf === "error") throw { code: "pdf_unreadable", message: "The original could not be opened.", retryable: false };
      if (backend.pdf === "unavailable") return { version: 1, available: false, reason: "no_original" };
      return {
        version: 1, available: true, fileName: "sha256-prob", extractionId: EXTRACTION_ID, sourceId: SOURCE_ID,
        revisionId: "rev_prob", blocks: [], pageSpans: PAGES.map(([spanId, page]) => ({ spanId, page }))
      };
    case "reader_mark_section_progress":
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

// jsdom has no layout: each page of the original, and each passage of the
// text view, is 1000px tall; the reading area is 1000px with its marker 700px
// down; `view.scrollY` is how far the learner has scrolled.
const view = { scrollY: 0 };
const PAGE = 1000;

function rect(top: number, height: number): DOMRect {
  return { top, bottom: top + height, height, width: 600, left: 0, right: 600, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
}

beforeEach(() => {
  vi.useFakeTimers({
    toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "Date", "requestAnimationFrame", "cancelAnimationFrame"]
  });
  clear();
  backend.checks = {};
  backend.pdf = "ok";
  view.scrollY = 0;
  pane.scrollToPage.mockReset();
  pane.scrollToSegment.mockReset();
  vi.stubGlobal("localStorage", memoryStorage());
  Element.prototype.scrollIntoView = vi.fn();
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
    const element = this as HTMLElement;
    const page = element.dataset?.pdfPage;
    if (page !== undefined) return rect(Number(page) * PAGE - view.scrollY, PAGE);
    const passage = element.dataset?.spanId ? SPAN_INDEX.get(element.dataset.spanId) : undefined;
    if (passage !== undefined && element.dataset?.extractionId) return rect(passage * PAGE - view.scrollY, PAGE);
    return rect(0, PAGE);
  });
  invoke.mockReset().mockImplementation(async (command: string) => sidecar(command));
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

async function settle(ms = 0) {
  for (let i = 0; i < 8; i += 1) {
    await act(async () => {
      await vi.advanceTimersByTimeAsync(i === 0 ? ms : 20);
    });
  }
}

// Longer than the Reader's settling after an open or a resume (1.5 s).
const SETTLED_MS = 2_000;

/** ``command``'s answer waits until the returned ``release`` is called. */
function holdBack(command: string): () => Promise<void> {
  let release: () => void = () => undefined;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  const before = invoke.getMockImplementation()!;
  invoke.mockImplementation(async (name: string, ...rest: unknown[]) => {
    if (name === command) await held;
    return before(name, ...rest);
  });
  return async () => {
    release();
    await settle();
    await settle(SETTLED_MS);
  };
}

/** The learner's own wheel moves the reading area so ``scrollY`` px are above it. */
async function readTo(scrollY: number) {
  view.scrollY = scrollY;
  const pdf = screen.queryByTestId("pdf-pane");
  const body = pdf ? pdf.parentElement! : document.querySelector<HTMLElement>('[data-span-id="s1"][data-extraction-id]')!.parentElement!;
  fireEvent.wheel(body, { deltaY: 100 });
  fireEvent.scroll(body);
  await settle(50);
}

/** Opens the book resumed at ``spanId`` with the guide and the original's
 *  manifest answering in ``order``; resolves once both have landed and the
 *  Reader has settled (placing the page is not reading). */
async function resume(spanId: string, order: "guide first" | "original first") {
  window.localStorage.setItem(`learnloop.reader.position.${SOURCE_ID}`, spanId);
  const second = holdBack(order === "guide first" ? "reader_pdf_view" : "reader_guide_plan");
  render(<ReaderScreen onError={() => undefined} initialSource={{ card: CARD, spanId: null }} />);
  await settle(SETTLED_MS);
  return second;
}

function offeredButtons() {
  return screen.queryAllByRole("button", { name: "quick check →" });
}

function nothingOffered(prompt: string) {
  expect(offeredButtons()).toEqual([]);
  expect(screen.queryByText("A quick check on this section is ready, just below.")).toBeNull();
  expect(screen.queryByText("You’re near the section break. Take a quick check or keep reading.")).toBeNull();
  expect(screen.queryByText(prompt)).toBeNull(); // no guide card
}

const ORDERS = ["guide first", "original first"] as const;

describe("the text view's section-break button while the original is still loading", () => {
  it("offers nothing on a resume until the original lands and the learner reads there", async () => {
    // Codex: SectionBoundaryOffer rendered "quick check →" beside the resumed
    // passage while the manifest was pending (only the ready line was held).
    backend.checks = { u3: AUTO_CHECK };
    const pdfArrives = await resume("s4", "guide first");
    expect(screen.queryByTestId("pdf-pane")).toBeNull(); // the text view shows meanwhile
    expect(screen.getAllByText("Text of s4.").length).toBeGreaterThan(0);
    nothingOffered(AUTO_CHECK.prompt);

    await pdfArrives();
    expect(screen.getByTestId("pdf-pane")).toBeTruthy();
    nothingOffered(AUTO_CHECK.prompt);

    await readTo(2900); // the learner's own reading on the section's last page
    expect(offeredButtons().length).toBe(1);
    expect(screen.getByText("A quick check on this section is ready, just below.")).toBeTruthy();
  });
});

for (const failure of ["error", "unavailable"] as const) {
  describe(`a manifest that is ${failure === "error" ? "an error" : "unavailable"} falls back to the text view`, () => {
    for (const order of ORDERS) {
      for (const [placement, check] of [["an auto-authored", AUTO_CHECK], ["a placed", { ...AUTO_CHECK, placement: "owner_reviewed" as const, placementEventId: "pe_3", authoredQuestionId: undefined }]] as const) {
        it(`${order}: a resume never pins ${placement} check by the 70 % rule; the learner's reading offers it`, async () => {
          // Codex: the fallback judged the resumed position (the section's last
          // passage, 100 %) by the text rule and pinned the check unread; the
          // text surface also opened an auto-authored check at once.
          backend.checks = { u3: check };
          backend.pdf = failure;
          const second = await resume("s4", order);
          nothingOffered(check.prompt);
          await second();
          expect(screen.queryByTestId("pdf-pane")).toBeNull();
          nothingOffered(check.prompt);
          await settle(5_000);
          nothingOffered(check.prompt);

          await readTo(2900); // reading in the text view, the marker on s4
          expect(offeredButtons().length).toBe(1); // the section-break button under s4
          expect(screen.getAllByText(check.prompt).length).toBeGreaterThan(0); // the guide's card
        });
      }
    }
  });
}

describe("the original PDF's section-break offer", () => {
  for (const order of ORDERS) {
    it(`${order}: a resume offers neither the resumed section's check nor one left behind it`, async () => {
      // u2's check was left unanswered last time, behind the resumed u3.
      backend.checks = { u2: PLACED_CHECK, u3: AUTO_CHECK };
      const second = await resume("s4", order);
      await second();
      expect(screen.getByTestId("pdf-pane")).toBeTruthy();
      nothingOffered(AUTO_CHECK.prompt);
      expect(screen.queryByText(PLACED_CHECK.prompt)).toBeNull();

      // Reading on the section's first page: the check behind it is offered,
      // the section's own waits for its last page.
      await readTo(1500);
      expect(offeredButtons().length).toBe(1);
      expect(screen.getAllByText(PLACED_CHECK.prompt).length).toBeGreaterThan(0);
      expect(screen.queryByText(AUTO_CHECK.prompt)).toBeNull();
      await readTo(2900);
      expect(screen.getAllByText(AUTO_CHECK.prompt).length).toBeGreaterThan(0);
    });
  }

  it("a section first reached by reading in this visit follows the normal rule", async () => {
    backend.checks = { u3: AUTO_CHECK };
    const second = await resume("s2", "guide first");
    await second();
    await readTo(1500); // into u3's first page
    nothingOffered(AUTO_CHECK.prompt);
    await readTo(2900); // its last page
    expect(offeredButtons().length).toBe(1);
  });

  it("an offered check stays offered after a jump elsewhere (pinned for the visit)", async () => {
    backend.checks = { u3: AUTO_CHECK };
    const second = await resume("s4", "original first");
    await second();
    await readTo(2900);
    expect(screen.getAllByText(AUTO_CHECK.prompt).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: /Table of Contents/ }));
    await settle(SETTLED_MS);
    expect(screen.getAllByText(AUTO_CHECK.prompt).length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// Codex's verify of reading-hardening (N1): a video seek carried earlier
// watching into an unread section. Playback through the lecture set the
// learner's movement; a click on a transcript cue past 70 % of the next,
// unread section only moved the playback position, so that section's check
// was offered (and pinned) before a second of it was watched.
// ---------------------------------------------------------------------------

describe("a video seek (verify N1)", () => {
  const LECTURE_CHECK: ReaderSectionQuestionDto = { ...AUTO_CHECK, prompt: "What does the lecture open with?", authoredQuestionId: "raq_v1", spanIds: ["v1"] };
  const SUMMARY_CHECK: ReaderSectionQuestionDto = { ...AUTO_CHECK, prompt: "What does the summary conclude?", authoredQuestionId: "raq_v2", spanIds: ["v8"] };
  const CUES = ["v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9"];
  const VIDEO: SourceLibraryCard = { ...CARD, sourceId: "src_vid", canonicalUri: "https://www.youtube.com/watch?v=abcdefghijk" };

  function videoBackend() {
    const videoView: ReaderRenderViewDto = {
      ...VIEW,
      sourceId: "src_vid",
      blocks: CUES.map((spanId, index) => ({
        ...VIEW.blocks[0],
        displayNodeId: `node-${spanId}`,
        spanId,
        extractorBlockId: `t=${index * 10}-${index * 10 + 10}`,
        markdown: `Caption ${spanId}.`
      }))
    };
    const section = (id: string, label: string, spanIds: string[], question: ReaderSectionQuestionDto) => ({
      id, label, startSpanId: spanIds[0], endSpanId: spanIds[spanIds.length - 1], spanIds, question, suggestedPassages: []
    });
    // The lecture (0-40 s), then a summary (40-90 s) not watched yet.
    const videoPlan = {
      version: 1, sourceId: "src_vid", extractionId: EXTRACTION_ID, personalized: false, selectionBasis: "", goalContext: null,
      pendingDiagnosisAttemptIds: [],
      sections: [
        section("u1", "The lecture", CUES.slice(0, 4), LECTURE_CHECK),
        section("u2", "Summary", CUES.slice(4), SUMMARY_CHECK)
      ]
    };
    invoke.mockImplementation(async (command: string) => {
      if (command === "get_source_library") return { version: 1, sources: [VIDEO] };
      if (command === "reader_render_view") return videoView;
      if (command === "reader_guide_plan") return videoPlan;
      if (command === "reader_watch_plan") return { version: 1, sourceId: "src_vid", videoId: "abcdefghijk", embedUrl: "https://www.youtube-nocookie.com/embed/abcdefghijk", pausePoints: [] };
      return sidecar(command);
    });
    // jsdom has no smooth scrolling; the transcript follows playback with it.
    Element.prototype.scrollTo = vi.fn();
  }

  async function player(info: Record<string, unknown>) {
    window.dispatchEvent(new MessageEvent("message", {
      origin: "https://www.youtube-nocookie.com",
      data: JSON.stringify({ event: "infoDelivery", info })
    }));
    await settle(100);
  }

  function shown(prompt: string): boolean {
    return screen.queryAllByText(prompt).length > 0;
  }

  async function watchTheLecture() {
    videoBackend();
    render(<ReaderScreen onError={() => undefined} initialSource={{ card: VIDEO, spanId: null }} />);
    await settle(SETTLED_MS);
    fireEvent.load(document.querySelector("iframe")!);
    await settle(100);
    await player({ playerState: 1 });
    for (const seconds of [2, 12, 22, 32]) await player({ currentTime: seconds });
  }

  it("a click on a cue past 70 % of an unread section offers its check only once playback moves on there", async () => {
    await watchTheLecture();
    expect(shown(LECTURE_CHECK.prompt)).toBe(true); // earned by watching the lecture through

    // The learner clicks the summary's fourth cue (80 % of it); the player
    // lands there, still playing.
    fireEvent.click(document.querySelector('[data-transcript-span="v8"]')!);
    await settle(100);
    await player({ currentTime: 72 });
    expect(shown(SUMMARY_CHECK.prompt)).toBe(false);
    await settle(5_000);
    expect(shown(SUMMARY_CHECK.prompt)).toBe(false);

    // Watching on from there is watching the summary.
    await player({ currentTime: 82 });
    expect(shown(SUMMARY_CHECK.prompt)).toBe(true);
  });

  it("a seek keeps a check already earned", async () => {
    await watchTheLecture();
    expect(shown(LECTURE_CHECK.prompt)).toBe(true);

    fireEvent.click(document.querySelector('[data-transcript-span="v8"]')!);
    await settle(100);
    await player({ currentTime: 72 });
    await settle(5_000);

    expect(shown(LECTURE_CHECK.prompt)).toBe(true); // pinned when offered, until answered or set aside
    expect(shown(SUMMARY_CHECK.prompt)).toBe(false);
  });

  // Codex's review of the verify follow-up (F2): the player's reports are
  // messages, and one sent before the seek can arrive after the click. It
  // moved the place back to where the player had been; a landing after the
  // settle window then counted as watching from there to the clicked cue.

  it("a report from before the seek, then a landing after the settle window, is still a placement", async () => {
    await watchTheLecture();
    expect(shown(LECTURE_CHECK.prompt)).toBe(true);

    fireEvent.click(document.querySelector('[data-transcript-span="v8"]')!);
    await settle(100);
    // Sent before the click took effect: the player had played on into v5.
    await player({ currentTime: 41 });
    await settle(1_800);
    // The seek lands 2.4 s after the click, the player still playing.
    await player({ currentTime: 70.5 });
    expect(shown(SUMMARY_CHECK.prompt)).toBe(false);
    await settle(5_000);
    expect(shown(SUMMARY_CHECK.prompt)).toBe(false);

    // Playing on from where it landed is watching the summary.
    await player({ currentTime: 81 });
    expect(shown(SUMMARY_CHECK.prompt)).toBe(true);
  });

  it("a report from before the seek that arrives just after its landing is not playback", async () => {
    await watchTheLecture();

    fireEvent.click(document.querySelector('[data-transcript-span="v8"]')!);
    await settle(100);
    await player({ currentTime: 70.5 }); // lands at once
    await player({ currentTime: 41 }); // then a late report of where the player was
    await settle(1_800);
    await player({ currentTime: 73 }); // playing on inside the cue it landed on
    expect(shown(SUMMARY_CHECK.prompt)).toBe(false);
    await settle(5_000);
    expect(shown(SUMMARY_CHECK.prompt)).toBe(false);

    await player({ currentTime: 81 });
    expect(shown(SUMMARY_CHECK.prompt)).toBe(true);
  });

  it("a seek whose landing is never reported stops holding playback back", async () => {
    await watchTheLecture();

    fireEvent.click(document.querySelector('[data-transcript-span="v8"]')!);
    await settle(100);
    // The player never reports the clicked cue (the learner moved it with
    // YouTube's own controls): where it reports from is a placement ...
    await player({ currentTime: 41 });
    await settle(10_000);
    await player({ currentTime: 52 });
    expect(shown(SUMMARY_CHECK.prompt)).toBe(false);
    // ... and watching on from there is watching.
    await player({ currentTime: 62 });
    await player({ currentTime: 72 });
    expect(shown(SUMMARY_CHECK.prompt)).toBe(true);
  });
});
