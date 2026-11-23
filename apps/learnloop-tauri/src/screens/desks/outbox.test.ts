// The desk outbox (spec §3.4, §3.5): one sequence per client continued from the server's head,
// batches sent in order and dropped only on their receipt, a conflict or a refused number handing the
// state back to the server, and an unreachable sidecar keeping the batch for the next flush.
import { describe, expect, it, vi } from "vitest";
import type { DeskApplyDto, DeskApplyInput, DeskOpDto } from "../../api/dto";
import { DeskOutbox, MemoryOutboxStore, clientIdFor } from "./outbox";

const op = (title: string): DeskOpDto => ({ op: "rename_desk", deskId: "d1", title, expectedVersion: 1 });

function reply(seq: number, results: DeskApplyDto["results"] = [{ status: "ok" }]): DeskApplyDto {
  return { version: 1, appliedSeq: seq, results, versions: [{ deskId: "d1", version: seq + 1 }] };
}

describe("the sequence", () => {
  it("continues the server's head for this client and drops what it already applied", () => {
    const store = new MemoryOutboxStore();
    store.put({ seq: 3, ops: [op("a")] });
    store.put({ seq: 4, ops: [op("b")] });
    const outbox = new DeskOutbox("me", { apply: vi.fn() }, store);
    outbox.syncSeq({ serverSeq: [{ clientId: "other", seq: 99 }, { clientId: "me", seq: 3 }] });
    expect(store.load().map((batch) => batch.seq)).toEqual([4]);
    expect(outbox.enqueue([op("c")])).toBe(5);
    expect(outbox.enqueue([])).toBeNull();
  });

  it("starts at 1 for a client the server has never seen", () => {
    const outbox = new DeskOutbox("new", { apply: vi.fn() });
    outbox.syncSeq({ serverSeq: [] });
    expect(outbox.enqueue([op("a")])).toBe(1);
    expect(outbox.durable).toBe(false);
  });
});

describe("flushing", () => {
  it("sends batches oldest first and drops each on its receipt", async () => {
    const sent: DeskApplyInput[] = [];
    const outbox = new DeskOutbox("me", { apply: async (input) => { sent.push(input); return reply(input.seq); } });
    outbox.syncSeq({ serverSeq: [] });
    outbox.enqueue([op("a")]);
    outbox.enqueue([op("b")]);
    const outcome = await outbox.flush();
    expect(sent.map((input) => [input.clientId, input.seq, input.ops[0]])).toEqual([["me", 1, op("a")], ["me", 2, op("b")]]);
    expect(outcome.kind).toBe("applied");
    expect(outbox.pending).toBe(0);
  });

  it("a conflict drops the batches queued after it, continues the numbering, and asks for the server's state", async () => {
    const sent: number[] = [];
    const outbox = new DeskOutbox("me", {
      apply: async (input) => {
        sent.push(input.seq);
        return reply(input.seq, input.seq === 1 ? [{ status: "conflict", current: { deskId: "d1", version: 9 } }] : [{ status: "ok" }]);
      },
    });
    outbox.syncSeq({ serverSeq: [] });
    outbox.enqueue([op("a")]);
    outbox.enqueue([op("b")]);
    expect((await outbox.flush()).kind).toBe("conflict");
    expect(sent).toEqual([1]);
    expect(outbox.pending).toBe(0);
    expect(outbox.enqueue([op("c")])).toBe(2);
  });

  it("a refused batch number resynchronises", async () => {
    const outbox = new DeskOutbox("me", { apply: async () => { throw { code: "seq_gap", message: "expected 3" }; } });
    outbox.syncSeq({ serverSeq: [] });
    outbox.enqueue([op("a")]);
    expect((await outbox.flush()).kind).toBe("resync");
    expect(outbox.pending).toBe(0);
  });

  it("an unreachable sidecar keeps the batch for the next flush", async () => {
    let up = false;
    const apply = vi.fn(async (input: DeskApplyInput) => {
      if (!up) throw { code: "sidecar_unavailable", message: "down" };
      return reply(input.seq);
    });
    const outbox = new DeskOutbox("me", { apply });
    outbox.syncSeq({ serverSeq: [] });
    outbox.enqueue([op("a")]);
    expect((await outbox.flush()).kind).toBe("offline");
    expect(outbox.pending).toBe(1);
    up = true;
    expect((await outbox.flush()).kind).toBe("applied");
    expect(apply.mock.calls.map(([input]) => input.seq)).toEqual([1, 1]);
  });

  it("runs one flush at a time", async () => {
    let release: () => void = () => undefined;
    const gate = new Promise<void>((resolve) => { release = resolve; });
    const order: number[] = [];
    const outbox = new DeskOutbox("me", { apply: async (input) => { order.push(input.seq); await gate; return reply(input.seq); } });
    outbox.syncSeq({ serverSeq: [] });
    outbox.enqueue([op("a")]);
    const first = outbox.flush();
    outbox.enqueue([op("b")]);
    const second = outbox.flush();
    release();
    await Promise.all([first, second]);
    expect(order).toEqual([1, 2]);
  });
});

describe("the client id", () => {
  it("is kept per vault on this machine", () => {
    const values = new Map<string, string>();
    const storage = { getItem: (key: string) => values.get(key) ?? null, setItem: (key: string, value: string) => void values.set(key, value) };
    const first = clientIdFor("vault-a", storage, () => "c1");
    expect(clientIdFor("vault-a", storage, () => "c2")).toBe(first);
    expect(clientIdFor("vault-b", storage, () => "c3")).toBe("c3");
    expect(clientIdFor("vault-c", null, () => "c4")).toBe("c4");
  });
});
