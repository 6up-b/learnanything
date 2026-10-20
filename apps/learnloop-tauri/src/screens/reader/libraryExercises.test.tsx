// RW4b in RW4a's "practice this question" (spec §7.4; UX §4.5, §4.6; G34).
//
// * Switched off (no `libraryExercises` in the prompt contract, so no
//   `exercises` prop), the practice block renders exactly as on fab576ac1:
//   the snapshots in __snapshots__/libraryExercises.test.tsx.snap were written
//   with the base commit's LibraryAnswer.tsx in place, and no RW4b call is made
//   (the api mock names none; a call would throw).
// * On: the proposal's textbook exercises show beside the items as candidate
//   cards (verbatim statement, source and page, the honest line, "open in the
//   book", "use this one"), only those the server let through; an exposed one
//   says why and that it is practice, never a check on your own; the shown
//   ones are recorded as impressions; a failed check shows none of them.
// * Nothing fits: "Nothing in practice fits yet · find an exercise in my
//   sources ▸" while the fallback is on, which searches only when pressed.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ExerciseCandidatesDto, FindExercisesDto, FindPracticeResultDto, LibraryAskDto } from "../../api/dto";
import { LibraryAnswer } from "./LibraryAnswer";
import type { LibraryAskController, LibraryAskState } from "./useLibraryAsk";

