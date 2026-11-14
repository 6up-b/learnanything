// A collection's "synthesize →" uses the same brief wizard as Quick Add, so an
// exam-prep brief must ask its build for the goal the wizard promises.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { clear } from "../api/queryCache";
import { SourceLibrarySidebar } from "./SourceLibrarySidebar";

const api = vi.hoisted(() => ({
  getSourceLibrary: vi.fn(),
  listSourceSets: vi.fn(),
  getSourceSet: vi.fn(),
  buildStudyMap: vi.fn(),
  deleteSource: vi.fn()
}));
vi.mock("../api/client", () => ({ api }));

beforeEach(() => {
  clear();
  api.getSourceLibrary.mockResolvedValue({ version: 1, sources: [] });
  api.listSourceSets.mockResolvedValue({
    version: 1,
    sourceSets: [{ id: "set_prob", subjectId: "probability", title: "Probability", memberCount: 0 }]
  });
  api.getSourceSet.mockResolvedValue({
    version: 1,
    sourceSet: { id: "set_prob", subjectId: "probability", title: "Probability", members: [] }
  });
  api.buildStudyMap.mockResolvedValue({ id: "batch_1", mode: "bootstrap", jobs: [] });
});

afterEach(() => cleanup());

async function openCollection() {
  render(<SourceLibrarySidebar onOpenOutline={vi.fn()} onFocusSource={vi.fn()} />);
  const row = await screen.findByText("Probability");
  await act(async () => {
    fireEvent.click(row);
  });
  await screen.findByText("no members");
}

it("an exam-prep collection brief asks the build for its goal", async () => {
  await openCollection();
  fireEvent.click(screen.getByText("brief"));
  fireEvent.click(screen.getByText("exam prep"));
  for (let step = 0; step < 3; step += 1) fireEvent.click(screen.getByRole("button", { name: "next →" }));
  fireEvent.change(document.querySelector('input[type="date"]') as HTMLInputElement, { target: { value: "2026-11-27" } });
  fireEvent.click(screen.getByRole("button", { name: "Use brief" }));
  await act(async () => {
    fireEvent.click(screen.getByText("synthesize →"));
  });

  await waitFor(() => expect(api.buildStudyMap).toHaveBeenCalledTimes(1));
  const input = api.buildStudyMap.mock.calls[0][0];
  expect(input.createGoal).toBe(true);
  expect(input.brief).toMatchObject({ outcome: "exam_prep" });
  expect(input.brief.dueAt).toBeTruthy();
});

it("a collection with no brief asks for no goal", async () => {
  await openCollection();
  await act(async () => {
    fireEvent.click(screen.getByText("synthesize →"));
  });

  await waitFor(() => expect(api.buildStudyMap).toHaveBeenCalledTimes(1));
  expect(api.buildStudyMap.mock.calls[0][0].createGoal).toBe(false);
});
