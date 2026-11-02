// followups-nov1c D: the Reader's selection action "scope my deliverable from this
// passage" sends the selection to the existing scope input (curriculum.set_scope, kind
// "passage", its spans); honest copy; not offered on a protected selection, and the
// server's refusal of an exam-role or protected passage reaches the learner in its words.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { NotesRail, type NotesRailProps } from "./NotesRail";
import { SCOPE_FROM_PASSAGE_COPY, ScopeFromPassage } from "./ScopeFromPassage";

const { api } = vi.hoisted(() => ({ api: { curriculumDeliverables: vi.fn(), curriculumSetScope: vi.fn() } }));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../../render/MarkdownMath", () => ({ MarkdownMath: ({ value }: { value: string }) => <div>{value}</div> }));

beforeEach(() => { for (const mock of Object.values(api)) mock.mockReset(); });
afterEach(cleanup);

const noop = () => undefined;

function scope(goalId: string, title: string, topics = 0) {
  return {
    goalId, title, sentence: "my midterm", kind: "exam", dueAt: null, depth: null,
    topics: Array.from({ length: topics }, (_, i) => ({ learningObjectId: `lo_${i}`, title: `T${i}`, phrase: "p" })),
    unmatched: [], receipt: null, syllabi: [], subjects: [], subjectId: null,
  };
}

async function settle() {
  await act(async () => { for (let i = 0; i < 4; i += 1) await Promise.resolve(); });
}

async function mount(props: Partial<Parameters<typeof ScopeFromPassage>[0]> = {}) {
  const onError = vi.fn();
  const utils = render(<ScopeFromPassage extractionId="ext_book" spanIds={["s2", "s3"]} onError={onError} {...props} />);
  await settle();
  return { ...utils, onError };
}

it("scopes the one deliverable from the selected passage through set_scope's passage input", async () => {
  api.curriculumDeliverables.mockResolvedValueOnce({ deliverables: [scope("g1", "midterm")] });
  api.curriculumSetScope.mockResolvedValueOnce({ status: "ready", message: null, scope: scope("g1", "midterm", 3) });
  await mount();
  expect(screen.getByText(SCOPE_FROM_PASSAGE_COPY.meaning)).toBeTruthy();  // honest: what the model reads
  fireEvent.click(screen.getByRole("button", { name: SCOPE_FROM_PASSAGE_COPY.action }));
  await settle();
  expect(api.curriculumSetScope).toHaveBeenCalledWith({
    goalId: "g1", kind: "passage", extractionId: "ext_book", spanIds: ["s2", "s3"], context: { from: "reader_selection" },
  });
  expect(document.querySelector("[data-scope-from-passage-notice]")?.textContent).toBe("For midterm: 3 topics from your books");
});

it("says the passage joins earlier scope inputs and the scope is updated, not only added to (Codex review F3)", async () => {
  // A deliverable that already has a syllabus and an earlier passage as scope inputs: the
  // resolver rereads them all with the new passage and replaces the scope (here it drops
  // topics), so the copy never promises "only this passage" or "adds".
  const earlier = {
    ...scope("g1", "midterm", 3),
    inputs: [
      { id: "dsi_1", kind: "passage", text: null, extractionId: "ext_syllabus", createdAt: "2026-10-30T00:00:00Z" },
      { id: "dsi_2", kind: "passage", text: null, extractionId: "ext_book", createdAt: "2026-10-31T00:00:00Z" },
    ],
  };
  api.curriculumDeliverables.mockResolvedValueOnce({ deliverables: [earlier] });
  api.curriculumSetScope.mockResolvedValueOnce({ status: "ready", message: null, scope: scope("g1", "midterm", 1) });
  await mount({ spanIds: ["s9"] });
  const meaning = SCOPE_FROM_PASSAGE_COPY.meaning;
  expect(screen.getByText(meaning)).toBeTruthy();
  expect(meaning).not.toMatch(/only it/);
  expect(meaning).toMatch(/earlier passages/);
  expect(meaning).toMatch(/drop/);
  fireEvent.click(screen.getByRole("button", { name: SCOPE_FROM_PASSAGE_COPY.action }));
  await settle();
  // The scope shown is the resolver's replacement (1 topic), not the earlier 3 plus more.
  expect(document.querySelector("[data-scope-from-passage-notice]")?.textContent).toBe("For midterm: 1 topic from your books");
});

