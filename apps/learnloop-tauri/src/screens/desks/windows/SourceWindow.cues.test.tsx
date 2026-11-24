// Margin cues in source windows on a desk, with their real bodies (spec §7.1; §21.1 "margin marks in source windows;
// keys unchanged"): two book windows, each with its own marks; Alt+↓ / Alt+↑ move between the marks of the active
// window only; the popover's actions run there, and what they change (not relevant, fewer marks, off for the book)
// can be undone in the window itself, with the density control at the foot of its reading, since a desk shows no
// Guide rail unless a panel is opened for it.
import { act, cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderCueDto, ReaderGuidePlanDto } from "../../../api/dto";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_GUIDES, FIXTURE_SOURCES, FIXTURE_VIEWS } from "../../../fixtures/desks/sources";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book, paper } = FIXTURE_SOURCES;
const windowOf = (windowId: string, source: { sourceId: string; extractionId: string }) => ({
  windowId, pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: source.sourceId, extractionId: source.extractionId, view: "render" },
});

function cue(extractionId: string, spanId: string, rank: number): ReaderCueDto {
  const note = "Connects to something you worked on: Softmax weights.";
  const because = "Because: your answer on 2 Oct · from the Guide's citations";
  return {
    cueId: `cue_${spanId}`, kind: "revisit", spanId, sectionId: `${extractionId}_s1`, learningObjectId: "lo_softmax",
    learningObjectTitle: "Softmax weights", targetId: "err_1", rank, sectionRank: rank, note, because,
    label: `Note on this paragraph: ${note} ${because}`,
    earlier: {
      attemptId: "att_1", practiceItemId: "pi_softmax", prompt: "Do the weights add up to one?", answer: "Only the biggest one counts.",
      answeredAt: "2026-10-02T09:00:00Z", answeredOn: "2 Oct", statement: "The learner reads softmax as a hard maximum.", statementPending: false,
    },
  };
}

const state = { density: "normal" as "off" | "fewer" | "normal" | "more", sourceOff: new Set<string>(), hidden: new Set<string>() };

/** The fixture's Guide for a reading, with two misunderstanding passages carrying marks (a screenful apart). */
function guideWithCues(extractionId: string): ReaderGuidePlanDto {
  const base = FIXTURE_GUIDES[extractionId];
  const spans = base.sections.flatMap((section) => section.spanIds);
  const marked = [spans[1], spans[spans.length - 2]];
  const marks = state.density === "off" || state.sourceOff.has(extractionId) ? [] : marked
    .filter((spanId) => !state.hidden.has(`cue_${spanId}`))
    .slice(0, state.density === "fewer" ? 1 : 2)
    .map((spanId, rank) => cue(extractionId, spanId, rank));
  return {
    ...base, personalized: true,
    sections: base.sections.map((section, index) => (index === 0 ? {
      ...section, suggestedPassages: marked.map((spanId) => ({ spanId, quote: "", reason: "Revisit this", learningObjectId: "lo_softmax", learningObjectTitle: "Softmax weights", learnerSignal: "recent_misunderstanding" })),
    } : section)),
    cues: { version: "rw3a-guide-cues-v1", density: state.density, budgetPerSection: 2, onePerViewport: true, sourceOff: state.sourceOff.has(extractionId), marks, withheld: {} },
  } as ReaderGuidePlanDto;
}

let rectSpy: { mockRestore: () => void } | null = null;

