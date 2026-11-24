// Handwritten work on a problem pad, with real bodies (owner decision 2026-11-23: "feed the transcription into the
// existing workbench steps"; "show to the user their transcription output in a subtle way … which they can audit and
// correct"). The desks mount the problem pad's workbench and the pen; only the sidecar is faked:
//
// * an ink line's reading becomes a step of the problem, through the workbench's own step writer, its key derived
//   from the line (a reopened problem finds the same step), shown as the line with its reading quiet under it;
// * the learner's correction of that reading replaces the step's text (what help and the check read from then on);
// * a line not read yet is never a step: nothing of it is sent, and the ladder says it cannot see it, with
//   "type what you wrote";
// * help on a step still read only by LearnLoop says so, once, beside the ladder.
import { act, cleanup, fireEvent, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { WorkbenchSessionDto } from "../../../api/dto";
import { setAlgoConfig } from "../../../app/algoConfig";
import { answers, inputsOf, memoryStorage, mountRealDesk, oneDesk, resetSidecar, settleDesk } from "../../../fixtures/desks/realDesk";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { readerIntentContractFixture } from "../../../fixtures/readerIntentContract";
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
const READING = "$p_k = -h_k$";

function session(overrides: Partial<WorkbenchSessionDto> = {}): WorkbenchSessionDto {
  return {
    sessionId: "wb_ink", practiceItemId: "pi_ink", stemMd: "Exercise 1.2 Show the weights sum to one.", importStatus: "none", importError: null,
    origin: "reader", entry: "work_through", parentSessionId: null, extractionId: book.extractionId, spanIds: [FIRST], sourceVisible: true,
    sourceHiddenAt: null, sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open", attemptId: null,
    createdAt: "2026-11-23T09:00:00Z", updatedAt: "2026-11-23T09:00:00Z", closedAt: null, steps: [], lastEditedStepId: null,
    record: RECORD, parts: null, sourceId: book.sourceId, ...overrides,
  };
}

/** The steps the fake workbench holds, by chain: what help and the check read. */
const steps = new Map<string, string>();
const chainOfRow = new Map<string, string>();
const byKey = new Map<string, unknown>();
let rows = 0;
/** Whether GLM-OCR reads (else it is refused: not set up). */
let reads = true;
let desk: ReturnType<typeof mountRealDesk>;

beforeEach(() => {
  resetSidecar();
  resetProblemsForTests();
  steps.clear();
  chainOfRow.clear();
  byKey.clear();
  rows = 0;
  reads = true;
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
  answers.set("workbench_open", () => ({ session: session(), resumed: false }));
  answers.set("workbench_refresh_import", () => ({ session: session() }));
  answers.set("workbench_save_step", (input) => {
    // The service's own rules: a repeated key answers what it answered; an edit is a new row of the same chain.
    const key = String(input.clientIdempotencyKey);
    if (byKey.has(key)) return byKey.get(key);
    rows += 1;
    const row = `row_${rows}`;
    const chain = input.op === "add" ? row : chainOfRow.get(String(input.stepId)) ?? String(input.stepId);
    chainOfRow.set(row, chain);
    if (input.bodyMd !== undefined && input.bodyMd !== null) steps.set(chain, String(input.bodyMd));
    const answer = { version: 1, savedAt: "2026-11-23T09:00:05Z", record: RECORD,
      step: { stepId: row, chainId: chain, ordinal: rows, kind: input.kind ?? "step", bodyMd: steps.get(chain) ?? "", deleted: false, createdAt: "x", editedAt: "x", versions: [] } };
    byKey.set(key, answer);
    return answer;
  });
  answers.set("workbench_help_state", () => ({ version: 1, check: null, hints: [], helpStyle: null, storedHelpStyle: "socratic", hintsEnabled: true }));
  answers.set("workbench_suggest_help", () => ({ version: 1, jobId: "job_suggest", kind: "suggest", state: "pending", result: null }));
  answers.set("workbench_help_job", () => ({ version: 1, jobId: "job_suggest", kind: "suggest", state: "pending", result: null }));
  answers.set("workbench_cancel_help", () => ({ cancelled: true }));
  // Ink saves and lists go to the desk's own fake server (one client sequence with its pad batches).
  answers.set("ink_save", (input) => desk.server.applyInk(input as never));
  answers.set("ink_list", (input) => ({ version: 1, padId: input.padId ?? null, sourceId: input.sourceId ?? null, owners: input.padId ? desk.server.inkFor(String(input.padId)) : [] }));
  answers.set("ink_transcribe", (input) => {
    if (!reads) {
      return { version: 1, jobId: null, status: "failed", done: true, result: null,
        error: { code: "unavailable", message: "not set up", retryable: true, details: null } };
    }
    // GLM-OCR's reading becomes the line's words as the server writes them (provenance ink_transcription).
    const blockId = ownerOf(String(input.inkId));
    const headVersionId = `v_read_${blockId}`;
    setBlock(blockId, { headVersionId, bodyMd: READING, provenance: "ink_transcription" });
    return { version: 1, jobId: null, status: "done", done: true, error: null, result: {
      transcriptionId: `it_${blockId}`, ownerKind: "block", ownerId: blockId, contentHash: `h_${blockId}`, latexMd: READING,
      confidenceLabel: "may_be_wrong", model: "glm-ocr-0.9B", createdAt: "t", applied: true, reason: null, headVersionId } };
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
  window.getSelection()?.removeAllRanges();
});

function ownerOf(inkId: string): string {
  const save = inputsOf("ink_save").find((input) => input.inkId === inkId);
  return String((save?.owner as { blockId: string }).blockId);
}

function setBlock(blockId: string, change: Record<string, unknown>) {
  const pads = desk.server.pads;
  const padId = Object.keys(pads).find((id) => pads[id].blocks.some((block) => block.blockId === blockId))!;
  desk.server.pads = { ...pads, [padId]: { ...pads[padId], blocks: pads[padId].blocks.map((block) => (block.blockId === blockId ? { ...block, ...change } as never : block)) } };
}

const padsEl = () => document.querySelector<HTMLElement>('[data-desk-window="w_pads"]')!;
const problemEl = () => padsEl().querySelector<HTMLElement>("[data-problem-pad]")!;

function pointer(type: string, x: number, y: number) {
  const event = new MouseEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 1 });
  Object.assign(event, { pointerId: 3, pointerType: "pen", pressure: 0.5, tiltX: 0, tiltY: 0 });
  return event;
}

/** A pen stroke on the problem pad's last row: a new ink line. */
async function writeLine() {
  const jot = await waitFor(() => {
    const found = problemEl()?.closest("[data-pad]")?.querySelector<HTMLElement>('[data-ink-surface][aria-label="write a new line with the pen"]');
    if (!found) throw new Error("no jot yet");
    return found;
  });
  act(() => {
    jot.dispatchEvent(pointer("pointerdown", 10, 20));
    for (const [x, y] of [[16, 28], [22, 18], [28, 30], [34, 22]]) jot.dispatchEvent(pointer("pointermove", x, y));
    jot.dispatchEvent(pointer("pointerup", 34, 22));
  });
  await settleDesk(0, 12);
}

async function openProblemWithPen() {
  desk = mountRealDesk({
    state: oneDesk([[BOOK_WINDOW as never], [STACK_WINDOW as never]]),
    props: { reader: { workbench: { practiceSessionId: null, onSubmitted: vi.fn() } } },
  });
  await settleDesk(0, 20);
  const win = () => document.querySelector<HTMLElement>('[data-desk-window="w_book"]')!;
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
  await waitFor(() => expect(problemEl()).toBeTruthy());
  fireEvent.click(document.querySelector<HTMLElement>(".penchip")!);
  await settleDesk(0, 6);
}

const inkSteps = () => inputsOf("workbench_save_step").filter((input) => String(input.clientIdempotencyKey).startsWith("ink-step:"));

it("an ink line's reading becomes a step of the problem, shown as the line with its reading quiet under it", async () => {
  await openProblemWithPen();
  await writeLine();
  // Not read yet: no step, nothing sent.
  expect(inkSteps()).toEqual([]);
  fireEvent.click(await within(padsEl()).findByRole("button", { name: "read it" }));
  await settleDesk(0, 16);
  await waitFor(() => expect(inkSteps()).toHaveLength(1));
  const [added] = inkSteps();
  const blockId = ownerOf(String(inputsOf("ink_save")[0].inkId));
  expect(added).toMatchObject({ sessionId: "wb_ink", op: "add", kind: "step", bodyMd: READING, clientIdempotencyKey: `ink-step:${blockId}` });
  // In the workbench, as its step: the handwriting, with "read as … may be wrong · fix it" under it.
  const line = await waitFor(() => {
    const found = problemEl().querySelector<HTMLElement>(`[data-ink-step="${blockId}"]`);
    if (!found) throw new Error("not a step yet");
    return found;
  });
  expect(line.querySelector("[data-ink-transcription='reading']")?.textContent).toContain("may be wrong");
  // Shown once: not also as a pad block under the workbench.
  expect(padsEl().querySelectorAll(`[data-ink-block="${blockId}"]`)).toHaveLength(1);
});

it("the learner's correction replaces the step's text, and help says once that it reads LearnLoop's reading until then", async () => {
  await openProblemWithPen();
  await writeLine();
  fireEvent.click(await within(padsEl()).findByRole("button", { name: "read it" }));
  await settleDesk(0, 16);
  await waitFor(() => expect(inkSteps()).toHaveLength(1));
  const chain = String((byKey.get(String(inkSteps()[0].clientIdempotencyKey)) as { step: { chainId: string } }).step.chainId);
  // Help on the step, still LearnLoop's reading: said beside the ladder, once.
  const stepLine = problemEl().querySelector<HTMLElement>("[data-ink-step]")!;
  fireEvent.focusIn(stepLine);
  fireEvent.click(within(problemEl()).getByRole("button", { name: /help ·/ }));
  await settleDesk(0, 6);
  await waitFor(() => expect(problemEl().querySelector("[data-ink-help-note='reading']")).toBeTruthy());
  fireEvent.keyDown(problemEl().querySelector("[role=listbox]")!, { key: "Escape" });
  await settleDesk(0, 4);
  fireEvent.click(within(problemEl()).getByRole("button", { name: /help ·/ }));
  await settleDesk(0, 6);
  expect(problemEl().querySelector("[data-ink-help-note='reading']")).toBeNull();
  fireEvent.keyDown(problemEl().querySelector("[role=listbox]")!, { key: "Escape" });
  // The correction, made in place under the line: a new version of the line, and the step's text.
  fireEvent.click(within(stepLine).getByRole("button", { name: "fix it" }));
  const field = within(stepLine).getByLabelText("what this line says");
  fireEvent.change(field, { target: { value: "p_k = e^{h_k} / \\sum_j e^{h_j}" } });
  fireEvent.blur(field);
  await settleDesk(0, 6);
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 700));
  });
  await settleDesk(0, 10);
  await waitFor(() => expect(steps.get(chain)).toBe("p_k = e^{h_k} / \\sum_j e^{h_j}"));
  const edits = inputsOf("workbench_save_step").filter((input) => input.op === "edit");
  expect(edits[edits.length - 1]).toMatchObject({ op: "edit", bodyMd: "p_k = e^{h_k} / \\sum_j e^{h_j}" });
  expect(problemEl().querySelector("[data-ink-step] [data-ink-transcription='yours']")).toBeTruthy();
});

