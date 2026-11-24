// The app's ways back onto the desks, end to end (spec §21.1's parity rows; the RD-retire record's loose ends): the
// whole App mounted with the real desks (fixtures/desks/realApp.tsx), the Reader place on the desks, every desk, pad
// and book read through the app's api client from a fake sidecar. Only the practice screen is a stand-in (its back is
// the app's own way back), and the leave-time offer shows only whether the app mounted it.
//
// - Back from a check begun in the paired (second) book of a side-by-side pair: the pair, that window focused at the
//   check's passage, still a pair (F6 goes to its partner).
// - Today's resume of an unfinished problem: its problem pad on the desk it lives on.
// - Leaving the Reader place while the book being read is skimmed: no leave-time offer; read closely: the offer.
import { act, cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clear } from "../api/queryCache";
import { appSidecar } from "../fixtures/desks/realApp";
import { answers, inputsOf, oneDesk, settleDesk } from "../fixtures/desks/realDesk";
import { FIXTURE_GUIDES, FIXTURE_SOURCES } from "../fixtures/desks/sources";
import { readerIntentContractFixture } from "../fixtures/readerIntentContract";
import { resetProblemsForTests } from "../screens/desks/problem/problemPads";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: async (command: string, args?: unknown) => (await import("../fixtures/desks/realDesk")).core.invoke(command, args as never),
  convertFileSrc: (path: string) => path,
}));
vi.mock("@tauri-apps/api/event", () => ({ listen: vi.fn(async () => () => undefined) }));
vi.mock("@tauri-apps/plugin-dialog", () => ({ open: vi.fn(async () => null) }));
vi.mock("../components/useSourceFileDrop", () => ({ useSourceFileDrop: () => false, pickSourceFiles: async () => [] }));
vi.mock("../components/InboxStrip", () => ({ InboxStrip: () => null }));
vi.mock("../components/PdfReaderPane", () => ({ PdfReaderPane: () => null }));
vi.mock("../screens/PracticeScreen", () => ({
  PracticeScreen: ({ practiceItemId, onBack }: { practiceItemId: string; onBack?: () => void }) => (
    <div data-testid="practice-stand-in" data-item={practiceItemId}>
      <button type="button" onClick={() => onBack?.()}>practice back</button>
    </div>
  ),
}));
vi.mock("../screens/reader/WrapUpOffer", () => ({ WrapUpOffer: () => <div data-testid="wrap-up-offer" /> }));
vi.mock("../screens/FeedbackScreen", () => ({
  FeedbackScreen: ({ attemptId, onBack, onNext }: { attemptId: string; onBack: () => void; onNext: () => void }) => (
    <div data-testid="feedback-stand-in" data-attempt={attemptId}>
      <button type="button" onClick={() => onNext()}>back to the book</button>
      <button type="button" onClick={() => onBack()}>feedback back</button>
    </div>
  ),
}));

import { App } from "./App";

const { book, paper } = FIXTURE_SOURCES;
const BOOK_WINDOW = { windowId: "w_book", pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: book.sourceId, extractionId: book.extractionId, view: "render" } };
const PADS_WINDOW = { windowId: "w_pads", pane: 0, kind: "pad_stack", active: true, view: {}, stack: [{ kind: "pad", padId: "fx_pad_running" }] };
const SESSION = { version: 1, sessionId: "ps_1", startedAt: "2026-11-23T09:00:00Z", endedAt: null, energy: null, sleepQuality: null, availableMinutes: 25, notesMdPath: null, checkpoint: null };
const PAPER_P2 = `${paper.extractionId}_p2_2`;

const winOf = (id: string) => document.querySelector<HTMLElement>(`[data-desk-window="${id}"]`);
const slotOf = (el: Element) => el.closest("[data-desk-slot]")?.getAttribute("data-desk-slot")?.split(":") ?? [];
const focusedWindow = () => document.querySelector(".desk-window.focus [data-desk-window]")?.getAttribute("data-desk-window") ?? null;
const paperWindow = () => Array.from(document.querySelectorAll<HTMLElement>("[data-desk-window]"))
  .find((each) => each.querySelector(`[data-span-id^="${paper.extractionId}_"]`)) ?? null;

async function press(init: KeyboardEventInit) {
  await act(async () => {
    window.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, cancelable: true, ...init }));
  });
}

/** The app, mounted and shown its Reader place (the desks). */
async function openReaderPlace() {
  render(<App />);
  await screen.findByRole("navigation", { name: "Places" });
  await press({ key: "3", altKey: true });
  await settleDesk(0, 20);
  await waitFor(() => expect(document.querySelector("[data-desk-shell]")).not.toBeNull());
}

