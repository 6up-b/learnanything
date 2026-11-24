// While an inline check is open, what would reveal veiled material or send it to a model waits (spec §12.6.4; the
// record lists the call per verb): the menu's verbs that quote, search, explain, teach or open more are disabled with
// the reason and refuse if reached by key; carrying, appending, a margin note and moving windows still work; a pen
// reading waits with the reason.
import { describe, expect, it, vi } from "vitest";
import { Poller } from "../../../api/poller";
import type { MenuObject } from "../menu/model";
import { CHECK_HELD_VERBS, runVerb, sourceMenuRows, type MenuContext } from "../menu/verbs";
import { InkCache } from "../pen/inkCache";

const HELD = "after your check · it is open on this desk";
const passage: MenuObject = { kind: "passage", windowId: "w1", text: "the words", extractionId: "ext1", spanId: "s1", spanIds: ["s1"], sourceId: "src1", at: { x: 5, y: 5 } };

function context(held: string | null) {
  const toasts: string[] = [];
  const ctx = {
    deskId: "d1", api: {}, mintId: (prefix: string) => `${prefix}_1`, toast: (text: string) => toasts.push(text),
    ask: vi.fn(), openSearch: vi.fn(), openContent: vi.fn(), carry: vi.fn(), append: vi.fn(), askNote: vi.fn(async () => null), confirm: vi.fn(async () => true),
    showMe: vi.fn(async () => null), figureDestination: () => "pad_asked_on", landFigure: vi.fn(), windowMove: vi.fn(), teachMe: vi.fn(), reviewExercise: vi.fn(),
    showKnows: vi.fn(), promotedRows: () => [], withheld: async () => false, heldReason: () => held,
  } as unknown as MenuContext;
  return { ctx, toasts };
}

describe("the menu while a check is open", () => {
  it("disables the verbs that would reveal or send veiled material, with the reason, and leaves the rest", () => {
    const rows = sourceMenuRows(passage, context(HELD).ctx, "running");
    const disabled = rows.filter((row) => row.disabled).map((row) => row.id).sort();
    const offered = rows.map((row) => row.id).filter((id) => (CHECK_HELD_VERBS as readonly string[]).includes(id)).sort();
    expect(disabled).toEqual(offered);
    expect(offered).toEqual(expect.arrayContaining(["ask", "find", "show_me", "teach_me"]));
    expect(rows.find((row) => row.id === "ask")?.note).toBe(HELD);
    expect(rows.find((row) => row.id === "carry")?.disabled).toBeFalsy();
    expect(sourceMenuRows(passage, context(null).ctx, "running").some((row) => row.disabled)).toBe(false);
  });

  it("a held verb reached by key says why and does nothing; carry still carries", async () => {
    const { ctx, toasts } = context(HELD);
    await runVerb("ask", passage, ctx);
    await runVerb("find", passage, ctx);
    await runVerb("teach_me", passage, ctx);
    expect(ctx.ask).not.toHaveBeenCalled();
    expect(ctx.openSearch).not.toHaveBeenCalled();
    expect(ctx.teachMe).not.toHaveBeenCalled();
    expect(toasts).toEqual([`this waits · ${HELD}`, `this waits · ${HELD}`, `this waits · ${HELD}`]);
    await runVerb("carry", passage, ctx);
    expect(ctx.carry).toHaveBeenCalled();
  });
});

describe("the open check and a verb's own verdict compose", () => {
  it("a held verb waits for the check first and never asks for its verdict; after the check, the verdict (per verb) decides", async () => {
    const { ctx, toasts } = context(HELD);
    const withheld = vi.fn(async (verb?: string) => verb === "ask");
    (ctx as { withheld: unknown }).withheld = withheld;
    await runVerb("ask", passage, ctx);
    expect(withheld).not.toHaveBeenCalled();
    expect(toasts).toEqual([`this waits · ${HELD}`]);
    // The check answered: the same verb now waits for its own verdict, which refuses it; another verb's verdict lets it run.
    (ctx as { heldReason: () => string | null }).heldReason = () => null;
    await runVerb("ask", passage, ctx);
    expect(withheld).toHaveBeenCalledWith("ask");
    expect(ctx.ask).not.toHaveBeenCalled();
    expect(toasts[1]).toBe("this is exam or held-out material: its words are not sent anywhere from here");
    // A verb the check never held (carry) runs during the check only once its own verdict clears it.
    const during = context(HELD);
    const verdict = vi.fn(async () => false);
    (during.ctx as { withheld: unknown }).withheld = verdict;
    await runVerb("carry", passage, during.ctx);
    expect(during.ctx.carry).toHaveBeenCalled();
  });
});

describe("a pen reading while a check is open", () => {
  it("waits with the reason and sends nothing", async () => {
    const inkTranscribe = vi.fn();
    let held: string | null = HELD;
    const cache = new InkCache({ api: { inkList: vi.fn(async () => ({ owners: [] })), inkTranscribe, inkTranscribeJob: vi.fn(), inkTranscribeCancel: vi.fn() } as never,
      poller: new Poller({ setInterval: () => 1, clearInterval: () => undefined }), settled: async () => "saved", refreshPad: async () => undefined, held: () => held });
    cache.addStrokes("p", "b1", "ink_1", [{ strokeId: "s1", points: [[1, 2, 0, 0.5, 0, 0], [3, 4, 8, 0.5, 0, 0]] }]);
    await cache.read("p", "b1", null);
    expect(inkTranscribe).not.toHaveBeenCalled();
    expect(cache.pad("p").readings.b1).toMatchObject({ status: "failed", message: `read it ${HELD}` });
    held = null;
    inkTranscribe.mockResolvedValue({ version: 1, jobId: null, status: "done", done: true, result: null, error: null });
    await cache.read("p", "b1", null);
    expect(inkTranscribe).toHaveBeenCalled();
  });
});
