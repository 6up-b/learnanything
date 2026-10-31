// Curriculum C0b: the Guide's slice of a deliverable's path (spec §7.5), its overrides
// (§7.3) and "Am I ready?" (§8.5); with no deliverable or the switch off, RW7a's card.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { DeliverableLineDto, DeliverableReadyDto, DeliverableScopeDto, DeliverableSliceDto } from "../../api/dto";
import { GuidePathSlot } from "./DeliverableSliceCard";
import { DELIVERABLE_COPY, offeredChoices, shouldPollSlice, sliceHeading, sliceShown } from "./deliverableSlice";
import { SCOPE_COPY, scopeNotice, scopeSummary } from "./DeliverableScope";

const { api } = vi.hoisted(() => ({ api: {
  curriculumGuideSlice: vi.fn(), curriculumSetDepth: vi.fn(), curriculumPathOverride: vi.fn(),
  curriculumSetScope: vi.fn(), curriculumReadyCheck: vi.fn(), curriculumDeliverables: vi.fn(),
  curriculumCreateDeliverable: vi.fn(), curriculumScope: vi.fn(), curriculumScopeDecide: vi.fn(),
} }));
vi.mock("../../api/client", () => ({ api }));

const DEPTHS = [
  { id: "get_the_idea" as const, label: "get the idea", means: "definitions, examples, visualizations" },
  { id: "learn_to_use_it" as const, label: "learn to use it", means: "explanations, worked examples, practice" },
  { id: "fluency" as const, label: "fluency", means: "novel problems, changed assumptions, delayed checks" },
];

function section(over: Partial<DeliverableLineDto["section"]> = {}): DeliverableLineDto["section"] {
  return { extractionId: "ext_book", sectionId: "ch5", title: "5.1 Eigenvalues", book: "Axler", sourceId: "src_axler",
    startSpanId: "s10", minutes: 6, treatment: "develops", treatmentWords: "develops it", read: false, ...over };
}

function line(over: Partial<DeliverableLineDto> = {}): DeliverableLineDto {
  return {
    learningObjectId: "lo_eigen", title: "Eigenvalues", phrase: "eigenvalues", kind: "needed", label: "core", chip: "core",
    effectiveLabel: "core", reason: "proves it the way your exam asks", reasonBy: "model", override: null,
    section: section(), alternates: [section({ extractionId: "ext_strang", sectionId: "s61", title: "6.1 Eigenvectors",
      book: "Strang", difference: "more geometric" })], exercise: null, check: null, ordinal: 0, ...over,
  };
}

function slice(over: Partial<DeliverableSliceDto> = {}): DeliverableSliceDto {
  return {
    extractionId: "ext_book", status: "ready", goal: { id: "goal_d", title: "my midterm", kind: "exam", dueAt: "2026-11-12T23:59:59Z" },
    depth: "learn_to_use_it", depthLabel: "learn to use it", depths: DEPTHS, lines: [line()],
    elsewhere: [{ learningObjectId: "lo_det", title: "determinants", label: "core",
      section: section({ extractionId: "ext_strang", sectionId: "s52", title: "5.2 Determinants", book: "Strang" }) }],
    notNeeded: [{ sectionId: "ch9", title: "9 Jordan form", startSpanId: "s90" }], notNeededLabel: "not needed for my midterm",
    uncovered: [{ learningObjectId: "lo_svd", title: "SVD", phrase: "svd" }], message: null, reason: null, covering: false,
    ...over,
  };
}

const READY: DeliverableReadyDto = {
  goalId: "goal_d", title: "my midterm", dueAt: "2026-11-12T23:59:59Z", checksOwed: [],
  summary: "0 of 1 shown on your own",
  lines: [{ learningObjectId: "lo_eigen", title: "Eigenvalues", phrase: "eigenvalues", state: "untested",
    line: "Not tested on your own yet.", checks: [{ commitmentId: "cm_1", dueHint: "2026-11-03" }] }],
};

