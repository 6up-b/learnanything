// RW2a uses LiveMarkdownEditor for each workbench step (spec §5.1). The editor
// gains optional props only: a label, a focus request, key information (at the
// end of the step? empty?) and a compact layout. Without them it renders as it
// did. The editor binds no chord of its own, so the workbench's Ctrl+K,
// Ctrl+Shift+B, Ctrl+D and Ctrl+Enter never clash with it (UX §3.5).
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { useState } from "react";
import { LiveMarkdownEditor } from "./LiveMarkdownEditor";

vi.mock("./MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
afterEach(cleanup);

function Controlled(props: Partial<Parameters<typeof LiveMarkdownEditor>[0]> & { initial?: string }) {
  const [value, setValue] = useState(props.initial ?? "");
  return <LiveMarkdownEditor {...props} value={value} onChange={setValue} />;
}

it("without the new props it renders exactly as before: no role, no tab stop", () => {
  const { container } = render(<LiveMarkdownEditor value={"one\n\ntwo"} onChange={vi.fn()} />);
  const wrapper = container.firstElementChild as HTMLElement;
  expect(wrapper.className).toBe("ll-scroll");
  expect(wrapper.getAttribute("role")).toBeNull();
  expect(wrapper.getAttribute("tabindex")).toBeNull();
  expect(container.querySelector("textarea")).toBeNull();
});

it("a labelled, focusable editor is a text box at rest and starts editing on focus", async () => {
  render(<Controlled initial="one" ariaLabel="Step 1" focusable compact />);
  const box = screen.getByRole("textbox", { name: "Step 1" });
  fireEvent.focus(box);
  const area = await screen.findByRole("textbox", { name: "Step 1" });
  expect(area.tagName).toBe("TEXTAREA");
});

it("a focus request opens the last block with the caret at the end", async () => {
  const { rerender } = render(<LiveMarkdownEditor value={"one\n\ntwo"} onChange={vi.fn()} ariaLabel="Step 1" focusSignal={0} />);
  expect(document.querySelector("textarea")).toBeNull();
  rerender(<LiveMarkdownEditor value={"one\n\ntwo"} onChange={vi.fn()} ariaLabel="Step 1" focusSignal={1} />);
  await waitFor(() => expect(document.activeElement?.tagName).toBe("TEXTAREA"));
  const area = document.activeElement as HTMLTextAreaElement;
  expect(area.value).toBe("two");
  expect(area.selectionStart).toBe(3);
});

it("reports whether a key was pressed at the step's very end, and whether the step is empty", async () => {
  const onKeyDown = vi.fn();
  render(<Controlled initial={"one\n\ntwo"} ariaLabel="Step 1" focusSignal={1} onKeyDown={onKeyDown} />);
  await waitFor(() => expect(document.activeElement?.tagName).toBe("TEXTAREA"));
  const area = document.activeElement as HTMLTextAreaElement;
  fireEvent.keyDown(area, { key: "Enter" });
  expect(onKeyDown.mock.calls[0][1]).toEqual({ atEnd: true, empty: false });
  area.setSelectionRange(1, 1);
  fireEvent.keyDown(area, { key: "Enter" });
  expect(onKeyDown.mock.calls[1][1]).toEqual({ atEnd: false, empty: false });
});
