// The live walk sectionend-1 (2026-11-21) on the guide: a student read a one-section chapter to its end, closed a quick
// check on the way, and found the guide's words around the end wrong. Closing the check took her answer and the
// comparison away (UX-79); at the book's last passage the guide said "You're near the section break. Keep going" and,
// after the check, "quick check complete — keep going" (UX-80); "I've read this section" vanished under her pointer
// when the reading reached the end, and nothing said the reading itself had finished the section (UX-81).
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderGuideSectionDto } from "../../api/dto";
import { findJargon } from "../../copy/denyList";
import {
  BACK_TO_TODAY, CHECK_COMES_UP, CHECK_DONE, closedCheckSummary, END_PRESS_GUARD_MS, GuideRail, nearTheEnd, READ_NEXT_SECTION, SECTION_DONE,
  SECTION_DONE_LINE, SECTION_ENDED_LINE, type GuideRailProps,
} from "./GuideRail";

const { api } = vi.hoisted(() => ({
  api: { readerAuthoredQuestionAction: vi.fn(async () => ({})), readerPresentQuestion: vi.fn(async () => ({ administrationId: "adm_1" })),
    readerSubmitQuestion: vi.fn(async () => ({})) },
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

beforeEach(() => {
  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
    callback(0);
    return 1;
  });
  vi.stubGlobal("cancelAnimationFrame", () => undefined);
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

const BOOK = "Symmetric Matrices and Variance";
const ONLY: ReaderGuideSectionDto = {
  id: "u1", label: "symmetric-matrices", startSpanId: "s1", endSpanId: "s9", spanIds: ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9"],
  question: null, suggestedPassages: [],
};
const AUTHORED = {
  placement: "auto_authored", authoredQuestionId: "aq_1", prompt: "What does diagonalizing a symmetric matrix need?",
  expectedAnswer: "Symmetry is necessary and sufficient: Q holds orthonormal eigenvectors, D the eigenvalues.", reason: "A quick check.",
  spanIds: ["s5"], readingPhase: "after_section",
};
const CHECKED = { ...ONLY, question: AUTHORED } as unknown as ReaderGuideSectionDto;
const NEXT: ReaderGuideSectionDto = { ...ONLY, id: "u2", label: "Variance", startSpanId: "s10", endSpanId: "s12", spanIds: ["s10", "s11", "s12"] };

function props(overrides: Partial<GuideRailProps> = {}, section: ReaderGuideSectionDto = ONLY, sections: ReaderGuideSectionDto[] = [section]): GuideRailProps {
  const noop = () => undefined;
  return {
    visible: true, extractionId: "ext", offline: false,
    guidePlan: { sourceId: "src", extractionId: "ext", personalized: false, selectionBasis: "", sections, pendingDiagnosisAttemptIds: [], goalContext: null },
    guideLoading: false, currentGuideSection: section, currentSectionProgress: 0.8, currentQuestionOpen: false,
    boundaryChecksAvailable: true, authoringSections: [], revealedSections: [], completedSections: [], sectionSeen: { u1: 7 },
    readingMoved: true, annotatedSpans: new Set(), openQuestionSections: [], setDismissedSections: vi.fn(), jumpToSpan: noop,
    revealSection: noop, completeSection: vi.fn(async () => ({ progress: { completedAt: null }, enqueuedGeneration: false, batchId: null })),
    onError: noop, boundaryBlock: null, boundarySkipped: false, bookTitle: BOOK, onOpenToday: vi.fn(),
    setBoundarySkipped: noop, boundaryAnswered: false, setBoundaryAnswered: noop, boundaryResponse: "",
    setBoundaryResponse: noop, boundarySubmitted: false, setBoundarySubmitted: noop, questionControl: null,
    sendQuestionControl: noop, disposition: null, chooseDisposition: noop,
    ...overrides,
  } as unknown as GuideRailProps;
}

const checkCard = () => screen.getByText(AUTHORED.prompt).closest("div[data-quick-check]") as HTMLElement;

async function answerAndClose() {
  fireEvent.click(within(checkCard()).getByRole("button", { name: /think it through/ }));
  fireEvent.change(within(checkCard()).getByPlaceholderText("Answer in your own words…"), {
    target: { value: "Symmetry is required; Q has orthonormal eigenvectors and D the eigenvalues." },
  });
  await act(async () => {
    fireEvent.click(within(checkCard()).getByRole("button", { name: /compare with the source/ }));
  });
  fireEvent.click(await within(checkCard()).findByRole("button", { name: CHECK_DONE }));
}

// -- UX-79: closing a quick check keeps what the learner wrote and what it was compared with -------------------------

it("'Done with this check' keeps the learner's answer and the comparison in the guide, folded, one press to open", async () => {
  const setDismissedSections = vi.fn();
  const open = props({ setDismissedSections, openQuestionSections: [CHECKED], currentQuestionOpen: true }, CHECKED);
  const { rerender } = render(<GuideRail {...open} />);
  await answerAndClose();
  expect(setDismissedSections).toHaveBeenCalledTimes(1);
  // The hook then stops offering the check (it is dismissed): the card goes, what it showed stays.
  rerender(<GuideRail {...open} openQuestionSections={[]} currentQuestionOpen={false} />);
  expect(screen.queryByText(AUTHORED.prompt, { selector: "div[data-quick-check] *" })).toBeNull();
  const kept = screen.getByTestId("closed-check");
  const summary = within(kept).getByText(closedCheckSummary("symmetric-matrices"));
  expect(summary.tagName).toBe("SUMMARY");
  expect((kept as HTMLDetailsElement).open).toBe(false);
  fireEvent.click(summary);
  expect(within(kept).getByText("Symmetry is required; Q has orthonormal eigenvectors and D the eigenvalues.")).toBeTruthy();
  expect(within(kept).getByText(AUTHORED.expectedAnswer)).toBeTruthy();
  expect(within(kept).getByText(AUTHORED.prompt)).toBeTruthy();
  // Shown from what the Reader holds: nothing is sent again (the one "answered" record went when it was compared).
  expect(api.readerAuthoredQuestionAction).toHaveBeenCalledTimes(1);
  expect(findJargon(kept.textContent ?? "")).toEqual([]);
  expect(closedCheckSummary("symmetric-matrices")).toBe("Your answer to the quick check on “Symmetric matrices”");
});

it("a check closed without an answer (skip, keep reading) keeps nothing to show", async () => {
  const open = props({ openQuestionSections: [CHECKED], currentQuestionOpen: true }, CHECKED);
  const { rerender } = render(<GuideRail {...open} />);
  fireEvent.click(within(checkCard()).getByRole("button", { name: "keep reading" }));
  rerender(<GuideRail {...open} openQuestionSections={[]} currentQuestionOpen={false} />);
  expect(screen.queryByTestId("closed-check")).toBeNull();
});

it("a placed question's closed check keeps the learner's answer (it shows no intended answer to compare with)", async () => {
  const PLACED = { ...ONLY, question: { placement: "owner_reviewed", practiceItemId: "pi_1", prompt: "Explain the variance identity.", reason: "r",
    readingPhase: "after_section", placementEventId: "pe_1", learningObjectId: "lo_1" } } as unknown as ReaderGuideSectionDto;
  const open = props({ openQuestionSections: [PLACED], currentQuestionOpen: true }, PLACED);
  const { rerender } = render(<GuideRail {...open} />);
  const card = () => screen.getByText("Explain the variance identity.").closest("div[data-quick-check]") as HTMLElement;
  await act(async () => {
    fireEvent.click(within(card()).getByRole("button", { name: /think it through/ }));
  });
  fireEvent.change(within(card()).getByPlaceholderText("Answer in your own words…"), { target: { value: "E[X²] − E[X]²." } });
  await act(async () => {
    fireEvent.click(within(card()).getByRole("button", { name: /record answer/ }));
  });
  fireEvent.click(await within(card()).findByRole("button", { name: CHECK_DONE }));
  rerender(<GuideRail {...open} openQuestionSections={[]} currentQuestionOpen={false} />);
  const kept = screen.getByTestId("closed-check");
  fireEvent.click(within(kept).getByText(closedCheckSummary("symmetric-matrices")));
  expect(within(kept).getByText("E[X²] − E[X]².")).toBeTruthy();
  expect(within(kept).queryByText(/intended answer/)).toBeNull();
});

// -- UX-80: the book's last section says nothing about keeping going ----------------------------------------------

it("near the end of the book's last section: no section break, no 'keep going'", () => {
  render(<GuideRail {...props()} />);
  const guide = document.body.textContent ?? "";
  expect(guide).toContain(nearTheEnd(BOOK));
  expect(nearTheEnd(BOOK)).toBe(`You’re near the end of “${BOOK}”.`);
  expect(nearTheEnd(null)).toBe("You’re near the end.");
  expect(guide).not.toMatch(/section break|keep going/i);
});

it("mid-book the same place still reads as before: near the section break, keep going", () => {
  render(<GuideRail {...props({}, ONLY, [ONLY, NEXT])} />);
  expect(document.body.textContent).toContain("You’re near the section break. Keep going, or revisit a useful passage.");
});

it("the last section's answered check: compare below, with no 'keep reading'; finished, no 'quick check complete — keep going'", async () => {
  const open = props({ openQuestionSections: [CHECKED], currentQuestionOpen: true, answeredSections: ["u1"] }, CHECKED);
  const { rerender } = render(<GuideRail {...open} />);
  expect(document.body.textContent).toContain("You answered this section's quick check: compare below.");
  expect(document.body.textContent).not.toMatch(/then keep reading/);
  rerender(<GuideRail {...open} openQuestionSections={[]} currentQuestionOpen={false} completedSections={["u1"]} />);
  expect(document.body.textContent).not.toMatch(/keep going/i);
  expect(screen.getByRole("button", { name: BACK_TO_TODAY })).toBeTruthy();
});

it("mid-book, answered and finished: the check's lines read as before", () => {
  const open = props({ openQuestionSections: [CHECKED], currentQuestionOpen: true, answeredSections: ["u1"] }, CHECKED, [CHECKED, NEXT]);
  const { rerender } = render(<GuideRail {...open} />);
  expect(document.body.textContent).toContain("You answered this section's quick check: compare below, then keep reading.");
  rerender(<GuideRail {...open} openQuestionSections={[]} currentQuestionOpen={false} completedSections={["u1"]} />);
  expect(document.body.textContent).toContain("✓ quick check complete — keep going.");
  expect(screen.getByRole("button", { name: READ_NEXT_SECTION })).toBeTruthy();
});

it("the last section's open check after the section break says where it is, with no 'keep reading'", () => {
  const PLACED = { ...ONLY, question: { placement: "owner_reviewed", practiceItemId: "pi_1", prompt: "P?", reason: "r",
    readingPhase: "after_section", placementEventId: "pe_1" } } as unknown as ReaderGuideSectionDto;
  render(<GuideRail {...props({ openQuestionSections: [PLACED], currentQuestionOpen: true }, PLACED)} />);
  expect(document.body.textContent).toContain("A quick check on this section is ready, just below.");
  expect(document.body.textContent).not.toMatch(/section break/);
});

// -- UX-81: the end arriving while "I've read this section" is under the pointer ------------------------------------

it("when the reading's end finishes the section, its control's place says so; a press arriving then does no harm", () => {
  vi.useFakeTimers({ toFake: ["Date", "setTimeout", "clearTimeout"] });
  const onOpenToday = vi.fn();
  const completeSection = vi.fn();
  const base = props({ onOpenToday, completeSection, currentSectionProgress: 1 });
  const { rerender } = render(<GuideRail {...base} />);
  const control = screen.getByRole("button", { name: SECTION_DONE });
  const slot = control.closest("[data-section-control]") as HTMLElement;
  expect(slot).toBeTruthy();
  // The save carrying the end comes back: the section is finished by its end, and the book was not ready yet.
  rerender(<GuideRail {...base} completedSections={["u1"]} sectionFinishes={{ u1: "waiting" }} endedSections={["u1"]} />);
  expect(screen.queryByRole("button", { name: SECTION_DONE })).toBeNull();
  // In the control's own place.
  const ended = screen.getByTestId("section-ended");
  expect(ended.hasAttribute("data-section-control")).toBe(true);
  expect(ended.textContent).toBe(SECTION_ENDED_LINE);
  expect(SECTION_ENDED_LINE).toBe("Section finished: you read to the end.");
  // What the finish started is said too, under it.
  expect(screen.getByTestId("section-done").textContent).toContain(`as soon as “${BOOK}” is ready`);
  // The press meant for the control that just went lands on nothing that acts: not on Back to Today.
  fireEvent.click(ended);
  fireEvent.click(screen.getByRole("button", { name: BACK_TO_TODAY }));
  expect(onOpenToday).not.toHaveBeenCalled();
  expect(completeSection).not.toHaveBeenCalled();
  // A moment later Back to Today is the learner's to press.
  act(() => {
    vi.advanceTimersByTime(END_PRESS_GUARD_MS + 1);
  });
  fireEvent.click(screen.getByRole("button", { name: BACK_TO_TODAY }));
  expect(onOpenToday).toHaveBeenCalledTimes(1);
  expect(findJargon(SECTION_ENDED_LINE)).toEqual([]);
});

it("a section finished by the learner's own press, or found finished on opening, keeps its words and its way on at once", async () => {
  const onOpenToday = vi.fn();
  render(<GuideRail {...props({ onOpenToday, completedSections: ["u1"] })} />);
  expect(screen.getByTestId("section-done").textContent).toBe(SECTION_DONE_LINE);
  expect(screen.queryByTestId("section-ended")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: BACK_TO_TODAY }));
  expect(onOpenToday).toHaveBeenCalledTimes(1);
});

it("a section read to its end in an earlier visit says so on opening, with its way on at once", () => {
  const onOpenToday = vi.fn();
  render(<GuideRail {...props({ onOpenToday, completedSections: ["u1"], endedSections: ["u1"] })} />);
  expect(screen.getByTestId("section-ended").textContent).toBe(SECTION_ENDED_LINE);
  fireEvent.click(screen.getByRole("button", { name: BACK_TO_TODAY }));
  expect(onOpenToday).toHaveBeenCalledTimes(1);
});

// -- UX-84 (the live walk sectionend-2): "writing a quick check" vanished with no check and no word -----------------

it("a check written at 60 % but shown only at 70 % says it is ready and where it comes up, never a silent gap", () => {
  const writing = props({ authoringSections: ["u1"], currentSectionProgress: 0.62 }, ONLY, [ONLY, NEXT]);
  const { rerender } = render(<GuideRail {...writing} />);
  expect(document.body.textContent).toContain("◐ writing a quick check for this section…");
  // The poll brings the written check; the check-offer rule shows it only once 70 % of the section is read.
  const written = props({ currentSectionProgress: 0.66 }, CHECKED, [CHECKED, NEXT]);
  rerender(<GuideRail {...written} />);
  expect(document.body.textContent).toContain(CHECK_COMES_UP);
  expect(CHECK_COMES_UP).toBe("A quick check on this section is ready. It comes up as you read on, near the end of the section.");
  expect(findJargon(CHECK_COMES_UP)).toEqual([]);
  // At 70 % the rule offers it: the card shows, and the guide says it is just below.
  rerender(<GuideRail {...written} openQuestionSections={[CHECKED]} currentQuestionOpen currentSectionProgress={0.71} />);
  expect(document.body.textContent).not.toContain(CHECK_COMES_UP);
  expect(document.body.textContent).toContain("A quick check on this section is ready, just below.");
  // Set aside, or the section finished: nothing more is said of it.
  rerender(<GuideRail {...written} dismissedSections={["u1"]} />);
  expect(document.body.textContent).not.toContain(CHECK_COMES_UP);
});
