// Quick Add is where new-vault onboarding sends a student who skipped the
// optional first subject, so it must be able to make one; and the exam-prep
// brief's "creates the Goal in the same flow" must reach the build.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { QuickAddDialog } from "./QuickAddDialog";

const api = vi.hoisted(() => ({
  runCliCommand: vi.fn(),
  planQuickAdd: vi.fn(),
  confirmQuickAdd: vi.fn(),
  startImportBatch: vi.fn(),
  getIngestBatch: vi.fn()
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("./useSourceFileDrop", () => ({ useSourceFileDrop: () => false, pickSourceFile: vi.fn() }));

const PLAN = {
  title: "Probability notes",
  normalizedUri: "/notes/probability.md",
  wholeSource: true,
  selectedUnitIds: ["u1"],
  selectedUnitLabels: ["Conditional probability"],
  suggestedRole: "primary_textbook",
  roleAmbiguous: false,
  confirmation: { estimatedInputTokens: 1000, externalAiConsent: [] }
};

beforeEach(() => {
  api.runCliCommand.mockResolvedValue({ argv: [], exitCode: 0, stdout: "", stderr: "" });
  api.planQuickAdd.mockResolvedValue({ plan: PLAN });
  api.confirmQuickAdd.mockResolvedValue({ quickAdd: { batchId: "batch_1" } });
});

afterEach(() => cleanup());

function analyze(): HTMLButtonElement {
  return screen.getByRole("button", { name: "Analyze →" }) as HTMLButtonElement;
}

it("with no subject to pick, lets the student create one and Analyze enables", async () => {
  render(
    <QuickAddDialog subjects={[]} defaultSource="/notes/probability.md" guided onClose={vi.fn()} onEnqueued={vi.fn()} />
  );
  expect(analyze().disabled).toBe(true);

  fireEvent.change(screen.getByPlaceholderText("new subject title"), { target: { value: "Probability 101" } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "create subject" }));
  });

  expect(api.runCliCommand).toHaveBeenCalledWith(["add-subject", "probability-101", "Probability 101"]);
  await waitFor(() => expect(analyze().disabled).toBe(false));
  await act(async () => {
    fireEvent.click(analyze());
  });
  expect(api.planQuickAdd).toHaveBeenCalledWith(expect.objectContaining({ subjectId: "probability-101" }));
});

async function examPrepBriefDue(date: string) {
  fireEvent.click(screen.getByText("customize brief"));
  fireEvent.click(screen.getByText("exam prep"));
  for (let step = 0; step < 3; step += 1) fireEvent.click(screen.getByRole("button", { name: "next →" }));
  fireEvent.change(screen.getByPlaceholderText("e.g. Linear algebra final"), { target: { value: "Probability midterm" } });
  fireEvent.change(document.querySelector('input[type="date"]') as HTMLInputElement, { target: { value: date } });
  fireEvent.click(screen.getByRole("button", { name: "Use brief" }));
}

async function analyzeAndConfirm() {
  await act(async () => {
    fireEvent.click(analyze());
  });
  await act(async () => {
    fireEvent.click(await screen.findByRole("button", { name: "Confirm & build" }));
  });
}

it("an exam-prep brief asks the build for its goal, with the brief's deadline", async () => {
  const subjects = [{ id: "probability", title: "Probability" }];
  render(<QuickAddDialog subjects={subjects} defaultSource="/notes/probability.md" onClose={vi.fn()} onEnqueued={vi.fn()} />);
  await examPrepBriefDue("2026-11-27");
  await analyzeAndConfirm();

  expect(api.confirmQuickAdd).toHaveBeenCalledTimes(1);
  const input = api.confirmQuickAdd.mock.calls[0][0];
  expect(input.createGoal).toBe(true);
  expect(input.brief).toMatchObject({ outcome: "exam_prep", goalTitle: "Probability midterm" });
  expect(new Date(input.brief.dueAt).toDateString()).toBe(new Date(2026, 10, 27).toDateString());
});

it("a brief that is not exam prep asks for no goal", async () => {
  const subjects = [{ id: "probability", title: "Probability" }];
  render(<QuickAddDialog subjects={subjects} defaultSource="/notes/probability.md" onClose={vi.fn()} onEnqueued={vi.fn()} />);
  await analyzeAndConfirm();

  expect(api.confirmQuickAdd.mock.calls[0][0].createGoal).toBe(false);
});

it("a refused subject leaves Analyze disabled and says why", async () => {
  api.runCliCommand.mockResolvedValue({ argv: [], exitCode: 1, stdout: "", stderr: "Subject already exists" });
  render(
    <QuickAddDialog subjects={[]} defaultSource="/notes/probability.md" onClose={vi.fn()} onEnqueued={vi.fn()} />
  );

  fireEvent.change(screen.getByPlaceholderText("new subject title"), { target: { value: "Probability" } });
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "create subject" }));
  });

  expect(await screen.findByText("Subject already exists")).toBeTruthy();
  expect(analyze().disabled).toBe(true);
});
