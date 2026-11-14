// The brief wizard reopens on a saved brief ("edit brief" in Quick Add and on a
// collection); saving again without touching a field must keep it.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { StudyMapBriefDto } from "../api/dto";
import { StudyMapBriefWizard } from "./StudyMapBriefWizard";

afterEach(() => cleanup());

// The wizard saves a due date as that day's 23:59:59 local time.
const DUE = new Date(2026, 10, 27, 23, 59, 59).toISOString();

const EXAM_BRIEF: StudyMapBriefDto = {
  outcome: "exam_prep",
  startingLevel: "some_exposure",
  level: "undergraduate",
  depth: "deep",
  notation: "Leibniz",
  includeTopics: ["Bayes' theorem"],
  excludeTopics: ["measure theory"],
  scope: "Only chapters 1-3.",
  practiceItems: "upfront",
  goalTitle: "Probability midterm",
  intentSentence: "Pass the midterm.",
  dueAt: DUE,
  targetRecall: 0.9,
  examItemCount: 12
};

function reopen(initialBrief: StudyMapBriefDto) {
  const onSubmit = vi.fn();
  render(<StudyMapBriefWizard initialBrief={initialBrief} submitLabel="Use brief" onSubmit={onSubmit} onClose={vi.fn()} />);
  for (let step = 0; step < 3; step += 1) fireEvent.click(screen.getByRole("button", { name: "next →" }));
  return onSubmit;
}

function dateInput(): HTMLInputElement {
  return document.querySelector('input[type="date"]') as HTMLInputElement;
}

it("starts the due date from the brief it was opened with", () => {
  reopen(EXAM_BRIEF);
  expect(dateInput().value).toBe("2026-11-27");
});

it("saving without touching the date keeps the deadline, and every other field", () => {
  const onSubmit = reopen(EXAM_BRIEF);
  fireEvent.click(screen.getByRole("button", { name: "Use brief" }));

  expect(onSubmit).toHaveBeenCalledTimes(1);
  const [brief, createGoal] = onSubmit.mock.calls[0];
  expect(brief).toEqual(EXAM_BRIEF);
  expect(createGoal).toBe(true);
});

it("clearing the date removes the deadline", () => {
  const onSubmit = reopen(EXAM_BRIEF);
  fireEvent.change(dateInput(), { target: { value: "" } });
  fireEvent.click(screen.getByRole("button", { name: "Use brief" }));

  expect(onSubmit.mock.calls[0][0].dueAt).toBeUndefined();
});

it("a date-only deadline opens on that day", () => {
  reopen({ ...EXAM_BRIEF, dueAt: "2026-11-27" });
  expect(dateInput().value).toBe("2026-11-27");
});
