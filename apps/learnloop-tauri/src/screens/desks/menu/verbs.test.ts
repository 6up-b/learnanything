import { describe, expect, it, vi } from "vitest";
import type { PassageKnowsDto, PromotedRowDto } from "../../../api/dto";
import type { MenuObject } from "./model";
import { promotedRef, runVerb, sourceMenuRows, type MenuContext } from "./verbs";

const passage = (extra: Partial<MenuObject> = {}): MenuObject => ({
  kind: "passage", windowId: "w1", text: "the passage's words", extractionId: "ext1", spanId: "s1", spanIds: ["s1"], sourceId: "src1", at: { x: 5, y: 5 }, ...extra,
});

const knows = (role: string | null, sectionId: string | null): PassageKnowsDto => ({
  objectKey: "k", sourceIds: ["src1"],
  places: [{ extractionId: "ext1", spanId: "s1", role, knows: { spanId: "s1", sectionId } }],
} as unknown as PassageKnowsDto);

function context(over: Partial<MenuContext> = {}, apiOver: Partial<MenuContext["api"]> = {}) {
  const toasts: string[] = [];
  const ctx: MenuContext = {
    deskId: "d1",
    api: {
      passageKnows: vi.fn(async () => knows(null, "sec1")),
      readerCorrespondents: vi.fn(async () => ({ extractionId: "ext1", sectionId: "sec1", status: "judged", learningObjects: [], search: null, checkableLearningObjectIds: [] }) as never),
      readingIdentity: vi.fn(async () => ({ sourceId: "src1", revisionId: "rev1", renderViewId: "rv1" })),
      readerCapture: vi.fn(async () => ({ annotationId: "a1" }) as never),
      readerImportExercise: vi.fn(async () => ({}) as never),
      readerAuthorSectionQuestion: vi.fn(async () => ({ status: "queued", question: null }) as never),
      ...apiOver,
    },
    mintId: (prefix) => `${prefix}_1`,
    toast: (text) => toasts.push(text),
    ask: vi.fn(),
    openSearch: vi.fn(),
    openContent: vi.fn(),
    carry: vi.fn(),
    append: vi.fn(),
    askNote: vi.fn(async () => "my note"),
    confirm: vi.fn(async () => true),
    showMe: vi.fn(async () => ({ figureId: "fig1", line: "a figure" })),
    figureDestination: () => "pad_asked_on",
    landFigure: vi.fn(),
    windowMove: vi.fn(),
    teachMe: vi.fn(),
    showKnows: vi.fn(),
    promotedRows: () => [],
    ...over,
  };
  return { ctx, toasts };
}

const correspondent = (rowId: string): PromotedRowDto => ({
  rowId, kind: "correspondent", glyph: "§", label: "elsewhere", reason: "treats it too", learnerAt: null, checked: true, judgeRank: 1, basis: "judged", extra: {},
  action: { verb: "open", ref: { kind: "source", sourceId: "src2", extractionId: "ext2" }, target: { spanId: "t9" } },
} as unknown as PromotedRowDto);

