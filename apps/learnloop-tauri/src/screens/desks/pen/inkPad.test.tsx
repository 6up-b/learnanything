// Ink pads and ink lines (spec §10.10, "Freewrite pads"; mockup `#pen=pad`): lined paper with its bar, each line's
// strokes and its transcription shown as LearnLoop's reading that may be wrong, a new line started with the pen, a
// finished line read through the central poller (cancellable), today's refusal said plainly with the ink kept, the
// learner's correction as a new version, and kept_your_correction. Every call is a fake.
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { InkTranscribeJobDto, PadOpDto } from "../../../api/dto";
import { Poller } from "../../../api/poller";
import { FixtureDeskServer } from "../../../fixtures/desks/workspace";
import { FIXTURE_INK_PAD, fixtureInkOwners, fixtureInkPad, fixturePads } from "../../../fixtures/desks/pads";
import type { PadStackHandle } from "../pads/host";
import { PadsHostContext, PendingFigures, type PadsHost } from "../pads/host";
import { PadStackWindow } from "../pads/PadStackWindow";
import type { Timers } from "../keys/router";
import { DIRECT_HUB, WindowScope, type WindowState } from "../lifecycle";
import { DeskStore } from "../store";
import { PenHostContext, type PenApi, type PenHost } from "./host";
import { InkCache } from "./inkCache";

const timers: Timers = { set: () => 0, clear: () => undefined, now: () => 0 };

const refused: InkTranscribeJobDto = { version: 1, jobId: null, status: "failed", done: true, result: null,
  error: { code: "cannot_read_images", message: "The model routed to read handwriting cannot read images.", retryable: false, details: null } };

function reading(over: Partial<NonNullable<InkTranscribeJobDto["result"]>>): InkTranscribeJobDto {
  return { version: 1, jobId: null, status: "done", done: true, error: null, result: {
    transcriptionId: "it_9", ownerKind: "block", ownerId: "fx_b_h3", contentHash: "h9", latexMd: "$a + b$", confidenceLabel: "may_be_wrong",
    model: "m", createdAt: "t", applied: true, reason: null, headVersionId: "v9", ...over } };
}

let minted = 0;
function mount({ state = "active" as WindowState, on = true, transcribe = async (): Promise<InkTranscribeJobDto> => refused } = {}) {
  const server = new FixtureDeskServer(undefined, [...fixturePads(), fixtureInkPad()]);
  const calls: string[] = [];
  const padGet = vi.fn(async ({ padId }: { padId: string }) => server.padGet(padId));
  const store = new DeskStore("me", {
    state: async () => server.state(),
    apply: async (input) => server.apply(input),
    applyPad: async (input) => {
      calls.push(`pad:${input.ops.map((op) => op.op).join(",")}`);
      return server.applyPad(input);
    },
    applyInk: async (input) => {
      calls.push(`ink:${input.inkId}`);
      return server.applyInk(input);
    },
    padGet,
  }, timers);
  const api: PenApi = {
    readerCapture: vi.fn(), readerDeleteIntentAnnotation: vi.fn(), readerEditAnnotation: vi.fn(),
    readerSourceAnnotations: vi.fn(async () => ({ annotations: [] })),
    inkList: vi.fn(async () => ({ version: 1, padId: FIXTURE_INK_PAD, sourceId: null, owners: fixtureInkOwners() })),
    inkTranscribe: vi.fn(transcribe),
    inkTranscribeJob: vi.fn(async ({ jobId }: { jobId: string }) => ({ version: 1, jobId, status: "running" as const, done: false, result: null, error: null })),
    inkTranscribeCancel: vi.fn(async ({ jobId }: { jobId: string }) => ({ version: 1, jobId, status: "cancelled" as const, done: false, result: null, error: null })),
  };
  const poller = new Poller({ setInterval: () => 1, clearInterval: () => undefined });
  const pen: PenHost = {
    on, simulate: false, setOn: vi.fn(),
    saveInk: (ink) => store.commitInk(ink),
    eraseInk: (erase) => store.commitInkErase(erase),
    settled: () => store.settled(),
    mintId: (prefix) => `${prefix}_${++minted}`,
    api, poller, askCompanion: vi.fn(),
    ink: undefined as unknown as InkCache,
  };
  pen.ink = new InkCache({ api, poller, settled: pen.settled, refreshPad: (padId) => store.refreshPad(padId) });
  let handle: PadStackHandle | null = null;
  const host: PadsHost = {
    store, deskId: "fx_desk_softmax", mintId: pen.mintId, today: () => "2026-11-23",
    api: { padProposals: async ({ padId }: { padId: string }) => ({ version: 1, padId, proposals: [] }) } as unknown as PadsHost["api"],
    practiceSessionId: null, openPassage: vi.fn(), openSearch: vi.fn(), askAbout: vi.fn(), toast: vi.fn(), setView: vi.fn(),
    sourcePieces: () => [], register: (_id, h) => { handle = h; }, carry: vi.fn(), figures: new PendingFigures(), addToStack: vi.fn(),
  };
  const ui = (now: WindowState) => (
    <WindowScope lifecycle={{ windowId: "w1", state: now }} hub={DIRECT_HUB}>
      <PadsHostContext.Provider value={host}>
        <PenHostContext.Provider value={pen}>
          <PadStackWindow windowId="w1" stack={[{ kind: "pad", padId: FIXTURE_INK_PAD }]} view={{}} />
        </PenHostContext.Provider>
      </PadsHostContext.Provider>
    </WindowScope>
  );
  const view = render(ui(state));
  return { server, store, api, pen, poller, calls, padGet, handle: () => handle, rerender: (now: WindowState) => view.rerender(ui(now)) };
}

