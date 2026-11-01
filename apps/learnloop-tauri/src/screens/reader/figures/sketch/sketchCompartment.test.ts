// Reader RW5d P2, the sketch compartment (G-SM14's remedy): the frame document and its policy, the
// set-up messages on every side, and the engine still rendering the verified corpus through the whole
// chain (Reader -> frame script -> blob Worker -> engine), with only the browser's frame and Worker faked.
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import parity from "./sketchParityCorpus.json";
import { ENGINE_BYTES, nodeDigest } from "./engineForTests";
import { SketchEngineHost, SketchRunError } from "./sketchEngine";
import { createSketchCompartment, type WorkerLike } from "./sketchCompartment";
import {
  FRAME_MESSAGE_MAX, parseFrameNotice, parseWorkerBoot, SKETCH_ENGINE_MAX_BYTES, SKETCH_FRAME_PATH,
  SKETCH_WORKER_SOURCE_MAX_CHARS, stripNetwork, STRIPPED_GLOBALS,
} from "./sketchFrameProtocol";
import { portRunner } from "./sketchRunner";
import { startSketchWorker, type WorkerScopeLike } from "./sketchWorkerCore";
import { readSchedule, type SketchProgram } from "./sketchScene";

const APP = join(__dirname, "../../../../..");
const FRAME_HTML = readFileSync(join(APP, "sketch-frame.html"), "utf8");
const FRAME_SCRIPT = /<script>([\s\S]*?)<\/script>/.exec(FRAME_HTML)![1];
const FRAME_CSP = /http-equiv="Content-Security-Policy" content="([^"]+)"/.exec(FRAME_HTML)![1];
const directives = (policy: string) => new Map(policy.split(";").map((part) => part.trim()).filter(Boolean)
  .map((part) => { const [name, ...sources] = part.split(/\s+/); return [name, sources] as [string, string[]]; }));
const sha256Base64 = (text: string) => {
  // node:crypto's digest is typed hex-only in this app's shim: convert.
  const hex = createHash("sha256").update(new TextEncoder().encode(text)).digest("hex");
  let binary = "";
  for (let i = 0; i < hex.length; i += 2) binary += String.fromCharCode(parseInt(hex.slice(i, i + 2), 16));
  return btoa(binary);
};

describe("the frame document's policy", () => {
  const csp = directives(FRAME_CSP);

  it("allows exactly its one script, by hash, and WebAssembly", () => {
    expect(csp.get("script-src")).toEqual([`'sha256-${sha256Base64(FRAME_SCRIPT)}'`, "'wasm-unsafe-eval'"]);
    expect(FRAME_HTML.match(/<script/g)).toHaveLength(1);
  });

  it("connects nowhere and loads nothing; Workers only from blobs", () => {
    expect(csp.get("default-src")).toEqual(["'none'"]);
    expect(csp.get("connect-src")).toEqual(["'none'"]);
    expect(csp.get("worker-src")).toEqual(["blob:"]);
    expect(csp.get("child-src")).toEqual(["blob:"]);
    for (const name of ["img-src", "style-src", "font-src", "media-src", "frame-src", "object-src", "manifest-src", "form-action", "base-uri"]) {
      expect(csp.get(name), name).toEqual(["'none'"]);
    }
    expect(FRAME_CSP).not.toMatch(/unsafe-inline|'unsafe-eval'|'self'|ipc|\*/);
  });

  it("mirrors the protocol's caps", () => {
    expect(FRAME_SCRIPT).toContain(`const ENGINE_MAX_BYTES = ${SKETCH_ENGINE_MAX_BYTES};`);
    expect(FRAME_SCRIPT).toContain(`const WORKER_SOURCE_MAX_CHARS = ${SKETCH_WORKER_SOURCE_MAX_CHARS};`);
    expect(FRAME_SCRIPT).toContain(`const MESSAGE_MAX = ${FRAME_MESSAGE_MAX};`);
  });

  it("is the page's only frame source besides the existing video embed, and the app's IPC endpoints stay page-only", () => {
    const conf = JSON.parse(readFileSync(join(APP, "src-tauri/tauri.conf.json"), "utf8")) as { app: { security: { csp: string } } };
    const page = directives(conf.app.security.csp);
    expect(page.get("frame-src")).toEqual([`tauri://localhost${SKETCH_FRAME_PATH}`, `http://tauri.localhost${SKETCH_FRAME_PATH}`, "https://www.youtube-nocookie.com"]);
    expect(page.get("connect-src")).toContain("ipc:");  // the page needs it; the frame's own policy removes it
    const vite = readFileSync(join(APP, "vite.config.mjs"), "utf8");
    expect(vite).toContain('sketchFrame: resolve(root, "sketch-frame.html")');
  });
});

