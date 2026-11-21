// A request the sidecar refused for want of the one OK to use AI (nothing was sent) waits for the sheet: OK sends
// it again once, "Not now" leaves it refused; requests refused together share one sheet and one answer.
import { afterEach, describe, expect, it, vi } from "vitest";

const { invoke } = vi.hoisted(() => ({ invoke: vi.fn() }));
vi.mock("@tauri-apps/api/core", () => ({ invoke }));

import { api } from "../api/client";
import { answerAiOk, askForAiOk, isWaitingForOk, useAiOkAsked } from "./aiOk";
import { renderHook, act } from "@testing-library/react";

const WAITING = { code: "waiting_for_ok", message: "LearnLoop is waiting for your OK before it uses AI.", retryable: false };

afterEach(() => {
  answerAiOk(false);
  vi.clearAllMocks();
});

async function settled(): Promise<void> {
  for (let i = 0; i < 5; i += 1) await Promise.resolve();
}

describe("the one OK", () => {
  it("asks once, then sends the refused request again exactly once after OK", async () => {
    const asked = renderHook(() => useAiOkAsked());
    invoke.mockRejectedValueOnce(WAITING).mockResolvedValueOnce({ deliverables: [] });
    const pending = api.curriculumDeliverables();
    await settled();
    expect(asked.result.current).toBe(true);
    expect(invoke).toHaveBeenCalledTimes(1);
    act(() => answerAiOk(true));
    await expect(pending).resolves.toEqual({ deliverables: [] });
    expect(invoke).toHaveBeenCalledTimes(2);
    expect(invoke.mock.calls[1]).toEqual(invoke.mock.calls[0]);
    expect(asked.result.current).toBe(false);
  });

  it("Not now leaves the request refused and sends nothing more", async () => {
    invoke.mockRejectedValueOnce(WAITING);
    const pending = api.curriculumDeliverables();
    await settled();
    answerAiOk(false);
    await expect(pending).rejects.toMatchObject({ code: "waiting_for_ok" });
    expect(invoke).toHaveBeenCalledTimes(1);
  });

  it("shares one sheet among requests refused together, and never loops", async () => {
    invoke.mockRejectedValue(WAITING);
    const first = api.curriculumDeliverables();
    const second = api.curriculumDeliverables();
    await settled();
    expect(invoke).toHaveBeenCalledTimes(2);
    answerAiOk(true);
    // Each is sent again once; refused again (the OK did not land), each says so instead of asking forever.
    await expect(first).rejects.toMatchObject({ code: "waiting_for_ok" });
    await expect(second).rejects.toMatchObject({ code: "waiting_for_ok" });
    expect(invoke).toHaveBeenCalledTimes(4);
  });

  it("an Add whose questions wait asks with nothing to send again", () => {
    const asked = renderHook(() => useAiOkAsked());
    act(() => askForAiOk());
    expect(asked.result.current).toBe(true);
    act(() => answerAiOk(true));
    expect(asked.result.current).toBe(false);
  });

  it("knows the refusal by its code only", () => {
    expect(isWaitingForOk(WAITING)).toBe(true);
    expect(isWaitingForOk({ code: "provider_unavailable" })).toBe(false);
    expect(isWaitingForOk(null)).toBe(false);
  });
});
