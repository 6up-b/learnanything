import { beforeEach, describe, expect, it, vi } from "vitest";
import { readCredential, saveCredential } from "./credential";
import { addToOutbox, flushOutbox, listOutbox, removeFromOutbox, requestFor, type OutboxRecord } from "./outbox";
import { resetCredentialForTests } from "./credential";

const fetchMock = vi.fn<typeof fetch>();

const record = (id: string, extra: Partial<OutboxRecord> = {}): OutboxRecord => ({
  clientCaptureId: id, kind: "text", text: `text ${id}`, capturedAt: "2026-11-03T00:00:00Z", ...extra
});

function respond(status: number, message = "m"): Response {
  return new Response(JSON.stringify({ ok: status < 300, error: { code: "x", message } }), { status });
}

beforeEach(async () => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  await saveCredential({ token: "tok", deviceId: "dev", scope: "app" });
});

describe("the outbox (§7)", () => {
  it("survives a reopened app: it is IndexedDB, not memory", async () => {
    await addToOutbox(record("a"));
    resetCredentialForTests();
    await expect(listOutbox()).resolves.toEqual([record("a")]);
  });

  it.each([200, 201])("a %i removes the record", async (status) => {
    await addToOutbox(record("a"));
    fetchMock.mockResolvedValueOnce(respond(status));
    await expect(flushOutbox()).resolves.toEqual({ reason: "drained" });
    await expect(listOutbox()).resolves.toEqual([]);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/v1/capture");
    expect(JSON.parse(init?.body as string)).toMatchObject({ client_capture_id: "a", kind: "text", text: "text a" });
  });

  it.each([429, 500, 503])("a %i keeps it for a later flush", async (status) => {
    await addToOutbox(record("a"));
    fetchMock.mockResolvedValueOnce(respond(status));
    await expect(flushOutbox()).resolves.toEqual({ reason: "offline" });
    await expect(listOutbox()).resolves.toEqual([record("a")]);
  });

  it("a network error keeps it, and stops the pass", async () => {
    await addToOutbox(record("a"));
    await addToOutbox(record("b"));
    fetchMock.mockRejectedValueOnce(new TypeError("offline"));
    await expect(flushOutbox()).resolves.toEqual({ reason: "offline" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await expect(listOutbox()).resolves.toHaveLength(2);
  });

  it("a 401 stops, drops the token, keeps the outbox and counts it for the pairing screen", async () => {
    await addToOutbox(record("a"));
    await addToOutbox(record("b"));
    fetchMock.mockResolvedValueOnce(respond(401));
    await expect(flushOutbox()).resolves.toEqual({ reason: "not_paired", waiting: 2 });
    await expect(readCredential()).resolves.toBeNull();
    await expect(listOutbox()).resolves.toHaveLength(2);
  });

  it("a 403 stops with its reason", async () => {
    await addToOutbox(record("a"));
    fetchMock.mockResolvedValueOnce(respond(403, "not this host"));
    await expect(flushOutbox()).resolves.toEqual({ reason: "forbidden", message: "not this host" });
    await expect(listOutbox()).resolves.toHaveLength(1);
  });

  it("a 409 is flagged for the learner, and the pass goes on", async () => {
    await addToOutbox(record("a"));
    await addToOutbox(record("b"));
    fetchMock.mockResolvedValueOnce(respond(409, "capture_conflict")).mockResolvedValueOnce(respond(201));
    await expect(flushOutbox()).resolves.toEqual({ reason: "drained" });
    const left = await listOutbox();
    expect(left).toHaveLength(1);
    expect(left[0].problem).toEqual({ kind: "conflict", message: "capture_conflict" });
  });

  it.each([413, 415, 422])("a %i is refused for good, kept until dismissed, and never re-sent", async (status) => {
    await addToOutbox(record("a"));
    fetchMock.mockResolvedValueOnce(respond(status, "too large"));
    await flushOutbox();
    expect((await listOutbox())[0].problem).toEqual({ kind: "refused", message: "too large" });
    await flushOutbox();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await removeFromOutbox("a");
    await expect(listOutbox()).resolves.toEqual([]);
  });

  it("sends an image as multipart with its fields", () => {
    // The request itself: a fake IndexedDB's clone of a jsdom Blob is no Blob.
    const { body, headers } = requestFor(record("a", { kind: "image", text: undefined, media: new Blob(["jpeg"], { type: "image/jpeg" }), note: "n" }));
    const form = body as FormData;
    expect(headers).toEqual({}); // the browser writes the multipart boundary
    expect(form.get("kind")).toBe("image");
    expect(form.get("note")).toBe("n");
    expect(form.get("file")).toBeTruthy();
  });

  it("with no token, sends nothing and says how many wait", async () => {
    const { deleteCredential } = await import("./credential");
    await deleteCredential();
    await addToOutbox(record("a"));
    await expect(flushOutbox()).resolves.toEqual({ reason: "not_paired", waiting: 1 });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
