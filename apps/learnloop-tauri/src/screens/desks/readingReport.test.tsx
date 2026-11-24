// The book being read, as the desks tell the app (the Reader's retirement, phase 2 step 2: `onReadingChange`), is
// never told while an inline check holds the desks: the windows' heads show neutral titles then, and the app must not
// learn the check's book this way either. The desks and the check as in checks/deskChecks.test.tsx (this file's
// helpers are that file's, copied: a test file never imports another).
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { CheckCardDto } from "../../api/dto";
import { FixtureDeskServer, fixtureDeskState } from "../../fixtures/desks/workspace";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "../../fixtures/desks/sources";
import { DeskShell, type CompanionTransport, type DeskTransport, type PadsTransport } from "./DeskShell";
import type { GoalTransport } from "./goal/controller";
import type { CheckTransport } from "./checks/controller";

vi.mock("../../api/client", () => ({ api: {} }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
// A book window stands in as its passages, with whatever its lens puts before the host passage.
vi.mock("./windows/SourceWindow", () => ({
  SourceWindow: (props: { content: { kind: string; extractionId: string }; lens?: { before?: (span: string) => unknown } | null }) => (
    <div data-testid={`src-${props.content.extractionId}`}>
      {props.content.kind === "source" ? <>{props.lens?.before?.("fx_ext_softmax_s1_1") as never}<p data-span-id="fx_ext_softmax_s1_1">the gradient is p minus one-hot</p></> : null}
    </div>
  ),
}));
vi.mock("./windows/PanelWindow", () => ({ PANEL_TITLES: { guide: "Guide", notes: "Notes", path: "Reading path", library: "Library" }, LibraryPanel: () => null, PathPanel: () => null, RailHostPanel: () => null }));

const { book } = FIXTURE_SOURCES;

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
  passageUnionRange: async () => ({ version: 1, extractionId: "", spans: [], sections: [] }),
} as unknown as PadsTransport;

function cardFor(over: Partial<CheckCardDto> = {}): CheckCardDto {
  return {
    administrationToken: "cad_1", commitmentId: "cm_1", itemRef: "pi_1", contractHash: "h", cold: true, state: "open",
    protection: { veilSetId: "cvs_1", method: "structural+notes_by_default", groups: ["pads"], opened: [],
      veiled: [{ group: "pads", kind: "window", window_id: "fx_w_pads" }] },
    prompt: { prompt: "What is the gradient of the loss?" }, ...over,
  };
}

let mintCount = 0;
const mint = (prefix: string) => `${prefix}_${++mintCount}`;

function mount(over: Partial<CheckTransport> = {}, onPracticeSession = vi.fn(), onReadingChange = vi.fn(), server = new FixtureDeskServer()) {
  const checkTransport: CheckTransport = {
    dueFor: vi.fn(async (input: { extractionId: string }) => ({ version: 1, checks: input.extractionId === book.extractionId
      ? [{ commitmentId: "cm_1", loId: "lo_1", due: "2026-11-22T00:00:00Z", host: { extractionId: book.extractionId, sectionId: "s1", spanId: "fx_ext_softmax_s1_1" }, provenance: {} }]
      : [] })),
    begin: vi.fn(async () => cardFor()),
    protectMore: vi.fn(async () => ({ veilAdditions: [] })),
    expose: vi.fn(async () => ({ protectionStatus: { exposure: [], coldNow: true } })),
    submit: vi.fn(async () => ({ administrationToken: "cad_1", attemptId: "at_1", cold: true, reason: "on_your_own" as const })),
    abandon: vi.fn(async () => ({})),
    openInline: vi.fn(async () => ({ administration: null })),
    ...over,
  };
  render(
    <DeskShell vaultKey={`vault-checks-${Math.random()}`} onError={vi.fn()} transport={deskTransport(server)} initialViewport={{ width: 1600, height: 960 }}
      mintId={mint} goalTransport={quietGoal} companion={quietCompanion} padsTransport={quietPads} checkTransport={checkTransport}
      reader={{ workbench: { practiceSessionId: "s_1", onPracticeSession } } as never} onReadingChange={onReadingChange} />,
  );
  return { server, checkTransport, onPracticeSession };
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
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("the book being read, while a check is open", () => {
  it("is not told while the check holds the desks, and is told once the check is set aside", async () => {
    const onReadingChange = vi.fn();
    mount({ openInline: vi.fn(async () => ({ administration: cardFor({ administrationToken: "cad_open" }) })) }, vi.fn(), onReadingChange);
    await waitFor(() => expect(screen.getByTestId(`src-${book.extractionId}`).querySelector('[data-check-card="inline"]')).toBeTruthy());
    await act(async () => { await vi.advanceTimersByTimeAsync(200); });
    expect(onReadingChange).not.toHaveBeenCalled();
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "not now" })); });
    await waitFor(() => expect(document.querySelector("[data-check-card]")).toBeNull());
    await waitFor(() => expect(onReadingChange).toHaveBeenCalled());
    expect(onReadingChange.mock.calls[onReadingChange.mock.calls.length - 1]?.[0]).toMatchObject({ sourceId: book.sourceId });
  });

  // The Reader's retirement, review fix round (major 12, ledger RDX-14): the book being read is the desk in view's.
  // Read the softmax book on its desk, then switch to a desk whose focus is a pad and which holds the paper: the app
  // is told the paper (the first book on that desk), never the softmax book from the desk left.
  it("is the book on the desk in view, not the one focused last on another desk", async () => {
    const onReadingChange = vi.fn();
    const state = fixtureDeskState();
    const attention = state.desks.find((desk) => desk.deskId === "fx_desk_attention")!;
    const paper2 = attention.slots.flatMap((slot) => slot.windows).find((window) => window.windowId === "fx_w_paper2")!;
    attention.slots = [
      { slot: 0, windows: [{ windowId: "w_pad_here", pane: 0, kind: "pad_stack", active: true, view: {}, stack: [{ kind: "pad", padId: "fx_pad_running" }] }] as never },
      { slot: 1, windows: [paper2] },
    ];
    attention.focusWindowId = "w_pad_here";
    mount({}, vi.fn(), onReadingChange, new FixtureDeskServer(state));
    await waitFor(() => expect(onReadingChange).toHaveBeenCalled());
    expect(onReadingChange.mock.calls[onReadingChange.mock.calls.length - 1]?.[0]).toMatchObject({ sourceId: book.sourceId });
    await act(async () => { fireEvent.keyDown(window, { key: "j", code: "KeyJ", altKey: true }); });
    await act(async () => { await vi.advanceTimersByTimeAsync(200); });
    await waitFor(() => expect(onReadingChange.mock.calls[onReadingChange.mock.calls.length - 1]?.[0]).toMatchObject({ sourceId: FIXTURE_SOURCES.paper.sourceId }));
  });
});
