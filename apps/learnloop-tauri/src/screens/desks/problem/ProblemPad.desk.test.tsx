// RW2 on a desk, with real bodies (spec §15.2, §21.1 "Workbench (RW2a–d): problem pads; help ladder, checks and submit
// unchanged"): "work through this" in a book window opens the problem on a problem pad in the desk's stack, never a
// working posture over the book; the pad hosts the workbench itself, so steps are saved, I'm stuck asks for help up
// the ladder, and Submit records and goes to feedback through the workbench's own services; Leave keeps the pad with
// a way back.
import { cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { WorkbenchSessionDto } from "../../../api/dto";
import { setAlgoConfig } from "../../../app/algoConfig";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { readerIntentContractFixture } from "../../../fixtures/readerIntentContract";
import { HELP_COPY } from "../../workbench/helpModel";
import { resetProblemsForTests } from "./problemPads";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../../../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("../../../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));

const { book } = FIXTURE_SOURCES;
const FIRST = `${book.extractionId}_s1_1`;
const BOX = "What do you want to do with this?";
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };
const STACK_WINDOW = { windowId: "w_pads", pane: 0, kind: "pad_stack", active: true, view: {}, stack: [{ kind: "pad", padId: "fx_pad_running" }] };
const RECORD = { bookCounted: false, bookVisible: true, hints: 0, questionHints: 0, ownAttempt: true, line: "your own attempt", footer: "book open · help used: none", stuckNote: null };

function session(overrides: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return {
    sessionId: "wb_desk", practiceItemId: "pi_desk", stemMd: "Exercise 1.2 Show the weights sum to one.", importStatus: "none", importError: null,
    origin: "reader", entry: "work_through", parentSessionId: null, extractionId: book.extractionId, spanIds: [FIRST], sourceVisible: true,
    sourceHiddenAt: null, sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open", attemptId: null,
    createdAt: "2026-11-23T09:00:00Z", updatedAt: "2026-11-23T09:00:00Z", closedAt: null, steps: [], lastEditedStepId: null,
    record: RECORD, parts: null, sourceId: book.sourceId, ...overrides,
  };
}

let saved = 0;
beforeEach(() => {
  resetSidecar();
  resetProblemsForTests();
  saved = 0;
  setAlgoConfig({ workbench: { enabled: true, openSessionDays: 30, help: { enabled: true } }, hints: { adaptiveEnabled: true } } as never);
  vi.stubGlobal("localStorage", memoryStorage());
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  Element.prototype.scrollIntoView = vi.fn();
  answers.set("reader_prompt_contract", () => ({
    version: "fixture", context: "reader", readerEnabled: true, notSocraticByDefault: true, defaultAnswerMode: "answer_directly",
    answerModes: ["answer_directly"], mayReveal: [], manifestIncludes: [], manifestNeverIncludes: [], citations: "spans",
    exposureOnCommit: "none", inquiryEnabled: true, intent: readerIntentContractFixture, activeReading: { foldBlocks: 2 },
  }));
  answers.set("reader_intent_outcome", () => ({ routingId: "r", recorded: true }));
  answers.set("workbench_for_source", () => ({ sessions: [], openSessionDays: 30 }));
  answers.set("workbench_open", (input) => ({ session: session(input.entry === "resume" ? { sessionId: String(input.sessionId) } : {}), resumed: input.entry === "resume" }));
  answers.set("workbench_refresh_import", () => ({ session: session() }));
  answers.set("workbench_admit", () => ({ session: session() }));
  answers.set("workbench_save_step", (input) => {
    saved += 1;
    return { version: 1, savedAt: "2026-11-23T09:00:05Z", record: RECORD,
      step: { stepId: `row_${saved}`, chainId: input.stepId ?? `row_${saved}`, ordinal: saved, kind: input.kind ?? "step", bodyMd: input.bodyMd ?? "", deleted: false, createdAt: "x", editedAt: "x", versions: [] } };
  });
  answers.set("workbench_help_state", () => ({ version: 1, check: null, hints: [], helpStyle: null, storedHelpStyle: "socratic", hintsEnabled: true }));
  answers.set("workbench_suggest_help", () => ({ version: 1, jobId: "job_suggest", kind: "suggest", state: "pending", result: null }));
  answers.set("workbench_help_job", () => ({ version: 1, jobId: "job_suggest", kind: "suggest", state: "pending", result: null }));
  answers.set("workbench_leave", () => ({ session: session() }));
  answers.set("workbench_check", () => ({ version: 1, jobId: "job_check", kind: "check", state: "pending", result: null }));
  answers.set("workbench_cancel_help", () => ({ cancelled: true }));
  answers.set("workbench_submit", () => ({
    version: 1, practiceSession: null, session: session({ status: "submitted", attemptId: "att_desk" }),
    attempt: { attemptId: "att_desk" },
  }));
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
  window.getSelection()?.removeAllRanges();
});

const bookEl = () => document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!;
const padsEl = () => document.querySelector<HTMLElement>('[data-desk-window="w_pads"]')!;

function twoDeskState() {
  const state = oneDesk([[BOOK_WINDOW as never], [STACK_WINDOW as never]]);
  const BOOK2 = { ...BOOK_WINDOW, windowId: "w_book2" };
  const STACK2 = { ...STACK_WINDOW, windowId: "w_pads2", stack: [] };
  return { ...state, desks: [state.desks[0], { ...state.desks[0], deskId: "d_two", title: "two", position: "b", focusWindowId: "w_book2",
    slots: [{ slot: 0, windows: [BOOK2] }, { slot: 1, windows: [STACK2] }] }] } as never;
}

async function openFrom(windowId: string) {
  const win = () => document.querySelector<HTMLElement>(`[data-desk-window="${windowId}"]`)!;
  const block = await waitFor(() => {
    const found = win()?.querySelector<HTMLElement>(`[data-span-id="${FIRST}"]`);
    if (!found) throw new Error("not yet");
    return found;
  });
  const range = document.createRange();
  range.selectNodeContents(block);
  window.getSelection()!.removeAllRanges();
  window.getSelection()!.addRange(range);
  fireEvent.mouseUp(block);
  const box = await within(win()).findByRole("textbox", { name: BOX });
  fireEvent.keyDown(box, { key: "Tab" });
  const palette = await within(win()).findByRole("group", { name: "what do you want to do?" });
  fireEvent.click(within(palette).getByRole("button", { name: "work through this" }));
  await settleDesk(0, 12);
}

async function workThrough(onSubmitted = vi.fn(), options: { pads?: never; twoDesks?: boolean } = {}) {
  const desk = mountRealDesk({
    state: options.twoDesks ? twoDeskState() : oneDesk([[BOOK_WINDOW as never], [STACK_WINDOW as never]]),
    ...(options.pads ? { pads: options.pads } : {}),
    props: { reader: { workbench: { practiceSessionId: null, onSubmitted } } },
  });
  await settleDesk(0, 20);
  await openFrom("w_book");
  return { desk };
}

it("work through this opens the problem on a problem pad in the desk's stack, not over the book", async () => {
  const { desk } = await workThrough();
  expect(inputsOf("workbench_open")[0]).toMatchObject({ origin: "reader", entry: "work_through", extractionId: book.extractionId });
  // No working posture in the book's window: it keeps reading.
  expect(bookEl().querySelector("[data-workbench-pane]")).toBeNull();
  expect(within(bookEl()).queryByRole("region", { name: "workbench" })).toBeNull();
  // A problem pad bound to the session, in the stack, hosting the workbench.
  await waitFor(() => expect(desk.server.padBatches.flatMap((batch) => batch.ops as Array<Record<string, unknown>>).find((op) => op.op === "create_pad"))
    .toMatchObject({ kind: "problem", workbenchSessionId: "wb_desk" }), { timeout: 4000 });
  await waitFor(() => expect(padsEl().querySelector('[data-problem-pad="wb_desk"][data-problem-state="open"]')).not.toBeNull());
  expect(within(padsEl()).getByRole("region", { name: "workbench" })).toBeTruthy();
});

it("on the pad, steps save, the help ladder and the check run, and Submit records and goes to feedback; the pad shows it submitted", async () => {
  const onSubmitted = vi.fn();
  await workThrough(onSubmitted);
  const pad = await waitFor(() => {
    const found = padsEl().querySelector<HTMLElement>('[data-problem-pad="wb_desk"]');
    if (!found) throw new Error("not yet");
    return found;
  });
  const step = within(pad).getAllByRole("textbox")[0];
  fireEvent.change(step, { target: { value: "Each weight is positive." } });
  await waitFor(() => expect(inputsOf("workbench_save_step").some((input) => String(input.bodyMd ?? "").includes("Each weight is positive."))).toBe(true), { timeout: 4000 });
  // The help ladder and the check, unchanged (the workbench's own controls and services).
  fireEvent.click(within(pad).getByRole("button", { name: new RegExp(`^${HELP_COPY.help} ·`) }));
  await waitFor(() => expect(within(pad).getByRole("listbox", { name: "help ladder" })).toBeTruthy());
  await waitFor(() => expect(inputsOf("workbench_suggest_help")[0]).toMatchObject({ sessionId: "wb_desk" }));
  fireEvent.click(within(pad).getByRole("button", { name: new RegExp(`^${HELP_COPY.check} ·`) }));
  await waitFor(() => expect(inputsOf("workbench_check")[0]).toMatchObject({ sessionId: "wb_desk" }));
  fireEvent.click(within(pad).getByRole("button", { name: /^submit/i }));
  await settleDesk(0, 8);
  expect(inputsOf("workbench_submit")[0]).toMatchObject({ sessionId: "wb_desk" });
  expect(onSubmitted).toHaveBeenCalledWith(expect.objectContaining({ attempt: { attemptId: "att_desk" } }),
    expect.objectContaining({ spanId: FIRST, card: expect.objectContaining({ sourceId: book.sourceId }) }));
  await waitFor(() => expect(padsEl().querySelector('[data-problem-pad="wb_desk"][data-problem-state="submitted"]')).not.toBeNull());
});

it("leave for now keeps the pad with a way back, and resume reopens the same problem there", async () => {
  await workThrough();
  const pad = await waitFor(() => {
    const found = padsEl().querySelector<HTMLElement>('[data-problem-pad="wb_desk"]');
    if (!found) throw new Error("not yet");
    return found;
  });
  fireEvent.click(within(pad).getByRole("button", { name: /leave for now/i }));
  await settleDesk(0, 8);
  const away = await waitFor(() => {
    const found = padsEl().querySelector<HTMLElement>('[data-problem-pad="wb_desk"][data-problem-state="left"]');
    if (!found) throw new Error("not yet");
    return found;
  });
  fireEvent.click(within(away).getByRole("button"));
  await settleDesk(0, 8);
  expect(inputsOf("workbench_open").slice(-1)[0]).toMatchObject({ entry: "resume", sessionId: "wb_desk" });
  await waitFor(() => expect(padsEl().querySelector('[data-problem-pad="wb_desk"][data-problem-state="open"]')).not.toBeNull());
});

// -- one pad per problem -----------------------------------------------------------------------------------------

function problemPadsOn(server: { pads: Record<string, { pad: { padId: string; kind: string; workbenchSessionId: string | null; homeDeskId: string | null } }> }) {
  return Object.values(server.pads).filter((each) => each.pad.kind === "problem" && each.pad.workbenchSessionId === "wb_desk");
}

it("opening the same problem again in a fresh desk view, its pad not loaded, finds that pad: one pad, never two", async () => {
  const first = await workThrough();
  await waitFor(() => expect(problemPadsOn(first.desk.server as never)).toHaveLength(1), { timeout: 4000 });
  // The server's pads as a new view finds them (the fixture's own and the problem's), as views.
  const server = first.desk.server as unknown as { padGet: (padId: string) => unknown; pads: Record<string, unknown> };
  const pads = Object.keys(server.pads).map((padId) => server.padGet(padId));
  cleanup();
  resetProblemsForTests();
  // A fresh view of the desks over the same server: the problem pad exists there, in no stack, not loaded.
  const again = await workThrough(vi.fn(), { pads: pads as never });
  // Long enough for the desks' outbox to have sent any pad it made (it flushes on a timer).
  await settleDesk(0, 10);
  await new Promise((resolve) => setTimeout(resolve, 2500));
  await settleDesk(0, 4);
  expect(problemPadsOn(again.desk.server as never)).toHaveLength(1);
  await waitFor(() => expect(padsEl().querySelector('[data-problem-pad="wb_desk"]')).not.toBeNull());
});

it("opened from another desk, the problem is shown on the desk its pad lives on", async () => {
  const { desk } = await workThrough(vi.fn(), { twoDesks: true });
  await waitFor(() => expect(problemPadsOn(desk.server as never)).toHaveLength(1), { timeout: 4000 });
  const home = problemPadsOn(desk.server as never)[0].pad.homeDeskId;
  // Switch to the second desk and open the same problem from its book window.
  fireEvent.click(within(document.body).getByRole("button", { name: "two", exact: true } as never));
  await settleDesk(0, 10);
  await openFrom("w_book2");
  await settleDesk(0, 12);
  await new Promise((resolve) => setTimeout(resolve, 2500));
  await settleDesk(0, 4);
  expect(problemPadsOn(desk.server as never)).toHaveLength(1);
  // Back on the desk the pad lives on (the current desk again), its stack showing the problem; the second desk's
  // stack never took it.
  expect(home).not.toBe("d_two");
  await waitFor(() => expect(within(document.body).getByRole("button", { name: "two", exact: true } as never).getAttribute("aria-current")).toBe("false"));
  expect(document.querySelector('[data-desk-window="w_pads"] [data-problem-pad="wb_desk"]')).not.toBeNull();
  expect(desk.server.state().desks.find((each) => each.deskId === "d_two")!.slots.flatMap((slot) => slot.windows).flatMap((window) => window.stack ?? [])
    .some((entry) => entry.kind === "pad" && entry.padId === problemPadsOn(desk.server as never)[0].pad.padId)).toBe(false);
});
