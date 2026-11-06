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

export function openDb(): Promise<IDBDatabase> {
  if (opened) return opened;
  opened = new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = (event) => {
      const db = request.result;
      if (event.oldVersion < 1) {
        db.createObjectStore(CREDENTIAL_STORE);
        db.createObjectStore(OUTBOX_STORE, { keyPath: "clientCaptureId" });
      }
      if (event.oldVersion < 2) db.createObjectStore(DISPLAY_STORE, { keyPath: "key" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => {
      opened = null;
      reject(request.error ?? new Error("IndexedDB is not available."));
    };
  });
  return opened;
}

/** Forget the open handle, so a test's fresh fake IndexedDB is the one used. */
export function resetDbForTests(): void {
  opened = null;
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
