// Mobile v2 §4.2-§4.3: the frame's back chevron and edge swipe, the keyboard inset that keeps the
// primary action visible, and the service worker's build stamp (§5.2).
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ScreenFrame } from "./ScreenFrame";
import { BUILD_MARKER, stampServiceWorker } from "./swBuild";
import { keyboardInset } from "./viewport";
import workerSource from "../../public/sw.js?raw";

function swipe(target: Element, fromX: number, toX: number, dy = 0) {
  fireEvent.touchStart(target, { touches: [{ clientX: fromX, clientY: 300 }] });
  fireEvent.touchEnd(target, { changedTouches: [{ clientX: toX, clientY: 300 + dy }] });
}

describe("the frame", () => {
  it("a back chevron, named, only where there is somewhere to go back to", () => {
    const back = vi.fn();
    const { rerender } = render(<ScreenFrame screenKey="a" title="Question" onBack={back} backName="Back to Today"><p>body</p></ScreenFrame>);
    fireEvent.click(screen.getByRole("button", { name: "Back to Today" }));
    expect(back).toHaveBeenCalledTimes(1);
    rerender(<ScreenFrame screenKey="b" title="Today" onBack={null}><p>body</p></ScreenFrame>);
    expect(screen.queryByRole("button", { name: /Back/ })).toBeNull();
  });

  it("a swipe from the left edge across a third of the screen goes back; anything else does not", () => {
    const back = vi.fn();
    render(<ScreenFrame screenKey="a" title="Question" onBack={back}><p>body</p></ScreenFrame>);
    const main = screen.getByRole("main");
    const third = window.innerWidth / 3;
    swipe(main, 200, 200 + third + 10);
    swipe(main, 5, 5 + third / 2);
    swipe(main, 5, 5 + third + 10, third + 50);
    expect(back).not.toHaveBeenCalled();
    swipe(main, 5, 5 + third + 10);
    expect(back).toHaveBeenCalledTimes(1);
  });

  it("moves focus to the new screen and announces its title, not the first one's", () => {
    const { rerender } = render(<ScreenFrame screenKey="a" title="Today"><p>one</p></ScreenFrame>);
    const live = document.querySelector("[aria-live='polite']") as HTMLElement;
    expect(live.textContent).toBe("");
    rerender(<ScreenFrame screenKey="b" title="Question"><p>two</p></ScreenFrame>);
    expect(live.textContent).toBe("Question");
    expect(document.activeElement).toBe(screen.getByRole("main"));
  });
});

it("the keyboard inset is the gap under the visual viewport, never negative", () => {
  expect(keyboardInset({ height: 500, offsetTop: 0 }, 844)).toBe(344);
  expect(keyboardInset({ height: 500, offsetTop: 44 }, 844)).toBe(300);
  expect(keyboardInset({ height: 844, offsetTop: 0 }, 844)).toBe(0);
  expect(keyboardInset({ height: 900, offsetTop: 0 }, 844)).toBe(0);
});

describe("the service worker's build stamp", () => {
  it("the source names the placeholder exactly once, and the stamp replaces it", () => {
    expect(workerSource.split(BUILD_MARKER)).toHaveLength(2);
    const stamped = stampServiceWorker(workerSource, "67edddbffcb567d5");
    expect(stamped).toContain('const BUILD = "67edddbffcb567d5";');
    expect(stamped).not.toContain(BUILD_MARKER);
  });

  it("refuses what is not a hash, and a source without the placeholder", () => {
    expect(() => stampServiceWorker(workerSource, "../x")).toThrow();
    expect(() => stampServiceWorker("self.x = 1;", "67edddbffcb567d5")).toThrow();
  });
});
