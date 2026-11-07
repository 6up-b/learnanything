import { beforeEach, describe, expect, it, vi } from "vitest";
import source from "../public/sw.js?raw";
import { PAGE_CACHE } from "./store/displayCache";

// The real service worker, run with its globals faked (§4.6): only the shell is ever cached.
let handlers: Record<string, (event: unknown) => void>;
const put = vi.fn();

beforeEach(() => {
  handlers = {};
  put.mockReset();
  const self = {
    location: { origin: "https://desktop.tail.ts.net" },
    addEventListener: (name: string, handler: (event: unknown) => void) => { handlers[name] = handler; },
    skipWaiting: vi.fn(),
    clients: { claim: vi.fn() }
  };
  const caches = { open: async () => ({ put }), match: async () => undefined, keys: async () => [], delete: async () => true };
  new Function("self", "caches", "fetch", "Response", source)(self, caches, async () => new Response("shell", { status: 200 }), Response);
});

function fetchEvent(url: string, method = "GET") {
  const respondWith = vi.fn();
  handlers.fetch({ request: { url, method, mode: "cors" }, respondWith, waitUntil: vi.fn() });
  return respondWith;
}

it.each(["/rpc", "/api/v1/jobs/j1", "/api/v1/queue-revision", "/pair", "/healthz"])("never touches %s", (path) => {
  expect(fetchEvent(`https://desktop.tail.ts.net${path}`)).not.toHaveBeenCalled();
});

it("never touches another origin or a write", () => {
  expect(fetchEvent("https://elsewhere.example/app/x")).not.toHaveBeenCalled();
  expect(fetchEvent("https://desktop.tail.ts.net/app/x", "POST")).not.toHaveBeenCalled();
});

it("answers for the shell", () => {
  expect(fetchEvent("https://desktop.tail.ts.net/app/assets/index.js")).toHaveBeenCalledTimes(1);
});

it("a first visit caches the shell and what it names, and a failure stays quiet", async () => {
  const added: string[] = [];
  const self = { location: { origin: "https://desktop.tail.ts.net" }, addEventListener: (name: string, handler: (event: unknown) => void) => { handlers[name] = handler; }, skipWaiting: vi.fn(), clients: { claim: vi.fn() } };
  const caches = { open: async () => ({ put, add: async (url: string) => { added.push(url); } }), match: async () => undefined, keys: async () => [], delete: async () => true };
  const html = '<script src="/app/assets/index-a.js"></script><link href="/app/assets/index-b.css"><link href="/app/manifest.webmanifest">';
  new Function("self", "caches", "fetch", "Response", source)(self, caches, async () => new Response(html, { status: 200 }), Response);
  const waits: Promise<unknown>[] = [];
  handlers.install({ waitUntil: (work: Promise<unknown>) => waits.push(work) });
  await Promise.all(waits);
  expect(added.sort()).toEqual(["/app/assets/index-a.js", "/app/assets/index-b.css", "/app/manifest.webmanifest"]);
  expect(put).toHaveBeenCalledWith("/app/", expect.anything());
});