it("names each deliverable when there are several", async () => {
  api.curriculumDeliverables.mockResolvedValueOnce({ deliverables: [scope("g1", "midterm"), scope("g2", "project")] });
  api.curriculumSetScope.mockResolvedValueOnce({ status: "ready", message: null, scope: scope("g2", "project", 1) });
  await mount();
  expect(screen.getByRole("button", { name: SCOPE_FROM_PASSAGE_COPY.actionFor("midterm") })).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: SCOPE_FROM_PASSAGE_COPY.actionFor("project") }));
  await settle();
  expect(api.curriculumSetScope.mock.calls[0][0].goalId).toBe("g2");
});

it("an exam-role or protected passage is refused by the server's guard, in its words", async () => {
  api.curriculumDeliverables.mockResolvedValueOnce({ deliverables: [scope("g1", "midterm")] });
  const refusal = "That passage is exam material: LearnLoop never sends it to a model.";
  api.curriculumSetScope.mockRejectedValueOnce(new Error(refusal));
  const { onError } = await mount();
  fireEvent.click(screen.getByRole("button", { name: SCOPE_FROM_PASSAGE_COPY.action }));
  await settle();
  expect(onError).toHaveBeenCalledTimes(1);
  expect(String(onError.mock.calls[0][0])).toContain("exam material");
  expect(document.querySelector("[data-scope-from-passage-notice]")).toBeNull();
});

it.each([
  ["the curriculum is off", () => api.curriculumDeliverables.mockRejectedValueOnce(new Error("curriculum_disabled")), {}],
  ["there is no deliverable", () => api.curriculumDeliverables.mockResolvedValueOnce({ deliverables: [] }), {}],
  ["the selection has no spans (never a whole document)",
    () => api.curriculumDeliverables.mockResolvedValueOnce({ deliverables: [scope("g1", "midterm")] }), { spanIds: [] }],
])("offers nothing when %s", async (_name, arrange, props) => {
  arrange();
  await mount(props);
  expect(document.querySelector("[data-scope-from-passage]")).toBeNull();
  expect(api.curriculumSetScope).not.toHaveBeenCalled();
});

function railProps(over: Partial<NotesRailProps>): NotesRailProps {
  return {
    visible: true, offline: false, busy: false, pdfSurfaceActive: false, activeSpan: null, activeBlock: null,
    selection: { spanId: "s1", quote: "A passage" }, selectionActions: [], editingCapture: false,
    setEditingCapture: noop, clearSelection: noop, editCaptureText: noop, resetCaptureText: noop, note: "",
    setNote: noop, captureHighlight: noop, invokePreset: noop, importExercise: noop, exerciseImport: null,
    setExerciseImport: noop, exerciseImportActive: false, authoringOpen: false, setAuthoringOpen: noop,
    setAuthoringSpanId: noop, authoringQuote: "", setAuthoringQuote: noop, authoredQuestion: "",
    setAuthoredQuestion: noop, authoredAnswer: "", setAuthoredAnswer: noop, authoredCardId: null,
    setAuthoredCardId: noop, authoredStatus: undefined, authoringBusy: false, saveOwnQuestion: noop, coach: null,
    setCoach: noop, runCoach: noop, requests: [], requestLoadError: null, refreshRequests: noop,
    synthesizedObjects: new Map(), openProposalIds: new Set(), proposalCount: 0, expandedRequests: new Set(),
    setExpandedRequests: noop, retryRequest: noop, decideProposal: noop, jumpToSpan: noop, arc: null,
    pauseArc: noop, setArcPolicy: noop, annotations: [], jumpToAnnotation: noop, reanchorAnnotation: noop,
    manualAnchorToSelection: noop, reanchorNotes: {}, editingAnnotationId: null, setEditingAnnotationId: noop,
    editingAnnotationText: "", setEditingAnnotationText: noop, saveAnnotationEdit: noop, deleteAnnotation: noop,
    scopeAction: <div data-scope-slot="">scope action</div>, ...over,
  } as unknown as NotesRailProps;
}

it("the Notes rail offers it with the other model actions, never on a protected selection or offline", () => {
  const { rerender } = render(<NotesRail {...railProps({})} />);
  expect(document.querySelector("[data-scope-slot]")).not.toBeNull();
  rerender(<NotesRail {...railProps({ protectionMessage: "This passage is exam material." })} />);
  expect(document.querySelector("[data-scope-slot]")).toBeNull();
  rerender(<NotesRail {...railProps({ offline: true })} />);
  expect(document.querySelector("[data-scope-slot]")).toBeNull();
});