function contract(extra: Record<string, unknown> = {}) {
  return {
    version: "fixture", context: "reader", readerEnabled: true, notSocraticByDefault: true, defaultAnswerMode: "answer_directly",
    answerModes: ["answer_directly"], mayReveal: [], manifestIncludes: [], manifestNeverIncludes: [], citations: "spans",
    exposureOnCommit: "none", inquiryEnabled: true, intent: readerIntentContractFixture, activeReading: { foldBlocks: 3 },
    sideBySide: { enabled: true }, ...extra,
  };
}

beforeEach(() => {
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
  vi.stubGlobal("IntersectionObserver", class { observe() {} unobserve() {} disconnect() {} takeRecords() { return []; } });
  resetProblemsForTests();
});
afterEach(() => {
  cleanup();
  clear();
  vi.unstubAllGlobals();
  window.getSelection()?.removeAllRanges();
});

function pairSidecar(options: { config?: Record<string, unknown>; withPads?: boolean } = {}) {
    const app = appSidecar({ state: oneDesk(options.withPads ? [[BOOK_WINDOW as never], [PADS_WINDOW as never]] : [[BOOK_WINDOW as never]]), session: SESSION,
      ...(options.config ? { config: options.config } : {}) });
    vi.stubGlobal("localStorage", app.storage);
    answers.set("reader_prompt_contract", () => contract());
    // The paper corresponds to the book's first section, so Ctrl+\ opens it paired.
    answers.set("reader_correspondents", (input) => {
      const sections = String(input.sectionId) === `${book.extractionId}_s1` ? [{
        extractionId: paper.extractionId, sectionId: `${paper.extractionId}_p1`, title: "p1 Attention", sourceId: paper.sourceId, sourceTitle: "Attention",
        read: false, jump: { extractionId: paper.extractionId, sectionId: `${paper.extractionId}_p1`, spanId: `${paper.extractionId}_p1_1` },
        treatment: "explains", by: "judge",
      }] : [];
      return { extractionId: input.extractionId, sectionId: input.sectionId, status: sections.length ? "judged" : "none", search: null,
        checkableLearningObjectIds: [], learningObjects: sections.length ? [{ learningObjectId: "lo_softmax", title: "Softmax",
          sources: [{ sourceId: paper.sourceId, sourceTitle: "Attention", sections }] }] : [] };
    });
    // The paper's Guide carries a margin mark on a passage of its second section; its "check me" finds a question.
    answers.set("reader_guide_plan", (input) => {
      const base = FIXTURE_GUIDES[String(input.extractionId)];
      if (String(input.extractionId) !== paper.extractionId) return base;
      const note = "Connects to something you worked on.";
      return { ...base, personalized: true,
        cues: { version: "rw3a-guide-cues-v1", density: "normal", budgetPerSection: 2, onePerViewport: true, sourceOff: false, withheld: {},
          marks: [{ cueId: "cue_p2", kind: "revisit", spanId: PAPER_P2, sectionId: `${paper.extractionId}_p2`, learningObjectId: "lo_attn",
            learningObjectTitle: "Attention weights", targetId: "e1", rank: 0, sectionRank: 0, note, because: "Because: your answer",
            label: `Note on this paragraph: ${note}`, earlier: null }] } };
    });
    answers.set("reader_cue_action", (input) => ({ cueId: input.cueId, action: input.action, eventId: "ev", verdict: "same", ledgerId: null,
      check: input.action === "check_me" ? { status: "found", practiceItemId: "pi_attn", proposalId: null } : null }));
    answers.set("plan_learner_pick", () => ({ version: 1, enabled: false, step: null }));
    answers.set("get_practice_item", () => ({ prompt: "Q" }));
    return app;
}

/** Book and paper side by side (Ctrl+\ from the book), then the paper's margin mark's check me. */
async function pairThenCheckFromPaper(): Promise<string> {
    await openReaderPlace();
    await waitFor(() => expect(winOf("w_book")?.querySelector(`[data-span-id="${book.extractionId}_s1_1"]`)).toBeTruthy());
    fireEvent.click(winOf("w_book")!);
    fireEvent.keyDown(window, { key: "\\", ctrlKey: true });
    await settleDesk(0, 20);
    await waitFor(() => expect(paperWindow()).toBeTruthy());
    const pairedId = paperWindow()!.getAttribute("data-desk-window")!;
    expect(slotOf(paperWindow()!)).toEqual([...slotOf(winOf("w_book")!).slice(0, 2), "1"]);
    const mark = await waitFor(() => {
      const found = paperWindow()!.querySelector<HTMLElement>(`[data-cue-id="cue_p2"], [data-span-id="${PAPER_P2}"] [aria-label^="Note on this paragraph"]`);
      expect(found).toBeTruthy();
      return found!;
    });
    fireEvent.click(mark);
    fireEvent.click(await within(paperWindow()!).findByRole("button", { name: /check me/ }));
    return pairedId;
}

