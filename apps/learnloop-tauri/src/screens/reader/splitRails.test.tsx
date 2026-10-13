// RW1a's rail split: each tab is its own component, mounted hidden when not
// the active tab (so their state and the rail's scroll clamp survive tab
// switches), and each renders on its own props.
import { createRef } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { AskRail, type AskRailProps } from "./AskRail";
import { GuideRail, type GuideRailProps } from "./GuideRail";
import { NotesRail, type NotesRailProps } from "./NotesRail";

vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));
afterEach(cleanup);

const noop = () => undefined;

function askProps(over: Partial<AskRailProps> = {}): AskRailProps {
  return {
    visible: true, enabled: true, inquiry: true, offline: false, busy: false, blocks: [], activeSpan: "s1",
    activeBlock: null, selection: null, parentExchange: null, setParentExchange: noop, answerMode: "answer_directly",
    changeAnswerMode: noop, question: "", setQuestion: noop, askComposerVersion: 0, askComposerRef: createRef(),
    ask: noop, history: [], visibleAskHistory: [], normalizedAskFind: "", collapsedAskIds: new Set(),
    setCollapsedAskIds: noop, askFindOpen: false, setAskFindOpen: noop, askFindQuery: "", setAskFindQuery: noop,
    askFindInputRef: createRef(), jumpToSpan: noop, ...over,
  } as AskRailProps;
}

it("the Ask rail names clarification threads when inquiry is on and previous asks when off", () => {
  const { rerender } = render(<AskRail {...askProps()} />);
  expect(screen.getByText("Clarification threads")).toBeTruthy();
  rerender(<AskRail {...askProps({ inquiry: false })} />);
  expect(screen.getByText("Previous asks")).toBeTruthy();
});

it("a hidden rail stays mounted but out of view", () => {
  const { container } = render(<AskRail {...askProps({ visible: false })} />);
  expect((container.firstElementChild as HTMLElement).style.display).toBe("none");
  expect(screen.getByPlaceholderText("ask about this passage…")).toBeTruthy();
});

it("the Ask rail submits through its ask callback", () => {
  const ask = vi.fn();
  render(<AskRail {...askProps({ ask, question: "Why?" })} />);
  fireEvent.click(screen.getByRole("button", { name: "ask ↵" }));
  expect(ask).toHaveBeenCalledTimes(1);
});

it("the Guide rail renders its section and contents from the plan", () => {
  const section = {
    id: "u1", label: "Mixtures", startSpanId: "s1", endSpanId: "s2", spanIds: ["s1", "s2"],
    question: null, suggestedPassages: [],
  };
  const props = {
    visible: true, extractionId: "ext", offline: false,
    guidePlan: { sections: [section, { ...section, id: "u2", label: "Sums" }] }, guideLoading: false,
    currentGuideSection: section, currentSectionProgress: 0.5, currentQuestionOpen: false,
    boundaryChecksAvailable: true, authoringSections: [], revealedSections: [], completedSections: [],
    annotatedSpans: new Set(), openQuestionSections: [], setDismissedSections: noop, jumpToSpan: vi.fn(),
    revealSection: noop, completeSection: noop, onError: noop, boundaryBlock: null, boundarySkipped: false,
    setBoundarySkipped: noop, boundaryAnswered: false, setBoundaryAnswered: noop, boundaryResponse: "",
    setBoundaryResponse: noop, boundarySubmitted: false, setBoundarySubmitted: noop, questionControl: null,
    sendQuestionControl: noop, disposition: null, chooseDisposition: noop,
  } as unknown as GuideRailProps;
  render(<GuideRail {...props} />);
  expect(screen.getByText("Reading guide")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: /Sums/ }));
  expect(props.jumpToSpan).toHaveBeenCalledWith("s1");
});

it("the Notes rail shows the capture hint without a selection and the palette with one", () => {
  const base = {
    visible: true, offline: false, busy: false, pdfSurfaceActive: false, activeSpan: null, activeBlock: null,
    selection: null, selectionActions: [], editingCapture: false, setEditingCapture: noop, clearSelection: noop,
    editCaptureText: noop, resetCaptureText: noop, note: "", setNote: noop, captureHighlight: noop,
    invokePreset: vi.fn(), importExercise: noop, exerciseImport: null, setExerciseImport: noop,
    exerciseImportActive: false, authoringOpen: false, setAuthoringOpen: noop, setAuthoringSpanId: noop,
    authoringQuote: "", setAuthoringQuote: noop, authoredQuestion: "", setAuthoredQuestion: noop,
    authoredAnswer: "", setAuthoredAnswer: noop, authoredCardId: null, setAuthoredCardId: noop,
    authoredStatus: undefined, authoringBusy: false, saveOwnQuestion: noop, coach: null, setCoach: noop,
    runCoach: noop, requests: [], requestLoadError: null, refreshRequests: noop, synthesizedObjects: new Map(),
    openProposalIds: new Set(), proposalCount: 0, expandedRequests: new Set(), setExpandedRequests: noop,
    retryRequest: noop, decideProposal: noop, jumpToSpan: noop, arc: null, pauseArc: noop, setArcPolicy: noop,
    annotations: [], jumpToAnnotation: noop, reanchorAnnotation: noop, manualAnchorToSelection: noop,
    reanchorNotes: {}, editingAnnotationId: null, setEditingAnnotationId: noop, editingAnnotationText: "",
    setEditingAnnotationText: noop, saveAnnotationEdit: noop, deleteAnnotation: noop,
  } as unknown as NotesRailProps;
  const { rerender } = render(<NotesRail {...base} />);
  expect(screen.getByText(/select text to capture it/)).toBeTruthy();
  rerender(<NotesRail {...base} selection={{ spanId: "s1", quote: "A passage" }} />);
  fireEvent.click(screen.getByRole("button", { name: "test me later" }));
  expect(base.invokePreset).toHaveBeenCalledWith("test_me_later");
});
