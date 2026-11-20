// First questions arrive, UX-29 (docs/reviews/ux-first-questions-today.md): the desktop Reader gets the phone's
// explicit way to finish a section. A section's questions are written when it is finished; on the desktop that was
// only the quick check's "done for now". "Done with this section" sends the same completion, once the learner has read
// to the section's end (the rule that ticks it "read" in Contents), and says what happens next in the Reader's posture.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { ReaderGuideSectionDto } from "../../api/dto";
import { findJargon } from "../../copy/denyList";
import { GuideRail, SECTION_DONE, type GuideRailProps } from "./GuideRail";

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

function props(overrides: Partial<GuideRailProps> = {}, section: ReaderGuideSectionDto = SECTION): GuideRailProps {
  const noop = () => undefined;
  return {
    visible: true, extractionId: "ext", offline: false,
    guidePlan: { sourceId: "src", extractionId: "ext", personalized: false, selectionBasis: "", sections: [section], pendingDiagnosisAttemptIds: [], goalContext: null },
    guideLoading: false, currentGuideSection: section, currentSectionProgress: 1, currentQuestionOpen: false,
    boundaryChecksAvailable: true, authoringSections: [], revealedSections: [], completedSections: [], sectionSeen: { u2: 3 },
    annotatedSpans: new Set(), openQuestionSections: [], setDismissedSections: vi.fn(), jumpToSpan: noop,
    revealSection: noop, completeSection: vi.fn(async () => ({ progress: {}, enqueuedGeneration: true, batchId: "batch_1" })),
    onError: noop, boundaryBlock: null, boundarySkipped: false,
    setBoundarySkipped: noop, boundaryAnswered: false, setBoundaryAnswered: noop, boundaryResponse: "",
    setBoundaryResponse: noop, boundarySubmitted: false, setBoundarySubmitted: noop, questionControl: null,
    sendQuestionControl: noop, disposition: null, chooseDisposition: noop,
    ...overrides
  } as unknown as GuideRailProps;
}

it("is absent before the section's last passage is read, and there once it is", () => {
  const { rerender } = render(<GuideRail {...props({ sectionSeen: { u2: 2 } })} />);
  expect(screen.queryByRole("button", { name: SECTION_DONE })).toBeNull();
  rerender(<GuideRail {...props({ sectionSeen: { u2: 3 } })} />);
  expect(screen.getByRole("button", { name: SECTION_DONE })).toBeTruthy();
  expect(SECTION_DONE).toBe("Done with this section");
});

it("sends the same completion as the quick check's 'done for now'", async () => {
  const completeSection = vi.fn(async () => ({ progress: {}, enqueuedGeneration: true, batchId: "batch_1" }));
  render(<GuideRail {...props({ completeSection, openQuestionSections: [CHECKED], currentQuestionOpen: true }, CHECKED)} />);
  // The quick check's own path: think it through, compare, done for now.
  const card = screen.getByText("Why is it conditional?").closest("div[data-quick-check]") as HTMLElement;
  fireEvent.click(within(card).getByRole("button", { name: /think it through/ }));
  fireEvent.change(within(card).getByPlaceholderText("Answer in your own words…"), { target: { value: "Because B happened." } });
  fireEvent.click(within(card).getByRole("button", { name: /compare with the source/ }));
  fireEvent.click(await within(card).findByRole("button", { name: "done for now" }));
  expect(completeSection).toHaveBeenCalledTimes(1);
  const viaCheck = completeSection.mock.calls[0];
  cleanup();
  const pressed = vi.fn(async () => ({ progress: {}, enqueuedGeneration: true, batchId: "batch_1" }));
  render(<GuideRail {...props({ completeSection: pressed })} />);
  fireEvent.click(screen.getByRole("button", { name: SECTION_DONE }));
  await waitFor(() => expect(pressed).toHaveBeenCalledTimes(1));
  expect(pressed.mock.calls[0]).toEqual(viaCheck);
  expect(viaCheck).toEqual(["u2"]);
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

it("a completion that queued nothing says only that the section is done", async () => {
  const completeSection = vi.fn(async () => ({ progress: {}, enqueuedGeneration: false, batchId: null }));
  render(<GuideRail {...props({ completeSection })} />);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: SECTION_DONE }));
  });
  const line = await screen.findByTestId("section-done");
  expect(line.textContent).toBe("✓ Done with this section.");
});

it("a section already finished shows that it is done, not the control", () => {
  render(<GuideRail {...props({ completedSections: ["u2"] })} />);
  expect(screen.queryByRole("button", { name: SECTION_DONE })).toBeNull();
  expect(screen.getByTestId("section-done").textContent).toBe("✓ Done with this section.");
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
  const completeSection = vi.fn(async () => ({ progress: {}, enqueuedGeneration: false, waitingForBuild: true, batchId: null }));
  render(<GuideRail {...props({ completeSection, bookTitle: "Symmetric Matrices and Variance" })} />);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: SECTION_DONE }));
  });
  const line = await screen.findByTestId("section-done");
  expect(line.textContent).toContain(
    "Your questions from this section will be written as soon as “Symmetric Matrices and Variance” is ready. They'll be on Today."
  );
  expect(line.textContent).not.toContain("✓ Done with this section.");
  expect(line.querySelector(".ll-wait-mark")?.getAttribute("data-motion")).toBe("still");
  expect(findJargon(line.textContent ?? "")).toEqual([]);
});

it("without the book's title it names the book plainly", async () => {
  const completeSection = vi.fn(async () => ({ progress: {}, enqueuedGeneration: false, waitingForBuild: true, batchId: null }));
  render(<GuideRail {...props({ completeSection })} />);
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: SECTION_DONE }));
  });
  expect((await screen.findByTestId("section-done")).textContent).toContain(
    "Your questions from this section will be written as soon as the book is ready."
  );
});
