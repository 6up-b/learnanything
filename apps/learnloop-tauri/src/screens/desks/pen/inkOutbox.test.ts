// Ink saves in the client's one write sequence (spec §3.4, §3.5; RD8a): numbered with desk and pad batches, sent in
// order, kept until acknowledged, retried when the sidecar is unreachable, and carried through a reconcile.
import { describe, expect, it, vi } from "vitest";
import type { DeskStateDto, InkSaveInput } from "../../../api/dto";
import { DeskOutbox } from "../outbox";
import { DeskStore } from "../store";

const INK = {
  owner: { annotationId: "ann_1" },
  inkId: "ink_1",
  strokes: [{ strokeId: "s1", points: [[1, 2, 0, 0.5, 0, 0]] as Array<[number, number, number, number, number, number]> }],
  pointerMeta: { pointerType: "pen" as const, devicePixelRatio: 2 },
};
const okInk = (input: InkSaveInput) => Promise.resolve({ version: 1, appliedSeq: input.seq, inkId: input.inkId, results: [{ status: "ok" as const, duplicate: false }] });

describe("ink in the outbox", () => {
  it("takes the next number after desk and pad batches and is sent with its client and number", async () => {
    const sent: Array<[string, number]> = [];
    const transport = {
      apply: vi.fn(async (input) => { sent.push(["desk", input.seq]); return { version: 1, appliedSeq: input.seq, results: [{ status: "ok" as const }], versions: [] }; }),
      applyPad: vi.fn(async (input) => { sent.push(["pad", input.seq]); return { version: 1, appliedSeq: input.seq, results: [{ status: "ok" as const }], heads: [], pads: [] }; }),
      applyInk: vi.fn(async (input: InkSaveInput) => { sent.push(["ink", input.seq]); return okInk(input); }),
    };
    const outbox = new DeskOutbox("c1", transport as never);
    outbox.enqueue([{ op: "set_focus", deskId: "d", expectedVersion: 1, windowId: "w" } as never]);
    expect(outbox.enqueueInk(INK)).toBe(2);
    outbox.enqueuePad("p", [{ op: "keep", expectedVersion: 1 }]);
    const outcome = await outbox.flush();
    expect(outcome.kind).toBe("applied");
    expect(sent).toEqual([["desk", 1], ["ink", 2], ["pad", 3]]);
    expect(transport.applyInk).toHaveBeenCalledWith({ clientId: "c1", seq: 2, ...INK });
    expect(outbox.pending).toBe(0);
  });

  it("stays queued while the sidecar is unreachable and is sent again unchanged", async () => {
    let up = false;
    const applyInk = vi.fn(async (input: InkSaveInput) => {
      if (!up) throw new Error("sidecar restarting");
      return okInk(input);
    });
    const outbox = new DeskOutbox("c1", { apply: vi.fn(), applyInk } as never);
    outbox.enqueueInk(INK);
    expect((await outbox.flush()).kind).toBe("offline");
    expect(outbox.pending).toBe(1);
    up = true;
    expect((await outbox.flush()).kind).toBe("applied");
    expect(applyInk.mock.calls.map(([input]) => [input.seq, input.inkId])).toEqual([[1, "ink_1"], [1, "ink_1"]]);
  });

  it("a refused ink save leaves the queue and the ones after it are still sent", async () => {
    const applyInk = vi.fn(async (input: InkSaveInput) => (input.inkId === "ink_bad"
      ? { version: 1, appliedSeq: input.seq, inkId: input.inkId, results: [{ status: "refused" as const, code: "annotation_not_found", message: "gone" }] }
      : okInk(input)));
    const state: DeskStateDto = { version: 1, desks: [], runningPadIds: [], serverSeq: [] } as unknown as DeskStateDto;
    const timers = { set: vi.fn(() => 1), clear: vi.fn(), now: () => 0 };
    const store = new DeskStore("c1", { apply: vi.fn(), applyInk, state: vi.fn(async () => ({ ...state, serverSeq: [{ clientId: "c1", seq: applyInk.mock.calls.length }] })) } as never, timers);
    store.commitInk({ ...INK, inkId: "ink_bad" });
    store.commitInk({ ...INK, inkId: "ink_2" });
    expect(await store.settled()).toBe("saved");
    expect(applyInk.mock.calls.map(([input]) => [input.seq, input.inkId])).toEqual([[1, "ink_bad"], [2, "ink_2"]]);
  });

  it("an ink erase takes its number in the same sequence and is sent as ink.erase", async () => {
    const sent: Array<[string, number]> = [];
    const outbox = new DeskOutbox("c1", {
      apply: vi.fn(),
      applyInk: vi.fn(async (input: InkSaveInput) => { sent.push(["ink", input.seq]); return okInk(input); }),
      applyInkErase: vi.fn(async (input) => { sent.push(["erase", input.seq]); return { version: 1, appliedSeq: input.seq, eraseId: input.eraseId, results: [{ status: "ok" as const, duplicate: false }] }; }),
    } as never);
    outbox.enqueueInk(INK);
    expect(outbox.enqueueInkErase({ owner: { extractionId: "ext" }, eraseId: "er_1", strokeIds: ["s1"] })).toBe(2);
    expect((await outbox.flush()).kind).toBe("applied");
    expect(sent).toEqual([["ink", 1], ["erase", 2]]);
  });
});
