// A pad stack window (spec §10): it reads its pads and their proposals only while live, writes through the
// store (pad.apply), edits in place with the editor's keys, shows provenance (a quote is kept, never read as
// the learner's words), lifts a block out, submits only the learner's words, and labels proposals.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { PadOpDto, PadProposalDto, PadViewDto } from "../../../api/dto";
import { FixtureDeskServer } from "../../../fixtures/desks/workspace";
import { isTypingTarget, type Timers } from "../keys/router";
import { DIRECT_HUB, WindowScope, type WindowState } from "../lifecycle";
import { DeskStore } from "../store";
import { objectAt } from "../menu/model";
import { PadsHostContext, PendingFigures, type PadsApi, type PadsHost, type PadStackHandle } from "./host";
import { PadStackWindow } from "./PadStackWindow";

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

const PROPOSAL: PadProposalDto = {
  proposalId: "p1", blockId: "fx_b_r1", blockVersionId: "fx_b_r1_v1", foundBy: "passage_link",
  target: { content: { kind: "source", extraction_id: "fx_ext_softmax" }, target: { span_id: "fx_ext_softmax_s2_1" } },
  reasonMd: "a passage takes this further", quote: "a project-authored line", judgmentRef: null,
  createdAt: "2026-11-23T09:00:00Z", current: true, labels: [], shown: true,
} as PadProposalDto;

function fakeApi(): PadsApi & { calls: Array<[string, unknown]> } {
  const calls: Array<[string, unknown]> = [];
  const log = <T,>(name: string, value: T) => async (input?: unknown) => {
    calls.push([name, input]);
    return value;
  };
  return {
    calls,
    padProposals: async (input) => {
      calls.push(["padProposals", input]);
      return { version: 1, padId: input.padId, proposals: input.padId === "fx_pad_running" ? [PROPOSAL] : [] } as never;
    },
    proposalLabel: log("proposalLabel", {}),
    padSubmitBlock: async (input) => {
      calls.push(["padSubmitBlock", input]);
      return { version: 1, submissionId: input.submissionId, blockId: input.blockId, versionId: input.versionId, as: input.as, practiceItemId: input.target.practiceItemId, attemptId: "att1", teachBackId: null, created: true } as never;
    },
    carriedCarry: log("carriedCarry", { carried: {} as never, created: true }),
    requestTeachBack: log("requestTeachBack", { practiceItemId: "tb_item" }),
    passageUnionRange: log("passageUnionRange", { sections: [] } as never),
    authorPracticeItem: log("authorPracticeItem", { practiceItemId: "new_item" }),
    workbenchOpenProblems: log("workbenchOpenProblems", { problems: [{ sessionId: "wb1", practiceItemId: "item_problem" }] }),
    submitTeachBackTurn: log("submitTeachBackTurn", { done: true } as never),
    getSession: log("getSession", { checkpoint: null } as never),
    passageContent: async (input) => {
      calls.push(["passageContent", input]);
      const span = (input as { fromSpanId: string }).fromSpanId;
      return { version: 1, extractionId: input.extractionId, sourceId: "src_other", title: "Another book", withheld: false,
        spans: [{ spanId: span, text: "The whole passage, as the source has it, unclipped and with $x^2$ intact.", page: 12, t0: null, t1: null, sectionId: "sec3", sectionLabel: "3 Temperature", withheld: false }] } as never;
    },
  };
}

let minted = 0;
const TOASTS = new WeakMap<object, string[]>();
const toastsOf = (host: PadsHost) => TOASTS.get(host) ?? [];

/** The mounted stack's handle (the desks reach a stack through it). */
let stackHandleOf: () => PadStackHandle | null = () => null;

