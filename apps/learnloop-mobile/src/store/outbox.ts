// The outbox (spec §7), generalized to intents by mobile v2 §5.4. A capture is saved here first;
// a record leaves only on 201 or 200. Flushed on open, on focus and every minute while open,
// because iOS has no Background Sync, and the outbox is durable only for the home-screen app.
//
// An intent may wait here only if all three hold (§5.4):
//   1. replaying it later means the same as sending it now;
//   2. it is idempotent by a client id;
//   3. nothing waits on its reply.
// Each kind of intent says how it is listed, sent and settled (`IntentKind`); the response classes
// of §7 are shared by all of them. V1 registers one kind, the capture, exactly as M1/M2a built it:
// its store, its request and its key are unchanged. Reading progress, activity, dose events, a
// kept comparison's take and hypothesis marks join in their own stages.
import { markReachable } from "../shell/connection";
import { deleteCredential, readCredential } from "./credential";
import { clearDisplayCache } from "./displayCache";
import { clearSessionCache } from "./sessionCache";
import { OUTBOX_STORE, txRequest } from "./db";

export interface OutboxRecord {
  readonly clientCaptureId: string;
  readonly kind: "text" | "url" | "image";
  readonly text?: string;
  readonly url?: string;
  readonly note?: string;
  readonly capturedAt: string;
  /** The re-encoded JPEG of an image capture (§4.4). */
  readonly media?: Blob;
  /** Why this record stopped: a conflict to look at, or a refusal to dismiss. */
  readonly problem?: OutboxProblem | null;
}

export interface OutboxProblem {
  readonly kind: "conflict" | "refused";
  readonly message: string;
}

export type FlushStop =
  | { readonly reason: "drained" }
  | { readonly reason: "offline" }
  | { readonly reason: "not_paired"; readonly waiting: number }
  | { readonly reason: "forbidden"; readonly message: string };

/** One kind of intent the outbox can hold (§5.4). */
export interface IntentKind<R> {
  readonly name: string;
  /** Every record of this kind, problems included. */
  list(): Promise<R[]>;
  /** The client id the host dedupes on; also the outbox's order (ULIDs sort by time). */
  clientId(record: R): string;
  problem(record: R): OutboxProblem | null | undefined;
  /** One send. A thrown error is no answer: the desktop is away. */
  send(record: R, token: string): Promise<Response>;
  remove(record: R): Promise<void>;
  keepWithProblem(record: R, problem: OutboxProblem): Promise<void>;
}

export function listOutbox(): Promise<OutboxRecord[]> {
  return txRequest<OutboxRecord[]>(OUTBOX_STORE, "readonly", (objects) => objects.getAll());
}

export async function addToOutbox(record: OutboxRecord): Promise<void> {
  await txRequest(OUTBOX_STORE, "readwrite", (objects) => objects.put(record));
}

export async function removeFromOutbox(clientCaptureId: string): Promise<void> {
  await txRequest(OUTBOX_STORE, "readwrite", (objects) => objects.delete(clientCaptureId));
}

export function requestFor(record: OutboxRecord): { body: BodyInit; headers: Record<string, string> } {
  const fields: Record<string, string> = { client_capture_id: record.clientCaptureId, kind: record.kind, captured_at: record.capturedAt };
  if (record.text) fields.text = record.text;
  if (record.url) fields.url = record.url;
  if (record.note) fields.note = record.note;
  if (record.media) {
    const form = new FormData();
    for (const [key, value] of Object.entries(fields)) form.append(key, value);
    form.append("file", record.media, `${record.clientCaptureId}.jpg`);
    return { body: form, headers: {} };
  }
  return { body: JSON.stringify(fields), headers: { "Content-Type": "application/json" } };
}

/** The capture, as built: `POST /api/v1/capture`, idempotent by `client_capture_id`. */
export const CAPTURE_INTENT: IntentKind<OutboxRecord> = {
  name: "capture",
  list: listOutbox,
  clientId: (record) => record.clientCaptureId,
  problem: (record) => record.problem,
  send: (record, token) => {
    const { body, headers } = requestFor(record);
    return fetch("/api/v1/capture", {
      method: "POST",
      credentials: "omit",
      cache: "no-store",
      headers: { ...headers, Authorization: `Bearer ${token}` },
      body
    });
  },
  remove: (record) => removeFromOutbox(record.clientCaptureId),
  keepWithProblem: (record, problem) => addToOutbox({ ...record, problem })
};

/** Every kind the outbox flushes. A kind is added here only if it meets the three rules above. */
export const INTENT_KINDS: readonly IntentKind<never>[] = [CAPTURE_INTENT as IntentKind<never>];

/** §7's response classes, for every intent: what one answer means for the record and the flush. */
export type ResponseClass = "sent" | "stop_offline" | "stop_unpaired" | "stop_forbidden" | "conflict" | "refused";

export function responseClass(status: number): ResponseClass {
  if (status === 200 || status === 201) return "sent";
  if (status === 429 || status >= 500) return "stop_offline";
  if (status === 401) return "stop_unpaired";
  if (status === 403) return "stop_forbidden";
  if (status === 409) return "conflict";
  return "refused";
}

interface Pending {
  readonly kind: IntentKind<never>;
  readonly record: never;
  readonly id: string;
}

/** What is waiting to go, every kind together, oldest first. */
export async function pendingIntents(kinds: readonly IntentKind<never>[] = INTENT_KINDS): Promise<Pending[]> {
  const lists = await Promise.all(
    kinds.map(async (kind) =>
      (await kind.list()).filter((record) => !kind.problem(record)).map((record) => ({ kind, record, id: kind.clientId(record) }))
    )
  );
  return lists.flat().sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
}

let flushing: Promise<FlushStop> | null = null;

/** One pass over the outbox, oldest first, under §7's table. Only one pass runs at a time. */
export function flushOutbox(kinds: readonly IntentKind<never>[] = INTENT_KINDS): Promise<FlushStop> {
  if (!flushing) {
    flushing = runFlush(kinds).finally(() => {
      flushing = null;
    });
  }
  return flushing;
}

async function runFlush(kinds: readonly IntentKind<never>[]): Promise<FlushStop> {
  const pending = await pendingIntents(kinds);
  const credential = await readCredential();
  if (!credential) {
    return pending.length ? { reason: "not_paired", waiting: pending.length } : { reason: "drained" };
  }
  for (const { kind, record } of pending) {
    let response: Response;
    try {
      response = await kind.send(record, credential.token);
    } catch {
      return { reason: "offline" };
    }
    const status = response.status;
    switch (responseClass(status)) {
      case "sent":
        markReachable();
        await kind.remove(record);
        continue;
      case "stop_offline":
        return { reason: "offline" };
      case "stop_unpaired":
        await deleteCredential();
        clearSessionCache();
        await clearDisplayCache().catch(() => undefined);
        return { reason: "not_paired", waiting: (await pendingIntents(kinds)).length };
      case "stop_forbidden":
        return { reason: "forbidden", message: await messageOf(response) };
      case "conflict":
        await kind.keepWithProblem(record, { kind: "conflict", message: await messageOf(response) });
        continue;
      case "refused":
        await kind.keepWithProblem(record, { kind: "refused", message: await messageOf(response) });
        continue;
    }
  }
  return { reason: "drained" };
}

async function messageOf(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return String(body?.error?.message ?? `The desktop refused this (${response.status}).`);
  } catch {
    return `The desktop refused this (${response.status}).`;
  }
}
