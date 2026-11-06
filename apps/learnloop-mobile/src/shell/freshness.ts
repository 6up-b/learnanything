// A stale cached app (mobile v2 §5.2). The host serves this app itself, so the two normally move
// together; the risk is a shell the service worker kept from before the allowlist moved. On open
// and on resume the app reads `GET /api/v1/meta` and compares the digest with the one this build
// was made against. A mismatch, or a `method_not_allowed` meanwhile, shows one line: *LearnLoop was
// updated.* with a Reload.
import { getJson } from "../api/http";
import { ALLOWLIST_DIGEST } from "../api/phoneMethods";
import { markStale } from "./connection";

export interface HostMeta {
  readonly host_version: string;
  readonly api_version: number;
  readonly allowlist_digest: string;
  readonly schema_version: number;
}

/** True when the host's allowlist is not this build's. An unreadable meta says nothing. */
export async function checkFreshness(): Promise<boolean> {
  let meta: HostMeta;
  try {
    meta = await getJson<HostMeta>("/api/v1/meta");
  } catch {
    return false;
  }
  if (meta.allowlist_digest === ALLOWLIST_DIGEST) return false;
  markStale();
  return true;
}

/** Swappable, because a test cannot navigate. */
export const reloader = { reload: (): void => window.location.reload() };

/**
 * Ask the service worker for the new build, then reload. The worker fetches the shell network
 * first, so the reload gets the host's current build whether or not the update lands first.
 */
export async function reloadApp(): Promise<void> {
  try {
    const registration = await navigator.serviceWorker?.getRegistration?.("/app/");
    await registration?.update();
  } catch {
    // An old worker still answers network first.
  }
  reloader.reload();
}
