// One IndexedDB database for what must survive a closed app (spec §0, §4.2, §7): the device token
// (IndexedDB, so a service worker could read it), the capture outbox, and since mobile v2 (§5.4) the
// display cache. Version 2 only adds the display store: an upgrade from 1 keeps the token and every
// capture still waiting to send.
const DB_NAME = "learnloop-phone";
const DB_VERSION = 2;
export const CREDENTIAL_STORE = "credential";
export const OUTBOX_STORE = "outbox";
export const DISPLAY_STORE = "display";

let opened: Promise<IDBDatabase> | null = null;
let blocked = false;
const blockedListeners = new Set<() => void>();

/** True while an upgrade waits on another tab's connection to the older version. */
export function dbBlocked(): boolean {
  return blocked;
}

export function subscribeDbBlocked(listener: () => void): () => void {
  blockedListeners.add(listener);
  return () => blockedListeners.delete(listener);
}

function setBlocked(next: boolean): void {
  if (blocked === next) return;
  blocked = next;
  for (const listener of blockedListeners) listener();
}

/**
 * The open handle. Two tabs of the app share the database, so an upgrade waits on every older
 * connection (Codex review of V1, F2): this one steps aside when a newer build asks, and while an
 * older tab that doesn't (M2a's) holds it, `dbBlocked()` says so. The open finishes by itself once
 * that tab closes.
 */
export function openDb(): Promise<IDBDatabase> {
  if (opened) return opened;
  const opening: Promise<IDBDatabase> = new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onblocked = () => setBlocked(true);
    request.onupgradeneeded = (event) => {
      const db = request.result;
      if (event.oldVersion < 1) {
        db.createObjectStore(CREDENTIAL_STORE);
        db.createObjectStore(OUTBOX_STORE, { keyPath: "clientCaptureId" });
      }
      if (event.oldVersion < 2) db.createObjectStore(DISPLAY_STORE, { keyPath: "key" });
    };
    request.onsuccess = () => {
      const db = request.result;
      db.onversionchange = () => {
        // A newer build in another tab: close, so its upgrade isn't blocked by this one. The next
        // open here meets the newer version, and the meta check offers the reload (§5.2).
        db.close();
        if (opened === opening) opened = null;
      };
      setBlocked(false);
      resolve(db);
    };
    request.onerror = () => {
      if (opened === opening) opened = null;
      setBlocked(false);
      reject(request.error ?? new Error("IndexedDB is not available."));
    };
  });
  opened = opening;
  return opening;
}

/** Forget the open handle, so a test's fresh fake IndexedDB is the one used. */
export function resetDbForTests(): void {
  opened = null;
  blocked = false;
}

export function txRequest<T>(store: string, mode: IDBTransactionMode, run: (objects: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  return openDb().then(
    (db) =>
      new Promise<T>((resolve, reject) => {
        const transaction = db.transaction(store, mode);
        const request = run(transaction.objectStore(store));
        // Resolved on the transaction's commit: a quota error surfaces here, not silently.
        transaction.oncomplete = () => resolve(request.result);
        transaction.onerror = () => reject(transaction.error ?? request.error);
        transaction.onabort = () => reject(transaction.error ?? new Error("IndexedDB write was aborted."));
      })
  );
}