function mount(options: { state?: WindowState; server?: FixtureDeskServer; padIds?: string[]; practiceSessionId?: string | null; view?: Record<string, unknown> } = {}) {
  const server = options.server ?? new FixtureDeskServer();
  const timers = new ManualTimers();
  const store = new DeskStore("me", {
    state: async () => server.state(),
    apply: async (input) => server.apply(input),
    applyPad: async (input) => server.applyPad(input),
    padGet: async ({ padId }) => server.padGet(padId),
  }, timers);
  const api = fakeApi();
  const views: Array<Record<string, unknown>> = [];
  const toasts: string[] = [];
  const host: PadsHost = {
    store,
    deskId: "fx_desk_softmax",
    mintId: (prefix) => `${prefix}_${++minted}`,
    today: () => "2026-11-23",
    api,
    practiceSessionId: options.practiceSessionId === undefined ? "session1" : options.practiceSessionId,
    openPassage: vi.fn(),
    openSearch: vi.fn(),
    askAbout: vi.fn(),
    toast: (text) => toasts.push(text),
    setView: (_windowId, view) => views.push(view),
    sourcePieces: () => [],
    register: (_windowId, handle) => {
      stackHandle = handle;
    },
    carry: vi.fn(),
    figures: new PendingFigures(),
    addToStack: vi.fn(),
  };
  const padIds = options.padIds ?? ["fx_pad_running", "fx_pad_deriving"];
  let stackHandle: PadStackHandle | null = null;
  stackHandleOf = () => stackHandle;
  // The desks' one right-click listener, as the shell has it: a pad line's menu opens in its window.
  const onContextMenuCapture = (event: React.MouseEvent) => {
    const object = objectAt(event.target as Element, () => "pad_stack", () => null, { x: event.clientX, y: event.clientY });
    if (object?.kind !== "pad_line" || !object.padId || !stackHandle) return;
    event.preventDefault();
    stackHandle.openMenu(object.padId, object.blockId ?? null, object.at, object.selection);
  };
  const ui = (state: WindowState) => (
    <WindowScope lifecycle={{ windowId: "w1", state }} hub={DIRECT_HUB}>
      <PadsHostContext.Provider value={host}>
        <div data-desk-window="w1" onContextMenuCapture={onContextMenuCapture}>
          <PadStackWindow windowId="w1" stack={padIds.map((padId) => ({ kind: "pad" as const, padId }))} view={options.view ?? {}} />
        </div>
      </PadsHostContext.Provider>
    </WindowScope>
  );
  const view = render(ui(options.state ?? "active"));
  const flush = async () => {
    for (let i = 0; i < 4; i += 1) {
      timers.fire();
      await act(async () => {
        await store.flush();
      });
    }
  };
  TOASTS.set(host, toasts);
  return { server, store, api, host, views, toasts, view, flush, rerender: (state: WindowState) => view.rerender(ui(state)) };
}

