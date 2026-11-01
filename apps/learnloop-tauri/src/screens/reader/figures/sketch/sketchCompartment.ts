// Reader RW5d P2: the sketch compartment, the Reader's side (G-SM14's remedy; spec_reader_show_me_figures_v1 §9.3-9.4).
//
// One hidden iframe per open sketch, `sandbox="allow-scripts"` only (an opaque
// origin: no storage, no access to this page, no IPC globals), on
// sketch-frame.html, whose CSP has `connect-src 'none'`. The frame starts the
// sketch Worker from a blob (so the Worker inherits that policy) and hands it
// the engine channel's port. The Reader then talks to the Worker over that
// private MessageChannel in sketchProtocol.ts's four operations, exactly as it
// talked to the URL-loaded Worker before (portRunner), and to the frame over a
// second private channel in sketchFrameProtocol.ts's closed notices. Requests
// wait here until the frame reports the engine started; a frame that reports
// failure answers every request with that failure. Terminating removes the
// frame, which ends the Worker with it.
import { parseFrameNotice, SKETCH_ENGINE_MAX_BYTES, SKETCH_FRAME_PATH, SKETCH_WORKER_SOURCE_MAX_CHARS } from "./sketchFrameProtocol";
import { parseWorkerRequest, REPLY_MESSAGE_MAX, type WorkerRequest, type WorkerResponse } from "./sketchProtocol";

export type WorkerLike = {
  postMessage(message: WorkerRequest): void;
  terminate(): void;
  onmessage: ((event: { data: WorkerResponse }) => void) | null;
};

/** What a compartment needs that only the app provides (the tests give fakes). */
export type CompartmentInputs = {
  /** The bundled Worker source (vite.config.mjs, `virtual:sketch-worker-source`). */
  workerSource: string;
  /** The pinned engine's bytes, fresh for each compartment (they are transferred). */
  engineBytes: () => Promise<ArrayBuffer>;
  document?: Document;
};

/** Make the sketch's compartment; a Worker-like handle for portRunner. */
export function createSketchCompartment(inputs: CompartmentInputs): WorkerLike {
  const doc = inputs.document ?? document;
  const control = new MessageChannel();
  const engine = new MessageChannel();
  const frame = doc.createElement("iframe");
  let state: "starting" | "started" | "failed" | "ended" = "starting";
  let failure = "";
  let pending: WorkerRequest[] = [];

  const handle: WorkerLike = {
    onmessage: null,
    postMessage(message) {
      if (state === "ended") return;
      if (state === "failed") {
        refuse(message);
        return;
      }
      if (state === "starting") {
        pending.push(message);
        return;
      }
      engine.port1.postMessage(message);
    },
    terminate() {
      if (state === "ended") return;
      state = "ended";
      pending = [];
      engine.port1.onmessage = null;
      engine.port1.close();
      // The frame stops its Worker; removing the frame ends both in any case (a document's dedicated
      // Workers end with it). The control port closes after the stop has been sent.
      try {
        control.port1.postMessage({ kind: "stop" });
      } catch {
        // the frame is gone
      }
      control.port1.onmessage = null;
      setTimeout(() => control.port1.close(), 0);
      frame.remove();
    },
  };

  /** Answer a request with the start-up failure, through the same validated reply path. */
  function refuse(message: WorkerRequest) {
    const parsed = parseWorkerRequest(message);
    const id = parsed.ok ? parsed.request.id : parsed.id;
    if (!id) return;
    handle.onmessage?.({ data: { id, ok: false, error: { kind: "no_program", message: failure.slice(0, REPLY_MESSAGE_MAX) } } });
  }

  function failWith(message: string) {
    if (state !== "starting" && state !== "started") return;
    state = "failed";
    failure = message;
    const waiting = pending;
    pending = [];
    for (const request of waiting) refuse(request);
  }

  engine.port1.onmessage = (event) => {
    if (state === "ended") return;
    handle.onmessage?.({ data: event.data as WorkerResponse });  // portRunner validates every reply (sketchProtocol.parseWorkerReply)
  };

  control.port1.onmessage = (event) => {
    const notice = parseFrameNotice(event.data);
    if (!notice || state === "ended") return;  // anything else is dropped
    if (notice.kind === "connected") {
      void boot();
      return;
    }
    if (notice.kind === "started") {
      if (state !== "starting") return;
      state = "started";
      const waiting = pending;
      pending = [];
      for (const request of waiting) engine.port1.postMessage(request);
      return;
    }
    failWith(notice.message);
  };

  let booted = false;
  async function boot() {
    if (booted) return;
    booted = true;
    try {
      if (inputs.workerSource.length > SKETCH_WORKER_SOURCE_MAX_CHARS) throw new Error("the sketch engine's Worker is too large");
      const bytes = await inputs.engineBytes();
      if (bytes.byteLength === 0 || bytes.byteLength > SKETCH_ENGINE_MAX_BYTES) throw new Error("the sketch engine's size is not the pinned one's");
      if (state !== "starting") return;
      control.port1.postMessage({ kind: "boot", worker: inputs.workerSource, engine: bytes }, [engine.port2, bytes]);
    } catch (caught) {
      failWith(caught instanceof Error ? caught.message : String(caught));
    }
  }

  frame.setAttribute("sandbox", "allow-scripts");
  frame.setAttribute("referrerpolicy", "no-referrer");
  frame.setAttribute("aria-hidden", "true");
  frame.setAttribute("tabindex", "-1");
  frame.setAttribute("title", "sketch engine");
  frame.dataset.sketchCompartment = "";
  Object.assign(frame.style, { position: "fixed", width: "0", height: "0", border: "0", visibility: "hidden", pointerEvents: "none" });
  frame.addEventListener("load", () => {
    if (state === "ended" || !frame.contentWindow) return;
    // The one window message: the control port, to whatever document the frame holds (opaque, hence "*").
    frame.contentWindow.postMessage({ kind: "connect" }, "*", [control.port2]);
  }, { once: true });
  frame.src = SKETCH_FRAME_PATH;
  doc.body.appendChild(frame);
  return handle;
}

let engineCache: Promise<ArrayBuffer> | null = null;

/** The pinned engine's bytes from the app's assets, fetched once by this page (a copy per compartment;
 *  the Worker checks the pin before it runs them). */
export function appEngineBytes(url: string): () => Promise<ArrayBuffer> {
  return () => {
    engineCache ??= fetch(url).then((response) => {
      if (!response.ok) throw new Error(`the sketch engine could not be read (${response.status})`);
      return response.arrayBuffer();
    });
    const shared = engineCache;
    shared.catch(() => { if (engineCache === shared) engineCache = null; });
    return shared.then((bytes) => bytes.slice(0));
  };
}
