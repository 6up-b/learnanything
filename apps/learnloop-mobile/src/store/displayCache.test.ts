// Mobile v2 §5.4's display cache: a bounded LRU of reader sections, the last copy of the plan and
// lessons, dropped on a new revision and on a 401. And the database upgrade that adds it.
import { beforeEach, describe, expect, it, vi } from "vitest";
import { call } from "../api/http";
import { readCredential, saveCredential } from "./credential";
import { CREDENTIAL_STORE, dbBlocked, OUTBOX_STORE, resetDbForTests, subscribeDbBlocked } from "./db";
import {
  clearDisplayCache,
  dropExtraction,
  getLatest,
  getSection,
  putLatest,
  putSection,
  SECTION_BUDGET_BYTES,
  sectionBytes
} from "./displayCache";
import { addToOutbox, listOutbox } from "./outbox";

const key = (sectionId: string, extractionId = "ext1", revision = "r1") => ({ extractionId, revision, sectionId });
/** A section whose JSON is exactly `bytes` long. */
const sized = (bytes: number) => "x".repeat(bytes - 2);

describe("sections", () => {
  it("keeps what was opened and reads it back", async () => {
    await putSection(key("s1"), { blocks: ["one"] });
    await expect(getSection(key("s1"))).resolves.toEqual({ blocks: ["one"] });
    await expect(getSection(key("s2"))).resolves.toBeNull();
  });

  it("evicts the least recently used past its byte bound, and a read counts as a use", async () => {
    const budget = 300;
    await putSection(key("s1"), sized(100), budget);
    await putSection(key("s2"), sized(100), budget);
    await putSection(key("s3"), sized(100), budget);
    await getSection(key("s1"));
    await putSection(key("s4"), sized(100), budget);
    await expect(getSection(key("s2"))).resolves.toBeNull();
    await expect(getSection(key("s1"))).resolves.not.toBeNull();
    await expect(getSection(key("s3"))).resolves.not.toBeNull();
    await expect(getSection(key("s4"))).resolves.not.toBeNull();
    expect(await sectionBytes()).toBeLessThanOrEqual(budget);
  });

  it("never keeps a section bigger than the whole bound", async () => {
    await expect(putSection(key("s1"), sized(400), 300)).resolves.toBe(false);
    await expect(getSection(key("s1"))).resolves.toBeNull();
  });

  it("a new revision drops the extraction's older sections, and only those", async () => {
    await putSection(key("s1", "ext1", "r1"), "old");
    await putSection(key("s1", "ext2", "r1"), "other book");
    await putSection(key("s2", "ext1", "r2"), "new");
    await expect(getSection(key("s1", "ext1", "r1"))).resolves.toBeNull();
    await expect(getSection(key("s1", "ext2", "r1"))).resolves.toBe("other book");
    await dropExtraction("ext2");
    await expect(getSection(key("s1", "ext2", "r1"))).resolves.toBeNull();
    await expect(getSection(key("s2", "ext1", "r2"))).resolves.toBe("new");
  });

  it("the bound is §5.4's 50 MB", () => {
    expect(SECTION_BUDGET_BYTES).toBe(50 * 1024 * 1024);
  });
});

it("the plan and a lesson keep their last copy only, outside the section bound", async () => {
  await putLatest("plan", { step: 1 });
  await putLatest("plan", { step: 2 });
  await expect(getLatest("plan")).resolves.toEqual({ step: 2 });
  await expect(getLatest("lesson:l1")).resolves.toBeNull();
  expect(await sectionBytes()).toBe(0);
});

describe("revocation (§1)", () => {
  beforeEach(async () => {
    await saveCredential({ token: "tok", deviceId: "dev", scope: "app" });
  });

  it("a 401 deletes the display cache with the token, and keeps the outbox", async () => {
    await putSection(key("s1"), "kept until revoked");
    await putLatest("plan", { step: 1 });
    await addToOutbox({ clientCaptureId: "c1", kind: "text", text: "x", capturedAt: "t" });
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ ok: false, error: { code: "unauthorized", message: "m", retryable: false } }), { status: 401 })));
    await expect(call("get_session", {})).rejects.toMatchObject({ code: "unauthorized" });
    await expect(readCredential()).resolves.toBeNull();
    await expect(getSection(key("s1"))).resolves.toBeNull();
    await expect(getLatest("plan")).resolves.toBeNull();
    await expect(listOutbox()).resolves.toHaveLength(1);
  });

  it("clearing an empty cache is fine", async () => {
    await expect(clearDisplayCache()).resolves.toBeUndefined();
  });
});

it("opening a version 1 database keeps its token and its waiting captures, and adds the display store", async () => {
  // M2a's database, as an installed phone has it today.
  await new Promise<void>((resolve, reject) => {
    const request = indexedDB.open("learnloop-phone", 1);
    request.onupgradeneeded = () => {
      request.result.createObjectStore(CREDENTIAL_STORE);
      request.result.createObjectStore(OUTBOX_STORE, { keyPath: "clientCaptureId" });
    };
    request.onsuccess = () => {
      const db = request.result;
      const tx = db.transaction([CREDENTIAL_STORE, OUTBOX_STORE], "readwrite");
      tx.objectStore(CREDENTIAL_STORE).put({ token: "old", deviceId: "d", scope: "app" }, "device");
      tx.objectStore(OUTBOX_STORE).put({ clientCaptureId: "c1", kind: "text", text: "waiting", capturedAt: "t" });
      tx.oncomplete = () => {
        db.close();
        resolve();
      };
      tx.onerror = () => reject(tx.error);
    };
    request.onerror = () => reject(request.error);
  });
  resetDbForTests();
  await expect(listOutbox()).resolves.toEqual([{ clientCaptureId: "c1", kind: "text", text: "waiting", capturedAt: "t" }]);
  await expect(readCredential()).resolves.toEqual({ token: "old", deviceId: "d", scope: "app" });
  await putSection(key("s1"), "works");
  await expect(getSection(key("s1"))).resolves.toBe("works");
});

describe("an upgrade another tab holds up (Codex review of V1, F2)", () => {
  /** M2a's database, left open in another tab: version 1, and no `versionchange` handler. */
  function openVersionOne(): Promise<IDBDatabase> {
    return new Promise<IDBDatabase>((resolve, reject) => {
      const request = indexedDB.open("learnloop-phone", 1);
      request.onupgradeneeded = () => {
        request.result.createObjectStore(CREDENTIAL_STORE);
        request.result.createObjectStore(OUTBOX_STORE, { keyPath: "clientCaptureId" });
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  it("says it is blocked while the old connection stays open, and carries on when it closes", async () => {
    const old = await openVersionOne();
    resetDbForTests();
    const seen: boolean[] = [];
    const stop = subscribeDbBlocked(() => seen.push(dbBlocked()));
    const reading = readCredential();
    await vi.waitFor(() => expect(dbBlocked()).toBe(true));
    old.close();
    await expect(reading).resolves.toBeNull();
    expect(dbBlocked()).toBe(false);
    expect(seen).toEqual([true, false]);
    stop();
  });

  it("this build closes its own connection when a newer build asks for the database", async () => {
    await putLatest("plan", { step: 1 });
    const newer = await new Promise<IDBDatabase>((resolve, reject) => {
      // V4's build is version 3 (the intents store), so a newer one asks for 4.
      const request = indexedDB.open("learnloop-phone", 4);
      request.onblocked = () => reject(new Error("blocked by this build's open connection"));
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    expect(newer.version).toBe(4);
    newer.close();
  });
});
