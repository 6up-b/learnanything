// A carried question beside several passages of one window (its own and related ones, RD10): each placement is its
// own mark, so one click opens one popover and React's keys never collide.
import { act, cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CarriedQuestionDto } from "../../../api/dto";
import { WINDOW_ATTRIBUTE } from "../keys/listeners";
import { PassageMarks, placeMarks } from "./PassageMarks";

afterEach(cleanup);

function question(spanId: string): CarriedQuestionDto {
  return { carriedId: "c1", text: "why real?", originKind: "typed", originRef: null, anchor: { extraction_id: "ext_book", span_id: spanId },
    deskId: null, since: "2026-11-20T10:00:00Z", state: "carried", carried: true, version: 1, updatedAt: "2026-11-20T10:00:00Z" } as unknown as CarriedQuestionDto;
}

function stage(): HTMLElement {
  const root = document.createElement("div");
  root.innerHTML = `<div ${WINDOW_ATTRIBUTE}="w" data-window-state="active"><p data-span-id="s1">one</p><p data-span-id="s2">two</p></div>`;
  document.body.appendChild(root);
  return root;
}

describe("a saved question beside two passages of one window", () => {
  it("is two marks with their own keys, and a click opens one popover", async () => {
    const root = stage();
    const carried = [question("s1"), question("s2")];
    const placed = placeMarks(root, [{ windowId: "w", extractionId: "ext_book" }], [], carried);
    expect(placed).toHaveLength(2);
    expect(new Set(placed.map((mark) => mark.key)).size).toBe(2);
    render(<PassageMarks stage={root} windows={[{ windowId: "w", extractionId: "ext_book" }]} links={[]} carried={carried}
      onOpenLink={vi.fn()} onSurfaced={vi.fn()} onMarkCarried={vi.fn()} />);
    await act(async () => { await Promise.resolve(); });
    const buttons = document.querySelectorAll("button[aria-label='Open saved question']");
    expect(buttons).toHaveLength(2);
    fireEvent.click(buttons[0]);
    expect(document.querySelectorAll(".desk-pmark .pop")).toHaveLength(1);
    root.remove();
  });
});