it("a line not read is never a step: the ladder says it cannot see it, and type what you wrote makes it one", async () => {
  reads = false;
  await openProblemWithPen();
  await writeLine();
  fireEvent.click(await within(padsEl()).findByRole("button", { name: "read it" }));
  await settleDesk(0, 10);
  expect(inkSteps()).toEqual([]);
  fireEvent.click(within(problemEl()).getByRole("button", { name: /help ·/ }));
  await settleDesk(0, 6);
  const note = await waitFor(() => {
    const found = problemEl().querySelector<HTMLElement>("[data-ink-help-note='unseen']");
    if (!found) throw new Error("no note");
    return found;
  });
  expect(note.textContent).toContain("can't see your line 1 yet");
  // Nothing of the line went to help: the only steps sent are none, the suggestion asked over no ink step.
  expect(inkSteps()).toEqual([]);
  fireEvent.click(within(note).getByRole("button", { name: "type what you wrote" }));
  await settleDesk(0, 4);
  const field = within(padsEl()).getByLabelText("what this line says");
  fireEvent.change(field, { target: { value: "w_k > 0" } });
  fireEvent.blur(field);
  await settleDesk(0, 12);
  await waitFor(() => expect(inkSteps()).toHaveLength(1));
  expect(inkSteps()[0]).toMatchObject({ op: "add", bodyMd: "w_k > 0" });
});