beforeEach(() => {
  resetSidecar();
  state.density = "normal";
  state.sourceOff = new Set();
  state.hidden = new Set();
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_guide_plan", (input) => guideWithCues(String(input.extractionId)));
  answers.set("reader_cue_action", (input) => {
    if (input.action === "not_relevant") state.hidden.add(String(input.cueId));
    if (input.action === "not_relevant_undone") state.hidden.delete(String(input.cueId));
    return { cueId: input.cueId, action: input.action, eventId: "ev", verdict: "same", ledgerId: null, check: null };
  });
  answers.set("reader_set_cue_preferences", (input) => {
    if (typeof input.density === "string") state.density = input.density as typeof state.density;
    if (typeof input.sourceOff === "boolean") {
      const extraction = Object.values(FIXTURE_SOURCES).find((source) => source.sourceId === input.sourceId)?.extractionId ?? "";
      if (input.sourceOff) state.sourceOff.add(extraction);
      else state.sourceOff.delete(extraction);
    }
    return { enabled: true, density: state.density, budgetPerSection: 2, onePerViewport: true, sourceOff: Boolean(input.sourceOff), offSourceCount: state.sourceOff.size };
  });
  // jsdom has no layout: a passage sits at 200 px per block of its reading; each reading area is 600 px tall.
  const order = new Map<string, number>();
  for (const view of [FIXTURE_VIEWS[book.sourceId], FIXTURE_VIEWS[paper.sourceId]]) view.blocks.forEach((block, index) => order.set(block.spanId ?? "", index));
  const real = Element.prototype.getBoundingClientRect;
  const spy = vi.spyOn(Element.prototype, "getBoundingClientRect").mockImplementation(function (this: Element) {
    const spanId = (this as HTMLElement).dataset?.spanId;
    if (!spanId || !order.has(spanId)) return real.call(this);
    const top = (order.get(spanId) ?? 0) * 200;
    return { top, bottom: top + 40, left: 0, right: 500, width: 500, height: 40, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
  });
  rectSpy = spy;
  Object.defineProperty(HTMLElement.prototype, "clientHeight", {
    configurable: true,
    get(this: HTMLElement) {
      return this.getAttribute("role") === "main" ? 600 : 0;
    },
  });
});
afterEach(() => {
  cleanup();
  rectSpy?.mockRestore();
  vi.unstubAllGlobals();
  // @ts-expect-error -- restore jsdom's own (prototype chain) getter
  delete HTMLElement.prototype.clientHeight;
});

const winEl = (windowId: string) => document.querySelector<HTMLElement>(`[data-desk-window="${windowId}"]`)!;
const marksIn = (windowId: string) => Array.from(winEl(windowId).querySelectorAll<HTMLButtonElement>("[data-cue-span]"));

async function openTwoBooks() {
  const desk = mountRealDesk({ state: oneDesk([[windowOf("w_book", book) as never], [windowOf("w_paper", paper) as never]]) });
  await settleDesk(0, 20);
  await waitFor(() => expect(marksIn("w_book").length).toBe(2));
  await waitFor(() => expect(marksIn("w_paper").length).toBe(2));
  return desk;
}

it("each window draws its own reading's marks, and Alt+↓ / Alt+↑ move between the active window's marks only", async () => {
  await openTwoBooks();
  const [bookFirst, bookLast] = marksIn("w_book");
  fireEvent.keyDown(window, { key: "ArrowDown", altKey: true });
  expect(document.activeElement).toBe(bookFirst);
  fireEvent.keyDown(document.activeElement as Element, { key: "ArrowDown", altKey: true });
  expect(document.activeElement).toBe(bookLast);
  fireEvent.keyDown(document.activeElement as Element, { key: "ArrowUp", altKey: true });
  expect(document.activeElement).toBe(bookFirst);
  // The other window, made active by a press in it, moves between its own marks.
  (document.activeElement as HTMLElement).blur();
  fireEvent.pointerDown(winEl("w_paper"));
  fireEvent.mouseDown(winEl("w_paper"));
  await settleDesk(0, 3);
  fireEvent.keyDown(window, { key: "ArrowDown", altKey: true });
  expect(marksIn("w_paper")).toContain(document.activeElement);
});

it("not relevant… from a mark is undone in its window, with no Guide rail on the desk", async () => {
  await openTwoBooks();
  const [first] = marksIn("w_book");
  fireEvent.click(first);
  const popover = await within(winEl("w_book")).findByRole("group", { name: "this margin note" });
  fireEvent.click(within(popover).getByRole("button", { name: "not relevant…" }));
  fireEvent.click(within(popover).getByRole("button", { name: "send" }));
  await waitFor(() => expect(inputsOf("reader_cue_action").map((input) => input.action)).toContain("not_relevant"));
  await waitFor(() => expect(marksIn("w_book").length).toBe(1));
  const receipt = within(winEl("w_book")).getByText("Marked not relevant.");
  fireEvent.click(within(receipt.closest("[data-cue-receipts]") as HTMLElement).getByRole("button", { name: "undo" }));
  await waitFor(() => expect(inputsOf("reader_cue_action").map((input) => input.action)).toContain("not_relevant_undone"));
  await waitFor(() => expect(marksIn("w_book").length).toBe(2));
  // The other book's marks never moved.
  expect(marksIn("w_paper").length).toBe(2);
});

it("fewer marks and marks off for this book are undone in the window, and the density control sits at the foot of its reading", async () => {
  await openTwoBooks();
  fireEvent.click(marksIn("w_book")[0]);
  fireEvent.click(within(within(winEl("w_book")).getByRole("group", { name: "this margin note" })).getByRole("button", { name: "fewer marks like this" }));
  await waitFor(() => expect(inputsOf("reader_set_cue_preferences")[0]).toMatchObject({ density: "fewer", via: "fewer" }));
  await waitFor(() => expect(marksIn("w_book").length).toBe(1));
  const footer = within(winEl("w_book")).getByRole("group", { name: "margin marks" });
  expect(within(footer).getByRole("button", { name: "●fewer" })).toBeTruthy();
  fireEvent.click(within(within(winEl("w_book")).getByText("Margin marks: fewer.").closest("[data-cue-receipts]") as HTMLElement).getByRole("button", { name: "undo" }));
  await waitFor(() => expect(inputsOf("reader_set_cue_preferences").slice(-1)[0]).toMatchObject({ density: "normal", via: "undo" }));
  await waitFor(() => expect(marksIn("w_book").length).toBe(2));

  fireEvent.click(marksIn("w_book")[0]);
  fireEvent.click(within(within(winEl("w_book")).getByRole("group", { name: "this margin note" })).getByRole("button", { name: "marks off for this book" }));
  await waitFor(() => expect(marksIn("w_book").length).toBe(0));
  expect(marksIn("w_paper").length).toBe(2);
  // Off for this book: the foot of its reading says so and turns them back on.
  const off = within(winEl("w_book")).getByText("Margin marks are off for this book.", { selector: "[data-cue-receipt]" });
  fireEvent.click(within(off.closest("[data-cue-receipts]") as HTMLElement).getByRole("button", { name: "undo" }));
  await waitFor(() => expect(marksIn("w_book").length).toBe(2));
  void act;
  void screen;
});
