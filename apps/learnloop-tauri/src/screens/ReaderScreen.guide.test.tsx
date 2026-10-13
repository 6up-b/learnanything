// The Reader Guide keeps up with the diagnoser (guide-overlay Codex review F1).
//
// Under the Slice 1 split a blind-graded error's misconception statement comes
// from the asynchronous diagnosis. While it is pending the Guide's reason
// names the error type; once it lands the Guide must name the statement, both
// in a mounted Guide and when a cached source is reopened. These tests drive
// the real ReaderScreen, the real api client (so its mutation wrappers really
// invalidate) and the real query cache over a fake sidecar.
import { act, cleanup, render, screen } from "@testing-library/react";
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
const backend = { attempted: true, diagnosisLanded: false, guidePlanCalls: 0 };

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
            learnerSignal: backend.attempted ? "recent_misunderstanding" : "new_material"
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
      return readerRenderViewFixture;
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
  invoke.mockReset().mockImplementation(async (command: string) => sidecar(command));
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

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
