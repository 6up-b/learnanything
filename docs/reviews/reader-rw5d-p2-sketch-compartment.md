# Reader RW5d P2: the sketch compartment (stage record)

- **Spec:** `docs/specs/spec_reader_show_me_figures_v1.md` rev 2, §9.3-9.4 and gate G-SM14 ("if Tauri does not refuse
  it, the Worker moves into an opaque-origin frame before P2 ships"). Inputs: the first probe's record,
  `docs/reviews/reader-rw5d-g-sm14-probe.md` (FAIL: a URL-loaded Worker gets no CSP, its prototype `fetch` survives
  the hardening, and Tauri can't tell it from the app).
- **Branch:** `reader/rw5d-p2-sketch-compartment` in `learnanything-astrafix`, base main `6318d46cfe`.
- **Migration:** none. **Successor:** none (content and display; nothing in scoring, scheduling, projection or serving
  reads a sketch).
- **Kill switch:** `figures.sketch_enabled`, now **on by default** (Q5's built default), because G-SM14 passed from
  inside the compartment (below). Off is unchanged: P1's contract byte for byte, no engine or wasmtime load.
- **Window:** one real desktop window, for the G-SM14 rerun only, under the owner's 2026-11-01 permission, with a
  throwaway synthetic vault. No other app or GUI window was launched.
- **Live calls:** none. Tests use fakes; Python outside pytest ran only under `env -i` with empty, existing `HOME`,
  `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` (to recompute fingerprints, regenerate references and make the probe vault).

## What the stage builds

### 1. The compartment (desktop)

- **`apps/learnloop-tauri/sketch-frame.html`** (a second Vite page; `vite.config.mjs` `build.rollupOptions.input`): the
  frame document. Its own CSP, enforced together with the app CSP header Tauri adds to every `.html` asset:
  `default-src 'none'; script-src 'sha256-…' 'wasm-unsafe-eval'; worker-src blob:; child-src blob:; connect-src 'none';`
  and `'none'` for images, styles, fonts, media, frames, objects, manifests, forms and base. `script-src` names only
  the hash of its one inline script (a vitest recomputes it), plus `'wasm-unsafe-eval'` for the engine. The script:
  - takes one `connect` window message, only from `window.parent`, carrying the control port, then never reads a window
    message again;
  - on the control port, accepts `boot {worker, engine}` once (the Worker's source ≤ `SKETCH_WORKER_SOURCE_MAX_CHARS`,
    the engine's bytes ≤ `SKETCH_ENGINE_MAX_BYTES`, exactly one transferred port) and `stop`; anything else is dropped;
  - starts the Worker **from a blob** of that source (so it inherits this document's policy; a URL-loaded Worker got
    none) and transfers the engine bytes and the engine port to it;
  - reports `connected`, `started` or `failed {message ≤ 600}`.
- **`sketchCompartment.ts`** (the Reader's side): one hidden iframe per open sketch, `sandbox="allow-scripts"` only (an
  opaque origin), `referrerpolicy="no-referrer"`, `aria-hidden`, zero-size; two private `MessageChannel`s. Requests wait
  until the frame reports `started`; a `failed` answers every request with that failure through the same validated
  reply path (`kind: "no_program"`). Terminating removes the frame, which ends its Worker. Control notices are parsed by
  `parseFrameNotice` (three kinds; everything else dropped; an over-long reason refused and replaced by code's words).
- **`sketchWorkerCore.ts`** (run by `sketch.worker.ts`): the Worker accepts one boot (`parseWorkerBoot`), checks the
  bytes against the pin and instantiates them (unchanged `SketchEngineHost`), removes its network, import and
  Worker-making globals **along the whole prototype chain** (`stripNetwork`: the first probe found `fetch` and
  `importScripts` on `WorkerGlobalScope.prototype`), and answers only the four operations on its port
  (`sketchProtocol.answerRequest`). It fetches nothing; the bytes came in.
- **`vite.config.mjs`**: a small plugin bundles `sketch.worker.ts` with esbuild into one IIFE string, the
  `virtual:sketch-worker-source` module, in dev and builds alike (`esbuild` added as a dev dependency; it was already
  installed through Vite at the overridden version). `sketchCompartmentClient.ts` (loaded only in the app) hands it and
  the engine's bytes (fetched once by the page from the `?url` asset, copied per compartment) to the compartment. The
  old URL Worker client (`sketchWorkerClient.ts`, `?worker`) is gone.
- **The protocol** (`sketchProtocol.ts`): a read now crosses the channel as the engine's own text
  (`{sceneText, probesText, digest}`), so the Reader bounds each reply exactly (`SKETCH_MAX_OUTPUT_CHARS`, the
  harness's 4 MiB output cap) and parses it itself; a reply carrying objects, extra keys or non-JSON text is
  malformed. Requests are validated in the Worker as before. Callers see the same `{scene, probes, digest}`.
- **The page's CSP** (`src-tauri/tauri.conf.json`): `frame-src` gains `tauri://localhost/sketch-frame.html` and
  `http://tauri.localhost/sketch-frame.html` and nothing else. Because the page's `frame-src` also governs where the
  frame may later navigate, its self-navigation to `ipc://` is refused (seen in the rerun).

New constants, each `keep` (structural or machine-safety guardrails, not tuning): `SKETCH_ENGINE_MAX_BYTES` (2 MiB;
the pinned engine is 869,346 bytes), `SKETCH_WORKER_SOURCE_MAX_CHARS` (1 MiB; the bundle is about 12 KB),
`FRAME_MESSAGE_MAX` (600, the protocol's `REPLY_MESSAGE_MAX`), `SKETCH_MAX_OUTPUT_CHARS` (the harness's output cap).
No config key was added, so nothing new to classify in `parameter_registry.py`.

### 2. Defense in depth in the Rust shell (item 3: what Tauri 2.11 allows)

- **Possible, and done:** LearnLoop's own invoke handler is wrapped (`main.rs`, `frame_guard.rs`): before any
  LearnLoop command runs, an invoke whose `Origin` is `null` (an opaque-origin frame) or whose `Referer` is a `blob:`,
  `data:`, `about:` (srcdoc) URL, a script asset (`/assets/…js`) or another HTML page (`/sketch-frame.html`) is
  rejected. The app's document (`/`, `/index.html`, extension-less routes, the dev origin) passes. Rust unit tests pin
  both lists, including every Referer the first probe saw. The custom protocol carries the webview's own `Origin` and
  `Referer` (forbidden headers for page script), so these can't be forged from a page.
- **Possible, and done (Linux):** the WebKit script-message handler `ipc` is unregistered after the window is built.
  WebKit exposes `window.webkit.messageHandlers` to **every** frame, and wry forwards each message with the **top**
  document's URL, so no handler can tell a sandboxed frame from the app on that path. On Linux Tauri sends every
  invoke over the `ipc:` custom protocol and uses postMessage only as a fallback when that fetch fails, so removing it
  costs only the fallback (the app's own start-up calls in the rerun all went over the custom protocol). With no
  handler registered, WebKit doesn't expose `window.webkit` at all (rerun: absent in the frame and the main window).
- **Not possible without replacing Tauri's IPC:** a hook *before* Tauri's `ipc:` protocol handler or its dispatcher
  (`Webview::on_message`). Tauri registers its `ipc` scheme only if the app hasn't (`manager/webview.rs`), so the app
  could pre-empt it, but `tauri::ipc::protocol` is crate-private and re-implementing the IPC protocol (responses,
  channels, raw bodies, CORS preflight) is not proportionate. Also not covered by the wrapper: core and plugin
  commands (`plugin:…`), which Tauri dispatches without the app's invoke handler. The boundary for those is the
  frame's CSP, which keeps the request inside WebKit (the rerun's verdict).

### 3. The G-SM14 rerun (item 5)

Recorded in full (every result line, every Rust log line, the scratch probe code) in
`docs/reviews/reader-rw5d-g-sm14-probe.md`, "Rerun after the compartment". **PASS**: no request from the frame
document, a fresh never-stripped blob Worker it made, that Worker's nested Worker, or the real sketch Worker reached
any Tauri handler (no `ipc-protocol`, `ipc-postmessage` or `on_message` line for any probe marker, none with Origin
`null`, every `ipc-protocol` Referer the app's own document), and every attempt failed in the page. The real path drew
the three verified corpus sketches digest-for-digest (55/55 tested reads) with no watchdog pause; the first call
(frame, blob Worker, engine compile, load) took 17-31 ms, every later call at most 3 ms (watchdog 480 ms). Scratch
branch `probe/g-sm14-compartment` (`2244360639`) holds the probe; it is never landed.

### 4. The default flips on (item 5, PASS)

- `FiguresConfig.sketch_enabled = True` (`config/schema.py`; the docstring says why and when).
- All 31 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` fingerprints recomputed with `defaults_fingerprint_for_version` after
  clearing the config `__pycache__` (first pass: 31 changed; second pass, caches cleared again: 0 changed). Parity
  check: setting `figures.sketch_enabled` back to false in each version's composed defaults reproduces the base
  fingerprint at every version, so nothing else moved. The note at mvp-0.9 records the flip.
- Tests that pinned "ships off until G-SM14" now pin the shipped default on and keep the off case:
  `tests/test_sketch_service.py` (`test_the_shipped_default_is_on`, `test_off_never_loads_the_engine`),
  `tests/test_figures_switch_off.py` (the contract with figures on carries `sketch: true`; turning the sketch off
  removes only that flag), `tests/figure_fixtures.py` (docstring).
- References regenerated (config field reference; desktop catalog for the new files); spec G-SM14 row and the UX doc
  carry a one-line status.
- **Not flipped:** `JS_ANIMATION_BUILD_FLAG` (`figures/rich.py`). The `js_animation` tier is a different frame
  (`llfig://`, not built), and its own extension of G-SM14 still has to run when it exists.

### Behaviour with the switch on

Same scenes, same verification, same timing budget: the engine, the protocol's four operations, the watchdog
(`SKETCH_FRAME_MS × SKETCH_WATCHDOG_FRAMES` = 480 ms per call, the first call still including start-up, as it did when
the Worker fetched and compiled the engine itself) and every scene check are unchanged; the parity corpus draws the
same digests through the whole compartment chain in vitest and in the real webview.

## Tests

- **vitest** `sketchCompartment.test.ts` (new, 21 cases): the frame document's policy (script hash recomputed, every
  directive, mirrored caps, the page's `frame-src`); control notices (three kinds, everything else dropped, over-long
  reason refused); the Worker's boot (bytes and exactly one port; oversize, empty, typed-array or extra-key boots
  refused); `stripNetwork` (own and prototype `fetch`, the Worker constructors, a non-configurable global reported); the
  compartment end to end with only the browser's frame and Worker faked (the real frame script evaluated, the real
  Worker start-up, the real engine): the verified corpus through `portRunner`, digest for digest; requests queued
  until start-up; a frame that can't make a Worker answers every request with the failure; a tampered engine refused
  inside the Worker; an oversize engine never booted; the frame script taking the control port only from its parent,
  once, dropping unknown kinds, refusing malformed and oversize boots, booting once, revoking the blob and terminating
  on stop; the Worker ignoring everything but one boot; the bundled `virtual:sketch-worker-source` running as one
  classic script with nothing to import.
- **vitest** `sketchProtocol.test.ts` (changed): a read reply carries the engine's text with its digest; replies with
  objects, extra keys or non-JSON text, or over the output cap, are malformed.
- The existing sketch vitest files (`SketchFigure`, `sketchSandboxReview`, `sketchParity`, `sketchScene`) are unchanged
  and pass; the kill switch's desktop behaviour (no sketch in the contract: no SketchFigure) is untouched.
- **Rust** `frame_guard` (3 tests): the app's documents pass; frames and workers (Origin `null`, blob, srcdoc, data,
  script assets, the frame page, a non-URL Referer) are refused; header parsing.
- **pytest**: see the gate.

## Gate

(Filled in below after the runs.)

## Open points

1. The postMessage fallback is removed on Linux (Tauri falls back to it when the custom-protocol fetch fails). If a
   future WebKitGTK ever breaks custom-protocol POSTs, invokes would fail instead of falling back. The rerun showed the
   app working without it; the owner may prefer keeping the fallback and accepting a frame-reachable handler there.
2. Dev mode (`npm run dev`): Vite serves `sketch-frame.html` itself and adds its HMR client script; the frame's meta CSP
   still blocks any connection. Not part of the gate (the gate is the shipped webview).
3. `js_animation` stays behind its build flag; its `llfig://` frame and G-SM14 extension are P2b's JS half.
