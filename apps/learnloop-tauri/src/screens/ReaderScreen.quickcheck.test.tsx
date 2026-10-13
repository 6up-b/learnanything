// UX Phase 1, item 1.10 (docs/specs/ux_learnloop_v1.md §10): when writing a
// section's quick check takes too long, the Reader says so with one action
// instead of the "writing a quick check…" line silently disappearing.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { forwardRef } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderGuidePlanDto, SourceLibraryCard } from "../api/dto";
import { clear } from "../api/queryCache";
import { readerRenderViewFixture } from "../fixtures/readerRenderView";
import { ReaderScreen } from "./ReaderScreen";

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn() }));
vi.mock("@tauri-apps/api/core", () => ({ invoke, convertFileSrc: (path: string) => path }));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: forwardRef(() => null) }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

const SOURCE_ID = readerRenderViewFixture.sourceId;
const EXTRACTION_ID = readerRenderViewFixture.extractionId;
const SPAN_IDS = readerRenderViewFixture.blocks.map((block) => block.spanId as string);

const CARD: SourceLibraryCard = {
  sourceId: SOURCE_ID,
  title: "Symmetric matrices",
  acquisitionKind: "pdf",
  canonicalUri: null,
  workId: null,
  currentRevisionId: readerRenderViewFixture.revisionId,
  revisionCount: 1,
  readiness: "ready",
  unitCount: 1,
  blockCount: SPAN_IDS.length,
  extractionStatus: "completed",
  suggestedRole: null,
  readerEnabled: true,
  updateAvailable: false
};

const plan: ReaderGuidePlanDto = {
  version: 1,
  sourceId: SOURCE_ID,
  extractionId: EXTRACTION_ID,
  personalized: false,
  selectionBasis: "",
  goalContext: null,
  pendingDiagnosisAttemptIds: [],
  sections: [
    {
      id: "u1",
      label: "Symmetric matrices",
      startSpanId: SPAN_IDS[0],
      endSpanId: SPAN_IDS[SPAN_IDS.length - 1],
      spanIds: SPAN_IDS,
      question: null,
      suggestedPassages: []
    }
  ]
} as ReaderGuidePlanDto;

const backend = { authorCalls: 0 };

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
      return readerRenderViewFixture;
    case "reader_guide_plan":
      return plan;
    case "reader_get_progress":
      return { version: 1, extractionId: EXTRACTION_ID, sections: [] };
    case "reader_pdf_view":
      return { version: 1, available: false, fileName: null, extractionId: EXTRACTION_ID, sourceId: SOURCE_ID, revisionId: null, blocks: [] };
    case "reader_author_section_question":
      backend.authorCalls += 1;
      return { version: 1, status: "queued", batchId: "b1", question: null };
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
    case "reader_mark_section_progress":
      return { version: 1, progress: {}, enqueuedGeneration: false, batchId: null };
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

beforeEach(() => {
  vi.useFakeTimers();
  clear();
  backend.authorCalls = 0;
  vi.stubGlobal("localStorage", memoryStorage());
  // jsdom has no layout: the Reader scrolls the resumed passage into view.
  Element.prototype.scrollIntoView = vi.fn();
  // The learner left off at the end of the section, so its check is due.
  window.localStorage.setItem(`learnloop.reader.position.${SOURCE_ID}`, SPAN_IDS[SPAN_IDS.length - 1]);
  invoke.mockReset().mockImplementation(async (command: string) => sidecar(command));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

async function settle(ms = 0) {
  for (let i = 0; i < 6; i += 1) {
    await act(async () => {
      await vi.advanceTimersByTimeAsync(i === 0 ? ms : 0);
    });
  }
}

function rect(top: number, height: number): DOMRect {
  return { top, bottom: top + height, height, width: 600, left: 0, right: 600, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
}

/** The learner reads on at the end of the section: their own wheel moves the
 * page, and the section's last passage sits at the reading marker (usability
 * round 2: only the learner's own scrolling is reading, never the resume). */
async function readOnAtTheSectionEnd() {
  const last = SPAN_IDS[SPAN_IDS.length - 1];
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
    const span = (this as HTMLElement).dataset?.spanId;
    if (span === last) return rect(650, 100);
    if (span) return rect(-400, 100);
    return rect(0, 1000);
  });
  await settle(2_000);
  const body = document.querySelector(`[data-span-id="${last}"]`)!.closest(".ll-scroll")!;
  fireEvent.wheel(body, { deltaY: 120 });
  fireEvent.scroll(body);
  await settle(50);
}

it("asks for no check on the passage a book reopens at until the learner reads on", async () => {
  render(<ReaderScreen onError={() => undefined} initialSource={{ card: CARD, spanId: null }} />);
  await settle(2_000);
  expect(backend.authorCalls).toBe(0);

  await readOnAtTheSectionEnd();
  expect(backend.authorCalls).toBe(1);
});

it("says when a section's check could not be written, and offers to try again", async () => {
  render(<ReaderScreen onError={() => undefined} initialSource={{ card: CARD, spanId: null }} />);
  await settle();
  await readOnAtTheSectionEnd();
  expect(backend.authorCalls).toBe(1);
  expect(screen.getByText(/writing a quick check for this section/)).toBeTruthy();

  await settle(4_000 * 50);

  expect(screen.queryByText(/writing a quick check for this section/)).toBeNull();
  expect(screen.getByText(/Couldn't write a check for this section/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  await settle();
  expect(backend.authorCalls).toBe(2);
  expect(screen.getByText(/writing a quick check for this section/)).toBeTruthy();
});
