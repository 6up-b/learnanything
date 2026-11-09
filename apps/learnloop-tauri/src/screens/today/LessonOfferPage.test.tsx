// Instruct hand-off IH1 (spec_instruct_handoff_v1 §4): the offer page's wording, its actions, and the `offer_shown`
// call (once per render path, never disturbing the page).
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { PlanLessonOfferDto, PlanLessonOfferStepDto } from "../../api/dto";
import { LessonOfferBlock } from "./LessonOfferBlock";
import { LessonOfferPage, offerSentence } from "./LessonOfferPage";

const { api } = vi.hoisted(() => ({
  api: { lessonSuggestionRespond: vi.fn(), recordOfferShown: vi.fn(async () => ({ version: 1, recorded: true })) }
}));
vi.mock("../../api/client", () => ({ api }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const OFFER: PlanLessonOfferDto = {
  decisionId: "dec1", blockId: "blk1", minutes: 12, whyLabel: "Suggested by LearnLoop's planner", answered: null,
  suggestion: { ref: "lesson:lo_relu", title: "ReLU", learningObjectIds: ["lo_relu"], reason: "cold_failing",
                why: "Your last two checks on it didn't come out right." },
  alternatives: [
    { ref: "lesson:lo_det", title: "Determinants", learningObjectIds: ["lo_det"], reason: "new_goal", why: "It's on your goal." },
    { ref: "lesson:lo_svd", title: "The SVD", learningObjectIds: ["lo_svd"], reason: "below_band", why: "Within reach." }
  ]
};
const STEP: PlanLessonOfferStepDto = {
  kind: "lesson_offer", planId: "p1", blockId: "blk1", blockOrdinal: 2, offer: OFFER, estMinutes: 12, boundary: true,
  why: "Picked to vary the order today.", whyKind: "computed"
};

function mount(step: PlanLessonOfferStepDto = STEP) {
  const onStartLesson = vi.fn();
  const onAnswered = vi.fn();
  const onError = vi.fn();
  render(<LessonOfferPage step={step} sessionId="sess1" onStartLesson={onStartLesson} onAnswered={onAnswered}
                          onError={onError} />);
  return { onStartLesson, onAnswered, onError };
}

it("says exactly the spec's sentence, with the offer's minutes and topic", () => {
  mount();
  expect(offerSentence(12, "ReLU")).toBe("This looks like something to learn. Start a 12 minute lesson on ReLU?");
  expect(screen.getByTestId("lesson-offer-sentence").textContent)
    .toBe("This looks like something to learn. Start a 12 minute lesson on ReLU?");
  expect(screen.queryByRole("dialog")).toBeNull();
});

it("has Start, Not now and up to two other topics, and leaves a place for IH3's link", () => {
  mount();
  expect(screen.getByRole("button", { name: "Start" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Not now" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Or: Determinants" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Or: The SVD" })).toBeTruthy();
  expect(screen.getByTestId("lesson-offer-something-else-slot")).toBeTruthy();
});

it("shows the router's rationale only when its guard let a model's through, else the plain reason", () => {
  mount();
  expect(screen.getByTestId("lesson-offer-reason").textContent).toContain("Your last two checks on it didn't come out right.");
  expect(screen.getByTestId("lesson-offer-reason").textContent).not.toContain("Picked to vary");
  cleanup();
  mount({ ...STEP, why: "A model wrote: you keep missing the sign.", whyKind: "model_written" });
  expect(screen.getByTestId("lesson-offer-reason").textContent).toContain("you keep missing the sign");
});

it("Start is one tap: it answers the offer's own decision and opens the lesson", async () => {
  const { onStartLesson, onAnswered } = mount();
  api.lessonSuggestionRespond.mockResolvedValueOnce({
    decisionId: "dec1", response: "accepted", candidateRef: "lesson:lo_relu",
    lesson: { lessonId: "les_1", decisionId: "dec1", learningObjectIds: ["lo_relu"], title: "ReLU" }
  });
  expect(api.lessonSuggestionRespond).not.toHaveBeenCalled(); // nothing starts unasked
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Start" })); });
  expect(api.lessonSuggestionRespond).toHaveBeenCalledTimes(1);
  expect(api.lessonSuggestionRespond).toHaveBeenCalledWith({ decisionId: "dec1", response: "accepted", sessionId: "sess1" });
  expect(onAnswered).toHaveBeenCalledWith("accepted");
  expect(onStartLesson).toHaveBeenCalledWith({
    kind: "open", entry: "learning_object", learningObjectIds: ["lo_relu"], title: "ReLU",
    suggestion: { decisionId: "dec1", lessonId: "les_1" }
  });
});

it("Not now answers declined, opens no lesson and moves the plan on", async () => {
  const { onStartLesson, onAnswered } = mount();
  api.lessonSuggestionRespond.mockResolvedValueOnce({ decisionId: "dec1", response: "declined", candidateRef: "x", lesson: null });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Not now" })); });
  expect(api.lessonSuggestionRespond).toHaveBeenCalledWith({ decisionId: "dec1", response: "declined", sessionId: "sess1" });
  expect(onAnswered).toHaveBeenCalledWith("declined");
  expect(onStartLesson).not.toHaveBeenCalled();
});

it("writes offer_shown once for the page, and once for the card, each on its own surface", async () => {
  const { rerender } = render(<LessonOfferPage step={STEP} sessionId="sess1" onAnswered={vi.fn()} onError={vi.fn()} />);
  rerender(<LessonOfferPage step={{ ...STEP }} sessionId="sess1" onAnswered={vi.fn()} onError={vi.fn()} />);
  await act(async () => undefined);
  expect(api.recordOfferShown).toHaveBeenCalledTimes(1);
  expect(api.recordOfferShown).toHaveBeenCalledWith({ blockId: "blk1", surface: "offer_page", sessionId: "sess1" });
  cleanup();
  vi.clearAllMocks();
  render(<LessonOfferBlock offer={OFFER} sessionId="sess1" onAnswered={vi.fn()} onError={vi.fn()} />);
  await act(async () => undefined);
  expect(api.recordOfferShown).toHaveBeenCalledTimes(1);
  expect(api.recordOfferShown).toHaveBeenCalledWith({ blockId: "blk1", surface: "today", sessionId: "sess1" });
});

it("an answered offer's card renders nothing and writes nothing", async () => {
  render(<LessonOfferBlock offer={{ ...OFFER, answered: "declined" }} sessionId="sess1" onAnswered={vi.fn()} onError={vi.fn()} />);
  await act(async () => undefined);
  expect(screen.queryByTestId("lesson-offer-block")).toBeNull();
  expect(api.recordOfferShown).not.toHaveBeenCalled();
});

it("a failing offer_shown call never disturbs the page", async () => {
  api.recordOfferShown.mockRejectedValueOnce(new Error("sidecar down"));
  mount();
  await act(async () => undefined);
  expect(screen.getByTestId("lesson-offer-sentence")).toBeTruthy();
  cleanup();
  api.recordOfferShown.mockImplementationOnce(() => { throw new Error("sync failure"); });
  mount();
  expect(screen.getByTestId("lesson-offer-sentence")).toBeTruthy();
});
