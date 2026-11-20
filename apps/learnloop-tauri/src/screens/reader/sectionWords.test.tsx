// A web page's sections are stored under the slug of their heading ("modeling-the-elevator-problem"; the
// heading's own words are not kept by the extraction), and the part before its first heading under
// "(intro)". The Reader names them in words (retainer-2 #16, #45); a book's own titles are left as they are.
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { ReaderGuideSectionDto, ReadingPathDto, ReadingPathSectionDto } from "../../api/dto";
import { findJargon } from "../../copy/denyList";
import { GuideRail, type GuideRailProps } from "./GuideRail";
import { ReadingPathCard } from "./ReadingPathCard";
import { sectionWords } from "./readerShared";
import { crumbLabel } from "./sideBySide";

const { api } = vi.hoisted(() => ({ api: { readerReadingPath: vi.fn() } }));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

afterEach(cleanup);

// The elevator sample's sections, as its extraction stores them.
const LABELS = ["(intro)", "modeling-the-elevator-problem", "more-than-one-elevator", "the-real-world-case", "references", "external-links"];
const WORDS = ["Introduction", "Modeling the elevator problem", "More than one elevator", "The real world case", "References", "External links"];

it("UX-24: a stored slug reads as words, with no punctuation", () => {
  expect(LABELS.map(sectionWords)).toEqual(WORDS);
  for (const words of WORDS) expect(findJargon(words)).toEqual([]);
});

it("UX-24: a book's own section titles are left as they are", () => {
  for (const title of ["7.1 Symmetric matrices and variance", "5.4 Mixtures", "§5.A", "Section 3", "Chapter 2: Limits", "Mixtures", "3"]) {
    expect(sectionWords(title)).toBe(title);
  }
});

function guideSection(id: string, label: string, spanId: string): ReaderGuideSectionDto {
  return { id, label, startSpanId: spanId, endSpanId: spanId, spanIds: [spanId], question: null, suggestedPassages: [] };
}

function guideProps(sections: ReaderGuideSectionDto[], current: ReaderGuideSectionDto): GuideRailProps {
  const noop = () => undefined;
  return {
    visible: true, extractionId: "ext", offline: false,
    guidePlan: { sourceId: "src", extractionId: "ext", personalized: false, selectionBasis: "", sections, pendingDiagnosisAttemptIds: [], goalContext: null },
    guideLoading: false, currentGuideSection: current, currentSectionProgress: 0, currentQuestionOpen: false,
    boundaryChecksAvailable: false, authoringSections: [], revealedSections: [], completedSections: [],
    annotatedSpans: new Set(), openQuestionSections: [], setDismissedSections: noop, jumpToSpan: noop,
    revealSection: noop, completeSection: noop, onError: noop, boundaryBlock: null, boundarySkipped: false,
    setBoundarySkipped: noop, boundaryAnswered: false, setBoundaryAnswered: noop, boundaryResponse: "",
    setBoundaryResponse: noop, boundarySubmitted: false, setBoundarySubmitted: noop, questionControl: null,
    sendQuestionControl: noop, disposition: null, chooseDisposition: noop,
  } as unknown as GuideRailProps;
}

it("UX-24: the Guide's contents and its section card name the page's sections in words (retainer-2 #16)", () => {
  const sections = LABELS.map((label, index) => guideSection(`u${index + 1}`, label, `s${index + 1}`));
  const { container } = render(<GuideRail {...guideProps(sections, sections[1])} />);
  for (const words of WORDS) expect(screen.getAllByText(words).length).toBeGreaterThan(0);
  for (const label of LABELS) expect(container.textContent).not.toContain(label);
  expect(container.innerHTML).not.toMatch(/elevator-problem|external-links/);
});

it("UX-24: the reading path lists the page's sections in words", async () => {
  const section = (sectionId: string, title: string): ReadingPathSectionDto => ({
    sectionId, title, startSpanId: "s1", label: "core", chip: "core", reason: "the main idea", reasonBy: "code",
    override: null, effectiveLabel: "core", exercise: null, words: 300, learningObjectIds: [],
  });
  const path: ReadingPathDto = {
    extractionId: "ext", status: "ready", depth: "get_the_idea", depthLabel: "get the idea", depthOrigin: "guide",
    intent: null, depths: [{ id: "get_the_idea", label: "get the idea", means: "definitions" }], goal: null, goalLine: "",
    sections: LABELS.map((label, index) => section(`u${index + 1}`, label)),
    next: { text: "Next: read (intro) · about 1 min of reading", sectionId: "u1", spanId: "s1", exercise: null, minutes: 1 },
  } as unknown as ReadingPathDto;
  api.readerReadingPath.mockResolvedValue(path);
  const { container } = render(<ReadingPathCard extractionId="ext" onJump={vi.fn()} onTryExercise={vi.fn()} onError={vi.fn()} />);
  await screen.findByRole("button", { name: "Modeling the elevator problem" });
  for (const words of WORDS.slice(1)) expect(screen.getByRole("button", { name: words })).toBeTruthy();
  expect(within(container).getByText("Next: read Introduction · about 1 min of reading")).toBeTruthy();
  for (const label of LABELS) expect(container.textContent).not.toContain(label);
});

it("UX-24: the side-by-side button names the other page's section in words (retainer-2 #45)", () => {
  expect(crumbLabel({ sourceTitle: "Wikipedia Elevator Paradox", title: "modeling-the-elevator-problem" }))
    .toBe("side by side with Wikipedia Elevator Paradox Modeling the elevator problem");
  expect(crumbLabel({ sourceTitle: "Axler", title: "5.A Invariant subspaces" })).toBe("side by side with Axler §5.A");
});
