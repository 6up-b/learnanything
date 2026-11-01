// Curriculum C3 (spec_deliverable_curriculum_v1 §9.1, §9.2): the syllabus role is offered where
// roles are chosen, with an honest line on what it does, and the deliverable's scope says which
// topics the learner's past papers test.
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { clear } from "../api/queryCache";
import type { DeliverableScopeDto } from "../api/dto";
import { findJargon } from "../copy/denyList";
import { DeliverableScopePanel, SCOPE_COPY } from "../screens/reader/DeliverableScope";
import { AddToCollectionPanel, SYLLABUS_ROLE_HINT } from "./AddToCollection";
import { roleLabel } from "./RewordConfirms";

const api = vi.hoisted(() => ({
  listSourceSets: vi.fn(),
  loadVault: vi.fn(),
  getSourceSet: vi.fn(),
  upsertSourceSet: vi.fn()
}));
vi.mock("../api/client", () => ({ api }));

beforeEach(() => {
  clear();
  for (const fn of Object.values(api)) fn.mockReset();
  api.listSourceSets.mockResolvedValue({ version: 1, sourceSets: [] });
  api.loadVault.mockResolvedValue({ vault: { subjects: ["la"] } });
});

afterEach(() => cleanup());

function panel(seedRole: string) {
  return render(
    <AddToCollectionPanel sourceId="src_syl" revisionId="rev_syl" scopeUnitIds={[]} seedRole={seedRole}
      onClose={vi.fn()} onAdded={vi.fn()} />
  );
}

it("offers the syllabus role and says what it does when it is chosen", async () => {
  const { container } = panel("syllabus");
  expect(await screen.findByText(SYLLABUS_ROLE_HINT)).toBeTruthy();
  expect(container.querySelector('[data-role-hint="syllabus"]')).not.toBeNull();
  expect(SYLLABUS_ROLE_HINT).toMatch(/never taught from/);
  expect(SYLLABUS_ROLE_HINT).toMatch(/never protected/);
  expect(findJargon(SYLLABUS_ROLE_HINT)).toEqual([]);
  expect(roleLabel("syllabus")).toBe("syllabus");
});

it("says nothing about a syllabus for another role", async () => {
  const { container } = panel("primary_textbook");
  await screen.findByText("role");
  expect(container.querySelector('[data-role-hint="syllabus"]')).toBeNull();
});

const SCOPE: DeliverableScopeDto = {
  goalId: "goal_d", title: "my midterm", sentence: "only my midterm", kind: "exam", dueAt: null, depth: "fluency",
  topics: [
    { learningObjectId: "lo_matrices", title: "Matrix computations", phrase: "matrix", onPastPapers: true },
    { learningObjectId: "lo_eigen", title: "Eigenvalues", phrase: "eigenvalues", onPastPapers: false },
  ],
  unmatched: [], inputs: [], subjectId: "linear-algebra", subjects: [],
  resolution: { id: "dsr_1", origin: "resolver", model: "fake", createdAt: "2026-11-01T09:00:00Z", facetScope: {} },
};

it("marks the topics your past papers test, and only those", () => {
  const { container } = render(<DeliverableScopePanel scope={SCOPE} onChanged={vi.fn()} onError={vi.fn()} />);
  const marked = container.querySelector('[data-deliverable-topic="lo_matrices"] [data-past-papers]');
  expect(marked?.textContent).toContain(SCOPE_COPY.pastPapers);
  expect(container.querySelector('[data-deliverable-topic="lo_eigen"] [data-past-papers]')).toBeNull();
  expect(findJargon(SCOPE_COPY.pastPapers + " " + SCOPE_COPY.pastPapersTitle)).toEqual([]);
});

it("shows no mark when the switch is off (the key is absent)", () => {
  const off = { ...SCOPE, topics: SCOPE.topics.map(({ onPastPapers: _unused, ...topic }) => topic) };
  const { container } = render(<DeliverableScopePanel scope={off} onChanged={vi.fn()} onError={vi.fn()} />);
  expect(container.querySelector("[data-past-papers]")).toBeNull();
});
