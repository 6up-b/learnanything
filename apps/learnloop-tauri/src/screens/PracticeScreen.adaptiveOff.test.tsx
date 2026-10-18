// Adaptive hints H2b, G-H1 (spec_adaptive_hints_v1 §2 H9, §11): with
// `hints.adaptive_enabled = false` (the sidecar then sends no `hints` key in
// the app snapshot's config) the practice screen is byte-identical to the
// base, `main` at 5b2efaf24. The file snapshots under __snapshots__/ were
// written by THIS test run against that base's PracticeScreen, before H2b
// changed anything, and are compared byte for byte here: the plain card and
// the classic card, an item with authored hints and one with none, before
// and after Ctrl+H (twice). The hint RPCs of H2a are never called.
import type { ComponentProps } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import { PracticeScreen } from "./PracticeScreen";

const { api } = vi.hoisted(() => ({ api: {
  getPracticeItem: vi.fn(), getProbeContract: vi.fn(), recoverPracticeSubmission: vi.fn(),
  acknowledgePracticeSubmission: vi.fn(), savePracticeDraft: vi.fn(), submitAttempt: vi.fn(),
  getNextProbeItem: vi.fn(), skipPracticeItem: vi.fn(), submitDontKnow: vi.fn(), stopProbeDiagnosing: vi.fn(),
  recordSelfGradeDisclosure: vi.fn(), recordHintReveal: vi.fn(),
  requestHint: vi.fn(), hintJob: vi.fn(), cancelHint: vi.fn(), answerDiscriminating: vi.fn(), setHelpStyle: vi.fn()
} }));
vi.mock("../api/client", () => ({ api }));
vi.mock("@tauri-apps/api/window", () => ({ getCurrentWindow: () => ({ onCloseRequested: async () => vi.fn(), destroy: vi.fn() }) }));
vi.mock("../render/MathLiveEditor", () => ({
  MathLiveEditor: (props: { value: string; onChange: (value: string) => void; disabled: boolean; placeholder?: string }) => (
    <textarea aria-label="answer" placeholder={props.placeholder} value={props.value} disabled={props.disabled}
      onChange={(event) => props.onChange(event.target.value)} />
  )
}));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("../components/CardControls", () => ({ CardControls: () => <span>card controls</span> }));

const ITEM_ID = "pi_hints";

function item(overrides: Record<string, unknown> = {}) {
  return {
    id: ITEM_ID, learningObjectId: "lo_det", learningObjectTitle: "Determinants", subject: "linear_algebra",
    subjects: ["linear_algebra"], practiceMode: "constructed_response", attemptTypesAllowed: ["independent_attempt", "hinted_attempt"],
    presentation: { practiceItemId: ITEM_ID, blocks: [{ kind: "prompt", markdown: "Compute det(A).", label: null }] },
    prompt: "Compute det(A).", expectedAnswer: "det(A) = -3.",
    hints: ["Start with the first row.", "Watch the signs."],
    hintPolicy: { maxUsefulHints: 2 }, candidateErrorTypes: [], tags: [], sourceRefs: [],
    attempts: [], evidenceFacets: [], evidenceWeights: {},
    rubric: { maxPoints: 4, criteria: [{ id: "value", description: "Gets -3", points: 4 }], fatalErrors: [] },
    mastery: { mean: 0.5, variance: 0.18 }, elicitation: null,
    ...overrides
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
  api.recordHintReveal.mockResolvedValue({ version: 1, recorded: true, reason: null, assistId: "ha_1" });
  vi.stubGlobal("ResizeObserver", class { observe() {} disconnect() {} });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  setAlgoConfig(undefined);
});

async function frames(mode: "simple" | "classic", withHints: boolean): Promise<string> {
  // The app snapshot of an adaptive-off sidecar: no `hints` key at all.
  setAlgoConfig({ ui: { practiceFeedback: mode } });
  api.getPracticeItem.mockResolvedValue(withHints ? item() : item({ hints: [], hintPolicy: { maxUsefulHints: 0 } }));
  const view = render(<PracticeScreen {...props()} />);
  const answer = await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.getProbeContract).toHaveBeenCalled());
  fireEvent.change(answer, { target: { value: "expand along row 1" } });
  const shots = [view.container.innerHTML];
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
  if (withHints) await screen.findByText("Start with the first row.");
  shots.push(view.container.innerHTML);
  fireEvent.keyDown(window, { key: "h", ctrlKey: true });
  if (withHints) await screen.findByText("Watch the signs.");
  await new Promise((resolve) => setTimeout(resolve, 0));
  shots.push(view.container.innerHTML);
  cleanup();
  return shots.join("\n<!-- frame -->\n");
}

for (const mode of ["simple", "classic"] as const) {
  for (const withHints of [true, false]) {
    it(`is byte-identical to the base with adaptive hints off (${mode} card, ${withHints ? "authored hints" : "no hints"})`, async () => {
      const html = await frames(mode, withHints);
      await expect(html).toMatchFileSnapshot(`./__snapshots__/adaptiveOff.${mode}.${withHints ? "hints" : "nohints"}.html`);
      expect(api.requestHint).not.toHaveBeenCalled();
      expect(api.hintJob).not.toHaveBeenCalled();
      expect(api.cancelHint).not.toHaveBeenCalled();
      expect(api.setHelpStyle).not.toHaveBeenCalled();
      expect(api.recordHintReveal).toHaveBeenCalledTimes(withHints ? 2 : 0);
    });
  }
}