/** Still a pair: F6 goes to its partner and back. */
async function stillPaired(pairedId: string) {
    fireEvent.keyDown(window, { key: "F6" });
    await settleDesk(0, 6);
    expect(focusedWindow()).toBe("w_book");
    fireEvent.keyDown(window, { key: "F6" });
    await settleDesk(0, 6);
    expect(focusedWindow()).toBe(pairedId);
}

describe("back from a check begun in the paired book", () => {
  const sidecar = () => pairSidecar();

  it("returns to the pair, the paired window focused at the check's passage, and still a pair", async () => {
    sidecar();
    await openReaderPlace();
    await waitFor(() => expect(winOf("w_book")?.querySelector(`[data-span-id="${book.extractionId}_s1_1"]`)).toBeTruthy());
    fireEvent.click(winOf("w_book")!);
    fireEvent.keyDown(window, { key: "\\", ctrlKey: true });
    await settleDesk(0, 20);
    await waitFor(() => expect(paperWindow()).toBeTruthy());
    const pairedId = paperWindow()!.getAttribute("data-desk-window")!;
    expect(slotOf(paperWindow()!)).toEqual([...slotOf(winOf("w_book")!).slice(0, 2), "1"]);
    // The paper's margin mark: its check me, from the paired window.
    const mark = await waitFor(() => {
      const found = paperWindow()!.querySelector<HTMLElement>(`[data-cue-id="cue_p2"], [data-span-id="${PAPER_P2}"] [aria-label^="Note on this paragraph"]`);
      expect(found).toBeTruthy();
      return found!;
    });
    fireEvent.click(mark);
    fireEvent.click(await within(paperWindow()!).findByRole("button", { name: /check me/ }));
    const practice = await screen.findByTestId("practice-stand-in");
    expect(practice.getAttribute("data-item")).toBe("pi_attn");
    expect(document.querySelector("[data-desk-shell]")).toBeNull();
    // Back: the desks again, the pair as it was, the paired window focused at the check's passage.
    fireEvent.click(screen.getByRole("button", { name: "practice back" }));
    await settleDesk(0, 20);
    await waitFor(() => expect(focusedWindow()).toBe(pairedId));
    expect(slotOf(winOf(pairedId)!)).toEqual([...slotOf(winOf("w_book")!).slice(0, 2), "1"]);
    const passage = winOf(pairedId)!.querySelector<HTMLElement>(`[data-span-id="${PAPER_P2}"]`)!;
    await waitFor(() => expect(passage.style.borderLeft).toContain("var(--amber)"));
    // Still a pair: F6 goes to its partner and back.
    fireEvent.keyDown(window, { key: "F6" });
    await settleDesk(0, 6);
    expect(focusedWindow()).toBe("w_book");
    fireEvent.keyDown(window, { key: "F6" });
    await settleDesk(0, 6);
    expect(focusedWindow()).toBe(pairedId);
    expect(inputsOf("plan_learner_pick").map((input) => input.practiceItemId)).toEqual(["pi_attn"]);
  }, 30_000);
});

// -- a problem: worked on its pad, its feedback's back, and Today's resume ----------------------------------------

const FIRST = `${book.extractionId}_s1_1`;
const RECORD = { bookCounted: false, bookVisible: true, hints: 0, questionHints: 0, ownAttempt: true, line: "your own attempt", footer: "book open · help used: none", stuckNote: null };
const WORKBENCH_CONFIG = { workbench: { enabled: true, openSessionDays: 30, help: { enabled: true } }, hints: { adaptiveEnabled: true } };

function problem(sessionId: string, overrides: Record<string, unknown> = {}) {
  return {
    sessionId, practiceItemId: "pi_desk", stemMd: "Exercise 1.2 Show the weights sum to one.", importStatus: "none", importError: null,
    origin: "reader", entry: "work_through", parentSessionId: null, extractionId: book.extractionId, spanIds: [FIRST], sourceVisible: true,
    sourceHiddenAt: null, sourceShownAt: null, practiceSessionId: null, helpStyle: null, status: "open", attemptId: null,
    createdAt: "2026-11-23T09:00:00Z", updatedAt: "2026-11-23T09:00:00Z", closedAt: null, steps: [], lastEditedStepId: null,
    record: RECORD, parts: null, sourceId: book.sourceId, ...overrides,
  };
}

