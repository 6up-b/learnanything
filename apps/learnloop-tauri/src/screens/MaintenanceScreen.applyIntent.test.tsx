// Refactor K3.5: an outstanding proposal apply on the Maintenance screen. Its
// feed notice carries the intent and the resolution, and its one action calls
// resolve_apply_intent: "Keep the files as they are" for a conflicted apply,
// "Complete pending apply" for a pending one (tests/test_apply_recovery.py
// pins the server side of both notices).
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { MaintenanceNoticeDto } from "../api/dto";
import { MaintenanceScreen } from "./MaintenanceScreen";

const { api, notices } = vi.hoisted(() => ({
  api: { resolveApplyIntent: vi.fn(), maintenanceNoticeAction: vi.fn() },
  notices: [] as MaintenanceNoticeDto[],
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("../api/useCachedQuery", () => ({
  useCachedQuery: (key: unknown[]) => ({
    data: key[0] === "maintenance_feed" ? { version: 1, notices } : undefined,
    error: null,
    refetch: vi.fn(),
  }),
}));

function notice(noticeType: string, label: string, resolution: string): MaintenanceNoticeDto {
  return {
    id: `mn_${noticeType}`, subjectId: null, noticeType, dedupKey: "ai_1", severity: "action_needed",
    agingPolicy: "auto_resolution", entityType: null, entityId: null,
    title: "A proposal apply stopped because concepts.yaml changed after it was planned.",
    detail: { intentId: "ai_1", proposedPatchId: "patch_1", paths: ["concepts.yaml"] },
    action: { action: "resolve_apply_intent", label, intentId: "ai_1", resolution },
    status: "active", snoozeCount: 0, snoozedUntil: null, firstSeenAt: "x", lastSeenAt: "x",
  };
}

beforeEach(() => {
  api.resolveApplyIntent.mockReset();
  api.resolveApplyIntent.mockResolvedValue({ version: 1, intent: { id: "ai_1", status: "set_aside", proposedPatchId: "patch_1", paths: [] } });
  notices.length = 0;
});
afterEach(cleanup);

it("Keep the files as they are sets the conflicted apply aside", async () => {
  notices.push(notice("apply_conflicted", "Keep the files as they are", "keep_files"));
  render(<MaintenanceScreen subjects={[]} onError={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Keep the files as they are" }));
  await waitFor(() => expect(api.resolveApplyIntent).toHaveBeenCalledWith("ai_1", "keep_files"));
});

it("Complete pending apply finishes the pending apply", async () => {
  notices.push(notice("append_partially_complete", "Complete pending apply", "complete"));
  render(<MaintenanceScreen subjects={[]} onError={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Complete pending apply" }));
  await waitFor(() => expect(api.resolveApplyIntent).toHaveBeenCalledWith("ai_1", "complete"));
});