describe("the Reader's side of the control channel", () => {
  it("accepts the three notices and drops every other kind", () => {
    expect(parseFrameNotice({ kind: "connected" })).toEqual({ kind: "connected" });
    expect(parseFrameNotice({ kind: "started" })).toEqual({ kind: "started" });
    expect(parseFrameNotice({ kind: "failed", message: "no" })).toEqual({ kind: "failed", message: "no" });
    for (const dropped of [null, "started", [], { kind: "invoke", cmd: "load_vault" }, { kind: "started", extra: 1 }, { kind: "ipc" }, { id: 1, ok: true }]) {
      expect(parseFrameNotice(dropped)).toBeNull();
    }
  });

  it("refuses an over-long reason (the failure still counts, in code's words)", () => {
    expect(parseFrameNotice({ kind: "failed", message: "m".repeat(FRAME_MESSAGE_MAX + 1) }))
      .toEqual({ kind: "failed", message: "the sketch engine could not start here" });
  });
});

describe("the Worker's boot", () => {
  const port = new MessageChannel().port1;
  afterEach(() => port.close());

  it("takes the engine's bytes and one port, nothing else", () => {
    const engine = new ArrayBuffer(8);
    expect(parseWorkerBoot({ kind: "boot", engine }, [port])).toEqual({ engine, port });
    expect(parseWorkerBoot({ kind: "boot", engine, worker: "x" }, [port])).toBeNull();
    expect(parseWorkerBoot({ kind: "boot", engine: new Uint8Array(8) }, [port])).toBeNull();
    expect(parseWorkerBoot({ kind: "boot", engine: new ArrayBuffer(0) }, [port])).toBeNull();
    expect(parseWorkerBoot({ kind: "boot", engine: new ArrayBuffer(SKETCH_ENGINE_MAX_BYTES + 1) }, [port])).toBeNull();
    expect(parseWorkerBoot({ kind: "boot", engine }, [])).toBeNull();
    expect(parseWorkerBoot({ kind: "boot", engine }, [port, port])).toBeNull();
    expect(parseWorkerBoot({ kind: "load", engine }, [port])).toBeNull();
  });

  it("strips fetch from the whole prototype chain and the Worker constructors (the G-SM14 probe's paths)", () => {
    const proto: Record<string, unknown> = { fetch: () => "proto", importScripts: () => "proto" };
    const scope = Object.create(proto) as Record<string, unknown>;
    Object.assign(scope, { fetch: () => "own", XMLHttpRequest: class {}, WebSocket: class {}, Worker: class {}, postMessage: () => undefined });
    expect(stripNetwork(scope)).toEqual([]);
    for (const name of STRIPPED_GLOBALS) expect(scope[name], name).toBeUndefined();
    expect(proto.fetch).toBeUndefined();
    expect(Object.getPrototypeOf(scope)).toBe(proto);
    expect(typeof scope.postMessage).toBe("function");
  });

  it("reports a global it could not remove", () => {
    const scope = {};
    Object.defineProperty(scope, "fetch", { value: () => 1, configurable: false, writable: false });
    expect(stripNetwork(scope)).toEqual(["fetch"]);
  });
});

// ---- The browser's frame and Worker, faked; everything else is the real code. ----