function workbenchAnswers(sessionId: string) {
  answers.set("reader_prompt_contract", () => contract());
  answers.set("workbench_for_source", () => ({ sessions: [], openSessionDays: 30 }));
  answers.set("workbench_open", (input) => ({ session: problem(input.entry === "resume" ? String(input.sessionId) : sessionId), resumed: input.entry === "resume" }));
  answers.set("workbench_get", (input) => ({ session: problem(String(input.sessionId)) }));
  answers.set("workbench_refresh_import", (input) => ({ session: problem(String(input.sessionId ?? sessionId)) }));
  answers.set("workbench_admit", (input) => ({ session: problem(String(input.sessionId ?? sessionId)) }));
  answers.set("workbench_help_state", () => ({ version: 1, check: null, hints: [], helpStyle: null, storedHelpStyle: "socratic", hintsEnabled: true }));
  answers.set("workbench_leave", (input) => ({ session: problem(String(input.sessionId ?? sessionId)) }));
}

const padsEl = (windowId = "w_pads") => document.querySelector<HTMLElement>(`[data-desk-window="${windowId}"]`);

describe("Today's resume of an unfinished problem", () => {
  function sidecar(state: never) {
    const app = appSidecar({ state, session: SESSION, config: WORKBENCH_CONFIG });
    vi.stubGlobal("localStorage", app.storage);
    workbenchAnswers("wb_res");
    answers.set("workbench_open_problems", () => ({ version: 1, problems: [{
      sessionId: "wb_res", status: "open", practiceItemId: "pi_desk", stemMd: "Exercise 1.2", origin: "reader", entry: "work_through",
      extractionId: book.extractionId, spanIds: [FIRST], importStatus: "none", sourceVisible: true, stepCount: 2,
      createdAt: "2026-11-22T00:00:00Z", updatedAt: "2026-11-22T00:00:00Z", unfinished: true, sourceId: book.sourceId }] }));
    return app;
  }

  async function resumeFromToday() {
    render(<App />);
    const thread = await screen.findByTestId("today-thread");
    fireEvent.click(within(thread).getByRole("button", { name: "resume ▸" }));
    await settleDesk(0, 30);
    await waitFor(() => expect(document.querySelector("[data-desk-shell]")).not.toBeNull());
  }

  it("lands on the problem's pad, on the desk in view, open, the book beside it", async () => {
    const app = sidecar(oneDesk([[BOOK_WINDOW as never], [PADS_WINDOW as never]]) as never);
    await resumeFromToday();
    await waitFor(() => expect(inputsOf("workbench_open").some((input) => input.entry === "resume" && input.sessionId === "wb_res")).toBe(true), { timeout: 5000 });
    await waitFor(() => expect(padsEl()?.querySelector('[data-problem-pad="wb_res"][data-problem-state="open"]')).not.toBeNull(), { timeout: 5000 });
    expect(within(padsEl()!).getByRole("region", { name: "workbench" })).toBeTruthy();
    // One pad for the problem, bound to its session; the book window keeps reading.
    await waitFor(() => expect(Object.values(app.server.pads).filter((each) => each.pad.kind === "problem")
      .map((each) => each.pad.workbenchSessionId)).toEqual(["wb_res"]), { timeout: 5000 });
    expect(winOf("w_book")!.querySelector("[data-workbench-pane]")).toBeNull();
  }, 30_000);

  it("lands on the desk the problem's pad lives on, that desk becoming the one in view", async () => {
    const state = oneDesk([[BOOK_WINDOW as never], [{ ...PADS_WINDOW, stack: [{ kind: "pad", padId: "fx_pad_running" }] } as never]]) as unknown as {
      desks: Array<Record<string, unknown>> };
    const other = { ...state.desks[0], deskId: "d_other", title: "other", position: "b", focusWindowId: "w_book2",
      slots: [{ slot: 0, windows: [{ ...BOOK_WINDOW, windowId: "w_book2" }] },
        { slot: 1, windows: [{ ...PADS_WINDOW, windowId: "w_pads2", stack: [{ kind: "pad", padId: "pad_wb_wb_res" }] }] }] };
    const { fixturePads } = await import("../fixtures/desks/pads");
    const pad = { version: 1, pad: { padId: "pad_wb_wb_res", kind: "problem", title: "Exercise 1.2", kept: true, homeDeskId: "d_other",
      workbenchSessionId: "wb_res", lessonId: null, version: 1, createdAt: "2026-11-22T00:00:00Z", updatedAt: "2026-11-22T00:00:00Z" }, blocks: [], anchors: [] };
    const app = appSidecar({ state: { ...state, desks: [state.desks[0], other] } as never, pads: [...fixturePads(), pad as never], session: SESSION, config: WORKBENCH_CONFIG });
    vi.stubGlobal("localStorage", app.storage);
    workbenchAnswers("wb_res");
    answers.set("workbench_open_problems", () => ({ version: 1, problems: [{
      sessionId: "wb_res", status: "open", practiceItemId: "pi_desk", stemMd: "Exercise 1.2", origin: "reader", entry: "work_through",
      extractionId: book.extractionId, spanIds: [FIRST], importStatus: "none", sourceVisible: true, stepCount: 2,
      createdAt: "2026-11-22T00:00:00Z", updatedAt: "2026-11-22T00:00:00Z", unfinished: true, sourceId: book.sourceId }] }));
    // Every window the problem's pad is ever shown in, from the click on.
    const shownIn = new Set<string>();
    const watch = new MutationObserver(() => {
      for (const el of document.querySelectorAll("[data-problem-pad]")) shownIn.add(el.closest("[data-desk-window]")?.getAttribute("data-desk-window") ?? "?");
    });
    watch.observe(document.body, { subtree: true, childList: true, attributes: true });
    await resumeFromToday();
    await waitFor(() => expect(padsEl("w_pads2")?.querySelector('[data-problem-pad="wb_res"][data-problem-state="open"]')).not.toBeNull(), { timeout: 5000 });
    expect(Object.values(app.server.pads).filter((each) => each.pad.kind === "problem")).toHaveLength(1);
    watch.disconnect();
    expect([...shownIn]).toEqual(["w_pads2"]);
    // The desk it lives on is the one in view, and the desk the learner was on never took the pad into its stack.
    const current = document.querySelector('nav[aria-label="desks"] button[aria-current="true"]')?.textContent;
    expect(current).toBe("other");
    const stacked = inputsOf("desk_apply").flatMap((input) => (input.ops as Array<Record<string, unknown>>) ?? [])
      .filter((op) => JSON.stringify(op).includes("pad_wb_wb_res"));
    expect(stacked).toEqual([]);
    expect(app.server.state().desks[0].slots.flatMap((slot) => slot.windows.flatMap((window) => (window as { stack?: Array<{ padId?: string }> }).stack ?? []))
      .some((entry) => entry.padId === "pad_wb_wb_res")).toBe(false);
  }, 30_000);
});

