// RW2a uses LiveMarkdownEditor for each workbench step (spec §5.1). The editor
// gains optional props only: a label, a focus request, key information (at the
// end of the step? empty?) and a compact layout. Without them it renders as it
// did. The editor binds no chord of its own, so the workbench's Ctrl+K,
// Ctrl+Shift+B, Ctrl+D and Ctrl+Enter never clash with it (UX §3.5).
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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

// RW2a round 4 F8: while Leave is under way the workbench shows its steps
// read-only. The box says so and accepts no change, so nothing typed is
// dropped unseen.
it("a read-only editor still opens its text but accepts no change", async () => {
  const onChange = vi.fn();
  render(<LiveMarkdownEditor value="one" onChange={onChange} ariaLabel="Step 1" focusable compact readOnly />);
  const rest = screen.getByRole("textbox", { name: "Step 1" });
  expect(rest.getAttribute("aria-readonly")).toBe("true");
  fireEvent.focus(rest);
  const area = (await screen.findByRole("textbox", { name: "Step 1" })) as HTMLTextAreaElement;
  expect(area.tagName).toBe("TEXTAREA");
  expect(area.readOnly).toBe(true);
  fireEvent.change(area, { target: { value: "one more" } });
  expect(onChange).not.toHaveBeenCalled();
});

// UX-19 (UX journey audit part 2, workbench-1 #8, #13, #28): the first click on "check my work", "help" or "+ a step"
// right after typing in a step did nothing; the key did. The press takes the focus at mousedown, and the step's text
// box then gave way to its rendered paragraph, which is taller, so everything under the step moved down before the
// release and the release missed the control (its click never fired). The box now stays until the press is released.
// jsdom has no layout: these tests check that nothing is swapped while the press is down, not the pointer's miss.
it("UX-19: a press elsewhere that takes the focus leaves the text box in place until it is released, then the click lands", async () => {
  const onClick = vi.fn();
  render(
    <>
      <Controlled initial="An eigenvector v satisfies Av = lambda v." ariaLabel="Step 1" focusable compact focusSignal={1} />
      <button type="button" onClick={onClick}>check my work</button>
    </>
  );
  await waitFor(() => expect(document.activeElement?.tagName).toBe("TEXTAREA"));
  const button = screen.getByRole("button", { name: "check my work" });
  fireEvent.mouseDown(button);
  act(() => button.focus());
  // Still the text box while the press is down: nothing under the step has moved.
  expect(screen.getByRole("textbox", { name: "Step 1" }).tagName).toBe("TEXTAREA");
  fireEvent.mouseUp(button);
  fireEvent.click(button);
  expect(onClick).toHaveBeenCalledTimes(1);
  // After the release, the step shows its rendered text, as before.
  await waitFor(() => expect(document.querySelector("textarea")).toBeNull());
  expect(screen.getByText("An eigenvector v satisfies Av = lambda v.")).toBeTruthy();
});

it("UX-19: leaving the box with no press down (Tab, a key) renders it at once, as before", async () => {
  render(
    <>
      <Controlled initial="one" ariaLabel="Step 1" focusable compact focusSignal={1} />
      <button type="button">next</button>
    </>
  );
  await waitFor(() => expect(document.activeElement?.tagName).toBe("TEXTAREA"));
  act(() => screen.getByRole("button", { name: "next" }).focus());
  expect(document.querySelector("textarea")).toBeNull();
});
