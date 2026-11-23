// Teacher lessons as windows and stack tabs (spec §11.1): an opening shows at once in the stack and is stored there
// when its turn returns, without remounting the window that opened it; a finished lesson reopened is its review
// (lesson.view only: no turn, no control that would start one); a paused window reads nothing and starts no turn;
// the learner's notes under a lesson go to its lesson_additions pad through the pad ops; the notebook seam; the tab's
// words. No model is called: lesson.turn and lesson.view are fakes.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { LessonSummaryDto, LessonTurnInput, LessonViewDto, PadOpDto, PadStackEntryDto } from "../../../api/dto";
import { FixtureDeskServer } from "../../../fixtures/desks/workspace";
import { FIXTURE_ADDITIONS_PAD_ID, FIXTURE_LESSON_ID, FIXTURE_LESSON_SUMMARY, FIXTURE_LESSON_VIEW, fixtureAdditionsPad } from "../../../fixtures/desks/lessons";
import { fixturePads } from "../../../fixtures/desks/pads";
import type { Timers } from "../keys/router";
import { DIRECT_HUB, WindowScope, type WindowState } from "../lifecycle";
import { DeskStore } from "../store";
import { PadsHostContext, PendingFigures, type PadsApi, type PadsHost } from "../pads/host";
import { PadStackWindow } from "../pads/PadStackWindow";
import { LessonDesk, type LessonsHost, type Opening } from "./host";
import { PathLessonRow } from "./PathLessonRow";