describe("back from a problem opened from the paired book", () => {
  async function submitFromPaper(): Promise<string> {
    pairSidecar({ config: WORKBENCH_CONFIG, withPads: true });
    workbenchAnswers("wb_pair");
    const onPaper = (sessionId: string, overrides: Record<string, unknown> = {}) => problem(sessionId, {
      extractionId: paper.extractionId, spanIds: [PAPER_P2], sourceId: paper.sourceId, practiceItemId: "pi_attn", entry: "check", ...overrides });
    let submitted = false;
    answers.set("workbench_open", (input) => ({ session: onPaper(String(input.sessionId ?? "wb_pair"), submitted ? { status: "submitted", attemptId: "att_pair" } : {}),
      resumed: input.entry === "resume" }));
    answers.set("workbench_get", () => ({ session: onPaper("wb_pair", submitted ? { status: "submitted", attemptId: "att_pair" } : {}) }));
    answers.set("workbench_for_source", () => ({ sessions: [], openSessionDays: 30 }));
    answers.set("workbench_submit", () => {
      submitted = true;
      return { version: 1, practiceSession: null, session: onPaper("wb_pair", { status: "submitted", attemptId: "att_pair" }), attempt: { attemptId: "att_pair" } };
    });
    answers.set("get_practice_item", () => ({ prompt: "Why does attention normalize its weights?" }));
    const pairedId = await pairThenCheckFromPaper();
    // The check is worked on the desk's problem pad, the paper window keeps reading.
    const pad = await waitFor(() => {
      const found = padsEl()?.querySelector<HTMLElement>('[data-problem-pad="wb_pair"][data-problem-state="open"]');
      expect(found).toBeTruthy();
      return found!;
    }, { timeout: 5000 });
    expect(winOf(pairedId)!.querySelector("[data-workbench-pane]")).toBeNull();
    fireEvent.change(within(pad).getAllByRole("textbox")[0], { target: { value: "So they sum to one." } });
    await settleDesk(0, 6);
    fireEvent.click(within(pad).getByRole("button", { name: /^submit/i }));
    const feedback = await screen.findByTestId("feedback-stand-in");
    expect(feedback.getAttribute("data-attempt")).toBe("att_pair");
    return pairedId;
  }

  it("feedback's back to the book returns to the pair, the paired window focused at the problem's passage, its pad showing it submitted", async () => {
    const pairedId = await submitFromPaper();
    fireEvent.click(screen.getByRole("button", { name: "back to the book" }));
    await settleDesk(0, 20);
    await waitFor(() => expect(focusedWindow()).toBe(pairedId));
    expect(slotOf(winOf(pairedId)!)).toEqual([...slotOf(winOf("w_book")!).slice(0, 2), "1"]);
    const passage = winOf(pairedId)!.querySelector<HTMLElement>(`[data-span-id="${PAPER_P2}"]`)!;
    await waitFor(() => expect(passage.style.borderLeft).toContain("var(--amber)"));
    await waitFor(() => expect(padsEl()?.querySelector('[data-problem-pad="wb_pair"][data-problem-state="submitted"]')).not.toBeNull(), { timeout: 5000 });
    await stillPaired(pairedId);
  }, 30_000);

  it("feedback's back returns to the problem: the paired window at its passage, the problem shown on its pad, submitted; the pair kept", async () => {
    const pairedId = await submitFromPaper();
    fireEvent.click(screen.getByRole("button", { name: "feedback back" }));
    await settleDesk(0, 20);
    await waitFor(() => expect(focusedWindow()).toBe(pairedId));
    const passage = winOf(pairedId)!.querySelector<HTMLElement>(`[data-span-id="${PAPER_P2}"]`)!;
    await waitFor(() => expect(passage.style.borderLeft).toContain("var(--amber)"));
    // The problem, read-only, on its pad in view (never a working posture over the paper).
    const pad = await waitFor(() => {
      const found = padsEl()?.querySelector<HTMLElement>('[data-problem-pad="wb_pair"][data-problem-state="submitted"]');
      expect(found).toBeTruthy();
      return found!;
    }, { timeout: 5000 });
    expect(within(pad).queryByRole("button", { name: /^submit/i })).toBeNull();
    expect(winOf(pairedId)!.querySelector("[data-workbench-pane]")).toBeNull();
    expect(slotOf(winOf(pairedId)!)).toEqual([...slotOf(winOf("w_book")!).slice(0, 2), "1"]);
    await stillPaired(pairedId);
  }, 30_000);
});

