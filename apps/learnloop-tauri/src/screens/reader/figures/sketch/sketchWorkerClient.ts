// Reader RW5d P2: the one place the sketch Worker is constructed (loaded only in the app).
import SketchWorker from "./sketch.worker?worker";
import type { WorkerRequest, WorkerResponse } from "./sketchRunner";

export function createSketchWorker(): {
  postMessage(message: WorkerRequest): void;
  terminate(): void;
  onmessage: ((event: { data: WorkerResponse }) => void) | null;
} {
  return new SketchWorker() as unknown as ReturnType<typeof createSketchWorker>;
}
