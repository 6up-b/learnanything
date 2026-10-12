import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { DiagnosisCardDto } from "../api/dto";
import { DiagnosisCard, DIAGNOSIS_POLL_MS } from "./DiagnosisCard";

const api = vi.hoisted(() => ({ diagnosisStatus: vi.fn(), recordDiagnosisFeedback: vi.fn() }));
vi.mock("../api/client", () => ({ api }));

const RESPONSES = [
  { response: "believed_candidate", label: "That's it" },
  { response: "partly", label: "Partly" },
  { response: "slipped", label: "I just slipped" },
  { response: "diagnosis_wrong", label: "That's wrong" },
  { response: "unsure", label: "Not sure" },
] as const;

const PENDING: DiagnosisCardDto = {
  version: 1,
  attemptId: "att_1",
  status: "pending",
  cardEnabled: true,
  responses: [...RESPONSES],
};

const DONE: DiagnosisCardDto = {
  ...PENDING,
  status: "done",
  diagnosisId: "diag_1",
  summaryMd: "You keep leaving the final factor untransposed.",
  repairSuggestions: [
    { practiceMode: "redo", learningObjectId: null, rationale: "Say what the transpose does." },
  ],
  madeBefore: [
    {
      attemptId: "att_0",
      practiceItemId: "pi_0",
      date: "2026-05-01T09:00:00Z",
      quote: "U Sigma V",
      rubricScore: 2,
      correctness: 0.5,
    },
  ],
  prerequisiteGap: {
    prerequisiteRef: "lo_transpose",
    title: "Transpose a matrix",
    suggestedCheckMd: null,
    label: "possible cause - not yet checked",
  },
  recordedResponse: null,
  notSameMistakeAttemptIds: [],
};

beforeEach(() => {
  vi.useFakeTimers();
  api.diagnosisStatus.mockReset();
  api.recordDiagnosisFeedback.mockReset().mockResolvedValue({
    version: 1,
    feedbackId: "fb_1",
    forwardedFactorId: null,
    forwarding: "card_only",
  });
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

it("shows a placeholder while pending, polls, and fills in place when done", async () => {
  api.diagnosisStatus.mockResolvedValueOnce(PENDING).mockResolvedValueOnce(DONE);
  const ready = vi.fn();
  render(
    <DiagnosisCard attemptId="att_1" initialStatus="pending" onDiagnosisReady={ready} onError={vi.fn()} />,
  );
  await act(async () => {});
  expect(screen.getByTestId("diagnosis-pending").textContent).toContain("analyzing your pattern");
  expect(ready).not.toHaveBeenCalled();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(DIAGNOSIS_POLL_MS);
  });
  expect(screen.getByTestId("diagnosis-summary").textContent).toContain("untransposed");
  expect(screen.getByTestId("diagnosis-made-before").textContent).toContain("U Sigma V");
  expect(screen.getByTestId("diagnosis-prerequisite").textContent).toContain("not yet checked");
  expect(ready).toHaveBeenCalledTimes(1);
  // Done: polling stops.
  await act(async () => {
    await vi.advanceTimersByTimeAsync(DIAGNOSIS_POLL_MS * 4);
  });
  expect(api.diagnosisStatus).toHaveBeenCalledTimes(2);
});

it("renders the taps in the fixed neutral order and records one", async () => {
  api.diagnosisStatus.mockResolvedValue(DONE);
  render(<DiagnosisCard attemptId="att_1" initialStatus="done" onError={vi.fn()} />);
  await act(async () => {});
  const taps = screen.getByTestId("diagnosis-taps").children;
  expect(Array.from(taps).map((node) => node.textContent)).toEqual([
    "That's it",
    "Partly",
    "I just slipped",
    "That's wrong",
    "Not sure",
  ]);
  await act(async () => {
    fireEvent.click(screen.getByTestId("diagnosis-tap-partly"));
  });
  expect(api.recordDiagnosisFeedback).toHaveBeenCalledWith(
    expect.objectContaining({ attemptId: "att_1", diagnosisId: "diag_1", response: "partly" }),
  );
  // One optional tap: the others are no longer actionable.
  await act(async () => {
    fireEvent.click(screen.getByTestId("diagnosis-tap-unsure"));
  });
  expect(api.recordDiagnosisFeedback).toHaveBeenCalledTimes(1);
});

it("records a per-citation 'not the same mistake'", async () => {
  api.diagnosisStatus.mockResolvedValue(DONE);
  render(<DiagnosisCard attemptId="att_1" initialStatus="done" onError={vi.fn()} />);
  await act(async () => {});
  await act(async () => {
    fireEvent.click(screen.getByText("not the same mistake"));
  });
  expect(api.recordDiagnosisFeedback).toHaveBeenCalledWith(
    expect.objectContaining({ response: "not_same_mistake", citedAttemptId: "att_0" }),
  );
  expect(screen.getByTestId("diagnosis-made-before").textContent).toContain("noted: not the same");
});

it("renders nothing when no diagnosis was queued, and an honest note when it failed", async () => {
  const { container, rerender } = render(
    <DiagnosisCard attemptId="att_1" initialStatus={undefined} onError={vi.fn()} />,
  );
  await act(async () => {});
  expect(container.textContent).toBe("");
  expect(api.diagnosisStatus).not.toHaveBeenCalled();
  api.diagnosisStatus.mockResolvedValue({ ...PENDING, status: "failed" });
  rerender(<DiagnosisCard attemptId="att_1" initialStatus="failed" onError={vi.fn()} />);
  await act(async () => {});
  expect(screen.getByTestId("diagnosis-failed").textContent).toContain("grade above stands");
});

it("respects the card kill switch", async () => {
  api.diagnosisStatus.mockResolvedValue({ ...DONE, cardEnabled: false });
  const { container } = render(
    <DiagnosisCard attemptId="att_1" initialStatus="done" onError={vi.fn()} />,
  );
  await act(async () => {});
  expect(container.textContent).toBe("");
});