// -- leaving the desks while skimming --------------------------------------------------------------------------------

describe("the leave-time offer after the desks", () => {
  const windowOf = (windowId: string, source: { sourceId: string; extractionId: string }) => ({
    windowId, pane: 0, kind: "source", active: true, view: {}, content: { kind: "source", sourceId: source.sourceId, extractionId: source.extractionId, view: "render" },
  });

  function sidecar() {
    const app = appSidecar({ state: oneDesk([[windowOf("w_book", book) as never], [windowOf("w_paper", paper) as never]]), session: SESSION,
      config: { recap: { enabled: true, wrapUpEnabled: true } } });
    vi.stubGlobal("localStorage", app.storage);
    answers.set("reader_prompt_contract", () => contract());
    answers.set("reader_set_mode", (input) => ({ mode: input.mode }));
    return app;
  }

  async function focusOn(windowId: string) {
    fireEvent.mouseDown(winOf(windowId)!.closest(".desk-window")!.querySelector(".desk-pane-head")!);
    fireEvent.click(winOf(windowId)!.closest(".desk-window")!.querySelector(".desk-pane-head")!);
    await settleDesk(0, 4);
    await waitFor(() => expect(focusedWindow()).toBe(windowId));
  }

  async function chooseMode(windowId: string, mode: "skim quickly" | "read closely") {
    const bar = await waitFor(() => {
      const found = winOf(windowId)?.querySelector<HTMLElement>("[data-window-source-bar]");
      expect(found).toBeTruthy();
      return found!;
    });
    fireEvent.keyDown(within(bar).getByRole("combobox"), { key: "Enter" });
    fireEvent.mouseDown(await within(document.body).findByRole("option", { name: mode }));
    await settleDesk(0, 6);
  }

  async function leaveForToday() {
    await press({ key: "1", altKey: true });
    await settleDesk(0, 6);
  }

  async function backToDesks() {
    await press({ key: "3", altKey: true });
    await settleDesk(0, 20);
    await waitFor(() => expect(document.querySelector("[data-desk-shell]")).not.toBeNull());
  }

  it("is held while the book being read on a desk is skimmed, and offered once it is read closely", async () => {
    sidecar();
    await openReaderPlace();
    await focusOn("w_book");
    await chooseMode("w_book", "skim quickly");
    expect(inputsOf("reader_set_mode").slice(-1)[0]).toEqual({ mode: "skim", extractionId: book.extractionId });
    await leaveForToday();
    expect(screen.queryByTestId("wrap-up-offer")).toBeNull();
    await backToDesks();
    await chooseMode("w_book", "read closely");
    await leaveForToday();
    expect(screen.getByTestId("wrap-up-offer")).toBeTruthy();
  }, 30_000);

  it("hears the book being read: another window skimmed does not hold it", async () => {
    sidecar();
    await openReaderPlace();
    await focusOn("w_paper");
    await chooseMode("w_paper", "skim quickly");
    // The learner goes back to the book, read closely: that is the book being read.
    await focusOn("w_book");
    await leaveForToday();
    expect(screen.getByTestId("wrap-up-offer")).toBeTruthy();
  }, 30_000);
});

