// Every lesson entry on the desks opens a window on the current desk (spec §11.1, RD9a's acceptance): a lesson opened
// from a selection lands in the desk's stack (one add_to_stack once its turn returns, not the lesson screen); a
// stored lesson the app asks for is added to the stack without a turn; a window whose content is a lesson shows it
// as a stack of one. jsdom lays nothing out; the harness shows the real webview.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { DeskOpDto, LessonViewDto } from "../../../api/dto";
import { FixtureDeskServer, fixtureDeskState } from "../../../fixtures/desks/workspace";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { FIXTURE_LESSON_ID, FIXTURE_LESSON_SUMMARY, FIXTURE_LESSON_VIEW } from "../../../fixtures/desks/lessons";
import { DeskShell, type CompanionTransport, type DeskTransport, type PadsTransport } from "../DeskShell";
import type { GoalTransport } from "../goal/controller";
import type { LessonEntry } from "../../LessonView";

const api = vi.hoisted(() => ({
  // No inline check is open (the desks read it before showing anything).
  checkOpenInline: async () => ({ administration: null }),
  lessonTurn: vi.fn(),
  lessonView: vi.fn(),
  lessonActivity: vi.fn(async () => ({ recorded: 0, enabled: false })),
}));
vi.mock("../../../api/client", () => ({ api }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
// A source window stands in as one button: its selection's "Teach me this", through the desks' reader pass-through.
vi.mock("../windows/SourceWindow", () => ({
  SourceWindow: (props: { content: { extractionId: string }; reader?: { onTeachMe?: (request: { extractionId: string; spanIds: string[] }) => void } }) => (
    <button type="button" onClick={() => props.reader?.onTeachMe?.({ extractionId: props.content.extractionId, spanIds: [`${props.content.extractionId}_s1_3`] })}>
      teach me from {props.content.extractionId}
    </button>
  ),
}));
vi.mock("../windows/PanelWindow", () => ({ PANEL_TITLES: { guide: "Guide", notes: "Notes", path: "Reading path", library: "Library" }, LibraryPanel: () => null, PathPanel: () => null, RailHostPanel: () => null }));

function deskTransport(server: FixtureDeskServer): DeskTransport {
  return {
    state: async () => server.state(),
    apply: async (input) => server.apply(input),
    applyPad: async (input) => server.applyPad(input),
    padGet: async ({ padId }) => server.padGet(padId),
    library: async () => FIXTURE_LIBRARY,
    resolveExtraction: async (sourceId: string) => Object.values(FIXTURE_SOURCES).find((source) => source.sourceId === sourceId)?.extractionId ?? sourceId,
  } as DeskTransport;
}

const quietGoal = { goals: async () => ({ version: 1, goals: [] }) } as unknown as GoalTransport;
const quietCompanion = { companionHistory: async () => ({ version: 1, days: [], cursor: null }) } as unknown as CompanionTransport;
const quietPads = {
  padProposals: async (input: { padId: string }) => ({ version: 1, padId: input.padId, proposals: [] }),
  padDrain: async () => ({ version: 1, pads: [] }),
  carriedList: async () => ({ carried: [], shelfLimit: 3 }),
  carriedMark: async () => ({}),
} as unknown as PadsTransport;

let mintCount = 0;
const mint = (prefix: string) => `${prefix}_${++mintCount}`;

function mount(options: { server?: FixtureDeskServer; request?: { seq: number; entry: LessonEntry } | null } = {}) {
  const server = options.server ?? new FixtureDeskServer();
  const appTeachMe = vi.fn();
  const lessonsTransport = { list: vi.fn(async () => ({ lessons: [FIXTURE_LESSON_SUMMARY] })) };
  // The desks keep one store per vault for the app's life: each test its own vault.
  const vaultKey = `vault-lessons-${Math.random()}`;
  const onConsumed = vi.fn();
  const ui = (request: { seq: number; entry: LessonEntry; vault?: string } | null) => (
    <DeskShell
      vaultKey={vaultKey}
      onError={vi.fn()}
      transport={deskTransport(server)}
      initialViewport={{ width: 1600, height: 960 }}
      mintId={mint}
      goalTransport={quietGoal}
      companion={quietCompanion}
      padsTransport={quietPads}
      lessonsTransport={lessonsTransport}
      reader={{ onTeachMe: appTeachMe }}
      lessons={{ request, onConsumed }}
    />
  );
  const view = render(ui(options.request ?? null));
  return { server, appTeachMe, onConsumed, vaultKey, rerender: (request: { seq: number; entry: LessonEntry; vault?: string } | null) => view.rerender(ui(request)) };
}

const sentOps = (server: FixtureDeskServer): DeskOpDto[] => server.batches.flatMap((batch) => batch.ops as DeskOpDto[]);
const lessonEntries = (server: FixtureDeskServer) => server.state().desks.flatMap((desk) => desk.slots.flatMap((slot) => slot.windows))
  .flatMap((window) => (window.stack ?? []).filter((entry) => entry.kind === "lesson").map((entry) => ({ windowId: window.windowId, entry })));

async function flushDesks() {
  // The desk's outbox sends on its own schedule: a few rounds of its timers and replies.
  for (let i = 0; i < 4; i += 1) {
    await act(async () => {
      vi.advanceTimersByTime(1000);
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
  }
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  const values = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => void values.set(key, value),
    removeItem: (key: string) => void values.delete(key),
    clear: () => values.clear(),
  });
  api.lessonTurn.mockReset();
  api.lessonView.mockReset();
  api.lessonView.mockImplementation(async () => FIXTURE_LESSON_VIEW);
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("lesson entries on the desks", () => {
  it("a lesson opened from a selection lands in the desk's stack, not on the lesson screen", async () => {
    let answer: (view: LessonViewDto) => void = () => undefined;
    api.lessonTurn.mockImplementation(() => new Promise<LessonViewDto>((resolve) => { answer = resolve; }));
    const { server, appTeachMe } = mount();
    fireEvent.click(await screen.findByRole("button", { name: "teach me from fx_ext_softmax" }));
    // The opening shows in the stack at once, the teacher writing.
    await waitFor(() => expect(document.querySelector('[data-pad-stack="fx_w_pads"] [data-pad-tab^="lesson-opening:"]')).toBeTruthy());
    expect(appTeachMe).not.toHaveBeenCalled();
    await waitFor(() => expect(api.lessonTurn).toHaveBeenCalledTimes(1));
    expect(api.lessonTurn.mock.calls[0][0]).toMatchObject({ action: "open", entry: "reader_selection", selection: { extractionId: "fx_ext_softmax", spanIds: ["fx_ext_softmax_s1_3"] } });
    expect(screen.queryByTestId("lesson-screen")).toBeNull();
    await act(async () => {
      answer({ ...FIXTURE_LESSON_VIEW, lessonId: "les_from_selection", closed: false, closeReason: null, feed: FIXTURE_LESSON_VIEW.feed.slice(0, 1) });
    });
    await flushDesks();
    expect(lessonEntries(server)).toEqual([{ windowId: "fx_w_pads", entry: { kind: "lesson", lessonId: "les_from_selection" } }]);
    expect(sentOps(server).filter((op) => op.op === "add_to_stack")).toHaveLength(1);
    await waitFor(() => expect(document.querySelector('[data-pad-tab="lesson:les_from_selection"]')).toBeTruthy());
    expect(api.lessonTurn).toHaveBeenCalledTimes(1);
    expect(api.lessonView).not.toHaveBeenCalled();
  });

  it("a stored lesson the app asks for joins the stack and is read with lesson.view, no turn", async () => {
    const { server, rerender } = mount();
    await screen.findByRole("button", { name: "teach me from fx_ext_softmax" });
    rerender({ seq: 1, entry: { kind: "resume", lessonId: FIXTURE_LESSON_ID } });
    await flushDesks();
    expect(lessonEntries(server)).toEqual([{ windowId: "fx_w_pads", entry: { kind: "lesson", lessonId: FIXTURE_LESSON_ID } }]);
    await screen.findByText("If every score goes up by 3, what happens to the loss?");
    expect(api.lessonTurn).not.toHaveBeenCalled();
    // The same ask again (a re-render) opens nothing more.
    rerender({ seq: 1, entry: { kind: "resume", lessonId: FIXTURE_LESSON_ID } });
    await flushDesks();
    expect(sentOps(server).filter((op) => op.op === "add_to_stack")).toHaveLength(1);
  });

  it("a request is taken once and the app told so; one asked in another vault opens nothing here", async () => {
    const { server, rerender, onConsumed, vaultKey } = mount();
    await screen.findByRole("button", { name: "teach me from fx_ext_softmax" });
    rerender({ seq: 1, entry: { kind: "resume", lessonId: FIXTURE_LESSON_ID }, vault: "another vault" });
    await flushDesks();
    expect(onConsumed).toHaveBeenCalledWith(1);
    expect(sentOps(server).filter((op) => op.op === "add_to_stack")).toHaveLength(0);
    rerender({ seq: 2, entry: { kind: "resume", lessonId: FIXTURE_LESSON_ID }, vault: vaultKey });
    await flushDesks();
    expect(onConsumed).toHaveBeenCalledWith(2);
    expect(sentOps(server).filter((op) => op.op === "add_to_stack")).toHaveLength(1);
  });

  it("a window whose content is a lesson shows it, as a stack of one", async () => {
    const state = fixtureDeskState();
    const desk = state.desks.find((each) => each.deskId === "fx_desk_softmax")!;
    desk.slots.push({ slot: desk.slots.length, windows: [{ windowId: "fx_w_lesson", pane: 0, kind: "lesson", active: true, view: {}, content: { kind: "lesson", lessonId: FIXTURE_LESSON_ID } }] } as never);
    mount({ server: new FixtureDeskServer(state) });
    await waitFor(() => expect(document.querySelector('[data-pad-stack="fx_w_lesson"] [data-lesson-paper]')).toBeTruthy());
    expect(api.lessonTurn).not.toHaveBeenCalled();
  });
});
