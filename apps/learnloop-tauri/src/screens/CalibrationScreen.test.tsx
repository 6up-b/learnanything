import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { CalibrationSessionProgressDto, QuickCheckProgressDto } from "../api/dto";
import { CalibrationScreen } from "./CalibrationScreen";

const { api } = vi.hoisted(() => ({
  api: { getCalibrationSession: vi.fn(), stopCalibrationSession: vi.fn() }
}));
vi.mock("../api/client", () => ({ api }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function progress(quickCheck: QuickCheckProgressDto, status: CalibrationSessionProgressDto["status"] = "active"): CalibrationSessionProgressDto {
  return {
    version: 1,
    calibrationSessionId: "cal1",
    sessionId: "s1",
    goalId: null,
    status,
    timeBudgetMinutes: 8,
    elapsedMinutes: 1,
    remainingMinutes: 7,
    blocksCompleted: 0,
    blocksPlanned: 0,
    episodes: [],
    nextTarget: status === "active"
      ? { episodeId: null, learningObjectId: "lo_diag", practiceItemId: "pi_diag_mid", selectionObjective: "conditional_gain", entropy: null }
      : null,
    quickCheck
  };
}

async function show(snapshot: CalibrationSessionProgressDto) {
  api.getCalibrationSession.mockResolvedValue(snapshot);
  const props = {
    onPractice: vi.fn(), onReviewAnswer: vi.fn(), onExit: vi.fn(), onError: vi.fn()
  };
  await act(async () => {
    render(<CalibrationScreen calibrationSessionId="cal1" {...props} />);
  });
  return props;
}

it("a running quick check withholds results and serves its next question", async () => {
  const props = await show(progress({
    learningObjectIds: ["lo_diag"], k: 4, answered: 1, remaining: 3, finished: false, results: null
  }));
  expect(screen.getByText("Check what I already know")).toBeTruthy();
  expect(screen.getByText("1/4 questions")).toBeTruthy();
  expect(screen.getByText("Answers are graded as you go; results and feedback appear when the check ends.")).toBeTruthy();
  expect(screen.queryByText(/Diagnostic dialogue/)).toBeNull();
  fireEvent.click(screen.getByText("Answer the next question"));
  expect(props.onPractice).toHaveBeenCalledWith("pi_diag_mid");
});

it("a finished quick check lists each topic's verdict and opens feedback per answer", async () => {
  const props = await show(progress({
    learningObjectIds: ["lo_diag", "lo_eigen"], k: 4, answered: 3, remaining: 1, finished: true,
    results: [
      {
        learningObjectId: "lo_diag", learningObjectTitle: "Diagonalization", verdict: "assumed", assumptionId: "a1",
        answers: [
          { attemptId: "att1", practiceItemId: "pi_diag_hard", learningObjectId: "lo_diag", correctness: 1, createdAt: "2026-10-12T10:00:00Z" },
          { attemptId: "att2", practiceItemId: "pi_diag_mid", learningObjectId: "lo_diag", correctness: 1, createdAt: "2026-10-12T10:01:00Z" }
        ]
      },
      {
        learningObjectId: "lo_eigen", learningObjectTitle: "Eigenvalues", verdict: "learning", assumptionId: null,
        answers: [
          { attemptId: "att3", practiceItemId: "pi_eig_mid", learningObjectId: "lo_eigen", correctness: 0.25, createdAt: "2026-10-12T10:02:00Z" }
        ]
      }
    ]
  }, "completed"));
  expect(screen.getByText("assumed (not tested)")).toBeTruthy();
  expect(screen.getByText("skipped for now; its first review in two weeks is the check")).toBeTruthy();
  expect(screen.getByText("it starts as learning")).toBeTruthy();
  expect(screen.getByText("25%")).toBeTruthy();
  fireEvent.click(screen.getAllByText("review answer")[2]);
  expect(props.onReviewAnswer).toHaveBeenCalledWith("att3");
});
