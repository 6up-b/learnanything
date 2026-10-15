// The Reader Guide keeps up with the diagnoser (guide-overlay Codex review F1).
//
// Under the Slice 1 split a blind-graded error's misconception statement comes
// from the asynchronous diagnosis. While it is pending the Guide's reason
// names the error type; once it lands the Guide must name the statement, both
// in a mounted Guide and when a cached source is reopened. These tests drive
// the real ReaderScreen, the real api client (so its mutation wrappers really
// invalidate) and the real query cache over a fake sidecar.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { forwardRef } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { api } from "../api/client";
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
const SPAN_IDS = readerRenderViewFixture.blocks.map((block) => block.spanId);
const FALLBACK = "Revisit this to resolve: conceptual schema error.";
const DIAGNOSED = "Revisit this to resolve: The learner thinks V needs no transpose.";
const FOUNDATION = "This is a useful foundation before building on it.";

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

/** What the fake sidecar knows: whether an attempt has been graded, and whether its diagnosis landed. */
const backend = {
  attempted: true, diagnosisLanded: false, guidePlanCalls: 0,
  // Re-read safety: the passage was cited on the reading before a re-read and
  // its words changed there; the open reading has aliases from that one.
  moved: false, aliasedFrom: [] as string[],
  // Every other reading of the book, aliases or not (Codex review F5); null:
  // a sidecar that does not say (the field absent).
  otherReadings: null as string[] | null,
  savedPlace: null as null | { spanId: string | null; status: "current" | "needs_reanchor" | "stale" },
  // A library search's one hit, on the reading it was found on (Codex review F8).
  searchHit: null as null | { extractionId: string; spanId: string },
};

function guidePlan(): ReaderGuidePlanDto {
  const reason = !backend.attempted ? FOUNDATION : backend.diagnosisLanded ? DIAGNOSED : FALLBACK;
  return {
    version: 1,
    sourceId: SOURCE_ID,
    extractionId: EXTRACTION_ID,
    personalized: true,
    selectionBasis: "reviewed boundary placements + local learner state + active goal + source provenance",
    goalContext: null,
    pendingDiagnosisAttemptIds: backend.attempted && !backend.diagnosisLanded ? ["att_svd_1"] : [],
    sections: [
      {
        id: "u1",
        label: "Symmetric matrices",
        startSpanId: SPAN_IDS[0],
        endSpanId: SPAN_IDS[SPAN_IDS.length - 1],
        spanIds: SPAN_IDS,
        question: null,
        suggestedPassages: [
          {
            spanId: SPAN_IDS[1],
            quote: "A real symmetric matrix admits an orthonormal eigenbasis.",
            reason,
            learningObjectId: "lo_svd_compute",
            learningObjectTitle: "Compute an SVD",
            learnerSignal: backend.attempted ? "recent_misunderstanding" : "new_material",
            anchor: backend.moved ? "needs_reanchor" : "current"
          }
        ]
      }
    ]
  } as ReaderGuidePlanDto;
}

function sidecar(command: string): unknown {
  switch (command) {
    case "reader_prompt_contract":
      return {
        version: "1",
        context: "reader",
        readerEnabled: true,
        notSocraticByDefault: true,
        defaultAnswerMode: "answer_directly",
        answerModes: ["answer_directly"],
        mayReveal: [],
        manifestIncludes: [],
        manifestNeverIncludes: [],
        citations: "",
        exposureOnCommit: ""
      };
    case "get_source_library":
      return { version: 1, sources: [CARD] };
    case "reader_render_view":
      return {
        ...readerRenderViewFixture, aliasedFrom: backend.aliasedFrom,
        ...(backend.otherReadings ? { otherReadings: backend.otherReadings } : {})
      };
    case "reader_search_sources":
      return {
        version: 1, query: "eigen", searchedSources: 1,
        hits: backend.searchHit ? [{
          sourceId: SOURCE_ID, sourceTitle: CARD.title, section: null, page: null, snippet: "the eigenbasis hit",
          ...backend.searchHit
        }] : []
      };
    case "reader_saved_place":
      return {
        version: 1, sourceId: SOURCE_ID, fromExtractionId: "ext_before", fromSpanId: "s_before",
        extractionId: EXTRACTION_ID, matchKind: null, ...backend.savedPlace
      };
    case "reader_guide_plan":
      backend.guidePlanCalls += 1;
      return guidePlan();
    case "reader_get_progress":
      // The section was revealed earlier, so its "Worth a second look" passages show.
      return {
        version: 1,
        extractionId: EXTRACTION_ID,
        sections: [{
          extractionId: EXTRACTION_ID,
          sectionId: "u1",
          spansSeen: SPAN_IDS.length,
          spanCount: SPAN_IDS.length,
          revealedAt: "2026-10-12T09:00:00Z",
          completedAt: null,
          generationBatchId: null
        }]
      };
    case "reader_pdf_view":
      return { version: 1, available: false, fileName: null, extractionId: EXTRACTION_ID, sourceId: SOURCE_ID, revisionId: null, blocks: [] };
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
    case "submit_attempt":
      backend.attempted = true;
      return { version: 1, attemptId: "att_svd_1" };
    default:
      throw { code: "not_mocked", message: `${command} is not mocked`, retryable: false };
  }
}

