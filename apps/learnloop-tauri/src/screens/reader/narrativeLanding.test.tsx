// RW6b part 2, Codex review F7: a narrative still being written lands in an
// already-open "Last time here" card and in an open Wrap up, with no
// navigation and no learner action: the surface showing it re-reads every
// NARRATIVE_POLL_MS while it is pending, and stops (timer cleared) once it
// lands, the source changes or Wrap up closes.
import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { ReaderDigestNarrativeDto, ReaderRecapCardDto, ReaderWrapUpDto } from "../../api/dto";
import { DigestNarrative, NARRATIVE_COPY } from "./DigestNarrative";
import { NARRATIVE_POLL_MS, useReaderRecap } from "./useReaderRecap";

const api = vi.hoisted(() => ({
  readerRecap: vi.fn(), readerRecapEvent: vi.fn(), readerWrapUp: vi.fn(), readerWrapUpOffer: vi.fn(),
}));
vi.mock("../../api/client", () => ({ api }));

const TEXT = "You read 5.4 on mixtures and asked why the densities are weighted by p.";

function narrative(state: ReaderDigestNarrativeDto["state"]): ReaderDigestNarrativeDto {
  return { state, label: "summary written by LearnLoop's model", authority: "salience_only", digestId: "rsd_1",
           ...(state === "landed" ? { text: TEXT, citedEventIds: ["ex1"] } : {}) };
}

function card(state: ReaderDigestNarrativeDto["state"]): { recap: ReaderRecapCardDto } {
  return { recap: {
    recapVersion: "rw6a-recap-v1", extractionId: "ext1",
    session: { sessionId: "v1", extractionId: "ext1", visitIds: ["v1"], startedAt: "2026-10-09T20:00:00Z", endedAt: "2026-10-09T20:40:00Z", minutes: 40 },
    continueAt: null, stillOpen: [], unfinished: [], worthASecondLook: [], sinceLastTime: { demonstrated: [], checksRetired: [] },
    narrative: narrative(state),
  } as ReaderRecapCardDto };
}

function wrapUp(state: ReaderDigestNarrativeDto["state"]): ReaderWrapUpDto {
  return {
    version: 1, wrapUpVersion: "rw6a-wrap-up-v1", available: true, extractionId: "ext1",
    session: { sessionId: "v1", extractionId: "ext1", visitIds: ["v1"], startedAt: "2026-10-14T21:10:00Z", endedAt: "2026-10-14T21:50:00Z", minutes: 40 },
    resolved: [], stillOpen: [], worthReinforcing: [], narrative: narrative(state),
  } as ReaderWrapUpDto;
}

function Harness({ extractionId = "ext1" }: { extractionId?: string }) {
  const ctl = useReaderRecap({ enabled: true, wrapUpEnabled: true, extractionId, visitId: () => "v1", readingMoved: false,
                               activityKey: "0", onError: () => undefined });
  return (
    <div>
      <section aria-label="card"><DigestNarrative narrative={ctl.recap?.narrative} /></section>
      <section aria-label="recap kept">{ctl.recap ? `session ${ctl.recap.session.sessionId}` : "no recap"}</section>
      <button type="button" onClick={() => void ctl.openWrapUp()}>open wrap up</button>
      <button type="button" onClick={ctl.closeWrapUp}>close wrap up</button>
      <section aria-label="wrap up">{ctl.wrapUpOpen ? <DigestNarrative narrative={ctl.wrapUpOpen.narrative} /> : null}</section>
    </div>
  );
}

async function flush() {
  await act(async () => { await Promise.resolve(); await Promise.resolve(); });
}

beforeEach(() => { vi.resetAllMocks(); vi.useFakeTimers(); });
afterEach(() => { cleanup(); vi.useRealTimers(); });

it("a narrative that lands after the card opened appears in it with no action", async () => {
  api.readerRecap.mockResolvedValueOnce(card("pending"));
  api.readerWrapUp.mockResolvedValue({ ...wrapUp("pending"), available: false });
  render(<Harness />);
  await flush();
  expect(screen.getByLabelText("card").textContent).toContain(NARRATIVE_COPY.writing);
  // Still writing at the first re-read; landed at the second.
  api.readerRecap.mockResolvedValueOnce(card("pending")).mockResolvedValueOnce(card("landed"));
  await act(async () => { await vi.advanceTimersByTimeAsync(NARRATIVE_POLL_MS); });
  expect(screen.getByLabelText("card").textContent).toContain(NARRATIVE_COPY.writing);
  await act(async () => { await vi.advanceTimersByTimeAsync(NARRATIVE_POLL_MS); });
  expect(screen.getByLabelText("card").textContent).toContain(NARRATIVE_COPY.collapsed);
  expect(api.readerRecap).toHaveBeenCalledTimes(3);
  // Landed: no more reads.
  await act(async () => { await vi.advanceTimersByTimeAsync(NARRATIVE_POLL_MS * 3); });
  expect(api.readerRecap).toHaveBeenCalledTimes(3);
});

