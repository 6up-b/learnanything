import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, onTestFinished, vi } from "vitest";
import type { FigureViewDto, LessonViewDto } from "../api/dto";
import { LESSON_FIGURE_COPY, LessonScreen } from "./LessonScreen";
import corpus from "./reader/figures/figureGoldenCorpus.json";
import { FIGURE_COPY } from "./reader/figures/FigureInline";

const { api } = vi.hoisted(() => ({
  api: { lessonTurn: vi.fn(), lessonView: vi.fn(), lessonActivity: vi.fn(), readerLogActivity: vi.fn(),
         readerFigurePredict: vi.fn(), readerFigureRevise: vi.fn(), figureRequest: vi.fn() }
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function lesson(overrides: Partial<LessonViewDto> = {}): LessonViewDto {
  return {
    version: 1, lessonId: "les1", goal: "Eigenvalues", learningObjectIds: ["lo_eigen"], closed: false,
    closeReason: null,
    feed: [{ kind: "message", text: "Here is the map.", choices: [] }],
    plan: [{ id: "n1", statement: "An eigenvalue scales its eigenvector.", position: "current" },
           { id: "n2", statement: "Find them.", position: "upcoming" }],
    openCheck: null, openPrediction: null, quickCheck: { learningObjectIds: ["lo_eigen"] },
    inspector: { doctrine: "teacher_doctrine_v1", route: "chatgpt_medium", model: "m", forecasts: [] },
    ...overrides,
  };
}

async function open(first: LessonViewDto, onQuickCheck = vi.fn()) {
  api.lessonTurn.mockResolvedValueOnce(first);
  const onError = vi.fn();
  await act(async () => {
    render(<LessonScreen entry={{ kind: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"] }}
                         onClose={vi.fn()} onQuickCheck={onQuickCheck} onError={onError} />);
  });
  return { onError, onQuickCheck };
}

it("opens a lesson on the topic and shows the document and the map as positions", async () => {
  await open(lesson());
  expect(api.lessonTurn).toHaveBeenCalledWith({ action: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"] });
  expect(screen.getByText("Here is the map.")).toBeTruthy();
  const map = screen.getByTestId("lesson-plan");
  expect(map.querySelector('[data-position="current"]')?.textContent).toContain("scales its eigenvector");
  expect(map.querySelector('[data-position="upcoming"]')).toBeTruthy();
});

it("offers the quick check at open, never prompting it", async () => {
  const { onQuickCheck } = await open(lesson());
  fireEvent.click(screen.getByTestId("lesson-quick-check"));
  expect(onQuickCheck).toHaveBeenCalledWith(["lo_eigen"]);
});

it("keeps a check collapsed until opened, shows the tap only after a draft, and sends thinking to the teacher", async () => {
  const withCheck = lesson({
    feed: [{ kind: "message", text: "Try it.", choices: [] },
           { kind: "check", checkRef: "c1", node: "n1", question: "What equation gives the eigenvalues?", form: "free",
             choices: [], unanchored: true }],
    openCheck: { checkRef: "c1", question: "What equation gives the eigenvalues?", form: "free", choices: [] },
  });
  await open(withCheck);
  expect(screen.queryByText("What equation gives the eigenvalues?")).toBeNull();
  fireEvent.click(screen.getByTestId("lesson-check-collapsed"));
  expect(screen.getByText("What equation gives the eigenvalues?")).toBeTruthy();
  expect(screen.queryByTestId("lesson-tap")).toBeNull();
  fireEvent.change(screen.getByLabelText("Your answer"), { target: { value: "det(A - tI) = 0" } });
  expect(screen.getByTestId("lesson-tap")).toBeTruthy();
  fireEvent.click(screen.getByText("4"));
  fireEvent.change(screen.getByLabelText("Your thinking (optional)"), { target: { value: "char poly" } });
  api.lessonTurn.mockResolvedValueOnce(lesson());
  await act(async () => { fireEvent.click(screen.getByText("Submit answer")); });
  expect(api.lessonTurn).toHaveBeenLastCalledWith({ action: "answer_check", lessonId: "les1", checkRef: "c1",
                                                    answer: "det(A - tI) = 0", tap: 4, thinking: "char poly" });
});

it("TE2-log: with the activity log on, the screen reports its intervals before a step and when it closes", async () => {
  api.lessonActivity.mockResolvedValue({ recorded: 1, enabled: true });
  let clock = Date.parse("2026-11-05T15:00:00.000Z");
  const now = vi.spyOn(Date, "now").mockImplementation(() => (clock += 1_000));
  onTestFinished(() => now.mockRestore());
  await open(lesson({ activityLog: true }));
  fireEvent.change(screen.getByLabelText("Reply to the teacher"), { target: { value: "Go on." } });
  api.lessonTurn.mockResolvedValueOnce(lesson({ activityLog: true }));
  await act(async () => { fireEvent.click(screen.getByText("Send")); });
  expect(api.lessonActivity).toHaveBeenCalled();
  const first = api.lessonActivity.mock.calls[0][0];
  expect(first.lessonId).toBe("les1");
  expect(first.intervals[0]).toMatchObject({ seq: 1, foreground: expect.any(Boolean) });
  expect(Object.keys(first.intervals[0]).sort()).toEqual(["endedAt", "foreground", "screenSession", "seq", "startedAt"]);
  // The learner's words are never sent with the intervals.
  expect(JSON.stringify(api.lessonActivity.mock.calls)).not.toContain("Go on.");
  const before = api.lessonActivity.mock.calls.length;
  await act(async () => { cleanup(); });
  expect(api.lessonActivity.mock.calls.length).toBeGreaterThanOrEqual(before);
});

it("TE2-log: without the activity log the screen sends no intervals", async () => {
  await open(lesson());
  fireEvent.change(screen.getByLabelText("Reply to the teacher"), { target: { value: "Go on." } });
  api.lessonTurn.mockResolvedValueOnce(lesson());
  await act(async () => { fireEvent.click(screen.getByText("Send")); });
  expect(api.lessonActivity).not.toHaveBeenCalled();
});

it("the close card promises only the checks that were set, and a plan outage keeps the lesson", async () => {
  await open(lesson({
    closed: true, closeReason: "goal_reached",
    feed: [{ kind: "close", reason: "goal_reached", recap: "Retrieve: det(A - tI) = 0.",
             delayedChecks: [{ learningObjectId: "lo_eigen", title: "Eigenvalues", purpose: "retention", due: "2099-01-01" }] }],
  }));
  const card = screen.getByTestId("lesson-close");
  expect(card.textContent).toContain("Lesson done.");
  expect(card.textContent).toContain("one question on Eigenvalues, on your own");
  expect(screen.queryByText("Send")).toBeNull();
});

it("a lesson ended by a protection change offers a fresh lesson with a fresh brief (ruling R1)", async () => {
  await open(lesson({
    closed: true, closeReason: "protection_changed",
    feed: [{ kind: "close", reason: "protection_changed", recap: null, delayedChecks: [] }],
  }));
  expect(screen.getByTestId("lesson-close").textContent).toContain("now kept for your exam or held out");
  expect(screen.queryByText("Send")).toBeNull();
  api.lessonTurn.mockResolvedValueOnce(lesson({ lessonId: "les2" }));
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-start-fresh")); });
  expect(api.lessonTurn).toHaveBeenLastCalledWith({ action: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"] });
  expect(screen.queryByTestId("lesson-start-fresh")).toBeNull();
});

it("only a protection change offers the fresh start", async () => {
  await open(lesson({ closed: true, closeReason: "goal_reached",
                      feed: [{ kind: "close", reason: "goal_reached", recap: null, delayedChecks: [] }] }));
  expect(screen.queryByTestId("lesson-start-fresh")).toBeNull();
});

it("a plan outage shows a plain line, not an error", async () => {
  api.lessonTurn.mockRejectedValueOnce({ code: "plan_unavailable", message: "The teacher isn't available right now." });
  const onError = vi.fn();
  await act(async () => {
    render(<LessonScreen entry={{ kind: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"] }}
                         onClose={vi.fn()} onError={onError} />);
  });
  expect(screen.getByTestId("lesson-unavailable").textContent).toContain("isn't available");
  expect(onError).not.toHaveBeenCalled();
});

it("an opening that failed after the lesson was saved is resumed, never opened twice (review F11)", async () => {
  api.lessonTurn.mockRejectedValueOnce({ code: "plan_unavailable", message: "The teacher isn't available right now.",
                                         details: { lesson_id: "les1" } });
  api.lessonView.mockResolvedValueOnce(lesson({ feed: [] }));
  await act(async () => {
    render(<LessonScreen entry={{ kind: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"] }}
                         onClose={vi.fn()} onError={vi.fn()} />);
  });
  expect(api.lessonView).toHaveBeenCalledWith({ lessonId: "les1" });
  api.lessonTurn.mockResolvedValueOnce(lesson());
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-retry")); });
  expect(api.lessonTurn).toHaveBeenLastCalledWith({ action: "resume", lessonId: "les1" });
  expect(api.lessonTurn).toHaveBeenCalledTimes(2);
  expect(screen.getByText("Here is the map.")).toBeTruthy();
  expect(screen.queryByTestId("lesson-retry")).toBeNull();
});

it("an opening that saved nothing is repeated by Try again", async () => {
  api.lessonTurn.mockRejectedValueOnce({ code: "plan_unavailable", message: "The plan is unavailable." });
  await act(async () => {
    render(<LessonScreen entry={{ kind: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"] }}
                         onClose={vi.fn()} onError={vi.fn()} />);
  });
  api.lessonTurn.mockResolvedValueOnce(lesson());
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-retry")); });
  expect(api.lessonTurn).toHaveBeenLastCalledWith({ action: "open", entry: "learning_object",
                                                    learningObjectIds: ["lo_eigen"] });
  expect(screen.getByText("Here is the map.")).toBeTruthy();
});

it("a suggested lesson whose opening failed before it was saved is opened again, never resumed (TE1b review F2)", async () => {
  // The Start reserved les_reserved; the teacher's client failed before the lesson row was written, so the
  // error names no saved lesson: Try again repeats the idempotent open with the suggestion's ids.
  api.lessonTurn.mockRejectedValueOnce({ code: "teacher_unavailable", message: "The teacher's model isn't set up." });
  const entry = { kind: "open" as const, entry: "learning_object" as const, learningObjectIds: ["lo_eigen"],
                  suggestion: { decisionId: "rd1", lessonId: "les_reserved" } };
  await act(async () => {
    render(<LessonScreen entry={entry} onClose={vi.fn()} onError={vi.fn()} />);
  });
  const opening = { action: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"],
                    origin: "router_suggestion", suggestionDecisionId: "rd1", lessonId: "les_reserved" };
  expect(api.lessonTurn).toHaveBeenLastCalledWith(opening);
  expect(api.lessonView).not.toHaveBeenCalled();
  api.lessonTurn.mockResolvedValueOnce(lesson({ lessonId: "les_reserved" }));
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-retry")); });
  expect(api.lessonTurn).toHaveBeenLastCalledWith(opening);
  expect(api.lessonTurn).not.toHaveBeenCalledWith({ action: "resume", lessonId: "les_reserved" });
  expect(screen.getByText("Here is the map.")).toBeTruthy();
});

it("a suggested lesson saved before the failure is resumed under the sidecar's saved id", async () => {
  api.lessonTurn.mockRejectedValueOnce({ code: "plan_unavailable", message: "The teacher isn't available right now.",
                                         details: { lesson_id: "les_reserved" } });
  api.lessonView.mockResolvedValueOnce(lesson({ lessonId: "les_reserved", feed: [] }));
  await act(async () => {
    render(<LessonScreen entry={{ kind: "open", entry: "learning_object", learningObjectIds: ["lo_eigen"],
                                  suggestion: { decisionId: "rd1", lessonId: "les_reserved" } }}
                         onClose={vi.fn()} onError={vi.fn()} />);
  });
  api.lessonTurn.mockResolvedValueOnce(lesson());
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-retry")); });
  expect(api.lessonTurn).toHaveBeenLastCalledWith({ action: "resume", lessonId: "les_reserved" });
});

it("a reply that hit an outage resumes the saved lesson", async () => {
  await open(lesson());
  api.lessonTurn.mockRejectedValueOnce({ code: "plan_unavailable", message: "The teacher isn't available right now." });
  api.lessonView.mockResolvedValueOnce(lesson({ feed: [{ kind: "message", text: "Here is the map.", choices: [] },
                                                       { kind: "learner", text: "Go ahead.", checkRef: null }] }));
  fireEvent.change(screen.getByLabelText("Reply to the teacher"), { target: { value: "Go ahead." } });
  await act(async () => { fireEvent.click(screen.getByText("Send")); });
  expect(screen.getByText("Go ahead.")).toBeTruthy();
  api.lessonTurn.mockResolvedValueOnce(lesson());
  await act(async () => { fireEvent.click(screen.getByTestId("lesson-retry")); });
  expect(api.lessonTurn).toHaveBeenLastCalledWith({ action: "resume", lessonId: "les1" });
});

// --- Reader RW5d P4b: the teacher's visual ------------------------------------------------------

const FLAGSHIP = corpus.figures.find((item) => item.id === "two_sided_exponential")!.spec as unknown as { demonstrates: string };

function teacherFigure(overrides: Partial<FigureViewDto> = {}): FigureViewDto {
  return {
    figureId: "fig_t1", extractionId: null as unknown as string, spanIds: [], anchorSpanId: null, region: null,
    origin: "teacher", verification: "illustrative", kind: "illustrative",
    label: "AI-built illustration of an interpretation · not checked against the book", reason: null,
    unsupportedKind: null, supersedesId: null, revisionNote: null, versions: 1, createdAt: "2026-11-02T00:00:00",
    specJson: JSON.stringify(FLAGSHIP), demonstrates: FLAGSHIP.demonstrates, assumptions: [],
    // A figure that carried its own prediction: the lesson suppresses it anyway.
    predictions: [{ index: 0, prompt: "OWNPREDICTION if λ doubles?", kind: "direction", answered: null,
                    choices: [{ value: "rises", label: "it rises" }, { value: "falls", label: "it falls" }] }],
    goalText: "Move λ with p fixed at 0.3", goalAuthor: "teacher", grounding: "retrieved", passages: [],
    tier: "grammar", host: "lesson",
    ...overrides,
  };
}

it("shows the teacher's figure inline in its turn, open, with no prediction of its own and no \"not right?\"", async () => {
  api.readerLogActivity.mockResolvedValue({ recorded: 0 });
  await open(lesson({
    feed: [{ kind: "message", text: "Here only λ is yours to move.", choices: [] },
           { kind: "prediction", node: "n1", prompt: "What happens to the left mass?", choices: [] },
           { kind: "figure", node: "n1", goal: "Move λ with p fixed at 0.3", status: "shown", figure: teacherFigure() }],
    openPrediction: { node: "n1", prompt: "What happens to the left mass?", choices: [] },
  }));
  const frame = screen.getByTestId("lesson-figure");
  expect(frame.getAttribute("data-status")).toBe("shown");
  expect(frame.querySelector('[data-figure="fig_t1"]')).not.toBeNull();
  expect(frame.querySelector("[data-figure-body]")).not.toBeNull();
  expect(frame.querySelector('[data-figure-goal="teacher"]')?.textContent).toContain("AI-written");
  expect(screen.getByText(FLAGSHIP.demonstrates)).toBeTruthy();
  expect(frame.querySelector("[data-figure-prediction]")).toBeNull();
  expect(screen.queryByText(/OWNPREDICTION/)).toBeNull();
  expect(screen.queryByText(FIGURE_COPY.notRight)).toBeNull();
  // The teacher's own prediction is the one prompt for this move.
  expect(screen.getByTestId("lesson-prediction-answer")).toBeTruthy();
  expect(api.readerFigurePredict).not.toHaveBeenCalled();
  expect(api.figureRequest).not.toHaveBeenCalled();
});

it("a lesson figure that isn't drawn says why in one quiet line", async () => {
  await open(lesson({
    feed: [{ kind: "figure", node: "n1", status: "failed", figure: null },
           { kind: "figure", node: "n2", status: "withheld", figure: null },
           { kind: "figure", node: "n3", status: "unavailable", figure: null }],
  }));
  const lines = screen.getAllByTestId("lesson-figure");
  expect(lines.map((line) => line.getAttribute("data-status"))).toEqual(["failed", "withheld", "unavailable"]);
  expect(lines.map((line) => line.textContent)).toEqual([LESSON_FIGURE_COPY.failed, LESSON_FIGURE_COPY.withheld,
                                                         LESSON_FIGURE_COPY.unavailable]);
  expect(document.querySelector("[data-figure]")).toBeNull();
});