const sentOps = (server: FixtureDeskServer): PadOpDto[] => server.padBatches.flatMap((batch) => batch.ops as PadOpDto[]);
const block = (id: string) => document.querySelector<HTMLElement>(`[data-block="${id}"]`) as HTMLElement;
const textarea = () => document.querySelector<HTMLTextAreaElement>("[data-pad-editor] textarea");

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("a pad stack window", () => {
  it("shows the running pad's day headings and every block's provenance; a quote is kept, never read as your words", async () => {
    mount();
    await screen.findByText("SUN 22 NOV");
    expect(screen.getByText("MON 23 NOV · TODAY")).toBeTruthy();
    expect(block("fx_b_r1").getAttribute("data-emits")).toBe("yes");
    for (const id of ["fx_b_r2", "fx_b_r3", "fx_b_r5"]) {
      expect(block(id).getAttribute("data-emits"), id).toBe("no");
      expect(block(id).getAttribute("title"), id).toBe("quoted, not read as your words");
    }
    expect(within(block("fx_b_r4")).getByText("submitted · teach-back")).toBeTruthy();
    expect(within(block("fx_b_r2")).getByRole("button", { name: /Softmax, a short book p\.1 ↩/ })).toBeTruthy();
  });

  it("a pad holding only quotes says in its ⓘ that nothing on it is read as your words", async () => {
    const server = new FixtureDeskServer();
    const running = server.pads.fx_pad_running as PadViewDto;
    server.pads.fx_pad_quotes = { ...running, pad: { ...running.pad, padId: "fx_pad_quotes", kind: "named", title: "quotes" }, blocks: running.blocks.filter((each) => each.kind === "source_quote"), anchors: [] };
    mount({ server, padIds: ["fx_pad_quotes"] });
    await screen.findAllByText(/quotes/);
    for (const element of document.querySelectorAll("[data-block]")) expect(element.getAttribute("data-emits")).toBe("no");
    fireEvent.click(screen.getByRole("button", { name: "where your words go" }));
    expect(screen.getByText(/nothing on these pads is read as your words yet/)).toBeTruthy();
  });

  it("the jot line opens a new block in the editor; ↵ keeps it and opens the next; esc takes back a line never written", async () => {
    const { server, store, flush } = mount();
    await screen.findByText("jot · it lands here by default");
    fireEvent.click(screen.getByText("jot · it lands here by default"));
    await waitFor(() => expect(textarea()).toBeTruthy());
    // The editor's frame and box are a typing scope: the desks' bare keys do not act while it is open.
    expect(document.querySelector("[data-pad-editor]")?.hasAttribute("data-desk-typing")).toBe(true);
    expect(isTypingTarget(textarea())).toBe(true);
    fireEvent.change(textarea() as HTMLTextAreaElement, { target: { value: "my own line" } });
    fireEvent.keyDown(textarea() as HTMLTextAreaElement, { key: "Enter" });
    await waitFor(() => expect(textarea()?.value).toBe(""));
    const blocks = store.pads.fx_pad_running.blocks;
    expect(blocks.some((each) => each.bodyMd === "my own line" && each.provenance === "learner" && each.day === "2026-11-23")).toBe(true);
    const fresh = blocks[blocks.length - 1];
    expect(fresh.bodyMd).toBe("");
    fireEvent.keyDown(textarea() as HTMLTextAreaElement, { key: "Escape" });
    await waitFor(() => expect(textarea()).toBeNull());
    expect(store.pads.fx_pad_running.blocks.some((each) => each.blockId === fresh.blockId)).toBe(false);
    await flush();
    const ops = sentOps(server).map((op) => op.op);
    expect(ops).toEqual(["insert_block", "edit_block", "insert_block", "remove_block"]);
  });

  it("esc restores a block as it was, and blur keeps the edit", async () => {
    const { store } = mount();
    await waitFor(() => expect(block("fx_b_r1")).toBeTruthy());
    fireEvent.click(block("fx_b_r1"));
    await waitFor(() => expect(textarea()).toBeTruthy());
    fireEvent.change(textarea() as HTMLTextAreaElement, { target: { value: "changed my mind" } });
    fireEvent.keyDown(textarea() as HTMLTextAreaElement, { key: "Escape" });
    await waitFor(() => expect(textarea()).toBeNull());
    expect(store.pads.fx_pad_running.blocks[0].bodyMd).toMatch(/^softmax keeps the winner/);
    fireEvent.click(block("fx_b_r1"));
    await waitFor(() => expect(textarea()).toBeTruthy());
    fireEvent.change(textarea() as HTMLTextAreaElement, { target: { value: "kept on blur" } });
    fireEvent.blur(textarea() as HTMLTextAreaElement);
    await waitFor(() => expect(store.pads.fx_pad_running.blocks[0].bodyMd).toBe("kept on blur"));
  });

  it("a quote does not open in the editor: it is the source's words", async () => {
    mount();
    await waitFor(() => expect(block("fx_b_r1")).toBeTruthy());
    fireEvent.click(block("fx_b_r2"));
    expect(textarea()).toBeNull();
  });

  it("a paused window reads no pad and no proposal and writes nothing; back on screen it reads them", async () => {
    const { server, api, rerender, store } = mount({ state: "hidden" });
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 20));
    });
    expect(api.calls.filter(([name]) => name === "padProposals")).toEqual([]);
    expect(store.pads.fx_pad_running).toBeUndefined();
    rerender("active");
    await waitFor(() => expect(block("fx_b_r1")).toBeTruthy());
    await waitFor(() => expect(api.calls.filter(([name]) => name === "padProposals").length).toBe(2));
    // Paused again with the pads read: a click on the jot line writes nothing.
    rerender("hidden");
    const before = store.pads.fx_pad_running.blocks.length;
    fireEvent.click(screen.getByText("jot · it lands here by default"));
    expect(store.pads.fx_pad_running.blocks.length).toBe(before);
    expect(textarea()).toBeNull();
    expect(server.padBatches).toEqual([]);
  });

  it("lift out makes the block its own pad in this stack, leaving a stub", async () => {
    const { store, views, server, flush, host } = mount();
    await waitFor(() => expect(block("fx_b_r1")).toBeTruthy());
    fireEvent.click(within(block("fx_b_r1")).getByRole("button", { name: "lift out" }));
    const stub = store.pads.fx_pad_running.blocks.find((each) => each.blockId === "fx_b_r1");
    expect(stub?.kind).toBe("lifted");
    const newPadId = String(stub?.payload.lifted_to_pad_id);
    // Membership by its own op (add_to_stack), never a whole-view write.
    expect(host.addToStack).toHaveBeenCalledWith("w1", newPadId);
    expect(views).toEqual([]);
    expect(store.pads[newPadId]?.blocks[0].bodyMd).toMatch(/^softmax keeps the winner/);
    await flush();
    expect(sentOps(server).map((op) => op.op)).toEqual(["lift_out"]);
  });

  it("the pad menu offers submit only on the learner's words, and its marimo row is live (notebooks are in)", async () => {
    mount();
    await waitFor(() => expect(block("fx_b_r1")).toBeTruthy());
    fireEvent.contextMenu(block("fx_b_r2"));
    let menu = screen.getByRole("menu", { name: "the pad menu" });
    expect(within(menu).queryByText("Submit this block as…")).toBeNull();
    expect((within(menu).getByText("marimo cell").closest("button") as HTMLButtonElement).disabled).toBe(false);
    expect(within(menu).queryByText(/arrives with notebooks/)).toBeNull();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("menu")).toBeNull();
    fireEvent.contextMenu(block("fx_b_r1"));
    menu = screen.getByRole("menu", { name: "the pad menu" });
    expect(within(menu).getByText("Submit this block as…")).toBeTruthy();
  });

  it("the marimo row inserts an empty cell of the learner's below the line", async () => {
    const { store, flush } = mount();
    await waitFor(() => expect(block("fx_b_r1")).toBeTruthy());
    fireEvent.contextMenu(block("fx_b_r1"));
    fireEvent.click(screen.getByText("marimo cell"));
    await flush();
    const blocks = store.pads.fx_pad_running.blocks;
    const at = blocks.findIndex((each) => each.blockId === "fx_b_r1");
    expect(blocks[at + 1]).toMatchObject({ kind: "cell", provenance: "learner", bodyMd: "" });
  });

  it("a notebook frame's right-click opens the pad menu labelled for its owner, the frame's text only ever quoted", async () => {
    const { store, flush } = mount();
    await waitFor(() => expect(block("fx_b_r1")).toBeTruthy());
    act(() => {
      stackHandleOf()?.openFrameMenu({ owner: "pad:fx_pad_running", padId: "fx_pad_running", lessonId: null, text: "<b>bold</b> words", x: 40, y: 40,
        label: "your pad", insertLabel: "insert at the end of this pad" });
    });
    const menu = screen.getByRole("menu", { name: "the pad menu" });
    expect(within(menu).getByText("your pad · “<b>bold</b> words”")).toBeTruthy();
    expect(menu.querySelector("b")).toBeNull();
    expect(within(menu).getByText("insert at the end of this pad")).toBeTruthy();
    // A pad's inserts from the frame land at the pad's end.
    fireEvent.click(within(menu).getByText("marimo cell"));
    await flush();
    expect(store.pads.fx_pad_running.blocks.slice(-1)[0]).toMatchObject({ kind: "cell", provenance: "learner" });
    act(() => {
      stackHandleOf()?.openFrameMenu({ owner: "lesson:les9", padId: null, lessonId: "les9", text: "a cell's words", x: 40, y: 40,
        label: "the lesson", insertLabel: "add under this lesson (the notebook stays as the teacher made it)" });
    });
    const lesson = screen.getByRole("menu", { name: "the pad menu" });
    expect(within(lesson).getByText("the lesson · “a cell's words”")).toBeTruthy();
    expect(within(lesson).getByText("add under this lesson (the notebook stays as the teacher made it)")).toBeTruthy();
    // Nothing of a pad's own (muting its suggestions) on a lesson's menu.
    expect(within(lesson).queryByText(/suggestions on this pad/)).toBeNull();
  });

  it("a piece of a source inserted from the menu lands below the line, linked to its passage in the same write", async () => {
    const { store, host, server, flush } = mount();
    host.sourcePieces = () => [{ label: "the passage in view · a book", extractionId: "fx_ext_x", spanId: "fx_ext_x_s4", text: "a passage's words", sourceTitle: "a book" }];
    await waitFor(() => expect(block("fx_b_r1")).toBeTruthy());
    fireEvent.contextMenu(block("fx_b_r1"));
    fireEvent.click(screen.getByText("the passage in view · a book"));
    // The piece's words are the passage's own, read whole (not the page's rendered text).
    await waitFor(() => expect(store.pads.fx_pad_running.blocks[1]?.kind).toBe("source_piece"));
    const blocks = store.pads.fx_pad_running.blocks;
    expect(blocks[1]).toMatchObject({ kind: "source_piece", provenance: "source", bodyMd: "The whole passage, as the source has it, unclipped and with $x^2$ intact." });
    expect(store.pads.fx_pad_running.anchors.some((anchor) => anchor.blockId === blocks[1].blockId && anchor.spanId === "fx_ext_x_s4")).toBe(true);
    await flush();
    expect(server.padBatches.map((batch) => (batch.ops as PadOpDto[]).map((op) => op.op))).toEqual([["insert_block", "link_anchor"]]);
  });

  it("a problem pad's block is submitted as my answer to its item, in the session, and shows its tag", async () => {
    const server = new FixtureDeskServer();
    const deriving = server.pads.fx_pad_deriving as PadViewDto;
    server.pads.fx_pad_problem = {
      ...deriving,
      pad: { ...deriving.pad, padId: "fx_pad_problem", kind: "problem", title: "a problem", workbenchSessionId: "wb1" },
      blocks: [{ ...deriving.blocks[0], blockId: "fx_b_p1", headVersionId: "fx_b_p1_v1", kind: "text", provenance: "learner", bodyMd: "my working", submissions: [] }],
      anchors: [],
    };
    const { api } = mount({ server, padIds: ["fx_pad_problem"] });
    await waitFor(() => expect(block("fx_b_p1")).toBeTruthy());
    fireEvent.contextMenu(block("fx_b_p1"));
    fireEvent.click(screen.getByText("Submit this block as…"));
    fireEvent.click(await screen.findByRole("button", { name: "my answer to this problem" }));
    await waitFor(() => expect(within(block("fx_b_p1")).getByText(/^submitted · attempt/)).toBeTruthy());
    const submitted = api.calls.find(([name]) => name === "padSubmitBlock")?.[1];
    expect(submitted).toMatchObject({ blockId: "fx_b_p1", versionId: "fx_b_p1_v1", as: "attempt", target: { sessionId: "session1", practiceItemId: "item_problem" } });
  });

  it("with no practice session a submission is not sent, and says why", async () => {
    const server = new FixtureDeskServer();
    const deriving = server.pads.fx_pad_deriving as PadViewDto;
    server.pads.fx_pad_problem = {
      ...deriving,
      pad: { ...deriving.pad, padId: "fx_pad_problem", kind: "problem", title: "a problem", workbenchSessionId: "wb1" },
      blocks: [{ ...deriving.blocks[0], blockId: "fx_b_p1", headVersionId: "fx_b_p1_v1", kind: "text", provenance: "learner", bodyMd: "my working", submissions: [] }],
      anchors: [],
    };
    const { api } = mount({ server, padIds: ["fx_pad_problem"], practiceSessionId: null });
    await waitFor(() => expect(block("fx_b_p1")).toBeTruthy());
    fireEvent.contextMenu(block("fx_b_p1"));
    fireEvent.click(screen.getByText("Submit this block as…"));
    fireEvent.click(await screen.findByRole("button", { name: "my answer to this problem" }));
    expect(await screen.findByText(/start a practice session first/)).toBeTruthy();
    expect(api.calls.some(([name]) => name === "padSubmitBlock")).toBe(false);
  });

  it("a proposal's card opens after 160 ms; not this is a label; a card closed with nothing chosen is labelled ignored", async () => {
    const { api } = mount();
    await waitFor(() => expect(block("fx_b_r1")).toBeTruthy());
    const mark = await waitFor(() => {
      const found = within(block("fx_b_r1")).getByRole("button", { name: "proposal mark" });
      return found;
    });
    vi.useFakeTimers();
    fireEvent.mouseEnter(mark);
    act(() => {
      vi.advanceTimersByTime(150);
    });
    expect(document.querySelector("[data-pad-card]")).toBeNull();
    act(() => {
      vi.advanceTimersByTime(20);
    });
    expect(document.querySelector('[data-pad-card="proposal"]')).toBeTruthy();
    fireEvent.mouseLeave(mark);
    act(() => {
      vi.advanceTimersByTime(230);
    });
    expect(document.querySelector("[data-pad-card]")).toBeNull();
    expect(api.calls.filter(([name]) => name === "proposalLabel").map(([, input]) => (input as { label: string }).label)).toEqual(["ignored"]);
    fireEvent.click(mark);
    fireEvent.click(screen.getByRole("button", { name: "not this" }));
    expect(api.calls.filter(([name]) => name === "proposalLabel").map(([, input]) => (input as { label: string }).label)).toEqual(["ignored", "not_this"]);
    expect(within(block("fx_b_r1")).queryByRole("button", { name: "proposal mark" })).toBeNull();
  });
});

