// The bridge's checks (spec §11.3): only the frame's own messages, from its own origin, of exactly the four
// shapes; geometry moved onto the page and kept inside the frame.
import { describe, expect, it } from "vitest";
import { BRIDGE_TEXT_MAX, frameOrigin, fromFrame, parseBridgeMessage, toPage } from "./bridge";

describe("parseBridgeMessage", () => {
  it("accepts the four kinds in their exact shapes", () => {
    expect(parseBridgeMessage({ ll: "companion", text: "softmax", rect: { x: 1, y: 2, width: 3, height: 4 }, shift: false }))
      .toEqual({ ll: "companion", text: "softmax", rect: { x: 1, y: 2, width: 3, height: 4 }, shift: false });
    expect(parseBridgeMessage({ ll: "menu", text: "", rect: null, x: 10, y: 20 })).toEqual({ ll: "menu", text: "", rect: null, x: 10, y: 20 });
    expect(parseBridgeMessage({ ll: "click" })).toEqual({ ll: "click" });
    expect(parseBridgeMessage({ ll: "escape" })).toEqual({ ll: "escape" });
  });

  it.each([
    ["an unknown kind", { ll: "run", code: "evil()" }],
    ["a string", '{"ll":"click"}'],
    ["an array", [{ ll: "click" }]],
    ["null", null],
    ["an extra key", { ll: "click", then: "run" }],
    ["text that is not a string", { ll: "companion", text: 5, rect: null, shift: false }],
    ["oversized text", { ll: "companion", text: "x".repeat(BRIDGE_TEXT_MAX + 1), rect: null, shift: false }],
    ["a missing shift", { ll: "companion", text: "x", rect: null }],
    ["shift that is not a boolean", { ll: "companion", text: "x", rect: null, shift: "yes" }],
    ["a rect missing a side", { ll: "menu", text: "x", rect: { x: 1, y: 1, width: 1 }, x: 0, y: 0 }],
    ["a rect with an extra key", { ll: "menu", text: "x", rect: { x: 1, y: 1, width: 1, height: 1, html: "<b>" }, x: 0, y: 0 }],
    ["a negative width", { ll: "companion", text: "x", rect: { x: 1, y: 1, width: -1, height: 1 }, shift: false }],
    ["an infinite point", { ll: "menu", text: "x", rect: null, x: Infinity, y: 0 }],
    ["a point that is a string", { ll: "menu", text: "x", rect: null, x: "0", y: 0 }],
    ["a class instance", Object.assign(Object.create({ ll: "click" }), {})],
  ])("refuses %s", (_name, data) => {
    expect(parseBridgeMessage(data)).toBeNull();
  });

  it("keeps text as the plain string it was sent, never markup it renders", () => {
    const message = parseBridgeMessage({ ll: "companion", text: "<img src=x onerror=alert(1)>", rect: null, shift: false });
    expect(message).toEqual({ ll: "companion", text: "<img src=x onerror=alert(1)>", rect: null, shift: false });
  });
});

describe("fromFrame", () => {
  const frameWindow = {};
  const origin = "http://127.0.0.1:40123";

  it("accepts the frame's own window from its own origin", () => {
    expect(fromFrame({ source: frameWindow as Window, origin }, { window: frameWindow, origin })).toBe(true);
  });
  it("refuses another window, even from the same origin", () => {
    expect(fromFrame({ source: {} as Window, origin }, { window: frameWindow, origin })).toBe(false);
  });
  it("refuses the frame's window from another origin (it navigated away)", () => {
    expect(fromFrame({ source: frameWindow as Window, origin: "http://127.0.0.1:40124" }, { window: frameWindow, origin })).toBe(false);
    expect(fromFrame({ source: frameWindow as Window, origin: "null" }, { window: frameWindow, origin })).toBe(false);
  });
  it("refuses everything before the frame has loaded", () => {
    expect(fromFrame({ source: null, origin }, { window: null, origin })).toBe(false);
  });
});

describe("frameOrigin", () => {
  it("is the loopback proxy's origin", () => {
    expect(frameOrigin("http://127.0.0.1:40123/s/abc/?view-as=present")).toBe("http://127.0.0.1:40123");
  });
  it.each(["https://example.com/s/x/", "http://localhost:40123/s/x/", "javascript:alert(1)", "not a url"])("is null for %s", (url) => {
    expect(frameOrigin(url)).toBeNull();
  });
});

describe("toPage", () => {
  const box = { left: 859, top: 288, width: 516, height: 518 };
  it("moves a selection's box and a point onto the page", () => {
    expect(toPage({ ll: "companion", text: "t", rect: { x: 10, y: 20, width: 30, height: 40 }, shift: false }, box))
      .toEqual({ ll: "companion", text: "t", rect: { x: 869, y: 308, width: 30, height: 40 }, shift: false });
    expect(toPage({ ll: "menu", text: "", rect: null, x: 5, y: 6 }, box)).toEqual({ ll: "menu", text: "", rect: null, x: 864, y: 294 });
  });
  it("keeps geometry a notebook made up inside the frame's box", () => {
    expect(toPage({ ll: "menu", text: "", rect: { x: -500, y: 9000, width: 99999, height: 5 }, x: -50, y: 99999 }, box))
      .toEqual({ ll: "menu", text: "", rect: { x: 859, y: 806, width: 516, height: 0 }, x: 859, y: 806 });
  });
});
