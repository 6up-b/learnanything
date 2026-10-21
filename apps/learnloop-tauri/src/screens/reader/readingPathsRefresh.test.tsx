// RW7a (Codex re-review F3): the mounted reading-path card reads the path
// again once the Reader's progress save has landed, not only on a timer
// raced against it. The Reader's own progress hook drives the card here, the
// refresh key built as ReaderScreen builds it, against a fake server whose
// "next" moves only with the progress it was sent.
import { act, cleanup, render, screen } from "@testing-library/react";
import { createRef, useState } from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderGuidePlanDto, ReaderGuideSectionDto, ReaderRenderViewDto, ReadingPathDto } from "../../api/dto";
import { readerRenderViewFixture } from "../../fixtures/readerRenderView";
import { resetReaderActivityForTests } from "./activity";
import { ReadingPathCard } from "./ReadingPathCard";
import { readingPathRefreshKey } from "./readingPath";
import { useReadingProgress, type ReadingProgressInput } from "./useReadingProgress";

const api = vi.hoisted(() => ({
  readerLogActivity: vi.fn(), readerNoteReadingProgress: vi.fn(), readerAuthorSectionQuestion: vi.fn(),
  readerGuidePlan: vi.fn(), readerMarkSectionProgress: vi.fn(), readerSavedPlace: vi.fn(),
  readerReadingPath: vi.fn(), readerReadingPathSetDepth: vi.fn(), readerReadingPathOverride: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("./readerCache", () => ({ cachedSourceRead: (_id: string, _key: unknown, fetch: () => unknown) => fetch() }));
vi.mock("./guidePlan", () => ({ useGuideDiagnosisRefresh: () => undefined }));

// Section A is s0-s1, section B s2-s4.
const SPANS = ["s0", "s1", "s2", "s3", "s4"];
const view: ReaderRenderViewDto = {
  ...readerRenderViewFixture,
  blocks: SPANS.map((spanId) => ({ ...readerRenderViewFixture.blocks[1], spanId, displayNodeId: `node-${spanId}`, markdown: `Passage ${spanId}.` })),
};

function section(id: string, spanIds: string[]): ReaderGuideSectionDto {
  return {
    id, label: `Section ${id}`, startSpanId: spanIds[0], endSpanId: spanIds[spanIds.length - 1], spanIds,
    question: null, suggestedPassages: [],
  } as unknown as ReaderGuideSectionDto;
}

const PLAN: ReaderGuidePlanDto = {
  version: 1, sourceId: view.sourceId, extractionId: view.extractionId, personalized: true, selectionBasis: "",
  goalContext: null, sections: [section("A", SPANS.slice(0, 2)), section("B", SPANS.slice(2))],
} as unknown as ReaderGuidePlanDto;

// What the server has saved, and the path it answers from it: "next" is the
// first section not read through.
let saved: Record<string, number> = {};
function serverPath(): ReadingPathDto {
  const next = (saved.A ?? 0) >= 2 ? "B" : "A";
  return {
    extractionId: view.extractionId, status: "ready", depth: "learn_to_use_it", depthLabel: "learn to use it", depthOrigin: "guide",
    intent: null, depths: [], goal: null, goalLine: null, sections: [],
    next: { text: `Next: read Section ${next}`, sectionId: next, spanId: null, exercise: null, minutes: 1 },
  } as unknown as ReadingPathDto;
}

function Harness() {
  const [activeSpan, setActiveSpan] = useState<string | null>(null);
  const input: ReadingProgressInput = {
    render: view, offline: false, blocks: view.blocks, guidePlan: PLAN, setGuidePlan: vi.fn(), guideLoading: false,
    pdfView: null, pdfViewPending: false, surface: "text", watch: null, watchLoading: false, mode: "anchor",
    inquiry: true, muted: false, activeSpan, setActiveSpan, bodyRef: createRef<HTMLDivElement>(),
    railRef: createRef<HTMLDivElement>(), paneRef: createRef(), watchRef: createRef(), noteProactive: () => true,
    showGuideRail: () => undefined,
  };
  const progress = useReadingProgress(input);
  harness.progress = progress;
  // As ReaderScreen builds it (the other signals do not move here).
  const refreshKey = readingPathRefreshKey({
    sections: PLAN.sections, completedSections: progress.completedSections, sectionSeen: progress.sectionSeen,
    progressSaves: progress.progressSaves, signals: [],
  });
  return <ReadingPathCard extractionId={view.extractionId} onJump={() => undefined} onTryExercise={null} onError={() => undefined} refreshKey={refreshKey} />;
}
const harness: { progress: ReturnType<typeof useReadingProgress> | null } = { progress: null };

async function advance(ms: number): Promise<void> {
  await act(async () => { await vi.advanceTimersByTimeAsync(ms); });
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "requestAnimationFrame", "cancelAnimationFrame", "Date"] });
  resetReaderActivityForTests();
  for (const fn of Object.values(api)) fn.mockReset();
  saved = {};
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerNoteReadingProgress.mockImplementation(async ({ sectionId, spansSeen }: { sectionId: string; spansSeen: number }) => {
    saved[sectionId] = Math.max(saved[sectionId] ?? 0, spansSeen);
    return {};
  });
  api.readerReadingPath.mockImplementation(async () => serverPath());
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  harness.progress = null;
});

