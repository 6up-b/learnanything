// The reading's own path on a desk with no goal, with real bodies (spec §21.1 "reading paths: panel from RD1; then
// the path view"): the goal's path view (§12.5) needs a goal, so a book read with none keeps RW7a's per-reading path,
// shown in its window: `p` toggles it in the focused book window, its depth is asked and changed there (stored), a
// section's "read it anyway" is stored, and the exercise worth trying opens as a problem.
import { cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReadingPathDto } from "../../../api/dto";
import { setAlgoConfig } from "../../../app/algoConfig";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book } = FIXTURE_SOURCES;
const FIRST = `${book.extractionId}_s1_1`;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };
const DEPTHS = [
  { id: "get_the_idea", label: "get the idea", means: "definitions and examples" },
  { id: "learn_to_use_it", label: "learn to use it", means: "worked examples and practice" },
  { id: "fluency", label: "fluency", means: "novel problems" },
] as ReadingPathDto["depths"];
const EXERCISE = {
  label: "Exercise 3.1", extractionId: book.extractionId, spanIds: [`${book.extractionId}_s3_3`], page: null,
  statement: "Compute the weights of (1, 2, 1) at T = 1 and T = 0.5.", preview: "Compute the weights",
  importRequest: { extractionId: book.extractionId, sourceId: book.sourceId, revisionId: `rev_${book.extractionId}`, rawSelection: { extractionId: book.extractionId, nodes: [{ spanId: `${book.extractionId}_s3_3` }] } },
};
const path = { depth: null as ReadingPathDto["depth"], override: null as "read_anyway" | null };

function readingPath(): ReadingPathDto {
  if (!path.depth) return { extractionId: book.extractionId, status: "ask_depth", depth: null, depths: DEPTHS, goal: null, sections: [], next: null };
  return {
    extractionId: book.extractionId, status: "ready", depth: path.depth, depthLabel: "learn to use it", depthOrigin: "guide", depths: DEPTHS, goal: null,
    sections: [
      { sectionId: `${book.extractionId}_s3`, title: "3 Temperature", startSpanId: `${book.extractionId}_s3_h`, label: "core", chip: "core", reason: "the knob you will turn", reasonBy: "code", override: null, effectiveLabel: "core", exercise: EXERCISE, words: 200, learningObjectIds: [] },
      { sectionId: `${book.extractionId}_s4`, title: "4 Cross-entropy", startSpanId: `${book.extractionId}_s4_h`, label: "enrichment", chip: "enrichment", reason: "useful later", reasonBy: "code", override: path.override, effectiveLabel: path.override ? "core" : "enrichment", exercise: null, words: 150, learningObjectIds: [] },
    ],
    next: { text: "Next: read 3 Temperature · about 1 min of reading", sectionId: `${book.extractionId}_s3`, spanId: null, exercise: null, minutes: 1 },
  } as ReadingPathDto;
}

beforeEach(() => {
  resetSidecar();
  path.depth = null;
  path.override = null;
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_reading_path", () => readingPath());
  answers.set("reader_reading_path_set_depth", (input) => {
    path.depth = input.depth as ReadingPathDto["depth"];
    return readingPath();
  });
  answers.set("reader_reading_path_override", (input) => {
    path.override = input.choice === "read_anyway" ? "read_anyway" : null;
    return readingPath();
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

const winEl = () => document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!;

async function openBook() {
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  await waitFor(() => expect(winEl().querySelector(`[data-span-id="${FIRST}"]`)).toBeTruthy());
  return desk;
}

it("with no goal, p opens the reading's guide in the focused book window, asking its depth and storing it; esc closes it", async () => {
  await openBook();
  fireEvent.keyDown(window, { key: "p" });
  const region = await within(winEl()).findByRole("region", { name: "the reading's guide" });
  const ask = await within(region).findByRole("group", { name: "How deep do you want to go?" });
  fireEvent.click(within(ask).getByRole("button", { name: /learn to use it/ }));
  await settleDesk(0, 4);
  expect(inputsOf("reader_reading_path_set_depth")).toEqual([{ extractionId: book.extractionId, depth: "learn_to_use_it" }]);
  await waitFor(() => expect(region.querySelector(`[data-reading-path-section="${book.extractionId}_s3"]`)).not.toBeNull());
  fireEvent.keyDown(window, { key: "Escape" });
  await settleDesk(0, 2);
  expect(within(winEl()).queryByRole("region", { name: "the reading's guide" })).toBeNull();
});

it("a section's read it anyway is stored, and the exercise worth trying opens as a problem", async () => {
  path.depth = "learn_to_use_it";
  // The workbench is on (its switch), so the exercise opens as a problem.
  setAlgoConfig({ workbench: { enabled: true } } as never);
  answers.set("workbench_open", () => { throw { code: "unavailable", message: "not in this test", retryable: false }; });
  await openBook();
  fireEvent.keyDown(window, { key: "p" });
  const region = await within(winEl()).findByRole("region", { name: "the reading's guide" });
  await waitFor(() => expect(region.querySelector(`[data-reading-path-section="${book.extractionId}_s4"]`)).not.toBeNull());
  const row = region.querySelector<HTMLElement>(`[data-reading-path-section="${book.extractionId}_s4"]`)!;
  fireEvent.click(within(row).getByRole("button", { name: /why/ }));
  fireEvent.click(within(row).getByRole("button", { name: /read it anyway/ }));
  await settleDesk(0, 4);
  expect(inputsOf("reader_reading_path_override")).toEqual([expect.objectContaining({ extractionId: book.extractionId, sectionId: `${book.extractionId}_s4`, choice: "read_anyway" })]);
  fireEvent.click(within(region).getByRole("button", { name: "Try it ▸" }));
  await settleDesk(0, 6);
  // The Reader's own problem open of the exercise, from this book, on its verbatim words.
  expect(inputsOf("workbench_open")[0]).toMatchObject({ stemMd: EXERCISE.statement });
});