beforeEach(() => {
  vi.useFakeTimers();
  clear();
  backend.attempted = true;
  backend.diagnosisLanded = false;
  backend.guidePlanCalls = 0;
  backend.moved = false;
  backend.aliasedFrom = [];
  backend.otherReadings = null;
  backend.savedPlace = null;
  backend.searchHit = null;
  vi.stubGlobal("localStorage", memoryStorage());
  invoke.mockReset().mockImplementation(async (command: string) => sidecar(command));
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

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
    setItem: (key: string, value: string) => void values.set(key, String(value)),
  };
}

/** Let the open sequence's chained reads settle without moving the clock far. */
async function settle(ms = 0) {
  for (let i = 0; i < 6; i += 1) {
    await act(async () => {
      await vi.advanceTimersByTimeAsync(i === 0 ? ms : 0);
    });
  }
}

function openReader() {
  return render(<ReaderScreen onError={() => undefined} initialSource={{ card: CARD, spanId: null }} />);
}

it("a mounted Guide names the diagnoser's statement once the pending diagnosis lands", async () => {
  openReader();
  await settle();
  expect(screen.getByText(FALLBACK)).toBeTruthy();

  backend.diagnosisLanded = true;
  await settle(30_000);
  expect(screen.queryByText(FALLBACK)).toBeNull();
  expect(screen.getByText(DIAGNOSED)).toBeTruthy();

  // Nothing is pending any more: the Guide stops asking.
  const calls = backend.guidePlanCalls;
  await settle(300_000);
  expect(backend.guidePlanCalls).toBe(calls);
});

// Every open of a real source also drains the capture outbox, a Reader
// mutation that marks every per-source read stale; so a reopen re-reads the
// plan even without the Guide's own rules. These two pin the end-to-end
// behaviour; guidePlan.test.tsx pins the Guide's own rules without the drain.
it("reopening a cached source re-reads a Guide plan that was waiting on a diagnosis", async () => {
  const first = openReader();
  await settle();
  expect(screen.getByText(FALLBACK)).toBeTruthy();
  expect(backend.guidePlanCalls).toBe(1);
  first.unmount();

  // The diagnosis lands while the Reader is closed; the learner returns well
  // inside the Reader's ten-minute cache window.
  backend.diagnosisLanded = true;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1_000);
  });
  openReader();
  await settle();
  expect(backend.guidePlanCalls).toBe(2);
  expect(screen.getByText(DIAGNOSED)).toBeTruthy();
});

it("an attempt submitted elsewhere invalidates the cached Guide plan", async () => {
  backend.attempted = false;
  const first = openReader();
  await settle();
  expect(screen.getByText(FOUNDATION)).toBeTruthy();
  first.unmount();

  // The learner practises on another screen; the blind grade localizes an error.
  await act(async () => {
    await api.submitAttempt({} as Parameters<typeof api.submitAttempt>[0]);
  });
  openReader();
  await settle();
  expect(backend.guidePlanCalls).toBe(2);
  expect(screen.getByText(FALLBACK)).toBeTruthy();
});

// -- Re-read safety (docs/reviews/reread-safety.md) ------------------------------

it("a passage cited before the book was read again shows flagged where its words changed", async () => {
  backend.moved = true;
  openReader();
  await settle();
  expect(screen.getByText("reworded since you read it")).toBeTruthy();
  expect(screen.getByText("“A real symmetric matrix admits an orthonormal eigenbasis.”")).toBeTruthy();
});

