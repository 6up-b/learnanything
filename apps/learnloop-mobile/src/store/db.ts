// One IndexedDB database for the two things that must survive a closed app (spec §0, §4.2, §7):
// the device token (IndexedDB, so a service worker could read it) and the capture outbox.
const DB_NAME = "learnloop-phone";
const DB_VERSION = 1;
export const CREDENTIAL_STORE = "credential";
export const OUTBOX_STORE = "outbox";

let opened: Promise<IDBDatabase> | null = null;

export function openDb(): Promise<IDBDatabase> {
  if (opened) return opened;
  opened = new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      db.createObjectStore(CREDENTIAL_STORE);
      db.createObjectStore(OUTBOX_STORE, { keyPath: "clientCaptureId" });
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