const SCOPE: DeliverableScopeDto = {
  goalId: "goal_d", title: "my midterm", sentence: "only my midterm", kind: "exam", dueAt: "2026-11-12T23:59:59Z",
  depth: null, topics: [{ learningObjectId: "lo_eigen", title: "Eigenvalues", phrase: "eigenvalues" }],
  unmatched: [{ phrase: "jordan form", proposedTitle: "Jordan form", proposedStatement: "What Jordan form means.",
    status: "open", createdLearningObjectId: null }],
  inputs: [], resolution: { id: "dsr_1", origin: "resolver", model: "fake", createdAt: "2026-10-31T09:00:00Z", facetScope: {} },
  subjectId: "linear-algebra", subjects: [{ subjectId: "linear-algebra", title: "Linear algebra" }],
};

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.curriculumDeliverables.mockResolvedValue({ deliverables: [] });
});
afterEach(() => { cleanup(); vi.useRealTimers(); });

async function mount(props: { readingPathCard?: React.ReactNode | null } = {}) {
  const handlers = { onJump: vi.fn(), onError: vi.fn() };
  const card = props.readingPathCard === undefined ? <div data-testid="rw7a">RW7a card</div> : props.readingPathCard;
  const utils = render(<GuidePathSlot extractionId="ext_book" readingPathCard={card} {...handlers} />);
  await act(async () => { await Promise.resolve(); await Promise.resolve(); });
  return { ...utils, ...handlers };
}

it("with no deliverable here, RW7a's card and the way to make one; with the switch off, RW7a's card exactly", async () => {
  api.curriculumGuideSlice.mockResolvedValueOnce({ extractionId: "ext_book", status: "none" });
  const none = await mount();
  expect(screen.getByTestId("rw7a")).toBeTruthy();
  expect(none.container.querySelector("[data-deliverable-slice]")).toBeNull();
  expect(none.container.querySelector("[data-deliverable-entry]")).not.toBeNull();
  none.unmount();
  api.curriculumGuideSlice.mockRejectedValueOnce({ code: "curriculum_disabled", message: "off" });
  const off = await mount();
  expect(screen.getByTestId("rw7a")).toBeTruthy();
  expect(off.container.querySelector("[data-deliverable-entry]")).toBeNull();
  expect(off.onError).not.toHaveBeenCalled();
});

it("makes a deliverable from the learner's words and a topic list, then shows what they resolved to (F4)", async () => {
  api.curriculumGuideSlice.mockResolvedValue({ extractionId: "ext_book", status: "none" });
  api.curriculumCreateDeliverable.mockResolvedValue({ goalId: "goal_d", status: "ready", message: null, scope: SCOPE });
  api.curriculumSetScope.mockResolvedValue({ status: "ready", message: null, scope: SCOPE });
  const { container } = await mount();
  fireEvent.click(screen.getByText(SCOPE_COPY.entry));
  fireEvent.change(screen.getByLabelText(SCOPE_COPY.sentence), { target: { value: "only my midterm" } });
  fireEvent.change(screen.getByLabelText(SCOPE_COPY.topics), { target: { value: "eigenvalues\njordan form" } });
  fireEvent.change(screen.getByLabelText(SCOPE_COPY.deadline), { target: { value: "2026-11-12" } });
  fireEvent.click(screen.getByLabelText(SCOPE_COPY.exam));
  await act(async () => { fireEvent.click(screen.getByText(SCOPE_COPY.make)); await Promise.resolve(); });
  expect(api.curriculumCreateDeliverable).toHaveBeenCalledWith({ sentence: "only my midterm", dueAt: "2026-11-12", exam: true });
  expect(api.curriculumSetScope).toHaveBeenCalledWith({ goalId: "goal_d", kind: "topic_list", text: "eigenvalues\njordan form" });
  expect(screen.getByText(scopeSummary(SCOPE))).toBeTruthy();
  expect(container.querySelector('[data-deliverable-topic="lo_eigen"]')?.textContent).toContain("“eigenvalues”");
  expect(container.querySelector('[data-deliverable-unmatched="open"]')).not.toBeNull();
});

