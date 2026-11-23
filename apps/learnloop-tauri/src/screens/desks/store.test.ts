// The vault's desk store (fix round, review findings 1, 3, 5 and 11): a permanent refusal is rejected
// visibly and reconciled, never retried; a conflict rebases the independent queued intent instead of
// dropping it; undo offers follow the server's state; one store per vault outlives the shell.
import { describe, expect, it, vi } from "vitest";
import type { DeskApplyInput } from "../../api/dto";
import { FixtureDeskServer } from "../../fixtures/desks/workspace";
import { closeWindow, deskById, renameDesk, moveFocused, undoClose, openBeside } from "./model/workspace";
import { REAL_TIMERS, type Timers } from "./keys/router";
import { DeskStore, deskStoreFor, type DeskNotice } from "./store";

class ManualTimers implements Timers {
  queue: Array<{ fn: () => void; id: number }> = [];
  private next = 1;
  set(fn: () => void): unknown {
    const id = this.next++;
    this.queue.push({ fn, id });
    return id;
  }
  clear(handle: unknown): void {
    this.queue = this.queue.filter((entry) => entry.id !== handle);
  }
  now(): number {
    return 0;
  }
  fire(): void {
    const due = this.queue;
    this.queue = [];
    for (const entry of due) entry.fn();
  }
}

/** A transport over the fixture server, with a hook to interfere before a batch lands. */
function transportOver(server: FixtureDeskServer, before?: (input: DeskApplyInput) => void) {
  return {
    state: async () => server.state(),
    apply: async (input: DeskApplyInput) => {
      before?.(input);
      return server.apply(input);
    },
  };
}

