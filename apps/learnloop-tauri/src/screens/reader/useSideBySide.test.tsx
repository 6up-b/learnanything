// Reader CA6: side by side's leader rule and follow along (ux_reader_compare_ask_v1
// §6.4, K14, C5). The following pane moves only when the leading pane crosses
// into a new section, once, to its book's first judged correspondent; never
// mid-section, never the last-touched pane, never to an unchecked search hit.
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { CorrespondentSectionDto, CorrespondentsDto, SideBySideSectionDto } from "../../api/dto";
import { flushReaderActivity, resetReaderActivityForTests, setReaderActivityEnabled } from "./activity";
import { crumbLabel, firstCorrespondent, firstJudgedIn, sectionShort, type PaneTarget } from "./sideBySide";
import { SIDE_BY_SIDE_COPY, useSideBySide, type CurrentEntry, type MainPane, type SideBySideInput } from "./useSideBySide";

const { api } = vi.hoisted(() => ({
  api: { readerSideBySideSection: vi.fn(), readerCorrespondents: vi.fn(), readerLogActivity: vi.fn() },
}));
vi.mock("../../api/client", () => ({ api }));

function hit(sourceId: string, sourceTitle: string, extractionId: string, sectionId: string, title: string, by: CorrespondentSectionDto["by"] = "judge"): CorrespondentSectionDto {
  return { extractionId, sectionId, title, sourceId, sourceTitle, read: false, jump: { extractionId, sectionId, spanId: `${sectionId}_s1` }, treatment: by === "search" ? null : "develops", by };
}
function judged(extractionId: string, sectionId: string, sections: CorrespondentSectionDto[]): CorrespondentsDto {
  return {
    extractionId, sectionId, status: "judged", search: null, checkableLearningObjectIds: ["lo_1"],
    learningObjects: [{ learningObjectId: "lo_1", title: "eigenvalues", sources: [...new Set(sections.map((s) => s.sourceId))].map((sourceId) => ({
      sourceId, sourceTitle: sections.find((s) => s.sourceId === sourceId)!.sourceTitle, sections: sections.filter((s) => s.sourceId === sourceId),
    })) }],
  };
}
function unchecked(extractionId: string, sectionId: string, sections: CorrespondentSectionDto[]): CorrespondentsDto {
  return {
    extractionId, sectionId, status: "unchecked", learningObjects: [], checkableLearningObjectIds: [],
    search: { label: "found by search, not checked", correctableLearningObjectIds: [], sources: [{ sourceId: sections[0].sourceId, sourceTitle: sections[0].sourceTitle, sections }] },
  };
}
function sectionDto(extractionId: string, sectionId: string, title: string): SideBySideSectionDto {
  return {
    extractionId, sectionId, sourceId: "src_axler", sourceTitle: "Axler", title, jumpSpanId: `${sectionId}_s1`, page: null,
    blocks: [{ spanId: `${sectionId}_s1`, blockType: "Text", page: null, text: `text of ${title}` }],
    previous: null, next: { sectionId: "ax5c", title: "5.C Eigenspaces" }, exposureEventIds: ["e1"],
  };
}

const AX5A: PaneTarget = { sourceId: "src_axler", sourceTitle: "Axler", extractionId: "ext_axler", sectionId: "ax5a", title: "5.A Invariant subspaces", spanId: "ax5a_s1", by: "judged" };
const STRANG = (sectionId: string | null): MainPane => ({ sourceId: "src_strang", sourceTitle: "Strang", extractionId: "ext_strang", sectionId });

