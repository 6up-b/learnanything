// UX journey audit UX-7 (beginner-1 #54): "add it" on a topic not in the library did nothing
// when the library had no subject yet: the server refused it (`no_subject`) and the subject
// picker it should then open renders only when there are subjects to pick from. The server now
// files the first topic under a first subject (tests/test_deliverable_scope.py); the panel never
// answers a refusal with nothing.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { DeliverableScopeDto } from "../../api/dto";
import { findJargon } from "../../copy/denyList";
import { DeliverableScopePanel, SCOPE_COPY } from "./DeliverableScope";

const { api } = vi.hoisted(() => ({ api: {
  curriculumSetScope: vi.fn(), curriculumScope: vi.fn(), curriculumScopeDecide: vi.fn(), curriculumSetDepth: vi.fn(),
} }));
vi.mock("../../api/client", () => ({ api }));

const OPEN = { phrase: "machine learning", proposedTitle: "Machine learning fundamentals",
  proposedStatement: "What machine learning is.", status: "open" };
const NO_SUBJECT: DeliverableScopeDto = {
  goalId: "goal_d", title: "I want to understand how machine learning works", sentence: "I want to understand how machine learning works",
  kind: "quest", dueAt: null, depth: null, topics: [], unmatched: [OPEN], inputs: [], subjectId: null, subjects: [],
  resolution: { id: "dsr_1", origin: "resolver", model: "fake", createdAt: "2026-11-18T09:00:00Z", facetScope: {} },
} as unknown as DeliverableScopeDto;

beforeEach(() => {
  for (const fn of Object.values(api)) fn.mockReset();
});
afterEach(() => cleanup());

it("UX-7: with no subject yet, add it is live and sends the topic for the server to file", async () => {
  const added = { ...NO_SUBJECT, unmatched: [{ ...OPEN, status: "created" }] };
  api.curriculumScopeDecide.mockResolvedValue({ created: { learningObjectId: "lo_ml" }, scope: added });
  const onChanged = vi.fn();
  render(<DeliverableScopePanel scope={NO_SUBJECT} onChanged={onChanged} onError={vi.fn()} />);
  expect(screen.queryByLabelText(SCOPE_COPY.subject)).toBeNull();
  const addIt = screen.getByRole("button", { name: SCOPE_COPY.addIt });
  expect((addIt as HTMLButtonElement).disabled).toBe(false);
  await act(async () => { fireEvent.click(addIt); });
  expect(api.curriculumScopeDecide).toHaveBeenCalledWith({ goalId: "goal_d", phrase: "machine learning", decision: "create" });
  expect(onChanged).toHaveBeenCalledWith(added);
});

it("UX-7: a no-subject refusal with no subject to pick says so in place, never nothing", async () => {
  api.curriculumScopeDecide.mockRejectedValue({ code: "no_subject", message: "Choose the subject this new topic belongs to.", retryable: false });
  const onError = vi.fn();
  render(<DeliverableScopePanel scope={NO_SUBJECT} onChanged={vi.fn()} onError={onError} />);
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: SCOPE_COPY.addIt })); });
  const line = screen.getByRole("status");
  expect(line.textContent).toBe(SCOPE_COPY.noSubjectYet);
  expect(findJargon(line.textContent ?? "")).toEqual([]);
  expect(onError).not.toHaveBeenCalled();
});

it("with subjects to pick from, the refusal opens the picker as before (Codex re-review F16)", async () => {
  api.curriculumScopeDecide.mockRejectedValue({ code: "no_subject", message: "Choose the subject this new topic belongs to.", retryable: false });
  const scope = { ...NO_SUBJECT, subjectId: "linear-algebra",
    subjects: [{ subjectId: "linear-algebra", title: "Linear algebra" }, { subjectId: "statistics", title: "Statistics" }] } as DeliverableScopeDto;
  render(<DeliverableScopePanel scope={scope} onChanged={vi.fn()} onError={vi.fn()} />);
  await act(async () => { fireEvent.click(screen.getByRole("button", { name: SCOPE_COPY.addIt })); });
  expect(screen.getByLabelText(SCOPE_COPY.subject)).toBeTruthy();
  expect(screen.queryByRole("status")).toBeNull();
});
