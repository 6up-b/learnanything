// Reader RW5d P2: the sketch's dedicated Web Worker (spec_reader_show_me_figures_v1 §9.3).
//
// No DOM, terminable by the Reader's watchdog. It fetches the tracked engine
// once, checks its SHA-256 against the pin and instantiates it with the
// deny-all shim (sketchEngine.ts); then it only relays the narrow protocol
// (load, init, step, read). The program inside the engine reaches nothing of
// this Worker either: it has no bindings at all. Belt and braces, the
// Worker's own network and import globals are removed once the engine is
// compiled, so not even this relay can use them afterwards.
import wasmUrl from "./sketch-engine.wasm?url";
import { SketchEngineHost, SketchRunError } from "./sketchEngine";
import type { WorkerRequest, WorkerResponse } from "./sketchRunner";

const scope = self as unknown as {
  onmessage: ((event: MessageEvent<WorkerRequest>) => void) | null;
  postMessage(message: WorkerResponse): void;
  [name: string]: unknown;
};

let engine: Promise<SketchEngineHost> | null = null;

function host(): Promise<SketchEngineHost> {
  engine ??= fetch(wasmUrl)
    .then((response) => response.arrayBuffer())
    .then((bytes) => SketchEngineHost.create(new Uint8Array(bytes)))
    .then((created) => {
      for (const name of ["fetch", "XMLHttpRequest", "WebSocket", "EventSource", "importScripts", "indexedDB", "caches"]) {
        try {
          delete scope[name];
          scope[name] = undefined;
        } catch {
          // a non-configurable global stays; the engine can't reach it anyway
        }
      }
      return created;
    });
  return engine;
}

scope.onmessage = (event) => {
  const { id, op, args } = event.data;
  host()
    .then((sketch) => {
      if (op === "load") return sketch.load(String(args[0]));
      if (op === "init") return sketch.init(args[0] as Record<string, number>, Number(args[1]));
      if (op === "step") return sketch.step(args[0] as Record<string, number>, Number(args[1]), Number(args[2]), Number(args[3]));
      const params = args[0] as Record<string, number>;
      const index = Number(args[1]);
      return { scene: sketch.view(params, index), probes: sketch.probes(params, index) };
    })
    .then(
      (result) => scope.postMessage({ id, ok: true, result }),
      (caught) => {
        const error = caught instanceof SketchRunError
          ? { kind: caught.kind, message: caught.message }
          : { kind: "error" as const, message: caught instanceof Error ? caught.message : String(caught) };
        scope.postMessage({ id, ok: false, error });
      },
    );
};
