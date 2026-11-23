// RD6's fix round: what the goal lens shows is the current goal's, read again when it may have changed. An old lens
// reply never lands under another goal or after a refresh; an open why card follows its section; a write elsewhere
// in the app and the next check's due time read the band (and the goals) again; a reading coming back into view is
// asked again; a path owing a judgment once coverage finished starts it, once, and is not polled for ever.
import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { GoalBandDto, GoalLensDto } from "../../../api/dto";
import { invalidate } from "../../../api/queryCache";
import { TAG } from "../../../api/queryTags";
import { FixtureGoal } from "../../../fixtures/desks/goal";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import { REAL_TIMERS } from "../keys/router";
import { BAND_RECHECK_MS, type GoalTransport, useGoalLens } from "./controller";

vi.mock("../../../api/client", () => ({ api: {} }));

const BOOK = FIXTURE_SOURCES.book.extractionId;

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

function tagged(goal: FixtureGoal, tag: string): GoalLensDto {
  const lens = goal.lens(BOOK);
  return { ...lens, levels: lens.levels.map((level) => ({ ...level, reasonMd: tag })) };
}

function transportFor(overrides: Partial<GoalTransport> = {}) {
  const goal = new FixtureGoal();
  const calls: Record<string, number> = {};
  const count = (name: string) => { calls[name] = (calls[name] ?? 0) + 1; };
  const transport: GoalTransport = {
    goals: async () => { count("goals"); return goal.goals(); },
    band: async () => { count("band"); return goal.band(); },
    lens: async ({ extractionId }) => { count("lens"); return goal.lens(extractionId); },
    sectionChoice: async () => ({}) as never,
    path: async () => { count("path"); return null; },
    setDepth: async () => null,
    override: async () => null,
    setScope: async () => null,
    scopeDecide: async () => null,
    ...overrides,
  };
  return { transport, calls, goal };
}

function lensHook(transport: GoalTransport, initial: { deskGoalId: string; readings: string[] }) {
  return renderHook((props: { deskGoalId: string; readings: string[] }) => useGoalLens({
    transport, deskGoalId: props.deskGoalId, readings: props.readings, timers: REAL_TIMERS, mintId: (prefix) => `${prefix}_1`,
    onError: () => undefined,
  }), { initialProps: initial });
}

async function flush(ms = 0) {
  await act(async () => {
    if (ms) vi.advanceTimersByTime(ms);
    for (let i = 0; i < 5; i += 1) await Promise.resolve();
  });
}

beforeEach(() => vi.useFakeTimers({ shouldAdvanceTime: false }));
afterEach(() => { cleanup(); vi.useRealTimers(); });

