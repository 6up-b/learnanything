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
// its store, its request and its key are unchanged. V4 adds the Reader's (`READER_INTENT`): reading
// progress, activity and dose events. A kept comparison's take and hypothesis marks join in their own
// stages.
import { phone, type ProgressInput } from "../api/phone";
import { markReachable } from "../shell/connection";
import { deleteCredential, readCredential } from "./credential";
import { clearDisplayCache } from "./displayCache";
import { clearSessionCache } from "./sessionCache";
import { INTENT_STORE, openDb, OUTBOX_STORE, txRequest } from "./db";

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

// ── Mobile v2 V4 (§3.4, §5.4): the Reader's intents. ──
// Each meets the three rules: reading progress is a monotonic upsert on the host (queued reports of a section are
// merged into one, their larger counts and any completion, Codex review F6); activity events carry their own
// `occurredAt`, so a late send keeps their time; a dose event names its draw. Each is a job on the host keyed by the
// intent's id (`mobile_jobs`): a replay after a lost reply is coalesced, never recorded twice (its rows and the job's
// receipt commit together, F5), and the job's end (a 200) is its delivery: an accepted job (202) is asked again
// under its key until it ends (F7).

export type ReaderIntentMethod = "reader.mark_section_progress" | "reader.log_activity" | "reader.dose_offer_event";

export interface ReaderIntentRecord {
  /** A ULID: the request id the host dedupes on, and the outbox's order. */
  readonly id: string;
  readonly method: ReaderIntentMethod;
  readonly params: Record<string, unknown>;
  /** Progress only: `extraction:section`, so a newer report replaces an unsent older one. */
  readonly coalesce?: string | null;
  readonly problem?: OutboxProblem | null;
}

export function listReaderIntents(): Promise<ReaderIntentRecord[]> {
  return txRequest<ReaderIntentRecord[]>(INTENT_STORE, "readonly", (objects) => objects.getAll());
}

/** Progress is monotonic (§3.4): two reports of one section are their larger counts, and a completion or a reveal
 *  either of them carried (Codex review F6: a later, smaller report never erases a queued completion). */
function mergeProgress(older: Record<string, unknown>, newer: Record<string, unknown>): Record<string, unknown> {
  const merged: Record<string, unknown> = { ...older, ...newer };
  for (const count of ["spansSeen", "spanCount"]) {
    const values = [older[count], newer[count]].filter((value): value is number => typeof value === "number");
    if (values.length) merged[count] = Math.max(...values);
  }
  for (const flag of ["completed", "revealed"]) {
    if (older[flag] === true || newer[flag] === true) merged[flag] = true;
  }
  return merged;
}

/** Queue one reader intent. A progress report takes the place of the unsent ones for its section, merged into it
 *  monotonically, in one IndexedDB transaction (so a flush never finds the section's report missing). */
export async function addReaderIntent(record: ReaderIntentRecord): Promise<void> {
  if (!record.coalesce) {
    await txRequest(INTENT_STORE, "readwrite", (objects) => objects.put(record));
    return;
  }
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const transaction = db.transaction(INTENT_STORE, "readwrite");
    const objects = transaction.objectStore(INTENT_STORE);
    const listed = objects.getAll();
    listed.onsuccess = () => {
      const older = (listed.result as ReaderIntentRecord[])
        .filter((one) => one.coalesce === record.coalesce && !one.problem)
        .sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
      let params = record.params;
      for (const one of older) {
        params = mergeProgress(one.params, params);
        objects.delete(one.id);
      }
      objects.put({ ...record, params });
    };
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
    transaction.onabort = () => reject(transaction.error ?? new Error("IndexedDB write was aborted."));
  });
}

export async function removeReaderIntent(id: string): Promise<void> {
  await txRequest(INTENT_STORE, "readwrite", (objects) => objects.delete(id));
}

/** A CommandError's code as the HTTP class the host answers it with, for §7's table. */
const STATUS_BY_CODE: Record<string, number> = {
  unauthorized: 401, method_not_allowed: 403, submission_conflict: 409, validation_error: 422, invalid_request: 422,
  host_busy: 503, database_busy: 503, vault_unsettled: 503, schema_mismatch: 503, internal: 500
};

export const READER_INTENT: IntentKind<ReaderIntentRecord> = {
  name: "reader",
  list: listReaderIntents,
  clientId: (record) => record.id,
  problem: (record) => record.problem,
  send: async (record) => {
    const params = record.params as Record<string, never>;
    try {
      const outcome = record.method === "reader.mark_section_progress"
        ? await phone.markProgress(record.params as unknown as ProgressInput, record.id)
        : record.method === "reader.log_activity"
          ? await phone.logActivity(params.events, record.id)
          : await phone.doseOfferEvent(params.drawId, params.event, record.id);
      // Codex review F7: a job accepted (202) is not yet recorded (a busy database can still fail it), so the
      // intent stays and goes again under its key: the host answers the job's end, or runs a retryable failure again.
      return new Response(null, { status: outcome?.kind === "accepted" ? 202 : 200 });
    } catch (error) {
      const command = error as { code?: string; message?: string };
      // No answer at all: the desktop is away (the flush stops and tries again later).
      if (!command || typeof command.code !== "string" || command.code === "desktop_offline") throw error;
      // The reader's switch off: kept, and sent again later (a 5xx stops the flush).
      const status = command.code === "phone_reader_off" ? 503 : STATUS_BY_CODE[command.code] ?? 409;
      return new Response(JSON.stringify({ ok: false, error: { code: command.code, message: command.message ?? command.code } }), {
        status
      });
    }
  },
  remove: (record) => removeReaderIntent(record.id),
  keepWithProblem: (record, problem) =>
    txRequest(INTENT_STORE, "readwrite", (objects) => objects.put({ ...record, problem })).then(() => undefined)
};

/** Every kind the outbox flushes. A kind is added here only if it meets the three rules above. */
export const INTENT_KINDS: readonly IntentKind<never>[] = [
  CAPTURE_INTENT as IntentKind<never>,
  READER_INTENT as unknown as IntentKind<never>
];

/** §7's response classes, for every intent: what one answer means for the record and the flush. */
export type ResponseClass = "sent" | "accepted" | "stop_offline" | "stop_unpaired" | "stop_forbidden" | "conflict" | "refused";

export function responseClass(status: number): ResponseClass {
  if (status === 200 || status === 201) return "sent";
  // Mobile v2 V4 (Codex review F7): a job the host accepted and has not ended. The desktop is there; the record
  // waits for the job's end, which the next flush asks for under the same key.
  if (status === 202) return "accepted";
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
/** A flush asked for while one ran: what was queued meanwhile goes in another pass, not the next minute's. */
let again = false;

/** One pass over the outbox, oldest first, under §7's table. Only one pass runs at a time; one asked for during
 *  it runs right after it (mobile v2 V4: the Reader queues its intents as it goes), while the desktop answers. */
export function flushOutbox(kinds: readonly IntentKind<never>[] = INTENT_KINDS): Promise<FlushStop> {
  if (flushing) {
    again = true;
    return flushing;
  }
  flushing = (async () => {
    let stop: FlushStop;
    do {
      again = false;
      stop = await runFlush(kinds);
    } while (again && stop.reason === "drained");
    return stop;
  })().finally(() => {
    flushing = null;
  });
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
      case "accepted":
        markReachable();
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
