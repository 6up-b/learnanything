// Show me in the companion, with real bodies (spec §13.1, §21.1 "Figures and Show me"): the figure Show me builds on
// a passage appears in the companion as "◇ Show me · a figure for <source> p.<page>", the live widget itself, with
// view source (its source, display tier), move to scratchpad (a `figure` block in the running pad of the desk it was
// asked on) and not useful (removed, and logged), and the footer that says it is help, not a check.
import { act, cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { FigureViewDto, PadOpDto } from "../../../api/dto";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import corpus from "../../reader/figures/figureGoldenCorpus.json";
import { resetSharedParamsForTests } from "../../reader/figures/sharedParams";
import { COMPANION_FIGURE_COPY, resetCompanionFiguresForTests } from "./companionFigures";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book } = FIXTURE_SOURCES;
const FIRST = `${book.extractionId}_s1_1`;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };
const STACK_WINDOW = { windowId: "w_pads", pane: 0, kind: "pad_stack", active: true, view: {}, stack: [{ kind: "pad", padId: "fx_pad_running" }] };
const SPEC = corpus.figures.find((item) => item.id === "two_sided_exponential")!.spec;

function figure(figureId: string): FigureViewDto {
  return {
    figureId, extractionId: book.extractionId, spanIds: [FIRST], anchorSpanId: FIRST, region: null, origin: "show_me",
    verification: "verified", shown: true, labelCode: "illustrative", kind: "reconstructed", label: "AI-built illustration",
    reason: null, unsupportedKind: null, supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-11-23T00:00:00",
    specJson: JSON.stringify(SPEC), demonstrates: "how the weights move with the temperature", assumptions: [], predictions: [],
    goalText: "softmax at a temperature", grounding: "passages",
    passages: [{ extractionId: book.extractionId, spanId: FIRST, sourceTitle: "Softmax, a short book", page: 2 }],
  } as unknown as FigureViewDto;
}

let built = "fig_a";
beforeEach(() => {
  resetSidecar();
  resetCompanionFiguresForTests();
  resetSharedParamsForTests();
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("figure_request", () => ({ jobId: "fj1", kind: "figure_build", askId: null, state: "pending", result: null }));
  answers.set("reader_figure_job", () => ({ jobId: "fj1", kind: "figure_build", askId: null, state: "done", result: { figure: figure(built), reused: false } }));
  answers.set("reader_log_activity", () => ({ recorded: 1 }));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const bookEl = () => document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!;
const companion = () => document.querySelector<HTMLElement>('[aria-label="the companion"]')!;

async function showMe(id: string) {
  built = id;
  const desk = mountRealDesk({ state: oneDesk([[BOOK_WINDOW as never], [STACK_WINDOW as never]]) });
  await settleDesk(0, 20);
  const passage = await waitFor(() => {
    const found = bookEl().querySelector<HTMLElement>(`[data-span-id="${FIRST}"]`);
    if (!found) throw new Error("not yet");
    return found;
  });
  fireEvent.contextMenu(passage);
  await settleDesk(0, 4);
  fireEvent.keyDown(window, { key: "v" });
  await settleDesk(0, 6);
  await act(async () => {
    await desk.poller.tick();
  });
  await settleDesk(0, 8);
  const item = await waitFor(() => {
    const found = companion().querySelector<HTMLElement>(`[data-companion-figure="${id}"]`);
    if (!found) throw new Error("not yet");
    return found;
  });
  return { desk, item };
}

it("the figure appears in the companion, live, named for its source and page, with its three buttons and footer", async () => {
  const { desk, item } = await showMe("fig_a");
  expect(inputsOf("figure_request")[0]).toMatchObject({ origin: "show_me" });
  expect(item.textContent).toContain(COMPANION_FIGURE_COPY.lead);
  expect(item.textContent).toContain("a figure for Softmax, a short book p.2");
  // The live widget: the Reader's figure, open, its sliders there.
  expect(item.querySelector('[data-figure="fig_a"]')).not.toBeNull();
  expect(within(item).getAllByRole("slider").length).toBeGreaterThan(0);
  expect(item.textContent).toContain(COMPANION_FIGURE_COPY.footer);
  // Nothing landed in the pad by itself.
  expect(desk.server.padBatches.some((batch) => (batch.ops as PadOpDto[]).some((op) => op.op === "insert_block" && op.kind === "figure"))).toBe(false);
});

it("view source shows the figure's source; move to scratchpad writes a figure block in the running pad and leaves the companion", async () => {
  const { desk, item } = await showMe("fig_b");
  fireEvent.click(within(item).getByRole("button", { name: COMPANION_FIGURE_COPY.viewSource }));
  expect(item.querySelector("[data-figure-source] pre")?.textContent).toContain("parameters");
  fireEvent.click(within(item).getByRole("button", { name: COMPANION_FIGURE_COPY.move }));
  await settleDesk(0, 8);
  await waitFor(() => {
    const inserts = desk.server.padBatches.filter((batch) => (batch.ops as PadOpDto[]).some((op) => op.op === "insert_block" && op.kind === "figure"));
    expect(inserts.map((batch) => batch.padId)).toEqual(["fx_pad_running"]);
  }, { timeout: 4000 });
  await waitFor(() => expect(companion().querySelector('[data-companion-figure="fig_b"]')).toBeNull());
});

it("not useful removes it and is logged", async () => {
  const { item } = await showMe("fig_c");
  fireEvent.click(within(item).getByRole("button", { name: COMPANION_FIGURE_COPY.notUseful }));
  await waitFor(() => expect(companion().querySelector('[data-companion-figure="fig_c"]')).toBeNull());
  await waitFor(() => expect(inputsOf("reader_log_activity").flatMap((input) => (input.events as Array<{ event?: string; payload?: Record<string, unknown> }>) ?? [])
    .some((event) => event.event === "figure_not_useful" && event.payload?.figure_id === "fig_c")).toBe(true), { timeout: 4000 });
});