it("a phrase not in the library is added only on the learner's yes, and not this / add are their words (F4)", async () => {
  api.curriculumGuideSlice.mockResolvedValue({ extractionId: "ext_book", status: "none" });
  api.curriculumDeliverables.mockResolvedValue({ deliverables: [SCOPE] });
  const decided = { ...SCOPE, unmatched: [{ ...SCOPE.unmatched[0], status: "created" as const, createdLearningObjectId: "lo_jordan" }] };
  api.curriculumScopeDecide.mockResolvedValue({ created: { learningObjectId: "lo_jordan" }, scope: decided });
  api.curriculumSetScope.mockResolvedValue({ status: "superseded", message: "Your newer words stand.", scope: decided });
  await mount();
  await act(async () => { fireEvent.click(screen.getByText(SCOPE_COPY.yours(1))); });
  await act(async () => { fireEvent.click(screen.getByText(SCOPE_COPY.addIt)); await Promise.resolve(); });
  expect(api.curriculumScopeDecide).toHaveBeenCalledWith({ goalId: "goal_d", phrase: "jordan form", decision: "create" });
  expect(screen.getByText(SCOPE_COPY.added)).toBeTruthy();
  fireEvent.change(screen.getByLabelText(SCOPE_COPY.notThis), { target: { value: "not proofs" } });
  await act(async () => { fireEvent.click(screen.getAllByText(SCOPE_COPY.send)[0]); await Promise.resolve(); });
  expect(api.curriculumSetScope).toHaveBeenCalledWith({ goalId: "goal_d", kind: "correction", text: "not proofs" });
  expect(screen.getByText("Your newer words stand.")).toBeTruthy();
});

it("the slice opens its scope for review, and a change there asks for the judgment it owes (F4, F9)", async () => {
  api.curriculumGuideSlice.mockResolvedValue(slice());
  api.curriculumScope.mockResolvedValue(SCOPE);
  api.curriculumSetScope.mockResolvedValue({ status: "ready", message: null, scope: SCOPE });
  await mount();
  await act(async () => { fireEvent.click(screen.getByText(new RegExp(DELIVERABLE_COPY.scope))); await Promise.resolve(); });
  expect(api.curriculumScope).toHaveBeenCalledWith({ goalId: "goal_d" });
  fireEvent.change(screen.getByLabelText(SCOPE_COPY.add), { target: { value: "determinants too" } });
  await act(async () => { fireEvent.click(screen.getAllByText(SCOPE_COPY.send)[1]); await Promise.resolve(); });
  expect(api.curriculumSetScope).toHaveBeenCalledWith({ goalId: "goal_d", kind: "text", text: "determinants too" });
  expect(api.curriculumGuideSlice).toHaveBeenLastCalledWith({ extractionId: "ext_book", judge: true });
});

it("add it asks which subject when it cannot be inferred, and sends the learner's choice (re-review F16)", async () => {
  const ambiguous: DeliverableScopeDto = { ...SCOPE, topics: [], subjectId: null,
    subjects: [{ subjectId: "linear-algebra", title: "Linear algebra" }, { subjectId: "statistics", title: "Statistics" }] };
  api.curriculumGuideSlice.mockResolvedValue({ extractionId: "ext_book", status: "none" });
  api.curriculumDeliverables.mockResolvedValue({ deliverables: [ambiguous] });
  const decided = { ...ambiguous, unmatched: [{ ...ambiguous.unmatched[0], status: "created" as const, createdLearningObjectId: "lo_j" }] };
  api.curriculumScopeDecide.mockResolvedValue({ created: { learningObjectId: "lo_j" }, scope: decided });
  await mount();
  await act(async () => { fireEvent.click(screen.getByText(SCOPE_COPY.yours(1))); });
  const addIt = screen.getByText(SCOPE_COPY.addIt) as HTMLButtonElement;
  expect(addIt.disabled).toBe(true);
  fireEvent.change(screen.getByLabelText(SCOPE_COPY.subject), { target: { value: "statistics" } });
  expect(addIt.disabled).toBe(false);
  await act(async () => { fireEvent.click(addIt); await Promise.resolve(); });
  expect(api.curriculumScopeDecide).toHaveBeenCalledWith(
    { goalId: "goal_d", phrase: "jordan form", decision: "create", subjectId: "statistics" });
  expect(screen.getByText(SCOPE_COPY.added)).toBeTruthy();
});