describe("each verb calls its server entry", () => {
  it("Ask opens the companion on the object; Find searches its words; Carry carries them with the passage", async () => {
    const { ctx } = context();
    await runVerb("ask", passage(), ctx);
    expect(ctx.ask).toHaveBeenCalledWith(expect.objectContaining({ spanId: "s1" }));
    await runVerb("find", passage({ selection: "chosen words" }), ctx);
    expect(ctx.openSearch).toHaveBeenCalledWith("chosen words");
    await runVerb("carry", passage(), ctx);
    expect(ctx.carry).toHaveBeenCalledWith("the passage's words", { kind: "selection", ref: null, anchor: { extractionId: "ext1", spanId: "s1" } });
  });

  it("Note in margin asks for the words, then writes an annotation on the passage through the capture", async () => {
    const { ctx, toasts } = context();
    await runVerb("note", passage({ selection: "some words", slices: [{ spanId: "s1", quote: "some words" }] }), ctx);
    expect(ctx.api.readerCapture).toHaveBeenCalledWith({
      sourceId: "src1", revisionId: "rev1", extractionId: "ext1", renderViewId: "rv1", action: "annotate", clientIdempotencyKey: "note_1", learnerText: "my note",
      rawSelection: { extractionId: "ext1", nodes: [{ spanId: "s1", quote: "some words" }] },
    });
    expect(toasts).toEqual(["noted in the margin"]);
  });

  it("Note in margin on a selection across passages quotes each passage's own words, and says when it could not be placed", async () => {
    const { ctx, toasts } = context({}, { readerCapture: vi.fn(async () => ({ annotationId: "a1", anchorStatus: "needs_reanchor" }) as never) });
    await runVerb("note", passage({ selection: "end of one start of two", spanIds: ["s1", "s2"], slices: [{ spanId: "s1", quote: "end of one" }, { spanId: "s2", quote: "start of two" }] }), ctx);
    expect(ctx.api.readerCapture).toHaveBeenCalledWith(expect.objectContaining({
      rawSelection: { extractionId: "ext1", nodes: [{ spanId: "s1", quote: "end of one" }, { spanId: "s2", quote: "start of two" }] },
    }));
    expect(toasts).toEqual(["noted, but its place in the passage needs re-anchoring"]);
  });

  it("Note in margin left empty writes nothing", async () => {
    const { ctx } = context({ askNote: vi.fn(async () => null) });
    await runVerb("note", passage(), ctx);
    expect(ctx.api.readerCapture).not.toHaveBeenCalled();
  });

  it("Append hands the object to the desk's remembered pad", async () => {
    const { ctx } = context();
    await runVerb("append", passage(), ctx);
    expect(ctx.append).toHaveBeenCalledWith(expect.objectContaining({ spanId: "s1" }), null);
  });

  it("Open beside opens the first promoted correspondent; without one it asks the section's correspondents", async () => {
    const { ctx } = context({ promotedRows: () => [correspondent("r1")] });
    await runVerb("open_beside", passage(), ctx);
    expect(ctx.openContent).toHaveBeenCalledWith({ kind: "source", sourceId: "src2", extractionId: "ext2" }, { spanId: "t9" });
    expect(ctx.api.readerCorrespondents).not.toHaveBeenCalled();

    const section = { extractionId: "ext3", sectionId: "x", title: "3.1", sourceId: "src3", sourceTitle: "another", read: false, jump: { extractionId: "ext3", sectionId: "x", spanId: "u1" } };
    const second = context({}, { readerCorrespondents: vi.fn(async () => ({ extractionId: "ext1", sectionId: "sec1", status: "unchecked", learningObjects: [], search: { label: "", sources: [{ sourceId: "src3", sourceTitle: "another", sections: [section] }], correctableLearningObjectIds: [] }, checkableLearningObjectIds: [] }) as never) });
    await runVerb("open_beside", passage(), second.ctx);
    expect(second.ctx.api.readerCorrespondents).toHaveBeenCalledWith({ extractionId: "ext1", sectionId: "sec1", searchFallback: true });
    expect(second.ctx.openContent).toHaveBeenCalledWith({ kind: "source", sourceId: "src3", extractionId: "ext3" }, { spanId: "u1" });
    expect(second.toasts).toEqual(["found by search, not checked"]);
  });

  it("Compare opens a compare window on the words; Teach me opens a lesson on the passage in the desk's stack", async () => {
    const { ctx } = context();
    await runVerb("compare", passage({ selection: "two ideas" }), ctx);
    expect(ctx.openContent).toHaveBeenCalledWith({ kind: "compare", query: "two ideas" });
    await runVerb("teach_me", passage(), ctx);
    expect(ctx.teachMe).toHaveBeenCalledWith({ kind: "open", entry: "reader_selection", selection: { extractionId: "ext1", spanIds: ["s1"] } });
    // With no passage (a margin note's words alone), the lesson starts from the words.
    await runVerb("teach_me", { kind: "pad_line", windowId: "w1", text: "why the exponential", at: { x: 0, y: 0 } }, ctx);
    expect(ctx.teachMe).toHaveBeenLastCalledWith({ kind: "open", entry: "new_topic", title: "why the exponential" });
  });

  it("Show me lands the shown figure in the running pad; no figure shown, nothing lands", async () => {
    const { ctx } = context();
    await runVerb("show_me", passage(), ctx);
    expect(ctx.showMe).toHaveBeenCalledWith("the passage's words", { extractionId: "ext1", spanId: "s1" }, "w1");
    expect(ctx.landFigure).toHaveBeenCalledWith(expect.objectContaining({ spanId: "s1" }), { figureId: "fig1", line: "a figure" }, "pad_asked_on");
    const none = context({ showMe: vi.fn(async () => null) });
    await runVerb("show_me", passage(), none.ctx);
    expect(none.ctx.landFigure).not.toHaveBeenCalled();
    expect(none.toasts).toContain("no figure for this passage · nothing was shown");
  });

  it("Make it practice imports an exercise as the book has it, otherwise drafts a section question, each after a review", async () => {
    const exercise = context({}, { passageKnows: vi.fn(async () => knows("exercise", "sec1")) });
    await runVerb("make_practice", passage(), exercise.ctx);
    expect(exercise.ctx.confirm).toHaveBeenCalled();
    expect(exercise.ctx.api.readerImportExercise).toHaveBeenCalledWith({
      sourceId: "src1", revisionId: "rev1", extractionId: "ext1", renderViewId: "rv1", clientIdempotencyKey: "import_1",
      rawSelection: { extractionId: "ext1", nodes: [{ spanId: "s1" }] },
    });
    expect(exercise.ctx.api.readerAuthorSectionQuestion).not.toHaveBeenCalled();

    const prose = context();
    await runVerb("make_practice", passage(), prose.ctx);
    expect(prose.ctx.api.readerAuthorSectionQuestion).toHaveBeenCalledWith({ extractionId: "ext1", sectionId: "sec1" });

    const declined = context({ confirm: vi.fn(async () => false) });
    await runVerb("make_practice", passage(), declined.ctx);
    expect(declined.ctx.api.readerAuthorSectionQuestion).not.toHaveBeenCalled();
  });

  it("a window's verbs are the desks' moves on it; What this knows opens the panel", async () => {
    const { ctx } = context();
    const window: MenuObject = { kind: "window", windowId: "w7", text: "A book", at: { x: 0, y: 0 } };
    for (const id of ["new_desk", "gather", "share_slot", "own_slot"] as const) await runVerb(id, window, ctx);
    expect((ctx.windowMove as ReturnType<typeof vi.fn>).mock.calls).toEqual([["new_desk", "w7"], ["gather", "w7"], ["share_slot", "w7"], ["own_slot", "w7"]]);
    await runVerb("knows", window, ctx);
    expect(ctx.showKnows).toHaveBeenCalledWith(window);
  });

  it("a failed call says so instead of throwing", async () => {
    const { ctx, toasts } = context({}, { readerCapture: vi.fn(async () => {
      throw new Error("the reader is away");
    }) });
    await runVerb("note", passage(), ctx);
    expect(toasts).toEqual(["couldn't do that just now · the reader is away"]);
  });
});

describe("the verb rows and a promoted row's place", () => {
  it("names the Append target and marks What this knows as the design aid", () => {
    const rows = sourceMenuRows(passage(), context().ctx, "running · 23 Nov");
    expect(rows.find((row) => row.id === "append")).toMatchObject({ label: "Append to “running · 23 Nov”  ▸", submenu: true, key: "w" });
    expect(rows.find((row) => row.id === "knows")).toMatchObject({ aid: true });
  });

  it("reads a promoted row's ref into a content ref (camel case either way), a video's time kept", () => {
    expect(promotedRef(correspondent("r1"))).toEqual({ ref: { kind: "source", sourceId: "src2", extractionId: "ext2" }, spanId: "t9" });
    const video = { ...correspondent("r2"), action: { verb: "open", ref: { kind: "video", source_id: "v", extraction_id: "ve" }, target: { spanId: null, t: 30 } } } as unknown as PromotedRowDto;
    expect(promotedRef(video)).toEqual({ ref: { kind: "video", sourceId: "v", extractionId: "ve", t: 30 }, spanId: null });
    expect(promotedRef({ ...correspondent("r3"), action: { verb: "knows" } } as unknown as PromotedRowDto)).toBeNull();
  });
});
