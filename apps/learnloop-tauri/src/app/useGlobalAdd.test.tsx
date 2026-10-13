// Add from anywhere (docs/specs/ux_learnloop_v1.md §6.2, §5.4): Ctrl+O chooses a
// file, Ctrl+V with no text field focused adds the link on the clipboard.
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { looksLikeSource, useGlobalAdd } from "./useGlobalAdd";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function Harness(props: Parameters<typeof useGlobalAdd>[0]) {
  useGlobalAdd(props);
  return <input aria-label="notes" />;
}

function paste(text: string, target: EventTarget = document.body) {
  const event = new Event("paste", { bubbles: true, cancelable: true }) as Event & { clipboardData: unknown };
  event.clipboardData = { getData: () => text };
  target.dispatchEvent(event);
  return event;
}

describe("useGlobalAdd", () => {
  it("opens the file picker on Ctrl+O", () => {
    const onPickFiles = vi.fn();
    render(<Harness enabled onPickFiles={onPickFiles} onLink={vi.fn()} />);
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "o", ctrlKey: true }));
    expect(onPickFiles).toHaveBeenCalledTimes(1);
  });

  it("adds a pasted link when no text field has focus", () => {
    const onLink = vi.fn();
    render(<Harness enabled onPickFiles={vi.fn()} onLink={onLink} />);
    paste("https://www.youtube.com/watch?v=abc123");
    expect(onLink).toHaveBeenCalledWith("https://www.youtube.com/watch?v=abc123");
  });

  it("leaves pastes into text fields and plain prose alone", () => {
    const onLink = vi.fn();
    const { getByLabelText } = render(<Harness enabled onPickFiles={vi.fn()} onLink={onLink} />);
    paste("https://example.org/article", getByLabelText("notes"));
    paste("some words I copied");
    expect(onLink).not.toHaveBeenCalled();
  });

  it("does nothing while disabled", () => {
    const onPickFiles = vi.fn();
    const onLink = vi.fn();
    render(<Harness enabled={false} onPickFiles={onPickFiles} onLink={onLink} />);
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "o", ctrlKey: true }));
    paste("https://example.org/article");
    expect(onPickFiles).not.toHaveBeenCalled();
    expect(onLink).not.toHaveBeenCalled();
  });
});

describe("looksLikeSource", () => {
  it.each([
    ["https://arxiv.org/abs/1706.03762", true],
    ["1706.03762", true],
    ["arXiv:1706.03762v2", true],
    ["/home/me/books/probability.pdf", true],
    ["http://example.org", true],
    ["a sentence about probability", false],
    ["", false]
  ])("%s → %s", (text, expected) => {
    expect(looksLikeSource(text)).toBe(expected);
  });
});
