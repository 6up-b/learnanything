// The goal lens on the desks (spec §12): the band from goal.band, `p` through the key router (and the path view
// owning its keys while open), one whole-reading goal.lens per reading in view (none for a paused window),
// curriculum.path judged once when a goal opens, and no lens without a goal. jsdom lays nothing out; the marks'
// geometry is the real-webview harness's.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FixtureDeskServer } from "../../../fixtures/desks/workspace";
import { FIXTURE_LIBRARY, FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { FixtureGoal } from "../../../fixtures/desks/goal";
import { DeskShell, type CompanionTransport, type DeskTransport, type PaneRenderInput } from "../DeskShell";
import type { GoalTransport } from "./controller";

vi.mock("../../../api/client", () => ({ api: {} }));
vi.mock("../windows/SourceWindow", () => ({ SourceWindow: () => null }));
vi.mock("../windows/PanelWindow", () => ({ PANEL_TITLES: { guide: "Guide", notes: "Notes", path: "Reading path", library: "Library" }, LibraryPanel: () => null, PathPanel: () => null, RailHostPanel: () => null }));

function deskTransport(server: FixtureDeskServer): DeskTransport {
  return {
    state: async () => server.state(),
    apply: async (input) => server.apply(input),
    library: async () => FIXTURE_LIBRARY,
    resolveExtraction: async (sourceId: string) => Object.values(FIXTURE_SOURCES).find((source) => source.sourceId === sourceId)?.extractionId ?? sourceId,
  } as DeskTransport;
}

function goalTransport(goal = new FixtureGoal(), overrides: Partial<GoalTransport> = {}) {
  const calls: Array<{ name: string; input: unknown }> = [];
  const log = <T,>(name: string, answer: (input: never) => T) => async (input?: unknown) => { calls.push({ name, input }); return answer(input as never); };
  const transport: GoalTransport = {
    goals: log("goals", () => goal.goals()),
    band: log("band", () => goal.band()),
    lens: log("lens", (input: { extractionId: string }) => goal.lens(input.extractionId)),
    sectionChoice: log("sectionChoice", (input: Parameters<FixtureGoal["sectionChoice"]>[0]) => goal.sectionChoice(input)) as never,
    path: log("path", () => goal.band().path),
    setDepth: log("setDepth", (input: { depth: never }) => goal.setDepth(input.depth)),
    override: log("override", (input: never) => goal.override(input)),
    setScope: log("setScope", () => ({})),
    scopeDecide: log("scopeDecide", () => ({})),
    ...overrides,
  };
  return { transport, calls, goal };
}

let mintCount = 0;
const mint = (prefix: string) => `${prefix}_${++mintCount}`;

// The companion's calls answer nothing yet (its history empty).
const quietCompanion = {
  companionHistory: async () => ({ version: 1, days: [], cursor: null }),
} as unknown as CompanionTransport;

function mount(goal: GoalTransport, server = new FixtureDeskServer()) {
  const onError = vi.fn();
  render(
    <DeskShell
      vaultKey={`vault-${Math.random()}`}
      onError={onError}
      transport={deskTransport(server)}
      renderPane={(input: PaneRenderInput) => <div data-testid={`pane-${input.window.windowId}`}>{input.window.windowId}</div>}
      initialViewport={{ width: 1600, height: 960 }}
      mintId={mint}
      goalTransport={goal}
      companion={quietCompanion}
    />,
  );
  return { server, onError };
}

async function settle() {
  await act(async () => {
    vi.advanceTimersByTime(300);
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
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

describe("the goal band on the desks", () => {
  it("shows the desk's goal (the primary one by default) and judges its path once", async () => {
    const { transport, calls } = goalTransport();
    mount(transport);
    await waitFor(() => expect(screen.getByRole("region", { name: "your goal" })).toBeTruthy());
    expect(screen.getByText("“Understand softmax well enough to implement attention”")).toBeTruthy();
    expect(screen.getByText(/5 learning objects · 1 likely · 4 untested/)).toBeTruthy();
    expect(screen.getByText("your path")).toBeTruthy();
    await settle();
    expect(calls.filter((call) => call.name === "path")).toEqual([{ name: "path", input: { goalId: "fx_goal_softmax", judge: true } }]);
  });

  it("asks goal.lens once per reading in view, for the whole reading, and nothing for a paused window", async () => {
    const { transport, calls } = goalTransport();
    mount(transport);
    await waitFor(() => expect(calls.some((call) => call.name === "lens")).toBe(true));
    await settle();
    const asked = calls.filter((call) => call.name === "lens").map((call) => call.input as Record<string, unknown>);
    // The first desk shows the book and the video; the note is off to the side (offscreen, paused) and the other
    // desks are hidden.
    expect(asked.map((input) => input.extractionId).sort()).toEqual([FIXTURE_SOURCES.book.extractionId, FIXTURE_SOURCES.video.extractionId]);
    for (const input of asked) expect(Object.keys(input).sort()).toEqual(["extractionId", "goalId"]);
  });

  it("opens the path view with p through the router; open, it owns its keys; esc closes it", async () => {
    const { transport } = goalTransport();
    mount(transport);
    await waitFor(() => expect(screen.getByRole("region", { name: "your goal" })).toBeTruthy());
    act(() => { fireEvent.keyDown(window, { key: "p", code: "KeyP" }); });
    const dialog = await screen.findByRole("dialog", { name: "your path" });
    expect(dialog.textContent).toContain("Turn scores into softmax weights");
    // A desk key does nothing while it is open: `/` would open search in context.
    act(() => { fireEvent.keyDown(window, { key: "/", code: "Slash" }); });
    expect(screen.queryByRole("dialog", { name: "search in context" })).toBeNull();
    act(() => { fireEvent.keyDown(dialog, { key: "Escape" }); });
    expect(screen.queryByRole("dialog", { name: "your path" })).toBeNull();
    act(() => { fireEvent.keyDown(window, { key: "p", code: "KeyP" }); });
    expect(await screen.findByRole("dialog", { name: "your path" })).toBeTruthy();
  });

  it("sets the depth through curriculum.set_depth and reads the band again", async () => {
    const { transport, calls } = goalTransport();
    mount(transport);
    await waitFor(() => expect(screen.getByRole("region", { name: "your goal" })).toBeTruthy());
    const bands = calls.filter((call) => call.name === "band").length;
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "get the idea" })); });
    await settle();
    expect(calls.find((call) => call.name === "setDepth")?.input).toEqual({ goalId: "fx_goal_softmax", depth: "get_the_idea" });
    expect(calls.filter((call) => call.name === "band").length).toBeGreaterThan(bands);
    await waitFor(() => expect(screen.getByText(/3 learning objects · 1 likely · 2 untested/)).toBeTruthy());
  });

  it("without any goal shows no band and a quiet chip in the top bar", async () => {
    const { transport } = goalTransport(new FixtureGoal(), { goals: async () => ({ version: 1, goals: [] }) });
    mount(transport);
    const chip = await screen.findByRole("button", { name: "◎ set a goal" });
    expect(screen.queryByRole("region", { name: "your goal" })).toBeNull();
    fireEvent.click(chip);
    expect(screen.getByText("no active goal yet · set one in Goals")).toBeTruthy();
  });

  it("switches the desk's goal from the band: no goal turns the lens off, a goal is stored on the desk", async () => {
    const { transport } = goalTransport();
    const { server } = mount(transport);
    await waitFor(() => expect(screen.getByRole("region", { name: "your goal" })).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: /Understand softmax/ }));
    await act(async () => { fireEvent.click(screen.getByRole("menuitem", { name: "no goal (the lens off)" })); });
    await settle();
    expect(screen.queryByRole("region", { name: "your goal" })).toBeNull();
    fireEvent.click(await screen.findByRole("button", { name: "◎ set a goal" }));
    await act(async () => { fireEvent.click(screen.getByRole("menuitem", { name: /Understand softmax/ })); });
    await settle();
    await waitFor(() => expect(screen.getByRole("region", { name: "your goal" })).toBeTruthy());
    await waitFor(() => expect(server.state().desks.find((desk) => desk.deskId === "fx_desk_softmax")?.goalId).toBe("fx_goal_softmax"));
  });

  it("the companion keeps the lens's goal in view, the default goal included", async () => {
    const { transport } = goalTransport();
    mount(transport);
    await waitFor(() => expect(screen.getByRole("region", { name: "your goal" })).toBeTruthy());
    act(() => { fireEvent.keyDown(window, { key: "C", code: "KeyC", shiftKey: true }); });
    await settle();
    const line = await screen.findByText("◎ goal in context");
    expect(line.className).toBe("goal gctx");
  });

  it("with no goal transport wired (the sidecar not reachable) shows no lens and reports nothing", async () => {
    const onError = vi.fn();
    const { transport } = goalTransport(new FixtureGoal(), { goals: () => { throw new TypeError("not wired"); } });
    render(<DeskShell vaultKey="vault-unwired" onError={onError} transport={deskTransport(new FixtureDeskServer())}
      renderPane={(input) => <div>{input.window.windowId}</div>} initialViewport={{ width: 1600, height: 960 }} mintId={mint} goalTransport={transport} />);
    await settle();
    expect(screen.queryByRole("region", { name: "your goal" })).toBeNull();
    expect(onError).not.toHaveBeenCalled();
  });
});