it("a narrative that lands while Wrap up is open appears there, and closing it stops the reads", async () => {
  api.readerRecap.mockResolvedValue(card("landed"));
  api.readerWrapUp.mockResolvedValue(wrapUp("pending"));
  render(<Harness />);
  await flush();
  await act(async () => { screen.getByRole("button", { name: "open wrap up" }).click(); });
  await flush();
  expect(screen.getByLabelText("wrap up").textContent).toContain(NARRATIVE_COPY.writing);
  const before = api.readerWrapUp.mock.calls.length;
  api.readerWrapUp.mockResolvedValueOnce(wrapUp("landed"));
  await act(async () => { await vi.advanceTimersByTimeAsync(NARRATIVE_POLL_MS); });
  expect(screen.getByLabelText("wrap up").textContent).toContain(NARRATIVE_COPY.collapsed);
  expect(api.readerWrapUp.mock.calls.length).toBe(before + 1);
  expect(api.readerRecap).toHaveBeenCalledTimes(1); // the landed card is not re-read

  // Pending again in a fresh Wrap up, then closed: the timer is cleared.
  api.readerWrapUp.mockResolvedValue(wrapUp("pending"));
  await act(async () => { screen.getByRole("button", { name: "open wrap up" }).click(); });
  await flush();
  await act(async () => { screen.getByRole("button", { name: "close wrap up" }).click(); });
  const closed = api.readerWrapUp.mock.calls.length;
  await act(async () => { await vi.advanceTimersByTimeAsync(NARRATIVE_POLL_MS * 3); });
  expect(api.readerWrapUp.mock.calls.length).toBe(closed);
});

it("a changed source clears the pending read", async () => {
  api.readerRecap.mockResolvedValueOnce(card("pending"));
  api.readerWrapUp.mockResolvedValue({ ...wrapUp("pending"), available: false });
  const { rerender } = render(<Harness />);
  await flush();
  api.readerRecap.mockResolvedValue(card("landed"));
  rerender(<Harness extractionId="ext2" />);
  await flush();
  const calls = api.readerRecap.mock.calls.length;
  await act(async () => { await vi.advanceTimersByTimeAsync(NARRATIVE_POLL_MS * 2); });
  expect(api.readerRecap.mock.calls.length).toBe(calls);
  expect(api.readerRecap.mock.calls.every(([params]) => params.extractionId === "ext1" || params.extractionId === "ext2")).toBe(true);
});

// RW6b part 2, fix round 4 (Sol verify finding 2): a polling read that fails
// is classified (W14) instead of being discarded: the sidecar down shows the
// offline state, any other failure says the summary could not be checked.
// The recap stays, polling continues, and the next successful read recovers.
const SIDECAR_DOWN = { code: "sidecar_unavailable", message: "The sidecar stopped.", retryable: true };

it("a failed re-read shows the offline state, keeps the recap and recovers when a read succeeds", async () => {
  api.readerRecap.mockResolvedValueOnce(card("pending"));
  api.readerWrapUp.mockResolvedValue({ ...wrapUp("pending"), available: false });
  render(<Harness />);
  await flush();
  expect(screen.getByLabelText("card").textContent).toContain(NARRATIVE_COPY.writing);
  // The sidecar goes down: the narrative says so, in place; the recap is kept.
  api.readerRecap.mockRejectedValueOnce(SIDECAR_DOWN);
  await act(async () => { await vi.advanceTimersByTimeAsync(NARRATIVE_POLL_MS); });
  const cardText = () => screen.getByLabelText("card").textContent ?? "";
  expect(cardText()).toContain("background service isn't responding");
  expect(cardText()).not.toContain(NARRATIVE_COPY.writing);
  expect(screen.getByLabelText("card").querySelector("[data-model-state='offline']")).not.toBeNull();
  expect(screen.getByLabelText("recap kept").textContent).toBe("session v1");
  // Another failure of another kind: still not "writing" forever.
  api.readerRecap.mockRejectedValueOnce(new Error("boom"));
  await act(async () => { await vi.advanceTimersByTimeAsync(NARRATIVE_POLL_MS); });
  expect(cardText()).toContain(NARRATIVE_COPY.pollFailed);
  expect(screen.getByLabelText("recap kept").textContent).toBe("session v1");
  // Polling continues; the next read succeeds (still pending): writing again.
  api.readerRecap.mockResolvedValueOnce(card("pending"));
  await act(async () => { await vi.advanceTimersByTimeAsync(NARRATIVE_POLL_MS); });
  expect(cardText()).toContain(NARRATIVE_COPY.writing);
  expect(cardText()).not.toContain("background service");
  // And it lands at the one after.
  api.readerRecap.mockResolvedValueOnce(card("landed"));
  await act(async () => { await vi.advanceTimersByTimeAsync(NARRATIVE_POLL_MS); });
  expect(cardText()).toContain(NARRATIVE_COPY.collapsed);
});

it("try again re-reads at once, and a failed Wrap up re-read shows offline there too", async () => {
  api.readerRecap.mockResolvedValue(card("landed"));
  api.readerWrapUp.mockResolvedValue(wrapUp("pending"));
  render(<Harness />);
  await flush();
  await act(async () => { screen.getByRole("button", { name: "open wrap up" }).click(); });
  await flush();
  api.readerWrapUp.mockRejectedValueOnce(SIDECAR_DOWN);
  await act(async () => { await vi.advanceTimersByTimeAsync(NARRATIVE_POLL_MS); });
  const wrapText = () => screen.getByLabelText("wrap up").textContent ?? "";
  expect(wrapText()).toContain("background service isn't responding");
  const before = api.readerWrapUp.mock.calls.length;
  api.readerWrapUp.mockResolvedValueOnce(wrapUp("landed"));
  await act(async () => { screen.getByRole("button", { name: /try again/ }).click(); });
  await flush();
  expect(api.readerWrapUp.mock.calls.length).toBe(before + 1);
  expect(wrapText()).toContain(NARRATIVE_COPY.collapsed);
});
