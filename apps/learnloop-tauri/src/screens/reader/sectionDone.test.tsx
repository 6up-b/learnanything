// The section's own controls (UX-29, docs/reviews/ux-first-questions-today.md; split by algorithm tag mvp-0.63,
// docs/reviews/algorithm-mvp-0.63.md): "I've read this section" finishes it, a short section that needs no scrolling
// included; "Done with this check" closes a quick check and passes its close on (it finishes the section only below
// the tag, as the backend decides); the section shows "Section finished" only once the backend's answer has it, and
// then "Read the next section" (navigation only) or, at the book's end, "Back to Today".
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { ReaderGuideSectionDto } from "../../api/dto";
import { findJargon } from "../../copy/denyList";
import { BACK_TO_TODAY, CHECK_DONE, GuideRail, READ_NEXT_SECTION, SECTION_DONE, SECTION_DONE_FAILED, SECTION_DONE_LINE, type GuideRailProps } from "./GuideRail";
import { QUESTIONS_FROM_READING } from "../../app/todayCause";

const { api } = vi.hoisted(() => ({ api: { readerAuthoredQuestionAction: vi.fn(async () => ({})) } }));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

afterEach(cleanup);

const SECTION: ReaderGuideSectionDto = {
  id: "u2", label: "Conditional probability", startSpanId: "s1", endSpanId: "s3", spanIds: ["s1", "s2", "s3"], question: null, suggestedPassages: []
};
const CHECKED: ReaderGuideSectionDto = {
  ...SECTION,
  question: { placement: "auto_authored", authoredQuestionId: "aq_1", prompt: "Why is it conditional?", expectedAnswer: "Because…", reason: "A quick check.", spanIds: ["s2"] }
} as unknown as ReaderGuideSectionDto;

/** The backend's answer to a completion that finished the section. */
function finished(extra: Record<string, unknown> = {}) {
  return { progress: { completedAt: "2026-11-21T10:00:00Z" }, enqueuedGeneration: false, batchId: null, ...extra };
}

function props(overrides: Partial<GuideRailProps> = {}, section: ReaderGuideSectionDto = SECTION): GuideRailProps {
  const noop = () => undefined;
  return {
    visible: true, extractionId: "ext", offline: false,
    guidePlan: { sourceId: "src", extractionId: "ext", personalized: false, selectionBasis: "", sections: [section], pendingDiagnosisAttemptIds: [], goalContext: null },
    guideLoading: false, currentGuideSection: section, currentSectionProgress: 1, currentQuestionOpen: false,
    boundaryChecksAvailable: true, authoringSections: [], revealedSections: [], completedSections: [], sectionSeen: { u2: 3 },
    annotatedSpans: new Set(), openQuestionSections: [], setDismissedSections: vi.fn(), jumpToSpan: noop,
    revealSection: noop, completeSection: vi.fn(async () => finished({ enqueuedGeneration: true, batchId: "batch_1" })),
    onError: noop, boundaryBlock: null, boundarySkipped: false,
    setBoundarySkipped: noop, boundaryAnswered: false, setBoundaryAnswered: noop, boundaryResponse: "",
    setBoundaryResponse: noop, boundarySubmitted: false, setBoundarySubmitted: noop, questionControl: null,
    sendQuestionControl: noop, disposition: null, chooseDisposition: noop,
    ...overrides
  } as unknown as GuideRailProps;
}

it("is there from the start, before any reading: a short section that needs no scrolling can be finished too", () => {
  render(<GuideRail {...props({ sectionSeen: {} })} />);
  expect(screen.getByRole("button", { name: SECTION_DONE })).toBeTruthy();
  expect(SECTION_DONE).toBe("I’ve read this section");
  expect(SECTION_DONE_LINE).toBe("Section finished");
  expect(READ_NEXT_SECTION).toBe("Read the next section");
  expect(BACK_TO_TODAY).toBe("Back to Today");
  expect(CHECK_DONE).toBe("Done with this check");
});

