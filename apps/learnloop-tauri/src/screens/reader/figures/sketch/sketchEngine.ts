// Reader RW5d P2: the sketch engine's desktop host (spec_reader_show_me_figures_v1 §9.2-9.4).
//
// The same sketch-engine.wasm the sidecar verifies with (learnloop.figures.
// sketch_engine) runs here, byte for byte (pinned by ENGINE_SHA256; a
// mismatch refuses to run). Its only imports are the five WASI functions
// wasi-libc links, each answered by a deny-all shim: no clock, no files, no
// randomness, no environment, no network; fd_write keeps a little error text
// and nothing else. The program inside sees its arguments and rand() and
// returns JSON text; nothing it writes is code to this page.
//
// This module is plain TypeScript with no DOM: the Worker (sketch.worker.ts)
// runs it off the UI thread, and the vitest parity corpus runs it in Node.

/** The pinned artifact's SHA-256 (engine.lock.json; tests keep the three pins equal). */
export const ENGINE_SHA256 = "564207205f358c907beea820b1b12dd7813992260fc805fdb4e84ac03a638706";

/** keep (display): one frame, and how many a call may take before the Worker is paused (spec §15). */
export const SKETCH_FRAME_MS = 16;
export const SKETCH_WATCHDOG_FRAMES = 30;
/** keep: the compiled-in caps, mirrored for the tests (sk_limits). */
export const SKETCH_MEMORY_BYTES = 67_108_864;
export const SKETCH_FUEL_PER_CALL = 48;

export const STATUS_NAMES = ["ok", "error", "work_cap", "memory_cap", "stack", "no_program", "output", "input"] as const;
export type SketchErrorKind = (typeof STATUS_NAMES)[number] | "trap" | "scene" | "probe" | "paused";

const STDERR_KEEP = 4096;
const EBADF = 8;
const ENOSYS = 52;
const ALLOWED_IMPORTS = new Set([
  "wasi_snapshot_preview1.clock_time_get",
  "wasi_snapshot_preview1.fd_close",
  "wasi_snapshot_preview1.fd_fdstat_get",
  "wasi_snapshot_preview1.fd_seek",
  "wasi_snapshot_preview1.fd_write",
]);

export class SketchRunError extends Error {
  readonly kind: SketchErrorKind;
  constructor(kind: SketchErrorKind, message: string) {
    super(message);
    this.kind = kind;
  }
}

export type Digest = (bytes: Uint8Array) => Promise<string>;