const PARENT = { name: "the Reader's window" };
async function until(condition: () => boolean, ms = 5000) {
  const end = Date.now() + ms;
  while (!condition()) {
    if (Date.now() > end) throw new Error("timed out waiting");
    await new Promise((resolve) => setTimeout(resolve, 5));
  }
}
const createHost = (bytes: Uint8Array) => SketchEngineHost.create(bytes, { digest: nodeDigest });

type FakeWorker = {
  url: string; source: string; terminated: boolean;
  onmessage: ((event: { data: unknown }) => void) | null; onerror: ((event: unknown) => void) | null;
  postMessage(message: unknown, transfer?: unknown[]): void; terminate(): void;
};

/** One frame realm: the real frame script, with `window`, `URL`, `Blob` and `Worker` provided. */
function frameRealm(options: { workerThrows?: boolean } = {}) {
  const listeners: Array<(event: unknown) => void> = [];
  const blobs = new Map<string, string>();
  const workers: FakeWorker[] = [];
  const wires: MessagePort[] = [];
  const win = {
    parent: PARENT,
    addEventListener: (type: string, listener: (event: unknown) => void) => { if (type === "message") listeners.push(listener); },
    removeEventListener: (type: string, listener: (event: unknown) => void) => {
      const at = listeners.indexOf(listener);
      if (type === "message" && at >= 0) listeners.splice(at, 1);
    },
  };
  let next = 0;
  const FakeURL = {
    createObjectURL: (blob: { text: string }) => { const url = `blob:null/${next += 1}`; blobs.set(url, blob.text); return url; },
    revokeObjectURL: (url: string) => { blobs.delete(url); },
  };
  class FakeBlob { text: string; constructor(parts: string[]) { this.text = parts.join(""); } }
  function FakeWorkerCtor(this: FakeWorker, url: string) {
    if (options.workerThrows) throw new DOMException("refused", "SecurityError");
    const wire = new MessageChannel();
    wires.push(wire.port1, wire.port2);
    const worker: FakeWorker = {
      url, source: blobs.get(url) ?? "", terminated: false, onmessage: null, onerror: null,
      postMessage(message, transfer) { wire.port1.postMessage(message, (transfer ?? []) as Transferable[]); },
      terminate() { worker.terminated = true; wire.port1.close(); wire.port2.close(); },
    };
    // The Worker's own realm: the real start-up, on a scope whose postMessage reaches its owner.
    const scope: WorkerScopeLike = { onmessage: null, postMessage: (message) => setTimeout(() => worker.onmessage?.({ data: message }), 0) };
    startSketchWorker(scope, createHost);
    wire.port2.onmessage = (event) => scope.onmessage?.({ data: event.data, ports: event.ports });
    workers.push(worker);
    return worker;
  }
  new Function("window", "URL", "Blob", "Worker", FRAME_SCRIPT)(win, FakeURL, FakeBlob, FakeWorkerCtor);
  return {
    workers, blobs,
    deliver: (event: { source: unknown; data: unknown; ports: unknown[] }) => { for (const listener of [...listeners]) listener(event); },
    listening: () => listeners.length,
    close: () => wires.forEach((wire) => wire.close()),
  };
}

const WORKER_SOURCE = "/* the bundled sketch Worker */";
let opened: Array<{ handle: WorkerLike; realm: ReturnType<typeof frameRealm> }> = [];
afterEach(() => {
  for (const { handle, realm } of opened) { handle.terminate(); realm.close(); }
  opened = [];
  document.body.innerHTML = "";
});

/** A compartment whose iframe holds `realm`: the iframe's one window message goes into the frame script. */
function compartment(realm = frameRealm(), engineBytes = () => Promise.resolve(ENGINE_BYTES.slice().buffer as ArrayBuffer)) {
  const handle = createSketchCompartment({ workerSource: WORKER_SOURCE, engineBytes });
  const frame = document.querySelector("iframe[data-sketch-compartment]") as HTMLIFrameElement;
  const posted: unknown[] = [];
  Object.defineProperty(frame.contentWindow, "postMessage", {
    configurable: true,
    value: (data: unknown, target: string, transfer: unknown[]) => { posted.push({ data, target }); realm.deliver({ source: PARENT, data, ports: transfer }); },
  });
  frame.dispatchEvent(new Event("load"));
  opened.push({ handle, realm });
  return { handle, frame, realm, posted };
}