describe("the goal lens stays current", () => {
  it("drops a lens reply asked under another goal, and one asked before a refresh", async () => {
    const goal = new FixtureGoal();
    const replies: Array<{ goalId: string; reply: ReturnType<typeof deferred<GoalLensDto>> }> = [];
    const { transport } = transportFor({
      band: async (input) => ({ ...goal.band(), goalId: input.goalId }),
      lens: (input) => { const reply = deferred<GoalLensDto>(); replies.push({ goalId: input.goalId, reply }); return reply.promise; },
    });
    const hook = lensHook(transport, { deskGoalId: "goal_a", readings: [BOOK] });
    await flush();
    hook.rerender({ deskGoalId: "goal_b", readings: [BOOK] });
    await flush();
    const a = replies.find((each) => each.goalId === "goal_a")!;
    const b = replies.find((each) => each.goalId === "goal_b")!;
    b.reply.resolve(tagged(goal, "goal b's"));
    await flush();
    a.reply.resolve(tagged(goal, "goal a's"));
    await flush();
    expect(hook.result.current.indexFor(BOOK)!.sections[0].reasonMd).toBe("goal b's");
    // A refresh (a depth, a choice) asks again: the reply from before it never overwrites the one after.
    act(() => hook.result.current.refresh());
    await flush();
    const mine = replies.filter((each) => each.goalId === "goal_b");
    const after = mine[mine.length - 1];
    expect(after).not.toBe(b);
    after.reply.resolve(tagged(goal, "after the refresh"));
    await flush();
    expect(hook.result.current.indexFor(BOOK)!.sections[0].reasonMd).toBe("after the refresh");
  });

  it("keeps an open why card on its section as the latest lens has it, and closes it with the goal", async () => {
    const goal = new FixtureGoal();
    let tag = "before";
    const { transport } = transportFor({ lens: async () => tagged(goal, tag) });
    const hook = lensHook(transport, { deskGoalId: "goal_a", readings: [BOOK] });
    await flush();
    const section = hook.result.current.indexFor(BOOK)!.sections[0];
    act(() => hook.result.current.showWhy({ section, extractionId: BOOK, windowId: "w", rect: { left: 0, top: 0, right: 1, bottom: 1 } }));
    tag = "a check fell due";
    act(() => hook.result.current.refresh());
    await flush();
    expect(hook.result.current.why!.section.reasonMd).toBe("a check fell due");
    hook.rerender({ deskGoalId: "goal_b", readings: [BOOK] });
    await flush();
    expect(hook.result.current.why).toBeNull();
  });

  it("reads the goals, the band and the readings again after a write elsewhere in the app", async () => {
    const { transport, calls } = transportFor();
    lensHook(transport, { deskGoalId: "goal_a", readings: [BOOK] });
    await flush();
    const before = { ...calls };
    act(() => invalidate({ tags: [TAG.queue] }));  // an answer, say
    await flush();
    expect(calls.goals).toBe(before.goals + 1);
    expect(calls.band).toBe(before.band + 1);
    expect(calls.lens).toBe(before.lens + 1);
    act(() => invalidate({ tags: [TAG.goals] }));  // a goal paused elsewhere
    await flush();
    expect(calls.goals).toBe(before.goals + 2);
  });

  it("reads the band again when the next check falls due", async () => {
    const goal = new FixtureGoal();
    const { transport, calls } = transportFor({
      band: async () => { calls.band = (calls.band ?? 0) + 1; return { ...goal.band(), nextCheckDue: new Date(Date.now() + 60_000).toISOString() } as GoalBandDto; },
    });
    lensHook(transport, { deskGoalId: "goal_a", readings: [] });
    await flush();
    const before = calls.band;
    await flush(59_000);
    expect(calls.band).toBe(before);
    await flush(2_000);
    expect(calls.band).toBe(before + 1);
  });

  it("asks again for a reading that comes back into view", async () => {
    const { transport, calls } = transportFor();
    const hook = lensHook(transport, { deskGoalId: "goal_a", readings: [BOOK] });
    await flush();
    expect(calls.lens).toBe(1);
    hook.rerender({ deskGoalId: "goal_a", readings: [] });
    await flush();
    hook.rerender({ deskGoalId: "goal_a", readings: [BOOK] });
    await flush();
    expect(calls.lens).toBe(2);
  });

  it("starts the judgment a path owes once coverage is done, once, and stops polling a path that did not start", async () => {
    const goal = new FixtureGoal();
    const pending = (): GoalBandDto => { const band = goal.band(); return { ...band, status: "pending", path: { ...band.path!, status: "pending", stateKey: "k1" } }; };
    const { transport, calls } = transportFor({ band: async () => { calls.band = (calls.band ?? 0) + 1; return pending(); } });
    lensHook(transport, { deskGoalId: "goal_a", readings: [] });
    await flush();
    // The open's one curriculum.path, then the one the owed judgment starts.
    expect(calls.path).toBe(2);
    const bands = calls.band;
    await flush(BAND_RECHECK_MS * 3);
    expect(calls.path).toBe(2);
    expect(calls.band).toBe(bands);
  });
});
