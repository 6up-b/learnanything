// The device's token (§4.2). A 401 deletes it and the session cache and keeps the outbox (§4.4).
import { CREDENTIAL_STORE, txRequest } from "./db";
import { purgePageImages } from "./displayCache";

export interface Credential {
  readonly token: string;
  readonly deviceId: string | null;
  readonly scope: string | null;
}

const KEY = "device";
let cached: Credential | null | undefined;
const listeners = new Set<() => void>();

function publish(next: Credential | null): void {
  cached = next;
  for (const listener of listeners) listener();
}

export function subscribeCredential(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export async function readCredential(): Promise<Credential | null> {
  if (cached !== undefined) return cached;
  const stored = await txRequest<Credential | undefined>(CREDENTIAL_STORE, "readonly", (objects) => objects.get(KEY));
  cached = stored ?? null;
  return cached;
}

export async function saveCredential(credential: Credential): Promise<void> {
  // Codex re-review F1: kept page images are the last pairing's; a new token starts with none, before anything is
  // fetched under it (the service worker's copies are tied to their token as well, `public/sw.js`).
  const previous = await readCredential().catch(() => null);
  if (previous?.token !== credential.token) await purgePageImages().catch(() => undefined);
  await txRequest(CREDENTIAL_STORE, "readwrite", (objects) => objects.put(credential, KEY));
  publish(credential);
}

export async function deleteCredential(): Promise<void> {
  await txRequest(CREDENTIAL_STORE, "readwrite", (objects) => objects.delete(KEY));
  publish(null);
}

/** Forget the in-memory copy, so a test reads IndexedDB again. */
export function resetCredentialForTests(): void {
  cached = undefined;
  listeners.clear();
}

/**
 * The token a pairing link hands over: `/app/#token=…` from the pairing page. A fragment never
 * reaches the server's request line or a log, and it is gone from the address bar before anything
 * else runs. iOS keeps a home-screen app's storage apart from Safari's, so an installed app pairs
 * with the manual code instead (PairScreen).
 */
export async function pickUpFragmentToken(location: Pick<Location, "hash" | "pathname" | "search"> = window.location): Promise<boolean> {
  const params = new URLSearchParams(location.hash.replace(/^#/, ""));
  const token = params.get("token");
  if (!token) return false;
  window.history.replaceState(null, "", location.pathname + location.search);
  await saveCredential({ token, deviceId: params.get("device"), scope: "app" });
  return true;
}
