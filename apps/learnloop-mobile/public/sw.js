// The app shell, for a phone with no desktop in reach (spec §4.6, §7). Only /app/ is cached:
// never /api, /rpc or /pair, which is the shape the host's Cache-Control also says. Scope is
// /app/ by this file's location, so those paths never reach this worker anyway; the check is
// the second lock.
"use strict";

// The build's hash, written in by the build (src/shell/swBuild.ts), so every build is a new worker
// whose activate drops the last build's cache (mobile v2 §5.2). "dev" in the source.
const BUILD = "dev";
const SHELL_CACHE = `learnloop-shell-${BUILD}`;

function isShell(url) {
  return url.origin === self.location.origin && url.pathname.startsWith("/app/");
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
      .then((names) => Promise.all(names.filter((name) => name !== SHELL_CACHE).map((name) => caches.delete(name))))
      .then(() => self.clients.claim()),
  );
});

async function cachedShell(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  return request.mode === "navigate" ? caches.match("/app/") : undefined;
}

// Network first, so a new build is what a reachable desktop serves; the cache answers only when
// the desktop is asleep, the tailnet is down, or Serve is up and answers 5xx for a host behind it
// that is stopped or restarting. A 4xx is the host's own answer (a refused token, say) and stands.
self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET" || !isShell(new URL(request.url))) return;
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
