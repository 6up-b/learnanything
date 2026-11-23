// The listener router (spec §3.6): N windows never mean N real listeners; input goes to the active
// window only; a press makes the window under it active first; paused windows hear nothing else; the
// shell's own handling runs first and can take an event from every window.
import { afterEach, describe, expect, it, vi } from "vitest";
import { DeskListenerRouter, WINDOW_ATTRIBUTE, windowOfTarget } from "./listeners";

const routers: DeskListenerRouter[] = [];
afterEach(() => {
  for (const router of routers.splice(0)) router.dispose();
  document.body.innerHTML = "";
});

function setup(active: { id: string | null }, paused = new Set<string>(), intercept?: (type: string, phase: string, event: Event) => boolean) {
  const onPointerWindow = vi.fn((id: string) => {
    active.id = id;
  });
  const router = new DeskListenerRouter({
    activeWindowId: () => active.id,
    isPaused: (id) => paused.has(id),
    onPointerWindow,
    intercept,
  });
  routers.push(router);
  return { router, onPointerWindow };
}

function windowElement(id: string): HTMLElement {
  const element = document.createElement("div");
  element.setAttribute(WINDOW_ATTRIBUTE, id);
  const inner = document.createElement("p");
  element.appendChild(inner);
  document.body.appendChild(element);
  return inner;
}

describe("one listener per type and phase", () => {
  it("installs one real listener for any number of windows", () => {
    const active = { id: "a" };
    const { router } = setup(active);
    const hubs = ["a", "b", "c", "d"].map((id) => router.hubFor(id));
    for (const hub of hubs) hub.listen("window", "keydown", () => undefined);
    for (const hub of hubs) hub.listen("window", "keydown", () => undefined, true);
    expect(router.realListenerCount).toBe(2);
    expect(router.subscriberCount()).toBe(8);
  });

  it("removes a window's subscription when its effect cleans up", () => {
    const { router } = setup({ id: "a" });
    const off = router.hubFor("a").listen("window", "keydown", () => undefined);
    expect(router.subscriberCount("a")).toBe(1);
    off();
    expect(router.subscriberCount("a")).toBe(0);
  });
});

describe("who hears what", () => {
  it("keys go to the active window only", () => {
    const active = { id: "a" };
    const { router } = setup(active);
    const heard: string[] = [];
    router.hubFor("a").listen("window", "keydown", () => heard.push("a"));
    router.hubFor("b").listen("window", "keydown", () => heard.push("b"));
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "x" }));
    active.id = "b";
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "x" }));
    expect(heard).toEqual(["a", "b"]);
  });

  it("a press inside a window makes it active before the press is handed on", () => {
    const active = { id: "a" };
    const { router, onPointerWindow } = setup(active);
    const heard: string[] = [];
    router.hubFor("a").listen("window", "mousedown", () => heard.push("a"), true);
    router.hubFor("b").listen("window", "mousedown", () => heard.push("b"), true);
    const target = windowElement("b");
    target.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));
    expect(onPointerWindow).toHaveBeenCalledWith("b", expect.any(MouseEvent));
    expect(heard).toEqual(["b"]);
    expect(windowOfTarget(target)).toBe("b");
  });

  it("other events reach every window that is not paused", () => {
    const paused = new Set(["b"]);
    const { router } = setup({ id: "a" }, paused);
    const heard: string[] = [];
    for (const id of ["a", "b", "c"]) router.hubFor(id).listen("window", "resize", () => heard.push(id));
    window.dispatchEvent(new Event("resize"));
    expect(heard).toEqual(["a", "c"]);
  });

  it("capture subscribers hear the capture phase, the others the bubble phase", () => {
    const { router } = setup({ id: "a" });
    const order: string[] = [];
    const hub = router.hubFor("a");
    hub.listen("window", "keydown", () => order.push("bubble"));
    hub.listen("window", "keydown", () => order.push("capture"), true);
    const target = windowElement("a");
    target.addEventListener("keydown", () => order.push("element"));
    target.dispatchEvent(new KeyboardEvent("keydown", { key: "x", bubbles: true }));
    expect(order).toEqual(["capture", "element", "bubble"]);
  });

  it("the shell's interception takes an event from every window", () => {
    const { router } = setup({ id: "a" }, new Set(), (type) => type === "keydown");
    const heard = vi.fn();
    router.hubFor("a").listen("window", "keydown", heard, true);
    router.ensure("window", "keydown");
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "x" }));
    expect(heard).not.toHaveBeenCalled();
  });

  it("a window that stops immediate propagation stops the windows after it", () => {
    const { router } = setup({ id: "a" });
    const later = vi.fn();
    router.hubFor("a").listen("window", "keydown", (event) => event.stopImmediatePropagation());
    router.hubFor("a").listen("window", "keydown", later);
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "x" }));
    expect(later).not.toHaveBeenCalled();
  });
});