function setup(overrides: Partial<SideBySideInput> = {}) {
  const jumpMain = vi.fn();
  // The crumb entries, as the return stack would hold them.
  const entries = new Map<string, CurrentEntry>();
  const pushCrumb = vi.fn((label: string, target: PaneTarget) => {
    const id = `crumb:${label}`;
    entries.set(id, { id, kind: "side_by_side", sourceId: props.main?.sourceId ?? "", sideBySide: target });
    return id;
  });
  const replaceCrumb = vi.fn((entryId: string, _label: string, target: PaneTarget) => {
    const entry = entries.get(entryId);
    if (!entry || props.currentEntry?.id !== entryId) return false;
    entries.set(entryId, { ...entry, sideBySide: target });
    return true;
  });
  const dropCrumb = vi.fn();
  const onError = vi.fn();
  const initial: SideBySideInput = { enabled: true, main: STRANG("st61"), jumpMain, pushCrumb, replaceCrumb, dropCrumb, currentEntry: null, onError, ...overrides };
  const props = { ...initial };
  const hook = renderHook((p: SideBySideInput) => useSideBySide(p), { initialProps: initial });
  const rerender = (patch: Partial<SideBySideInput>) => {
    Object.assign(props, patch);
    hook.rerender({ ...props });
  };
  const entry = (id: string | null) => (id ? entries.get(id) ?? null : null);
  return { hook, jumpMain, pushCrumb, replaceCrumb, dropCrumb, onError, rerender, props, entry };
}

function events(): Array<{ event: string; payload: Record<string, unknown> }> {
  flushReaderActivity();
  return api.readerLogActivity.mock.calls.flatMap((call) => call[0].events)
    .filter((entry: { kind: string }) => entry.kind === "reader_action_invoked");
}

async function openPanes(ctx: ReturnType<typeof setup>) {
  act(() => ctx.hook.result.current.open(AX5A, "find_list"));
  // The crumb is the current entry, as the return stack would make it.
  ctx.rerender({ currentEntry: ctx.entry(ctx.pushCrumb.mock.results[0]?.value ?? null) });
  await waitFor(() => expect(ctx.hook.result.current.phase).toBe("ready"));
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  resetReaderActivityForTests();
  setReaderActivityEnabled(true);
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  api.readerSideBySideSection.mockImplementation(async (input: { extractionId: string; sectionId: string }) => ({
    section: sectionDto(input.extractionId, input.sectionId, input.sectionId === "ax5c" ? "5.C Eigenspaces" : "5.A Invariant subspaces"),
  }));
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 1400 });
});
afterEach(() => { cleanup(); resetReaderActivityForTests(); });

// -- the pure parts --------------------------------------------------------------------------------

it("follow along reads judged coverage only, first in the API's order for the follower's book", () => {
  const view = judged("ext_strang", "st62", [hit("src_lay", "Lay", "ext_lay", "lay52", "5.2"), hit("src_axler", "Axler", "ext_axler", "ax5c", "5.C"), hit("src_axler", "Axler", "ext_axler", "ax5d", "5.D")]);
  expect(firstJudgedIn(view, "src_axler")?.sectionId).toBe("ax5c");
  expect(firstJudgedIn(view, "src_none")).toBeNull();
  // An unchecked search hit never moves a pane.
  expect(firstJudgedIn(unchecked("ext_strang", "st62", [hit("src_axler", "Axler", "ext_axler", "ax5c", "5.C", "search")]), "src_axler")).toBeNull();
  // Ctrl+\: the first correspondent; with nothing judged, the first hit the learner asked for.
  expect(firstCorrespondent(view)?.sectionId).toBe("lay52");
  expect(firstCorrespondent(unchecked("e", "s", [hit("src_axler", "Axler", "ext_axler", "ax5c", "5.C", "search")]))?.by).toBe("search");
  expect(firstCorrespondent({ ...view, status: "none", learningObjects: [] })).toBeNull();
  expect(crumbLabel(AX5A)).toBe("side by side with Axler §5.A");
  expect(sectionShort("Invariant subspaces")).toBe("Invariant subspaces");
});

// -- opening, the crumb, the records -------------------------------------------------------------------

it("opening pushes the crumb, reads the section and records side_by_side_opened", async () => {
  const ctx = setup();
  await openPanes(ctx);
  expect(ctx.pushCrumb).toHaveBeenCalledWith("side by side with Axler §5.A", AX5A);
  expect(api.readerSideBySideSection).toHaveBeenCalledWith({ extractionId: "ext_axler", sectionId: "ax5a" });
  expect(ctx.hook.result.current.panes).toBe(true);
  expect(ctx.hook.result.current.leader).toBe("main");
  expect(ctx.hook.result.current.follow).toBe(true);
  expect(events()).toEqual([expect.objectContaining({ event: "side_by_side_opened", payload: expect.objectContaining({
    extraction_id: "ext_strang", section_id: "st61", target_source_id: "src_axler", target_section_id: "ax5a", by: "judged", via: "find_list",
  }) })]);
});