async function settle() {
  for (let i = 0; i < 6; i += 1) {
    await act(async () => {
      await Promise.resolve();
      await new Promise((resolve) => setTimeout(resolve, 0));
    });
  }
}

function pointer(type: string, x: number, y: number, over: Record<string, unknown> = {}) {
  const { button = 0, buttons = 1, ...rest } = over as { button?: number; buttons?: number };
  const event = new MouseEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y, button, buttons });
  Object.assign(event, { pointerId: 3, pointerType: "pen", pressure: 0.5, tiltX: 0, tiltY: 0, ...rest });
  return event;
}

function stroke(target: Element, points: Array<[number, number]>, over: Record<string, unknown> = {}) {
  act(() => {
    target.dispatchEvent(pointer("pointerdown", ...points[0], over));
    for (const [x, y] of points.slice(1)) target.dispatchEvent(pointer("pointermove", x, y, over));
    target.dispatchEvent(pointer("pointerup", ...points[points.length - 1], over));
  });
}

const squiggle: Array<[number, number]> = [[10, 20], [16, 28], [22, 18], [28, 30], [34, 22]];
const line = (blockId: string) => document.querySelector(`[data-ink-block="${blockId}"]`) as HTMLElement;
const surfaceOf = (blockId: string) => line(blockId).querySelector("[data-ink-surface]") as HTMLElement;
const sentOps = (server: FixtureDeskServer): PadOpDto[] => server.padBatches.flatMap((batch) => batch.ops as PadOpDto[]);

afterEach(cleanup);