it("a place saved on the reading before a re-read is translated, and an approximate one says so", async () => {
  backend.aliasedFrom = ["ext_before"];
  backend.savedPlace = { spanId: SPAN_IDS[2], status: "needs_reanchor" };
  window.localStorage.setItem(`learnloop.reader.position.${SOURCE_ID}`, JSON.stringify({ extractionId: "ext_before", spanId: "s_before" }));
  openReader();
  await settle();
  const asked = invoke.mock.calls.filter(([command]) => command === "reader_saved_place");
  expect(asked).toHaveLength(1);
  expect(asked[0][1]).toEqual({ input: { sourceId: SOURCE_ID, spanId: "s_before", extractionId: "ext_before" } });
  expect(screen.getByText("This book was read again: you're near where you left off.")).toBeTruthy();
});

it("a place saved on the open reading is used as it is, with no translation", async () => {
  backend.aliasedFrom = ["ext_before"];
  window.localStorage.setItem(`learnloop.reader.position.${SOURCE_ID}`, JSON.stringify({ extractionId: EXTRACTION_ID, spanId: SPAN_IDS[2] }));
  openReader();
  await settle();
  expect(invoke.mock.calls.some(([command]) => command === "reader_saved_place")).toBe(false);
  expect(screen.queryByText("This book was read again: you're near where you left off.")).toBeNull();
});

it("a bare place from before places recorded their reading is translated once the book was read again", async () => {
  backend.aliasedFrom = ["ext_before"];
  backend.savedPlace = { spanId: null, status: "stale" };
  window.localStorage.setItem(`learnloop.reader.position.${SOURCE_ID}`, "s_before");
  openReader();
  await settle();
  const asked = invoke.mock.calls.filter(([command]) => command === "reader_saved_place");
  expect(asked[0][1]).toEqual({ input: { sourceId: SOURCE_ID, spanId: "s_before", extractionId: null } });
  expect(screen.queryByText("This book was read again: you're near where you left off.")).toBeNull();
});

// -- Codex review of re-read safety (2026-10-14) ----------------------------------

it("F5: a bare place on a book read again with no alias recorded asks the sidecar, never takes it as is", async () => {
  // A re-read made before aliases were recorded (or one that matched
  // nothing): no aliases into the open reading, but the book has another reading.
  backend.aliasedFrom = [];
  backend.otherReadings = ["ext_before"];
  backend.savedPlace = { spanId: null, status: "stale" };
  window.localStorage.setItem(`learnloop.reader.position.${SOURCE_ID}`, SPAN_IDS[2] as string);
  openReader();
  await settle();
  const asked = invoke.mock.calls.filter(([command]) => command === "reader_saved_place");
  expect(asked).toHaveLength(1);
  expect(asked[0][1]).toEqual({ input: { sourceId: SOURCE_ID, spanId: SPAN_IDS[2], extractionId: null } });
});

it("F5: a bare place on a book never read again is used as it is", async () => {
  backend.otherReadings = [];
  window.localStorage.setItem(`learnloop.reader.position.${SOURCE_ID}`, SPAN_IDS[2] as string);
  openReader();
  await settle();
  expect(invoke.mock.calls.some(([command]) => command === "reader_saved_place")).toBe(false);
});

async function searchAndOpenHit() {
  render(<ReaderScreen onError={() => undefined} />);
  await settle();
  fireEvent.change(screen.getByPlaceholderText("search all sources…"), { target: { value: "eigen" } });
  await settle(400);
  fireEvent.click(screen.getByText("the eigenbasis hit"));
  await settle();
}

it("F8: a search hit found on a reading the book was read again since is translated, not opened as is", async () => {
  backend.otherReadings = ["ext_before"];
  backend.searchHit = { extractionId: "ext_before", spanId: "s_before" };
  backend.savedPlace = { spanId: SPAN_IDS[2], status: "needs_reanchor" };
  await searchAndOpenHit();
  const asked = invoke.mock.calls.filter(([command]) => command === "reader_saved_place");
  expect(asked).toHaveLength(1);
  expect(asked[0][1]).toEqual({ input: { sourceId: SOURCE_ID, spanId: "s_before", extractionId: "ext_before" } });
  expect(screen.getByText("This book was read again: you're near the passage you found.")).toBeTruthy();
});

it("F8: a search hit on the reading the book opens on lands there with no translation", async () => {
  backend.otherReadings = ["ext_before"];
  backend.searchHit = { extractionId: EXTRACTION_ID, spanId: SPAN_IDS[2] as string };
  await searchAndOpenHit();
  expect(invoke.mock.calls.some(([command]) => command === "reader_saved_place")).toBe(false);
});