it("closing drops the crumb; walking off the crumb closes, walking back onto it reopens", async () => {
  const ctx = setup();
  await openPanes(ctx);
  const crumb = ctx.props.currentEntry?.id as string;
  ctx.rerender({ currentEntry: { id: "origin", kind: "origin", sourceId: "src_strang" } });
  expect(ctx.hook.result.current.panes).toBe(false);
  const reads = api.readerSideBySideSection.mock.calls.length;
  ctx.rerender({ currentEntry: ctx.entry(crumb) });
  await waitFor(() => expect(ctx.hook.result.current.panes).toBe(true));
  expect(api.readerSideBySideSection.mock.calls.length).toBe(reads + 1);
  expect(ctx.pushCrumb).toHaveBeenCalledTimes(1);
  act(() => ctx.hook.result.current.close());
  expect(ctx.dropCrumb).toHaveBeenCalledWith(crumb);
  expect(ctx.hook.result.current.panes).toBe(false);
});

// -- follow along at boundaries only (K14) ---------------------------------------------------------------

it("a crossing in the leading pane moves the follower once, to its first judged correspondent", async () => {
  const ctx = setup();
  await openPanes(ctx);
  api.readerCorrespondents.mockResolvedValue(judged("ext_strang", "st62", [hit("src_axler", "Axler", "ext_axler", "ax5c", "5.C Eigenspaces")]));
  ctx.rerender({ main: STRANG("st62") });
  await waitFor(() => expect(api.readerSideBySideSection).toHaveBeenLastCalledWith({ extractionId: "ext_axler", sectionId: "ax5c" }));
  expect(api.readerCorrespondents).toHaveBeenCalledTimes(1);
  expect(api.readerCorrespondents).toHaveBeenCalledWith({ extractionId: "ext_strang", sectionId: "st62", searchFallback: false });
  await waitFor(() => expect(ctx.hook.result.current.target?.title).toBe("5.C Eigenspaces"));
  // The leader never moves on its own.
  expect(ctx.jumpMain).not.toHaveBeenCalled();
  expect(events().map((e) => e.event)).toContain("follow_along_moved");
  expect(events().find((e) => e.event === "follow_along_moved")?.payload).toMatchObject({ leader: "main", section_id: "st62", target_section_id: "ax5c", by: "judged" });
});

it("mid-section scrolling in the leader moves nothing", async () => {
  const ctx = setup();
  await openPanes(ctx);
  // The same section, new renders (the learner scrolling inside §6.1).
  ctx.rerender({ main: STRANG("st61") });
  ctx.rerender({ main: STRANG("st61") });
  await act(async () => { await Promise.resolve(); });
  expect(api.readerCorrespondents).not.toHaveBeenCalled();
  expect(api.readerSideBySideSection).toHaveBeenCalledTimes(1);
});

it("the last-touched pane leads and is never moved", async () => {
  const ctx = setup();
  await openPanes(ctx);
  act(() => ctx.hook.result.current.touch("side"));
  expect(ctx.hook.result.current.leader).toBe("side");
  // The main pane crosses without the learner's hand on it: it is the follower, nothing moves.
  ctx.rerender({ main: STRANG("st62") });
  await act(async () => { await Promise.resolve(); });
  expect(api.readerCorrespondents).not.toHaveBeenCalled();
  // The side pane crosses (the learner moves it on): the main pane follows.
  api.readerCorrespondents.mockResolvedValue(judged("ext_axler", "ax5c", [hit("src_strang", "Strang", "ext_strang", "st63", "6.3 Applications")]));
  act(() => ctx.hook.result.current.goSide("ax5c"));
  await waitFor(() => expect(ctx.jumpMain).toHaveBeenCalledWith("st63_s1"));
  expect(api.readerCorrespondents).toHaveBeenCalledWith({ extractionId: "ext_axler", sectionId: "ax5c", searchFallback: false });
  expect(ctx.jumpMain).toHaveBeenCalledTimes(1);
});