describe("an ink pad", () => {
  it("is lined paper with its bar; each line shows its strokes and its reading, labelled as what it is", async () => {
    mount();
    await settle();
    expect(document.querySelector(".paper.handpad")).not.toBeNull();
    const bar = document.querySelector("[data-ink-bar]") as HTMLElement;
    expect(bar.textContent).toContain("✎ by hand");
    expect(within(bar).getByText("hide transcription")).toBeTruthy();
    expect(line("fx_b_h1").querySelectorAll("path[data-ink-stroke]")).toHaveLength(4);
    const first = line("fx_b_h1").querySelector(".ocrl2") as HTMLElement;
    expect(first.textContent).toContain("read as");
    expect(first.textContent).toContain("may be wrong");
    const second = line("fx_b_h2").querySelector(".ocrl2") as HTMLElement;
    expect(second.textContent).toContain("you corrected the transcription");
    // A line not read yet offers its reading; nothing claims to have read it.
    expect(within(line("fx_b_h3")).getByText("read it")).toBeTruthy();
    expect(line("fx_b_h3").textContent).not.toContain("read as");
  });

  it("hides and shows the transcriptions, and turns the lines into a dot grid", async () => {
    mount();
    await settle();
    fireEvent.click(screen.getByText("hide transcription"));
    expect(document.querySelectorAll(".ocrl2")).toHaveLength(0);
    fireEvent.click(screen.getByText("show transcription"));
    expect(document.querySelectorAll(".ocrl2").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByText("dotted"));
    expect(document.querySelector(".paper.handpad.dotted")).not.toBeNull();
  });

  it("a pen stroke on the last row starts a new ink line: its block, then its ink, in that order", async () => {
    const { server, store, calls } = mount();
    await settle();
    const jot = document.querySelector(".pb.jot [data-ink-surface]") as HTMLElement;
    stroke(jot, squiggle);
    await act(async () => {
      await store.settled();
    });
    const insert = sentOps(server).find((op) => op.op === "insert_block") as Extract<PadOpDto, { op: "insert_block" }>;
    expect(insert).toMatchObject({ kind: "ink", provenance: "ink_transcription" });
    expect(calls.findIndex((c) => c.startsWith("pad:insert_block"))).toBeLessThan(calls.findIndex((c) => c.startsWith("ink:")));
    expect(line(insert.blockId).querySelectorAll("path[data-ink-stroke]")).toHaveLength(1);
  });

  it("writing on another line reads the finished one; today's refusal is said plainly, the ink is kept, the learner types the words", async () => {
    const { api, server, store } = mount();
    await settle();
    stroke(surfaceOf("fx_b_h3"), squiggle);
    stroke(surfaceOf("fx_b_h1"), squiggle);
    await settle();
    expect(api.inkTranscribe).toHaveBeenCalledTimes(1);
    const inkId = vi.mocked(api.inkTranscribe).mock.calls[0][0].inkId;
    expect(inkId).toMatch(/^ink_/);
    expect(within(line("fx_b_h3")).getByText(/handwriting can't be read yet · your ink is kept/)).toBeTruthy();
    expect(line("fx_b_h3").querySelectorAll("path[data-ink-stroke]")).toHaveLength(4);
    fireEvent.click(within(line("fx_b_h3")).getByText("type what you wrote"));
    const field = within(line("fx_b_h3")).getByLabelText("what this line says");
    fireEvent.change(field, { target: { value: "$a + b = c$" } });
    fireEvent.keyDown(field, { key: "Enter" });
    await act(async () => {
      await store.settled();
    });
    expect(sentOps(server).find((op) => op.op === "edit_block")).toMatchObject({ blockId: "fx_b_h3", bodyMd: "$a + b = c$" });
    expect(store.pads[FIXTURE_INK_PAD].blocks.find((b) => b.blockId === "fx_b_h3")?.provenance).toBe("learner_correction");
  });

  it("a reading under way is polled through the central poller and can be cancelled", async () => {
    const { api, poller } = mount({ transcribe: async () => ({ version: 1, jobId: "job_1", status: "running", done: false, result: null, error: null }) });
    await settle();
    fireEvent.click(within(line("fx_b_h3")).getByText("read it"));
    await settle();
    expect(poller.size).toBe(1);
    fireEvent.click(within(line("fx_b_h3")).getByText("cancel"));
    expect(api.inkTranscribeCancel).toHaveBeenCalledWith({ jobId: "job_1" });
    expect(poller.size).toBe(0);
  });

  it("a reading written into the block is read back so the block's head is the server's", async () => {
    const { padGet } = mount({ transcribe: async () => reading({}) });
    await settle();
    const before = padGet.mock.calls.length;
    fireEvent.click(within(line("fx_b_h3")).getByText("read it"));
    await settle();
    expect(padGet.mock.calls.length).toBe(before + 1);
  });

  it("when the learner's words stand, the new reading is offered and using it is the learner's edit", async () => {
    const { server, store } = mount({ transcribe: async () => reading({ ownerId: "fx_b_h2", applied: false, reason: "kept_your_correction", latexMd: "$q$" }) });
    await settle();
    stroke(surfaceOf("fx_b_h2"), squiggle);
    fireEvent.click(within(line("fx_b_h2")).getByText("read it"));
    await settle();
    const offer = line("fx_b_h2").querySelector("[data-ink-kept-yours]") as HTMLElement;
    expect(offer.textContent).toContain("your words stand");
    expect(offer.textContent).toContain("may be wrong");
    fireEvent.click(within(offer).getByText("use it"));
    await act(async () => {
      await store.settled();
    });
    expect(sentOps(server).find((op) => op.op === "edit_block")).toMatchObject({ blockId: "fx_b_h2", bodyMd: "$q$" });
  });

  it("the barrel erases the strokes it passes over (erase_ink)", async () => {
    const { server, store } = mount();
    await settle();
    const first = fixtureInkOwners()[0].strokes[0].points;
    stroke(surfaceOf("fx_b_h1"), [[first[3][0], first[3][1]], [first[4][0], first[4][1]], [first[5][0], first[5][1]]], { button: 2 });
    await act(async () => {
      await store.settled();
    });
    expect(sentOps(server).find((op) => op.op === "erase_ink")).toMatchObject({ blockId: "fx_b_h1", strokeIds: ["fx_b_h1_s0"] });
    expect(line("fx_b_h1").querySelectorAll("path[data-ink-stroke]")).toHaveLength(3);
  });

  it("touch never draws, a paused window draws nothing, and a new pad in pen mode is a handwritten one", async () => {
    const touched = mount();
    await settle();
    stroke(surfaceOf("fx_b_h1"), squiggle, { pointerType: "touch" });
    expect(line("fx_b_h1").querySelectorAll("path[data-ink-stroke]")).toHaveLength(4);
    act(() => touched.handle()!.newPad());
    await act(async () => {
      await touched.store.settled();
    });
    expect(sentOps(touched.server).find((op) => op.op === "create_pad")).toMatchObject({ kind: "ink", title: "Scratchpad · ✎ by hand" });
    cleanup();
    const paused = mount();
    await settle();
    paused.rerender("offscreen");
    stroke(surfaceOf("fx_b_h1"), squiggle);
    await act(async () => {
      await paused.store.settled();
    });
    expect(paused.calls.filter((call) => call.startsWith("ink:"))).toHaveLength(0);
    expect(line("fx_b_h1").querySelectorAll("path[data-ink-stroke]")).toHaveLength(4);
  });
});