describe("the compartment", () => {
  it("is a hidden iframe with allow-scripts only, on the frame document, with no referrer", () => {
    const { frame, posted } = compartment();
    expect(frame.getAttribute("sandbox")).toBe("allow-scripts");
    expect(frame.getAttribute("src")).toBe(SKETCH_FRAME_PATH);
    expect(frame.getAttribute("referrerpolicy")).toBe("no-referrer");
    expect(frame.getAttribute("aria-hidden")).toBe("true");
    expect(frame.style.visibility).toBe("hidden");
    expect(posted).toEqual([{ data: { kind: "connect" }, target: "*" }]);  // the one window message
  });

  it("starts the Worker from a blob of the bundled source, inside the frame, and renders the verified corpus there", async () => {
    type Tested = { values: number[]; steps: number[]; digests: string[] };
    const verified = (parity as unknown as { verified: Array<{ name: string; program: { code: string; parameters: Array<{ name: string }>; clock?: { dt: number } }; sketch: { seed: number; tested: Tested[]; readSteps?: number[] } }> }).verified;
    let checked = 0;
    for (const item of verified) {
      const { handle, realm } = compartment();
      const runner = portRunner(handle);
      await runner.load(item.program.code);
      expect(realm.workers).toHaveLength(1);
      expect(realm.workers[0].source).toBe(WORKER_SOURCE);
      expect(realm.workers[0].url).toMatch(/^blob:/);
      const names = item.program.parameters.map((parameter) => parameter.name);
      for (const entry of item.sketch.tested) {
        const params = Object.fromEntries(names.map((name, i) => [name, entry.values[i]]));
        await runner.init(params, item.sketch.seed);
        // The page's run: every scheduled read, in order; at each step verification tested, its digest.
        let at = 0;
        for (const index of item.sketch.readSteps ?? readSchedule(item.program as unknown as SketchProgram)) {
          if (index > at) {
            await runner.step(params, item.program.clock!.dt, at, index - at);
            at = index;
          }
          const read = await runner.read(params, index);
          const position = entry.steps.indexOf(index);
          if (position < 0) continue;
          expect(read.digest, `${item.name} at step ${index}`).toBe(entry.digests[position]);
          checked += 1;
        }
      }
      runner.dispose();
      await until(() => realm.workers[0].terminated);
      expect(document.querySelector("iframe[data-sketch-compartment]")).toBeNull();  // the frame went with it
    }
    expect(checked).toBeGreaterThan(3);
  });

  it("waits for the engine: requests sent before it starts are answered in order", async () => {
    const { handle } = compartment();
    const runner = portRunner(handle);
    const loading = runner.load("function init(p){return 1} function view(s){return {viewport:{x:[0,1],y:[0,1]},elements:[]}} function probes(s){return {s:s}}");
    const starting = runner.init({}, 1);
    const reading = runner.read({}, 0);
    await expect(loading).resolves.toEqual({ init: true, step: false, view: true, probes: true });
    await expect(starting).resolves.toBeUndefined();
    await expect(reading).resolves.toMatchObject({ probes: { s: 1 } });
  });

  it("answers every request with the failure when the frame cannot start a Worker", async () => {
    const { handle } = compartment(frameRealm({ workerThrows: true }));
    const runner = portRunner(handle);
    const caught = await runner.load("function init(){return 1}").catch((error: unknown) => error);
    expect(caught).toBeInstanceOf(SketchRunError);
    expect((caught as SketchRunError).kind).toBe("no_program");
    expect((caught as SketchRunError).message).toMatch(/could not start here \(SecurityError\)/);
    await expect(runner.read({}, 0)).rejects.toThrow(/could not start here/);
  });

  it("refuses an engine whose digest is not the pin, inside the Worker", async () => {
    const tampered = ENGINE_BYTES.slice();
    tampered[tampered.length - 1] ^= 1;
    const { handle } = compartment(frameRealm(), () => Promise.resolve(tampered.buffer as ArrayBuffer));
    await expect(portRunner(handle).load("function init(){return 1}")).rejects.toThrow(/not the pinned/);
  });

  it("refuses to boot with an oversize engine (the frame never sees it)", async () => {
    const realm = frameRealm();
    const { handle } = compartment(realm, () => Promise.resolve(new ArrayBuffer(SKETCH_ENGINE_MAX_BYTES + 1)));
    await expect(portRunner(handle).load("x")).rejects.toThrow(/size is not the pinned/);
    expect(realm.workers).toHaveLength(0);
  });
});

