import { beforeEach, describe, expect, it, vi } from "vitest";
import { readCredential, saveCredential, pickUpFragmentToken } from "../store/credential";
import { cacheSessionId, cachedSessionId } from "../store/sessionCache";
import { addToOutbox, listOutbox } from "../store/outbox";
import { call, CLIENT_CAPABILITIES_HEADER, isRetrySafe, OFFLINE, pollJob, rpcOnce, rpcOutcome, runLong } from "./http";

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

const fetchMock = vi.fn<typeof fetch>();

beforeEach(async () => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  await saveCredential({ token: "tok", deviceId: "dev", scope: "app" });
});

describe("call", () => {
  it("posts the command and its params to /rpc with the bearer and no cookies", async () => {
    fetchMock.mockResolvedValueOnce(json(200, { ok: true, result: { sessionId: "s" } }));
    await expect(call("get_session", { sessionId: "s" })).resolves.toEqual({ sessionId: "s" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/rpc");
    expect(JSON.parse(init?.body as string)).toEqual({ method: "get_session", params: { sessionId: "s" } });
    expect(init?.credentials).toBe("omit");
    expect((init?.headers as Record<string, string>).Authorization).toBe("Bearer tok");
  });

  it("says on every /rpc that this app answers probes and has the Reader (mobile v2 V3, V4)", async () => {
    fetchMock.mockResolvedValueOnce(json(200, { ok: true, result: { sessionId: "s" } }));
    await call("get_session", { sessionId: "s" });
    const [, init] = fetchMock.mock.calls[0];
    expect((init?.headers as Record<string, string>)[CLIENT_CAPABILITIES_HEADER]).toBe("phone_probes,phone_reader");
  });

  it("turns the host's error body into the desktop's CommandError", async () => {
    const error = { code: "session_moved", message: "This session continued on desktop.", retryable: false, details: { owner_label: "desktop" } };
    fetchMock.mockResolvedValueOnce(json(409, { ok: false, error }));
    await expect(call("get_session", { sessionId: "s" })).rejects.toEqual(error);
  });

  it("reads a body that is not ours as internal, and a Serve gateway error as the desktop being away", async () => {
    fetchMock.mockResolvedValueOnce(new Response("<html>", { status: 500 }));
    await expect(rpcOnce("end_session", {})).rejects.toMatchObject({ code: "internal" });
    fetchMock.mockResolvedValueOnce(new Response("bad gateway", { status: 502 }));
    await expect(rpcOnce("end_session", {})).rejects.toEqual(OFFLINE);
    fetchMock.mockRejectedValueOnce(new TypeError("network"));
    await expect(rpcOnce("end_session", {})).rejects.toEqual(OFFLINE);
  });

  it("refuses without a token and sends nothing", async () => {
    const { deleteCredential } = await import("../store/credential");
    await deleteCredential();
    await expect(call("get_session", {})).rejects.toMatchObject({ code: "not_paired" });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe("a 401 (§4.4)", () => {
  it("deletes the token and the session cache and keeps the outbox", async () => {
    cacheSessionId("s1");
    await addToOutbox({ clientCaptureId: "c1", kind: "text", text: "x", capturedAt: "t" });
    fetchMock.mockResolvedValueOnce(json(401, { ok: false, error: { code: "unauthorized", message: "m", retryable: false } }));
    await expect(call("get_session", {})).rejects.toMatchObject({ code: "unauthorized" });
    await expect(readCredential()).resolves.toBeNull();
    expect(cachedSessionId()).toBeNull();
    await expect(listOutbox()).resolves.toHaveLength(1);
  });
});

describe("202 (§6.3)", () => {
  it("is a job to poll, never a result", async () => {
    fetchMock.mockResolvedValueOnce(json(202, { ok: true, accepted: { job_id: "j1", request_id: "r1", state: "accepted" } }));
    await expect(rpcOnce("submit_attempt", {}, "r1")).resolves.toEqual({
      kind: "accepted",
      accepted: { jobId: "j1", requestId: "r1", state: "accepted" }
    });
    expect(JSON.parse(fetchMock.mock.calls[0][1]?.body as string).request_id).toBe("r1");
  });

  it("a long method polls its job to the end and is told before it starts", async () => {
    vi.useFakeTimers();
    try {
      fetchMock
        .mockResolvedValueOnce(json(202, { ok: true, accepted: { job_id: "j1", request_id: "r1", state: "accepted" } }))
        .mockResolvedValueOnce(json(200, { state: "running" }))
        .mockRejectedValueOnce(new TypeError("offline for a moment"))
        .mockResolvedValueOnce(json(200, { state: "completed", result: { attemptId: "a1" } }));
      const onAccepted = vi.fn();
      const done = runLong("submit_attempt", {}, "r1", { onAccepted });
      await vi.runAllTimersAsync();
      await expect(done).resolves.toEqual({ attemptId: "a1" });
      expect(onAccepted).toHaveBeenCalledWith({ jobId: "j1", requestId: "r1", state: "accepted" });
      expect(fetchMock.mock.calls[1][0]).toBe("/api/v1/jobs/j1");
    } finally {
      vi.useRealTimers();
    }
  });

  it("a failed job rejects with its typed error", async () => {
    const error = { code: "grading_fallback_required", message: "m", retryable: true };
    fetchMock.mockResolvedValueOnce(json(200, { state: "failed", error }));
    await expect(pollJob("j1")).rejects.toEqual(error);
  });
});

describe("the retry policy (§6.2)", () => {
  const busy = () => json(503, { ok: false, error: { code: "database_busy", message: "m", retryable: true } });

  it("retries a retryable error on a retry-safe method", async () => {
    vi.useFakeTimers();
    try {
      fetchMock.mockResolvedValueOnce(busy()).mockResolvedValueOnce(json(200, { ok: true, result: 1 }));
      const done = rpcOutcome("get_session", {});
      await vi.runAllTimersAsync();
      await expect(done).resolves.toEqual({ kind: "result", result: 1 });
      expect(fetchMock).toHaveBeenCalledTimes(2);
    } finally {
      vi.useRealTimers();
    }
  });

  it.each(["start_session", "adopt_session", "end_session", "skip_practice_item"] as const)("never retries %s on its own", async (method) => {
    expect(isRetrySafe(method)).toBe(false);
    fetchMock.mockResolvedValueOnce(busy());
    await expect(rpcOutcome(method, {})).rejects.toMatchObject({ code: "database_busy" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("does not retry what is not retryable, or a grading outage, which waits for the learner", async () => {
    fetchMock.mockResolvedValueOnce(json(404, { ok: false, error: { code: "not_found", message: "m", retryable: false } }));
    await expect(rpcOutcome("get_session", {})).rejects.toMatchObject({ code: "not_found" });
    fetchMock.mockResolvedValueOnce(json(409, { ok: false, error: { code: "grading_fallback_required", message: "m", retryable: true } }));
    await expect(rpcOutcome("submit_attempt", {}, "r")).rejects.toMatchObject({ code: "grading_fallback_required" });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("gives up after its bound", async () => {
    vi.useFakeTimers();
    try {
      fetchMock.mockImplementation(async () => busy());
      const done = rpcOutcome("get_session", {}).catch((error) => error);
      await vi.runAllTimersAsync();
      await expect(done).resolves.toMatchObject({ code: "database_busy" });
      expect(fetchMock).toHaveBeenCalledTimes(4);
    } finally {
      vi.useRealTimers();
    }
  });
});

describe("token pickup from the fragment (§4.2)", () => {
  it("stores it and takes it out of the address bar", async () => {
    const { resetCredentialForTests } = await import("../store/credential");
    resetCredentialForTests();
    window.history.replaceState(null, "", "/app/#token=fresh&device=d2");
    await expect(pickUpFragmentToken()).resolves.toBe(true);
    expect(window.location.hash).toBe("");
    await expect(readCredential()).resolves.toEqual({ token: "fresh", deviceId: "d2", scope: "app" });
  });

  it("does nothing without one", async () => {
    window.history.replaceState(null, "", "/app/");
    await expect(pickUpFragmentToken()).resolves.toBe(false);
  });
});
