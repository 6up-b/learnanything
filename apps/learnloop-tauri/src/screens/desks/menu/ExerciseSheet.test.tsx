// @vitest-environment jsdom
// Make it practice on an exercise: its words first, then the import, then what it made with edit and retire.
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { PassageContentDto, ReaderExerciseImportStatusDto } from "../../../api/dto";
import { Poller } from "../../../api/poller";

vi.mock("../../../api/client", () => ({ api: { retirePracticeItem: vi.fn(async () => ({})), editPracticeItem: vi.fn(async () => ({})) } }));

import { ExerciseSheet } from "./ExerciseSheet";

afterEach(cleanup);

const words = (withheld = false): PassageContentDto => ({
  version: 1, extractionId: "e", sourceId: "src", title: "a book", withheld,
  spans: [{ spanId: "s1", text: withheld ? null : "Exercise 3. Show that the weights sum to one.", page: 4, t0: null, t1: null, sectionId: null, sectionLabel: null, withheld }],
});

describe("the exercise sheet", () => {
  it("shows the exercise's own words, imports only when asked, then lists what it made as already in the queue", async () => {
    const poller = new Poller({ setInterval: () => 1, clearInterval: () => undefined });
    const startImport = vi.fn(async () => ({ status: "queued", batchId: "b1" }));
    let done = false;
    const readStatus = vi.fn(async (): Promise<ReaderExerciseImportStatusDto> => (done
      ? { status: "completed", result: { extractionId: "e", anchorStatus: "exact", warnings: [], skipped: [],
        items: [{ practiceItemId: "pi1", title: "weights sum to one", prompt: "Show that the weights sum to one.", learningObjectId: "lo1", learningObjectTitle: "softmax",
          practiceMode: "free_response", capability: "", taskFeatures: {}, evidenceFacets: [], difficulty: null, hintCount: 0, classificationReason: "" }] } }
      : { status: "running" }));
    render(<ExerciseSheet readWords={async () => words()} startImport={startImport} readStatus={readStatus} poller={poller} owner="w1" onClose={() => undefined} onError={() => undefined} />);
    await screen.findByText("Exercise 3. Show that the weights sum to one.");
    expect(startImport).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("import it as practice"));
    await screen.findByText("◐ importing the exercise…");
    done = true;
    await act(async () => {
      await poller.tick();
    });
    await screen.findByText(/this is in your queue now · edit or retire it if it is wrong/);
    expect(screen.getByText("weights sum to one")).toBeTruthy();
    expect(screen.getByText("retire")).toBeTruthy();
    expect(poller.size).toBe(0);
  });

  it("exam or held-out material: nothing of it shows, and there is nothing to import", async () => {
    const poller = new Poller({ setInterval: () => 1, clearInterval: () => undefined });
    const startImport = vi.fn();
    render(<ExerciseSheet readWords={async () => words(true)} startImport={startImport} readStatus={vi.fn()} poller={poller} owner={null} onClose={() => undefined} onError={() => undefined} />);
    await screen.findByText(/exam or held-out material: it is not shown or made into practice from here/);
    expect(screen.queryByText("import it as practice")).toBeNull();
    expect(startImport).not.toHaveBeenCalled();
  });
});
