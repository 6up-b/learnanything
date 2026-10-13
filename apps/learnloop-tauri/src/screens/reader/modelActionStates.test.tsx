// G56: every model-backed action has seven states rendered the same way:
// pending (with "usually about N s" only when measured, and cancel), landed,
// failed (input kept), model unreachable, sidecar down, capped (naming the cap
// and what still works) and switched off (absent: no disabled control).
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ModelActionState, phaseForError } from "./ModelActionState";

afterEach(cleanup);

it("pending says what is happening and offers cancel; a time only when measured", () => {
  const cancel = vi.fn();
  const { rerender } = render(<ModelActionState phase="pending" verb="writing an answer" onCancel={cancel} />);
  expect(screen.getByRole("status").textContent).toContain("writing an answer…");
  expect(screen.getByRole("status").textContent).not.toMatch(/usually/);
  fireEvent.click(screen.getByRole("button", { name: "cancel" }));
  expect(cancel).toHaveBeenCalled();
  rerender(<ModelActionState phase="pending" verb="writing an answer" usuallySeconds={6.4} />);
  expect(screen.getByRole("status").textContent).toContain("usually about 6 s");
});

it("landed renders the result only", () => {
  render(<ModelActionState phase="landed" verb="writing"><p>the answer</p></ModelActionState>);
  expect(screen.getByText("the answer")).toBeTruthy();
  expect(screen.queryByRole("status")).toBeNull();
});

it("failed says what failed and what is kept, with try again", () => {
  const retry = vi.fn();
  render(<ModelActionState phase="failed" verb="writing" failure="Couldn't get an answer." kept="Your question is kept." onRetry={retry} />);
  const text = screen.getByRole("status").textContent ?? "";
  expect(text).toContain("Couldn't get an answer.");
  expect(text).toContain("Your question is kept.");
  fireEvent.click(screen.getByRole("button", { name: "try again ↵" }));
  expect(retry).toHaveBeenCalled();
});

it("model unreachable differs from sidecar down", () => {
  const { rerender } = render(<ModelActionState phase="unreachable" verb="writing" kept="Your question is kept." />);
  expect(screen.getByRole("status").textContent).toContain("Couldn't reach LearnLoop's model. Your question is kept.");
  rerender(<ModelActionState phase="offline" verb="writing" />);
  expect(screen.getByRole("status").textContent).toContain("background service isn't responding");
});

it("capped names the route's budget and what still works", () => {
  render(<ModelActionState phase="capped" verb="writing" capRoute="tutor" capAmount="$1.00" fallback="Your saved threads" />);
  expect(screen.getByRole("status").textContent).toBe("Today's tutor budget ($1.00) is used. Your saved threads still works.");
});

it("switched off (and idle) render nothing at all", () => {
  const { container, rerender } = render(<ModelActionState phase="off" verb="writing" />);
  expect(container.innerHTML).toBe("");
  rerender(<ModelActionState phase="idle" verb="writing" />);
  expect(container.innerHTML).toBe("");
});

it("maps rejected calls to their state", () => {
  expect(phaseForError({ code: "sidecar_unavailable", message: "down" })).toBe("offline");
  expect(phaseForError({ code: "provider_unavailable", message: "no model" })).toBe("unreachable");
  expect(phaseForError({ code: "question_limit_reached", message: "limit" })).toBe("capped");
  expect(phaseForError(new Error("boom"))).toBe("failed");
});
