// Reader RW5d P2: the sketch's dedicated Web Worker (spec_reader_show_me_figures_v1 §9.3).
//
// No DOM, terminable by the Reader's watchdog. It fetches the tracked engine
// once, checks its SHA-256 against the pin and instantiates it with the
// deny-all shim (sketchEngine.ts); then it only answers the narrow protocol
// (load, init, step, read), every request validated first and anything else
// refused (sketchProtocol.ts; fix round 4: an unknown operation is never
// treated as a read). The program inside the engine reaches nothing of this
// Worker either: it has no bindings at all. Supplementary hardening, not the
// boundary: the Worker's own network and import globals are removed once
// the engine is compiled.
import wasmUrl from "./sketch-engine.wasm?url";
import { SketchEngineHost } from "./sketchEngine";
import { answerRequest, type WorkerResponse } from "./sketchProtocol";

const scope = self as unknown as {
  onmessage: ((event: MessageEvent<unknown>) => void) | null;
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
  void answerRequest(host, event.data).then((reply) => scope.postMessage(reply));
};
