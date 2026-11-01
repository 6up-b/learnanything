// Curriculum C3 (spec_deliverable_curriculum_v1 §5.2; Codex review F5): a syllabus in the library
// is attached whole as a deliverable's scope input from the scope panel: the panel sends a passage
// input naming the deliverable and the syllabus's reading with an empty selection (the server reads
// every span of it and records them).
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { DeliverableScopeDto } from "../../api/dto";
import { findJargon } from "../../copy/denyList";
import { DeliverableScopePanel, SCOPE_COPY } from "./DeliverableScope";

const { api } = vi.hoisted(() => ({ api: {
  curriculumSetScope: vi.fn(), curriculumScope: vi.fn(), curriculumScopeDecide: vi.fn(), curriculumSetDepth: vi.fn(),
} }));
vi.mock("../../api/client", () => ({ api }));

const SCOPE: DeliverableScopeDto = {
  goalId: "goal_d", title: "my midterm", sentence: "only my midterm", kind: "exam", dueAt: null, depth: "fluency",
  topics: [{ learningObjectId: "lo_eigen", title: "Eigenvalues", phrase: "eigenvalues" }],
  unmatched: [], inputs: [], subjectId: "linear-algebra", subjects: [],
  resolution: { id: "dsr_1", origin: "resolver", model: "fake", createdAt: "2026-11-01T09:00:00Z", facetScope: {} },
  syllabi: [{ extractionId: "ext_syl", title: "Course syllabus" }],
};

beforeEach(() => {
  for (const fn of Object.values(api)) fn.mockReset();
});

afterEach(() => cleanup());

it("attaches a whole syllabus to this deliverable as a passage input with an empty selection", async () => {
  const resolved = { ...SCOPE, inputs: [{ id: "dsi_2", kind: "passage", text: null, extractionId: "ext_syl",
    createdAt: "2026-11-01T09:05:00Z" }] };
  api.curriculumSetScope.mockResolvedValue({ status: "ready", message: null, scope: resolved });
  const onChanged = vi.fn();
  const { container } = render(<DeliverableScopePanel scope={SCOPE} onChanged={onChanged} onError={vi.fn()} />);
  expect(container.querySelector("[data-deliverable-syllabus]")).not.toBeNull();
  const submit = screen.getByRole("button", { name: SCOPE_COPY.readSyllabus });
  expect((submit as HTMLButtonElement).disabled).toBe(true);  // nothing chosen yet
  fireEvent.change(screen.getByLabelText(SCOPE_COPY.syllabus), { target: { value: "ext_syl" } });
  await act(async () => { fireEvent.click(submit); });
  expect(api.curriculumSetScope).toHaveBeenCalledTimes(1);
  expect(api.curriculumSetScope).toHaveBeenCalledWith({ goalId: "goal_d", kind: "passage", extractionId: "ext_syl",
    spanIds: [] });
  expect(onChanged).toHaveBeenCalledWith(resolved);
});

it("says why it could not read the syllabus (the server refused it)", async () => {
  api.curriculumSetScope.mockRejectedValue(new Error("This page is protected exam material"));
  const onError = vi.fn();
  render(<DeliverableScopePanel scope={SCOPE} onChanged={vi.fn()} onError={onError} />);
  fireEvent.change(screen.getByLabelText(SCOPE_COPY.syllabus), { target: { value: "ext_syl" } });
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: SCOPE_COPY.readSyllabus })); });
  expect(onError).toHaveBeenCalledTimes(1);
});

it("offers no syllabus picker when the library has none (C0b's panel)", () => {
  const { syllabi: _unused, ...none } = SCOPE;
  const { container } = render(<DeliverableScopePanel scope={none} onChanged={vi.fn()} onError={vi.fn()} />);
  expect(container.querySelector("[data-deliverable-syllabus]")).toBeNull();
});

it("words the picker plainly", () => {
  const copy = [SCOPE_COPY.syllabus, SCOPE_COPY.chooseSyllabus, SCOPE_COPY.readSyllabus, SCOPE_COPY.syllabusTitle].join(" ");
  expect(findJargon(copy)).toEqual([]);
});
