// RD7 on the desks (spec §12.6): a due check's closed marker before its host passage in a book window; "check now"
// sends what is visible on every desk and opens the card at the host passage; the pad stack's body is veiled whole (its
// head still says what it is); the companion's ask, search and a new lesson wait while the check is open; a restart
// brings an open administration back as the card centred near the top. jsdom lays nothing out; the harness shows the
// real webview.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { CheckCardDto } from "../../../api/dto";
import { FixtureDeskServer } from "../../../fixtures/desks/workspace";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { DeskShell, type CompanionTransport, type DeskTransport, type PadsTransport } from "../DeskShell";
import type { GoalTransport } from "../goal/controller";
import type { CheckTransport } from "./controller";

vi.mock("../../../api/client", () => ({ api: {} }));
vi.mock("../../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
// A book window stands in as its passages, with whatever its lens puts before the host passage.
vi.mock("../windows/SourceWindow", () => ({
  SourceWindow: (props: { content: { kind: string; extractionId: string }; lens?: { before?: (span: string) => unknown } | null }) => (
    <div data-testid={`src-${props.content.extractionId}`}>
      {props.content.kind === "source" ? <>{props.lens?.before?.("fx_ext_softmax_s1_1") as never}<p data-span-id="fx_ext_softmax_s1_1">the gradient is p minus one-hot</p></> : null}
    </div>
  ),
}));
vi.mock("../windows/PanelWindow", () => ({ PANEL_TITLES: { guide: "Guide", notes: "Notes", path: "Reading path", library: "Library" }, LibraryPanel: () => null, PathPanel: () => null, RailHostPanel: () => null }));

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

function mount(over: Partial<CheckTransport> = {}, onPracticeSession = vi.fn()) {
  const server = new FixtureDeskServer();
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
      reader={{ workbench: { practiceSessionId: "s_1", onPracticeSession } } as never} />,
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

describe("an inline check on the desks", () => {
  it("opens from its closed marker with what is visible, at the host passage, and veils the pads whole", async () => {
    const session = { sessionId: "s_1" };
    const { checkTransport, onPracticeSession } = mount({ begin: vi.fn(async () => cardFor({ practiceSession: session as never })) });
    const marker = await screen.findByText(/a cold check is due before this page · on your own/);
    expect(marker.closest("[data-check-marker]")!.textContent).not.toContain("gradient");
    fireEvent.click(screen.getByRole("button", { name: "check now" }));
    await waitFor(() => expect(checkTransport.begin).toHaveBeenCalled());
    const sent = (checkTransport.begin as ReturnType<typeof vi.fn>).mock.calls[0][0];
    expect(sent).toMatchObject({ commitmentId: "cm_1", sessionId: "s_1" });
    // The app adopts the session the answer is recorded on.
    await waitFor(() => expect(onPracticeSession).toHaveBeenCalledWith(session));
    const kinds = Object.fromEntries(sent.visible.windows.map((window: { windowId: string; kind: string }) => [window.windowId, window.kind]));
    expect(kinds.fx_w_book).toBe("source");
    expect(kinds.fx_w_pads).toBe("pad_stack");
    expect(sent.visible.windows.find((window: { windowId: string }) => window.windowId === "fx_w_book").spanIds).toEqual(["fx_ext_softmax_s1_1"]);
    // The card opens inline, at the host passage, in the book.
    const inline = await waitFor(() => {
      const found = screen.getByTestId(`src-${book.extractionId}`).querySelector('[data-check-card="inline"]');
      expect(found).toBeTruthy();
      return found as HTMLElement;
    });
    expect(inline.textContent).toContain("What is the gradient of the loss?");
    expect(document.querySelector('[data-check-card="overlay"]')).toBeNull();
    const body = document.querySelector('[data-desk-window="fx_w_pads"] [data-desk-pane-body]')!;
    await waitFor(() => expect(body.className).toContain("veiled"));
    expect(document.querySelector('[data-desk-window="fx_w_pads"] .desk-pane-head')!.className).not.toContain("veiled");
    // The companion's ask waits, with the reason (shift+c brings it to its dock).
    fireEvent.keyDown(window, { key: "C", shiftKey: true });
    await waitFor(() => expect(document.body.textContent).toContain("the companion waits · after your check"));
    // The ask box is disabled, and held (its label is off while the check is open).
    const askBox = document.querySelector<HTMLInputElement>("[data-companion-dock] input.input")!;
    expect(askBox.disabled).toBe(true);
    expect(askBox.closest("[inert]")).toBeTruthy();
    // Answered: the veils lift and the card says so.
    fireEvent.change(screen.getByLabelText("your answer"), { target: { value: "p - onehot" } });
    fireEvent.click(screen.getByRole("button", { name: "answer ↵" }));
    await waitFor(() => expect(document.querySelector('[data-check-phase="answered"]')).toBeTruthy());
    await waitFor(() => expect(body.className).not.toContain("veiled"));
  });

  // A check whose host passage is not on the desks (cm_9 has no due row here) opens centred near the top.
  it("a second check cannot open while one is open, and search waits", async () => {
    const { checkTransport } = mount({ openInline: vi.fn(async () => ({ administration: cardFor({ administrationToken: "cad_open", commitmentId: "cm_9" }) })) });
    await waitFor(() => expect(document.querySelector('[data-check-card="overlay"]')).toBeTruthy());
    await screen.findByText(/a cold check is due before this page · on your own/);
    const button = screen.getByRole("button", { name: "check now" }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    expect(document.body.textContent).toContain("another check is open · answer it or say not now first");
    expect(checkTransport.begin).not.toHaveBeenCalled();
    fireEvent.keyDown(window, { key: "/" });
    await waitFor(() => expect(document.querySelector(".desk-toast")?.textContent).toBe("search waits · after your check · it is open on this desk"));
    expect(document.querySelector("[data-search-panel]")).toBeNull();
  });

  it("a restart brings the open administration back at its host passage, with its veils; not now closes it", async () => {
    const { checkTransport } = mount({ openInline: vi.fn(async () => ({ administration: cardFor({ administrationToken: "cad_open" }) })) });
    const inline = await waitFor(() => {
      const found = screen.getByTestId(`src-${book.extractionId}`).querySelector('[data-check-card="inline"]');
      expect(found).toBeTruthy();
      return found as HTMLElement;
    });
    expect(inline.textContent).toContain("What is the gradient of the loss?");
    expect(document.querySelector('[data-check-card="overlay"]')).toBeNull();
    await waitFor(() => expect(document.querySelector('[data-desk-window="fx_w_pads"] [data-desk-pane-body]')!.className).toContain("veiled"));
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "not now" })); });
    expect(checkTransport.abandon).toHaveBeenCalledWith({ administrationToken: "cad_open" });
    await waitFor(() => expect(document.querySelector('[data-check-card]')).toBeNull());
  });
});
