// Daily-loop DL2: a served "Check once" is a check on your own (Reader §9.3
// item 10, D42, D46, G61). The cold banner shows; help is never blocked, and
// the first hint press opens the ladder whose header states the consequence
// (nothing revealed, no dialog), the next press or its button takes the hint;
// the header names the book and nothing that locates the exercise (no number,
// page, section, link or why) until feedback. Without `intentCheck` the card
// is unchanged (PracticeScreen.adaptiveOff's byte snapshots pin that too).
import type { ComponentProps } from "react";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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

const ITEM_ID = "pi_ex";
const BANNER = "A check on your own. Help is still here — using it makes this practice with help.";
const HELP_HEADER = "Taking any help makes this attempt practice with help, not a check on your own.";

function item(overrides: Record<string, unknown> = {}) {
  return {
    id: ITEM_ID, learningObjectId: "lo_mix", learningObjectTitle: "Mixture distributions", subject: "probability",
    subjects: ["probability"], practiceMode: "constructed_response", attemptTypesAllowed: ["independent_attempt", "hinted_attempt"],
    presentation: { practiceItemId: ITEM_ID, blocks: [{ kind: "prompt", markdown: "Find the CDF.", label: null }] },
    prompt: "Find the CDF.", expectedAnswer: "F(x) = ...",
    hints: ["Split the integral at the mixing point."],
    hintPolicy: { maxUsefulHints: 1 }, candidateErrorTypes: [], tags: [],
    sourceRefs: [{ refId: "ref_1", refType: "source_span", displayName: "Blitzstein", locator: "p. 212, §5.4", path: null, quote: null }],
    attempts: [], evidenceFacets: [], evidenceWeights: {},
    rubric: { maxPoints: 4, criteria: [{ id: "value", description: "Correct CDF", points: 4 }], fatalErrors: [] },
    mastery: { mean: 0.5, variance: 0.18 }, elicitation: null,
    canonicalExercise: {
      sourceId: "src_b", revisionId: "rev_1", extractionId: "ex_1", spanIds: ["sp_1"], label: "Exercise 5.19",
      relation: "verbatim", sourceTitle: "Blitzstein & Hwang", keyStatus: "verified", keyLabel: "answer key checked",
      authorship: "book"
    },
    ...overrides
  };
}

const CHECK = {
  kind: "check_once", commitmentId: "c_1", dueSince: "2026-10-19T09:00:00Z", dateSource: "test_me_later_days",
  banner: BANNER, helpHeader: HELP_HEADER, locatorsHidden: true, restoration: null
};

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

async function open(mode: "simple" | "classic", overrides: Record<string, unknown> = {}) {
  setAlgoConfig({ ui: { practiceFeedback: mode } });
  api.getPracticeItem.mockResolvedValue(item(overrides));
  const view = render(<PracticeScreen {...props()} />);
  await screen.findByRole("textbox", { name: "answer" });
  await waitFor(() => expect(api.getProbeContract).toHaveBeenCalled());
  return view;
}

for (const mode of ["simple", "classic"] as const) {
  it(`shows the cold banner and locates nothing during the check (${mode})`, async () => {
    const view = await open(mode, { intentCheck: CHECK });
    expect(screen.getByTestId("intent-check-banner").textContent).toBe(BANNER);
    const text = view.container.textContent ?? "";
    // G61: the book's name, and no exercise number, page, section, link or why.
    expect(text).toContain("From Blitzstein & Hwang");
    for (const locator of ["Exercise 5.19", "p. 212", "§5.4", "answer key checked", "why"]) {
      expect(text).not.toContain(locator);
    }
    expect(view.container.querySelectorAll("a[href]")).toHaveLength(0);
  });

  it(`help is never blocked: the ladder states the consequence first, then the hint is taken (${mode})`, async () => {
    const view = await open(mode, { intentCheck: CHECK });
    fireEvent.change(screen.getByRole("textbox", { name: "answer" }), { target: { value: "split it" } });
    await act(async () => {
      fireEvent.keyDown(window, { key: "h", ctrlKey: true });
    });
    expect(screen.getByTestId("intent-check-help").textContent).toContain(HELP_HEADER);
    expect(screen.queryByText("Split the integral at the mixing point.")).toBeNull();
    expect(api.recordHintReveal).not.toHaveBeenCalled();
    expect(view.container.querySelector("[role=dialog]")).toBeNull();
    await act(async () => {
      fireEvent.click(screen.getByText("Take a hint"));
    });
    await screen.findByText("Split the integral at the mixing point.");
    expect(api.recordHintReveal).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId("intent-check-help")).toBeNull();
  });
}

it("the hint key again takes the hint (choose, then take)", async () => {
  await open("simple", { intentCheck: CHECK });
  await act(async () => {
    fireEvent.keyDown(window, { key: "h", ctrlKey: true });
  });
  expect(screen.getByTestId("intent-check-help")).toBeTruthy();
  await act(async () => {
    fireEvent.keyDown(window, { key: "h", ctrlKey: true });
  });
  await screen.findByText("Split the integral at the mixing point.");
});

it("an ordinary item keeps its locators and its direct hint", async () => {
  const view = await open("classic");
  expect(screen.queryByTestId("intent-check-banner")).toBeNull();
  expect(view.container.textContent).toContain("Exercise 5.19");
  await act(async () => {
    fireEvent.keyDown(window, { key: "h", ctrlKey: true });
  });
  await screen.findByText("Split the integral at the mixing point.");
  expect(screen.queryByTestId("intent-check-help")).toBeNull();
});
