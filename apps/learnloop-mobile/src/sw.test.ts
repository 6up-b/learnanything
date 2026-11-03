import { beforeEach, expect, it, vi } from "vitest";
import source from "../public/sw.js?raw";

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
