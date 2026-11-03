// Mobile M2a (§6.5): the desktop's prompt when a start finds a session a phone holds.
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const stubs = vi.hoisted(() => ({
  api: {} as Record<string, ReturnType<typeof vi.fn>>
}));
vi.mock("../api/client", () => ({ api: stubs.api }));

import { SessionElsewherePrompt } from "../components/SessionElsewherePrompt";
import { startSessionOrAsk } from "./sessionHandoff";

const ELSEWHERE = {
  code: "session_open_elsewhere",
  message: "m",
  retryable: false,
  details: { session_id: "ses_phone", owner_label: "Phone", owner_generation: 3, has_draft: true, draft_first_line: "my first line" }
};
const SNAPSHOT = { sessionId: "ses_phone" };

beforeEach(() => {
  stubs.api.startSession = vi.fn();
  stubs.api.adoptSession = vi.fn(async () => ({}));
  stubs.api.getSession = vi.fn(async () => SNAPSHOT);
});

afterEach(() => cleanup());

describe("startSessionOrAsk", () => {
  it("a free start asks nothing", async () => {
    stubs.api.startSession.mockResolvedValueOnce({ sessionId: "s" });
    await expect(startSessionOrAsk({ availableMinutes: 25 })).resolves.toEqual({ sessionId: "s" });
    expect(stubs.api.startSession).toHaveBeenCalledWith({ availableMinutes: 25 });
  });

  it("any other refusal is the caller's", async () => {
    stubs.api.startSession.mockRejectedValueOnce({ code: "internal", message: "m" });
    await expect(startSessionOrAsk({ availableMinutes: 25 })).rejects.toMatchObject({ code: "internal" });
  });

  it("shows what is open, and Cancel starts nothing", async () => {
    stubs.api.startSession.mockRejectedValueOnce(ELSEWHERE);
    render(<SessionElsewherePrompt />);
    let answer: unknown = "pending";
    void startSessionOrAsk({ availableMinutes: 25 }).then((value) => { answer = value; });
    expect((await screen.findByRole("dialog")).textContent).toContain("You have a session open on Phone.");
    expect(screen.getByRole("dialog").textContent).toContain("my first line");
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(answer).toBeNull());
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(stubs.api.startSession).toHaveBeenCalledTimes(1);
    expect(stubs.api.adoptSession).not.toHaveBeenCalled();
  });

  it("Continue it here adopts at the generation shown and answers the session", async () => {
    stubs.api.startSession.mockRejectedValueOnce(ELSEWHERE);
    render(<SessionElsewherePrompt />);
    const started = startSessionOrAsk({ availableMinutes: 25 });
    fireEvent.click(await screen.findByRole("button", { name: "Continue it here" }));
    await expect(started).resolves.toEqual(SNAPSHOT);
    expect(stubs.api.adoptSession).toHaveBeenCalledWith({ sessionId: "ses_phone", expectedGeneration: 3 });
  });

  it("Start fresh replaces that session, and a stale one asks again", async () => {
    stubs.api.startSession
      .mockRejectedValueOnce(ELSEWHERE)
      .mockRejectedValueOnce({ ...ELSEWHERE, details: { ...ELSEWHERE.details, session_id: "ses_newer" } })
      .mockResolvedValueOnce({ sessionId: "ses_new" });
    render(<SessionElsewherePrompt />);
    const started = startSessionOrAsk({ availableMinutes: 25 });
    fireEvent.click(await screen.findByRole("button", { name: "Start fresh" }));
    await waitFor(() => expect(stubs.api.startSession).toHaveBeenCalledTimes(2));
    expect(stubs.api.startSession).toHaveBeenNthCalledWith(2, { availableMinutes: 25, replace: "ses_phone" });
    fireEvent.click(await screen.findByRole("button", { name: "Start fresh" }));
    await expect(started).resolves.toEqual({ sessionId: "ses_new" });
    expect(stubs.api.startSession).toHaveBeenNthCalledWith(3, { availableMinutes: 25, replace: "ses_newer" });
    await act(async () => undefined);
  });
});