it("'Done with this check' closes the check and passes its close on; only the learner's own control sends a completion of its own", async () => {
  const completeSection = vi.fn(async () => ({ progress: { completedAt: null }, enqueuedGeneration: false, batchId: null }));
  const setDismissedSections = vi.fn();
  render(<GuideRail {...props({ completeSection, setDismissedSections, openQuestionSections: [CHECKED], currentQuestionOpen: true }, CHECKED)} />);
  const card = screen.getByText("Why is it conditional?").closest("div[data-quick-check]") as HTMLElement;
  fireEvent.click(within(card).getByRole("button", { name: /think it through/ }));
  fireEvent.change(within(card).getByPlaceholderText("Answer in your own words…"), { target: { value: "Because B happened." } });
  fireEvent.click(within(card).getByRole("button", { name: /compare with the source/ }));
  fireEvent.click(await within(card).findByRole("button", { name: CHECK_DONE }));
  expect(within(card).queryByRole("button", { name: "done for now" })).toBeNull();
  // The check closes; its close goes as what it is, never as the learner's word.
  expect(setDismissedSections).toHaveBeenCalledTimes(1);
  expect(completeSection.mock.calls).toEqual([["u2", "check_closed"]]);
  // The backend did not finish the section (algorithm tag mvp-0.63): the section's own control is still there.
  await waitFor(() => expect(screen.getByRole("button", { name: SECTION_DONE })).toBeTruthy());
  expect(screen.queryByTestId("section-done")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: SECTION_DONE }));
  await waitFor(() => expect(completeSection).toHaveBeenCalledTimes(2));
  expect(completeSection.mock.calls[1]).toEqual(["u2"]);
});

it("after the press: one still line that the section's questions are being written and will be on Today", async () => {
  render(<GuideRail {...props()} />);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: SECTION_DONE }));
  });
  const line = await screen.findByTestId("section-done");
  expect(line.textContent).toContain("Writing questions from this section. They'll be on Today.");
  // The Reader's posture: the shared mark, still (G54).
  expect(line.querySelector(".ll-wait-mark")?.getAttribute("data-motion")).toBe("still");
  expect(screen.queryByRole("button", { name: SECTION_DONE })).toBeNull();
  expect(findJargon(line.textContent ?? "")).toEqual([]);
});

it("a completion that queued nothing says only that the section is finished", async () => {
  const completeSection = vi.fn(async () => finished());
  render(<GuideRail {...props({ completeSection })} />);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: SECTION_DONE }));
  });
  const line = await screen.findByTestId("section-done");
  expect(line.textContent).toBe("Section finished");
});

it("a failed save shows no finished section: the control stays, and says the save failed", async () => {
  const completeSection = vi.fn(async () => null);
  render(<GuideRail {...props({ completeSection })} />);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: SECTION_DONE }));
  });
  expect(screen.queryByTestId("section-done")).toBeNull();
  expect(screen.getByRole("alert").textContent).toBe(SECTION_DONE_FAILED);
  expect(screen.getByRole("button", { name: SECTION_DONE })).toBeTruthy();
});

it("a section already finished shows that it is finished, not the control", () => {
  render(<GuideRail {...props({ completedSections: ["u2"] })} />);
  expect(screen.queryByRole("button", { name: SECTION_DONE })).toBeNull();
  expect(screen.getByTestId("section-done").textContent).toBe("Section finished");
});

it("a section finished by reading to its end says what its finish started, from the backend's answer", () => {
  render(<GuideRail {...props({ completedSections: ["u2"], sectionFinishes: { u2: "writing" } })} />);
  expect(screen.getByTestId("section-done").textContent).toContain("Writing questions from this section.");
});

