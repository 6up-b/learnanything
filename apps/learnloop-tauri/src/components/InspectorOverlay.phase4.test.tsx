// UX Phase 4.1 (docs/specs/ux_learnloop_v1.md §7.4, §10 4.1): the inspector
// never shows the expected answer or the rubric for a question the learner
// has not answered: one never answered (no attempt but skips), or the one
// open on the practice screen right now. `[ui] practice_feedback = "classic"`
// restores the inspector exactly.
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { setAlgoConfig } from "../app/algoConfig";
import { InspectorOverlay } from "./InspectorOverlay";

const { api } = vi.hoisted(() => ({ api: { inspectEntity: vi.fn() } }));
vi.mock("../api/client", () => ({ api }));
vi.mock("../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <span>{value}</span> }));
vi.mock("./CardControls", () => ({ RungVariantActions: () => null }));
vi.mock("./KnowledgeModel", () => ({ CapabilityGridView: () => null }));
vi.mock("./recipeedit/RecipeTreeEditor", () => ({ RecipeTreeEditor: () => null }));
vi.mock("./ConceptAnimationSection", () => ({ ConceptAnimationSection: () => null }));

const ANSWER = "Expand along the first row: det(A) = -3.";
const CRITERION = "Expands along a row with the right signs";

function practiceItem(attempts: Array<{ attemptType: string }>) {
  return {
    kind: "practice_item",
    id: "pi_det",
    detail: {
      id: "pi_det", learningObjectId: "lo_det", learningObjectTitle: "Determinants", subject: null, subjects: [],
      practiceMode: "constructed_response", attemptTypesAllowed: [], difficulty: null,
      presentation: { practiceItemId: "pi_det", blocks: [{ kind: "prompt", markdown: "Compute det(A).", label: null }] },
      prompt: "Compute det(A).", expectedAnswer: ANSWER, hints: [], hintPolicy: { maxUsefulHints: 0 },
      rubric: { maxPoints: 2, criteria: [{ id: "expansion", description: CRITERION, points: 2 }], fatalErrors: [] },
      candidateErrorTypes: [], tags: [], sourceRefs: [], evidenceFacets: [], evidenceWeights: {},
      state: null, scheduler: null, mastery: null,
      attempts: attempts.map((attempt, index) => ({
        id: `att_${index}`, rubricScore: 1, maxPoints: 2, attemptType: attempt.attemptType, createdAt: "2026-10-01T00:00:00Z",
        hintsUsed: 0, errorType: null, surpriseDirection: null
      }))
    }
  };
}

beforeEach(() => {
  setAlgoConfig({ ui: { practiceFeedback: "simple" } });
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  setAlgoConfig(undefined);
});

function open(answeringItemId: string | null = null) {
  render(
    <InspectorOverlay entityId="pi_det" answeringItemId={answeringItemId} onClose={vi.fn()} onInspect={vi.fn()} onError={vi.fn()} />
  );
}

it("hides the expected answer and the rubric of a question never answered", async () => {
  api.inspectEntity.mockResolvedValue(practiceItem([]));
  open();
  expect(await screen.findByText("Compute det(A).")).toBeTruthy();
  expect(screen.queryByText(ANSWER)).toBeNull();
  expect(screen.queryByText(new RegExp(CRITERION))).toBeNull();
  expect(screen.getByText(/once you've answered this question/i)).toBeTruthy();
});

it("a skip is not an answer", async () => {
  api.inspectEntity.mockResolvedValue(practiceItem([{ attemptType: "skip" }]));
  open();
  await screen.findByText("Compute det(A).");
  expect(screen.queryByText(ANSWER)).toBeNull();
});

it("hides them for the question open on the practice screen, even one answered before", async () => {
  api.inspectEntity.mockResolvedValue(practiceItem([{ attemptType: "independent_attempt" }]));
  open("pi_det");
  await screen.findByText("Compute det(A).");
  expect(screen.queryByText(ANSWER)).toBeNull();
  expect(screen.queryByText(new RegExp(CRITERION))).toBeNull();
});

it("shows them once the question has been answered and is not open", async () => {
  api.inspectEntity.mockResolvedValue(practiceItem([{ attemptType: "independent_attempt" }]));
  open();
  expect(await screen.findByText(ANSWER)).toBeTruthy();
  expect(screen.getByText(new RegExp(CRITERION))).toBeTruthy();
});

it("classic restores the inspector exactly", async () => {
  setAlgoConfig({ ui: { practiceFeedback: "classic" } });
  api.inspectEntity.mockResolvedValue(practiceItem([]));
  open("pi_det");
  expect(await screen.findByText(ANSWER)).toBeTruthy();
});
