// UX-67 (the live walk partread-2, steps 48 and 53): a long answer looked cut off in the answer box (the learner pasted
// a second copy into its middle), and once they typed, the optional confidence control appeared where Submit had been,
// so a click meant for Submit chose a confidence. The answer box takes the screen's height, not what is left under a
// long question; and nothing that appears while the learner types appears above Submit.
import type { ComponentProps } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import { PracticeScreen } from "./PracticeScreen";

const { api } = vi.hoisted(() => ({ api: {
  getPracticeItem: vi.fn(), getProbeContract: vi.fn(), recoverPracticeSubmission: vi.fn(),
  acknowledgePracticeSubmission: vi.fn(), savePracticeDraft: vi.fn(), submitAttempt: vi.fn(),
  getNextProbeItem: vi.fn(), skipPracticeItem: vi.fn(), stopProbeDiagnosing: vi.fn(),
  recordSelfGradeDisclosure: vi.fn(), recordHintReveal: vi.fn(),
  requestHint: vi.fn(), hintJob: vi.fn(), cancelHint: vi.fn(), answerDiscriminating: vi.fn(), setHelpStyle: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../render/MathLiveEditor", () => ({
  MathLiveEditor: (props: { value: string; onChange: (value: string) => void; disabled: boolean; maxHeight?: number }) => (
    <textarea aria-label="answer" data-max-height={props.maxHeight ?? ""} value={props.value} disabled={props.disabled}
      onChange={(event) => props.onChange(event.target.value)} />
  )
}));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("../components/CardControls", () => ({ CardControls: () => <span>card controls</span> }));

const ITEM_ID = "pi_hunt";

function item() {
  return {
    id: ITEM_ID, learningObjectId: "lo_diag", learningObjectTitle: "Build a diagonalization", subject: "linear_algebra",
    subjects: ["linear_algebra"], practiceMode: "constructed_response", attemptTypesAllowed: ["independent_attempt", "hinted_attempt"],
    presentation: { practiceItemId: ITEM_ID, blocks: [{ kind: "prompt", markdown: "Check the diagonalization of [[1,2],[2,1]].", label: null }] },
    prompt: "Check the diagonalization of [[1,2],[2,1]].", expectedAnswer: "It holds.",
    hints: [], hintPolicy: { maxUsefulHints: 0 }, candidateErrorTypes: [], tags: [], sourceRefs: [],
    attempts: [], evidenceFacets: [], evidenceWeights: {},
    rubric: { maxPoints: 4, criteria: [{ id: "value", description: "Checks each product", points: 4 }], fatalErrors: [] },
    mastery: null, elicitation: null
  };
}

function props(): ComponentProps<typeof PracticeScreen> {
  return {
    session: { sessionId: "s1" } as ComponentProps<typeof PracticeScreen>["session"],
    practiceItemId: ITEM_ID, gradingReady: true, gradingProvider: "codex",
    onFeedback: vi.fn(), onBlockEnd: vi.fn(), onContinueDiagnostic: vi.fn(), onBack: vi.fn(),
    onCheckpointCleared: vi.fn(), onDraftSaved: vi.fn(), onTeachBackActive: vi.fn(),
    onAskAvailabilityChange: vi.fn(), onInspect: vi.fn(), onAsk: vi.fn(), onError: vi.fn()
  };
}

beforeEach(() => {
  for (const mock of Object.values(api)) mock.mockReset();
  api.getProbeContract.mockResolvedValue({ version: 1, active: false });
  api.savePracticeDraft.mockResolvedValue({});
  api.getPracticeItem.mockResolvedValue(item());
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  setAlgoConfig(undefined);
});

const LONG_ANSWER = Array.from({ length: 40 }, (_, index) => `Line ${index + 1}: P D P^{-1} checked entry by entry.`).join("\n");

for (const mode of ["simple", "classic"] as const) {
  describe(`the answer box and Submit (${mode} card)`, () => {
    beforeEach(() => setAlgoConfig({ ui: { practiceFeedback: mode } }));

    it("the confidence control appears below Submit once the learner types: Submit stays where it was", async () => {
      render(<PracticeScreen {...props()} />);
      const answer = await screen.findByRole("textbox", { name: "answer" });
      await waitFor(() => expect(api.getProbeContract).toHaveBeenCalled());
      const submit = screen.getAllByRole("button").find((button) => (button.textContent ?? "").includes("Submit")) as HTMLElement;
      expect(submit).toBeTruthy();
      expect(screen.queryByRole("group", { name: /How likely is this answer to be correct/ })).toBeNull();
      fireEvent.change(answer, { target: { value: LONG_ANSWER } });
      const group = await screen.findByRole("group", { name: /How likely is this answer to be correct/ });
      // Submit comes first: the control that appears is placed after it, never between the box and it.
      expect(submit.compareDocumentPosition(group) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
      expect(submit.isConnected).toBe(true);
    });
  });
}

describe("the answer box's height", () => {
  it("a long question leaves the box its screen's height, not the floor left under the question", async () => {
    setAlgoConfig({ ui: { practiceFeedback: "simple" } });
    // An 800-pixel window whose scrolling area shows 764 of them; a long question puts the box's top at 700.
    vi.spyOn(window, "innerHeight", "get").mockReturnValue(800);
    vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockImplementation(function (this: HTMLElement) {
      return this.classList.contains("screen-scroll") ? 764 : 0;
    });
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockImplementation(function (this: HTMLElement) {
      const top = this.classList.contains("answer-editor-slot") ? 700 : 0;
      return { top, bottom: top, left: 0, right: 0, width: 0, height: 0, x: 0, y: top, toJSON: () => ({}) } as DOMRect;
    });
    render(<PracticeScreen {...props()} />);
    const answer = await screen.findByRole("textbox", { name: "answer" });
    fireEvent.change(answer, { target: { value: LONG_ANSWER } });
    // Before: max(140, 800 − 700 − what sits under it − the key bar − 28) = the 140-pixel floor, about four lines.
    await waitFor(() => expect(Number(answer.getAttribute("data-max-height"))).toBe(764 - 28));
  });
});