const { api } = vi.hoisted(() => ({
  api: { readerExerciseCandidates: vi.fn(), readerFindExercises: vi.fn(), recordProposalImpressions: vi.fn(),
    readerLibraryJob: vi.fn(), readerLibraryJobCancel: vi.fn() },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

const ASK: LibraryAskDto = {
  askId: "la_1", query: "solve for the eigenvalue", entry: "reader", status: "ok", policy: "reading", personalized: true,
  basis: "keyword", learningObjectIds: ["lo_matrices"], extractionId: "ext_open", anchorSpanIds: [],
  hits: [{ key: "ext_text:t2", extractionId: "ext_text", spanId: "t2", sourceId: "src_text", sourceTitle: "Matrix Theory", section: "Chapter 5",
    page: 7, text: "Eigenvalues are the roots of the characteristic polynomial.", role: "definition", group: "Foundation", expansion: null,
    learningObjectIds: [], authorship: "source", label: "source-authored" }],
  groups: { sources: [{ sourceId: "src_text", sourceTitle: "Matrix Theory", groups: [{ group: "Foundation", keys: ["ext_text:t2"] }] }], expansions: [] },
  expansions: [], expandGraph: false, sourceCount: 1, passageCount: 1,
} as unknown as LibraryAskDto;

const ITEM = { rank: 1, practiceItemId: "pi_1", learningObjectId: "lo_matrices", learningObjectTitle: "Matrices", practiceMode: "short_answer",
  prompt: "Find the eigenvalues of [[2,0],[0,3]].", facetIds: [], rationale: null };

function exercise(key: string, span: string, statement: string) {
  return { kind: "source_exercise" as const, key, extractionId: "ext_text", spanIds: [span], sourceId: "src_text", revisionId: "rev_text",
    sourceTitle: "Matrix Theory", label: `Exercise ${span}`, page: 9, statement, rationale: null, labelLine: "From Matrix Theory, p. 9 · not yet in your practice" };
}

const EX_A = exercise("srcex:ext_text:t6", "t6", "1. An eigenvalue t satisfies 3t + 5 = 20; solve 3x + 5 = 20 for x.");
const EX_B = exercise("srcex:ext_text:t7", "t7", "2. Solve 2x + 4 = 10 for x, the eigenvalue.");
const EX_HELD = exercise("srcex:ext_text:t8", "t8", "3. HELD-OUT SENTINEL exercise statement.");

function practiceResult(items: unknown[], exercises: unknown[]): FindPracticeResultDto {
  return { version: 1, status: "ok", proposalId: "pp_1", items, sourceExercises: exercises } as FindPracticeResultDto;
}

const fresh = { exposed: false, reasons: [], label: null, note: null, offeredAs: "check_on_your_own" as const, exposureRuleVersion: "reading_exposure_v1" };
const seen = { exposed: true, reasons: ["source_exposed"], label: "you've recently seen this page or its solution", note: null,
  offeredAs: "practice" as const, exposureRuleVersion: "reading_exposure_v1" };

function view(entries: Array<[string, typeof fresh | typeof seen]>): ExerciseCandidatesDto {
  return { version: 1, proposalId: "pp_1", withheld: 1,
    candidates: entries.map(([key, exposure]) => ({ key, extractionId: "ext_text", spanIds: [], sourceId: "src_text", revisionId: "rev_text", exposure })) };
}

const IDLE = { phase: "idle" as const, value: null, failure: null };

/** RW4b's RPCs answer with a library job; here, one already done. */
function done<T>(result: T, kind = "exercise_candidates") {
  return { jobId: `ljob_${kind}`, kind, askId: null, state: "done" as const, result };
}

function ctl(practice: FindPracticeResultDto | null): LibraryAskController {
  const state: LibraryAskState = {
    key: 1, request: { query: ASK.query, entry: "reader", extractionId: "ext_open", spanIds: [] }, personalized: true,
    ask: { phase: "landed", value: ASK, failure: null }, notes: IDLE, pinned: [], compare: IDLE, tutor: IDLE,
    practice: practice ? { phase: "landed", value: practice, failure: null } : IDLE, peek: null,
  };
  const noop = vi.fn();
  return {
    enabled: true, settings: { expandGraph: false, personalizedDefault: true, compare: false }, state, open: true, ask: noop, retry: noop,
    setPersonalized: noop, retryNotes: noop, togglePin: noop, canCompare: false, compare: noop, askTutor: noop, practice: noop, peek: noop,
    closePeek: noop, close: noop, cancelNotes: noop, cancelCompare: noop, cancelTutor: noop,
  } as unknown as LibraryAskController;
}

/** React's generated ids depend on render order; the markup is the contract. */
function markup(container: HTMLElement): string {
  return container.innerHTML.replace(/:r[0-9a-z]+:/g, ":r:").replace(/«r[0-9a-z]+»/g, "«r»");
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.recordProposalImpressions.mockResolvedValue({ recorded: 1 });
});
afterEach(() => cleanup());

// -- switched off: exactly as on fab576ac1 -----------------------------------------------------------

it("switched off, items with textbook exercises in the proposal render exactly as before RW4b", () => {
  const { container } = render(
    <LibraryAnswer ctl={ctl(practiceResult([ITEM], [EX_A, EX_B]))} onOpenHit={null} onPracticePick={vi.fn()} onClose={vi.fn()} />,
  );
  expect(markup(container)).toMatchSnapshot();
  expect(screen.queryByText(/use this one/)).toBeNull();
  expect(screen.queryByText(EX_A.statement)).toBeNull();
});

it("switched off, nothing fitting renders exactly as before RW4b", () => {
  const { container } = render(
    <LibraryAnswer ctl={ctl(practiceResult([], [EX_A]))} onOpenHit={null} onPracticePick={vi.fn()} onClose={vi.fn()} />,
  );
  expect(markup(container)).toMatchSnapshot();
  expect(screen.getByText("Nothing in practice fits yet.")).toBeTruthy();
  expect(screen.queryByText(/find an exercise in my sources/)).toBeNull();
});

// -- on: the candidate cards -------------------------------------------------------------------------

function renderOn(practice: FindPracticeResultDto, options: { fallback?: boolean } = {}) {
  const onUse = vi.fn();
  const onOpenInBook = vi.fn();
  const result = render(
    <LibraryAnswer
      ctl={ctl(practice)}
      onOpenHit={null}
      onPracticePick={vi.fn()}
      onClose={vi.fn()}
      exercises={{ settings: { fallback: options.fallback ?? false }, onUse, onOpenInBook }}
    />,
  );
  return { ...result, onUse, onOpenInBook };
}

it("shows the proposal's exercises the server let through, beside the items, each as an honest card", async () => {
  api.readerExerciseCandidates.mockResolvedValue(done(view([[EX_A.key, fresh], [EX_B.key, seen]])));
  const { onUse, onOpenInBook } = renderOn(practiceResult([ITEM], [EX_A, EX_B, EX_HELD]));
  expect(api.readerExerciseCandidates).toHaveBeenCalledWith({ proposalId: "pp_1", keys: [
    { extractionId: "ext_text", spanIds: ["t6"] }, { extractionId: "ext_text", spanIds: ["t7"] }, { extractionId: "ext_text", spanIds: ["t8"] },
  ] });
  const list = await screen.findByRole("list", { name: "exercises from your books" });
  expect(screen.getByRole("list", { name: "practice for this question" })).toBeTruthy(); // the items, unchanged
  const cards = within(list).getAllByTestId("exercise-candidate");
  expect(cards).toHaveLength(2);
  expect(screen.queryByText(/HELD-OUT SENTINEL/)).toBeNull(); // the server left it out
  // The exercise's own words, in the book's voice, with source and page.
  expect(within(cards[0]).getByText(EX_A.statement).closest("[data-voice]")?.getAttribute("data-voice")).toBe("source");
  expect(cards[0].textContent).toContain("Matrix Theory · p. 9 · Exercise t6");
  expect(cards[0].textContent).toContain("from your book · verbatim · answer completed by LearnLoop's model · checked when you use it");
  expect(cards[0].textContent).not.toContain("not a check on your own");
  // The seen one says why, and that it is practice, never a check on your own.
  expect(cards[1].textContent).toContain("you've recently seen this page or its solution · practice beside the book, not a check on your own");
  fireEvent.click(within(cards[1]).getByRole("button", { name: /use this one/ }));
  expect(onUse).toHaveBeenCalledWith(expect.objectContaining({ key: EX_B.key, origin: "proposal", proposalId: "pp_1", exposure: seen }));
  fireEvent.click(within(cards[0]).getByRole("button", { name: /open in the book/ }));
  expect(onOpenInBook).toHaveBeenCalledWith(expect.objectContaining({ key: EX_A.key, spanIds: ["t6"] }));
  // Displayed is not unseen: the shown exercises are the proposal's impressions.
  await waitFor(() => expect(api.recordProposalImpressions).toHaveBeenCalledWith({ proposalId: "pp_1", surface: "reader", keys: [
    { kind: "source_exercise", extractionId: "ext_text", spanIds: ["t6"] }, { kind: "source_exercise", extractionId: "ext_text", spanIds: ["t7"] },
  ] }));
});

it("a check that fails shows no exercise (fail closed) and keeps the items", async () => {
  api.readerExerciseCandidates.mockRejectedValue({ code: "internal_error", message: "boom" });
  renderOn(practiceResult([ITEM], [EX_A]));
  expect(await screen.findByText("Couldn't load the exercises from your books.")).toBeTruthy();
  expect(screen.queryByText(EX_A.statement)).toBeNull();
  expect(screen.getByRole("list", { name: "practice for this question" })).toBeTruthy();
  expect(api.recordProposalImpressions).not.toHaveBeenCalled();
});

it("exercises alone are not 'nothing fits'", async () => {
  api.readerExerciseCandidates.mockResolvedValue(done(view([[EX_A.key, fresh]])));
  renderOn(practiceResult([], [EX_A]), { fallback: true });
  await screen.findByRole("list", { name: "exercises from your books" });
  expect(screen.queryByText(/Nothing in practice fits yet/)).toBeNull();
  expect(screen.queryByText(/find an exercise in my sources/)).toBeNull();
});

// -- nothing fits: the fallback ----------------------------------------------------------------------

const FOUND: FindExercisesDto = { version: 1, status: "ok", policy: "reading", dropped: {}, candidates: [{
  key: "srcex:ext_text:t9", extractionId: "ext_text", spanIds: ["t9"], sourceId: "src_text", revisionId: "rev_text",
  sourceTitle: "Matrix Theory", page: 9, label: "Exercise 4, p. 9", statement: "4. Compute the eigenvalues of the diagonal matrix [[2,0],[0,3]].",
  exposure: fresh, importRequest: { extractionId: "ext_text", sourceId: "src_text", revisionId: "rev_text", rawSelection: { nodes: [{ spanId: "t9", start: 0, end: 60 }] } },
}] };

it("with nothing fitting and the fallback on, the learner can find an exercise in their sources", async () => {
  api.readerFindExercises.mockResolvedValue(done(FOUND, "find_exercises"));
  const { onUse } = renderOn(practiceResult([], []), { fallback: true });
  expect(api.readerExerciseCandidates).not.toHaveBeenCalled(); // no exercise was proposed: nothing to check
  const line = screen.getByText(/Nothing in practice fits yet ·/);
  expect(api.readerFindExercises).not.toHaveBeenCalled(); // learner-initiated only
  fireEvent.click(within(line).getByRole("button", { name: "find an exercise in my sources ▸" }));
  expect(api.readerFindExercises).toHaveBeenCalledWith({ query: ASK.query, learningObjectIds: ["lo_matrices"], extractionId: "ext_open" });
  const card = await screen.findByTestId("exercise-candidate");
  expect(card.textContent).toContain(FOUND.candidates[0].statement);
  expect(card.textContent).toContain("Matrix Theory · p. 9");
  fireEvent.click(within(card).getByRole("button", { name: /use this one/ }));
  expect(onUse).toHaveBeenCalledWith(expect.objectContaining({ origin: "fallback", importRequest: FOUND.candidates[0].importRequest }));
  expect(api.recordProposalImpressions).not.toHaveBeenCalled(); // the server recorded what it showed
});

it("a fallback that finds nothing says so; with the fallback off there is no offer", async () => {
  api.readerFindExercises.mockResolvedValue(done({ ...FOUND, status: "none_found", candidates: [] }, "find_exercises"));
  renderOn(practiceResult([], []), { fallback: true });
  fireEvent.click(screen.getByRole("button", { name: "find an exercise in my sources ▸" }));
  expect(await screen.findByText("No exercise in your books fits this yet.")).toBeTruthy();
  cleanup();
  renderOn(practiceResult([], []), { fallback: false });
  expect(screen.getByText("Nothing in practice fits yet.")).toBeTruthy();
  expect(screen.queryByRole("button", { name: /find an exercise in my sources/ })).toBeNull();
});

it("the check runs as a job read until done, off the sidecar's request path", async () => {
  api.readerExerciseCandidates.mockResolvedValue({ jobId: "ljob_x", kind: "exercise_candidates", askId: null, state: "pending", result: null });
  api.readerLibraryJob.mockResolvedValue(done(view([[EX_A.key, fresh]])));
  renderOn(practiceResult([], [EX_A]));
  expect(await screen.findByText(EX_A.statement)).toBeTruthy();
  expect(api.readerLibraryJob).toHaveBeenCalledWith({ jobId: "ljob_x" });
});

it("leaving before the check lands cancels its job and never reads it again", async () => {
  api.readerExerciseCandidates.mockResolvedValue({ jobId: "ljob_y", kind: "exercise_candidates", askId: null, state: "pending", result: null });
  api.readerLibraryJob.mockResolvedValue({ jobId: "ljob_y", kind: "exercise_candidates", askId: null, state: "pending", result: null });
  api.readerLibraryJobCancel.mockResolvedValue({ jobId: "ljob_y", state: "cancelled" });
  const { unmount } = renderOn(practiceResult([], [EX_A]));
  await waitFor(() => expect(api.readerExerciseCandidates).toHaveBeenCalledTimes(1));
  unmount();
  await waitFor(() => expect(api.readerLibraryJobCancel).toHaveBeenCalledWith({ jobId: "ljob_y" }));
});
