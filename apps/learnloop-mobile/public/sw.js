// The app shell, for a phone with no desktop in reach (spec §4.6, §7). Only /app/ is cached:
// never /api, /rpc or /pair, which is the shape the host's Cache-Control also says. Scope is
// /app/ by this file's location, so those paths never reach this worker anyway; the check is
// the second lock.
//
// One stated exception (mobile v2 §3.3, V4): the page and stored images the media lane serves.
// Their URLs name their content and the host says `immutable`, so a copy is the thing itself; it is
// shown only when the desktop can't be asked (`mediaResponse`).
"use strict";

// The build's hash, written in by the build (src/shell/swBuild.ts), so every build is a new worker
// whose activate drops the last build's cache (mobile v2 §5.2). "dev" in the source.
const BUILD = "dev";
const SHELL_CACHE = `learnloop-shell-${BUILD}`;
// Kept across builds (an image never changes), and cleared by the page on a 401, on a new token and when a
// reading's protection changes (`src/store/displayCache.ts`, PAGE_CACHE). v2 (Codex re-review F1): every copy in it
// is tied to the token it was fetched under (`Vary: Authorization`); v1, which held copies tied to none, is not
// carried over (activate drops every other name).
const PAGE_CACHE = "learnloop-pages-v2";
// A `keep` bound on the images kept: about the display cache's 50 MB of pages at 1080 px.
const PAGE_CACHE_ENTRIES = 300;

function isShell(url) {
  return url.origin === self.location.origin && url.pathname.startsWith("/app/");
}

function isMedia(url) {
  return url.origin === self.location.origin &&
    (url.pathname.startsWith("/api/v1/reader/page/") || url.pathname.startsWith("/api/v1/assets/"));
}

// The shell and the files it names, so a first visit already works with the desktop asleep. A
// failure here is no failure of the app: the next load caches what it fetches.
async function precacheShell() {
  const cache = await caches.open(SHELL_CACHE);
  const response = await fetch("/app/", { cache: "no-cache" });
  if (!response.ok) return;
  const html = await response.clone().text();
  await cache.put("/app/", response);
  const assets = html.match(/\/app\/(?:assets\/[^"']+|manifest\.webmanifest)/g) ?? [];
  await Promise.all(assets.map((asset) => cache.add(asset).catch(() => undefined)));
}

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(precacheShell().catch(() => undefined));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((names) => Promise.all(names.filter((name) => name !== SHELL_CACHE && name !== PAGE_CACHE)
        .map((name) => caches.delete(name))))
      .then(() => self.clients.claim()),
  );
});

async function cachedShell(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  return request.mode === "navigate" ? caches.match("/app/") : undefined;
}

async function trimPages(cache) {
  const keys = await cache.keys();
  // Insertion order: the oldest go first.
  for (const key of keys.slice(0, Math.max(0, keys.length - PAGE_CACHE_ENTRIES))) await cache.delete(key);
}

// Network first, revalidated (Codex review of V4, F1): an image's bytes never change, but whether this phone may
// see it does (a mark made on the desktop, a revoked token), so while the desktop answers every view asks it again
// (`no-cache`: past the browser's own cache too; the host answers a matching copy with a bodiless 304 after its
// checks). Only a 200 the host marked immutable is kept, and the copy is only the offline fallback: no answer at
// all, or Serve's 502/504 for a host that is down, or the host busy. A refusal is the answer, and the copy goes.
const GATEWAY_DOWN = [502, 504];

async function hostCode(response) {
  try {
    const body = await response.clone().json();
    return body && body.error ? body.error.code : null;
  } catch (error) {
    return null;
  }
}

// Codex re-review F1: a copy is one token's. The host says so (`Vary: Authorization`), and the Cache API then
// matches a request only under the token the copy was fetched with; a copy that says nothing of it is never kept
// and never answers (the page also drops the whole cache on a new token, `src/store/credential.ts`).
function tokenBound(response) {
  return (response.headers.get("Vary") || "").split(",").some((name) => name.trim().toLowerCase() === "authorization");
}

async function keptCopy(cache, request) {
  const copy = await cache.match(request);
  if (!copy) return undefined;
  if (tokenBound(copy)) return copy;
  await cache.delete(request);
  return undefined;
}

async function mediaResponse(request) {
  const cache = await caches.open(PAGE_CACHE);
  let response;
  try {
    response = await fetch(request, { cache: "no-cache" });
  } catch (error) {
    return (await keptCopy(cache, request)) || Response.error();
  }
  if (response.status === 200 && (response.headers.get("Cache-Control") || "").includes("immutable")) {
    if (tokenBound(response)) {
      await cache.put(request, response.clone());
      await trimPages(cache);
    }
    return response;
  }
  if (GATEWAY_DOWN.includes(response.status)) return (await keptCopy(cache, request)) || response;
  if (response.status === 503) {
    // The host is up and says why. Its vault changing under it may be a mark being made: no copy then.
    if ((await hostCode(response)) === "vault_unsettled") return response;
    return (await keptCopy(cache, request)) || response;
  }
  if (response.status >= 400 && response.status < 500) await cache.delete(request);
  return response;
}

// Network first, so a new build is what a reachable desktop serves; the cache answers only when
// the desktop is asleep, the tailnet is down, or Serve is up and answers 5xx for a host behind it
// that is stopped or restarting. A 4xx is the host's own answer (a refused token, say) and stands.
self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (isMedia(url)) {
    event.respondWith(mediaResponse(request));
    return;
  }
  if (!isShell(url)) return;
  event.respondWith(
    fetch(request)
      .then(async (response) => {
        if (response.ok) {
          const copy = response.clone();
          event.waitUntil(caches.open(SHELL_CACHE).then((cache) => cache.put(request, copy)));
        }
        if (response.status >= 500) return (await cachedShell(request)) ?? response;
        return response;
      })
      .catch(async () => (await cachedShell(request)) ?? Response.error()),
  );
});