// -- today's plan reading --------------------------------------------------------------------------------------------

describe("today's plan reading on the desks", () => {
  it("opens the plan's book at its section on the desk in view, under the plan's banner, and back to the plan ends the block", async () => {
    const reading = { sourceId: paper.sourceId, extractionId: paper.extractionId, sectionId: `${paper.extractionId}_p2`, sectionTitle: "2 Why divide by the square root",
      wordsLeft: 400, partial: false, startSpanId: `${paper.extractionId}_p2_1` };
    const app = appSidecar({ state: oneDesk([[BOOK_WINDOW as never]]), session: SESSION, config: { plan: { enabled: true } } });
    vi.stubGlobal("localStorage", app.storage);
    answers.set("reader_prompt_contract", () => contract());
    const block = { id: "blk_r", ordinal: 1, lane: "maintain", action: "reading", subtype: null, chosenBy: "lane_quota", why: "read the next section",
      whyKind: "computed", fallback: false, estMinutes: 8, status: "current", startedAt: null, endedAt: null, outcome: null, reading,
      learningObjectTitles: ["Attention"], items: [], displacedCount: 0 };
    const body = { id: "plan_1", localDate: "2026-11-23", kind: "normal", status: "open", stopReason: null, parentPlanId: null, minutesBudget: 25,
      rememberedMinutes: 25, minutesSource: "carried", minuteChoices: [10, 15, 25], minutesLeft: 25,
      split: { rule: "split_v1", line: "25 min", lanesAllowed: ["maintain"], requestedMinutes: 0, lanes: [] },
      admission: { admittedCount: 0, exemptRequests: 0, stoppedBy: null, floorApplied: false, reviewLoadPerDay: null, ceilingMinutes: null, override: null },
      blocks: [block], currentBlockId: "blk_r", projected: [], blockCountEstimate: 1, firstBlock: null, nextStep: null,
      totals: { plannedMinutes: 8, plannedItems: 0, doneItems: 0, skippedItems: 0, displacedItems: 0, readingBlocks: 1, readingBlocksEnded: 0, estMinutesDone: 0, actualMinutes: 0 },
      reentry: null, source: null, chooser: null };
    const daily = { version: 1, enabled: true, headlineEnabled: false, localDate: "2026-11-23", plan: body,
      day: { plans: 1, kinds: ["normal"], complete: false }, streak: { current: 1, activeToday: false, longest: 1 } };
    answers.set("get_daily_plan", () => daily);
    answers.set("next_plan_item", () => ({ ...daily, step: { kind: "reading", planId: "plan_1", blockId: "blk_r", blockOrdinal: 1, estMinutes: 8, boundary: false, reading } }));
    answers.set("plan_reading_ended", () => ({ version: 1 }));
    render(<App />);
    await screen.findByRole("navigation", { name: "Places" });
    await settleDesk(0, 10);
    await press({ key: "Enter" });
    await settleDesk(0, 30);
    const banner = await screen.findByTestId("plan-reading-banner");
    expect(banner.textContent).toContain("2 Why divide by the square root");
    // The desks, not the old Reader: the plan's book opened beside the book on the desk in view, focused at the section.
    await waitFor(() => expect(document.querySelector("[data-desk-shell]")).not.toBeNull());
    await waitFor(() => expect(paperWindow()).toBeTruthy());
    expect(focusedWindow()).toBe(paperWindow()!.getAttribute("data-desk-window"));
    const start = paperWindow()!.querySelector<HTMLElement>(`[data-span-id="${paper.extractionId}_p2_1"]`)!;
    await waitFor(() => expect(start.style.borderLeft).toContain("var(--amber)"));
    expect(winOf("w_book")).not.toBeNull();
    fireEvent.click(within(banner).getByRole("button"));
    await settleDesk(0, 10);
    expect(inputsOf("plan_reading_ended")[0]).toMatchObject({ outcome: "left_reader" });
    expect(screen.queryByTestId("plan-reading-banner")).toBeNull();
  }, 30_000);
});

// -- an exercise picked in a book window, with no session yet ----------------------------------------------------------