/** SHA-256 hex with Web Crypto (the Worker; Node 20+ has it too). */
export async function webDigest(bytes: Uint8Array): Promise<string> {
  const subtle = (globalThis as { crypto?: { subtle?: SubtleCrypto } }).crypto?.subtle;
  if (!subtle) throw new SketchRunError("no_program", "this window can't check the sketch engine's digest");
  const hash = await subtle.digest("SHA-256", bytes as unknown as BufferSource);
  return Array.from(new Uint8Array(hash), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

type Exports = {
  memory: WebAssembly.Memory;
  _initialize: () => void;
  sk_buffer: (size: number) => number;
  sk_output_ptr: () => number;
  sk_output_len: () => number;
  sk_limits: () => number;
  sk_load: (len: number) => number;
  sk_init: (len: number, seed: number) => number;
  sk_step: (len: number, index: number, count: number) => number;
  sk_view: (len: number, index: number) => number;
  sk_probes: (len: number, index: number) => number;
  sk_unload: () => void;
};

export type EntryPoints = { init: boolean; step: boolean; view: boolean; probes: boolean };
export type Params = Record<string, number>;

/** One sealed engine instance, one program at a time. Synchronous: call it off the UI thread. */
export class SketchEngineHost {
  private readonly exports: Exports;
  private broken = false;
  stderr = "";
  private readonly encoder = new TextEncoder();
  private readonly decoder = new TextDecoder("utf-8");

  private constructor(instance: WebAssembly.Instance, shim: { bind: (exports: Exports) => void }) {
    this.exports = instance.exports as unknown as Exports;
    shim.bind(this.exports);
    this.call(() => this.exports._initialize());
  }

  /** Check the bytes against the pin, refuse any import beyond the shim, instantiate. */
  static async create(bytes: Uint8Array, options: { expected?: string; digest?: Digest } = {}): Promise<SketchEngineHost> {
    const expected = options.expected ?? ENGINE_SHA256;
    const digest = await (options.digest ?? webDigest)(bytes);
    if (digest !== expected) {
      throw new SketchRunError("no_program", `the sketch engine's digest ${digest.slice(0, 12)} is not the pinned ${expected.slice(0, 12)}; it is not run`);
    }
    const module = await WebAssembly.compile(bytes as unknown as BufferSource);
    for (const item of WebAssembly.Module.imports(module)) {
      if (!ALLOWED_IMPORTS.has(`${item.module}.${item.name}`)) {
        throw new SketchRunError("no_program", `the sketch engine imports ${item.module}.${item.name}, which the sandbox does not answer`);
      }
    }
    let host: SketchEngineHost | null = null;
    let memory: WebAssembly.Memory | null = null;
    const shim = {
      bind(exports: Exports) {
        memory = exports.memory;
      },
    };
    const wasi = {
      clock_time_get: () => ENOSYS,
      fd_close: () => EBADF,
      fd_fdstat_get: () => EBADF,
      fd_seek: () => EBADF,
      fd_write: (_fd: number, iovs: number, count: number, written: number) => {
        if (!memory) return EBADF;
        const view = new DataView(memory.buffer);
        let total = 0;
        for (let index = 0; index < Math.min(count, 64); index += 1) {
          const pointer = view.getUint32(iovs + 8 * index, true);
          const length = view.getUint32(iovs + 8 * index + 4, true);
          if (host && host.stderr.length < STDERR_KEEP && length > 0) {
            const room = STDERR_KEEP - host.stderr.length;
            host.stderr += new TextDecoder().decode(new Uint8Array(memory.buffer, pointer, Math.min(length, room)));
          }
          total += length;
        }
        view.setUint32(written, total >>> 0, true);
        return 0;
      },
    };
    const instance = await WebAssembly.instantiate(module, { wasi_snapshot_preview1: wasi });
    host = new SketchEngineHost(instance, shim);
    return host;
  }

  private call<T>(run: () => T): T {
    if (this.broken) throw new SketchRunError("trap", "the engine was stopped earlier; a new one is needed");
    try {
      return run();
    } catch (caught) {
      // A WebAssembly trap can stop the interpreter mid-update: never call this instance again.
      this.broken = true;
      const message = caught instanceof Error ? caught.message : String(caught);
      throw new SketchRunError("trap", `the engine stopped it (${message.slice(0, 120)})`);
    }
  }

  private write(text: string): number {
    const bytes = this.encoder.encode(text);
    const pointer = this.call(() => this.exports.sk_buffer(bytes.length));
    if (!pointer) throw new SketchRunError("memory_cap", "the engine could not take the input");
    new Uint8Array(this.exports.memory.buffer, pointer, bytes.length).set(bytes);
    return bytes.length;
  }

  private output(): string {
    const pointer = this.exports.sk_output_ptr();
    const length = this.exports.sk_output_len();
    return this.decoder.decode(new Uint8Array(this.exports.memory.buffer, pointer, length).slice());
  }

  private run(status: number): string {
    const text = this.output();
    if (status !== 0) throw new SketchRunError(STATUS_NAMES[status] ?? "error", text || STATUS_NAMES[status] || "error");
    return text;
  }

  limits(): Record<string, unknown> {
    return JSON.parse(this.run(this.call(() => this.exports.sk_limits())));
  }

  load(code: string): EntryPoints {
    const length = this.write(code);
    return JSON.parse(this.run(this.call(() => this.exports.sk_load(length))) || "{}") as EntryPoints;
  }

  init(params: Params, seed: number): void {
    const length = this.write(JSON.stringify(params));
    this.run(this.call(() => this.exports.sk_init(length, seed >>> 0)));
  }

  step(params: Params, dt: number, index: number, count = 1): void {
    const length = this.write(JSON.stringify({ p: params, dt }));
    this.run(this.call(() => this.exports.sk_step(length, index >>> 0, count >>> 0)));
  }

  viewText(params: Params, index: number): string {
    const length = this.write(JSON.stringify(params));
    return this.run(this.call(() => this.exports.sk_view(length, index >>> 0)));
  }

  probesText(params: Params, index: number): string {
    const length = this.write(JSON.stringify(params));
    return this.run(this.call(() => this.exports.sk_probes(length, index >>> 0)));
  }

  view(params: Params, index: number): unknown {
    return JSON.parse(this.viewText(params, index));
  }

  probes(params: Params, index: number): unknown {
    return JSON.parse(this.probesText(params, index));
  }

  dispose(): void {
    try {
      this.exports.sk_unload();
    } catch {
      // closing never throws
    }
    this.broken = true;
  }
}