describe("a host that is down behind a reachable Serve (Codex review F6)", () => {
  function workerWith(status: number) {
    const shell = new Response("cached shell", { status: 200 });
    const reads: unknown[] = [];
    const self = { location: { origin: "https://desktop.tail.ts.net" }, addEventListener: (name: string, handler: (event: unknown) => void) => { handlers[name] = handler; }, skipWaiting: vi.fn(), clients: { claim: vi.fn() } };
    const caches = {
      open: async () => ({ put }),
      match: async (request: unknown) => {
        reads.push(request);
        return request === "/app/" ? shell : undefined;
      },
      keys: async () => [],
      delete: async () => true
    };
    new Function("self", "caches", "fetch", "Response", source)(self, caches, async () => new Response("from the gateway", { status }), Response);
    return { shell, reads };
  }

  async function navigate() {
    let answered: Promise<Response> | undefined;
    handlers.fetch({
      request: { url: "https://desktop.tail.ts.net/app/", method: "GET", mode: "navigate" },
      respondWith: (response: Promise<Response>) => { answered = response; },
      waitUntil: vi.fn()
    });
    return answered as Promise<Response>;
  }

  it.each([502, 503, 504])("a %i opens the cached shell", async (status) => {
    const { shell } = workerWith(status);
    expect(await navigate()).toBe(shell);
    expect(put).not.toHaveBeenCalled();
  });

  it.each([401, 403, 404])("a %i is an answer, never replaced by the cache", async (status) => {
    const { reads } = workerWith(status);
    expect((await navigate()).status).toBe(status);
    expect(reads).toEqual([]);
  });

  it("with no shell cached the gateway's own answer stands", async () => {
    const self = { location: { origin: "https://desktop.tail.ts.net" }, addEventListener: (name: string, handler: (event: unknown) => void) => { handlers[name] = handler; }, skipWaiting: vi.fn(), clients: { claim: vi.fn() } };
    const caches = { open: async () => ({ put }), match: async () => undefined, keys: async () => [], delete: async () => true };
    new Function("self", "caches", "fetch", "Response", source)(self, caches, async () => new Response("down", { status: 502 }), Response);
    expect((await navigate()).status).toBe(502);
  });
});