/** Open at A, the learner's own scroll starting the reading. */
async function startReading(): Promise<void> {
  render(<Harness />);
  await advance(0);
  expect(screen.getByText("Next: read Section A")).toBeTruthy();
  act(() => harness.progress!.placeAtOpen(view.sourceId, SPANS[0], null));
  await advance(2000);
  await act(async () => {
    harness.progress!.noteUserScroll();
    harness.progress!.onReadingScroll();
    await vi.advanceTimersByTimeAsync(20);
  });
  expect(harness.progress!.readingMoved).toBe(true);
  // Let the first passage's own save and any read it prompts settle.
  await advance(10_000);
  expect(screen.getByText("Next: read Section A")).toBeTruthy();
}

it("reading on into B before A's save lands still advances the path once the save lands", async () => {
  await startReading();
  // A read through at 0 ms: the card's refresh is due at 2,000 ms.
  act(() => harness.progress!.setReadingSpan(SPANS[1]));
  expect(harness.progress!.sectionSeen.A).toBe(2);
  await advance(1000);
  // Partial reading in B at 1,000 ms postpones the save to 2,500 ms.
  act(() => harness.progress!.setReadingSpan(SPANS[2]));
  expect(harness.progress!.sectionSeen.B).toBe(1);
  await advance(1100);
  // The timed refresh read the server before the save: still A.
  expect(saved.A ?? 0).toBeLessThan(2);
  expect(screen.getByText("Next: read Section A")).toBeTruthy();
  await advance(500);
  expect(saved.A).toBe(2);
  // The landed save reads the path again; no further reading needed.
  await advance(5000);
  expect(screen.getByText("Next: read Section B")).toBeTruthy();
  expect(screen.queryByText("Next: read Section A")).toBeNull();
});

it("a progress save that lands on its retry also advances the path", async () => {
  await startReading();
  let failures = 1;
  const succeed = api.readerNoteReadingProgress.getMockImplementation()!;
  api.readerNoteReadingProgress.mockImplementation(async (params: { sectionId: string; spansSeen: number }) => {
    if (failures > 0) {
      failures -= 1;
      throw new Error("database is locked");
    }
    return succeed(params);
  });
  act(() => harness.progress!.setReadingSpan(SPANS[1]));
  await advance(1600);
  expect(saved.A ?? 0).toBeLessThan(2); // the save failed; its retry is timed
  await advance(5000);
  expect(saved.A).toBe(2);
  await advance(5000);
  expect(screen.getByText("Next: read Section B")).toBeTruthy();
});