it("an answer that lands after the learner touched the follower is dropped", async () => {
  const ctx = setup();
  await openPanes(ctx);
  let answer: (view: CorrespondentsDto) => void = () => undefined;
  api.readerCorrespondents.mockImplementation(() => new Promise((resolve) => { answer = resolve; }));
  ctx.rerender({ main: STRANG("st62") });
  await waitFor(() => expect(api.readerCorrespondents).toHaveBeenCalled());
  act(() => ctx.hook.result.current.touch("side"));
  await act(async () => { answer(judged("ext_strang", "st62", [hit("src_axler", "Axler", "ext_axler", "ax5c", "5.C")])); await Promise.resolve(); });
  expect(api.readerSideBySideSection).toHaveBeenCalledTimes(1);
  expect(events().map((e) => e.event)).not.toContain("follow_along_moved");
});

it("with no matching section the follower stays put and says so until the learner moves it", async () => {
  const ctx = setup();
  await openPanes(ctx);
  api.readerCorrespondents.mockResolvedValue({ ...judged("ext_strang", "st62", []), status: "none", learningObjects: [] });
  ctx.rerender({ main: STRANG("st62") });
  await waitFor(() => expect(ctx.hook.result.current.staysPut).toBe("side"));
  expect(api.readerSideBySideSection).toHaveBeenCalledTimes(1);
  expect(SIDE_BY_SIDE_COPY.staysPut).toBe("no matching section here · stays put");
  act(() => ctx.hook.result.current.touch("side"));
  expect(ctx.hook.result.current.staysPut).toBeNull();
});

it("an unchecked search hit never moves a pane", async () => {
  const ctx = setup();
  await openPanes(ctx);
  api.readerCorrespondents.mockResolvedValue(unchecked("ext_strang", "st62", [hit("src_axler", "Axler", "ext_axler", "ax5c", "5.C", "search")]));
  ctx.rerender({ main: STRANG("st62") });
  await waitFor(() => expect(ctx.hook.result.current.staysPut).toBe("side"));
  expect(api.readerSideBySideSection).toHaveBeenCalledTimes(1);
});

it("follow along off: crossings move nothing", async () => {
  const ctx = setup();
  await openPanes(ctx);
  act(() => ctx.hook.result.current.toggleFollow());
  expect(ctx.hook.result.current.follow).toBe(false);
  ctx.rerender({ main: STRANG("st62") });
  await act(async () => { await Promise.resolve(); });
  expect(api.readerCorrespondents).not.toHaveBeenCalled();
});

// -- the narrow window, the switch ----------------------------------------------------------------------

it("in a narrow window side by side is a peek: no crumb, the sheet, corresponding_section_peeked", async () => {
  Object.defineProperty(window, "innerWidth", { configurable: true, value: 900 });
  const ctx = setup();
  act(() => ctx.hook.result.current.open(AX5A, "key"));
  await waitFor(() => expect(ctx.hook.result.current.phase).toBe("ready"));
  expect(ctx.hook.result.current.sheet).toBe(true);
  expect(ctx.hook.result.current.panes).toBe(false);
  expect(ctx.pushCrumb).not.toHaveBeenCalled();
  expect(events().map((e) => e.event)).toEqual(["corresponding_section_peeked"]);
  // Nothing follows in a peek.
  ctx.rerender({ main: STRANG("st62") });
  await act(async () => { await Promise.resolve(); });
  expect(api.readerCorrespondents).not.toHaveBeenCalled();
});

it("switched off, opening does nothing and nothing is read", async () => {
  const ctx = setup({ enabled: false });
  act(() => ctx.hook.result.current.open(AX5A, "find_list"));
  await act(async () => { await ctx.hook.result.current.openFirst(); });
  expect(ctx.hook.result.current.panes || ctx.hook.result.current.sheet).toBe(false);
  expect(api.readerSideBySideSection).not.toHaveBeenCalled();
  expect(api.readerCorrespondents).not.toHaveBeenCalled();
  expect(ctx.pushCrumb).not.toHaveBeenCalled();
});

