// The goal lens's components (spec §12.2-§12.5): the band, the marks with their why card (and its timing), the
// callouts and the path view with its stored choices. Every value comes from the goal fixture, which answers as
// goal.band and goal.lens do.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { FixtureGoal } from "../../../fixtures/desks/goal";
import { FIXTURE_SOURCES } from "../../../fixtures/desks/sources";
import type { GoalBandDto } from "../../../api/dto";
import { GoalBand } from "./GoalBand";
import { readerLens, WhyCard, WHY_HIDE_MS, WHY_OPEN_MS } from "./marks";
import { indexLens } from "./model";
import { PathView } from "./PathView";
import { useGoalDesk } from "./GoalLayer";
import type { GoalTransport } from "./controller";
import { DIRECT_HUB } from "../lifecycle";
import type { Timers } from "../keys/router";

const BOOK = FIXTURE_SOURCES.book.extractionId;
afterEach(cleanup);

function band(depth: "get_the_idea" | "learn_to_use_it" = "learn_to_use_it"): GoalBandDto {
  const goal = new FixtureGoal();
  goal.depth = depth;
  return goal.band();
}

function bandProps(overrides: Partial<Parameters<typeof GoalBand>[0]> = {}) {
  return {
    band: band(), goals: new FixtureGoal().goals().goals, here: null, dimOn: true, onToggleDim: vi.fn(), onPath: vi.fn(),
    onDepth: vi.fn(), onOpenLo: vi.fn(), onNext: vi.fn(), onChooseGoal: vi.fn(), onMapIt: vi.fn(), ...overrides,
  };
}