it("a no_subject refusal opens the subject choice instead of a dead end (re-review F16)", async () => {
  const two: DeliverableScopeDto = { ...SCOPE,
    subjects: [{ subjectId: "linear-algebra", title: "Linear algebra" }, { subjectId: "statistics", title: "Statistics" }] };
  api.curriculumGuideSlice.mockResolvedValue({ extractionId: "ext_book", status: "none" });
  api.curriculumDeliverables.mockResolvedValue({ deliverables: [two] });
  api.curriculumScopeDecide.mockRejectedValueOnce({ code: "no_subject", message: "Choose the subject this new topic belongs to." });
  const { onError } = await mount();
  await act(async () => { fireEvent.click(screen.getByText(SCOPE_COPY.yours(1))); });
  expect(screen.queryByLabelText(SCOPE_COPY.subject)).toBeNull();
  await act(async () => { fireEvent.click(screen.getByText(SCOPE_COPY.addIt)); await Promise.resolve(); });
  expect(screen.getByLabelText(SCOPE_COPY.subject)).toBeTruthy();
  expect(onError).not.toHaveBeenCalled();
});

it("a correction that makes the Guide pick another deliverable closes the previous one's scope (re-review F17)", async () => {
  const other = slice({ goal: { id: "goal_b", title: "my final", kind: "exam", dueAt: null } });
  api.curriculumGuideSlice.mockResolvedValueOnce(slice()).mockResolvedValue(other);
  api.curriculumScope.mockResolvedValue(SCOPE);
  api.curriculumSetScope.mockResolvedValue({ status: "ready", message: null, scope: SCOPE });
  const { container } = await mount();
  await act(async () => { fireEvent.click(screen.getByText(new RegExp(DELIVERABLE_COPY.scope))); await Promise.resolve(); });
  expect(container.querySelector('[data-deliverable-scope="goal_d"]')).not.toBeNull();
  fireEvent.change(screen.getByLabelText(SCOPE_COPY.notThis), { target: { value: "not this book; my final" } });
  await act(async () => {
    fireEvent.click(screen.getAllByText(SCOPE_COPY.send)[0]);
    for (let i = 0; i < 6; i += 1) await Promise.resolve();
  });
  expect(api.curriculumGuideSlice).toHaveBeenLastCalledWith({ extractionId: "ext_book", judge: true });
  expect(screen.getByText(sliceHeading(other))).toBeTruthy();
  // The panel that edited goal_d is gone: nothing on screen can send goal_d's edits now.
  expect(container.querySelector('[data-deliverable-scope="goal_d"]')).toBeNull();
});

it("use this one instead is offered only on a section that introduces or develops the topic (F10)", async () => {
  api.curriculumGuideSlice.mockResolvedValue(slice({ lines: [line({ alternates: [
    section({ extractionId: "ext_strang", sectionId: "s61", title: "6.1 Eigenvectors", book: "Strang", canUseInstead: false,
      treatment: "mentions" })] })] }));
  await mount();
  fireEvent.click(screen.getByText(/why/));
  expect(screen.getByText(/another way: Strang §6.1 Eigenvectors/)).toBeTruthy();
  expect(screen.queryByText(DELIVERABLE_COPY.useInstead)).toBeNull();
});

it("shows this book's lines, other books' lines, what isn't covered and what isn't needed", async () => {
  api.curriculumGuideSlice.mockResolvedValue(slice());
  const { container, onJump } = await mount();
  expect(screen.queryByTestId("rw7a")).toBeNull();
  expect(screen.getByText("for my midterm · learn to use it")).toBeTruthy();
  expect(container.querySelector('[data-deliverable-line="lo_eigen"]')).not.toBeNull();
  expect(screen.getByText(DELIVERABLE_COPY.onPathIn("determinants", "Strang", "§5.2 Determinants"))).toBeTruthy();
  expect(container.querySelector("[data-deliverable-uncovered]")?.textContent).toContain("SVD");
  fireEvent.click(screen.getByText(/1 section not needed here/));
  expect(screen.getByText("not needed for my midterm")).toBeTruthy();
  fireEvent.click(screen.getByText("§5.1 Eigenvalues"));
  expect(onJump).toHaveBeenCalledWith("s10");
});

