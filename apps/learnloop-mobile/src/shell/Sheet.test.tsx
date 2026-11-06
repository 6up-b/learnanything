// Mobile v2 §4.3 and §4.7: a sheet opens from the bottom, traps focus and returns it, closes with
// Escape, its button, its backdrop or a long enough downward swipe on its handle.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";
import { Sheet } from "./Sheet";

function Harness({ onClose = () => undefined }: { onClose?: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button type="button" onClick={() => setOpen(true)}>Open</button>
      {open ? (
        <Sheet title="Display" onClose={() => { onClose(); setOpen(false); }} closeLabel="Done">
          <button type="button">First inside</button>
          <button type="button">Last inside</button>
        </Sheet>
      ) : null}
    </>
  );
}

function openSheet(onClose?: () => void) {
  render(<Harness onClose={onClose} />);
  const opener = screen.getByRole("button", { name: "Open" });
  opener.focus();
  fireEvent.click(opener);
  return { opener, dialog: screen.getByRole("dialog", { name: "Display" }) };
}

describe("a sheet", () => {
  it("is a labelled modal dialog that takes focus, and gives it back when it closes", () => {
    const { opener, dialog } = openSheet();
    expect(dialog.getAttribute("aria-modal")).toBe("true");
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Done" }));
    fireEvent.click(screen.getByRole("button", { name: "Done" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(opener);
  });

  it("keeps Tab inside, both ways", () => {
    const { dialog } = openSheet();
    const last = screen.getByRole("button", { name: "Last inside" });
    last.focus();
    fireEvent.keyDown(dialog, { key: "Tab" });
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Done" }));
    fireEvent.keyDown(dialog, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(last);
  });

  it("closes on Escape and on its backdrop", () => {
    const closed = vi.fn();
    const { dialog } = openSheet(closed);
    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(closed).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    fireEvent.click(document.querySelector(".sheet-backdrop") as Element);
    expect(closed).toHaveBeenCalledTimes(2);
  });

  it("a short swipe down springs back; past a quarter of its height it closes", () => {
    // jsdom has no PointerEvent; a MouseEvent carries the clientY the sheet reads.
    if (typeof window.PointerEvent === "undefined") vi.stubGlobal("PointerEvent", class extends MouseEvent {});
    const closed = vi.fn();
    const { dialog } = openSheet(closed);
    vi.spyOn(dialog, "getBoundingClientRect").mockReturnValue({ height: 400 } as DOMRect);
    const handle = document.querySelector(".sheet-handle") as Element;
    act(() => {
      fireEvent.pointerDown(handle, { clientY: 500 });
      fireEvent.pointerMove(handle, { clientY: 550 });
      fireEvent.pointerUp(handle, { clientY: 550 });
    });
    expect(closed).not.toHaveBeenCalled();
    expect(dialog.style.transform).toBe("");
    act(() => {
      fireEvent.pointerDown(handle, { clientY: 500 });
      fireEvent.pointerMove(handle, { clientY: 620 });
      fireEvent.pointerUp(handle, { clientY: 620 });
    });
    expect(closed).toHaveBeenCalledTimes(1);
  });
});