const api = vi.hoisted(() => ({
  lessonTurn: vi.fn(),
  lessonView: vi.fn(),
  lessonActivity: vi.fn(async () => ({ recorded: 0, enabled: false })),
}));
vi.mock("../../../api/client", () => ({ api }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

class ManualTimers implements Timers {
  queue: Array<{ fn: () => void; id: number }> = [];
  private next = 1;
  set(fn: () => void): unknown {
    const id = this.next++;
    this.queue.push({ fn, id });
    return id;
  }
  clear(handle: unknown): void {
    this.queue = this.queue.filter((entry) => entry.id !== handle);
  }
  now(): number {
    return 0;
  }
  fire(): void {
    const due = this.queue;
    this.queue = [];
    for (const entry of due) entry.fn();
  }
}

function quietPadsApi(): PadsApi {
  const none = async () => ({}) as never;
  return {
    padProposals: async (input) => ({ version: 1, padId: input.padId, proposals: [] }) as never,
    proposalLabel: none, padSubmitBlock: none, carriedCarry: none, requestTeachBack: none, passageUnionRange: none,
    authorPracticeItem: none, workbenchOpenProblems: none, submitTeachBackTurn: none, getSession: none, passageContent: none,
  };
}

let minted = 0;

function mount(options: { stack: PadStackEntryDto[]; state?: WindowState; summaries?: LessonSummaryDto[]; withAdditions?: boolean; host?: Partial<LessonsHost> }) {
  const server = new FixtureDeskServer(undefined, [...fixturePads(), ...(options.withAdditions ? [fixtureAdditionsPad()] : [])]);
  const timers = new ManualTimers();
  const store = new DeskStore("me", {
    state: async () => server.state(),
    apply: async (input) => server.apply(input),
    applyPad: async (input) => server.applyPad(input),
    padGet: async ({ padId }) => server.padGet(padId),
  }, timers);
  const listed: Array<{ lessonIds?: string[]; learningObjectIds?: string[] }> = [];
  const summaries = options.summaries ?? [FIXTURE_LESSON_SUMMARY];
  const opened: Array<{ opening: Opening; lessonId: string }> = [];
  const desk = new LessonDesk({
    list: async (input) => {
      listed.push(input);
      return { lessons: summaries.filter((each) => !input.lessonIds || input.lessonIds.includes(each.lessonId)) };
    },
  }, (opening, lessonId) => opened.push({ opening, lessonId }));
  const lessons: LessonsHost = { desk, onError: vi.fn(), openLesson: vi.fn(), ...options.host };
  const host: PadsHost = {
    store, deskId: "fx_desk_softmax", mintId: (prefix) => `${prefix}_${++minted}`, today: () => "2026-11-23", api: quietPadsApi(),
    practiceSessionId: null, openPassage: vi.fn(), openSearch: vi.fn(), askAbout: vi.fn(), toast: vi.fn(), setView: vi.fn(),
    sourcePieces: () => [], register: () => undefined, carry: vi.fn(), figures: new PendingFigures(), addToStack: vi.fn(), lessons,
  };
  const ui = (state: WindowState, stack: PadStackEntryDto[]) => (
    <WindowScope lifecycle={{ windowId: "w1", state }} hub={DIRECT_HUB}>
      <PadsHostContext.Provider value={host}>
        <PadStackWindow windowId="w1" stack={stack} view={{}} />
      </PadsHostContext.Provider>
    </WindowScope>
  );
  const view = render(ui(options.state ?? "active", options.stack));
  const flush = async () => {
    for (let i = 0; i < 4; i += 1) {
      timers.fire();
      await act(async () => {
        await store.flush();
      });
    }
  };
  return { server, store, desk, lessons, opened, listed, flush, rerender: (state: WindowState, stack = options.stack) => view.rerender(ui(state, stack)) };
}

const sentPadOps = (server: FixtureDeskServer): PadOpDto[] => server.padBatches.flatMap((batch) => batch.ops as PadOpDto[]);
const lessonCalls = () => ({ turns: api.lessonTurn.mock.calls.length, views: api.lessonView.mock.calls.length });

beforeEach(() => {
  api.lessonTurn.mockReset();
  api.lessonView.mockReset();
  api.lessonView.mockImplementation(async () => FIXTURE_LESSON_VIEW);
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

const PADS: PadStackEntryDto[] = [{ kind: "pad", padId: "fx_pad_running" }, { kind: "pad", padId: "fx_pad_deriving" }];
const WITH_LESSON: PadStackEntryDto[] = [...PADS, { kind: "lesson", lessonId: FIXTURE_LESSON_ID }];

describe("a Teacher lesson as a stack tab", () => {
  it("reopened finished, it is its review: lesson.view only, the feed as recorded, no turn and nothing that would start one", async () => {
    mount({ stack: WITH_LESSON });
    await screen.findByText("If every score goes up by 3, what happens to the loss?");
    const lesson = screen.getByTestId("lesson-view");
    expect(within(lesson).getByTestId("lesson-learner").textContent).toContain("the log-sum-exp goes up by 3");
    expect(within(lesson).getByTestId("lesson-check-result").textContent).toContain("correct");
    expect(within(lesson).getByTestId("lesson-close").textContent).toContain("Lesson done.");
    expect(api.lessonView).toHaveBeenCalledWith({ lessonId: FIXTURE_LESSON_ID });
    expect(api.lessonTurn).not.toHaveBeenCalled();
    // Nothing to answer, reply to or stop.
    expect(within(lesson).queryByRole("textbox")).toBeNull();
    expect(within(lesson).queryByText("Stop the lesson")).toBeNull();
    expect(within(lesson).queryByText("Close")).toBeNull();
    // Its modes: review (on) and your additions; redo and extend are not shown before RD9c.
    const modes = screen.getByRole("group", { name: "lesson modes" });
    expect(within(modes).getAllByRole("button").map((button) => button.textContent)).toEqual(["review", "your additions"]);
    expect(within(modes).getByText("review").getAttribute("aria-pressed")).toBe("true");
    expect(within(modes).getByText("your committed answers and the reveals, as you left them")).toBeTruthy();
  });

  it("its tab reads “Teacher lesson · <topic>” and “made <date> from your <what>”", async () => {
    mount({ stack: WITH_LESSON });
    const tab = await waitFor(() => {
      const found = document.querySelector<HTMLElement>(`[data-pad-tab="lesson:${FIXTURE_LESSON_ID}"]`);
      expect(found?.textContent).toContain("softmax + cross-entropy");
      return found as HTMLElement;
    });
    expect(tab.querySelector(".tt")?.textContent).toBe("Teacher lesson · softmax + cross-entropy");
    expect(tab.querySelector(".tm")?.textContent).toBe("made 21 Nov from your question");
  });

  it("a paused stack reads no lesson and starts no turn; live again, it reads the lesson once", async () => {
    const { desk, rerender } = mount({ stack: WITH_LESSON, state: "hidden" });
    desk.open("w1", { kind: "open", entry: "reader_selection", selection: { extractionId: "fx_ext_softmax", spanIds: ["s1"] } });
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 20));
    });
    expect(lessonCalls()).toEqual({ turns: 0, views: 0 });
    api.lessonTurn.mockImplementation(() => new Promise(() => undefined));
    rerender("visible");
    await waitFor(() => expect(lessonCalls()).toEqual({ turns: 1, views: 1 }));
    expect(api.lessonView).toHaveBeenCalledWith({ lessonId: FIXTURE_LESSON_ID });
  });

  it("a question being prepared is checked back on only while the window is live", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const preparing: LessonViewDto = { ...FIXTURE_LESSON_VIEW, closed: false, closeReason: null, feed: FIXTURE_LESSON_VIEW.feed.slice(0, 1),
      probe: { probeRef: "pr1", status: "preparing", label: "Preparing a question on this…", teachAnyway: true } as never };
    api.lessonView.mockImplementation(async () => preparing);
    const { rerender } = mount({ stack: WITH_LESSON });
    await screen.findByText("Preparing a question on this…");
    const before = lessonCalls().views;
    rerender("offscreen");
    await act(async () => {
      vi.advanceTimersByTime(30_000);
    });
    expect(lessonCalls().views).toBe(before);
    rerender("active");
    await act(async () => {
      vi.advanceTimersByTime(30_000);
    });
    expect(lessonCalls().views).toBeGreaterThan(before);
  });
});

