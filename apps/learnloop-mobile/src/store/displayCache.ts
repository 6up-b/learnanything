// The display cache (mobile v2 §1, §5.4): the last copy of what the host showed, never
// authoritative. Every screen re-reads the host when it can and says when it shows this copy.
//
// Two kinds of entry:
// * reader sections, keyed by extraction, revision and section, in a least-recently-used set
//   bounded by bytes. A new revision of an extraction drops that extraction's older sections.
// * a "latest" copy per name (the plan step, a lesson's view): the last one only.
//
// A 401 deletes all of it, with the session cache (`http.ts`, `outbox.ts`). Nothing here is a bulk
// export: a screen caches what it opened and one section ahead, never a whole book (§5.4).
import { DISPLAY_STORE, openDb, txRequest } from "./db";

/** §5.4's `keep` bound on reader sections: 50 MB of UTF-8 JSON. Page images are the service worker's. */
export const SECTION_BUDGET_BYTES = 50 * 1024 * 1024;

export interface SectionKey {
  readonly extractionId: string;
  readonly revision: string;
  readonly sectionId: string;
}

interface Entry {
  readonly key: string;
  readonly kind: "section" | "latest";
  readonly extractionId?: string;
  readonly revision?: string;
  readonly value: unknown;
  readonly bytes: number;
  readonly usedAt: number;
}

let lastUse = 0;
/** Strictly increasing, so two uses in one millisecond still order. */
function useStamp(): number {
  lastUse = Math.max(Date.now(), lastUse + 1);
  return lastUse;
}

const sectionKey = (key: SectionKey) => `section:${key.extractionId}:${key.revision}:${key.sectionId}`;
const latestKey = (name: string) => `latest:${name}`;

function sizeOf(value: unknown): number {
  return new TextEncoder().encode(JSON.stringify(value) ?? "").length;
}

function all(): Promise<Entry[]> {
  return txRequest<Entry[]>(DISPLAY_STORE, "readonly", (objects) => objects.getAll());
}

/** Deletes and one put, in one transaction: the bound holds at every commit. */
async function writeAll(deletes: readonly string[], put: Entry | null): Promise<void> {
  const db = await openDb();
  await new Promise<void>((resolve, reject) => {
    const transaction = db.transaction(DISPLAY_STORE, "readwrite");
    const objects = transaction.objectStore(DISPLAY_STORE);
    for (const key of deletes) objects.delete(key);
    if (put) objects.put(put);
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
    transaction.onabort = () => reject(transaction.error ?? new Error("IndexedDB write was aborted."));
  });
}

/**
 * Keep one section. Older revisions of its extraction go, then the least recently used sections
 * until the set fits `budget`. A section bigger than the whole budget is not kept at all.
 */
export async function putSection(key: SectionKey, value: unknown, budget = SECTION_BUDGET_BYTES): Promise<boolean> {
  const bytes = sizeOf(value);
  if (bytes > budget) return false;
  const entry: Entry = { key: sectionKey(key), kind: "section", extractionId: key.extractionId, revision: key.revision, value, bytes, usedAt: useStamp() };
  const sections = (await all()).filter((one) => one.kind === "section" && one.key !== entry.key);
  const stale = sections.filter((one) => one.extractionId === key.extractionId && one.revision !== key.revision);
  const kept = sections.filter((one) => !stale.includes(one)).sort((a, b) => a.usedAt - b.usedAt);
  const evicted: string[] = stale.map((one) => one.key);
  let total = kept.reduce((sum, one) => sum + one.bytes, 0) + bytes;
  for (const one of kept) {
    if (total <= budget) break;
    evicted.push(one.key);
    total -= one.bytes;
  }
  await writeAll(evicted, entry);
  return true;
}

export async function getSection<T>(key: SectionKey): Promise<T | null> {
  const entry = await txRequest<Entry | undefined>(DISPLAY_STORE, "readonly", (objects) => objects.get(sectionKey(key)));
  if (!entry) return null;
  await writeAll([], { ...entry, usedAt: useStamp() });
  return entry.value as T;
}

/** Drop every cached section of an extraction (its revision changed under a screen that knows it). */
export async function dropExtraction(extractionId: string): Promise<void> {
  const gone = (await all()).filter((one) => one.kind === "section" && one.extractionId === extractionId).map((one) => one.key);
  await writeAll(gone, null);
}

/** The last copy of something with one current value: the plan step, a lesson's view. */
export async function putLatest(name: string, value: unknown): Promise<void> {
  await writeAll([], { key: latestKey(name), kind: "latest", value, bytes: sizeOf(value), usedAt: useStamp() });
}

export async function getLatest<T>(name: string): Promise<T | null> {
  const entry = await txRequest<Entry | undefined>(DISPLAY_STORE, "readonly", (objects) => objects.get(latestKey(name)));
  return entry ? (entry.value as T) : null;
}

/** §1: revocation deletes the display cache with the token; the outbox stays. */
export async function clearDisplayCache(): Promise<void> {
  await txRequest(DISPLAY_STORE, "readwrite", (objects) => objects.clear());
}

/** Bytes held in sections, for tests and a future Display sheet line. */
export async function sectionBytes(): Promise<number> {
  return (await all()).filter((one) => one.kind === "section").reduce((sum, one) => sum + one.bytes, 0);
}