it("finished: 'Read the next section' only moves the reading there; at the book's end 'Back to Today', and no keep-reading line", () => {
  const NEXT: ReaderGuideSectionDto = { ...SECTION, id: "u3", label: "Bayes", startSpanId: "s4", endSpanId: "s5", spanIds: ["s4", "s5"] };
  const jumpToSpan = vi.fn();
  const completeSection = vi.fn();
  const twoSections = props({ completedSections: ["u2"], jumpToSpan, completeSection });
  render(<GuideRail {...twoSections} guidePlan={{ ...twoSections.guidePlan!, sections: [SECTION, NEXT] }} />);
  fireEvent.click(screen.getByRole("button", { name: READ_NEXT_SECTION }));
  expect(jumpToSpan).toHaveBeenCalledWith("s4", "start");
  expect(completeSection).not.toHaveBeenCalled();
  expect(screen.queryByRole("button", { name: BACK_TO_TODAY })).toBeNull();
  cleanup();
  // A one-section book: no fictitious next section, no "keep reading".
  const onOpenToday = vi.fn();
  render(<GuideRail {...props({ completedSections: ["u2"], onOpenToday, currentSectionProgress: 0.2 })} />);
  expect(screen.queryByRole("button", { name: READ_NEXT_SECTION })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: BACK_TO_TODAY }));
  expect(onOpenToday).toHaveBeenCalledTimes(1);
  expect(document.body.textContent).not.toMatch(/keep reading/i);
});

it("the section's position is labelled as a position, and a finished section is not forced to 100 %", () => {
  render(<GuideRail {...props({ completedSections: ["u2"], currentSectionRead: 0.4 })} />);
  const bar = screen.getByRole("progressbar", { name: "Position through this section" });
  expect(bar.getAttribute("aria-valuenow")).toBe("40");
  expect(screen.getByTestId("section-position").textContent).toBe("40% through this section");
});

it("an open quick check stays open and answerable after the press: nothing dismisses it", async () => {
  const setDismissedSections = vi.fn();
  render(<GuideRail {...props({ setDismissedSections, openQuestionSections: [CHECKED], currentQuestionOpen: true }, CHECKED)} />);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: SECTION_DONE }));
  });
  expect(setDismissedSections).not.toHaveBeenCalled();
  const card = screen.getByText("Why is it conditional?").closest("div[data-quick-check]") as HTMLElement;
  expect(within(card).getByRole("button", { name: /think it through/ })).toBeTruthy();
});

it("offline: no control (nothing could be sent)", () => {
  render(<GuideRail {...props({ offline: true })} />);
  expect(screen.queryByRole("button", { name: SECTION_DONE })).toBeNull();
});

// A section finished before its book is ready (docs/reviews/ux31-section-done-before-build.md): the completion is
// kept until the book's topics are in, and its questions are written then, with no press.
it("a section finished before its book is ready says its questions come once the book is, still and plain", async () => {
  const completeSection = vi.fn(async () => finished({ waitingForBuild: true }));
  render(<GuideRail {...props({ completeSection, bookTitle: "Symmetric Matrices and Variance" })} />);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: SECTION_DONE }));
  });
  const line = await screen.findByTestId("section-done");
  expect(line.textContent).toContain(
    "Your questions from this section will be written as soon as “Symmetric Matrices and Variance” is ready. They'll be on Today."
  );
  expect(line.textContent).not.toContain(SECTION_DONE_LINE);
  expect(line.querySelector(".ll-wait-mark")?.getAttribute("data-motion")).toBe("still");
  expect(findJargon(line.textContent ?? "")).toEqual([]);
});

it("without the book's title it names the book plainly", async () => {
  const completeSection = vi.fn(async () => finished({ waitingForBuild: true }));
  render(<GuideRail {...props({ completeSection })} />);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: SECTION_DONE }));
  });
  expect((await screen.findByTestId("section-done")).textContent).toContain(
    "Your questions from this section will be written as soon as the book is ready."
  );
});

it("the guide says where questions come from in the one explanation Today and the Library use (not offline)", () => {
  render(<GuideRail {...props({ sectionSeen: { u2: 1 } })} />);
  expect(screen.getByTestId("guide-questions-from").textContent).toBe(QUESTIONS_FROM_READING);
  expect(findJargon(QUESTIONS_FROM_READING)).toEqual([]);
  cleanup();
  render(<GuideRail {...props({ offline: true })} />);
  expect(screen.queryByTestId("guide-questions-from")).toBeNull();
});
