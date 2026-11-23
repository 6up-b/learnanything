// The role pickers read the vocabulary and its authority from the sidecar's
// matrix (`get_source_roles`). A desktop copy said only exams and problem sets
// "never define concepts"; the matrix gives notes no semantic authority either.
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { clear } from "../api/queryCache";
import type { SourceRoleDto } from "../api/dto";

function row(role: string, semanticContract: boolean, extra: Partial<SourceRoleDto> = {}): SourceRoleDto {
  return {
    role, semanticContract, assessmentAlignment: true, assessmentOnly: role === "exam",
    scopeOnly: false, defaultInventoryProfile: "semantic", ...extra
  };
}

const ROLES: SourceRoleDto[] = [
  row("primary_textbook", true), row("lecture", true), row("paper", true), row("reference", true),
  row("alternate_explanation", true), row("problem_set", false), row("exam", false), row("notes", false),
  row("syllabus", false, { scopeOnly: true })
];

const outline = {
  extractionId: "ext_1", revisionId: "rev_1", sourceId: "src_1", title: "A paper", authors: [], extractor: "pypdf",
  extractorVersion: "1", unitCount: 1, blockCount: 1, approxTokens: 1213, healthFlags: [], difficultPageCount: 0,
  units: [{
    unitId: "u1", parentUnitId: null, label: "Abstract", ordinal: 0, locator: {}, semanticHash: "h", pageStart: 0,
    pageEnd: 0, blockCount: 1, blockCounts: {}, structuralSignals: {}, healthFlags: [], approxTokens: 1213,
    inventory: { status: "cached" }
  }],
  selection: { selectedUnitIds: [], boundaryOverrides: [], needsReview: [], roleOverride: null }
};

const api = vi.hoisted(() => {
  const target: Record<string, unknown> = {};
  return new Proxy(target, {
    get: (store, name: string) => (name in store ? store[name] : () => new Promise(() => undefined))
  }) as Record<string, ReturnType<typeof vi.fn>>;
});
vi.mock("../api/client", () => ({ api }));

import { OutlinePlanFlow } from "./OutlineAndPlan";

const NEVER_DEFINES = "assessment-only authority — never defines concepts";

beforeEach(() => {
  clear();
  api.getSourceOutline = vi.fn(async () => outline);
  api.saveUnitSelection = vi.fn(async () => ({}));
  api.getSourceRoles = vi.fn(async () => ({ version: 1, roles: ROLES }));
});

afterEach(() => cleanup());

async function rolePicker(suggestedRole: string) {
  render(
    <OutlinePlanFlow sourceRef="src_1" subjectId={null} suggestedRole={suggestedRole} onClose={vi.fn()}
      onOpenBatch={vi.fn()} />
  );
  await screen.findByText("role");
}

it.each(["notes", "problem_set", "exam"])("says %s never defines concepts, as the matrix does", async (role) => {
  await rolePicker(role);
  expect(await screen.findByText(NEVER_DEFINES)).toBeTruthy();
});

it.each(["primary_textbook", "syllabus"])("says nothing of the kind for %s", async (role) => {
  await rolePicker(role);
  await screen.findByText(role);
  expect(screen.queryByText(NEVER_DEFINES)).toBeNull();
});

it("asks the sidecar for the vocabulary", async () => {
  await rolePicker("notes");
  expect(api.getSourceRoles).toHaveBeenCalled();
});