describe("the band", () => {
  it("says the goal in the learner's words, its LOs as dots in path order, the depth and what is next", () => {
    const props = bandProps();
    render(<GoalBand {...props} />);
    expect(screen.getByText(/◎ your goal · quest · no deadline/)).toBeTruthy();
    expect(screen.getByText(/your words, 2 Nov/)).toBeTruthy();
    const dots = [...document.querySelectorAll("[data-gstop]")];
    expect(dots.map((dot) => dot.getAttribute("data-gstop"))).toEqual(["lo_fx_xent", "lo_fx_softmax", "lo_fx_temp", "lo_fx_grad", "lo_fx_attend"]);
    expect(dots[0].className).toBe("gs rd-untested pre");
    expect(dots[1].className).toBe("gs rd-likely");
    expect(document.querySelectorAll(".gs.unm")).toHaveLength(1);
    expect(screen.getByRole("button", { name: "learn to use it" }).getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(screen.getByRole("button", { name: "get the idea" }));
    expect(props.onDepth).toHaveBeenCalledWith("get_the_idea");
    fireEvent.click(dots[1]);
    expect(props.onOpenLo).toHaveBeenCalledWith("lo_fx_softmax");
    fireEvent.click(screen.getByRole("button", { name: "§ Softmax, a short book 4 Cross-entropy" }));
    expect(props.onNext).toHaveBeenCalled();
    fireEvent.click(document.querySelector("[data-gdim]")!);
    expect(props.onToggleDim).toHaveBeenCalled();
    fireEvent.click(document.querySelector("[data-gpath]")!);
    expect(props.onPath).toHaveBeenCalled();
  });

  it("dims the LOs beyond the depth and rings the one being read", () => {
    render(<GoalBand {...bandProps({ band: band("get_the_idea"), here: { where: "1 Scores into weights", lo: "Turn scores into softmax weights", tag: null, loId: "lo_fx_softmax" } })} />);
    expect(document.querySelector("[data-gstop='lo_fx_xent']")!.className).toBe("gs rd-untested pre later");
    expect(document.querySelector("[data-gstop='lo_fx_softmax']")!.className).toBe("gs rd-likely here");
    expect(document.querySelector("[data-goal-here]")!.textContent).toBe("1 Scores into weights · Turn scores into softmax weights");
  });

  it("shows a due check's ◇ with no name, and an answered one filled", () => {
    const value = band();
    const dots = value.learningObjects!.map((dot, i) => (i === 1 ? { ...dot, check: "due" as const, held: true, title: null } : i === 3 ? { ...dot, check: "answered" as const } : dot));
    render(<GoalBand {...bandProps({ band: { ...value, learningObjects: dots } })} />);
    expect(document.querySelector(".gs.chk.due")!.getAttribute("title")).toBeNull();
    expect(document.querySelector(".gs.chk.done")).toBeTruthy();
    expect(document.querySelector("[data-gstop='lo_fx_softmax']")!.getAttribute("title")).toBe("a cold check is due on this topic");
  });

  it("an unmapped goal offers map it; a goal the learner did not set says so", () => {
    const props = bandProps({ band: { ...band(), status: "no_scope", learningObjects: [], counts: undefined } });
    const view = render(<GoalBand {...props} />);
    fireEvent.click(screen.getByRole("button", { name: "map it" }));
    expect(props.onMapIt).toHaveBeenCalled();
    view.unmount();
    render(<GoalBand {...bandProps({ band: { ...band(), status: "not_a_deliverable", message: "LearnLoop maps only goals you set yourself to your sources." } })} />);
    expect(screen.getByText("LearnLoop maps only goals you set yourself to your sources.")).toBeTruthy();
  });
});

describe("marks, dimming and callouts on a reading", () => {
  const goal = new FixtureGoal();
  const index = indexLens(goal.lens(BOOK));
  const handlers = { hover: vi.fn(), tap: vi.fn() };

  it("classes each passage by its section's level and dims skippable and later text", () => {
    const lens = readerLens({ index, dimOn: true, windowId: "w", handlers })!;
    expect(lens.className!(`${BOOK}_s1_2`)).toBe("g-core");
    expect(lens.className!(`${BOOK}_s6_2`)).toBe("g-skip gl-dim");
    expect(readerLens({ index, dimOn: false, windowId: "w", handlers })!.className!(`${BOOK}_s6_2`)).toBe("g-skip");
    expect(lens.className!("not-a-passage")).toBeUndefined();
    expect(readerLens({ index: null, dimOn: true, windowId: "w", handlers })).toBeNull();
  });

  it("puts a mark in each passage's gutter that opens its why, and a callout at a section on the path", () => {
    const lens = readerLens({ index, dimOn: true, windowId: "w", handlers })!;
    render(<div>{lens.before!(`${BOOK}_s1_h`)}<p>{lens.mark!(`${BOOK}_s1_2`)}</p>{lens.before!(`${BOOK}_s6_h`)}</div>);
    const mark = document.querySelector(".gm")!;
    expect(mark.className).toBe("gm gl-core");
    fireEvent.mouseEnter(mark);
    expect(handlers.hover).toHaveBeenCalledWith(expect.objectContaining({ windowId: "w", extractionId: BOOK }));
    fireEvent.click(mark);
    expect(handlers.tap).toHaveBeenCalled();
    expect(document.querySelectorAll(".callout.gcall")).toHaveLength(1);
    expect(document.querySelector(".callout.gcall .lab")!.textContent).toBe("◎ for your goal · core");
  });

  it("a paper's section heads take the light one-line form", () => {
    const paper = indexLens(goal.lens(FIXTURE_SOURCES.paper.extractionId));
    const lens = readerLens({ index: paper, dimOn: true, windowId: "w", handlers, paper: true })!;
    render(<div>{lens.before!(`${FIXTURE_SOURCES.paper.extractionId}_p1_h`)}{lens.mark!(`${FIXTURE_SOURCES.paper.extractionId}_p1_1`)}</div>);
    expect(document.querySelector(".gpcall")!.textContent).toContain("for your goal · core:");
    expect(document.querySelector(".gm")!.className).toBe("gm gl-core gl-paper");
  });

  it("the why card: the level, For <goal>: the reason, the learner's part and the coverage line", () => {
    const section = index!.bySpan.get(`${BOOK}_s1_2`)!;
    render(<WhyCard why={{ section, extractionId: BOOK, windowId: "w", rect: { left: 10, top: 200, right: 13, bottom: 260 } }} band={band()} />);
    const card = document.querySelector(".gwhy")!;
    expect(card.querySelector(".gwh")!.textContent).toBe("core for your goal");
    expect(card.querySelector(".gwr")!.textContent).toBe("For softmax for attention: The formula you'll write: exponentiate each score and divide by the sum.");
    expect(card.querySelector(".gwc")!.textContent).toBe("coverage: introduces “Turn scores into softmax weights” · a goal LO · its primary section · core · judged per section");
  });

  it("the why card of a held section says only the neutral line", () => {
    const section = { ...index!.bySpan.get(`${BOOK}_s1_2`)!, held: true, reasonMd: "A cold check is due on a topic here. Why it matters comes back once you've answered it.", coverageLine: null, learnerLine: null };
    render(<WhyCard why={{ section, extractionId: BOOK, windowId: "w", rect: { left: 10, top: 200, right: 13, bottom: 260 } }} band={band()} />);
    expect(document.querySelector(".gwhy")!.textContent).not.toContain("Turn scores");
  });
});

describe("the why's timing (spec §12.3: 120 ms in; the reference's 160 ms out; a tap toggles)", () => {
  function fakeTimers(): Timers & { tick: (ms: number) => void } {
    let now = 0;
    let queue: Array<{ at: number; fn: () => void; id: number }> = [];
    let next = 0;
    return {
      set: (fn, ms) => { next += 1; queue.push({ at: now + ms, fn, id: next }); return next; },
      clear: (handle) => { queue = queue.filter((entry) => entry.id !== handle); },
      now: () => now,
      tick: (ms) => { now += ms; const due = queue.filter((entry) => entry.at <= now); queue = queue.filter((entry) => entry.at > now); due.forEach((entry) => entry.fn()); },
    };
  }

  it("opens after 120 ms of hover, hides 160 ms after leaving, and a tap toggles it", async () => {
    const goal = new FixtureGoal();
    const transport: GoalTransport = {
      goals: async () => goal.goals(), band: async () => goal.band(), lens: async (input) => goal.lens(input.extractionId),
      sectionChoice: async () => ({}) as never, path: async () => ({}), setDepth: async () => ({}), override: async () => ({}),
      setScope: async () => ({}), scopeDecide: async () => ({}),
    };
    const timers = fakeTimers();
    let desk: ReturnType<typeof useGoalDesk> | null = null;
    const readings = [{ windowId: "w", extractionId: BOOK, paused: false, book: "Softmax, a short book" }];
    const hubFor = () => DIRECT_HUB;
    const mintId = (prefix: string) => `${prefix}_1`;
    const quiet = () => undefined;
    function Probe() {
      desk = useGoalDesk({ transport, deskGoalId: null, offKey: null, onSetGoal: quiet, readings, focused: null,
        padAnchors: [], hubFor, timers, mintId, onError: quiet, onOpen: quiet });
      const lens = desk.lensFor("w", BOOK);
      return <div>{lens?.mark?.(`${BOOK}_s1_2`)}{desk.overlays}</div>;
    }
    render(<Probe />);
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });
    const mark = document.querySelector(".gm")!;
    fireEvent.mouseEnter(mark);
    act(() => timers.tick(WHY_OPEN_MS - 1));
    expect(document.querySelector(".gwhy")).toBeNull();
    act(() => timers.tick(1));
    expect(document.querySelector(".gwhy")).toBeTruthy();
    expect(document.querySelector(".gm")!.className).toContain(" on");
    fireEvent.mouseLeave(document.querySelector(".gm")!);
    act(() => timers.tick(WHY_HIDE_MS - 1));
    expect(document.querySelector(".gwhy")).toBeTruthy();
    act(() => timers.tick(1));
    expect(document.querySelector(".gwhy")).toBeNull();
    fireEvent.click(document.querySelector(".gm")!);
    expect(document.querySelector(".gwhy")).toBeTruthy();
    fireEvent.click(document.querySelector(".gm")!);
    expect(document.querySelector(".gwhy")).toBeNull();
    // esc closes it (through the window's listener hub).
    fireEvent.click(document.querySelector(".gm")!);
    act(() => { fireEvent.keyDown(window, { key: "Escape" }); });
    expect(document.querySelector(".gwhy")).toBeNull();
    expect(desk).not.toBeNull();
  });
});