async function settle(store: DeskStore, timers: ManualTimers) {
  for (let i = 0; i < 6; i += 1) {
    timers.fire();
    await store.flush();
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
}

describe("a permanent refusal (finding 1)", () => {
  it("is rejected once, said, and reconciled: the desk is back as saved and later writes go through", async () => {
    const server = new FixtureDeskServer();
    const timers = new ManualTimers();
    const sent: DeskApplyInput[] = [];
    const transport = {
      state: async () => server.state(),
      apply: async (input: DeskApplyInput) => {
        sent.push(input);
        // The server's params model refuses a compare reference with neither a query nor a comparison.
        if (input.ops.some((op) => op.op === "open_window" && op.content?.kind === "compare" && !op.content.query && !op.content.comparisonId)) {
          throw { code: "validation_error", message: "a compare reference names a comparison_id or a query" };
        }
        return server.apply(input);
      },
    };
    const store = new DeskStore("me", transport, timers);
    const notices: DeskNotice[] = [];
    store.onNotice((notice) => notices.push(notice));
    await store.load();
    store.commit(openBeside(store.ws, "fx_desk_softmax", { kind: "compare" }, () => "bad_compare"));
    store.commit(renameDesk(store.ws, "fx_desk_attention", "attention, renamed"));
    expect(store.ws.windows.bad_compare).toBeDefined();
    await settle(store, timers);
    expect(notices.map((notice) => notice.kind)).toContain("rejected");
    // Reconciled: the invalid window is gone, the independent rename was kept and saved.
    expect(store.ws.windows.bad_compare).toBeUndefined();
    expect(server.state().desks.find((desk) => desk.deskId === "fx_desk_attention")?.title).toBe("attention, renamed");
    expect(sent.filter((input) => input.ops.some((op) => op.op === "open_window" && op.windowId === "bad_compare"))).toHaveLength(1);
    expect(store.outbox.pending).toBe(0);
  });
});

describe("a conflict (finding 3)", () => {
  it("drops only the conflicting change; independent queued changes are rebased and saved, and the loss is reported", async () => {
    const server = new FixtureDeskServer();
    const timers = new ManualTimers();
    let interfered = false;
    const store = new DeskStore("me", transportOver(server, () => {
      if (interfered) return;
      interfered = true;
      // Another installation moves the paper first: our move on that desk is now stale.
      server.apply({ clientId: "other", seq: 1, ops: [{ op: "move_window", deskId: "fx_desk_softmax", windowId: "fx_w_paper", toSlot: 0, expectedVersion: 1 }] });
    }), timers);
    const notices: DeskNotice[] = [];
    store.onNotice((notice) => notices.push(notice));
    await store.load();
    store.commit(moveFocused(store.ws, "fx_desk_softmax", 1));
    store.commit(renameDesk(store.ws, "fx_desk_attention", "attention, kept"));
    await settle(store, timers);
    const desks = server.state().desks;
    expect(desks.find((desk) => desk.deskId === "fx_desk_attention")?.title).toBe("attention, kept");
    expect(desks[0].slots[0].windows[0].windowId).toBe("fx_w_paper");
    expect(deskById(store.ws, "fx_desk_softmax")?.slots[0]).toEqual(["fx_w_paper"]);
    expect(notices).toContainEqual({ kind: "conflict", dropped: 1, lost: 0 });
  });

  it("a change committed while the server's state is on its way is rebased too", async () => {
    const server = new FixtureDeskServer();
    const timers = new ManualTimers();
    let release: () => void = () => undefined;
    let first = true;
    const transport = {
      state: async () => {
        if (!first) await new Promise<void>((resolve) => { release = resolve; });
        first = false;
        return server.state();
      },
      apply: async (input: DeskApplyInput) => {
        if (input.seq === 1) server.apply({ clientId: "other", seq: 1, ops: [{ op: "rename_desk", deskId: "fx_desk_softmax", title: "elsewhere", expectedVersion: 1 }] });
        return server.apply(input);
      },
    };
    const store = new DeskStore("me", transport, timers);
    await store.load();
    store.commit(renameDesk(store.ws, "fx_desk_softmax", "mine"));
    timers.fire();
    const flushing = store.flush();
    await new Promise((resolve) => setTimeout(resolve, 0));
    store.commit(renameDesk(store.ws, "fx_desk_backprop", "backprop, later"));
    release();
    await flushing;
    await settle(store, timers);
    expect(server.state().desks.find((desk) => desk.deskId === "fx_desk_backprop")?.title).toBe("backprop, later");
    expect(server.state().desks.find((desk) => desk.deskId === "fx_desk_softmax")?.title).toBe("elsewhere");
  });
});

describe("undo after a rejected close (finding 11)", () => {
  it("the undo offer goes once the server says the window is open; reopening an open window is refused", async () => {
    const server = new FixtureDeskServer();
    const timers = new ManualTimers();
    let interfered = false;
    const store = new DeskStore("me", transportOver(server, () => {
      if (interfered) return;
      interfered = true;
      server.apply({ clientId: "other", seq: 1, ops: [{ op: "rename_desk", deskId: "fx_desk_softmax", title: "renamed elsewhere", expectedVersion: 1 }] });
    }), timers);
    await store.load();
    store.commit(closeWindow(store.ws, "fx_desk_softmax", "fx_w_paper"));
    expect(store.ws.closed.fx_desk_softmax?.map((entry) => entry.window.windowId)).toEqual(["fx_w_paper"]);
    await settle(store, timers);
    // The close was stale: the paper is open on the server, so nothing is offered to undo.
    expect(store.ws.windows.fx_w_paper).toBeDefined();
    expect(store.ws.closed.fx_desk_softmax ?? []).toEqual([]);
    expect(undoClose(store.ws, "fx_desk_softmax").ops).toEqual([]);
    const desk = deskById(store.ws, "fx_desk_softmax")!;
    expect(desk.slots.flat().filter((id) => id === "fx_w_paper")).toHaveLength(1);
  });
});

describe("one store per vault (finding 5)", () => {
  it("is the same store for the same vault and transport, and a new one for another vault", () => {
    const transport = transportOver(new FixtureDeskServer());
    const a = deskStoreFor("vault-a", transport, REAL_TIMERS, () => "c");
    expect(deskStoreFor("vault-a", transport, REAL_TIMERS, () => "c")).toBe(a);
    expect(deskStoreFor("vault-b", transport, REAL_TIMERS, () => "c")).not.toBe(a);
  });

  it("two loads share one read", async () => {
    const server = new FixtureDeskServer();
    const state = vi.fn(async () => server.state());
    const store = new DeskStore("me", { state, apply: async (input) => server.apply(input) }, new ManualTimers());
    await Promise.all([store.load(), store.load()]);
    expect(state).toHaveBeenCalledTimes(1);
  });
});

describe("coming back to the desks (finding 5)", () => {
  it("a second load reads the server's state again and keeps what is still queued", async () => {
    const server = new FixtureDeskServer();
    const timers = new ManualTimers();
    const store = new DeskStore("me", transportOver(server), timers);
    await store.load();
    store.commit(renameDesk(store.ws, "fx_desk_attention", "queued here"));
    server.apply({ clientId: "other", seq: 1, ops: [{ op: "rename_desk", deskId: "fx_desk_softmax", title: "changed elsewhere", expectedVersion: 1 }] });
    await store.load();
    expect(deskById(store.ws, "fx_desk_softmax")?.title).toBe("changed elsewhere");
    expect(deskById(store.ws, "fx_desk_attention")?.title).toBe("queued here");
    await settle(store, timers);
    expect(server.state().desks.find((desk) => desk.deskId === "fx_desk_attention")?.title).toBe("queued here");
  });
});

describe("pads in the store (RD4b)", () => {
  function padTransport(server: FixtureDeskServer, beforePad?: (input: Parameters<FixtureDeskServer["applyPad"]>[0]) => void) {
    return {
      state: async () => server.state(),
      apply: async (input: DeskApplyInput) => server.apply(input),
      applyPad: async (input: Parameters<FixtureDeskServer["applyPad"]>[0]) => {
        beforePad?.(input);
        return server.applyPad(input);
      },
      padGet: async ({ padId }: { padId: string }) => server.padGet(padId),
    };
  }

  it("a pad edit shows at once and is sent by pad.apply in the same numbering as desk batches", async () => {
    const server = new FixtureDeskServer();
    const timers = new ManualTimers();
    const store = new DeskStore("me", padTransport(server), timers);
    await store.load();
    await store.loadPad("fx_pad_running");
    store.commit(renameDesk(store.ws, "fx_desk_attention", "renamed"));
    expect(store.commitPad("fx_pad_running", [{ op: "edit_block", blockId: "fx_b_r1", expectedHead: "fx_b_r1_v1", versionId: "mine1", bodyMd: "my edit" }])).toBeNull();
    expect(store.pads.fx_pad_running.blocks[0].bodyMd).toBe("my edit");
    await settle(store, timers);
    expect(server.batches.map((batch) => batch.seq)).toEqual([1]);
    expect(server.padBatches.map((batch) => batch.seq)).toEqual([2]);
    expect(server.padGet("fx_pad_running").blocks[0]).toMatchObject({ bodyMd: "my edit", headVersionId: "mine1" });
  });

  it("an edit whose head moved elsewhere is rebased on the new head (the other version stays in history); an edit of a block removed elsewhere is dropped and reported", async () => {
    const server = new FixtureDeskServer();
    const timers = new ManualTimers();
    let interfered = false;
    const store = new DeskStore("me", padTransport(server, () => {
      if (interfered) return;
      interfered = true;
      server.applyPad({ clientId: "other", seq: 1, padId: "fx_pad_running", ops: [
        { op: "edit_block", blockId: "fx_b_r1", expectedHead: "fx_b_r1_v1", versionId: "theirs", bodyMd: "their edit" },
        { op: "remove_block", blockId: "fx_b_r7", expectedHead: "fx_b_r7_v1" },
      ] });
    }), timers);
    const notices: DeskNotice[] = [];
    store.onNotice((notice) => notices.push(notice));
    await store.load();
    await store.loadPad("fx_pad_running");
    store.commitPad("fx_pad_running", [{ op: "edit_block", blockId: "fx_b_r1", expectedHead: "fx_b_r1_v1", versionId: "mine1", bodyMd: "my edit" }]);
    store.commitPad("fx_pad_running", [{ op: "edit_block", blockId: "fx_b_r7", expectedHead: "fx_b_r7_v1", versionId: "mine7", bodyMd: "an edit of a removed block" }]);
    await settle(store, timers);
    const saved = server.padGet("fx_pad_running");
    expect(saved.blocks.find((block) => block.blockId === "fx_b_r1")).toMatchObject({ bodyMd: "my edit", headVersionId: "mine1" });
    expect(saved.blocks.some((block) => block.blockId === "fx_b_r7")).toBe(false);
    expect(store.pads.fx_pad_running.blocks.find((block) => block.blockId === "fx_b_r1")?.bodyMd).toBe("my edit");
    expect(notices).toEqual([{ kind: "conflict", dropped: 0, lost: 1 }]);
  });
});


describe("an ask waits for the desk writes it depends on (RD3 review)", () => {
  it("settled() sends what is queued at once and resolves saved only once the server has it", async () => {
    const server = new FixtureDeskServer();
    const timers = new ManualTimers();
    const store = new DeskStore("me", transportOver(server), timers);
    await store.load();
    store.commit(renameDesk(store.ws, "fx_desk_attention", "renamed"));
    expect(server.batches).toHaveLength(0);
    // No timer fires: the ask does not wait for the idle flush.
    const settled = await store.settled();
    expect(settled).toBe("saved");
    expect(server.batches).toHaveLength(1);
  });

  it("settled() with nothing queued is saved at once; a write that cannot be sent is unsaved", async () => {
    const server = new FixtureDeskServer();
    const timers = new ManualTimers();
    let offline = false;
    const store = new DeskStore("me", {
      state: async () => server.state(),
      apply: async (input: DeskApplyInput) => {
        if (offline) throw { code: "sidecar_unavailable", message: "LearnLoop is not running." };
        return server.apply(input);
      },
    }, timers);
    await store.load();
    expect(await store.settled()).toBe("saved");
    offline = true;
    store.commit(renameDesk(store.ws, "fx_desk_attention", "renamed"));
    expect(await store.settled()).toBe("unsaved");
  });
});
