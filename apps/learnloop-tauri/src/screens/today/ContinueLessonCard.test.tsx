// Teacher TE2 (spec_teacher_v1 §11.8): Today's "Continue your lesson on X" with "Close it", and "Learn something new".
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ContinueLessonCard } from "./ContinueLessonCard";

const { api } = vi.hoisted(() => ({ api: { lessonOpenLessons: vi.fn(), lessonTurn: vi.fn() } }));
vi.mock("../../api/client", () => ({ api }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

it("lists each open lesson to continue or close, and offers a new one", async () => {
  api.lessonOpenLessons.mockResolvedValueOnce({ lessons: [
    { lessonId: "les1", title: "Eigenvalues", goal: "Eigenvalues", openedAt: "t", learningObjectIds: ["lo_eigen"] }] });
  const onStartLesson = vi.fn();
  await act(async () => { render(<ContinueLessonCard onStartLesson={onStartLesson} onError={vi.fn()} />); });
  expect(screen.getByTestId("continue-lesson").textContent).toContain("Continue your lesson on Eigenvalues");
  fireEvent.click(screen.getByText("Continue"));
  expect(onStartLesson).toHaveBeenCalledWith({ kind: "resume", lessonId: "les1" });
  api.lessonTurn.mockResolvedValueOnce({});
  await act(async () => { fireEvent.click(screen.getByText("Close it")); });
  expect(api.lessonTurn).toHaveBeenCalledWith({ action: "close", lessonId: "les1" });
  expect(screen.queryByTestId("continue-lesson")).toBeNull();
  fireEvent.click(screen.getByTestId("learn-something-new"));
  expect(onStartLesson).toHaveBeenLastCalledWith({ kind: "typed" });
});
