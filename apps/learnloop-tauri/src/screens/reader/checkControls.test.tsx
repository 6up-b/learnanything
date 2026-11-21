// A quick check's controls above the fold (the first evening's design, "Quick-check controls above the fold"): the
// active check comes before optional guide material; its action area sits beside the answer box, and after the
// comparison "Done with this check" is in that same area, before the intended answer; opening it brings that area into
// the guide's own view (never the chapter's); typed work and keyboard focus survive results arriving.
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderGuideSectionDto } from "../../api/dto";
import { CHECK_DONE, GuideRail, type GuideRailProps } from "./GuideRail";

const { api, scrolled } = vi.hoisted(() => ({
  api: { readerAuthoredQuestionAction: vi.fn(async () => ({})) },
  scrolled: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
vi.mock("../../components/scrollWithin", () => ({ scrollIntoViewWithin: scrolled }));

beforeEach(() => {
  scrolled.mockReset();
  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
    callback(0);
    return 1;
  });
  vi.stubGlobal("cancelAnimationFrame", () => undefined);
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const CHECKED = {
  id: "u2", label: "Conditional probability", startSpanId: "s1", endSpanId: "s3", spanIds: ["s1", "s2", "s3"], suggestedPassages: [],
  question: { placement: "auto_authored", authoredQuestionId: "aq_1", prompt: "Why is it conditional?", expectedAnswer: "Because the intended answer says so.", reason: "A quick check.", spanIds: ["s2"] },
} as unknown as ReaderGuideSectionDto;

function props(overrides: Partial<GuideRailProps> = {}): GuideRailProps {
  const noop = () => undefined;
  return {
    visible: true, extractionId: "ext", offline: false,
    guidePlan: { sourceId: "src", extractionId: "ext", personalized: false, selectionBasis: "", sections: [CHECKED], pendingDiagnosisAttemptIds: [], goalContext: null },
    guideLoading: false, currentGuideSection: CHECKED, currentSectionProgress: 0.8, currentQuestionOpen: true,
    boundaryChecksAvailable: true, authoringSections: [], revealedSections: [], completedSections: [], sectionSeen: { u2: 2 },
    annotatedSpans: new Set(), openQuestionSections: [CHECKED], setDismissedSections: vi.fn(), jumpToSpan: noop,
    revealSection: noop, completeSection: vi.fn(async () => null), onError: noop, boundaryBlock: null, boundarySkipped: false,
    setBoundarySkipped: noop, boundaryAnswered: false, setBoundaryAnswered: noop, boundaryResponse: "",
    setBoundaryResponse: noop, boundarySubmitted: false, setBoundarySubmitted: noop, questionControl: null,
    sendQuestionControl: noop, disposition: null, chooseDisposition: noop,
    header: <div data-testid="optional-header">Last time here</div>,
    path: <div data-testid="optional-path">Your path</div>,
    ...overrides,
  } as unknown as GuideRailProps;
}

const card = () => screen.getByText("Why is it conditional?").closest("div[data-quick-check]") as HTMLElement;
const follows = (a: Element, b: Element) => Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);

it("the active check comes before the optional guide material", () => {
  render(<GuideRail {...props()} />);
  expect(follows(card(), screen.getByTestId("optional-header"))).toBe(true);
  expect(follows(card(), screen.getByTestId("optional-path"))).toBe(true);
});

it("opening it brings its action area, beside the answer box, into the guide's own view", () => {
  render(<GuideRail {...props()} />);
  scrolled.mockReset();
  fireEvent.click(within(card()).getByRole("button", { name: /think it through/ }));
  const box = within(card()).getByPlaceholderText("Answer in your own words…");
  const actions = card().querySelector("[data-check-actions]") as HTMLElement;
  expect(actions).toBeTruthy();
  expect(follows(box, actions)).toBe(true);
  expect(within(actions).getByRole("button", { name: /compare with the source/ })).toBeTruthy();
  expect(within(actions).getByRole("button", { name: "skip" })).toBeTruthy();
  expect(scrolled).toHaveBeenCalledWith(actions, { block: "nearest" });
});

it("after the comparison 'Done with this check' is in the same action area, before the intended answer, and has focus", async () => {
  render(<GuideRail {...props()} />);
  fireEvent.click(within(card()).getByRole("button", { name: /think it through/ }));
  const box = within(card()).getByPlaceholderText("Answer in your own words…");
  box.focus();
  fireEvent.change(box, { target: { value: "Because B happened." } });
  await act(async () => {
    fireEvent.click(within(card()).getByRole("button", { name: /compare with the source/ }));
  });
  const done = await within(card()).findByRole("button", { name: CHECK_DONE });
  const actions = done.closest("[data-check-actions]") as HTMLElement;
  expect(actions).toBeTruthy();
  expect(follows(actions, within(card()).getByText("Because the intended answer says so."))).toBe(true);
  expect(follows(within(card()).getByText("Because B happened."), actions)).toBe(true);
  expect(document.activeElement).toBe(done);
});

it("typed work and keyboard focus survive results arriving (a guide refresh, the section finishing under the check)", () => {
  const { rerender } = render(<GuideRail {...props()} />);
  fireEvent.click(within(card()).getByRole("button", { name: /think it through/ }));
  const box = within(card()).getByPlaceholderText("Answer in your own words…") as HTMLTextAreaElement;
  box.focus();
  fireEvent.change(box, { target: { value: "Half an answer" } });
  // A poll returns a new guide plan object, and the section's end finishes it.
  const refreshed = props({ completedSections: ["u2"], sectionFinishes: { u2: "writing" } });
  rerender(<GuideRail {...refreshed} guidePlan={{ ...refreshed.guidePlan!, sections: [{ ...CHECKED }] }} />);
  const after = within(card()).getByPlaceholderText("Answer in your own words…") as HTMLTextAreaElement;
  expect(after).toBe(box);
  expect(after.value).toBe("Half an answer");
  expect(document.activeElement).toBe(after);
});
