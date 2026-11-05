// FG1c §7: the panel: optional marks in the server's order, a change of mind, None of these with its
// words, one display event per list, a failed save that says so and stands in nobody's way.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { HypothesisMarksDto } from "../../api/dto";
import { clear } from "../../api/queryCache";

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn() }));
vi.mock("@tauri-apps/api/core", () => ({ invoke }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

import { HypothesisMarksPanel, useHypothesisListExposure } from "./HypothesisMarks";

const MARKS: HypothesisMarksDto = {
  attemptId: "att_1", surface: "marks_feedback", orderSeed: "seed", probeAnswered: true, replacesCardTap: true,
  hypotheses: [
    { hypothesisVersionId: "h2", statement: "The second cause.", mark: null },
    { hypothesisVersionId: "h1", statement: "The first cause.", mark: null },
  ],
  noneOfThese: false, noneOfTheseText: null,
};

let reply: HypothesisMarksDto | null;
beforeEach(() => {
  reply = MARKS;
  invoke.mockImplementation(async (command: string) => {
    if (command === "record_hypothesis_exposure") return { version: 1, recorded: true };
    if (command === "record_hypothesis_mark") return { version: 1, recorded: true, marks: reply };
    return null;
  });
});
afterEach(() => { cleanup(); clear(); vi.clearAllMocks(); });

function calls(command: string) {
  return invoke.mock.calls.filter(([name]) => name === command).map(([, args]) => (args as { method?: unknown; params?: { input?: unknown } }));
}

function exposures() {
  return calls("record_hypothesis_exposure");
}

it("lists the causes in the server's order and sends one display event in that order", async () => {
  const { rerender } = render(<HypothesisMarksPanel marks={MARKS} />);
  const rows = screen.getAllByTestId("hypothesis-mark-row");
  expect(rows[0].textContent).toContain("The second cause.");
  expect(rows[1].textContent).toContain("The first cause.");
  await waitFor(() => expect(exposures().length).toBe(1));
  expect(JSON.stringify(exposures()[0])).toContain('"hypothesisVersionIds":["h2","h1"]');
  expect(JSON.stringify(exposures()[0])).toContain('"surface":"marks_feedback"');
  rerender(<HypothesisMarksPanel marks={MARKS} />);
  await waitFor(() => expect(exposures().length).toBe(1));
});

it("says plainly that it is optional and doesn't change the grade", () => {
  render(<HypothesisMarksPanel marks={MARKS} />);
  expect(screen.getByTestId("hypothesis-marks").textContent).toContain("optional");
  expect(screen.getByTestId("hypothesis-marks").textContent).toContain("doesn't change your grade");
});

it("records a mark, shows it, and tapping it again takes it back", async () => {
  reply = { ...MARKS, hypotheses: [{ ...MARKS.hypotheses[0], mark: "my_gap" }, MARKS.hypotheses[1]] };
  render(<HypothesisMarksPanel marks={MARKS} />);
  const row = within(screen.getAllByTestId("hypothesis-mark-row")[0]);
  fireEvent.click(row.getByText("This is my gap"));
  await waitFor(() => expect(row.getByText("This is my gap").getAttribute("aria-pressed")).toBe("true"));
  expect(JSON.stringify(calls("record_hypothesis_mark")[0])).toContain('"mark":"my_gap"');
  expect(JSON.stringify(calls("record_hypothesis_mark")[0])).toContain('"hypothesisVersionId":"h2"');
  reply = MARKS;
  fireEvent.click(row.getByText("This is my gap"));
  await waitFor(() => expect(row.getByText("This is my gap").getAttribute("aria-pressed")).toBe("false"));
  expect(JSON.stringify(calls("record_hypothesis_mark")[1])).toContain('"mark":"cleared"');
});

it("None of these opens an optional box and saves its words", async () => {
  reply = { ...MARKS, noneOfThese: true };
  render(<HypothesisMarksPanel marks={MARKS} />);
  expect(screen.queryByRole("textbox")).toBeNull();
  fireEvent.click(screen.getByText("None of these"));
  const box = await screen.findByRole("textbox");
  expect(screen.getByText("Save").hasAttribute("disabled")).toBe(true);
  reply = { ...MARKS, noneOfThese: true, noneOfTheseText: "I misread it" };
  fireEvent.change(box, { target: { value: "I misread it" } });
  fireEvent.click(screen.getByText("Save"));
  await waitFor(() => expect(calls("record_hypothesis_mark").length).toBe(2));
  expect(JSON.stringify(calls("record_hypothesis_mark")[1])).toContain('"freeText":"I misread it"');
});

it("a failed save says so and leaves everything usable", async () => {
  invoke.mockImplementation(async (command: string) => {
    if (command === "record_hypothesis_mark") throw new Error("nope");
    return { version: 1, recorded: true };
  });
  render(<HypothesisMarksPanel marks={MARKS} />);
  fireEvent.click(screen.getAllByText("Not it")[0]);
  expect((await screen.findByTestId("hypothesis-marks-failed")).textContent).toContain("optional");
  expect(screen.getAllByText("Not it")[0].hasAttribute("disabled")).toBe(false);
});

it("Enter on a mark stays with the mark and never reaches the screen's Next", () => {
  const next = vi.fn();
  window.addEventListener("keydown", next);
  render(<HypothesisMarksPanel marks={MARKS} />);
  fireEvent.keyDown(screen.getAllByText("Partly")[0], { key: "Enter" });
  window.removeEventListener("keydown", next);
  expect(next).not.toHaveBeenCalled();
});

function Listing({ ids, on }: { ids: string[]; on: boolean }) {
  useHypothesisListExposure("att_1", "why", ids, on);
  return null;
}

it("a list that isn't on screen sends nothing, and a refused receipt fails nothing", async () => {
  const { rerender } = render(<Listing ids={["h1"]} on={false} />);
  rerender(<Listing ids={[]} on />);
  expect(exposures().length).toBe(0);
  invoke.mockImplementation(async () => { throw new Error("refused"); });
  rerender(<Listing ids={["h1"]} on />);
  await waitFor(() => expect(exposures().length).toBe(1));
  rerender(<Listing ids={["h1"]} on />);
  rerender(<Listing ids={["h1", "h2"]} on />);
  await waitFor(() => expect(exposures().length).toBe(2));
});