describe("the fix round (RD4 review)", () => {
  it("a click inside the editor (moving the caret) keeps the draft; blur writes it", async () => {
    const { store, server, flush } = mount();
    await waitFor(() => expect(block("fx_b_r1")).toBeTruthy());
    fireEvent.click(block("fx_b_r1"));
    await waitFor(() => expect(textarea()).toBeTruthy());
    fireEvent.change(textarea() as HTMLTextAreaElement, { target: { value: "my new words" } });
    // The learner clicks inside the box to move the caret: the click bubbles to the block.
    fireEvent.mouseDown(textarea() as HTMLTextAreaElement);
    fireEvent.click(textarea() as HTMLTextAreaElement);
    expect(textarea()?.value).toBe("my new words");
    fireEvent.blur(textarea() as HTMLTextAreaElement);
    await waitFor(() => expect(textarea()).toBeNull());
    expect(store.pads.fx_pad_running.blocks[0].bodyMd).toBe("my new words");
    await flush();
    const edits = sentOps(server).filter((op) => op.op === "edit_block");
    expect(edits.map((op) => (op as { bodyMd?: string }).bodyMd)).toEqual(["my new words"]);
  });

  function anchoredRunning() {
    const server = new FixtureDeskServer();
    const running = server.pads.fx_pad_running as PadViewDto;
    running.anchors = [...running.anchors, { eventId: "fx_an_r1", blockId: "fx_b_r1", extractionId: "fx_ext_softmax", spanId: "fx_ext_softmax_s1_1", anchor: {}, annotationId: null, createdAt: "2026-11-22T09:00:00Z" }];
    return server;
  }
  async function openTeachBack(api: PadsApi) {
    api.passageUnionRange = (async () => ({ sections: [{ learningObjects: [{ learningObjectId: "lo1" }] }] })) as never;
    await waitFor(() => expect(block("fx_b_r1")).toBeTruthy());
    fireEvent.contextMenu(block("fx_b_r1"));
    fireEvent.click(screen.getByText("Submit this block as…"));
    return screen.findByRole("button", { name: /a teach-back of the idea/ });
  }

  it("a submission retried after a lost reply resends the same frozen request: one submission id, one teach-back target", async () => {
    const { api } = mount({ server: anchoredRunning() });
    const sent: unknown[] = [];
    let first = true;
    api.padSubmitBlock = async (input) => {
      sent.push(input);
      if (first) {
        first = false;
        throw { code: "sidecar_unavailable", message: "the reply was lost" };
      }
      return { version: 1, submissionId: input.submissionId, blockId: input.blockId, versionId: input.versionId, as: input.as, practiceItemId: input.target.practiceItemId, attemptId: null, teachBackId: "tb1", duplicate: true, entry: null } as never;
    };
    const row = await openTeachBack(api);
    fireEvent.click(row);
    expect(await screen.findByText(/the reply was lost/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /a teach-back of the idea/ }));
    await waitFor(() => expect(sent).toHaveLength(2));
    const [a, b] = sent as Array<{ submissionId: string; versionId: string; target: { practiceItemId: string } }>;
    expect(b.submissionId).toBe(a.submissionId);
    expect(b.versionId).toBe(a.versionId);
    expect(b.target).toEqual(a.target);
    expect(api.calls.filter(([name]) => name === "requestTeachBack")).toHaveLength(1);
  });

  it("a teach-back that asks a follow-up shows the question and continues the conversation", async () => {
    const { api } = mount({ server: anchoredRunning() });
    api.padSubmitBlock = (async (input: { submissionId: string; blockId: string; versionId: string; as: string; target: { practiceItemId: string } }) => ({
      version: 1, submissionId: input.submissionId, blockId: input.blockId, versionId: input.versionId, as: input.as, practiceItemId: input.target.practiceItemId,
      attemptId: null, teachBackId: "tb1", duplicate: false,
      entry: { done: false, questionMd: "why do the weights stay positive?", questionNumber: 1, remaining: 1, asked: 1, budget: 2 },
    })) as never;
    const turns: unknown[] = [];
    api.submitTeachBackTurn = (async (input: unknown) => {
      turns.push(input);
      return { done: true };
    }) as never;
    fireEvent.click(await openTeachBack(api));
    expect(await screen.findByText("why do the weights stay positive?")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("your answer"), { target: { value: "the exponential is positive" } });
    fireEvent.click(screen.getByRole("button", { name: "answer" }));
    await waitFor(() => expect(turns).toHaveLength(1));
    expect(turns[0]).toMatchObject({ sessionId: "session1", practiceItemId: "tb_item", answerMd: "the exponential is positive" });
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "submit this block" })).toBeNull());
  });

  it("a duplicate reply resumes the conversation the submission reserved (its stored state's open question)", async () => {
    const { api } = mount({ server: anchoredRunning() });
    api.padSubmitBlock = (async (input: { submissionId: string; blockId: string; versionId: string; as: string; target: { practiceItemId: string } }) => ({
      version: 1, submissionId: input.submissionId, blockId: input.blockId, versionId: input.versionId, as: input.as, practiceItemId: input.target.practiceItemId,
      attemptId: null, teachBackId: "tb1", duplicate: true, entry: null,
      teachBack: { status: "ongoing", conversationId: "conv1", state: { practice_item_id: "tb_item", turns: [{ role: "learner", content_md: "mine" }, { role: "ai", content_md: "what if all scores are equal?" }] } },
    })) as never;
    fireEvent.click(await openTeachBack(api));
    expect(await screen.findByText("what if all scores are equal?")).toBeTruthy();
    expect(api.calls.some(([name]) => name === "getSession")).toBe(false);
  });

  it("a duplicate reply from an older sidecar (no conversation in it) resumes from the session's checkpoint", async () => {
    const { api } = mount({ server: anchoredRunning() });
    api.padSubmitBlock = (async (input: { submissionId: string; blockId: string; versionId: string; as: string; target: { practiceItemId: string } }) => ({
      version: 1, submissionId: input.submissionId, blockId: input.blockId, versionId: input.versionId, as: input.as, practiceItemId: input.target.practiceItemId,
      attemptId: null, teachBackId: "tb1", duplicate: true, entry: null,
    })) as never;
    api.getSession = (async () => ({ checkpoint: { currentPracticeItemId: "tb_item", hintsUsed: 0, submissionId: null,
      currentAnswer: JSON.stringify({ mode: "teach_back", state: { practice_item_id: "tb_item", turns: [{ role: "learner", content_md: "mine" }, { role: "ai", content_md: "and for a negative score?" }] } }) } })) as never;
    fireEvent.click(await openTeachBack(api));
    expect(await screen.findByText("and for a negative score?")).toBeTruthy();
  });

  it("a figure Show me asked for, finished while the pad is paused, writes nothing until the pad is back, then lands", async () => {
    const { host, store, rerender } = mount({ server: anchoredRunning() });
    let finish: (figure: { figureId: string; line: string }) => void = () => undefined;
    host.showMe = (() => new Promise((resolve) => { finish = resolve; })) as never;
    await waitFor(() => expect(block("fx_b_r1")).toBeTruthy());
    fireEvent.contextMenu(block("fx_b_r1"));
    fireEvent.click(screen.getByText("Show me"));
    const before = store.pads.fx_pad_running.blocks.length;
    rerender("hidden");
    await act(async () => {
      finish({ figureId: "fig9", line: "softmax at two temperatures" });
      await Promise.resolve();
    });
    expect(store.pads.fx_pad_running.blocks.length).toBe(before);
    rerender("active");
    await waitFor(() => expect(store.pads.fx_pad_running.blocks.some((each) => each.kind === "figure" && each.payload.figure_id === "fig9")).toBe(true));
  });

  it("in split view a gutter mark still opens its card", async () => {
    mount({ view: { split: { pads: ["fx_pad_running", "fx_pad_deriving"], ratios: [1, 1] } } });
    await waitFor(() => expect(block("fx_b_r2")).toBeTruthy());
    expect(document.querySelector(".desk-pads .split")).not.toBeNull();
    const mark = within(block("fx_b_r2")).getByRole("button", { name: "source mark" });
    vi.useFakeTimers();
    fireEvent.mouseEnter(mark);
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(document.querySelector('[data-pad-card="source"]')).not.toBeNull();
    fireEvent.mouseLeave(mark);
    act(() => {
      vi.advanceTimersByTime(300);
    });
    fireEvent.click(mark);
    expect(document.querySelector('[data-pad-card="source"]')).not.toBeNull();
  });

  it("a piece of another source is the passage's own words (fetched whole), with its title and page apart; a whole source is not a piece", async () => {
    const { host, store } = mount();
    let insert: ((row: never) => void) | undefined;
    host.openSearch = ((_query: string, callback?: (row: never) => void) => { insert = callback; }) as never;
    await waitFor(() => expect(block("fx_b_r1")).toBeTruthy());
    fireEvent.contextMenu(block("fx_b_r1"));
    fireEvent.click(screen.getByText("a piece of another source…"));
    expect(insert).toBeDefined();
    // A source row (no passage) inserts nothing and says why.
    await act(async () => {
      insert!({ kind: "result", key: "s", group: "sources", text: "Another book", where: "source", byMeaning: false, ref: { kind: "source", sourceId: "src_other", extractionId: "ext_other" }, target: null, raw: {} } as never);
    });
    expect(store.pads.fx_pad_running.blocks.some((each) => each.kind === "source_piece")).toBe(false);
    expect(toastsOf(host).some((text) => /choose a passage/.test(text))).toBe(true);
    // A passage row inserts the passage's canonical words, never the row's clipped label.
    await act(async () => {
      insert!({ kind: "result", key: "p", group: "passages", text: "Another book p.12 · The whole passage, as the…", where: "passage", byMeaning: false, ref: { kind: "source", sourceId: "src_other", extractionId: "ext_other" }, target: { spanId: "ext_other_s9" }, raw: {} } as never);
      await Promise.resolve();
    });
    const piece = await waitFor(() => {
      const found = store.pads.fx_pad_running.blocks.find((each) => each.kind === "source_piece");
      expect(found).toBeTruthy();
      return found!;
    });
    expect(piece.bodyMd).toBe("The whole passage, as the source has it, unclipped and with $x^2$ intact.");
    expect(piece.payload).toMatchObject({ source_title: "Another book", page: 12, extraction_id: "ext_other", span_id: "ext_other_s9", source_id: "src_other", section_label: "3 Temperature" });
  });

  it("a held-out passage is not copied into a pad, and says so", async () => {
    const { host, store, api } = mount();
    api.passageContent = (async (input: { extractionId: string; fromSpanId: string }) => ({ version: 1, extractionId: input.extractionId, sourceId: "src_other", title: "An exam", withheld: true,
      spans: [{ spanId: input.fromSpanId, text: null, page: 1, t0: null, t1: null, sectionId: null, sectionLabel: null, withheld: true }] })) as never;
    let insert: ((row: never) => void) | undefined;
    host.openSearch = ((_query: string, callback?: (row: never) => void) => { insert = callback; }) as never;
    await waitFor(() => expect(block("fx_b_r1")).toBeTruthy());
    fireEvent.contextMenu(block("fx_b_r1"));
    fireEvent.click(screen.getByText("a piece of another source…"));
    await act(async () => {
      insert!({ kind: "result", key: "p", group: "passages", text: "An exam · question 1", where: "passage", byMeaning: false, ref: { kind: "source", sourceId: "src_other", extractionId: "ext_exam" }, target: { spanId: "ext_exam_s1" }, raw: {} } as never);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(store.pads.fx_pad_running.blocks.some((each) => each.kind === "source_piece")).toBe(false);
    expect(toastsOf(host).some((text) => /held out/.test(text))).toBe(true);
  });
});
