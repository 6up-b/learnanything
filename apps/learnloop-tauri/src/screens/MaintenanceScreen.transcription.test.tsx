// Reader CA1, Codex review F7: a transcription report on the Maintenance
// screen shows what was reported (how often, the learner's words, the
// wording beside the page) and its action works: *Fix the wording* edits the
// card's prompt (edit_practice_item) and the feed is read again, where the
// report resolves; the inspector is one click away. The generic, inert
// action button is not shown for it.
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { MaintenanceNoticeDto } from "../api/dto";
import { MaintenanceScreen } from "./MaintenanceScreen";

const { api, refetch } = vi.hoisted(() => ({
  api: { editPracticeItem: vi.fn(), readerProblemCrops: vi.fn(), maintenanceNoticeAction: vi.fn() },
  refetch: vi.fn(),
}));
vi.mock("../api/client", () => ({ api }));

// The notice as get_maintenance_feed returns it after practice.report_transcription
// (tests/test_reader_ca1_codex_review.py pins the server side of this shape).
const NOTICE: MaintenanceNoticeDto = {
  id: "mn_1", subjectId: null, noticeType: "transcription_mismatch", dedupKey: "pi_ex", severity: "action_needed",
  agingPolicy: "auto_resolution", entityType: "practice_item", entityId: "pi_ex",
  title: "The transcription of Exercise 6.1.12 doesn't match the page",
  detail: { practiceItemId: "pi_ex", promptSha256: "sha256:x", prompt: "Find x_1 such that A x_1 = 0.",
            extractionId: "ext", spanIds: ["e1"], exerciseLabel: "Exercise 6.1.12", reports: 2,
            firstReportedAt: "2026-10-25T09:00:00Z", lastReportedAt: "2026-10-25T09:05:00Z",
            notes: [{ text: "the subscript should be i", at: "2026-10-25T09:00:00Z" }] },
  action: { action: "open_practice_item", label: "Fix the wording", practiceItemId: "pi_ex" },
  status: "active", snoozeCount: 0, snoozedUntil: null, firstSeenAt: "x", lastSeenAt: "x",
};

vi.mock("../api/useCachedQuery", () => ({
  useCachedQuery: (key: unknown[]) => ({
    data: key[0] === "maintenance_feed" ? { version: 1, notices: [NOTICE] } : undefined,
    error: null,
    refetch,
  }),
}));

beforeEach(() => {
  for (const mock of [...Object.values(api), refetch]) mock.mockReset();
  api.readerProblemCrops.mockResolvedValue({ extractionId: "ext", spanIds: ["e1"], status: "ok", skippedSpanIds: [],
    crops: [{ page: 0, pageLabel: "1", bbox: [1, 2, 3, 4], spanIds: ["e1"], image: null }] });
  api.editPracticeItem.mockResolvedValue({ practiceItemId: "pi_ex", changed: ["prompt"] });
});
afterEach(cleanup);

it("shows the report's count, the learner's words, the wording beside the page, and no inert button", async () => {
  const onInspect = vi.fn();
  render(<MaintenanceScreen subjects={[]} onError={vi.fn()} onInspect={onInspect} />);
  const card = screen.getByTestId("transcription-report");
  expect(card.textContent).toContain("reported 2 times");
  expect(within(screen.getByTestId("transcription-report-notes")).getByText("the subscript should be i")).toBeTruthy();
  expect(card.textContent).toContain("Find x_1 such that A x_1 = 0.");
  expect(await within(card).findByRole("button", { name: /as printed/ })).toBeTruthy();   // the page beside it
  // One "Fix the wording" (the card's), not the generic one with no handler.
  expect(screen.getAllByRole("button", { name: "Fix the wording" })).toHaveLength(1);
  fireEvent.click(within(card).getByRole("button", { name: "pi_ex" }));
  expect(onInspect).toHaveBeenCalledWith("pi_ex");
});

it("Fix the wording edits the card's prompt and reads the feed again", async () => {
  render(<MaintenanceScreen subjects={[]} onError={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Fix the wording" }));
  const box = screen.getByRole("textbox", { name: "the card's wording" }) as HTMLTextAreaElement;
  expect(box.value).toBe("Find x_1 such that A x_1 = 0.");
  fireEvent.change(box, { target: { value: "Find x_i such that A x_i = 0." } });
  fireEvent.click(screen.getByRole("button", { name: "save the wording" }));
  await waitFor(() => expect(api.editPracticeItem).toHaveBeenCalledWith({
    practiceItemId: "pi_ex", prompt: "Find x_i such that A x_i = 0.", reason: "the transcription didn't match the page" }));
  await waitFor(() => expect(refetch).toHaveBeenCalled());
  expect(screen.getByRole("status").textContent).toContain("saved");
});

it("an unchanged wording saves nothing", async () => {
  render(<MaintenanceScreen subjects={[]} onError={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Fix the wording" }));
  fireEvent.click(screen.getByRole("button", { name: "save the wording" }));
  expect(api.editPracticeItem).not.toHaveBeenCalled();
});