describe("the frame script", () => {
  it("takes the control port only from the Reader's window, once, and only as a connect", () => {
    const realm = frameRealm();
    const control = new MessageChannel();
    realm.deliver({ source: { name: "someone else" }, data: { kind: "connect" }, ports: [control.port2] });
    realm.deliver({ source: PARENT, data: { kind: "connect", extra: 1 }, ports: [control.port2] });
    realm.deliver({ source: PARENT, data: { kind: "boot" }, ports: [control.port2] });
    expect(realm.listening()).toBe(1);  // still waiting
    realm.deliver({ source: PARENT, data: { kind: "connect" }, ports: [control.port2] });
    expect(realm.listening()).toBe(0);  // connected: no window message is read again
    control.port1.close();
    realm.close();
  });

  async function connected(realm = frameRealm()) {
    const control = new MessageChannel();
    const notices: unknown[] = [];
    control.port1.onmessage = (event) => notices.push(event.data);
    realm.deliver({ source: PARENT, data: { kind: "connect" }, ports: [control.port2] });
    await new Promise((resolve) => setTimeout(resolve, 10));
    return { control, notices, realm };
  }

  it("drops unknown kinds and refuses a malformed or oversize boot", async () => {
    for (const [boot, reason] of [
      [{ kind: "boot", worker: 1, engine: new ArrayBuffer(8) }, /malformed/],
      [{ kind: "boot", worker: "x", engine: new ArrayBuffer(8), extra: true }, /malformed/],
      [{ kind: "boot", worker: "x".repeat(SKETCH_WORKER_SOURCE_MAX_CHARS + 1), engine: new ArrayBuffer(8) }, /too large/],
      [{ kind: "boot", worker: "x", engine: new ArrayBuffer(SKETCH_ENGINE_MAX_BYTES + 1) }, /too large/],
    ] as Array<[Record<string, unknown>, RegExp]>) {
      const { control, notices, realm } = await connected();
      control.port1.postMessage({ kind: "invoke", cmd: "load_vault" });
      control.port1.postMessage({ kind: "fetch", url: "ipc://localhost/load_vault" });
      const engine = new MessageChannel();
      control.port1.postMessage(boot, [engine.port2]);
      await new Promise((resolve) => setTimeout(resolve, 10));
      expect(notices[0]).toEqual({ kind: "connected" });
      expect(notices.slice(1)).toHaveLength(1);
      expect((notices[1] as { kind: string; message: string }).kind).toBe("failed");
      expect((notices[1] as { message: string }).message).toMatch(reason);
      expect(realm.workers).toHaveLength(0);
      control.port1.close();
      engine.port1.close();
      realm.close();
    }
  });

  it("boots once, revokes the blob and terminates the Worker on stop", async () => {
    const { control, notices, realm } = await connected();
    const engine = new MessageChannel();
    const bytes = ENGINE_BYTES.slice().buffer as ArrayBuffer;
    control.port1.postMessage({ kind: "boot", worker: WORKER_SOURCE, engine: bytes }, [engine.port2, bytes]);
    await until(() => notices.length >= 2);
    expect(notices).toEqual([{ kind: "connected" }, { kind: "started" }]);
    const second = new MessageChannel();
    control.port1.postMessage({ kind: "boot", worker: WORKER_SOURCE, engine: new ArrayBuffer(8) }, [second.port2]);
    await new Promise((resolve) => setTimeout(resolve, 10));
    expect(realm.workers).toHaveLength(1);  // one boot per frame
    control.port1.postMessage({ kind: "stop" });
    await new Promise((resolve) => setTimeout(resolve, 10));
    expect(realm.workers[0].terminated).toBe(true);
    expect(realm.blobs.size).toBe(0);
    control.port1.close();
    engine.port1.close();
    second.port1.close();
    realm.close();
  });
});

