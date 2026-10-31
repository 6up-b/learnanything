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
export const ENGINE_SHA256 = "7fc7671506ec276c1c4e338afafb86b0d1ff3b397f901813b62715d7e274cbfe";

/** keep (display): one frame, and how many a call may take before the Worker is paused (spec §15). */
export const SKETCH_FRAME_MS = 16;
export const SKETCH_WATCHDOG_FRAMES = 30;
/** keep (display): how many reads play takes from t = 0 to t_max (sketch.py SKETCH_PLAY_TICKS; a test keeps them equal).
 *  Part of the read schedule (sketchScene.readSchedule) every run follows. */
export const PLAY_TICKS = 100;
/** How many hex digits of a read's SHA-256 the verifier's report keeps (sketch_verify.TESTED_DIGEST_HEX). */
export const TESTED_DIGEST_HEX = 32;
/** keep: the compiled-in caps, mirrored for the tests (sk_limits). */
export const SKETCH_MEMORY_BYTES = 67_108_864;
export const SKETCH_FUEL_PER_CALL = 16;
export const SKETCH_SERIALIZE_TICKS = 48;

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

const K256 = new Uint32Array([
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01,
  0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
  0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
  0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08,
  0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
  0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]);

/** SHA-256 hex in plain TypeScript (FIPS 180-4), for a page whose Web Crypto
 *  is unavailable (an insecure context): the pin is checked either way. */
export function sha256Hex(bytes: Uint8Array): string {
  const length = bytes.length;
  const padded = new Uint8Array(((length + 9 + 63) >> 6) << 6);
  padded.set(bytes);
  padded[length] = 0x80;
  const view = new DataView(padded.buffer);
  view.setUint32(padded.length - 8, Math.floor((length * 8) / 0x100000000), false);
  view.setUint32(padded.length - 4, (length * 8) >>> 0, false);
  const h = new Uint32Array([0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]);
  const w = new Uint32Array(64);
  const rotr = (x: number, n: number) => (x >>> n) | (x << (32 - n));
  for (let offset = 0; offset < padded.length; offset += 64) {
    for (let i = 0; i < 16; i += 1) w[i] = view.getUint32(offset + 4 * i, false);
    for (let i = 16; i < 64; i += 1) {
      const s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >>> 3);
      const s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >>> 10);
      w[i] = (w[i - 16] + s0 + w[i - 7] + s1) >>> 0;
    }
    let [a, b, c, d, e, f, g, hh] = h;
    for (let i = 0; i < 64; i += 1) {
      const t1 = (hh + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + K256[i] + w[i]) >>> 0;
      const t2 = ((rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) >>> 0;
      hh = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = b; b = a; a = (t1 + t2) >>> 0;
    }
    h[0] = (h[0] + a) >>> 0; h[1] = (h[1] + b) >>> 0; h[2] = (h[2] + c) >>> 0; h[3] = (h[3] + d) >>> 0;
    h[4] = (h[4] + e) >>> 0; h[5] = (h[5] + f) >>> 0; h[6] = (h[6] + g) >>> 0; h[7] = (h[7] + hh) >>> 0;
  }
  return Array.from(h, (word) => word.toString(16).padStart(8, "0")).join("");
}

/** One read's digest (fix round 4, the independent sandbox review): the SHA-256 of the scene text, a NUL and
 *  the probes text (UTF-8), the first TESTED_DIGEST_HEX hex digits, as sketch_verify.tested_digest computes it.
 *  Synchronous, so the Worker and the in-process host compute it the same way. */
export function sceneDigest(sceneText: string, probesText: string): string {
  return sha256Hex(new TextEncoder().encode(`${sceneText}\u0000${probesText}`)).slice(0, TESTED_DIGEST_HEX);
}

/** SHA-256 hex with Web Crypto (the Worker; Node 20+ has it too), else in plain TypeScript. */
export async function webDigest(bytes: Uint8Array): Promise<string> {
  const subtle = (globalThis as { crypto?: { subtle?: SubtleCrypto } }).crypto?.subtle;
  if (!subtle) return sha256Hex(bytes);
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

/** An input as JSON text with every -0 written as 0 (JSON.stringify already does; stated here because the
 *  sidecar must match it: the sandbox review verify, Astra round 2). No program can see -0 as an input. */
export function canonicalJson(value: unknown): string {
  return JSON.stringify(value, (_key, item: unknown) => (typeof item === "number" && Object.is(item, -0) ? 0 : item));
}
export type Params = Record<string, number>;

/** One sealed engine instance, one program at a time. Synchronous: call it off the UI thread. */
export class SketchEngineHost {
  private readonly exports: Exports;
  private broken = false;
  /** The loaded program's text: every init reloads it (fix round 4). */
  private code: string | null = null;
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
    const found = JSON.parse(this.run(this.call(() => this.exports.sk_load(length))) || "{}") as EntryPoints;
    this.code = code;
    return found;
  }

  /** Start a run: the program is loaded afresh first (the independent sandbox review, finding 1), so a
   *  run's history is "a freshly loaded program, init, then its own calls", whatever ran before: a
   *  program counting its own starts sees its first start every time, as verification does. */
  init(params: Params, seed: number): void {
    if (this.code !== null) {
      const code = this.write(this.code);
      this.run(this.call(() => this.exports.sk_load(code)));
    }
    const length = this.write(canonicalJson(params));
    this.run(this.call(() => this.exports.sk_init(length, seed >>> 0)));
  }

  step(params: Params, dt: number, index: number, count = 1): void {
    const length = this.write(canonicalJson({ p: params, dt }));
    this.run(this.call(() => this.exports.sk_step(length, index >>> 0, count >>> 0)));
  }

  viewText(params: Params, index: number): string {
    const length = this.write(canonicalJson(params));
    return this.run(this.call(() => this.exports.sk_view(length, index >>> 0)));
  }

  probesText(params: Params, index: number): string {
    const length = this.write(canonicalJson(params));
    return this.run(this.call(() => this.exports.sk_probes(length, index >>> 0)));
  }

  /** One read as every host reads: view(), then probes(), the text exactly as the engine wrote it. */
  readText(params: Params, index: number): { sceneText: string; probesText: string } {
    const sceneText = this.viewText(params, index);
    return { sceneText, probesText: this.probesText(params, index) };
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