describe("the path view", () => {
  function props(overrides: Partial<Parameters<typeof PathView>[0]> = {}) {
    const goal = new FixtureGoal();
    const skippable = indexLens(goal.lens(BOOK))!.bySpan.get(`${BOOK}_s6_1`)!;
    return {
      band: goal.band(), here: "lo_fx_softmax", notNeeded: [{ extractionId: BOOK, book: "Softmax, a short book", section: skippable }],
      onClose: vi.fn(), onDepth: vi.fn(), onOpen: vi.fn(), onUseInstead: vi.fn(), onReadAnyway: vi.fn(), onAddPhrase: vi.fn(), ...overrides,
    };
  }

  it("lists each LO with its primary, another way and the depth sizes; marks where you are reading", () => {
    const value = props();
    render(<PathView {...value} />);
    const rows = [...document.querySelectorAll("[data-gp-lo]")].map((row) => row.getAttribute("data-gp-lo"));
    expect(rows).toEqual(["lo_fx_xent", "lo_fx_softmax", "lo_fx_temp", "lo_fx_grad", "lo_fx_attend"]);
    expect(document.querySelector("[data-gp-lo='lo_fx_softmax']")!.className).toBe("gp-lo here");
    expect(screen.getByText("you are reading here")).toBeTruthy();
    expect(screen.getByText(/resolved to/).textContent).toBe("resolved to 3 learning objects, plus 2 prerequisites you haven't shown yet · change: type what's missing or not needed");
    expect(screen.getAllByText(/· 5 sections · 10 min/)).toHaveLength(2);
    expect(screen.getByText(/No deadline, so no pace target; you've averaged 4.2 attempts a day over 14 days./)).toBeTruthy();
    fireEvent.click(screen.getByText("use this one instead"));
    expect(value.onUseInstead).toHaveBeenCalledWith("lo_fx_softmax", expect.objectContaining({ sectionId: `${BOOK}_s2` }));
    fireEvent.click(screen.getByText("1 Scores into weights"));
    expect(value.onOpen).toHaveBeenCalledWith({ extractionId: BOOK, sourceId: FIXTURE_SOURCES.book.sourceId, startSpanId: `${BOOK}_s1_h` });
    fireEvent.click(screen.getByRole("button", { name: "add it" }));
    expect(value.onAddPhrase).toHaveBeenCalledWith("implement");
  });

  it("stores read it anyway on what isn't needed, and closes on esc or p", () => {
    const value = props();
    render(<PathView {...value} />);
    fireEvent.click(screen.getByRole("button", { name: "read it anyway" }));
    expect(value.onReadAnyway).toHaveBeenCalledWith(BOOK, `${BOOK}_s6`, true);
    fireEvent.keyDown(screen.getByRole("dialog", { name: "your path" }), { key: "Escape" });
    fireEvent.keyDown(screen.getByRole("dialog", { name: "your path" }), { key: "p" });
    expect(value.onClose).toHaveBeenCalledTimes(2);
  });

  it("a held LO's row shows no name and no purpose", () => {
    const value = props();
    const held = { ...value.band, learningObjects: value.band.learningObjects!.map((dot, i) => (i === 1 ? { ...dot, title: null, held: true, check: "due" as const } : dot)),
      path: { ...value.band.path!, lines: value.band.path!.lines.map((line) => (line.learningObjectId === "lo_fx_softmax" ? { ...line, reason: null, held: true } : line)) } };
    render(<PathView {...value} band={held} />);
    const row = document.querySelector("[data-gp-lo='lo_fx_softmax']")!;
    expect(row.textContent).not.toContain("Turn scores");
    expect(row.textContent).not.toContain("The formula you'll write");
    expect(row.textContent).toContain("due today");
  });
});