describe("the Worker in its compartment", () => {
  it("ignores everything but one boot, then answers only on its port", async () => {
    const posted: unknown[] = [];
    const scope: WorkerScopeLike & Record<string, unknown> = { onmessage: null, postMessage: (message) => posted.push(message), fetch: () => "network" };
    startSketchWorker(scope, createHost);
    const engine = new MessageChannel();
    scope.onmessage!({ data: { id: 1, op: "load", args: ["x"] }, ports: [] });  // a request on the wrong channel
    scope.onmessage!({ data: { kind: "boot", engine: new ArrayBuffer(SKETCH_ENGINE_MAX_BYTES + 1) }, ports: [engine.port2] });
    expect(posted).toEqual([]);
    expect(scope.onmessage).not.toBeNull();
    scope.onmessage!({ data: { kind: "boot", engine: ENGINE_BYTES.slice().buffer }, ports: [engine.port2] });
    expect(scope.onmessage).toBeNull();
    const replies: unknown[] = [];
    engine.port1.onmessage = (event) => replies.push(event.data);
    engine.port1.postMessage({ id: 7, op: "probe", args: [{}, 0] });
    engine.port1.postMessage({ id: 8, op: "load", args: ["function init(){return 1} function view(){return {}} function probes(){return {}}"] });
    await until(() => replies.length >= 2 && posted.length >= 1);
    expect(posted).toEqual([{ kind: "started" }]);
    expect(scope.fetch).toBeUndefined();  // stripped once the engine was compiled
    expect(replies).toEqual([
      { id: 7, ok: false, error: { kind: "input", message: "unknown operation" } },
      { id: 8, ok: true, result: { init: true, step: false, view: true, probes: true } },
    ]);
    engine.port1.close();
    engine.port2.close();
  });
});

describe("the bundled Worker source (vite.config.mjs)", () => {
  it("is one classic script with nothing to import, and it boots and answers like the Worker", async () => {
    const source = (await import("virtual:sketch-worker-source")).default;
    expect(source.length).toBeLessThan(SKETCH_WORKER_SOURCE_MAX_CHARS);
    expect(source).not.toMatch(/\bimport\s*[({"'`]|importScripts\(|new URL\(|sketch-engine\.wasm/);
    const posted: unknown[] = [];
    const scope: Record<string, unknown> & WorkerScopeLike = { onmessage: null, postMessage: (message: unknown) => posted.push(message), fetch: () => "network" };
    new Function("self", source)(scope);
    expect(typeof scope.onmessage).toBe("function");
    const engine = new MessageChannel();
    const replies: unknown[] = [];
    engine.port1.onmessage = (event) => replies.push(event.data);
    scope.onmessage!({ data: { kind: "boot", engine: ENGINE_BYTES.slice().buffer }, ports: [engine.port2] });
    engine.port1.postMessage({ id: 1, op: "load", args: ["function init(){return 2} function view(s){return {viewport:{x:[0,1],y:[0,1]},elements:[]}} function probes(s){return {s:s}}"] });
    engine.port1.postMessage({ id: 2, op: "init", args: [{}, 1] });
    engine.port1.postMessage({ id: 3, op: "read", args: [{}, 0] });
    await until(() => replies.length >= 3);
    expect(posted).toEqual([{ kind: "started" }]);
    expect(scope.fetch).toBeUndefined();
    expect(replies[0]).toEqual({ id: 1, ok: true, result: { init: true, step: false, view: true, probes: true } });
    expect((replies[2] as { result: { probesText: string } }).result.probesText).toBe('{"s":2}');
    engine.port1.close();
    engine.port2.close();
  });
});
