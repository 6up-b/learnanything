// The Guide on a desk with no Guide panel, with real bodies (spec §21.1 "Guide rail: then margin marks, the band and
// path, callouts"): what has no margin or band home (the section's card with how far through it the learner is and
// what to do near its break, finding the section in other books, the contents, a deliverable's slice for the book)
// is the reading's guide, opened in the window with p on a desk with no goal, the Guide's own component.
import { cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book } = FIXTURE_SOURCES;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };
const DEPTHS = [{ id: "learn_to_use_it" as const, label: "learn to use it", means: "worked examples and practice" }];

function slice() {
  const section = { extractionId: book.extractionId, sectionId: `${book.extractionId}_s3`, title: "3 Temperature", book: "Softmax, a short book", sourceId: book.sourceId,
    startSpanId: `${book.extractionId}_s3_h`, minutes: 3, treatment: "develops", treatmentWords: "develops it", read: false };
  return {
    extractionId: book.extractionId, status: "ready", goal: { id: "goal_d", title: "my midterm", kind: "exam", dueAt: "2026-12-12T23:59:59Z" },
    depth: "learn_to_use_it", depthLabel: "learn to use it", depths: DEPTHS,
    lines: [{ learningObjectId: "lo_t", title: "Temperature", phrase: "temperature", kind: "needed", label: "core", chip: "core", effectiveLabel: "core",
      reason: "the knob your exam asks about", reasonBy: "code", override: null, section, alternates: [], exercise: null, check: null, ordinal: 0 }],
    elsewhere: [], notNeeded: [], notNeededLabel: "not needed for my midterm", uncovered: [], message: null, reason: null, covering: false,
  };
}

beforeEach(() => {
  resetSidecar();
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_prompt_contract", () => ({
    version: "fixture", context: "reader", readerEnabled: true, notSocraticByDefault: true, defaultAnswerMode: "answer_directly",
    answerModes: ["answer_directly"], mayReveal: [], manifestIncludes: [], manifestNeverIncludes: [], citations: "spans", exposureOnCommit: "none",
    inquiryEnabled: true, readingPaths: { enabled: true, depths: [] },
    correspondence: { enabled: true, findSection: true, alsoInBooks: false },
  }));
  answers.set("reader_correspondents", () => ({ status: "none", learningObjects: [], search: null }));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const winEl = () => document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!;

async function openGuide() {
  mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never]]) });
  await settleDesk(0, 20);
  await waitFor(() => expect(winEl().querySelector(`[data-span-id="${book.extractionId}_s1_1"]`)).toBeTruthy());
  fireEvent.keyDown(window, { key: "p" });
  return within(winEl()).findByRole("region", { name: "the reading's guide" });
}

it("the reading's guide holds the section's card, how far through it, what to do near its break, the contents and finding it elsewhere", async () => {
  const guide = await openGuide();
  // The section in view, and how far through it.
  expect(within(guide).getByRole("progressbar", { name: "Position through this section" })).toBeTruthy();
  expect(within(guide).getByTestId("section-position").textContent).toMatch(/% through this section/);
  // Where questions come from, as the Guide says it.
  expect(within(guide).getByTestId("guide-questions-from")).toBeTruthy();
  // The contents: each section, a press away.
  expect(guide.textContent).toContain("Why the exponential");
  // Finding this section in my other books.
  const find = guide.querySelector<HTMLElement>("[data-find-section]")!;
  fireEvent.click(within(find).getByRole("button"));
  await settleDesk(0, 4);
  expect(inputsOf("reader_correspondents")[0]).toMatchObject({ extractionId: book.extractionId, sectionId: expect.any(String) });
});

it("a deliverable's slice for the book takes the path card's place in the reading's guide", async () => {
  answers.set("curriculum_guide_slice", () => slice());
  const guide = await openGuide();
  await waitFor(() => expect(guide.querySelector("[data-deliverable-slice]") ?? guide.querySelector("[data-deliverable-line]")).not.toBeNull());
  expect(guide.textContent).toContain("my midterm");
  expect(guide.textContent).toContain("Temperature");
  expect(inputsOf("curriculum_guide_slice")[0]).toMatchObject({ extractionId: book.extractionId });
});