describe("the page images (mobile v2 §3.3, V4): the one stated exception", () => {
  function workerFor(answer: () => Response) {
    const stored = new Map<string, Response>();
    const opened: string[] = [];
    const self = { location: { origin: "https://desktop.tail.ts.net" }, addEventListener: (name: string, handler: (event: unknown) => void) => { handlers[name] = handler; }, skipWaiting: vi.fn(), clients: { claim: vi.fn() } };
    const caches = {
      open: async (name: string) => {
        opened.push(name);
        return {
          put: async (request: { url: string }, response: Response) => { stored.set(request.url, response); },
          match: async (request: { url: string }) => stored.get(request.url),
          keys: async () => [...stored.keys()].map((url) => ({ url })),
          delete: async (request: { url: string }) => stored.delete(request.url)
        };
      },
      match: async () => undefined, keys: async () => [], delete: async () => true
    };
    const network = vi.fn(async () => answer());
    new Function("self", "caches", "fetch", "Response", source)(self, caches, network, Response);
    return { stored, opened, network };
  }

  async function get(url: string): Promise<Response> {
    let answered: Promise<Response> | undefined;
    handlers.fetch({ request: { url, method: "GET", mode: "cors" }, respondWith: (response: Promise<Response>) => { answered = response; }, waitUntil: vi.fn() });
    expect(answered).toBeDefined();
    return answered as Promise<Response>;
  }

  const PAGE = "https://desktop.tail.ts.net/api/v1/reader/page/ext1/1?w=720";

  const IMMUTABLE = { "Cache-Control": "private, max-age=31536000, immutable", Vary: "Authorization" };
  // The page cache's name: the page's own (`src/store/displayCache.ts`), so the two never drift.
  const PAGES = PAGE_CACHE;

  it("keeps an immutable page, and asks the host again at every view while it answers (Codex review F1)", async () => {
    const { stored, opened, network } = workerFor(() => new Response("png", { status: 200, headers: IMMUTABLE }));
    expect((await get(PAGE)).status).toBe(200);
    expect(stored.has(PAGE)).toBe(true);
    expect(opened).toEqual([PAGES]);
    await get(PAGE);
    expect(network).toHaveBeenCalledTimes(2);
    // Past the browser's own cache too: every view revalidates the token and the protection with the host.
    expect(network.mock.calls.every((call) => ((call as unknown[])[1] as RequestInit | undefined)?.cache === "no-cache")).toBe(true);
  });

  it.each([401, 403, 404])("a kept page the host now refuses (%i) is that refusal, and the copy goes (F1)", async (status) => {
    let answer = new Response("png", { status: 200, headers: IMMUTABLE });
    const { stored } = workerFor(() => answer);
    await get(PAGE);
    expect(stored.has(PAGE)).toBe(true);
    answer = new Response(JSON.stringify({ ok: false, error: { code: "held_out_material" } }), { status });
    expect((await get(PAGE)).status).toBe(status);
    expect(stored.has(PAGE)).toBe(false);
  });

  it("with the desktop away (no answer, or Serve's 502/504) the kept copy answers", async () => {
    let answer: () => Response = () => new Response("png", { status: 200, headers: IMMUTABLE });
    const { stored } = workerFor(() => answer());
    await get(PAGE);
    const kept = stored.get(PAGE);
    answer = () => { throw new TypeError("offline"); };
    expect(await get(PAGE)).toBe(kept);
    answer = () => new Response("down", { status: 502 });
    expect(await get(PAGE)).toBe(kept);
    // The host itself saying its vault is changing is no reason to show a copy it may be about to withhold.
    answer = () => new Response(JSON.stringify({ ok: false, error: { code: "vault_unsettled" } }), { status: 503 });
    expect((await get(PAGE)).status).toBe(503);
    expect(stored.has(PAGE)).toBe(true);
  });

  it.each([401, 403, 404, 503])("never keeps a %i (a refusal is not the page)", async (status) => {
    const { stored } = workerFor(() => new Response("{}", { status }));
    expect((await get(PAGE)).status).toBe(status);
    expect(stored.size).toBe(0);
  });

  it("never keeps a 200 the host did not mark immutable", async () => {
    const { stored } = workerFor(() => new Response("png", { status: 200, headers: { "Cache-Control": "no-store" } }));
    await get(PAGE);
    expect(stored.size).toBe(0);
  });

  // Codex re-review F1: a kept copy is one token's (`Vary: Authorization`, which the Cache API matches on), and
  // the cache that predates that is not carried over.
  it("never keeps a page the host did not tie to its token (no Vary: Authorization)", async () => {
    const { stored } = workerFor(() => new Response("png", { status: 200, headers: { "Cache-Control": IMMUTABLE["Cache-Control"] } }));
    expect((await get(PAGE)).status).toBe(200);
    expect(stored.size).toBe(0);
  });

  it("offline, a copy not tied to a token is never the answer", async () => {
    let answer: () => Response = () => new Response("png", { status: 200, headers: IMMUTABLE });
    const { stored } = workerFor(() => answer());
    await get(PAGE);
    stored.set(PAGE, new Response("legacy", { status: 200, headers: { "Cache-Control": IMMUTABLE["Cache-Control"] } }));
    answer = () => { throw new TypeError("offline"); };
    expect((await get(PAGE)).type).toBe("error");
    answer = () => new Response("down", { status: 502 });
    expect((await get(PAGE)).status).toBe(502);
  });

  it("a new worker drops the pre-fix page cache, keeps its own and the shell", async () => {
    const deleted: string[] = [];
    const self = { location: { origin: "https://desktop.tail.ts.net" }, addEventListener: (name: string, handler: (event: unknown) => void) => { handlers[name] = handler; }, skipWaiting: vi.fn(), clients: { claim: vi.fn() } };
    const caches = {
      open: async () => ({ put }), match: async () => undefined,
      keys: async () => ["learnloop-shell-dev", "learnloop-pages-v1", PAGES, "learnloop-shell-old"],
      delete: async (name: string) => { deleted.push(name); return true; }
    };
    new Function("self", "caches", "fetch", "Response", source)(self, caches, async () => new Response("x"), Response);
    const waits: Promise<unknown>[] = [];
    handlers.activate({ waitUntil: (work: Promise<unknown>) => waits.push(work) });
    await Promise.all(waits);
    expect(deleted.sort()).toEqual(["learnloop-pages-v1", "learnloop-shell-old"]);
  });
});