describe("opening a lesson into a stack", () => {
  it("shows its tab at once, and once its turn returns it is stored in the stack and keeps its window (no second read)", async () => {
    const { desk, opened, rerender } = mount({ stack: PADS });
    let answer: (view: LessonViewDto) => void = () => undefined;
    api.lessonTurn.mockImplementation((input: LessonTurnInput) => new Promise<LessonViewDto>((resolve) => {
      answer = resolve;
      void input;
    }));
    act(() => {
      desk.open("w1", { kind: "open", entry: "reader_selection", selection: { extractionId: "fx_ext_softmax", spanIds: ["fx_ext_softmax_s1_3"] } });
    });
    const tab = await waitFor(() => document.querySelector<HTMLElement>('[data-pad-tab^="lesson-opening:"]') as HTMLElement);
    expect(tab.querySelector(".tt")?.textContent).toBe("Teacher lesson · your selection");
    expect(tab.querySelector(".tm")?.textContent).toBe("opening…");
    await waitFor(() => expect(api.lessonTurn).toHaveBeenCalledTimes(1));
    expect(api.lessonTurn.mock.calls[0][0]).toMatchObject({ action: "open", entry: "reader_selection", selection: { extractionId: "fx_ext_softmax", spanIds: ["fx_ext_softmax_s1_3"] } });
    expect(screen.getByTestId("lesson-wait")).toBeTruthy();
    // While its turn is in flight there is nothing to let go.
    expect(screen.queryByRole("button", { name: "let it go" })).toBeNull();
    const view: LessonViewDto = { ...FIXTURE_LESSON_VIEW, lessonId: "les_new", closed: false, closeReason: null, feed: FIXTURE_LESSON_VIEW.feed.slice(0, 1) };
    await act(async () => {
      answer(view);
    });
    expect(opened.map((each) => each.lessonId)).toEqual(["les_new"]);
    // The shell's add_to_stack lands: the stack now holds the lesson, and the same window goes on showing it.
    rerender("active", [...PADS, { kind: "lesson", lessonId: "les_new" }]);
    await screen.findByText(/Each score becomes a weight/);
    expect(document.querySelector('[data-pad-tab="lesson:les_new"]')).toBeTruthy();
    expect(document.querySelector('[data-pad-tab^="lesson-opening:"]')).toBeNull();
    expect(lessonCalls()).toEqual({ turns: 1, views: 0 });
    // An open lesson is taken, not reviewed: its first mode says so, and the reply box is there.
    expect(within(screen.getByRole("group", { name: "lesson modes" })).getAllByRole("button")[0].textContent).toBe("lesson");
    expect(screen.getByRole("textbox", { name: "Reply to the teacher" })).toBeTruthy();
  });

  it("an opening that failed outright can be let go", async () => {
    const { desk } = mount({ stack: PADS });
    api.lessonTurn.mockImplementation(async () => {
      throw { code: "validation_error", message: "nothing to teach there" };
    });
    act(() => {
      desk.open("w1", { kind: "open", entry: "learning_object", learningObjectIds: ["lo1"], title: "eigenvalues" });
    });
    const letGo = await screen.findByRole("button", { name: "let it go" });
    fireEvent.click(letGo);
    await waitFor(() => expect(document.querySelector('[data-pad-tab^="lesson-opening:"]')).toBeNull());
  });
});