it("this book alone shows RW7a's card, and back returns to the deliverable", async () => {
  api.curriculumGuideSlice.mockResolvedValue(slice());
  await mount();
  fireEvent.click(screen.getByText(DELIVERABLE_COPY.thisBookAlone));
  expect(screen.getByTestId("rw7a")).toBeTruthy();
  fireEvent.click(screen.getByText(DELIVERABLE_COPY.backToDeliverable));
  expect(screen.queryByTestId("rw7a")).toBeNull();
});

it("without RW7a's card there is no 'this book alone'", async () => {
  api.curriculumGuideSlice.mockResolvedValue(slice());
  await mount({ readingPathCard: null });
  expect(screen.queryByText(DELIVERABLE_COPY.thisBookAlone)).toBeNull();
});

it("overrides: use this one instead names the alternate; skip and check me later are offered", async () => {
  api.curriculumGuideSlice.mockResolvedValue(slice());
  api.curriculumPathOverride.mockResolvedValue({});
  await mount();
  fireEvent.click(screen.getByText(/why/));
  expect(screen.getByText(/another way: Strang §6.1 Eigenvectors, more geometric/)).toBeTruthy();
  expect(screen.getByText(DELIVERABLE_COPY.modelsReading)).toBeTruthy();
  await act(async () => { fireEvent.click(screen.getByText(DELIVERABLE_COPY.useInstead)); });
  expect(api.curriculumPathOverride).toHaveBeenCalledWith({ goalId: "goal_d", learningObjectId: "lo_eigen",
    choice: "use_instead", sectionRef: "ext_strang/s61" });
  await act(async () => { fireEvent.click(screen.getByText(DELIVERABLE_COPY.checkLater)); });
  expect(api.curriculumPathOverride).toHaveBeenLastCalledWith({ goalId: "goal_d", learningObjectId: "lo_eigen", choice: "check_later" });
  expect(api.curriculumGuideSlice).toHaveBeenLastCalledWith({ extractionId: "ext_book", judge: false });
});

it("a waiting check shows as off the path, with undo", async () => {
  api.curriculumGuideSlice.mockResolvedValue(slice({ lines: [line({ override: "check_later", effectiveLabel: "check_pending",
    check: { commitmentId: "cm_1", state: "one_check_pending" } })] }));
  api.curriculumPathOverride.mockResolvedValue({});
  await mount();
  fireEvent.click(screen.getByText(/why/));
  expect(screen.getByText(DELIVERABLE_COPY.checkWaiting)).toBeTruthy();
  await act(async () => { fireEvent.click(screen.getByText(DELIVERABLE_COPY.undo)); });
  expect(api.curriculumPathOverride).toHaveBeenCalledWith({ goalId: "goal_d", learningObjectId: "lo_eigen", choice: "none" });
});

it("not what I need goes to the scope resolver as the learner's words", async () => {
  api.curriculumGuideSlice.mockResolvedValue(slice());
  api.curriculumSetScope.mockResolvedValue({ status: "ready", message: null, scope: {} });
  await mount();
  fireEvent.click(screen.getByText(/why/));
  fireEvent.change(screen.getByLabelText(DELIVERABLE_COPY.notWhatINeed), { target: { value: "we skipped proofs" } });
  await act(async () => { fireEvent.click(screen.getByText(DELIVERABLE_COPY.send)); });
  expect(api.curriculumSetScope).toHaveBeenCalledWith({ goalId: "goal_d", kind: "correction", text: "we skipped proofs",
    context: { via: "path_line", learning_object_id: "lo_eigen" } });
  // A scope change reads the slice with judge on (F9): the topic it adds is placed.
  expect(api.curriculumGuideSlice).toHaveBeenLastCalledWith({ extractionId: "ext_book", judge: true });
});

