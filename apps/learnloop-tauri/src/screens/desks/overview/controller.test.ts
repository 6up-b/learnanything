// The zoom's one writer (spec §6.3): frames go straight onto the elements, the spring ends on the goal's
// exact frame, a cancel or a commit removes every style the zoom wrote, and a key or press settles.
import { describe, expect, it, vi } from "vitest";
import { IDENTITY, OVERVIEW } from "./engine";
import { ZoomController, cameraTransform, selectionShadow, type FrameClock, type ZoomPlan } from "./controller";
import { cloneForMiniature, MiniatureBook } from "./miniature";

class ManualClock implements FrameClock {
  queue: Array<{ handle: number; callback: (now: number) => void }> = [];
  now = 0;
  private next = 1;
  request(callback: (now: number) => void): number {
    const handle = this.next++;
    this.queue.push({ handle, callback });
    return handle;
  }
  cancel(handle: number): void {
    this.queue = this.queue.filter((entry) => entry.handle !== handle);
  }
  frame(): void {
    this.now += 1000 / 60;
    const due = this.queue;
    this.queue = [];
    for (const entry of due) entry.callback(this.now);
  }
}

function setup() {
  const world = document.createElement("div");
  const box = document.createElement("div");
  const inner = document.createElement("div");
  const card = document.createElement("div");
  box.append(inner, card);
  world.append(box);
  const clock = new ManualClock();
  const ended = vi.fn();
  const controller = new ZoomController(clock, ended);
  const a = { x: 34, y: 8, w: 643, h: 880 };
  const b = { x: 204, y: 8, w: 760, h: 656 };
  const B = { x: 24, y: 70, s: OVERVIEW.scale };
  const plan: ZoomPlan = { base: 0, A: IDENTITY, B, items: [{ key: "k", a, b, base: a, live: true, focus: true }] };
  controller.begin(plan, { world, slots: new Map([["k", { box, inner, card }]]), late: [], slivers: [] });
  return { world, box, inner, card, clock, ended, controller, B };
}

describe("the zoom's writer", () => {
  it("writes the first frame on begin without moving anything", () => {
    const { world, box } = setup();
    expect(world.style.transform).toBe(cameraTransform(IDENTITY));
    expect(box.style.transform).toBe("translate(0px, 0px) scale(1, 1)");
  });

  it("springs to the goal, writes the goal's exact frame, then hands the commit over", () => {
    const { world, box, card, clock, ended, controller, B } = setup();
    controller.go(1);
    for (let i = 0; i < 60 && ended.mock.calls.length === 0; i += 1) clock.frame();
    expect(ended).toHaveBeenCalledWith(1, 0);
    expect(world.style.transform).toBe(cameraTransform(B));
    const [tx, ty, sx, sy] = box.style.transform.match(/-?[\d.]+(e-?\d+)?/g)!.map(Number);
    expect(34 + tx).toBeCloseTo(204, 6);
    expect(8 + ty).toBeCloseTo(8, 6);
    expect(643 * sx).toBeCloseTo(760, 6);
    expect(880 * sy).toBeCloseTo(656, 6);
    expect(card.style.opacity).toBe("1");
    expect(box.style.boxShadow).toBe(selectionShadow(1));
    expect(controller.frameTimes.length).toBeGreaterThan(5);
  });

  it("clean removes every style it wrote and ends the zoom", () => {
    const { box, inner, card, clock, controller } = setup();
    controller.setTarget(0.5);
    clock.frame();
    controller.clean();
    expect(controller.active).toBe(false);
    expect([box.style.transform, box.style.boxShadow, inner.style.transform, inner.style.opacity, inner.style.visibility, card.style.opacity]).toEqual(["", "", "", "", "", ""]);
    expect(clock.queue).toEqual([]);
  });

  it("settles at once on a key or a press: past 40 % it completes, short of it it goes back", () => {
    const first = setup();
    first.controller.setProgress(0.45);
    first.controller.settle();
    expect(first.ended).toHaveBeenCalledWith(1, 0);
    const second = setup();
    second.controller.setProgress(0.2);
    second.controller.settle();
    expect(second.ended).toHaveBeenCalledWith(0, 0);
  });

  it("lifting the fingers releases by the rule", () => {
    const { clock, ended, controller } = setup();
    controller.setTarget(0.3);
    for (let i = 0; i < 20; i += 1) clock.frame();
    controller.release();
    for (let i = 0; i < 60 && ended.mock.calls.length === 0; i += 1) clock.frame();
    expect(ended).toHaveBeenCalledWith(0, 0);
  });
});

describe("miniatures", () => {
  it("a clone keeps no ids, window marks, frames or focusable controls, and is inert", () => {
    const pane = document.createElement("div");
    pane.setAttribute("data-desk-window", "w1");
    pane.innerHTML = '<p id="x">text</p><iframe title="player"></iframe><button>go</button><div contenteditable="true">edit</div>';
    const { node } = cloneForMiniature(pane);
    expect(node.getAttribute("data-desk-window")).toBeNull();
    expect(node.querySelector("[id]")).toBeNull();
    expect(node.querySelector("iframe")).toBeNull();
    expect(node.querySelector(".desk-mini-frame")?.textContent).toBe("▶");
    expect(node.querySelector("button")?.getAttribute("tabindex")).toBe("-1");
    expect(node.querySelector("[contenteditable]")).toBeNull();
    expect(node.hasAttribute("inert")).toBe(true);
    expect(node.textContent).toContain("text");
  });

  it("is rebuilt only after its window changed", () => {
    const book = new MiniatureBook();
    expect(book.needs("w1")).toBe(true);
    book.store("w1", document.createElement("div"));
    expect(book.needs("w1")).toBe(false);
    book.invalidate("w1");
    expect(book.needs("w1")).toBe(true);
  });
});
