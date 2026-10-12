import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { InboxStrip } from "./InboxStrip";
import type { CaptureDto } from "../api/capture";

const { api, card, source } = vi.hoisted(() => ({
  api: { getInboxSummary: vi.fn(), listCaptureInbox: vi.fn(), dismissCapture: vi.fn(), purgeCapture: vi.fn() },
  card: vi.fn(), source: vi.fn()
}));
vi.mock("../api/client", () => ({ api }));
vi.mock("./WriteCardDialog", () => ({ WriteCardDialog: (props: { onClose: () => void }) => {
  card(props); return <button onClick={props.onClose}>Cancel card</button>;
} }));
vi.mock("./QuickAddDialog", () => ({ QuickAddDialog: (props: { onClose: () => void }) => {
  source(props); return <button onClick={props.onClose}>Cancel source</button>;
} }));

function capture(kind: CaptureDto["kind"] = "text"): CaptureDto {
  return { captureId: "capture-1", kind, text: kind === "text" ? "Why eigenvectors?" : null,
    url: kind === "url" ? "https://example.org/book" : null, note: null,
    mediaSha256: null, mediaMime: null, mediaDeletePending: false, mediaRetainedShared: false, status: "new", receivedAt: "2026-10-11" };
}
function summary(row = capture()) {
  return { count: 1, newCount: 1, captures: [row], pinnedVault: "/other", vaultMismatch: true, enabled: true };
}
beforeEach(() => {
  vi.useFakeTimers();
  vi.clearAllMocks();
  api.getInboxSummary.mockResolvedValue(summary());
  api.listCaptureInbox.mockResolvedValue({ captures: [{ ...capture(), status: "routed" }] });
  api.dismissCapture.mockResolvedValue({});
  api.purgeCapture.mockResolvedValue({ capture: { ...capture(), status: "purged" } });
});
afterEach(() => { cleanup(); vi.useRealTimers(); });
async function show() {
  const onAsk = vi.fn();
  const view = render(<InboxStrip subjects={[{ id: "subject", title: "Subject" }]} onAsk={onAsk} />);
  await act(async () => {});
  return { ...view, onAsk };
}

it("polls every 30 seconds and on focus, cleans up, and shows the pinned-vault banner", async () => {
  const view = await show();
  expect(screen.getByRole("status").textContent).toContain("/other");
  expect(api.getInboxSummary).toHaveBeenCalledTimes(1);
  await act(async () => { vi.advanceTimersByTime(30_000); });
  expect(api.getInboxSummary).toHaveBeenCalledTimes(2);
  await act(async () => { fireEvent(window, new Event("focus")); });
  expect(api.getInboxSummary).toHaveBeenCalledTimes(3);
  view.unmount();
  await act(async () => { vi.advanceTimersByTime(60_000); fireEvent(window, new Event("focus")); });
  expect(api.getInboxSummary).toHaveBeenCalledTimes(3);
});

it("prefills card and tutor without mutating the capture on open/cancel", async () => {
  const { onAsk } = await show();
  fireEvent.click(screen.getByText("Make a card"));
  expect(card.mock.lastCall?.[0]).toMatchObject({ captureId: "capture-1", initialPrompt: "Why eigenvectors?" });
  fireEvent.click(screen.getByText("Cancel card"));
  fireEvent.click(screen.getByText("Ask tutor"));
  expect(onAsk).toHaveBeenCalledWith({ context: "library", captureId: "capture-1", initialQuestion: "Why eigenvectors?", subjectId: "subject" });
  expect(api.dismissCapture).not.toHaveBeenCalled();
  expect(api.purgeCapture).not.toHaveBeenCalled();
});

it.each(["url", "image"] as const)("routes %s into its existing dialog with capture provenance", async (kind) => {
  api.getInboxSummary.mockResolvedValue(summary(capture(kind)));
  await show();
  fireEvent.click(screen.getByText(kind === "url" ? "Quick Add source" : "Make a card"));
  const props = (kind === "url" ? source : card).mock.lastCall?.[0];
  expect(props.captureId).toBe("capture-1");
  if (kind === "url") expect(props.defaultSource).toBe("https://example.org/book");
  else expect(screen.getByText(/Photo → card \(manual\)/)).toBeTruthy();
  expect(api.dismissCapture).not.toHaveBeenCalled();
});

it("requires confirmation to purge and refreshes after a successful dismiss", async () => {
  await show();
  fireEvent.click(screen.getByText("Purge"));
  expect(api.purgeCapture).not.toHaveBeenCalled();
  await act(async () => { fireEvent.click(screen.getByText("Confirm purge")); });
  expect(api.purgeCapture).toHaveBeenCalledWith("capture-1");
  await act(async () => { fireEvent.click(screen.getByText("Dismiss")); });
  expect(api.dismissCapture).toHaveBeenCalledWith("capture-1");
  expect(api.getInboxSummary).toHaveBeenCalledTimes(3);
});

it("allows purging already handled captures without offering routing again", async () => {
  await show();
  await act(async () => { fireEvent.click(screen.getByText("Include handled")); });
  expect(api.listCaptureInbox).toHaveBeenCalledWith({ status: null, limit: 100 });
  expect(screen.queryByText("Ask tutor")).toBeNull();
  expect(screen.queryByText("Make a card")).toBeNull();
  fireEvent.click(screen.getByText("Purge"));
  expect(screen.getByText(/Notes\/cards already created are kept/)).toBeTruthy();
});

it("inspects the purge response and offers Retry delete even after content leaves the new inbox", async () => {
  const purged = { ...capture("image"), status: "purged", mediaDeletePending: true };
  api.purgeCapture.mockResolvedValue({ capture: purged });
  await show();
  fireEvent.click(screen.getByText("Purge"));
  await act(async () => { fireEvent.click(screen.getByText("Confirm purge")); });
  expect(screen.getByText(/original media deletion is pending/)).toBeTruthy();
  api.purgeCapture.mockResolvedValue({ capture: { ...purged, mediaDeletePending: false } });
  await act(async () => { fireEvent.click(screen.getByText("Retry delete")); });
  expect(api.purgeCapture).toHaveBeenCalledTimes(2);
  expect(screen.queryByText("Retry delete")).toBeNull();
});

it("shows persisted pending and shared-media flags for purged entries after remount", async () => {
  api.listCaptureInbox.mockResolvedValue({ captures: [{
    ...capture("image"), status: "purged", mediaDeletePending: true, mediaRetainedShared: true,
  }] });
  await show();
  await act(async () => { fireEvent.click(screen.getByText("Include handled")); });
  expect(screen.getByText(/Original media deletion is pending/)).toBeTruthy();
  expect(screen.getByText(/another source or capture still references these bytes/)).toBeTruthy();
  expect(screen.queryByText("Purge")).toBeNull();
  await act(async () => { fireEvent.click(screen.getByText("Retry delete")); });
  expect(api.purgeCapture).toHaveBeenCalledWith("capture-1");
});

it("reports shared-original retention from the purge response", async () => {
  api.purgeCapture.mockResolvedValue({ capture: {
    ...capture("image"), status: "purged", mediaRetainedShared: true,
  } });
  await show();
  fireEvent.click(screen.getByText("Purge"));
  await act(async () => { fireEvent.click(screen.getByText("Confirm purge")); });
  expect(screen.getByText(/another source or capture still references these bytes/)).toBeTruthy();
  expect(screen.queryByText("Retry delete")).toBeNull();
});
