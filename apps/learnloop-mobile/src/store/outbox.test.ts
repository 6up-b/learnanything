import { beforeEach, describe, expect, it, vi } from "vitest";
import { readCredential, saveCredential } from "./credential";
import {
  addToOutbox,
  CAPTURE_INTENT,
  flushOutbox,
  INTENT_KINDS,
  listOutbox,
  removeFromOutbox,
  requestFor,
  responseClass,
  type IntentKind,
  type OutboxProblem,
  type OutboxRecord
} from "./outbox";
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

  it("a capture saved twice under one id is one record: the id is what the host dedupes on", async () => {
    await addToOutbox(record("a"));
    await addToOutbox(record("a", { text: "edited" }));
    await expect(listOutbox()).resolves.toEqual([record("a", { text: "edited" })]);
  });
});

describe("the outbox generalized to intents (mobile v2 §5.4)", () => {
  /** A second kind of intent, in memory, standing in for the ones later stages add. */
  function memoryKind(name: string, ids: string[]) {
    const records = ids.map((id) => ({ id, problem: null as OutboxProblem | null }));
    const sent: string[] = [];
    const kind: IntentKind<{ id: string; problem: OutboxProblem | null }> = {
      name,
      list: async () => records,
      clientId: (one) => one.id,
      problem: (one) => one.problem,
      send: async (one) => {
        sent.push(`${name}:${one.id}`);
        return fetch(`/${name}`, { method: "POST" });
      },
      remove: async (one) => void records.splice(records.indexOf(one), 1),
      keepWithProblem: async (one, problem) => void (one.problem = problem)
    };
    return { kind: kind as IntentKind<never>, records, sent };
  }

  it("V1 flushes one kind, the capture, exactly as built", () => {
    expect(INTENT_KINDS).toEqual([CAPTURE_INTENT]);
  });

  it("every kind together, oldest client id first", async () => {
    const first = memoryKind("progress", ["01B", "01D"]);
    const second = memoryKind("activity", ["01A", "01C"]);
    fetchMock.mockImplementation(async () => respond(201));
    await expect(flushOutbox([first.kind, second.kind])).resolves.toEqual({ reason: "drained" });
    const order = fetchMock.mock.calls.map(([url]) => String(url));
    expect(order).toEqual(["/activity", "/progress", "/activity", "/progress"]);
    expect(first.records).toEqual([]);
    expect(second.records).toEqual([]);
  });

  it("the response classes are §7's for every kind: a stop keeps the rest in order", async () => {
    const one = memoryKind("progress", ["01A", "01B", "01C"]);
    fetchMock.mockResolvedValueOnce(respond(201)).mockResolvedValueOnce(respond(409, "conflict")).mockResolvedValueOnce(respond(503));
    await expect(flushOutbox([one.kind])).resolves.toEqual({ reason: "offline" });
    expect(one.records.map((record) => [record.id, record.problem?.kind ?? null])).toEqual([["01B", "conflict"], ["01C", null]]);
  });

  it.each([
    [200, "sent"], [201, "sent"], [429, "stop_offline"], [500, "stop_offline"], [503, "stop_offline"], [401, "stop_unpaired"],
    [403, "stop_forbidden"], [409, "conflict"], [413, "refused"], [422, "refused"]
  ])("%i is %s", (status, kind) => {
    expect(responseClass(status)).toBe(kind);
  });
});
