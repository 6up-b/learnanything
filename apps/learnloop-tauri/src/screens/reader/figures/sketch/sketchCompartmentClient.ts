// Reader RW5d P2: the one place the sketch compartment is made (loaded only in the app).
import workerSource from "virtual:sketch-worker-source";
import wasmUrl from "./sketch-engine.wasm?url";
import { appEngineBytes, createSketchCompartment, type WorkerLike } from "./sketchCompartment";

const engineBytes = appEngineBytes(wasmUrl);

export function createSketchWorker(): WorkerLike {
  return createSketchCompartment({ workerSource, engineBytes });
}
