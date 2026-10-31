// Reader RW5d P2: how the Reader talks to a sketch's sealed engine (spec_reader_show_me_figures_v1 §9.3).
//
// In the app every call goes to a dedicated Web Worker (sketch.worker.ts: no
// DOM, terminable) through workerRunner; the vitest renderer tests run the
// same engine host in-process (hostRunner). withWatchdog wraps either: a call
// that takes longer than SKETCH_FRAME_MS x SKETCH_WATCHDOG_FRAMES ends the
// runner (the Worker is terminated) and the sketch shows as paused. Every
// result is JSON text the engine wrote, parsed here and validated by the
// caller before anything is drawn. Every read also carries the digest of the
// text the engine wrote (sketchEngine.sceneDigest), which the sketch compares
// with the verifier's at the states it tested (fix round 4). Requests and
// replies are validated at runtime on both sides of the Worker
// (sketchProtocol.ts).
import { createContext } from "react";
import { sceneDigest, SKETCH_FRAME_MS, SKETCH_WATCHDOG_FRAMES, SketchRunError, type EntryPoints, type Params, type SketchEngineHost } from "./sketchEngine";
import { parseWorkerReply, type SketchRead, type WorkerOp, type WorkerRequest, type WorkerResponse } from "./sketchProtocol";

export type { SketchRead, WorkerRequest, WorkerResponse } from "./sketchProtocol";

export interface SketchRunner {
  load(code: string): Promise<EntryPoints>;
  init(params: Params, seed: number): Promise<void>;
  step(params: Params, dt: number, index: number, count: number): Promise<void>;
  read(params: Params, index: number): Promise<SketchRead>;
  dispose(): void;
}

export type SketchRunnerFactory = () => SketchRunner;

/** The engine host in this thread (tests; and the Worker's own side of the protocol). */
export function hostRunner(host: SketchEngineHost): SketchRunner {
  const wrap = <T,>(run: () => T): Promise<T> => {
    try {
      return Promise.resolve(run());
    } catch (caught) {
      return Promise.reject(caught);
    }
  };
  return {
    load: (code) => wrap(() => host.load(code)),
    init: (params, seed) => wrap(() => host.init(params, seed)),
    step: (params, dt, index, count) => wrap(() => host.step(params, dt, index, count)),
    read: (params, index) => wrap(() => {
      const { sceneText, probesText } = host.readText(params, index);
      return { scene: JSON.parse(sceneText), probes: JSON.parse(probesText), digest: sceneDigest(sceneText, probesText) };
    }),
    dispose: () => host.dispose(),
  };
}

/** A runner over a Worker-like port (postMessage / onmessage / terminate). */
export function portRunner(worker: { postMessage(message: WorkerRequest): void; terminate(): void; onmessage: ((event: { data: WorkerResponse }) => void) | null }): SketchRunner {
  let next = 1;
  const waiting = new Map<number, { op: WorkerOp; resolve: (value: unknown) => void; reject: (error: unknown) => void }>();
  let ended = false;
  worker.onmessage = (event) => {
    // Validated against the request's operation (fix round 4): a reply of
    // another shape rejects its call; one no request is waiting for is ignored.
    const reply = parseWorkerReply(event.data as unknown, (id) => waiting.get(id)?.op);
    if (!reply) return;
    const entry = waiting.get(reply.id)!;
    waiting.delete(reply.id);
    if (reply.ok) entry.resolve(reply.result);
    else entry.reject(reply.error);
  };
  const send = <T,>(op: WorkerOp, args: unknown[]): Promise<T> => {
    if (ended) return Promise.reject(new SketchRunError("paused", "the sketch was stopped"));
    const id = next++;
    return new Promise<T>((resolve, reject) => {
      waiting.set(id, { op, resolve: resolve as (value: unknown) => void, reject });
      worker.postMessage({ id, op, args });
    });
  };
  return {
    load: (code) => send<EntryPoints>("load", [code]),
    init: (params, seed) => send<void>("init", [params, seed]),
    step: (params, dt, index, count) => send<void>("step", [params, dt, index, count]),
    read: (params, index) => send<SketchRead>("read", [params, index]),
    dispose: () => {
      ended = true;
      worker.terminate();
      for (const entry of waiting.values()) entry.reject(new SketchRunError("paused", "the sketch was stopped"));
      waiting.clear();
    },
  };
}

/** keep: the watchdog's limit, SKETCH_FRAME_MS x SKETCH_WATCHDOG_FRAMES (480 ms). */
export const WATCHDOG_MS = SKETCH_FRAME_MS * SKETCH_WATCHDOG_FRAMES;

/** End the runner when one call outlives the watchdog (the Worker is
 *  terminated: a loop the engine could not interrupt can't freeze the Reader). */
export function withWatchdog(runner: SketchRunner, ms: number = WATCHDOG_MS, onPause?: () => void): SketchRunner {
  let stopped = false;
  const guard = <T,>(call: () => Promise<T>): Promise<T> => {
    if (stopped) return Promise.reject(new SketchRunError("paused", "the sketch is paused"));
    return new Promise<T>((resolve, reject) => {
      const timer = setTimeout(() => {
        stopped = true;
        runner.dispose();
        onPause?.();
        reject(new SketchRunError("paused", "paused — this simulation is too slow here"));
      }, ms);
      call().then(
        (value) => { clearTimeout(timer); resolve(value); },
        (error) => { clearTimeout(timer); reject(error); },
      );
    });
  };
  return {
    load: (code) => guard(() => runner.load(code)),
    init: (params, seed) => guard(() => runner.init(params, seed)),
    step: (params, dt, index, count) => guard(() => runner.step(params, dt, index, count)),
    read: (params, index) => guard(() => runner.read(params, index)),
    dispose: () => {
      stopped = true;
      runner.dispose();
    },
  };
}

/** The Worker, created on first use (its module is loaded only in the app). */
export function workerRunner(): SketchRunner {
  let real: SketchRunner | null = null;
  let disposed = false;
  const ready = import("./sketchWorkerClient").then((client) => {
    real = portRunner(client.createSketchWorker());
    if (disposed) real.dispose();
    return real;
  });
  const via = <T,>(call: (runner: SketchRunner) => Promise<T>) => ready.then(call);
  return {
    load: (code) => via((runner) => runner.load(code)),
    init: (params, seed) => via((runner) => runner.init(params, seed)),
    step: (params, dt, index, count) => via((runner) => runner.step(params, dt, index, count)),
    read: (params, index) => via((runner) => runner.read(params, index)),
    dispose: () => {
      disposed = true;
      real?.dispose();
    },
  };
}

/** Which runner a sketch uses: the Worker in the app; tests provide the in-process host. */
export const SketchRunnerContext = createContext<SketchRunnerFactory>(workerRunner);