it("Ctrl+\\'s open reads the section in view and opens its first correspondent", async () => {
  const ctx = setup();
  api.readerCorrespondents.mockResolvedValue(judged("ext_strang", "st61", [hit("src_axler", "Axler", "ext_axler", "ax5a", "5.A Invariant subspaces")]));
  await act(async () => { await ctx.hook.result.current.openFirst(); });
  expect(api.readerCorrespondents).toHaveBeenCalledWith({ extractionId: "ext_strang", sectionId: "st61", searchFallback: true });
  expect(ctx.pushCrumb).toHaveBeenCalledWith("side by side with Axler §5.A", expect.objectContaining({ sectionId: "ax5a" }));
  // Nothing to open: one dim line, nothing else.
  const empty = setup();
  api.readerCorrespondents.mockResolvedValue({ ...judged("ext_strang", "st61", []), status: "none", learningObjects: [] });
  await act(async () => { await empty.hook.result.current.openFirst(); });
  expect(empty.hook.result.current.notice).toBe(SIDE_BY_SIDE_COPY.nothing);
  expect(empty.pushCrumb).not.toHaveBeenCalled();
});

// -- Codex review fixes (F3-F6, F8) -------------------------------------------------------------------

function deferredCorrespondents() {
  const answers: Array<(view: CorrespondentsDto) => void> = [];
  api.readerCorrespondents.mockImplementation(() => new Promise((resolve) => { answers.push(resolve); }));
  return answers;
}

it("F3: switching leaders twice drops the first leader's pending follow request", async () => {
  const ctx = setup();
  await openPanes(ctx);
  const answers = deferredCorrespondents();
  ctx.rerender({ main: STRANG("st62") });
  await waitFor(() => expect(answers).toHaveLength(1));
  // The learner scrolls the side pane, then clicks the main pane again, with no new crossing.
  act(() => ctx.hook.result.current.touch("side"));
  act(() => ctx.hook.result.current.touch("main"));
  expect(ctx.hook.result.current.leader).toBe("main");
  await act(async () => { answers[0](judged("ext_strang", "st62", [hit("src_axler", "Axler", "ext_axler", "ax5c", "5.C")])); await Promise.resolve(); });
  // The side pane keeps the position the learner chose.
  expect(api.readerSideBySideSection).toHaveBeenCalledTimes(1);
  expect(ctx.hook.result.current.target?.sectionId).toBe("ax5a");
  expect(events().map((e) => e.event)).not.toContain("follow_along_moved");
});

it("F4: a Ctrl+\\ read pending when side by side becomes ineligible never opens it", async () => {
  const ctx = setup();
  const answers = deferredCorrespondents();
  let pending: Promise<void> = Promise.resolve();
  act(() => { pending = ctx.hook.result.current.openFirst(); });
  await waitFor(() => expect(answers).toHaveLength(1));
  // The working posture (or the switch off) before the answer lands; same section and reading.
  ctx.rerender({ enabled: false });
  await act(async () => { answers[0](judged("ext_strang", "st61", [hit("src_axler", "Axler", "ext_axler", "ax5a", "5.A")])); await pending; });
  expect(ctx.pushCrumb).not.toHaveBeenCalled();
  expect(api.readerSideBySideSection).not.toHaveBeenCalled();
  // Back to reading: nothing reappears on its own.
  ctx.rerender({ enabled: true });
  expect(ctx.hook.result.current.panes || ctx.hook.result.current.sheet).toBe(false);
});

it("F4: a pending Ctrl+\\ read is superseded by an open the learner made meanwhile", async () => {
  const ctx = setup();
  const answers = deferredCorrespondents();
  let pending: Promise<void> = Promise.resolve();
  act(() => { pending = ctx.hook.result.current.openFirst(); });
  await waitFor(() => expect(answers).toHaveLength(1));
  act(() => ctx.hook.result.current.open(AX5A, "find_list"));
  await act(async () => { answers[0](judged("ext_strang", "st61", [hit("src_lay", "Lay", "ext_lay", "lay52", "5.2")])); await pending; });
  expect(ctx.pushCrumb).toHaveBeenCalledTimes(1);
  expect(ctx.hook.result.current.target?.sourceId).toBe("src_axler");
});