describe("an exercise used from a book window with no session yet", () => {
  it("starts the session and the exercise is worked on the desk's problem pad", async () => {
    const SECOND = `${book.extractionId}_s1_2`;
    const app = appSidecar({ state: oneDesk([[BOOK_WINDOW as never], [PADS_WINDOW as never]]), session: null, config: WORKBENCH_CONFIG });
    vi.stubGlobal("localStorage", app.storage);
    workbenchAnswers("wb_ex");
    answers.set("reader_prompt_contract", () => contract({ libraryAsk: { expandGraph: false, personalizedDefault: true, compare: true },
      libraryExercises: { fallback: false } }));
    answers.set("start_session", () => ({ ...SESSION, sessionId: "ps_new" }));
    const done = <T,>(result: T, kind: string) => ({ jobId: `ljob_${kind}`, kind, askId: "la_1", state: "done" as const, result });
    answers.set("reader_library_ask", () => done({ askId: "la_1", query: "softmax", entry: "where_else_explained", status: "ok", policy: "reading",
      personalized: true, basis: "keyword + meaning", learningObjectIds: [], extractionId: book.extractionId, anchorSpanIds: [FIRST],
      hits: [{ key: `${paper.extractionId}:${paper.extractionId}_p1_1`, extractionId: paper.extractionId, spanId: `${paper.extractionId}_p1_1`,
        sourceId: paper.sourceId, sourceTitle: "Attention", section: "1", page: 1, text: "Scores pass through a softmax.", role: "definition",
        group: "Foundation", expansion: null, learningObjectIds: [], authorship: "source", label: "source-authored" }],
      groups: { sources: [{ sourceId: paper.sourceId, sourceTitle: "Attention", groups: [{ group: "Foundation", keys: [`${paper.extractionId}:${paper.extractionId}_p1_1`] }] }],
        expansions: [] }, expansions: [], expandGraph: false, sourceCount: 1, passageCount: 1 }, "ask"));
    answers.set("reader_library_ask_notes", () => done({ askId: "la_1", status: "judged", notes: [], order: [] }, "notes"));
    answers.set("record_proposal_impressions", () => ({ recorded: 1 }));
    answers.set("reader_intent_outcome", () => ({ routingId: "r", recorded: true }));
    answers.set("find_practice", () => ({ version: 1, status: "ok", proposalId: "pp_1", items: [], sourceExercises: [{
      kind: "source_exercise", key: "srcex:here", extractionId: book.extractionId, spanIds: [SECOND], sourceId: book.sourceId, revisionId: "rev",
      sourceTitle: "Softmax", label: "Exercise 1", page: 4, statement: "Show the weights sum to one.", rationale: null,
      labelLine: "From the book · not yet in your practice" }] }));
    answers.set("reader_exercise_candidates", () => done({ version: 1, proposalId: "pp_1", withheld: 0, candidates: [{ key: "srcex:here",
      extractionId: book.extractionId, spanIds: [], sourceId: book.sourceId, revisionId: "rev",
      exposure: { exposed: false, reasons: [], label: null, note: null, offeredAs: "check_on_your_own", exposureRuleVersion: "reading_exposure_v1" } }] },
      "exercise_candidates"));
    await openReaderPlace();
    const win = winOf("w_book")!;
    const block = await waitFor(() => {
      const found = win.querySelector<HTMLElement>(`[data-span-id="${FIRST}"]`);
      expect(found).toBeTruthy();
      return found!;
    });
    const range = document.createRange();
    range.selectNodeContents(block);
    window.getSelection()!.removeAllRanges();
    window.getSelection()!.addRange(range);
    fireEvent.mouseUp(block);
    fireEvent.keyDown(await within(win).findByRole("textbox", { name: "What do you want to do with this?" }), { key: "Tab" });
    fireEvent.click(within(await within(win).findByRole("group", { name: "what do you want to do?" })).getByRole("button", { name: "where else is this explained?" }));
    await settleDesk(0, 10);
    fireEvent.click(await within(win).findByRole("button", { name: /practice this question/ }));
    await settleDesk(0, 10);
    const [card] = await within(win).findAllByTestId("exercise-candidate");
    fireEvent.click(within(card).getByRole("button", { name: /use this one/ }));
    await settleDesk(0, 20);
    // The implicit start: one session, then the exercise opens through the workbench and lands on the pad.
    await waitFor(() => expect(inputsOf("start_session")).toHaveLength(1));
    await waitFor(() => expect(inputsOf("workbench_open").length).toBeGreaterThan(0), { timeout: 5000 });
    await waitFor(() => expect(padsEl()?.querySelector('[data-problem-pad="wb_ex"][data-problem-state="open"]')).not.toBeNull(), { timeout: 5000 });
    expect(winOf("w_book")!.querySelector("[data-workbench-pane]")).toBeNull();
    expect(document.querySelector("[data-desk-shell]")).not.toBeNull();
  }, 30_000);
});
