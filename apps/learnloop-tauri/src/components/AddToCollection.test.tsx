// Exam protection by extraction identity (docs/reviews/exam-protection-identity.md):
// a scope names the reading its unit ids were chosen on, and the desktop
// re-sends every member exactly as it received it.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { clear } from "../api/queryCache";
import { AddToCollectionPanel } from "./AddToCollection";

const api = vi.hoisted(() => ({
  listSourceSets: vi.fn(),
  loadVault: vi.fn(),
  getSourceSet: vi.fn(),
  upsertSourceSet: vi.fn()
}));
vi.mock("../api/client", () => ({ api }));

const EXAM_MEMBER = {
  sourceId: "src_exam",
  revisionId: "rev_exam",
  defaultRole: "primary_textbook",
  scope: [{ unitId: "u2", roleOverride: "exam" }],
  priority: 1,
  scopeExtractionId: "ext_exam_b",
  scopeRevisionId: "rev_exam",
  scopeSeal: "sha256:sealed-by-the-vault-writer"
};

beforeEach(() => {
  clear();
  for (const fn of Object.values(api)) fn.mockReset();
  api.listSourceSets.mockResolvedValue({ version: 1, sourceSets: [{ id: "set_la", subjectId: "la", title: "LA", memberCount: 1 }] });
  api.loadVault.mockResolvedValue({ vault: { subjects: ["la"] } });
  api.getSourceSet.mockResolvedValue({ version: 1, sourceSet: { id: "set_la", subjectId: "la", title: "LA", members: [EXAM_MEMBER] } });
  api.upsertSourceSet.mockImplementation(async (payload) => ({ version: 1, sourceSet: payload }));
});

afterEach(() => cleanup());

it("pins a scope with the reading its units were chosen on and re-sends other members untouched", async () => {
  const onAdded = vi.fn();
  render(
    <AddToCollectionPanel
      sourceId="src_text"
      revisionId="rev_text"
      scopeUnitIds={["ch1", "ch2"]}
      scopeExtractionId="ext_text_2"
      seedRole="primary_textbook"
      onClose={vi.fn()}
      onAdded={onAdded}
    />
  );
  const pin = await screen.findByText("pin to collection →");
  await act(async () => {
    fireEvent.click(pin);
  });
  await waitFor(() => expect(api.upsertSourceSet).toHaveBeenCalledTimes(1));
  const payload = api.upsertSourceSet.mock.calls[0][0];
  expect(payload.members).toEqual([
    EXAM_MEMBER,
    {
      sourceId: "src_text",
      revisionId: "rev_text",
      defaultRole: "primary_textbook",
      scope: [
        { unitId: "ch1", roleOverride: null },
        { unitId: "ch2", roleOverride: null }
      ],
      priority: 1,
      scopeExtractionId: "ext_text_2",
      scopeRevisionId: "rev_text"
    }
  ]);
});

it("a whole-source member names no reading", async () => {
  render(
    <AddToCollectionPanel
      sourceId="src_text"
      revisionId="rev_text"
      scopeUnitIds={[]}
      scopeExtractionId="ext_text_2"
      seedRole="reference"
      onClose={vi.fn()}
      onAdded={vi.fn()}
    />
  );
  const pin = await screen.findByText("pin to collection →");
  await act(async () => {
    fireEvent.click(pin);
  });
  await waitFor(() => expect(api.upsertSourceSet).toHaveBeenCalledTimes(1));
  const added = api.upsertSourceSet.mock.calls[0][0].members[1];
  expect(added.scopeExtractionId).toBeUndefined();
  expect(added.scope).toEqual([]);
});
