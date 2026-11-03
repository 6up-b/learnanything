// The capture outbox (spec §7). A capture is saved here first; a record leaves only on 201 or 200.
// Flushed on open, on focus and every minute while open, because iOS has no Background Sync, and
// the outbox is durable only for the home-screen app.
import { deleteCredential, readCredential } from "./credential";
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
  readonly problem?: { readonly kind: "conflict" | "refused"; readonly message: string } | null;
}

export type FlushStop =
  | { readonly reason: "drained" }
  | { readonly reason: "offline" }
  | { readonly reason: "not_paired"; readonly waiting: number }
  | { readonly reason: "forbidden"; readonly message: string };

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

let flushing: Promise<FlushStop> | null = null;

/** One pass over the outbox, oldest first, under §7's table. Only one pass runs at a time. */
export function flushOutbox(): Promise<FlushStop> {
  if (!flushing) {
    flushing = runFlush().finally(() => {
      flushing = null;
    });
  }
  return flushing;
}

async function runFlush(): Promise<FlushStop> {
  const records = (await listOutbox()).filter((record) => !record.problem);
  const credential = await readCredential();
  if (!credential) {
    return records.length ? { reason: "not_paired", waiting: records.length } : { reason: "drained" };
  }
  for (const record of records) {
    let response: Response;
    const { body, headers } = requestFor(record);
    try {
      response = await fetch("/api/v1/capture", {
        method: "POST",
        credentials: "omit",
        cache: "no-store",
        headers: { ...headers, Authorization: `Bearer ${credential.token}` },
        body
      });
    } catch {
      return { reason: "offline" };
    }
    const status = response.status;
    if (status === 200 || status === 201) {
      await removeFromOutbox(record.clientCaptureId);
      continue;
    }
    if (status === 429 || status >= 500) return { reason: "offline" };
    if (status === 401) {
      await deleteCredential();
      clearSessionCache();
      return { reason: "not_paired", waiting: (await listOutbox()).filter((one) => !one.problem).length };
    }
    if (status === 403) return { reason: "forbidden", message: await messageOf(response) };
    const message = await messageOf(response);
    await addToOutbox({
      ...record,
      problem: status === 409 ? { kind: "conflict", message } : { kind: "refused", message }
    });
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
