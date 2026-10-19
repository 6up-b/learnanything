// Adaptive difficulty AD2+AD3 (spec §5.12, §12; Codex review F6) on the real screen: a section
// with two quick checks. The Reader tells the dose arm which check the section already shows,
// so the draw's extra is the other one; "yes" shows that exact question (never the section's
// ordinary check again), and answering it answers the delivered question, whose reading
// opportunity names the offer (the sidecar side: tests/test_ad23_fix_review.py).
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderGuidePlanDto, ReaderRenderViewDto, ReaderSectionQuestionDto, SourceLibraryCard } from "../api/dto";
import { clear } from "../api/queryCache";
import { ReaderScreen } from "./ReaderScreen";

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn() }));
vi.mock("@tauri-apps/api/core", () => ({ invoke, convertFileSrc: (path: string) => path }));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => <div data-testid="pdf-pane" /> }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

const SOURCE_ID = "src_dose";
const EXTRACTION_ID = "ext_dose";
const SPANS = ["s1", "s2", "s3"];

const VIEW: ReaderRenderViewDto = {
  renderViewId: "rv_dose", extractionId: EXTRACTION_ID, revisionId: "rev_dose", sourceId: SOURCE_ID,
  renderer: "marker_markdown", rendererVersion: "1", contentHash: "sha256:dose", status: "ready", layers: {},
  blocks: SPANS.map((spanId) => ({
    displayNodeId: `node-${spanId}`, spanId, blockType: "Text", markdown: `Text of ${spanId}.`, sanitized: false,
    katexNodes: [], assets: [], health: { status: "ok", recommendedView: "derived", reasonFlags: [] }
  }))
};

const CARD: SourceLibraryCard = {
  sourceId: SOURCE_ID, title: "A book", acquisitionKind: "pdf", canonicalUri: null, workId: null,
  currentRevisionId: "rev_dose", revisionCount: 1, readiness: "ready", unitCount: 2, blockCount: SPANS.length,
  extractionStatus: "completed", suggestedRole: null, readerEnabled: true, updateAvailable: false
};

const ORDINARY: ReaderSectionQuestionDto = {
  practiceItemId: null, learningObjectId: null, learningObjectTitle: null, prompt: "The ordinary check?",
  reason: "Written from this section's text.", learnerSignal: "auto_authored", goalId: null, goalTitle: null,
  goldenPathRunId: null, targetContractVersionId: null, readingPhase: "after_section", pattern: null,
  placementEventId: null, blueprintVersionId: null, placement: "auto_authored", authoredQuestionId: "raq_ordinary",
  expectedAnswer: "The ordinary answer.", spanIds: ["s1"], escalationLearningObjectId: null
};

function plan(): ReaderGuidePlanDto {
  return {
    version: 1, sourceId: SOURCE_ID, extractionId: EXTRACTION_ID, personalized: false, selectionBasis: "",
    goalContext: null, pendingDiagnosisAttemptIds: [],
    sections: [
      { id: "u1", label: "One", startSpanId: "s1", endSpanId: "s2", spanIds: ["s1", "s2"], question: ORDINARY,
        suggestedPassages: [] },
      { id: "u2", label: "Two", startSpanId: "s3", endSpanId: "s3", spanIds: ["s3"], question: null,
        suggestedPassages: [] }
    ]
  } as ReaderGuidePlanDto;
}

function sidecar(command: string, args: any): unknown {
  switch (command) {
    case "reader_prompt_contract":
      return {
        version: "1", context: "reader", readerEnabled: true, inquiryEnabled: true, notSocraticByDefault: true,
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
      // Section u1 was completed: its boundary is the dose arm's decision point.
      return { version: 1, extractionId: EXTRACTION_ID, sections: [{
        extractionId: EXTRACTION_ID, sectionId: "u1", spansSeen: 2, spanCount: 2, revealedAt: null,
        completedAt: "2026-10-18T10:00:00Z", generationBatchId: null }] };
    case "reader_pdf_view":
      return { version: 1, available: false, reason: "no_original" };
    case "reader_dose_offer": {
      // The sidecar's rule: the check on show is never the extra.
      const showing = args?.input?.showingQuestionId ?? null;
      const chosen = showing === "raq_ordinary" ? "raq_extra" : "raq_ordinary";
      return { version: 1, eligible: true, reason: null, drawId: "d1", offer: {
        drawId: "d1", variant: "extra_question", text: "One more quick question on this?",
        why: "Offered at random, to learn how much of this helps you",
        content: { questionId: chosen, style: "recall" },
        question: { questionId: chosen, sectionId: "u1",
          prompt: chosen === "raq_extra" ? "The extra question?" : ORDINARY.prompt,
          expectedAnswer: chosen === "raq_extra" ? "The extra answer." : "The ordinary answer.", spanIds: ["s2"] } } };
    }
    case "reader_dose_offer_event":
      return { version: 1, rowId: "r1", event: args?.input?.event };
    case "reader_mark_section_progress":
      return { version: 1, progress: {}, enqueuedGeneration: false, batchId: null };
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

beforeEach(() => {
  vi.useFakeTimers({
    toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "Date", "requestAnimationFrame", "cancelAnimationFrame"]
  });
  clear();
  vi.stubGlobal("localStorage", memoryStorage());
  Element.prototype.scrollIntoView = vi.fn();
  invoke.mockReset().mockImplementation(async (command: string, args: unknown) => sidecar(command, args));
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

function calls(command: string): any[] {
  return invoke.mock.calls.filter(([name]) => name === command).map(([, args]) => (args as any)?.input);
}

it("offers the section's other question and shows exactly that one when taken", async () => {
  render(<ReaderScreen onError={() => undefined} initialSource={{ card: CARD, spanId: null }} />);
  await settle(2_000);
  const draws = calls("reader_dose_offer");
  expect(draws.length).toBe(1);
  expect(draws[0]).toMatchObject({ extractionId: EXTRACTION_ID, sectionId: "u1", showingQuestionId: "raq_ordinary" });
  expect(screen.getByTestId("dose-offer").textContent).toContain("One more quick question");
  expect(calls("reader_dose_offer_event")).toEqual([{ drawId: "d1", event: "delivered" }]);

  fireEvent.click(screen.getByRole("button", { name: "yes" }));
  await settle();
  const uptake = calls("reader_dose_offer_event");
  expect(uptake[uptake.length - 1]).toEqual({ drawId: "d1", event: "taken" });
  const extra = screen.getByTestId("dose-extra-question");
  expect(extra.textContent).toContain("The extra question?");
  expect(extra.textContent).not.toContain("The ordinary check?");

  fireEvent.change(extra.querySelector("textarea")!, { target: { value: "my answer" } });
  fireEvent.click(screen.getByRole("button", { name: /compare with the source/ }));
  await settle();
  // The delivered question is the one answered (its opportunity names the offer, sidecar side).
  expect(calls("reader_authored_question_action")).toEqual([
    { questionId: "raq_extra", action: "answered", response: "my answer" }
  ]);
});
