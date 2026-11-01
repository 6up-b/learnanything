// Reader RW5d P2: the sketch Worker's start-up and loop (sketch.worker.ts runs it; vitest runs it on a fake scope).
//
// The Worker lives inside the sketch compartment's opaque-origin frame,
// created there from a blob (sketchFrameProtocol.ts). Its owner (the frame)
// sends one boot message: the pinned engine's bytes and the private port to
// the Reader. The Worker checks the bytes against the pin and instantiates
// them with the deny-all shim (sketchEngine.ts), removes its own network,
// import and Worker-making globals, tells the frame `started` (or `failed`),
// and from then on answers only sketchProtocol.ts's four operations on that
// port, every request validated first. It fetches nothing: the bytes came in.
import { SketchEngineHost } from "./sketchEngine";
import { parseWorkerBoot, stripNetwork, FRAME_MESSAGE_MAX } from "./sketchFrameProtocol";
import { answerRequest } from "./sketchProtocol";

export type WorkerScopeLike = {
  onmessage: ((event: { data: unknown; ports: readonly unknown[] }) => void) | null;
  postMessage(message: unknown): void;
};

export type EngineFactory = (bytes: Uint8Array) => Promise<SketchEngineHost>;

/** Start the Worker on its scope; `create` is the pinned engine host (tests may pass a Node digest). */
export function startSketchWorker(scope: WorkerScopeLike, create: EngineFactory = (bytes) => SketchEngineHost.create(bytes)): void {
  scope.onmessage = (event) => {
    const boot = parseWorkerBoot(event.data, event.ports ?? []);
    if (!boot) return;  // not a boot: dropped
    scope.onmessage = null;  // one boot; the frame has nothing more to say
    const { port } = boot;
    const engine = create(new Uint8Array(boot.engine)).then((created) => {
      stripNetwork(scope);
      return created;
    });
    engine.then(
      () => scope.postMessage({ kind: "started" }),
      (caught: unknown) => scope.postMessage({
        kind: "failed",
        message: (caught instanceof Error ? caught.message : String(caught)).slice(0, FRAME_MESSAGE_MAX),
      }),
    );
    port.onmessage = (message: MessageEvent<unknown>) => {
      void answerRequest(() => engine, message.data).then((reply) => port.postMessage(reply));
    };
  };
}