it("F5: a source detour keeps the pair; walking back onto the crumb reopens it", async () => {
  const ctx = setup();
  await openPanes(ctx);
  const crumb = ctx.props.currentEntry?.id as string;
  // A source detour to another book: its entry is current, then the main pane holds that book.
  ctx.rerender({ currentEntry: { id: "detour_c", kind: "source", sourceId: "src_lay" } });
  ctx.rerender({ main: { sourceId: "src_lay", sourceTitle: "Lay", extractionId: "ext_lay", sectionId: "lay1" } });
  expect(ctx.hook.result.current.panes).toBe(false);
  // Alt+← onto the crumb: the stack moves first, then the source reopens.
  ctx.rerender({ currentEntry: ctx.entry(crumb) });
  expect(ctx.hook.result.current.panes).toBe(false);
  ctx.rerender({ main: STRANG("st61") });
  await waitFor(() => expect(ctx.hook.result.current.panes).toBe(true));
  expect(ctx.hook.result.current.target?.sectionId).toBe("ax5a");
  expect(ctx.pushCrumb).toHaveBeenCalledTimes(1);
  expect(ctx.dropCrumb).not.toHaveBeenCalled();
});

it("F6: opening another book beside the same passage replaces the pair on the same crumb", async () => {
  const ctx = setup();
  await openPanes(ctx);
  const crumb = ctx.props.currentEntry?.id as string;
  const LAY: PaneTarget = { sourceId: "src_lay", sourceTitle: "Lay", extractionId: "ext_lay", sectionId: "lay52", title: "5.2 The characteristic equation", spanId: "lay52_s1", by: "judged" };
  act(() => ctx.hook.result.current.open(LAY, "find_list"));
  expect(ctx.replaceCrumb).toHaveBeenCalledWith(crumb, "side by side with Lay §5.2", LAY);
  expect(ctx.pushCrumb).toHaveBeenCalledTimes(1);
  expect(ctx.entry(crumb)?.sideBySide).toEqual(LAY);
  ctx.rerender({ currentEntry: ctx.entry(crumb) });
  expect(ctx.hook.result.current.target?.sourceId).toBe("src_lay");
  // Closing takes that one crumb off.
  act(() => ctx.hook.result.current.close());
  expect(ctx.dropCrumb).toHaveBeenCalledWith(crumb);
});

it("F8: a session records its id, the visit and how long it was open; an undone follow move is recorded", async () => {
  const visitPayload = () => ({ visit_id: "visit_1" });
  const ctx = setup({ visitPayload });
  await openPanes(ctx);
  api.readerCorrespondents.mockResolvedValue(judged("ext_strang", "st62", [hit("src_axler", "Axler", "ext_axler", "ax5c", "5.C Eigenspaces")]));
  ctx.rerender({ main: STRANG("st62") });
  await waitFor(() => expect(ctx.hook.result.current.target?.sectionId).toBe("ax5c"));
  // The learner takes the side pane back to the section it was on.
  act(() => ctx.hook.result.current.goSide("ax5a"));
  act(() => ctx.hook.result.current.close());
  const recorded = events();
  const opened = recorded.find((e) => e.event === "side_by_side_opened")!.payload;
  expect(opened).toMatchObject({ visit_id: "visit_1", detour_id: ctx.props.currentEntry?.id });
  const session = opened.side_by_side_id;
  expect(typeof session).toBe("string");
  expect(recorded.find((e) => e.event === "follow_along_moved")?.payload).toMatchObject({ visit_id: "visit_1", side_by_side_id: session });
  expect(recorded.find((e) => e.event === "follow_along_undone")?.payload).toMatchObject({
    side_by_side_id: session, leader: "side", section_id: "ax5c", target_section_id: "ax5a", seconds_after: expect.any(Number),
  });
  expect(recorded.find((e) => e.event === "side_by_side_closed")?.payload).toMatchObject({
    visit_id: "visit_1", side_by_side_id: session, via: "close", seconds_open: expect.any(Number),
  });
});

it("F8: moving the followed pane on elsewhere is not an undo", async () => {
  const ctx = setup();
  await openPanes(ctx);
  api.readerCorrespondents.mockResolvedValue(judged("ext_strang", "st62", [hit("src_axler", "Axler", "ext_axler", "ax5c", "5.C Eigenspaces")]));
  ctx.rerender({ main: STRANG("st62") });
  await waitFor(() => expect(ctx.hook.result.current.target?.sectionId).toBe("ax5c"));
  act(() => ctx.hook.result.current.goSide("ax5d"));
  act(() => ctx.hook.result.current.goSide("ax5a"));
  expect(events().map((e) => e.event)).not.toContain("follow_along_undone");
});
