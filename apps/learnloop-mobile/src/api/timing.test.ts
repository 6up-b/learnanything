// Mobile v2 §4.4 and §4.5 in the transport: what each exchange tells the connection line, and the
// round trip carried to the host on the next request.
import { beforeEach, describe, expect, it, vi } from "vitest";
import { connectionState, onReconnect } from "../shell/connection";
import { saveCredential } from "../store/credential";
import { call, CLIENT_TIMING_HEADER, getJson, pendingTimingSample, rpcOnce, runLong, serverTimingTotal } from "./http";

const fetchMock = vi.fn<typeof fetch>();

function json(status: number, body: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...headers } });
}

function headerOf(callIndex: number): string | undefined {
  const init = fetchMock.mock.calls[callIndex][1];
  return (init?.headers as Record<string, string>)[CLIENT_TIMING_HEADER];
}

beforeEach(async () => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  await saveCredential({ token: "tok", deviceId: "dev", scope: "app" });
});

describe("Server-Timing and the round trip (§4.5)", () => {
  it("reads the host's total", () => {
    expect(serverTimingTotal("queue;dur=1.5, handler;dur=8.0, total;dur=12.5")).toBe(12.5);
    expect(serverTimingTotal("total;dur=3")).toBe(3);
    expect(serverTimingTotal("handler;dur=8.0")).toBeNull();
    expect(serverTimingTotal(null)).toBeNull();
  });

  it("the first request carries nothing; the next carries the first's round trip, once", async () => {
    fetchMock.mockImplementation(async () => json(200, { ok: true, result: {} }, { "Server-Timing": "queue;dur=1.0, handler;dur=4.0, total;dur=6.5" }));
    await call("get_session", { sessionId: "s1" });
    expect(headerOf(0)).toBeUndefined();
    expect(pendingTimingSample()).toMatchObject({ method: "get_session", status: 200, hostMs: 6.5 });
    await call("get_feedback", { attemptId: "a1" });
    expect(headerOf(1)).toMatch(/^get_session;status=200;dur=\d+\.\d;host=6\.5$/);
    expect(pendingTimingSample()?.method).toBe("get_feedback");
  });

  it("an error reply is measured too, and no reply is not", async () => {
    fetchMock.mockResolvedValueOnce(json(404, { ok: false, error: { code: "not_found", message: "m", retryable: false } }));
    await expect(rpcOnce("get_session", {})).rejects.toMatchObject({ code: "not_found" });
    expect(pendingTimingSample()).toMatchObject({ method: "get_session", status: 404, hostMs: null });
    fetchMock.mockRejectedValueOnce(new TypeError("network"));
    await expect(rpcOnce("get_feedback", {})).rejects.toMatchObject({ code: "desktop_offline" });
    expect(pendingTimingSample()).toBeNull();
  });

  it("a status poll carries no sample and leaves the pending one for the next /rpc", async () => {
    fetchMock.mockResolvedValueOnce(json(200, { ok: true, result: {} }, { "Server-Timing": "total;dur=2" }));
    await call("get_session", {});
    fetchMock.mockResolvedValueOnce(json(200, { revision: 1 }));
    await getJson("/api/v1/queue-revision");
    expect(headerOf(1)).toBeUndefined();
    expect(pendingTimingSample()?.method).toBe("get_session");
  });
});

describe("the connection line's states (§4.4)", () => {
  it("no reply or Serve's 502 is offline; the host's own answer is back, once", async () => {
    const reconnects = vi.fn();
    onReconnect(reconnects);
    fetchMock.mockRejectedValueOnce(new TypeError("network"));
    await expect(rpcOnce("get_session", {})).rejects.toMatchObject({ code: "desktop_offline" });
    expect(connectionState().offline).toBe(true);
    fetchMock.mockResolvedValueOnce(new Response("bad gateway", { status: 502 }));
    await expect(rpcOnce("get_session", {})).rejects.toMatchObject({ code: "desktop_offline" });
    expect(reconnects).not.toHaveBeenCalled();
    fetchMock.mockResolvedValueOnce(json(404, { ok: false, error: { code: "not_found", message: "m", retryable: false } }));
    await expect(rpcOnce("get_session", {})).rejects.toMatchObject({ code: "not_found" });
    expect(connectionState().offline).toBe(false);
    expect(reconnects).toHaveBeenCalledTimes(1);
  });

  it("host_busy and database_busy are busy, and the next answer clears it", async () => {
    fetchMock.mockResolvedValueOnce(json(503, { ok: false, error: { code: "host_busy", message: "m", retryable: true } }));
    await expect(rpcOnce("end_session", {})).rejects.toMatchObject({ code: "host_busy" });
    expect(connectionState()).toMatchObject({ busy: true, offline: false });
    fetchMock.mockResolvedValueOnce(json(200, { ok: true, result: {} }));
    await call("end_session", {});
    expect(connectionState().busy).toBe(false);
  });

  it("a grading outage stays until a grade comes back", async () => {
    fetchMock.mockResolvedValueOnce(json(409, { ok: false, error: { code: "grading_fallback_required", message: "m", retryable: true } }));
    await expect(rpcOnce("submit_attempt", {}, "k")).rejects.toMatchObject({ code: "grading_fallback_required" });
    expect(connectionState().gradingDown).toBe(true);
    fetchMock.mockResolvedValueOnce(json(200, { ok: true, result: {} }));
    await call("get_session", {});
    expect(connectionState().gradingDown).toBe(true);
    fetchMock.mockResolvedValueOnce(json(200, { ok: true, result: { attemptId: "a1" } }));
    await runLong("submit_attempt", {}, "k");
    expect(connectionState().gradingDown).toBe(false);
  });

  it("method_not_allowed means this build is older than the host's allowlist", async () => {
    fetchMock.mockResolvedValueOnce(json(403, { ok: false, error: { code: "method_not_allowed", message: "m", retryable: false } }));
    await expect(rpcOnce("get_session", {})).rejects.toMatchObject({ code: "method_not_allowed" });
    expect(connectionState().stale).toBe(true);
  });
});