describe("your additions under a lesson", () => {
  it("the first note creates the lesson's lesson_additions pad and writes the block through the pad ops", async () => {
    const summaries = [{ ...FIXTURE_LESSON_SUMMARY, additionsPadId: null }];
    const { server, store, desk, flush } = mount({ stack: WITH_LESSON, summaries });
    await screen.findByText("If every score goes up by 3, what happens to the loss?");
    fireEvent.click(within(screen.getByRole("group", { name: "lesson modes" })).getByText("your additions"));
    expect(screen.getByText(/your own notes under this lesson/)).toBeTruthy();
    fireEvent.click(screen.getByText("write under this lesson"));
    const editor = await waitFor(() => document.querySelector<HTMLTextAreaElement>("[data-pad-editor] textarea") as HTMLTextAreaElement);
    fireEvent.change(editor, { target: { value: "my note on the shift" } });
    fireEvent.keyDown(editor, { key: "Enter" });
    await flush();
    const padId = desk.additionsFor(FIXTURE_LESSON_ID) as string;
    expect(padId).toBeTruthy();
    const ops = sentPadOps(server);
    expect(ops[0]).toMatchObject({ op: "create_pad", kind: "lesson_additions", lessonId: FIXTURE_LESSON_ID });
    expect(ops.some((op) => op.op === "insert_block")).toBe(true);
    expect(server.padGet(padId).pad.lessonId).toBe(FIXTURE_LESSON_ID);
    expect(store.pads[padId].blocks.map((block) => block.bodyMd)).toContain("my note on the shift");
  });

  it("a lesson held for a due check gives its additions pad no topic in the stored title", async () => {
    const summaries = [{ ...FIXTURE_LESSON_SUMMARY, additionsPadId: null, title: "a topic with a cold check due", goal: null, held: true }];
    const { server, flush } = mount({ stack: WITH_LESSON, summaries });
    await screen.findByText("If every score goes up by 3, what happens to the loss?");
    fireEvent.click(within(screen.getByRole("group", { name: "lesson modes" })).getByText("your additions"));
    fireEvent.click(screen.getByText("write under this lesson"));
    const editor = await waitFor(() => document.querySelector<HTMLTextAreaElement>("[data-pad-editor] textarea") as HTMLTextAreaElement);
    fireEvent.change(editor, { target: { value: "a note" } });
    fireEvent.keyDown(editor, { key: "Enter" });
    await flush();
    expect(sentPadOps(server)[0]).toMatchObject({ op: "create_pad", kind: "lesson_additions", title: "your additions" });
  });

  it("notes already under a lesson show beneath its review", async () => {
    mount({ stack: WITH_LESSON, withAdditions: true });
    await screen.findByText("why does the gradient not depend on which wrong class got the mass?");
    expect(screen.getByText("your additions under this lesson")).toBeTruthy();
    expect(document.querySelector(`[data-block="fx_b_add1"]`)?.getAttribute("data-emits")).toBe("yes");
    void FIXTURE_ADDITIONS_PAD_ID;
  });
});

describe("the notebook seam", () => {
  it("a notebook lesson shows the host's frame instead of the lesson; any other lesson shows itself", async () => {
    api.lessonView.mockImplementation(async () => ({ ...FIXTURE_LESSON_VIEW, medium: "notebook" }));
    mount({ stack: WITH_LESSON, host: { notebookFrame: (lessonId) => <div data-testid="nb-frame">{lessonId}</div> } });
    expect((await screen.findByTestId("nb-frame")).textContent).toBe(FIXTURE_LESSON_ID);
  });
});

describe("the path view's Teacher lesson row", () => {
  it("names the newest lesson on the LO and opens it; an LO with none shows no row", async () => {
    const desk = new LessonDesk({ list: async () => ({ lessons: [FIXTURE_LESSON_SUMMARY] }) }, () => undefined);
    const onOpen = vi.fn();
    render(<div><PathLessonRow desk={desk} learningObjectId="fx_lo_softmax" onOpen={onOpen} /><PathLessonRow desk={desk} learningObjectId="fx_lo_other" onOpen={onOpen} /></div>);
    const row = await screen.findByRole("button", { name: /Teacher lesson/ });
    expect(row.textContent).toContain("softmax + cross-entropy");
    expect(row.textContent).toContain("made 21 Nov from your question");
    expect(row.textContent).toContain("review it");
    expect(document.querySelectorAll("[data-gp-lesson]").length).toBe(1);
    fireEvent.click(row);
    expect(onOpen).toHaveBeenCalledWith(FIXTURE_LESSON_ID);
  });
});