it("not what I need: an unavailable resolution says so, and new phrases open the scope (F9)", async () => {
  api.curriculumGuideSlice.mockResolvedValue(slice());
  api.curriculumSetScope.mockResolvedValue({ status: "unavailable", message: "Couldn't reach LearnLoop's model.", scope: SCOPE });
  const { container } = await mount();
  fireEvent.click(screen.getByText(/why/));
  fireEvent.change(screen.getByLabelText(DELIVERABLE_COPY.notWhatINeed), { target: { value: "and jordan form" } });
  await act(async () => { fireEvent.click(screen.getByText(DELIVERABLE_COPY.send)); await Promise.resolve(); });
  expect(screen.getByText("Couldn't reach LearnLoop's model.")).toBeTruthy();
  expect(container.querySelector('[data-deliverable-unmatched="open"]')).not.toBeNull();
  expect(scopeNotice({ status: "fresh", message: "x" })).toBeNull();
});

it("asks the depth once and saves it", async () => {
  api.curriculumGuideSlice.mockResolvedValue(slice({ status: "ask_depth", depth: null, depthLabel: null, lines: [] }));
  api.curriculumSetDepth.mockResolvedValue({});
  await mount();
  expect(screen.getByText(DELIVERABLE_COPY.ask)).toBeTruthy();
  await act(async () => { fireEvent.click(screen.getByText("fluency")); });
  expect(api.curriculumSetDepth).toHaveBeenCalledWith({ goalId: "goal_d", depth: "fluency" });
});

it("Am I ready? adds the checks and shows each topic's line, never what was read", async () => {
  api.curriculumGuideSlice.mockResolvedValue(slice());
  api.curriculumReadyCheck.mockResolvedValue({ created: [], readiness: READY });
  const { container } = await mount();
  await act(async () => { fireEvent.click(screen.getByText(DELIVERABLE_COPY.ready)); });
  expect(api.curriculumReadyCheck).toHaveBeenCalledWith({ goalId: "goal_d" });
  expect(container.querySelector('[data-deliverable-ready-line="untested"]')?.textContent).toContain("check on 2026-11-03");
  expect(screen.getByText(DELIVERABLE_COPY.readyNote)).toBeTruthy();
});

it("polls while a judgment or coverage runs, and a failure offers try again", async () => {
  vi.useFakeTimers();
  api.curriculumGuideSlice.mockResolvedValueOnce(slice({ status: "judging", lines: [], covering: true }))
    .mockResolvedValueOnce(slice({ status: "failed", lines: [], message: "Couldn't choose a path.", reason: "failed" }))
    .mockResolvedValue(slice());
  render(<GuidePathSlot extractionId="ext_book" readingPathCard={null} onJump={vi.fn()} onError={vi.fn()} />);
  await act(async () => { await Promise.resolve(); await Promise.resolve(); });
  expect(screen.getByText(DELIVERABLE_COPY.covering)).toBeTruthy();
  await act(async () => { vi.advanceTimersByTime(1600); await Promise.resolve(); await Promise.resolve(); });
  await act(async () => { fireEvent.click(screen.getByText(DELIVERABLE_COPY.tryAgain)); await Promise.resolve(); });
  expect(api.curriculumGuideSlice).toHaveBeenLastCalledWith({ extractionId: "ext_book", retry: true });
});

it("the helpers word the choices and decide when to read again", () => {
  expect(sliceShown(null)).toBe(false);
  expect(sliceShown({ extractionId: "x", status: "none" })).toBe(false);
  expect(shouldPollSlice(slice({ status: "pending" }))).toBe(true);
  expect(shouldPollSlice(slice())).toBe(false);
  expect(sliceHeading(slice())).toBe("for my midterm · learn to use it");
  expect(offeredChoices(line())).toEqual(["skip", "check_later"]);
  expect(offeredChoices(line({ effectiveLabel: "already_shown", label: "already_shown" }))).toEqual(["read_anyway"]);
  expect(offeredChoices(line({ override: "skip", effectiveLabel: "skipped" }))).toEqual([]);
});
