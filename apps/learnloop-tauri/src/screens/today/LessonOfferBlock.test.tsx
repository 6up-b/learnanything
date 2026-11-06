// Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): a lesson offer as a block of today's plan.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { PlanBlockDto, PlanLessonOfferDto } from "../../api/dto";
import { LessonOfferBlock } from "./LessonOfferBlock";
import { todayRows } from "../../app/todayPlan";

const { api } = vi.hoisted(() => ({ api: { lessonSuggestionRespond: vi.fn() } }));
vi.mock("../../api/client", () => ({ api }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const OFFER: PlanLessonOfferDto = {
  decisionId: "dec1", blockId: "blk1", minutes: 15, whyLabel: "Suggested by LearnLoop's planner", answered: null,
  suggestion: { ref: "lesson:lo_eigen", title: "Eigenvalues", learningObjectIds: ["lo_eigen"], reason: "cold_failing",
                why: "Your last two checks on it didn't come out right." },
  alternatives: [{ ref: "lesson:lo_det", title: "Determinants", learningObjectIds: ["lo_det"], reason: "new_goal",
                   why: "It's on your goal and you haven't started it yet." }]
};

function mount(offer: PlanLessonOfferDto = OFFER) {
  const onStartLesson = vi.fn();
  const onAnswered = vi.fn();
  const onError = vi.fn();
  render(<LessonOfferBlock offer={offer} sessionId="sess1" onStartLesson={onStartLesson} onAnswered={onAnswered}
                           onError={onError} />);
  return { onStartLesson, onAnswered, onError };
}

it("shows the offer in plain words with Start, the alternative and Not now, never as a dialog", () => {
  mount();
  const block = screen.getByTestId("lesson-offer-block");
  expect(block.textContent).toContain("Learn Eigenvalues now? (about 15 min)");
  expect(block.textContent).toContain("Your last two checks on it didn't come out right.");
  expect(screen.getByRole("button", { name: "Start" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Or: Determinants" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Not now" })).toBeTruthy();
  expect(screen.queryByRole("dialog")).toBeNull();
});

it("Start answers the block's own decision, re-reads the plan and opens the lesson", async () => {
  const { onStartLesson, onAnswered } = mount();
  api.lessonSuggestionRespond.mockResolvedValueOnce({
    decisionId: "dec1", response: "accepted", candidateRef: "lesson:lo_eigen",
    lesson: { lessonId: "les_1", decisionId: "dec1", learningObjectIds: ["lo_eigen"], title: "Eigenvalues" }
  });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Start" })); });
  expect(api.lessonSuggestionRespond).toHaveBeenCalledWith({ decisionId: "dec1", response: "accepted", sessionId: "sess1" });
  expect(onAnswered).toHaveBeenCalled();
  expect(onStartLesson).toHaveBeenCalledWith({
    kind: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"], title: "Eigenvalues",
    suggestion: { decisionId: "dec1", lessonId: "les_1" }
  });
});

it("Not now answers declined and goes on with the plan (no lesson opens)", async () => {
  const { onStartLesson, onAnswered } = mount();
  api.lessonSuggestionRespond.mockResolvedValueOnce({
    decisionId: "dec1", response: "declined", candidateRef: "lesson:lo_eigen", lesson: null
  });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Not now" })); });
  expect(api.lessonSuggestionRespond).toHaveBeenCalledWith({ decisionId: "dec1", response: "declined", sessionId: "sess1" });
  expect(onAnswered).toHaveBeenCalled();
  expect(onStartLesson).not.toHaveBeenCalled();
});

it("an alternative names its candidate", async () => {
  mount();
  api.lessonSuggestionRespond.mockResolvedValueOnce({ decisionId: "dec1", response: "chose_alternative",
                                                     candidateRef: "lesson:lo_det", lesson: null });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Or: Determinants" })); });
  expect(api.lessonSuggestionRespond).toHaveBeenCalledWith({
    decisionId: "dec1", response: "chose_alternative", sessionId: "sess1", candidateRef: "lesson:lo_det" });
});

it("an answered offer shows nothing", () => {
  mount({ ...OFFER, answered: "declined" });
  expect(screen.queryByTestId("lesson-offer-block")).toBeNull();
});

it("Today's rows name the offer's block in plain words", () => {
  const block = {
    id: "blk1", ordinal: 2, lane: "new", action: "instruct", subtype: "lesson_offer", chosenBy: "mixture", why: "",
    whyKind: null, fallback: false, estMinutes: 0, status: "current", startedAt: null, endedAt: null, outcome: null,
    reading: null, learningObjectTitles: [], items: [], displacedCount: 0, lessonOffer: OFFER
  } as unknown as PlanBlockDto;
  const rows = todayRows({ blocks: [block], projected: [], currentBlockId: "blk1" } as never);
  expect(rows[0].text).toBe("A lesson you could take · Eigenvalues");
});
