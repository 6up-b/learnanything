# Reader RW5d P2: G-SM14 probe record (sketch Worker → Tauri IPC)

- **Date:** 2026-11-01 (run 14:23:23–14:24:13 -05:00, one window, about 50 s).
- **Permission:** the owner granted permission on 2026-11-01 to open one real desktop window for this probe only,
  with a throwaway synthetic vault. No owner vault, retired vault or book was opened or listed.
- **Gate:** spec_reader_show_me_figures_v1 G-SM14 (gates table; §9.4 threat model; §16 P2): "In the real desktop
  webview on Linux, a request to the IPC endpoint from inside the sketch Worker is refused (if not, the
  opaque-origin frame is added before merge)." Recipe: `docs/reviews/reader-rw5d-p2-sketch.md`, "G-SM14 probe recipe".
- **Verdict: FAIL.** Requests from inside the sketch Worker, after its normal start-up, reach Tauri's `ipc:`
  custom-protocol handler and, for POSTs, Tauri's invoke dispatcher (`Webview::on_message`), where they're refused
  only because the invoke key is wrong. No command ran. The recipe counts a request that reaches a handler and is then
  refused for lack of the initialization key as a failure. So `figures.sketch_enabled` **stays off** (the default
  is unchanged), and the opaque-origin compartment becomes its own stage (not built here).
- **Rerun after the compartment (same day): PASS.** With the Worker started from a blob inside a sandboxed,
  opaque-origin frame whose CSP has `connect-src 'none'`, no request from the frame, its Workers or a nested Worker
  reached any Tauri handler, and every attempt failed. `figures.sketch_enabled` now defaults on. See "Rerun after the
  compartment" at the end.

## Versions

| Component | Version |
|---|---|
| Tauri (crate) / tauri-runtime-wry | 2.11.2 / 2.11.2 (Cargo.lock) |
| Wry / tao | 0.55.1 / 0.35.2 |
| webkit2gtk (Rust binding) | 2.0.2 |
| WebKitGTK (system, `webkit2gtk-4.1`) | 2.54.1 (pacman `webkit2gtk-4.1 2.54.1-1`) |
| `@tauri-apps/api` (node_modules) | 2.11.0 |
| User agent seen by the page | `Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/60.5 Safari/605.1.15` |
| OS / compositor | CachyOS, Linux 7.2.9-2-cachyos, Hyprland (Wayland) |
| rustc | 1.99.0 |
| Base commit | main `0d607bdfe9` |

## How it was run

- **Build: production-equivalent, not `tauri dev`.** On desktop, `tauri dev` loads the Vite server
  (`http://localhost:1420`) directly. Tauri's CSP is not applied there, and the origin is not the app's. The gate is
  about the shipped webview, so the probe ran in a debug binary with embedded assets:
  `VITE_GSM14_PROBE=1 npm run frontend:build`, then `cargo build --features custom-protocol --offline -j 8` (the
  `tauri build` path without bundling). The page loads from `tauri://localhost` with the app's CSP header injected,
  exactly as in a release. Both builds ran in `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`. No dev
  server was started; nothing bound a port.
- **Scratch branch `probe/g-sm14`** (commit `f61cc5aadb`, from main `0d607bdfe9`, **never landed**) holds all probe
  code: the Worker probe, the main-window harness, a temporary `gsm14_report` command and a Cargo patch. The patch
  points `tauri` at a scratch copy of 2.11.2 under `/tmp` that adds logging (diff below).
- **Automation:** with `VITE_GSM14_PROBE=1`, `main.tsx` waits 4 s after start, then:
  1. runs two labelled CONTROLS (C1: a main-window fetch without a key; C2: a fresh blob Worker created by the main
     window). These are context, not part of the verdict;
  2. creates the real sketch Worker through `createSketchWorker()` (the production `?worker` import);
  3. sends one real `load` request, so the Worker's normal start-up runs: wasm fetched, pinned SHA-256 checked,
     engine instantiated, then `fetch`/`XMLHttpRequest`/`WebSocket`/`EventSource`/`importScripts`/`indexedDB`/`caches`
     deleted;
  4. sends `{gsm14: "probe"}`. The Worker awaits `host()` again (already resolved), runs every attempt in try/catch
     and posts back one line per attempt;
  5. invokes `gsm14_report` from the **main window** (never from the Worker). Rust writes each line to stderr as
     `GSM14-RESULT …` and calls `app.exit(0)` 1.5 s later.
- **Rust-side visibility:** the patched Tauri logs every request that reaches the `ipc:` protocol handler (method,
  URI, Origin, Referer, whether a `Tauri-Invoke-Key` header is present, body length) and every message on the
  postMessage (WebKit script message handler) path. It also logs every call into `Webview::on_message` before the key
  check. The stock key-mismatch `eprintln!` was changed to redact the expected key. The app's own traffic is logged
  too; probe requests carry a `?gsm14=<W|N|M|I|C1|C2>` marker (W = sketch Worker fetch, M = sketch Worker
  `import()`, N = nested Worker spawned by the sketch Worker, I = importScripts, C1/C2 = controls).
- **Environment** (one launch, `env -i`, inside the same 5G scope, `timeout 240` as a backstop):

```
PATH=$PATH
HOME=<scratch>/gsm14/home            (empty)
XDG_CONFIG_HOME=<scratch>/gsm14/xdg/config  XDG_DATA_HOME=<scratch>/gsm14/xdg/data  XDG_CACHE_HOME=<scratch>/gsm14/xdg/cache
TMPDIR=<scratch>/gsm14/tmp
WAYLAND_DISPLAY=wayland-1  DISPLAY=:0  XDG_RUNTIME_DIR=/run/user/1000
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus  XDG_SESSION_TYPE=wayland
LEARNLOOP_VAULT=<scratch>/gsm14/vault        (fresh: `learnloop init` under env -i, empty HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR)
LEARNLOOP_CONFIG_DIR=<scratch>/gsm14/config  (empty)
CODEX_HOME=<scratch>/gsm14/codex             (empty: no ChatGPT-plan sign-in)
LEARNLOOP_AI_PROVIDER=gsm14-none             (no such profile)
LEARNLOOP_PYTHON=<worktree>/.venv/bin/python
RUST_LOG=debug  LEARNLOOP_SIDECAR_DEBUG_LOG=<scratch>/gsm14/sidecar-run1.log  VITE_GSM14_PROBE=1
```

  `<scratch>` = `/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/a22010cc-5149-4947-a2b8-247f18b8f1a0/scratchpad`.
  The app exited on its own (exit 0); no LearnLoop or sidecar process remained afterwards. The vault has **0**
  `model_call_receipts` rows (no model call). The app has no Rust logger, so `RUST_LOG` printed nothing extra and
  stderr held only the probe's lines. The sidecar debug log stayed empty.

## Results (every line, as reported)

```
main: location.origin=tauri://localhost userAgent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/60.5 Safari/605.1.15
main: __TAURI_INTERNALS__=object
CONTROL C1 (main-window fetch, no key): OK status=500 body="missing Tauri-Invoke-Key header"
CONTROL C2 (fresh blob Worker from main window, not the sketch Worker): GET OK status=405 body="only POST and OPTIONS are allowed" | POST error Error: timeout (no answer in 4 s)
WORKER real load op reply: {"id":1,"ok":true,"result":{"init":true,"step":true,"view":true,"probes":true}}
WORKER startup: engine verified and instantiated; globals deleted
WORKER context: location.origin=tauri://localhost isSecureContext=true
WORKER fetch GET via self.fetch -> ipc-scheme: absent (undefined)
WORKER fetch POST(real invoke shape) via self.fetch -> ipc-scheme: absent (undefined)
WORKER fetch GET via self.fetch -> ipc-scheme-real-shape: absent (undefined)
WORKER fetch POST(real invoke shape) via self.fetch -> ipc-scheme-real-shape: absent (undefined)
WORKER fetch GET via self.fetch -> http-ipc-localhost: absent (undefined)
WORKER fetch POST(real invoke shape) via self.fetch -> http-ipc-localhost: absent (undefined)
WORKER fetch GET via self.fetch -> http-ipc-localhost-real-shape: absent (undefined)
WORKER fetch POST(real invoke shape) via self.fetch -> http-ipc-localhost-real-shape: absent (undefined)
WORKER fetch GET via globalThis.fetch -> ipc-scheme: absent (undefined)
WORKER fetch POST(real invoke shape) via globalThis.fetch -> ipc-scheme: absent (undefined)
WORKER fetch GET via globalThis.fetch -> ipc-scheme-real-shape: absent (undefined)
WORKER fetch POST(real invoke shape) via globalThis.fetch -> ipc-scheme-real-shape: absent (undefined)
WORKER fetch GET via globalThis.fetch -> http-ipc-localhost: absent (undefined)
WORKER fetch POST(real invoke shape) via globalThis.fetch -> http-ipc-localhost: absent (undefined)
WORKER fetch GET via globalThis.fetch -> http-ipc-localhost-real-shape: absent (undefined)
WORKER fetch POST(real invoke shape) via globalThis.fetch -> http-ipc-localhost-real-shape: absent (undefined)
WORKER fetch GET via Object.getPrototypeOf(self).fetch -> ipc-scheme: OK status=405 tauri-response=null body="only POST and OPTIONS are allowed"
WORKER fetch POST(real invoke shape) via Object.getPrototypeOf(self).fetch -> ipc-scheme: error Error: timeout (no answer in 4 s)
WORKER fetch GET via Object.getPrototypeOf(self).fetch -> ipc-scheme-real-shape: OK status=405 tauri-response=null body="only POST and OPTIONS are allowed"
WORKER fetch POST(real invoke shape) via Object.getPrototypeOf(self).fetch -> ipc-scheme-real-shape: error Error: timeout (no answer in 4 s)
WORKER fetch GET via Object.getPrototypeOf(self).fetch -> http-ipc-localhost: error TypeError: Load failed
WORKER fetch POST(real invoke shape) via Object.getPrototypeOf(self).fetch -> http-ipc-localhost: error TypeError: Load failed
WORKER fetch GET via Object.getPrototypeOf(self).fetch -> http-ipc-localhost-real-shape: error TypeError: Load failed
WORKER fetch POST(real invoke shape) via Object.getPrototypeOf(self).fetch -> http-ipc-localhost-real-shape: error TypeError: Load failed
WORKER fetch GET via WorkerGlobalScope.prototype.fetch -> ipc-scheme: OK status=405 tauri-response=null body="only POST and OPTIONS are allowed"
WORKER fetch POST(real invoke shape) via WorkerGlobalScope.prototype.fetch -> ipc-scheme: error Error: timeout (no answer in 4 s)
WORKER fetch GET via WorkerGlobalScope.prototype.fetch -> ipc-scheme-real-shape: OK status=405 tauri-response=null body="only POST and OPTIONS are allowed"
WORKER fetch POST(real invoke shape) via WorkerGlobalScope.prototype.fetch -> ipc-scheme-real-shape: error Error: timeout (no answer in 4 s)
WORKER fetch GET via WorkerGlobalScope.prototype.fetch -> http-ipc-localhost: error TypeError: Load failed
WORKER fetch POST(real invoke shape) via WorkerGlobalScope.prototype.fetch -> http-ipc-localhost: error TypeError: Load failed
WORKER fetch GET via WorkerGlobalScope.prototype.fetch -> http-ipc-localhost-real-shape: error TypeError: Load failed
WORKER fetch POST(real invoke shape) via WorkerGlobalScope.prototype.fetch -> http-ipc-localhost-real-shape: error TypeError: Load failed
WORKER fetch GET via DedicatedWorkerGlobalScope.prototype.fetch -> ipc-scheme: OK status=405 tauri-response=null body="only POST and OPTIONS are allowed"
WORKER fetch POST(real invoke shape) via DedicatedWorkerGlobalScope.prototype.fetch -> ipc-scheme: error Error: timeout (no answer in 4 s)
WORKER fetch GET via DedicatedWorkerGlobalScope.prototype.fetch -> ipc-scheme-real-shape: OK status=405 tauri-response=null body="only POST and OPTIONS are allowed"
WORKER fetch POST(real invoke shape) via DedicatedWorkerGlobalScope.prototype.fetch -> ipc-scheme-real-shape: error Error: timeout (no answer in 4 s)
WORKER fetch GET via DedicatedWorkerGlobalScope.prototype.fetch -> http-ipc-localhost: error TypeError: Load failed
WORKER fetch POST(real invoke shape) via DedicatedWorkerGlobalScope.prototype.fetch -> http-ipc-localhost: error TypeError: Load failed
WORKER fetch GET via DedicatedWorkerGlobalScope.prototype.fetch -> http-ipc-localhost-real-shape: error TypeError: Load failed
WORKER fetch POST(real invoke shape) via DedicatedWorkerGlobalScope.prototype.fetch -> http-ipc-localhost-real-shape: error TypeError: Load failed
WORKER fetch GET via prototype chain depth 2 (WorkerGlobalScope).fetch -> ipc-scheme: OK status=405 tauri-response=null body="only POST and OPTIONS are allowed"
WORKER fetch POST(real invoke shape) via prototype chain depth 2 (WorkerGlobalScope).fetch -> ipc-scheme: error Error: timeout (no answer in 4 s)
WORKER fetch GET via prototype chain depth 2 (WorkerGlobalScope).fetch -> ipc-scheme-real-shape: OK status=405 tauri-response=null body="only POST and OPTIONS are allowed"
WORKER fetch POST(real invoke shape) via prototype chain depth 2 (WorkerGlobalScope).fetch -> ipc-scheme-real-shape: error Error: timeout (no answer in 4 s)
WORKER fetch GET via prototype chain depth 2 (WorkerGlobalScope).fetch -> http-ipc-localhost: error TypeError: Load failed
WORKER fetch POST(real invoke shape) via prototype chain depth 2 (WorkerGlobalScope).fetch -> http-ipc-localhost: error TypeError: Load failed
WORKER fetch GET via prototype chain depth 2 (WorkerGlobalScope).fetch -> http-ipc-localhost-real-shape: error TypeError: Load failed
WORKER fetch POST(real invoke shape) via prototype chain depth 2 (WorkerGlobalScope).fetch -> http-ipc-localhost-real-shape: error TypeError: Load failed
WORKER XMLHttpRequest GET via self.XMLHttpRequest -> ipc-scheme: absent (undefined)
WORKER XMLHttpRequest POST via self.XMLHttpRequest -> ipc-scheme: absent (undefined)
WORKER XMLHttpRequest GET via self.XMLHttpRequest -> ipc-scheme-real-shape: absent (undefined)
WORKER XMLHttpRequest POST via self.XMLHttpRequest -> ipc-scheme-real-shape: absent (undefined)
WORKER XMLHttpRequest GET via self.XMLHttpRequest -> http-ipc-localhost: absent (undefined)
WORKER XMLHttpRequest POST via self.XMLHttpRequest -> http-ipc-localhost: absent (undefined)
WORKER XMLHttpRequest GET via self.XMLHttpRequest -> http-ipc-localhost-real-shape: absent (undefined)
WORKER XMLHttpRequest POST via self.XMLHttpRequest -> http-ipc-localhost-real-shape: absent (undefined)
WORKER XMLHttpRequest GET via globalThis.XMLHttpRequest -> ipc-scheme: absent (undefined)
WORKER XMLHttpRequest POST via globalThis.XMLHttpRequest -> ipc-scheme: absent (undefined)
WORKER XMLHttpRequest GET via globalThis.XMLHttpRequest -> ipc-scheme-real-shape: absent (undefined)
WORKER XMLHttpRequest POST via globalThis.XMLHttpRequest -> ipc-scheme-real-shape: absent (undefined)
WORKER XMLHttpRequest GET via globalThis.XMLHttpRequest -> http-ipc-localhost: absent (undefined)
WORKER XMLHttpRequest POST via globalThis.XMLHttpRequest -> http-ipc-localhost: absent (undefined)
WORKER XMLHttpRequest GET via globalThis.XMLHttpRequest -> http-ipc-localhost-real-shape: absent (undefined)
WORKER XMLHttpRequest POST via globalThis.XMLHttpRequest -> http-ipc-localhost-real-shape: absent (undefined)
WORKER WebSocket ws://ipc.localhost via self.WebSocket: absent (undefined)
WORKER WebSocket ws://ipc.localhost via globalThis.WebSocket: absent (undefined)
WORKER self.__TAURI_INTERNALS__: absent
WORKER self.__TAURI__: absent
WORKER self.__TAURI_INVOKE_KEY__: absent
WORKER self.ipc: absent
WORKER self.webkit: absent
WORKER self.webkit?.messageHandlers: absent
WORKER self.chrome?.webview: absent
WORKER self.window / document / parent / top: absent / absent / absent / absent
WORKER other: EventSource=absent importScripts=absent WorkerGlobalScope.prototype.importScripts=PRESENT (function) Worker=PRESENT (function) SharedWorker=absent WebTransport=absent navigator.serviceWorker=PRESENT (object)
WORKER importScripts(blob:) via self.importScripts: absent (undefined)
WORKER importScripts(blob:) via WorkerGlobalScope.prototype.importScripts: loaded; fetch absent in importScripts scope (undefined)
WORKER dynamic import() -> ipc-scheme: error TypeError: Importing a module script failed.
WORKER dynamic import() -> ipc-scheme-real-shape: error TypeError: Importing a module script failed.
WORKER dynamic import() -> http-ipc-localhost: error TypeError: Importing a module script failed.
WORKER dynamic import() -> http-ipc-localhost-real-shape: error TypeError: Importing a module script failed.
WORKER nested blob Worker: started
WORKER nested.typeof fetch=function XMLHttpRequest=function WebSocket=function
WORKER nested.global __TAURI_INTERNALS__: absent
WORKER nested.global __TAURI__: absent
WORKER nested.global ipc: absent
WORKER nested.global webkit: absent
WORKER nested.fetch GET ipc-scheme: OK status=405 tauri-response=null body="only POST and OPTIONS are allowed"
WORKER nested.fetch POST ipc-scheme: error Error: timeout (no answer in 4 s)
WORKER nested.fetch GET ipc-scheme-real-shape: OK status=405 tauri-response=null body="only POST and OPTIONS are allowed"
WORKER nested.fetch POST ipc-scheme-real-shape: error Error: timeout (no answer in 4 s)
WORKER nested.fetch GET http-ipc-localhost: error TypeError: Load failed
WORKER nested.fetch POST http-ipc-localhost: error TypeError: Load failed
WORKER nested.fetch GET http-ipc-localhost-real-shape: error TypeError: Load failed
WORKER nested.fetch POST http-ipc-localhost-real-shape: error TypeError: Load failed
GSM14-RESULT-END (102 lines)
```

## Rust-side log (every probe-marked request, and what followed it)

All 22 requests from the sketch Worker and its nested Worker reached the `ipc:` protocol handler, as did the 3
control requests. Every POST that carried the real invoke shape went on into `on_message` and was refused at the key
check. That's 11 refusals: 8 from the sketch Worker, 2 from its nested Worker, 1 from control C2. Stock Tauri then
never answers the request, which is why those fetches time out in the Worker. GETs got Tauri's own
`405 only POST and OPTIONS are allowed`. Nothing reached the postMessage path (`ipc-postmessage`: 0 lines). No probe
request reached an app command handler or a plugin command.

```
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=C1 origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=false body_len=2
GSM14-RUST ipc-protocol label=main method=GET uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=C2 origin=Some("tauri://localhost") referer=Some("blob:tauri://localhost/475eccc0-0dbe-45be-8fd9-29b96144c0d1") has_invoke_key_header=false body_len=0
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=C2 origin=Some("tauri://localhost") referer=Some("blob:tauri://localhost/475eccc0-0dbe-45be-8fd9-29b96144c0d1") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=plugin:app|version url=tauri://localhost
GSM14-RUST on_message: __TAURI_INVOKE_KEY__ mismatch (expected <redacted, 20 chars>) received "gsm14-guessed-key" cmd=plugin:app|version url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=GET uri=ipc://localhost/plugin:app|ping?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=false body_len=0
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin:app|ping?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=plugin:app|ping url=tauri://localhost
GSM14-RUST on_message: __TAURI_INVOKE_KEY__ mismatch (expected <redacted, 20 chars>) received "gsm14-guessed-key" cmd=plugin:app|ping url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=GET uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=false body_len=0
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=plugin:app|version url=tauri://localhost
GSM14-RUST on_message: __TAURI_INVOKE_KEY__ mismatch (expected <redacted, 20 chars>) received "gsm14-guessed-key" cmd=plugin:app|version url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=GET uri=ipc://localhost/plugin:app|ping?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=false body_len=0
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin:app|ping?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=plugin:app|ping url=tauri://localhost
GSM14-RUST on_message: __TAURI_INVOKE_KEY__ mismatch (expected <redacted, 20 chars>) received "gsm14-guessed-key" cmd=plugin:app|ping url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=GET uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=false body_len=0
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=plugin:app|version url=tauri://localhost
GSM14-RUST on_message: __TAURI_INVOKE_KEY__ mismatch (expected <redacted, 20 chars>) received "gsm14-guessed-key" cmd=plugin:app|version url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=GET uri=ipc://localhost/plugin:app|ping?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=false body_len=0
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin:app|ping?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=plugin:app|ping url=tauri://localhost
GSM14-RUST on_message: __TAURI_INVOKE_KEY__ mismatch (expected <redacted, 20 chars>) received "gsm14-guessed-key" cmd=plugin:app|ping url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=GET uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=false body_len=0
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=plugin:app|version url=tauri://localhost
GSM14-RUST on_message: __TAURI_INVOKE_KEY__ mismatch (expected <redacted, 20 chars>) received "gsm14-guessed-key" cmd=plugin:app|version url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=GET uri=ipc://localhost/plugin:app|ping?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=false body_len=0
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin:app|ping?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=plugin:app|ping url=tauri://localhost
GSM14-RUST on_message: __TAURI_INVOKE_KEY__ mismatch (expected <redacted, 20 chars>) received "gsm14-guessed-key" cmd=plugin:app|ping url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=GET uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=false body_len=0
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=W origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=plugin:app|version url=tauri://localhost
GSM14-RUST on_message: __TAURI_INVOKE_KEY__ mismatch (expected <redacted, 20 chars>) received "gsm14-guessed-key" cmd=plugin:app|version url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=GET uri=ipc://localhost/plugin:app|ping?gsm14=M origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=false body_len=0
GSM14-RUST ipc-protocol label=main method=GET uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=M origin=Some("tauri://localhost") referer=Some("tauri://localhost/assets/sketch.worker-DD4eymAa.js") has_invoke_key_header=false body_len=0
GSM14-RUST ipc-protocol label=main method=GET uri=ipc://localhost/plugin:app|ping?gsm14=N origin=Some("tauri://localhost") referer=Some("blob:tauri://localhost/bd98b893-5790-4e74-b773-57e669cf2440") has_invoke_key_header=false body_len=0
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin:app|ping?gsm14=N origin=Some("tauri://localhost") referer=Some("blob:tauri://localhost/bd98b893-5790-4e74-b773-57e669cf2440") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=plugin:app|ping url=tauri://localhost
GSM14-RUST on_message: __TAURI_INVOKE_KEY__ mismatch (expected <redacted, 20 chars>) received "gsm14-guessed-key" cmd=plugin:app|ping url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=GET uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=N origin=Some("tauri://localhost") referer=Some("blob:tauri://localhost/bd98b893-5790-4e74-b773-57e669cf2440") has_invoke_key_header=false body_len=0
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=N origin=Some("tauri://localhost") referer=Some("blob:tauri://localhost/bd98b893-5790-4e74-b773-57e669cf2440") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=plugin:app|version url=tauri://localhost
GSM14-RUST on_message: __TAURI_INVOKE_KEY__ mismatch (expected <redacted, 20 chars>) received "gsm14-guessed-key" cmd=plugin:app|version url=tauri://localhost
```

The app's own calls, for contrast. They look identical (label `main`, Origin `tauri://localhost`) except for the
Referer and the real key:

```
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/load_vault origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=load_vault url=tauri://localhost
```

## What the results show

1. **The Worker's network hardening doesn't remove `fetch`.** In this WebKitGTK, `fetch` and `importScripts` live on
   `WorkerGlobalScope.prototype`. `delete self.fetch; self.fetch = undefined` only shadows them, so
   `Object.getPrototypeOf(self).fetch`, `WorkerGlobalScope.prototype.fetch` and
   `DedicatedWorkerGlobalScope.prototype.fetch` all still work (the last two resolve through the chain).
   `WorkerGlobalScope.prototype.importScripts` survives the same way. `XMLHttpRequest`, `WebSocket` and `EventSource`
   are own properties and were removed. The `Worker` constructor is never removed, so a nested blob Worker starts
   with intact `fetch`, `XMLHttpRequest` and `WebSocket`.
2. **The Worker has no CSP of its own.** Tauri 2.11.2 attaches the `Content-Security-Policy` header only to `.html`
   assets (`manager/mod.rs`, `get_asset`: `is_html`). The Worker script `assets/sketch.worker-*.js` is served
   without one, and a dedicated Worker loaded from a URL takes its policy from its own response. Evidence: a
   module `import()` of `ipc://localhost/…` was sent to Rust (`gsm14=M`) even though the app CSP's `script-src` is
   `'self' 'wasm-unsafe-eval'`. (The app CSP's `connect-src` names `ipc:` anyway, so fetch would pass under it
   too.)
3. **Tauri can't tell the Worker from the app's document.** Its requests arrive as label `main`, Origin
   `tauri://localhost`, and `on_message` resolves `url=tauri://localhost`, a local origin, the same ACL origin as
   the app. Only the Referer (`tauri://localhost/assets/sketch.worker-*.js`, `blob:tauri://localhost/…`) differs,
   and Tauri doesn't use it. **The only barrier is the 20-character invoke key.** It sits in a closure in the main
   window's init script (`__TAURI_INVOKE_KEY__`), and nothing in the Worker protocol carries it. That matches the
   Astra review's "low likelihood of a successful call". The gate, though, is about reaching a handler, and that
   happened.
4. **Not reachable:** `__TAURI_INTERNALS__`, `__TAURI__`, `ipc`, `webkit.messageHandlers` and `chrome.webview` are
   absent in the Worker and in its nested Worker. The postMessage IPC path was never hit. `http://ipc.localhost` is
   Windows/Android-only in Tauri; on Linux it is plain HTTP to 127.0.0.1:80, where nothing listens on this machine
   (`TypeError: Load failed`), and it never reached Tauri.
5. **Context from the controls:** C1 proves the logging sees a keyless request from the app (500
   `missing Tauri-Invoke-Key header`). C2 shows that any Worker in this webview reaches the `ipc:` handler, not just
   a stripped one that leaks.

**Realistic risk** (proportionate bar): a model sketch still can't reach the Worker's globals without a QuickJS/wasm
escape. Even then, it would also need the invoke key to run a command. The concrete exposure is the
handler and dispatcher being reachable at all, plus one unanswered pending request and one stderr line per attempt.
The gate is written to fail on exactly this, so P2 stays off.

## Inputs for the follow-up stage (opaque-origin compartment; not built here)

- Deleting more globals (the prototype `fetch`/`importScripts`, the `Worker` constructor) would close the paths
  this probe found. It would still be deny-listing inside a same-origin context that Tauri treats as the app, and any
  Worker here reaches `ipc:` (C2). The spec's remedy is the compartment: block the request before it leaves WebKit,
  or change what it is.
- **A frame CSP does not reach a URL-loaded Worker.** The fallback recipe's "restrictive CSP inside the frame,
  including `connect-src 'none'`" governs a Worker only if it is a `blob:`/`data:` Worker created inside the frame
  (it inherits the frame's policy), or if the Worker script's own response carries a CSP. Tauri adds none to `.js`.
  Either serve the Worker script with a CSP header (e.g. from a custom protocol, as `llpdf`/`llmedia` are served) or
  create it from a blob inside the sandboxed frame. Then rerun this probe from inside.
- In an opaque-origin frame, Origin becomes `null`. Tauri's `parse_invoke_request` then fails with "Origin header is
  not a valid URL", but **inside the protocol handler**, which this gate still counts as reaching it. The rerun
  should therefore look for **no `ipc-protocol` line at all**: a CSP that blocks the request in WebKit before it is
  sent. Keep the WebKit message-handler checks; they're absent in a Worker but must be rechecked in a frame.
- The patched-Tauri logging and the harness on `probe/g-sm14` can be reused for the rerun.

## Probe code (exact; branch `probe/g-sm14`, commit `f61cc5aadb`, never landed)

### Sketch Worker probe (`apps/learnloop-tauri/src/screens/reader/figures/sketch/sketch.worker.ts`)

```diff
diff --git a/apps/learnloop-tauri/src/screens/reader/figures/sketch/sketch.worker.ts b/apps/learnloop-tauri/src/screens/reader/figures/sketch/sketch.worker.ts
index 16484eea98..cd01e7cd91 100644
--- a/apps/learnloop-tauri/src/screens/reader/figures/sketch/sketch.worker.ts
+++ b/apps/learnloop-tauri/src/screens/reader/figures/sketch/sketch.worker.ts
@@ -39,6 +39,220 @@ function host(): Promise<SketchEngineHost> {
   return engine;
 }
 
+// ---- G-SM14 PROBE (scratch branch probe/g-sm14, never landed) ----
+// Runs only when the build sets VITE_GSM14_PROBE=1 and the owner sends
+// {gsm14: "probe"}; it first waits for the normal start-up (wasm fetched,
+// pinned digest checked, network/import globals deleted).
+const GSM14_TIMEOUT_MS = 4000;
+const GSM14_CMD = "plugin:app|version"; // core:default -> core:app:default allows it; harmless read
+const GSM14_IPC_URLS = [
+  { label: "ipc-scheme", url: "ipc://localhost/plugin:app|ping?gsm14=W" },
+  { label: "ipc-scheme-real-shape", url: `ipc://localhost/${encodeURIComponent(GSM14_CMD)}?gsm14=W` },
+  { label: "http-ipc-localhost", url: "http://ipc.localhost/plugin:app|ping?gsm14=W" },
+  { label: "http-ipc-localhost-real-shape", url: `http://ipc.localhost/${encodeURIComponent(GSM14_CMD)}?gsm14=W` },
+];
+// The exact request @tauri-apps/api's invoke makes on Linux (tauri 2.11.2
+// scripts/ipc-protocol.js): POST ipc://localhost/<encodeURIComponent(cmd)>
+// with these headers; the invoke key is a guess (the Worker has no way to
+// learn the real one).
+const gsm14RealInit = (): RequestInit => ({
+  method: "POST",
+  body: "{}",
+  headers: {
+    "Content-Type": "application/json",
+    "Tauri-Callback": "12345",
+    "Tauri-Error": "12346",
+    "Tauri-Invoke-Key": "gsm14-guessed-key",
+  },
+});
+
+function gsm14Describe(caught: unknown): string {
+  if (caught instanceof Error) return `error ${caught.name}: ${caught.message}`.slice(0, 200);
+  return `error ${String(caught)}`.slice(0, 200);
+}
+
+function gsm14Timeout<T>(promise: Promise<T>): Promise<T> {
+  return Promise.race([
+    promise,
+    new Promise<T>((_, reject) => setTimeout(() => reject(new Error("timeout (no answer in 4 s)")), GSM14_TIMEOUT_MS)),
+  ]);
+}
+
+async function gsm14Fetch(fn: unknown, url: string, init?: RequestInit): Promise<string> {
+  if (typeof fn !== "function") return `absent (${typeof fn})`;
+  try {
+    const response = (await gsm14Timeout((fn as typeof fetch).call(self, url, init))) as Response;
+    let body = "";
+    try {
+      body = (await gsm14Timeout(response.text())).slice(0, 80);
+    } catch (caught) {
+      body = gsm14Describe(caught);
+    }
+    return `OK status=${response.status} tauri-response=${response.headers.get("Tauri-Response")} body=${JSON.stringify(body)}`;
+  } catch (caught) {
+    return gsm14Describe(caught);
+  }
+}
+
+function gsm14Xhr(ctor: unknown, method: string, url: string): Promise<string> {
+  if (typeof ctor !== "function") return Promise.resolve(`absent (${typeof ctor})`);
+  return new Promise((resolve) => {
+    try {
+      const xhr = new (ctor as typeof XMLHttpRequest)();
+      const timer = setTimeout(() => resolve("timeout (no answer in 4 s)"), GSM14_TIMEOUT_MS);
+      xhr.onload = () => { clearTimeout(timer); resolve(`OK status=${xhr.status} body=${JSON.stringify(String(xhr.responseText).slice(0, 80))}`); };
+      xhr.onerror = () => { clearTimeout(timer); resolve(`error (onerror, status=${xhr.status})`); };
+      xhr.open(method, url);
+      xhr.send(method === "POST" ? "{}" : null);
+    } catch (caught) {
+      resolve(gsm14Describe(caught));
+    }
+  });
+}
+
+function gsm14Ws(ctor: unknown, url: string): Promise<string> {
+  if (typeof ctor !== "function") return Promise.resolve(`absent (${typeof ctor})`);
+  return new Promise((resolve) => {
+    try {
+      const socket = new (ctor as typeof WebSocket)(url);
+      const timer = setTimeout(() => { try { socket.close(); } catch { /* */ } resolve("timeout (no answer in 4 s)"); }, GSM14_TIMEOUT_MS);
+      socket.onopen = () => { clearTimeout(timer); socket.close(); resolve("OK (open)"); };
+      socket.onerror = () => { clearTimeout(timer); resolve("error (onerror)"); };
+    } catch (caught) {
+      resolve(gsm14Describe(caught));
+    }
+  });
+}
+
+// The nested context's code: fresh globals, so its own fetch/XHR are intact.
+const GSM14_NESTED_SOURCE = `
+const urls = ${JSON.stringify(GSM14_IPC_URLS.map((item) => ({ ...item, url: item.url.replace("gsm14=W", "gsm14=N") })))};
+const describe = (e) => (e && e.name ? "error " + e.name + ": " + e.message : "error " + String(e)).slice(0, 200);
+const timeout = (p) => Promise.race([p, new Promise((_, r) => setTimeout(() => r(new Error("timeout (no answer in 4 s)")), 4000))]);
+const realInit = () => ({ method: "POST", body: "{}", headers: { "Content-Type": "application/json", "Tauri-Callback": "12345", "Tauri-Error": "12346", "Tauri-Invoke-Key": "gsm14-guessed-key" } });
+async function f(url, init) {
+  if (typeof fetch !== "function") return "absent (" + typeof fetch + ")";
+  try {
+    const r = await timeout(fetch(url, init));
+    let b = ""; try { b = (await timeout(r.text())).slice(0, 80); } catch (e) { b = describe(e); }
+    return "OK status=" + r.status + " tauri-response=" + r.headers.get("Tauri-Response") + " body=" + JSON.stringify(b);
+  } catch (e) { return describe(e); }
+}
+(async () => {
+  const lines = [];
+  lines.push("nested.typeof fetch=" + typeof fetch + " XMLHttpRequest=" + typeof XMLHttpRequest + " WebSocket=" + typeof WebSocket);
+  for (const p of ["__TAURI_INTERNALS__", "__TAURI__", "ipc", "webkit"]) lines.push("nested.global " + p + ": " + (self[p] !== undefined ? "PRESENT" : "absent"));
+  for (const { label, url } of urls) {
+    lines.push("nested.fetch GET " + label + ": " + await f(url));
+    lines.push("nested.fetch POST " + label + ": " + await f(url, realInit()));
+  }
+  postMessage(lines);
+})();
+`;
+
+async function gsm14NestedWorker(): Promise<string[]> {
+  const ctor = (self as unknown as { Worker?: unknown }).Worker;
+  if (typeof ctor !== "function") return [`nested blob Worker: absent (${typeof ctor})`];
+  let url = "";
+  try {
+    url = URL.createObjectURL(new Blob([GSM14_NESTED_SOURCE], { type: "text/javascript" }));
+  } catch (caught) {
+    return [`nested blob Worker: blob URL ${gsm14Describe(caught)}`];
+  }
+  return new Promise((resolve) => {
+    try {
+      const nested = new (ctor as typeof Worker)(url);
+      const timer = setTimeout(() => { nested.terminate(); resolve(["nested blob Worker: timeout (no lines in 30 s)"]); }, 30_000);
+      nested.onmessage = (event: MessageEvent<string[]>) => { clearTimeout(timer); nested.terminate(); resolve(["nested blob Worker: started", ...event.data]); };
+      nested.onerror = (event: ErrorEvent) => { clearTimeout(timer); resolve([`nested blob Worker: error event (${event.message || "no message"})`]); };
+    } catch (caught) {
+      resolve([`nested blob Worker: ${gsm14Describe(caught)}`]);
+    }
+  });
+}
+
+async function gsm14Probe(): Promise<string[]> {
+  const lines: string[] = [];
+  try {
+    await host();
+    lines.push("startup: engine verified and instantiated; globals deleted");
+  } catch (caught) {
+    lines.push(`startup: ${gsm14Describe(caught)}`);
+  }
+  const g = self as unknown as Record<string, unknown>;
+  const proto = Object.getPrototypeOf(self) as Record<string, unknown> | null;
+  const wgs = (g.WorkerGlobalScope as { prototype?: Record<string, unknown> } | undefined)?.prototype;
+  const dwgs = (g.DedicatedWorkerGlobalScope as { prototype?: Record<string, unknown> } | undefined)?.prototype;
+  lines.push(`context: location.origin=${self.location.origin} isSecureContext=${String(self.isSecureContext)}`);
+  // Every surviving reference to fetch, walking the whole prototype chain too.
+  const refs: Array<[string, unknown]> = [
+    ["self.fetch", g.fetch],
+    ["globalThis.fetch", (globalThis as unknown as Record<string, unknown>).fetch],
+    ["Object.getPrototypeOf(self).fetch", proto?.fetch],
+    ["WorkerGlobalScope.prototype.fetch", wgs?.fetch],
+    ["DedicatedWorkerGlobalScope.prototype.fetch", dwgs?.fetch],
+  ];
+  let level: object | null = proto;
+  for (let depth = 1; level && depth < 8; depth += 1, level = Object.getPrototypeOf(level)) {
+    const descriptor = Object.getOwnPropertyDescriptor(level, "fetch");
+    if (descriptor) refs.push([`prototype chain depth ${depth} (${level.constructor?.name}).fetch`, descriptor.value]);
+  }
+  for (const [label, fn] of refs) {
+    for (const { label: target, url } of GSM14_IPC_URLS) {
+      lines.push(`fetch GET via ${label} -> ${target}: ${await gsm14Fetch(fn, url)}`);
+      lines.push(`fetch POST(real invoke shape) via ${label} -> ${target}: ${await gsm14Fetch(fn, url, gsm14RealInit())}`);
+    }
+  }
+  for (const [label, ctor] of [["self.XMLHttpRequest", g.XMLHttpRequest], ["globalThis.XMLHttpRequest", (globalThis as unknown as Record<string, unknown>).XMLHttpRequest]] as const) {
+    for (const { label: target, url } of GSM14_IPC_URLS) {
+      lines.push(`XMLHttpRequest GET via ${label} -> ${target}: ${await gsm14Xhr(ctor, "GET", url)}`);
+      lines.push(`XMLHttpRequest POST via ${label} -> ${target}: ${await gsm14Xhr(ctor, "POST", url)}`);
+    }
+  }
+  lines.push(`WebSocket ws://ipc.localhost via self.WebSocket: ${await gsm14Ws(g.WebSocket, "ws://ipc.localhost/?gsm14=W")}`);
+  lines.push(`WebSocket ws://ipc.localhost via globalThis.WebSocket: ${await gsm14Ws((globalThis as unknown as Record<string, unknown>).WebSocket, "ws://ipc.localhost/?gsm14=W")}`);
+  const presence = (value: unknown) => (value !== undefined && value !== null ? `PRESENT (${typeof value})` : "absent");
+  lines.push(`self.__TAURI_INTERNALS__: ${presence(g.__TAURI_INTERNALS__)}`);
+  lines.push(`self.__TAURI__: ${presence(g.__TAURI__)}`);
+  lines.push(`self.__TAURI_INVOKE_KEY__: ${presence(g.__TAURI_INVOKE_KEY__)}`);
+  lines.push(`self.ipc: ${presence(g.ipc)}`);
+  lines.push(`self.webkit: ${presence(g.webkit)}`);
+  lines.push(`self.webkit?.messageHandlers: ${presence((g.webkit as { messageHandlers?: unknown } | undefined)?.messageHandlers)}`);
+  lines.push(`self.chrome?.webview: ${presence((g.chrome as { webview?: unknown } | undefined)?.webview)}`);
+  lines.push(`self.window / document / parent / top: ${presence(g.window)} / ${presence(g.document)} / ${presence(g.parent)} / ${presence(g.top)}`);
+  lines.push(`other: EventSource=${presence(g.EventSource)} importScripts=${presence(g.importScripts)} WorkerGlobalScope.prototype.importScripts=${presence(wgs?.importScripts)} Worker=${presence(g.Worker)} SharedWorker=${presence(g.SharedWorker)} WebTransport=${presence(g.WebTransport)} navigator.serviceWorker=${presence((self.navigator as unknown as Record<string, unknown>).serviceWorker)}`);
+  // importScripts of a blob: script that calls fetch (runs in this same, stripped scope).
+  for (const [label, fn] of [["self.importScripts", g.importScripts], ["WorkerGlobalScope.prototype.importScripts", wgs?.importScripts]] as const) {
+    if (typeof fn !== "function") {
+      lines.push(`importScripts(blob:) via ${label}: absent (${typeof fn})`);
+      continue;
+    }
+    try {
+      const blobUrl = URL.createObjectURL(new Blob([`self.__gsm14 = typeof fetch === "function" ? fetch("ipc://localhost/plugin:app|ping?gsm14=I").then(r => "OK status=" + r.status, e => "error " + e.name + ": " + e.message) : Promise.resolve("fetch absent in importScripts scope (" + typeof fetch + ")");`], { type: "text/javascript" }));
+      (fn as (url: string) => void).call(self, blobUrl);
+      lines.push(`importScripts(blob:) via ${label}: loaded; ${await gsm14Timeout(g.__gsm14 as Promise<string>)}`);
+    } catch (caught) {
+      lines.push(`importScripts(blob:) via ${label}: ${gsm14Describe(caught)}`);
+    }
+  }
+  // Module import of the IPC URL (a GET through the script loader, not fetch).
+  for (const { label, url } of GSM14_IPC_URLS) {
+    try {
+      await gsm14Timeout(import(/* @vite-ignore */ url.replace("gsm14=W", "gsm14=M")));
+      lines.push(`dynamic import() -> ${label}: OK (module loaded)`);
+    } catch (caught) {
+      lines.push(`dynamic import() -> ${label}: ${gsm14Describe(caught)}`);
+    }
+  }
+  lines.push(...(await gsm14NestedWorker()));
+  return lines;
+}
+
 scope.onmessage = (event) => {
+  const data = event.data as { gsm14?: unknown } | null;
+  if (import.meta.env.VITE_GSM14_PROBE === "1" && data && typeof data === "object" && data.gsm14 === "probe") {
+    void gsm14Probe().then((lines) => (scope.postMessage as (message: unknown) => void)({ gsm14: "result", lines }));
+    return;
+  }
   void answerRequest(host, event.data).then((reply) => scope.postMessage(reply));
 };
```

### Main-window harness (`apps/learnloop-tauri/src/gsm14/gsm14Harness.ts`, new)

```ts
// ---- G-SM14 PROBE HARNESS (scratch branch probe/g-sm14, never landed) ----
// Built only with VITE_GSM14_PROBE=1. In the MAIN window: create the real
// sketch Worker exactly as production does (sketchWorkerClient's `?worker`
// import), drive one real `load` so its normal start-up runs, send the probe,
// then report every line through a temporary Rust command from the main
// window (never from the Worker). Two labelled CONTROLS show that the Rust
// logging would see a request that does reach IPC.
import { invoke } from "@tauri-apps/api/core";
import { createSketchWorker } from "../screens/reader/figures/sketch/sketchWorkerClient";

const describe = (caught: unknown) =>
  (caught instanceof Error ? `error ${caught.name}: ${caught.message}` : `error ${String(caught)}`).slice(0, 200);

async function controlMainWindowFetch(): Promise<string> {
  // A request from the main document with no invoke key: Tauri answers 500
  // "missing Tauri-Invoke-Key header" from its IPC protocol handler.
  try {
    const response = await fetch("ipc://localhost/plugin%3Aapp%7Cversion?gsm14=C1", { method: "POST", body: "{}", headers: { "Content-Type": "application/json" } });
    return `OK status=${response.status} body=${JSON.stringify((await response.text()).slice(0, 80))}`;
  } catch (caught) {
    return describe(caught);
  }
}

function controlFreshWorker(): Promise<string> {
  // A fresh blob Worker from the main window, NOT the sketch Worker: its
  // globals are intact. Context only (is the ipc: scheme reachable from a
  // worker at all in this webview?); not part of the verdict.
  const source = `
    (async () => {
      const out = [];
      for (const [label, init] of [["GET", undefined], ["POST", { method: "POST", body: "{}", headers: { "Content-Type": "application/json", "Tauri-Callback": "1", "Tauri-Error": "2", "Tauri-Invoke-Key": "gsm14-guessed-key" } }]]) {
        try {
          const r = await Promise.race([fetch("ipc://localhost/plugin%3Aapp%7Cversion?gsm14=C2", init), new Promise((_, j) => setTimeout(() => j(new Error("timeout (no answer in 4 s)")), 4000))]);
          out.push(label + " OK status=" + r.status + " body=" + JSON.stringify((await r.text()).slice(0, 80)));
        } catch (e) { out.push(label + " error " + e.name + ": " + e.message); }
      }
      postMessage(out.join(" | "));
    })();`;
  return new Promise((resolve) => {
    try {
      const worker = new Worker(URL.createObjectURL(new Blob([source], { type: "text/javascript" })));
      const timer = setTimeout(() => { worker.terminate(); resolve("timeout (30 s)"); }, 30_000);
      worker.onmessage = (event: MessageEvent<string>) => { clearTimeout(timer); worker.terminate(); resolve(event.data); };
      worker.onerror = (event) => { clearTimeout(timer); resolve(`error event (${event.message || "no message"})`); };
    } catch (caught) {
      resolve(describe(caught));
    }
  });
}

function runSketchWorkerProbe(): Promise<string[]> {
  return new Promise((resolve) => {
    const worker = createSketchWorker();
    const port = worker as unknown as { postMessage(message: unknown): void; onmessage: ((event: { data: unknown }) => void) | null; terminate(): void };
    const lines: string[] = [];
    const timer = setTimeout(() => { worker.terminate(); resolve([...lines, "sketch Worker probe: TIMEOUT (240 s)"]); }, 240_000);
    port.onmessage = (event) => {
      const data = event.data as { id?: number; gsm14?: string; lines?: string[] } | null;
      if (data && data.id === 1) {
        lines.push(`real load op reply: ${JSON.stringify(data).slice(0, 160)}`);
        port.postMessage({ gsm14: "probe" });
        return;
      }
      if (data && data.gsm14 === "result") {
        clearTimeout(timer);
        worker.terminate();
        resolve([...lines, ...(data.lines ?? [])]);
      }
    };
    // A real protocol request first, so the Worker's normal start-up runs as in production.
    port.postMessage({ id: 1, op: "load", args: ["function init(p){return {}} function step(s,p,dt){return s} function view(s,p){return {elements:[]}} function probes(s,p){return {}}"] });
  });
}

export async function runGsm14Probe(): Promise<void> {
  const lines: string[] = [];
  lines.push(`main: location.origin=${window.location.origin} userAgent=${navigator.userAgent}`);
  lines.push(`main: __TAURI_INTERNALS__=${typeof (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__}`);
  lines.push(`CONTROL C1 (main-window fetch, no key): ${await controlMainWindowFetch()}`);
  lines.push(`CONTROL C2 (fresh blob Worker from main window, not the sketch Worker): ${await controlFreshWorker()}`);
  try {
    for (const line of await runSketchWorkerProbe()) lines.push(`WORKER ${line}`);
  } catch (caught) {
    lines.push(`WORKER harness ${describe(caught)}`);
  }
  await invoke("gsm14_report", { lines });
}
```

### Entry hook, report command and Cargo patch (`main.tsx`, `src-tauri/src/main.rs`, `src-tauri/Cargo.toml`)

```diff
diff --git a/apps/learnloop-tauri/src-tauri/Cargo.toml b/apps/learnloop-tauri/src-tauri/Cargo.toml
index ed106b4958..cc7db7ed85 100644
--- a/apps/learnloop-tauri/src-tauri/Cargo.toml
+++ b/apps/learnloop-tauri/src-tauri/Cargo.toml
@@ -19,3 +19,8 @@ thiserror = "1"
 
 [features]
 custom-protocol = ["tauri/custom-protocol"]
+
+# G-SM14 PROBE (scratch branch probe/g-sm14, never landed): tauri 2.11.2 with
+# eprintln! at the ipc: protocol handler, the postMessage handler and on_message.
+[patch.crates-io]
+tauri = { path = "/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/a22010cc-5149-4947-a2b8-247f18b8f1a0/scratchpad/gsm14/tauri-2.11.2" }
diff --git a/apps/learnloop-tauri/src-tauri/src/main.rs b/apps/learnloop-tauri/src-tauri/src/main.rs
index 946806366d..e2aec1d45e 100644
--- a/apps/learnloop-tauri/src-tauri/src/main.rs
+++ b/apps/learnloop-tauri/src-tauri/src/main.rs
@@ -185,6 +185,20 @@ fn debug_zoom_enabled() -> bool {
     })
 }
 
+// G-SM14 PROBE (scratch branch probe/g-sm14, never landed): the MAIN
+// window reports the probe's lines here; they go to stderr, then the app exits.
+#[tauri::command]
+fn gsm14_report(app: tauri::AppHandle, lines: Vec<String>) {
+    for line in &lines {
+        eprintln!("GSM14-RESULT {line}");
+    }
+    eprintln!("GSM14-RESULT-END ({} lines)", lines.len());
+    std::thread::spawn(move || {
+        std::thread::sleep(std::time::Duration::from_millis(1500));
+        app.exit(0);
+    });
+}
+
 fn main() {
     // WebKitGTK's DMA-BUF renderer intermittently drops composited tiles on
     // Linux (Intel/Mesa): toggling display on the reader rail's tab panels
@@ -701,7 +715,8 @@ fn main() {
             reader_pause_arc,
             reader_shrink_envelope,
             reader_prime,
-            reader_restore
+            reader_restore,
+            gsm14_report
         ])
         .run(tauri::generate_context!())
         .expect("error while running LearnLoop");
diff --git a/apps/learnloop-tauri/src/main.tsx b/apps/learnloop-tauri/src/main.tsx
index 9d56cac617..401283fe47 100644
--- a/apps/learnloop-tauri/src/main.tsx
+++ b/apps/learnloop-tauri/src/main.tsx
@@ -17,3 +17,10 @@ ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
   </React.StrictMode>
 );
 
+
+// G-SM14 probe (scratch branch probe/g-sm14, never landed).
+if (import.meta.env.VITE_GSM14_PROBE === "1") {
+  setTimeout(() => {
+    void import("./gsm14/gsm14Harness").then((harness) => harness.runGsm14Probe());
+  }, 4000);
+}
```

### Logging added to the scratch copy of tauri 2.11.2

```diff
--- a/tauri-2.11.2/src/ipc/protocol.rs
+++ b/tauri-2.11.2/src/ipc/protocol.rs
@@ -37,6 +37,18 @@
 
 pub fn get<R: Runtime>(manager: Arc<AppManager<R>>) -> UriSchemeProtocolHandler {
   Box::new(move |label, request, responder| {
+    // G-SM14 PROBE (scratch copy of tauri 2.11.2, never landed): log every
+    // request that reaches the ipc: custom-protocol handler.
+    eprintln!(
+      "GSM14-RUST ipc-protocol label={} method={} uri={} origin={:?} referer={:?} has_invoke_key_header={} body_len={}",
+      label,
+      request.method(),
+      request.uri(),
+      request.headers().get("Origin"),
+      request.headers().get("Referer"),
+      request.headers().contains_key("Tauri-Invoke-Key"),
+      request.body().len()
+    );
     #[cfg(feature = "tracing")]
     let span = tracing::trace_span!(
       "ipc::request",
@@ -183,6 +195,16 @@
 }
 
 fn handle_ipc_message<R: Runtime>(request: Request<String>, manager: &AppManager<R>, label: &str) {
+  // G-SM14 PROBE: log every message that reaches the postMessage (WebKit
+  // script message handler) IPC path. The body is not printed (it carries
+  // the real invoke key for the app's own calls).
+  eprintln!(
+    "GSM14-RUST ipc-postmessage label={} uri={} body_len={} body_has_gsm14_marker={}",
+    label,
+    request.uri(),
+    request.body().len(),
+    request.body().contains("gsm14")
+  );
   if let Some(webview) = manager.get_webview(label) {
     #[cfg(feature = "tracing")]
     let _span = tracing::trace_span!(
--- a/tauri-2.11.2/src/webview/mod.rs
+++ b/tauri-2.11.2/src/webview/mod.rs
@@ -1740,6 +1740,8 @@
 
   /// Handles this window receiving an [`InvokeRequest`].
   pub fn on_message(self, request: InvokeRequest, responder: Box<OwnedInvokeResponder<R>>) {
+    // G-SM14 PROBE: every request that reached the invoke dispatcher (before the key check).
+    eprintln!("GSM14-RUST on_message cmd={} url={}", request.cmd, request.url);
     let manager = self.manager_owned();
     let is_local = self.is_local_url(&request.url);
 
@@ -1754,8 +1756,11 @@
 
       #[cfg(not(feature = "tracing"))]
       eprintln!(
-        "__TAURI_INVOKE_KEY__ expected {expected} but received {}",
-        request.invoke_key
+        "GSM14-RUST on_message: __TAURI_INVOKE_KEY__ mismatch (expected <redacted, {} chars>) received {:?} cmd={} url={}",
+        expected.len(),
+        request.invoke_key,
+        request.cmd,
+        request.url
       );
 
       return;
```

## Rerun after the compartment (2026-11-01)

- **Date:** 2026-11-01, run 14:53:42–14:53:54 -05:00, one window, about 12 s. The app exited on its own (exit 0);
  no LearnLoop or sidecar process remained afterwards.
- **Permission:** the owner's 2026-11-01 permission for one real desktop window for this animation sandbox check,
  with a throwaway synthetic vault. No owner vault, retired vault or book was opened or listed.
- **What changed since the first run** (stage `reader/rw5d-p2-sketch-compartment`, record
  `docs/reviews/reader-rw5d-p2-sketch-compartment.md`): the sketch Worker is no longer loaded by URL. The Reader makes
  a hidden `<iframe sandbox="allow-scripts">` (no `allow-same-origin`: an opaque origin) on `sketch-frame.html`, whose
  own CSP is `default-src 'none'; script-src '<its one script's sha256>' 'wasm-unsafe-eval'; worker-src blob:;
  child-src blob:; connect-src 'none'; …` (enforced together with the app CSP header Tauri adds to every `.html`
  asset). The frame's script starts the Worker **from a blob**, so the Worker inherits the frame's policy; the engine's
  bytes and the bundled Worker source travel over a private MessageChannel; the Reader and the Worker talk over a
  second one in the four-operation protocol. The shell also unregisters WebKit's `ipc` script-message handler on Linux
  (the postMessage IPC path, Tauri's fallback there) and refuses LearnLoop commands whose Origin is `null` or whose
  Referer is a worker, blob, srcdoc or frame document (`src-tauri/src/frame_guard.rs`).
- **Verdict: PASS.** No request from the frame, its blob Workers or any nested Worker reached a Tauri handler: there
  is **no** `ipc-protocol`, `ipc-postmessage` or `on_message` line for any probe-marked request (`gsm14=F`, `B`,
  `BN`, `W`, `FF`, `FN`), none with Origin `null`, and none with a Referer other than the app's own document
  (`tauri://localhost`, 23 of 23 `ipc-protocol` lines). Every attempt failed in the page (each line below). The only
  probe-marked line in the Rust log is the main-window control `C1`, which shows the logging was live.
  `figures.sketch_enabled` therefore defaults **on** (Q5's built default), in the same stage.

### How it was run

The same method as the first run, with the probe moved inside the compartment:

- **Build: production-equivalent, not `tauri dev`.** `npm run frontend:build`, then
  `cargo build --offline --features custom-protocol` (debug binary, embedded assets, the page at `tauri://localhost`
  with the app CSP header). Both in `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`. No dev server,
  nothing bound a port.
- **Scratch branch `probe/g-sm14-compartment`** (commit `2244360639`, from the stage tip `d2afa824ce`, **never
  landed**) holds all probe code (diff below): `src/gsm14/attempts.js` (one self-contained function that tries every
  path from whatever context calls it), the same function inlined into `sketch-frame.html`'s script (its CSP hash
  recomputed for the probe build), a listener in the real sketch Worker, a main-window harness, a temporary
  `gsm14_report` command, and the Cargo patch to the same logging copy of tauri 2.11.2 as the first run (diff in "Logging
  added to the scratch copy of tauri 2.11.2" above, unchanged).
- **Contexts probed** (markers in `?gsm14=`):
  - `F`: the frame document itself (opaque origin, inside the frame's CSP);
  - `B`: a **fresh** blob Worker the frame creates, never stripped (so only the inherited CSP stands between it and
    the network), and `BN`, a Worker nested inside it;
  - `W`: the real sketch Worker, after its normal start-up through the production path (pinned engine verified and
    instantiated, then network, import and Worker-making globals removed along the whole prototype chain), and its
    nested Worker (it can no longer make one);
  - `FF`/`FN`: the frame submitting a form to `ipc://` and navigating itself to `ipc://` (last, after the results
    were sent).
  Each context tried `fetch` (own, `globalThis` and every prototype level that has it) GET and the real invoke POST
  shape against `ipc://localhost` (app, `load_vault`, `plugin:opener|open_url`, `plugin:dialog|open`),
  `http://ipc.localhost`, `llpdf://` and a `tauri://` asset; `XMLHttpRequest`; `WebSocket`; `EventSource`;
  `navigator.sendBeacon`; `import()`; `importScripts` (own and prototype, `ipc://` and `blob:`); `new Worker(ipc://)`;
  and the frame also `img`, `script`, `link` and `iframe` elements at `ipc://`, an `about:blank` child frame,
  `parent`/`top` access, `window.open` and `localStorage`. Presence of `__TAURI_INTERNALS__`, `__TAURI__`,
  `__TAURI_INVOKE_KEY__`, `isTauri`, `ipc`, `webkit`, `webkit.messageHandlers(.ipc)` and `chrome.webview` was checked
  everywhere; had `messageHandlers.ipc` been present, the probe would have posted to it.
- **Before the probe,** the harness ran the three verified parity-corpus sketches through the production compartment
  (`createSketchWorker` → `portRunner` → `withWatchdog`, as `SketchFigure` does), reading every scheduled step and
  comparing every digest verification recorded, with timings.
- **Environment** (one launch, `env -i`, inside a 5G scope, `timeout 540` as a backstop): as in the first run, with
  `<scratch>` = `/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/a22010cc-5149-4947-a2b8-247f18b8f1a0/scratchpad/sketch-compartment/gsm14r`:

```
PATH=/usr/bin:/bin
HOME=<scratch>/home            (empty)
XDG_CONFIG_HOME=<scratch>/xdg/config  XDG_DATA_HOME=<scratch>/xdg/data  XDG_CACHE_HOME=<scratch>/xdg/cache
TMPDIR=<scratch>/tmp
WAYLAND_DISPLAY=wayland-1  DISPLAY=:0  XDG_RUNTIME_DIR=/run/user/1000
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus  XDG_SESSION_TYPE=wayland
LEARNLOOP_VAULT=<scratch>/vault        (fresh: `learnloop init` under env -i, empty HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR)
LEARNLOOP_CONFIG_DIR=<scratch>/config  (empty)
CODEX_HOME=<scratch>/codex             (empty: no ChatGPT-plan sign-in)
LEARNLOOP_AI_PROVIDER=gsm14-none       (no such profile)
LEARNLOOP_PYTHON=<worktree>/.venv/bin/python
RUST_LOG=debug  LEARNLOOP_SIDECAR_DEBUG_LOG=<scratch>/sidecar-run1.log
```

  The vault has **0** `model_call_receipts` rows (no model call); the sidecar debug log stayed empty; `HOME`,
  `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` stayed empty. Versions are the first run's (same Tauri, Wry, WebKitGTK
  2.54.1, user agent).

### Results (every line, as reported)

```
main: location.origin=tauri://localhost userAgent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/60.5 Safari/605.1.15
main: __TAURI_INTERNALS__=object webkit.messageHandlers.ipc=undefined
REAL random walk: digests matched 27/27; first load (frame + Worker start-up + engine compile + load) 31.0 ms; other calls 606, max 3.0 ms; watchdog 480 ms; paused=false
REAL marks when read: digests matched 9/9; first load (frame + Worker start-up + engine compile + load) 18.0 ms; other calls 202, max 2.0 ms; watchdog 480 ms; paused=false
REAL signed zero: digests matched 19/19; first load (frame + Worker start-up + engine compile + load) 17.0 ms; other calls 404, max 2.0 ms; watchdog 480 ms; paused=false
REAL compartments left in the page after dispose: 0
PROBE compartment real start-up: load+init+read OK (probes {"s":1})
FRAME context: location=tauri://localhost/sketch-frame.html origin=null isSecureContext=true referrer=""
FRAME global __TAURI_INTERNALS__: absent
FRAME global __TAURI__: absent
FRAME global __TAURI_INVOKE_KEY__: absent
FRAME global isTauri: absent
FRAME global ipc: absent
FRAME global webkit: absent
FRAME global chrome: absent
FRAME webkit.messageHandlers: absent ; .ipc: absent
FRAME fetch GET via self.fetch -> ipc-scheme: error TypeError: Load failed
FRAME fetch POST(real shape) via self.fetch -> ipc-scheme: error TypeError: Load failed
FRAME fetch GET via self.fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRAME fetch POST(real shape) via self.fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRAME fetch GET via self.fetch -> ipc-load_vault: error TypeError: Load failed
FRAME fetch POST(real shape) via self.fetch -> ipc-load_vault: error TypeError: Load failed
FRAME fetch GET via self.fetch -> ipc-opener: error TypeError: Load failed
FRAME fetch POST(real shape) via self.fetch -> ipc-opener: error TypeError: Load failed
FRAME fetch GET via self.fetch -> ipc-dialog: error TypeError: Load failed
FRAME fetch POST(real shape) via self.fetch -> ipc-dialog: error TypeError: Load failed
FRAME fetch GET via self.fetch -> http-ipc-localhost: error TypeError: Load failed
FRAME fetch POST(real shape) via self.fetch -> http-ipc-localhost: error TypeError: Load failed
FRAME fetch GET via self.fetch -> llpdf: error TypeError: Load failed
FRAME fetch POST(real shape) via self.fetch -> llpdf: error TypeError: Load failed
FRAME fetch GET via self.fetch -> tauri-asset: error TypeError: Load failed
FRAME fetch POST(real shape) via self.fetch -> tauri-asset: error TypeError: Load failed
FRAME fetch GET via globalThis.fetch -> ipc-scheme: error TypeError: Load failed
FRAME fetch POST(real shape) via globalThis.fetch -> ipc-scheme: error TypeError: Load failed
FRAME fetch GET via globalThis.fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRAME fetch POST(real shape) via globalThis.fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRAME fetch GET via globalThis.fetch -> ipc-load_vault: error TypeError: Load failed
FRAME fetch POST(real shape) via globalThis.fetch -> ipc-load_vault: error TypeError: Load failed
FRAME fetch GET via globalThis.fetch -> ipc-opener: error TypeError: Load failed
FRAME fetch POST(real shape) via globalThis.fetch -> ipc-opener: error TypeError: Load failed
FRAME fetch GET via globalThis.fetch -> ipc-dialog: error TypeError: Load failed
FRAME fetch POST(real shape) via globalThis.fetch -> ipc-dialog: error TypeError: Load failed
FRAME fetch GET via globalThis.fetch -> http-ipc-localhost: error TypeError: Load failed
FRAME fetch POST(real shape) via globalThis.fetch -> http-ipc-localhost: error TypeError: Load failed
FRAME fetch GET via globalThis.fetch -> llpdf: error TypeError: Load failed
FRAME fetch POST(real shape) via globalThis.fetch -> llpdf: error TypeError: Load failed
FRAME fetch GET via globalThis.fetch -> tauri-asset: error TypeError: Load failed
FRAME fetch POST(real shape) via globalThis.fetch -> tauri-asset: error TypeError: Load failed
FRAME XMLHttpRequest GET -> ipc-scheme: error (onerror, status=0)
FRAME XMLHttpRequest POST -> ipc-scheme: error (onerror, status=0)
FRAME XMLHttpRequest GET -> ipc-scheme-real-shape: error (onerror, status=0)
FRAME XMLHttpRequest POST -> ipc-scheme-real-shape: error (onerror, status=0)
FRAME XMLHttpRequest GET -> ipc-load_vault: error (onerror, status=0)
FRAME XMLHttpRequest POST -> ipc-load_vault: error (onerror, status=0)
FRAME WebSocket ws://ipc.localhost: error SecurityError: The operation is insecure.
FRAME EventSource ipc://: error SecurityError: The operation is insecure.
FRAME navigator.sendBeacon ipc://: error TypeError: Beacons can only be sent over HTTP(S)
FRAME dynamic import() -> ipc-scheme: error TypeError: Importing a module script failed.
FRAME dynamic import() -> ipc-scheme-real-shape: error TypeError: Importing a module script failed.
FRAME img src=ipc://: error event
FRAME script src=ipc://: error event
FRAME link stylesheet ipc://: error event
FRAME iframe src=ipc://: LOADED
FRAME child about:blank iframe: error SecurityError: Sandbox access violation: Blocked a frame at "tauri://localhost" from accessing a cross-origin frame.  Both frames are sandboxed and lack the "allow-same-origin" flag.
FRAME parent.document: error SecurityError: Sandbox access violation: Blocked a frame at "tauri://localhost" from accessing a cross-origin frame.  The frame requesting access is sandboxed and lacks the "allow-same-origin" f
FRAME parent.__TAURI_INTERNALS__: error SecurityError: Sandbox access violation: Blocked a frame at "tauri://localhost" from accessing a cross-origin frame.  The frame requesting access is sandboxed and lacks the "allow-same-origin" f
FRAME top.location.href: error SecurityError: Sandbox access violation: Blocked a frame at "tauri://localhost" from accessing a cross-origin frame.  The frame requesting access is sandboxed and lacks the "allow-same-origin" f
FRAME window.open(ipc://): null (refused)
FRAME localStorage: error SecurityError: The operation is insecure.
FRAME new Worker(ipc://): constructed (object)
FRESH-BLOB-WORKER started
FRESH-BLOB-WORKER context: location=blob:null/fc1a0c5b-f66a-43c8-b40a-4bfbe3496f35 origin=null isSecureContext=true
FRESH-BLOB-WORKER global __TAURI_INTERNALS__: absent
FRESH-BLOB-WORKER global __TAURI__: absent
FRESH-BLOB-WORKER global __TAURI_INVOKE_KEY__: absent
FRESH-BLOB-WORKER global isTauri: absent
FRESH-BLOB-WORKER global ipc: absent
FRESH-BLOB-WORKER global webkit: absent
FRESH-BLOB-WORKER global chrome: absent
FRESH-BLOB-WORKER webkit.messageHandlers: absent ; .ipc: absent
FRESH-BLOB-WORKER fetch GET via self.fetch -> ipc-scheme: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via self.fetch -> ipc-scheme: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via self.fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via self.fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via self.fetch -> ipc-load_vault: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via self.fetch -> ipc-load_vault: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via self.fetch -> ipc-opener: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via self.fetch -> ipc-opener: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via self.fetch -> ipc-dialog: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via self.fetch -> ipc-dialog: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via self.fetch -> http-ipc-localhost: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via self.fetch -> http-ipc-localhost: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via self.fetch -> llpdf: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via self.fetch -> llpdf: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via self.fetch -> tauri-asset: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via self.fetch -> tauri-asset: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via globalThis.fetch -> ipc-scheme: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via globalThis.fetch -> ipc-scheme: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via globalThis.fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via globalThis.fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via globalThis.fetch -> ipc-load_vault: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via globalThis.fetch -> ipc-load_vault: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via globalThis.fetch -> ipc-opener: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via globalThis.fetch -> ipc-opener: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via globalThis.fetch -> ipc-dialog: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via globalThis.fetch -> ipc-dialog: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via globalThis.fetch -> http-ipc-localhost: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via globalThis.fetch -> http-ipc-localhost: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via globalThis.fetch -> llpdf: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via globalThis.fetch -> llpdf: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via globalThis.fetch -> tauri-asset: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via globalThis.fetch -> tauri-asset: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-scheme: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-scheme: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-load_vault: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-load_vault: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-opener: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-opener: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-dialog: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-dialog: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> http-ipc-localhost: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> http-ipc-localhost: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> llpdf: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> llpdf: error TypeError: Load failed
FRESH-BLOB-WORKER fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> tauri-asset: error TypeError: Load failed
FRESH-BLOB-WORKER fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> tauri-asset: error TypeError: Load failed
FRESH-BLOB-WORKER XMLHttpRequest GET -> ipc-scheme: error (onerror, status=0)
FRESH-BLOB-WORKER XMLHttpRequest POST -> ipc-scheme: error (onerror, status=0)
FRESH-BLOB-WORKER XMLHttpRequest GET -> ipc-scheme-real-shape: error (onerror, status=0)
FRESH-BLOB-WORKER XMLHttpRequest POST -> ipc-scheme-real-shape: error (onerror, status=0)
FRESH-BLOB-WORKER XMLHttpRequest GET -> ipc-load_vault: error (onerror, status=0)
FRESH-BLOB-WORKER XMLHttpRequest POST -> ipc-load_vault: error (onerror, status=0)
FRESH-BLOB-WORKER WebSocket ws://ipc.localhost: error SecurityError: The operation is insecure.
FRESH-BLOB-WORKER EventSource ipc://: error SecurityError: The operation is insecure.
FRESH-BLOB-WORKER navigator.sendBeacon: absent
FRESH-BLOB-WORKER dynamic import() -> ipc-scheme: error TypeError: Importing a module script failed.
FRESH-BLOB-WORKER dynamic import() -> ipc-scheme-real-shape: error TypeError: Importing a module script failed.
FRESH-BLOB-WORKER importScripts(ipc://) via self.importScripts: error NetworkError:  A network error occurred.
FRESH-BLOB-WORKER importScripts(blob:) via self.importScripts: error NetworkError:  A network error occurred.
FRESH-BLOB-WORKER importScripts(ipc://) via WorkerGlobalScope.prototype.importScripts: error NetworkError:  A network error occurred.
FRESH-BLOB-WORKER importScripts(blob:) via WorkerGlobalScope.prototype.importScripts: error NetworkError:  A network error occurred.
FRESH-BLOB-WORKER new Worker(ipc://): constructed (object)
FRESH-BLOB-WORKER nested blob Worker: started
FRESH-BLOB-WORKER nested: context: location=blob:null/b06b374a-5211-47cf-bff4-89e3a39a5f62 origin=null isSecureContext=true
FRESH-BLOB-WORKER nested: global __TAURI_INTERNALS__: absent
FRESH-BLOB-WORKER nested: global __TAURI__: absent
FRESH-BLOB-WORKER nested: global __TAURI_INVOKE_KEY__: absent
FRESH-BLOB-WORKER nested: global isTauri: absent
FRESH-BLOB-WORKER nested: global ipc: absent
FRESH-BLOB-WORKER nested: global webkit: absent
FRESH-BLOB-WORKER nested: global chrome: absent
FRESH-BLOB-WORKER nested: webkit.messageHandlers: absent ; .ipc: absent
FRESH-BLOB-WORKER nested: fetch GET via self.fetch -> ipc-scheme: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via self.fetch -> ipc-scheme: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via self.fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via self.fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via self.fetch -> ipc-load_vault: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via self.fetch -> ipc-load_vault: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via self.fetch -> ipc-opener: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via self.fetch -> ipc-opener: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via self.fetch -> ipc-dialog: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via self.fetch -> ipc-dialog: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via self.fetch -> http-ipc-localhost: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via self.fetch -> http-ipc-localhost: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via self.fetch -> llpdf: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via self.fetch -> llpdf: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via self.fetch -> tauri-asset: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via self.fetch -> tauri-asset: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via globalThis.fetch -> ipc-scheme: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via globalThis.fetch -> ipc-scheme: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via globalThis.fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via globalThis.fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via globalThis.fetch -> ipc-load_vault: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via globalThis.fetch -> ipc-load_vault: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via globalThis.fetch -> ipc-opener: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via globalThis.fetch -> ipc-opener: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via globalThis.fetch -> ipc-dialog: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via globalThis.fetch -> ipc-dialog: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via globalThis.fetch -> http-ipc-localhost: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via globalThis.fetch -> http-ipc-localhost: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via globalThis.fetch -> llpdf: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via globalThis.fetch -> llpdf: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via globalThis.fetch -> tauri-asset: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via globalThis.fetch -> tauri-asset: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-scheme: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-scheme: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-scheme-real-shape: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-load_vault: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-load_vault: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-opener: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-opener: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-dialog: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> ipc-dialog: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> http-ipc-localhost: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> http-ipc-localhost: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> llpdf: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> llpdf: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch GET via prototype depth 2 (WorkerGlobalScope).fetch -> tauri-asset: error TypeError: Load failed
FRESH-BLOB-WORKER nested: fetch POST(real shape) via prototype depth 2 (WorkerGlobalScope).fetch -> tauri-asset: error TypeError: Load failed
FRESH-BLOB-WORKER nested: XMLHttpRequest GET -> ipc-scheme: error (onerror, status=0)
FRESH-BLOB-WORKER nested: XMLHttpRequest POST -> ipc-scheme: error (onerror, status=0)
FRESH-BLOB-WORKER nested: XMLHttpRequest GET -> ipc-scheme-real-shape: error (onerror, status=0)
FRESH-BLOB-WORKER nested: XMLHttpRequest POST -> ipc-scheme-real-shape: error (onerror, status=0)
FRESH-BLOB-WORKER nested: XMLHttpRequest GET -> ipc-load_vault: error (onerror, status=0)
FRESH-BLOB-WORKER nested: XMLHttpRequest POST -> ipc-load_vault: error (onerror, status=0)
FRESH-BLOB-WORKER nested: WebSocket ws://ipc.localhost: error SecurityError: The operation is insecure.
FRESH-BLOB-WORKER nested: EventSource ipc://: error SecurityError: The operation is insecure.
FRESH-BLOB-WORKER nested: navigator.sendBeacon: absent
FRESH-BLOB-WORKER nested: dynamic import() -> ipc-scheme: error TypeError: Importing a module script failed.
FRESH-BLOB-WORKER nested: dynamic import() -> ipc-scheme-real-shape: error TypeError: Importing a module script failed.
FRESH-BLOB-WORKER nested: importScripts(ipc://) via self.importScripts: error NetworkError:  A network error occurred.
FRESH-BLOB-WORKER nested: importScripts(blob:) via self.importScripts: error NetworkError:  A network error occurred.
FRESH-BLOB-WORKER nested: importScripts(ipc://) via WorkerGlobalScope.prototype.importScripts: error NetworkError:  A network error occurred.
FRESH-BLOB-WORKER nested: importScripts(blob:) via WorkerGlobalScope.prototype.importScripts: error NetworkError:  A network error occurred.
FRESH-BLOB-WORKER nested: new Worker(ipc://): constructed (object)
SKETCH-WORKER context: location=blob:null/8ea8e22c-5292-4926-ae89-8466e32bb02b origin=null isSecureContext=true
SKETCH-WORKER global __TAURI_INTERNALS__: absent
SKETCH-WORKER global __TAURI__: absent
SKETCH-WORKER global __TAURI_INVOKE_KEY__: absent
SKETCH-WORKER global isTauri: absent
SKETCH-WORKER global ipc: absent
SKETCH-WORKER global webkit: absent
SKETCH-WORKER global chrome: absent
SKETCH-WORKER webkit.messageHandlers: absent ; .ipc: absent
SKETCH-WORKER fetch GET via self.fetch -> ipc-scheme: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via self.fetch -> ipc-scheme: absent (undefined)
SKETCH-WORKER fetch GET via self.fetch -> ipc-scheme-real-shape: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via self.fetch -> ipc-scheme-real-shape: absent (undefined)
SKETCH-WORKER fetch GET via self.fetch -> ipc-load_vault: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via self.fetch -> ipc-load_vault: absent (undefined)
SKETCH-WORKER fetch GET via self.fetch -> ipc-opener: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via self.fetch -> ipc-opener: absent (undefined)
SKETCH-WORKER fetch GET via self.fetch -> ipc-dialog: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via self.fetch -> ipc-dialog: absent (undefined)
SKETCH-WORKER fetch GET via self.fetch -> http-ipc-localhost: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via self.fetch -> http-ipc-localhost: absent (undefined)
SKETCH-WORKER fetch GET via self.fetch -> llpdf: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via self.fetch -> llpdf: absent (undefined)
SKETCH-WORKER fetch GET via self.fetch -> tauri-asset: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via self.fetch -> tauri-asset: absent (undefined)
SKETCH-WORKER fetch GET via globalThis.fetch -> ipc-scheme: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via globalThis.fetch -> ipc-scheme: absent (undefined)
SKETCH-WORKER fetch GET via globalThis.fetch -> ipc-scheme-real-shape: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via globalThis.fetch -> ipc-scheme-real-shape: absent (undefined)
SKETCH-WORKER fetch GET via globalThis.fetch -> ipc-load_vault: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via globalThis.fetch -> ipc-load_vault: absent (undefined)
SKETCH-WORKER fetch GET via globalThis.fetch -> ipc-opener: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via globalThis.fetch -> ipc-opener: absent (undefined)
SKETCH-WORKER fetch GET via globalThis.fetch -> ipc-dialog: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via globalThis.fetch -> ipc-dialog: absent (undefined)
SKETCH-WORKER fetch GET via globalThis.fetch -> http-ipc-localhost: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via globalThis.fetch -> http-ipc-localhost: absent (undefined)
SKETCH-WORKER fetch GET via globalThis.fetch -> llpdf: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via globalThis.fetch -> llpdf: absent (undefined)
SKETCH-WORKER fetch GET via globalThis.fetch -> tauri-asset: absent (undefined)
SKETCH-WORKER fetch POST(real shape) via globalThis.fetch -> tauri-asset: absent (undefined)
SKETCH-WORKER XMLHttpRequest GET -> ipc-scheme: absent (undefined)
SKETCH-WORKER XMLHttpRequest POST -> ipc-scheme: absent (undefined)
SKETCH-WORKER XMLHttpRequest GET -> ipc-scheme-real-shape: absent (undefined)
SKETCH-WORKER XMLHttpRequest POST -> ipc-scheme-real-shape: absent (undefined)
SKETCH-WORKER XMLHttpRequest GET -> ipc-load_vault: absent (undefined)
SKETCH-WORKER XMLHttpRequest POST -> ipc-load_vault: absent (undefined)
SKETCH-WORKER WebSocket ws://ipc.localhost: absent (undefined)
SKETCH-WORKER EventSource ipc://: absent (undefined)
SKETCH-WORKER navigator.sendBeacon: absent
SKETCH-WORKER dynamic import() -> ipc-scheme: error TypeError: Importing a module script failed.
SKETCH-WORKER dynamic import() -> ipc-scheme-real-shape: error TypeError: Importing a module script failed.
SKETCH-WORKER importScripts via self.importScripts: absent (undefined)
SKETCH-WORKER importScripts via WorkerGlobalScope.prototype.importScripts: absent (undefined)
SKETCH-WORKER new Worker(ipc://): error TypeError: undefined is not a constructor (evaluating 'new t.Worker(d[1][1])')
SKETCH-WORKER nested blob Worker: absent (undefined)
FRAME-NAV form.submit(ipc://): no exception
FRAME-NAV self-navigation to ipc:// now
FRAME-NAV frame load events in the 5 s after the navigation attempts: 1
CONTROL C1 (main-window fetch, no key): OK status=500 body="missing Tauri-Invoke-Key header"
GSM14-RESULT-END (278 lines)
```

### Rust-side log (every line)

All 46 lines. The 23 `ipc-protocol` lines are the app's own start-up calls from the main window (Origin and Referer
`tauri://localhost`, the real key), the main-window control `C1` (refused for the missing key, as in the first run) and
the report itself. There is no `ipc-postmessage` line (the handler is gone) and no key-mismatch line.

```
GSM14-RUST shell: unregistered the WebKit script message handler 'ipc'
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Awindow%7Cis_maximized origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=16
GSM14-RUST on_message cmd=plugin:window|is_maximized url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aevent%7Clisten origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=89
GSM14-RUST on_message cmd=plugin:event|listen url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/load_vault origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=load_vault url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aevent%7Clisten origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=88
GSM14-RUST on_message cmd=plugin:event|listen url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aevent%7Clisten origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=93
GSM14-RUST on_message cmd=plugin:event|listen url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aevent%7Clisten origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=93
GSM14-RUST on_message cmd=plugin:event|listen url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aevent%7Clisten origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=93
GSM14-RUST on_message cmd=plugin:event|listen url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aevent%7Clisten origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=93
GSM14-RUST on_message cmd=plugin:event|listen url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/get_ai_connection origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=12
GSM14-RUST on_message cmd=get_ai_connection url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/get_source_library origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=get_source_library url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aevent%7Cunlisten origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=38
GSM14-RUST on_message cmd=plugin:event|unlisten url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Awindow%7Cis_maximized origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=16
GSM14-RUST on_message cmd=plugin:window|is_maximized url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aevent%7Clisten origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=87
GSM14-RUST on_message cmd=plugin:event|listen url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/list_question_queue origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=12
GSM14-RUST on_message cmd=list_question_queue url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/workbench_open_problems origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=12
GSM14-RUST on_message cmd=workbench_open_problems url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/get_inbox_summary origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=12
GSM14-RUST on_message cmd=get_inbox_summary url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/get_source_library origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=get_source_library url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/goals_list origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=goals_list url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/get_review_counts origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=get_review_counts url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/get_review_counts origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=2
GSM14-RUST on_message cmd=get_review_counts url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/get_daily_plan origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=28
GSM14-RUST on_message cmd=get_daily_plan url=tauri://localhost
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/plugin%3Aapp%7Cversion?gsm14=C1 origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=false body_len=2
GSM14-RUST ipc-protocol label=main method=POST uri=ipc://localhost/gsm14_report origin=Some("tauri://localhost") referer=Some("tauri://localhost") has_invoke_key_header=true body_len=26295
GSM14-RUST on_message cmd=gsm14_report url=tauri://localhost
```

### What the results show

1. **The frame's CSP stops every request before it leaves WebKit.** `fetch` (every reference, GET and the invoke
   POST), `XMLHttpRequest`, `WebSocket`, `EventSource`, `import()`, `importScripts`, and the frame's `img`, `script`,
   `link` and `iframe` loads all fail in the page, and none of them appears in the Rust log, which logs every request
   that reaches the `ipc:` handler (`C1` proves it was live). The opaque-origin frame needs no deny-listing for this:
   the **fresh, never-stripped** blob Worker `B` and its nested Worker `BN` still have `fetch`, `XMLHttpRequest` and
   `WebSocket` and still fail the same way. So a blob Worker created inside the frame inherits the frame's policy in
   this WebKitGTK, which is what the first run's "inputs" asked for.
2. **No IPC global anywhere in the compartment.** `__TAURI_INTERNALS__`, `__TAURI__`, `ipc`, `isTauri` are absent in
   the frame and every Worker (Tauri injects its scripts into the top frame only). `window.webkit` itself is absent
   in the frame: WebKit exposes the namespace only while a script-message handler is registered, and the shell
   unregisters `ipc` at start-up (`GSM14-RUST shell: …`; the main window shows it absent too). The app's own invokes
   all went over the custom protocol, unaffected.
3. **The sandbox holds.** `parent.document`, `parent.__TAURI_INTERNALS__`, `top.location` and an `about:blank` child
   frame's window all throw WebKit's "Sandbox access violation"; `window.open` returns null; `localStorage` throws.
4. **Lines that are not failures in form, and why they are not requests:**
   - `FRAME iframe src=ipc://: LOADED`: WebKit replaces a frame its CSP blocks with an empty document and still fires
     `load`; no `gsm14=F` request reached Rust.
   - `new Worker(ipc://): constructed (object)` (frame, `B`, `BN`): the constructor returns before the script is
     fetched; `worker-src blob:` blocks the fetch, and no request reached Rust.
   - `FRAME-NAV … load events …: 1`: the frame's self-navigation to `ipc://` (and its form submission) produced one
     load event, the blocked navigation's empty document (the page's `frame-src` names only the frame document and
     the video embed); no `gsm14=FN`/`FF` request reached Rust.
5. **The real sketch path works and keeps its timing.** All three verified sketches drew digest-for-digest as
   verification recorded (27/27, 9/9, 19/19), with no watchdog pause. The first call, which now includes making the
   frame, starting the blob Worker, compiling the engine and loading the program, took 17–31 ms; every later call
   took at most 3 ms (watchdog 480 ms). After `dispose`, no compartment frame remained in the page.

**Not covered here (recorded, not run):** `llpdf://` and `tauri://` attempts failed in the page like the `ipc:` ones,
but the Rust side logs only the `ipc:` handler and the postMessage path, so for those two schemes the evidence is the
page's error alone. The `js_animation` frame (`llfig://`) is not built; its own G-SM14 extension is still to run when
it is.

### Probe code (exact; branch `probe/g-sm14-compartment`, commit `2244360639`, never landed; `Cargo.lock` omitted)

```diff
diff --git a/apps/learnloop-tauri/sketch-frame.html b/apps/learnloop-tauri/sketch-frame.html
index 3c96b699f7..231aabee14 100644
--- a/apps/learnloop-tauri/sketch-frame.html
+++ b/apps/learnloop-tauri/sketch-frame.html
@@ -12,7 +12,7 @@
 <html lang="en">
   <head>
     <meta charset="utf-8" />
-    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'sha256-emQFfwAXdRixTv/cOh+FLF/J8HyyHExoib3oYolFij8=' 'wasm-unsafe-eval'; worker-src blob:; child-src blob:; connect-src 'none'; img-src 'none'; style-src 'none'; font-src 'none'; media-src 'none'; frame-src 'none'; object-src 'none'; manifest-src 'none'; form-action 'none'; base-uri 'none'" />
+    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'sha256-/EdsEEgQjq7o8L6okb2WVGr+lwIBLEfkSDvNj/czk5M=' 'wasm-unsafe-eval'; worker-src blob:; child-src blob:; connect-src 'none'; img-src 'none'; style-src 'none'; font-src 'none'; media-src 'none'; frame-src 'none'; object-src 'none'; manifest-src 'none'; form-action 'none'; base-uri 'none'" />
     <meta name="referrer" content="no-referrer" />
     <title>sketch engine</title>
   </head>
@@ -28,6 +28,191 @@
   let worker = null;
   let workerUrl = "";
   let booted = false;
+  // ---- G-SM14 RERUN PROBE (scratch branch probe/g-sm14-compartment, never landed) ----
+  let gsm14Pending = null;
+async function gsm14Attempts(marker, spawnNested) {
+  const lines = [];
+  const g = self;
+  const T = 4000;
+  const describe = (e) => (e && e.name ? "error " + e.name + ": " + e.message : "error " + String(e)).slice(0, 200);
+  const timeout = (p) => Promise.race([p, new Promise((_, r) => setTimeout(() => r(new Error("timeout (no answer in 4 s)")), T))]);
+  const presence = (v) => (v !== undefined && v !== null ? "PRESENT (" + typeof v + ")" : "absent");
+  const urls = [
+    ["ipc-scheme", "ipc://localhost/plugin:app|ping?gsm14=" + marker],
+    ["ipc-scheme-real-shape", "ipc://localhost/" + encodeURIComponent("plugin:app|version") + "?gsm14=" + marker],
+    ["ipc-load_vault", "ipc://localhost/load_vault?gsm14=" + marker],
+    ["ipc-opener", "ipc://localhost/" + encodeURIComponent("plugin:opener|open_url") + "?gsm14=" + marker],
+    ["ipc-dialog", "ipc://localhost/" + encodeURIComponent("plugin:dialog|open") + "?gsm14=" + marker],
+    ["http-ipc-localhost", "http://ipc.localhost/" + encodeURIComponent("plugin:app|version") + "?gsm14=" + marker],
+    ["llpdf", "llpdf://localhost/sha256-deadbeef?gsm14=" + marker],
+    ["tauri-asset", "tauri://localhost/index.html?gsm14=" + marker],
+  ];
+  const realInit = () => ({ method: "POST", body: "{}", headers: { "Content-Type": "application/json", "Tauri-Callback": "12345", "Tauri-Error": "12346", "Tauri-Invoke-Key": "gsm14-guessed-key" } });
+  async function viaFetch(fn, url, init) {
+    if (typeof fn !== "function") return "absent (" + typeof fn + ")";
+    try {
+      const r = await timeout(fn.call(g, url, init));
+      let b = "";
+      try { b = (await timeout(r.text())).slice(0, 80); } catch (e) { b = describe(e); }
+      return "OK status=" + r.status + " tauri-response=" + r.headers.get("Tauri-Response") + " body=" + JSON.stringify(b);
+    } catch (e) { return describe(e); }
+  }
+  function viaXhr(ctor, method, url) {
+    if (typeof ctor !== "function") return Promise.resolve("absent (" + typeof ctor + ")");
+    return new Promise((resolve) => {
+      try {
+        const x = new ctor();
+        const timer = setTimeout(() => resolve("timeout (no answer in 4 s)"), T);
+        x.onload = () => { clearTimeout(timer); resolve("OK status=" + x.status + " body=" + JSON.stringify(String(x.responseText).slice(0, 80))); };
+        x.onerror = () => { clearTimeout(timer); resolve("error (onerror, status=" + x.status + ")"); };
+        x.open(method, url);
+        x.send(method === "POST" ? "{}" : null);
+      } catch (e) { resolve(describe(e)); }
+    });
+  }
+  function viaEvents(ctor, url, kind) {
+    if (typeof ctor !== "function") return Promise.resolve("absent (" + typeof ctor + ")");
+    return new Promise((resolve) => {
+      try {
+        const s = new ctor(url);
+        const timer = setTimeout(() => { try { s.close(); } catch (_) { /* */ } resolve("timeout (no answer in 4 s)"); }, T);
+        s.onopen = () => { clearTimeout(timer); try { s.close(); } catch (_) { /* */ } resolve("OK (open) " + kind); };
+        s.onerror = () => { clearTimeout(timer); try { s.close(); } catch (_) { /* */ } resolve("error (onerror)"); };
+      } catch (e) { resolve(describe(e)); }
+    });
+  }
+  lines.push("context: location=" + String(g.location && g.location.href).slice(0, 80) + " origin=" + g.origin + " isSecureContext=" + String(g.isSecureContext)
+    + (g.document ? " referrer=" + JSON.stringify(g.document.referrer) : ""));
+  for (const name of ["__TAURI_INTERNALS__", "__TAURI__", "__TAURI_INVOKE_KEY__", "isTauri", "ipc", "webkit", "chrome"]) lines.push("global " + name + ": " + presence(g[name]));
+  lines.push("webkit.messageHandlers: " + presence(g.webkit && g.webkit.messageHandlers) + " ; .ipc: " + presence(g.webkit && g.webkit.messageHandlers && g.webkit.messageHandlers.ipc));
+  if (g.webkit && g.webkit.messageHandlers && g.webkit.messageHandlers.ipc) {
+    try { g.webkit.messageHandlers.ipc.postMessage(JSON.stringify({ cmd: "plugin:app|version", callback: 1, error: 2, payload: {}, options: {}, __TAURI_INVOKE_KEY__: "gsm14-guessed-key", gsm14: marker })); lines.push("webkit.messageHandlers.ipc.postMessage: SENT (no exception)"); }
+    catch (e) { lines.push("webkit.messageHandlers.ipc.postMessage: " + describe(e)); }
+  }
+  if (g.chrome && g.chrome.webview) lines.push("chrome.webview: PRESENT");
+  // Every reference to fetch, own and along the prototype chain.
+  const refs = [["self.fetch", g.fetch], ["globalThis.fetch", globalThis.fetch]];
+  let level = Object.getPrototypeOf(g);
+  for (let depth = 1; level && depth < 8; depth += 1, level = Object.getPrototypeOf(level)) {
+    const d = Object.getOwnPropertyDescriptor(level, "fetch");
+    if (d) refs.push(["prototype depth " + depth + " (" + (level.constructor && level.constructor.name) + ").fetch", d.value]);
+  }
+  for (const [label, fn] of refs) {
+    for (const [target, url] of urls) {
+      lines.push("fetch GET via " + label + " -> " + target + ": " + await viaFetch(fn, url));
+      lines.push("fetch POST(real shape) via " + label + " -> " + target + ": " + await viaFetch(fn, url, realInit()));
+    }
+  }
+  for (const [target, url] of urls.slice(0, 3)) {
+    lines.push("XMLHttpRequest GET -> " + target + ": " + await viaXhr(g.XMLHttpRequest, "GET", url));
+    lines.push("XMLHttpRequest POST -> " + target + ": " + await viaXhr(g.XMLHttpRequest, "POST", url));
+  }
+  lines.push("WebSocket ws://ipc.localhost: " + await viaEvents(g.WebSocket, "ws://ipc.localhost/?gsm14=" + marker, "ws"));
+  lines.push("EventSource ipc://: " + await viaEvents(g.EventSource, urls[0][1], "es"));
+  if (g.navigator && typeof g.navigator.sendBeacon === "function") {
+    try { lines.push("navigator.sendBeacon ipc://: returned " + g.navigator.sendBeacon(urls[1][1], "{}")); } catch (e) { lines.push("navigator.sendBeacon ipc://: " + describe(e)); }
+  } else lines.push("navigator.sendBeacon: absent");
+  for (const [target, url] of urls.slice(0, 2)) {
+    try { await timeout(import(/* @vite-ignore */ url)); lines.push("dynamic import() -> " + target + ": OK (module loaded)"); }
+    catch (e) { lines.push("dynamic import() -> " + target + ": " + describe(e)); }
+  }
+  const wgs = g.WorkerGlobalScope && g.WorkerGlobalScope.prototype;
+  for (const [label, fn] of [["self.importScripts", g.importScripts], ["WorkerGlobalScope.prototype.importScripts", wgs && wgs.importScripts]]) {
+    if (!g.WorkerGlobalScope) break;
+    if (typeof fn !== "function") { lines.push("importScripts via " + label + ": absent (" + typeof fn + ")"); continue; }
+    try { fn.call(g, urls[0][1]); lines.push("importScripts(ipc://) via " + label + ": loaded"); } catch (e) { lines.push("importScripts(ipc://) via " + label + ": " + describe(e)); }
+    try {
+      const b = URL.createObjectURL(new Blob(["self.__gsm14i = 1;"], { type: "text/javascript" }));
+      fn.call(g, b);
+      lines.push("importScripts(blob:) via " + label + ": loaded (" + g.__gsm14i + ")");
+    } catch (e) { lines.push("importScripts(blob:) via " + label + ": " + describe(e)); }
+  }
+  if (g.document) {
+    // Window-only loaders: each is a request if its directive allows it.
+    const doc = g.document;
+    const wait = (el, label) => new Promise((resolve) => {
+      const timer = setTimeout(() => resolve(label + ": no load/error event in 4 s"), T);
+      el.onload = () => { clearTimeout(timer); resolve(label + ": LOADED"); };
+      el.onerror = () => { clearTimeout(timer); resolve(label + ": error event"); };
+    });
+    try { const img = new Image(); const p = wait(img, "img src=ipc://"); img.src = urls[1][1]; lines.push(await p); } catch (e) { lines.push("img: " + describe(e)); }
+    try { const s = doc.createElement("script"); const p = wait(s, "script src=ipc://"); s.src = urls[1][1]; doc.body.appendChild(s); lines.push(await p); } catch (e) { lines.push("script: " + describe(e)); }
+    try { const l = doc.createElement("link"); l.rel = "stylesheet"; const p = wait(l, "link stylesheet ipc://"); l.href = urls[1][1]; doc.head.appendChild(l); lines.push(await p); } catch (e) { lines.push("link: " + describe(e)); }
+    try { const f = doc.createElement("iframe"); const p = wait(f, "iframe src=ipc://"); f.src = urls[1][1]; doc.body.appendChild(f); lines.push(await p); } catch (e) { lines.push("iframe: " + describe(e)); }
+    try {
+      const child = doc.createElement("iframe");
+      doc.body.appendChild(child);
+      const w = child.contentWindow;
+      lines.push("child about:blank iframe: webkit=" + presence(w && w.webkit) + " messageHandlers.ipc=" + presence(w && w.webkit && w.webkit.messageHandlers && w.webkit.messageHandlers.ipc)
+        + " __TAURI_INTERNALS__=" + presence(w && w.__TAURI_INTERNALS__));
+      if (w && w.webkit && w.webkit.messageHandlers && w.webkit.messageHandlers.ipc) {
+        try { w.webkit.messageHandlers.ipc.postMessage(JSON.stringify({ gsm14: marker + "-child" })); lines.push("child messageHandlers.ipc.postMessage: SENT"); } catch (e) { lines.push("child postMessage: " + describe(e)); }
+      }
+    } catch (e) { lines.push("child about:blank iframe: " + describe(e)); }
+    try { lines.push("parent.document: " + presence(g.parent.document)); } catch (e) { lines.push("parent.document: " + describe(e)); }
+    try { lines.push("parent.__TAURI_INTERNALS__: " + presence(g.parent.__TAURI_INTERNALS__)); } catch (e) { lines.push("parent.__TAURI_INTERNALS__: " + describe(e)); }
+    try { lines.push("top.location.href: " + String(g.top.location.href)); } catch (e) { lines.push("top.location.href: " + describe(e)); }
+    try { const w = g.open(urls[1][1]); lines.push("window.open(ipc://): " + (w ? "OPENED" : "null (refused)")); } catch (e) { lines.push("window.open(ipc://): " + describe(e)); }
+    try { lines.push("localStorage: " + presence(g.localStorage)); } catch (e) { lines.push("localStorage: " + describe(e)); }
+  }
+  try {
+    const w = new g.Worker(urls[1][1]);
+    lines.push("new Worker(ipc://): constructed (" + typeof w + ")");
+    try { w.terminate(); } catch (_) { /* */ }
+  } catch (e) { lines.push("new Worker(ipc://): " + describe(e)); }
+  if (spawnNested) {
+    if (typeof g.Worker !== "function") lines.push("nested blob Worker: absent (" + typeof g.Worker + ")");
+    else {
+      const source = "(" + gsm14Attempts.toString() + ")(" + JSON.stringify(marker + "N") + ", false).then((l) => postMessage(l), (e) => postMessage(['nested crashed ' + e]));";
+      lines.push(...await new Promise((resolve) => {
+        try {
+          const n = new g.Worker(URL.createObjectURL(new Blob([source], { type: "text/javascript" })));
+          const timer = setTimeout(() => { n.terminate(); resolve(["nested blob Worker: timeout (120 s)"]); }, 120000);
+          n.onmessage = (e) => { clearTimeout(timer); n.terminate(); resolve(["nested blob Worker: started"].concat(e.data.map((l) => "nested: " + l))); };
+          n.onerror = (e) => { clearTimeout(timer); resolve(["nested blob Worker: error event (" + (e.message || "no message") + ")"]); };
+        } catch (e) { resolve(["nested blob Worker: " + describe(e)]); }
+      }));
+    }
+  }
+  return lines;
+}
+
+  const gsm14Run = async () => {
+    const lines = [];
+    try { for (const l of await gsm14Attempts("F", false)) lines.push("FRAME " + l); } catch (e) { lines.push("FRAME crashed " + e); }
+    const fresh = await new Promise((resolve) => {
+      try {
+        const src = "(" + gsm14Attempts.toString() + ")('B', true).then((l) => postMessage(l), (e) => postMessage(['crashed ' + e]));";
+        const b = new Worker(URL.createObjectURL(new Blob([src], { type: "text/javascript" })));
+        const timer = setTimeout(() => { b.terminate(); resolve(["timeout (240 s)"]); }, 240000);
+        b.onmessage = (e) => { clearTimeout(timer); b.terminate(); resolve(["started"].concat(e.data)); };
+        b.onerror = (e) => { clearTimeout(timer); resolve(["error event (" + (e.message || "no message") + ")"]); };
+      } catch (e) { resolve(["could not start: " + e]); }
+    });
+    for (const l of fresh) lines.push("FRESH-BLOB-WORKER " + l);
+    const sketch = await new Promise((resolve) => {
+      if (!worker) { resolve(["no sketch Worker"]); return; }
+      gsm14Pending = resolve;
+      setTimeout(() => resolve(["timeout (240 s)"]), 240000);
+      worker.postMessage({ gsm14: "probe" });
+    });
+    for (const l of sketch) lines.push("SKETCH-WORKER " + l);
+    tell({ kind: "gsm14-result", lines });
+  };
+  const gsm14Navigate = () => {
+    try {
+      const f = document.createElement("form");
+      f.method = "POST";
+      f.action = "ipc://localhost/" + encodeURIComponent("plugin:app|version") + "?gsm14=FF";
+      document.body.appendChild(f);
+      f.submit();
+      tell({ kind: "gsm14-note", line: "form.submit(ipc://): no exception" });
+    } catch (e) { tell({ kind: "gsm14-note", line: "form.submit(ipc://): " + e }); }
+    setTimeout(() => {
+      tell({ kind: "gsm14-note", line: "self-navigation to ipc:// now" });
+      try { location.href = "ipc://localhost/" + encodeURIComponent("plugin:app|version") + "?gsm14=FN"; } catch (e) { tell({ kind: "gsm14-note", line: "location.href=ipc://: " + e }); }
+    }, 500);
+  };
   const isBuffer = (value) => Object.prototype.toString.call(value) === "[object ArrayBuffer]";
   const isPlain = (value) => typeof value === "object" && value !== null && !Array.isArray(value) && Object.getPrototypeOf(value) === Object.prototype;
   const tell = (message) => {
@@ -72,6 +257,7 @@
     worker.onmessage = (event) => {
       const notice = event.data;
       if (!isPlain(notice)) return;
+      if (notice.gsm14 === "result" && gsm14Pending) { gsm14Pending(notice.lines); gsm14Pending = null; return; }
       if (notice.kind === "started" && Object.keys(notice).length === 1) tell({ kind: "started" });
       else if (notice.kind === "failed" && typeof notice.message === "string") fail(notice.message);
     };
@@ -92,6 +278,8 @@
       if (!isPlain(data)) return;
       if (data.kind === "boot") boot(data, message.ports);
       else if (data.kind === "stop" && Object.keys(data).length === 1) stop();
+      else if (data.kind === "gsm14") void gsm14Run();
+      else if (data.kind === "gsm14-navigate") gsm14Navigate();
     };
     tell({ kind: "connected" });
   };
diff --git a/apps/learnloop-tauri/src-tauri/Cargo.toml b/apps/learnloop-tauri/src-tauri/Cargo.toml
index 25f492896f..c85f870553 100644
--- a/apps/learnloop-tauri/src-tauri/Cargo.toml
+++ b/apps/learnloop-tauri/src-tauri/Cargo.toml
@@ -24,3 +24,8 @@ webkit2gtk = { version = "=2.0.2", features = ["v2_38"] }
 
 [features]
 custom-protocol = ["tauri/custom-protocol"]
+
+# G-SM14 RERUN PROBE (scratch branch probe/g-sm14-compartment, never landed): tauri 2.11.2 with
+# eprintln! at the ipc: protocol handler, the postMessage handler and on_message.
+[patch.crates-io]
+tauri = { path = "/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/a22010cc-5149-4947-a2b8-247f18b8f1a0/scratchpad/gsm14/tauri-2.11.2" }
diff --git a/apps/learnloop-tauri/src-tauri/src/main.rs b/apps/learnloop-tauri/src-tauri/src/main.rs
index 9e1c84d0ee..ee60e2ba82 100644
--- a/apps/learnloop-tauri/src-tauri/src/main.rs
+++ b/apps/learnloop-tauri/src-tauri/src/main.rs
@@ -186,6 +186,20 @@ fn debug_zoom_enabled() -> bool {
     })
 }
 
+// G-SM14 RERUN PROBE (scratch branch probe/g-sm14-compartment, never landed): the MAIN
+// window reports the probe's lines here; they go to stderr, then the app exits.
+#[tauri::command]
+fn gsm14_report(app: tauri::AppHandle, lines: Vec<String>) {
+    for line in &lines {
+        eprintln!("GSM14-RESULT {line}");
+    }
+    eprintln!("GSM14-RESULT-END ({} lines)", lines.len());
+    std::thread::spawn(move || {
+        std::thread::sleep(std::time::Duration::from_millis(1500));
+        app.exit(0);
+    });
+}
+
 fn main() {
     // WebKitGTK's DMA-BUF renderer intermittently drops composited tiles on
     // Linux (Intel/Mesa): toggling display on the reader rail's tab panels
@@ -246,6 +260,7 @@ fn main() {
                 use webkit2gtk::{UserContentManagerExt, WebViewExt};
                 if let Some(manager) = platform.inner().user_content_manager() {
                     manager.unregister_script_message_handler("ipc");
+                    eprintln!("GSM14-RUST shell: unregistered the WebKit script message handler 'ipc'");
                 }
             })?;
             #[cfg(not(target_os = "linux"))]
@@ -718,13 +733,15 @@ fn main() {
                 reader_pause_arc,
                 reader_shrink_envelope,
                 reader_prime,
-                reader_restore
+                reader_restore,
+                gsm14_report
             ];
             // RW5d P2 sketch compartment, defense in depth: a LearnLoop command
             // asked from a frame or a worker (not the app's own document) is
             // refused before it runs (frame_guard.rs says what this can't cover).
             move |invoke| {
                 if let Some(reason) = frame_guard::refusal_reason(invoke.message.headers()) {
+                    eprintln!("GSM14-RUST frame_guard refused cmd={} reason={reason}", invoke.message.command());
                     invoke.resolver.reject(format!("refused: {reason}"));
                     return true;
                 }
diff --git a/apps/learnloop-tauri/src/gsm14/attempts.js b/apps/learnloop-tauri/src/gsm14/attempts.js
new file mode 100644
index 0000000000..b72e552bcf
--- /dev/null
+++ b/apps/learnloop-tauri/src/gsm14/attempts.js
@@ -0,0 +1,150 @@
+// ---- G-SM14 RERUN PROBE (scratch branch probe/g-sm14-compartment, never landed) ----
+// One self-contained function (its source is also inlined into sketch-frame.html and into blob Workers):
+// every IPC/network path tried from the calling context, one line each. `marker` tags each request
+// (?gsm14=<marker>) so the patched-Tauri log shows where it came from.
+export async function gsm14Attempts(marker, spawnNested) {
+  const lines = [];
+  const g = self;
+  const T = 4000;
+  const describe = (e) => (e && e.name ? "error " + e.name + ": " + e.message : "error " + String(e)).slice(0, 200);
+  const timeout = (p) => Promise.race([p, new Promise((_, r) => setTimeout(() => r(new Error("timeout (no answer in 4 s)")), T))]);
+  const presence = (v) => (v !== undefined && v !== null ? "PRESENT (" + typeof v + ")" : "absent");
+  const urls = [
+    ["ipc-scheme", "ipc://localhost/plugin:app|ping?gsm14=" + marker],
+    ["ipc-scheme-real-shape", "ipc://localhost/" + encodeURIComponent("plugin:app|version") + "?gsm14=" + marker],
+    ["ipc-load_vault", "ipc://localhost/load_vault?gsm14=" + marker],
+    ["ipc-opener", "ipc://localhost/" + encodeURIComponent("plugin:opener|open_url") + "?gsm14=" + marker],
+    ["ipc-dialog", "ipc://localhost/" + encodeURIComponent("plugin:dialog|open") + "?gsm14=" + marker],
+    ["http-ipc-localhost", "http://ipc.localhost/" + encodeURIComponent("plugin:app|version") + "?gsm14=" + marker],
+    ["llpdf", "llpdf://localhost/sha256-deadbeef?gsm14=" + marker],
+    ["tauri-asset", "tauri://localhost/index.html?gsm14=" + marker],
+  ];
+  const realInit = () => ({ method: "POST", body: "{}", headers: { "Content-Type": "application/json", "Tauri-Callback": "12345", "Tauri-Error": "12346", "Tauri-Invoke-Key": "gsm14-guessed-key" } });
+  async function viaFetch(fn, url, init) {
+    if (typeof fn !== "function") return "absent (" + typeof fn + ")";
+    try {
+      const r = await timeout(fn.call(g, url, init));
+      let b = "";
+      try { b = (await timeout(r.text())).slice(0, 80); } catch (e) { b = describe(e); }
+      return "OK status=" + r.status + " tauri-response=" + r.headers.get("Tauri-Response") + " body=" + JSON.stringify(b);
+    } catch (e) { return describe(e); }
+  }
+  function viaXhr(ctor, method, url) {
+    if (typeof ctor !== "function") return Promise.resolve("absent (" + typeof ctor + ")");
+    return new Promise((resolve) => {
+      try {
+        const x = new ctor();
+        const timer = setTimeout(() => resolve("timeout (no answer in 4 s)"), T);
+        x.onload = () => { clearTimeout(timer); resolve("OK status=" + x.status + " body=" + JSON.stringify(String(x.responseText).slice(0, 80))); };
+        x.onerror = () => { clearTimeout(timer); resolve("error (onerror, status=" + x.status + ")"); };
+        x.open(method, url);
+        x.send(method === "POST" ? "{}" : null);
+      } catch (e) { resolve(describe(e)); }
+    });
+  }
+  function viaEvents(ctor, url, kind) {
+    if (typeof ctor !== "function") return Promise.resolve("absent (" + typeof ctor + ")");
+    return new Promise((resolve) => {
+      try {
+        const s = new ctor(url);
+        const timer = setTimeout(() => { try { s.close(); } catch (_) { /* */ } resolve("timeout (no answer in 4 s)"); }, T);
+        s.onopen = () => { clearTimeout(timer); try { s.close(); } catch (_) { /* */ } resolve("OK (open) " + kind); };
+        s.onerror = () => { clearTimeout(timer); try { s.close(); } catch (_) { /* */ } resolve("error (onerror)"); };
+      } catch (e) { resolve(describe(e)); }
+    });
+  }
+  lines.push("context: location=" + String(g.location && g.location.href).slice(0, 80) + " origin=" + g.origin + " isSecureContext=" + String(g.isSecureContext)
+    + (g.document ? " referrer=" + JSON.stringify(g.document.referrer) : ""));
+  for (const name of ["__TAURI_INTERNALS__", "__TAURI__", "__TAURI_INVOKE_KEY__", "isTauri", "ipc", "webkit", "chrome"]) lines.push("global " + name + ": " + presence(g[name]));
+  lines.push("webkit.messageHandlers: " + presence(g.webkit && g.webkit.messageHandlers) + " ; .ipc: " + presence(g.webkit && g.webkit.messageHandlers && g.webkit.messageHandlers.ipc));
+  if (g.webkit && g.webkit.messageHandlers && g.webkit.messageHandlers.ipc) {
+    try { g.webkit.messageHandlers.ipc.postMessage(JSON.stringify({ cmd: "plugin:app|version", callback: 1, error: 2, payload: {}, options: {}, __TAURI_INVOKE_KEY__: "gsm14-guessed-key", gsm14: marker })); lines.push("webkit.messageHandlers.ipc.postMessage: SENT (no exception)"); }
+    catch (e) { lines.push("webkit.messageHandlers.ipc.postMessage: " + describe(e)); }
+  }
+  if (g.chrome && g.chrome.webview) lines.push("chrome.webview: PRESENT");
+  // Every reference to fetch, own and along the prototype chain.
+  const refs = [["self.fetch", g.fetch], ["globalThis.fetch", globalThis.fetch]];
+  let level = Object.getPrototypeOf(g);
+  for (let depth = 1; level && depth < 8; depth += 1, level = Object.getPrototypeOf(level)) {
+    const d = Object.getOwnPropertyDescriptor(level, "fetch");
+    if (d) refs.push(["prototype depth " + depth + " (" + (level.constructor && level.constructor.name) + ").fetch", d.value]);
+  }
+  for (const [label, fn] of refs) {
+    for (const [target, url] of urls) {
+      lines.push("fetch GET via " + label + " -> " + target + ": " + await viaFetch(fn, url));
+      lines.push("fetch POST(real shape) via " + label + " -> " + target + ": " + await viaFetch(fn, url, realInit()));
+    }
+  }
+  for (const [target, url] of urls.slice(0, 3)) {
+    lines.push("XMLHttpRequest GET -> " + target + ": " + await viaXhr(g.XMLHttpRequest, "GET", url));
+    lines.push("XMLHttpRequest POST -> " + target + ": " + await viaXhr(g.XMLHttpRequest, "POST", url));
+  }
+  lines.push("WebSocket ws://ipc.localhost: " + await viaEvents(g.WebSocket, "ws://ipc.localhost/?gsm14=" + marker, "ws"));
+  lines.push("EventSource ipc://: " + await viaEvents(g.EventSource, urls[0][1], "es"));
+  if (g.navigator && typeof g.navigator.sendBeacon === "function") {
+    try { lines.push("navigator.sendBeacon ipc://: returned " + g.navigator.sendBeacon(urls[1][1], "{}")); } catch (e) { lines.push("navigator.sendBeacon ipc://: " + describe(e)); }
+  } else lines.push("navigator.sendBeacon: absent");
+  for (const [target, url] of urls.slice(0, 2)) {
+    try { await timeout(import(/* @vite-ignore */ url)); lines.push("dynamic import() -> " + target + ": OK (module loaded)"); }
+    catch (e) { lines.push("dynamic import() -> " + target + ": " + describe(e)); }
+  }
+  const wgs = g.WorkerGlobalScope && g.WorkerGlobalScope.prototype;
+  for (const [label, fn] of [["self.importScripts", g.importScripts], ["WorkerGlobalScope.prototype.importScripts", wgs && wgs.importScripts]]) {
+    if (!g.WorkerGlobalScope) break;
+    if (typeof fn !== "function") { lines.push("importScripts via " + label + ": absent (" + typeof fn + ")"); continue; }
+    try { fn.call(g, urls[0][1]); lines.push("importScripts(ipc://) via " + label + ": loaded"); } catch (e) { lines.push("importScripts(ipc://) via " + label + ": " + describe(e)); }
+    try {
+      const b = URL.createObjectURL(new Blob(["self.__gsm14i = 1;"], { type: "text/javascript" }));
+      fn.call(g, b);
+      lines.push("importScripts(blob:) via " + label + ": loaded (" + g.__gsm14i + ")");
+    } catch (e) { lines.push("importScripts(blob:) via " + label + ": " + describe(e)); }
+  }
+  if (g.document) {
+    // Window-only loaders: each is a request if its directive allows it.
+    const doc = g.document;
+    const wait = (el, label) => new Promise((resolve) => {
+      const timer = setTimeout(() => resolve(label + ": no load/error event in 4 s"), T);
+      el.onload = () => { clearTimeout(timer); resolve(label + ": LOADED"); };
+      el.onerror = () => { clearTimeout(timer); resolve(label + ": error event"); };
+    });
+    try { const img = new Image(); const p = wait(img, "img src=ipc://"); img.src = urls[1][1]; lines.push(await p); } catch (e) { lines.push("img: " + describe(e)); }
+    try { const s = doc.createElement("script"); const p = wait(s, "script src=ipc://"); s.src = urls[1][1]; doc.body.appendChild(s); lines.push(await p); } catch (e) { lines.push("script: " + describe(e)); }
+    try { const l = doc.createElement("link"); l.rel = "stylesheet"; const p = wait(l, "link stylesheet ipc://"); l.href = urls[1][1]; doc.head.appendChild(l); lines.push(await p); } catch (e) { lines.push("link: " + describe(e)); }
+    try { const f = doc.createElement("iframe"); const p = wait(f, "iframe src=ipc://"); f.src = urls[1][1]; doc.body.appendChild(f); lines.push(await p); } catch (e) { lines.push("iframe: " + describe(e)); }
+    try {
+      const child = doc.createElement("iframe");
+      doc.body.appendChild(child);
+      const w = child.contentWindow;
+      lines.push("child about:blank iframe: webkit=" + presence(w && w.webkit) + " messageHandlers.ipc=" + presence(w && w.webkit && w.webkit.messageHandlers && w.webkit.messageHandlers.ipc)
+        + " __TAURI_INTERNALS__=" + presence(w && w.__TAURI_INTERNALS__));
+      if (w && w.webkit && w.webkit.messageHandlers && w.webkit.messageHandlers.ipc) {
+        try { w.webkit.messageHandlers.ipc.postMessage(JSON.stringify({ gsm14: marker + "-child" })); lines.push("child messageHandlers.ipc.postMessage: SENT"); } catch (e) { lines.push("child postMessage: " + describe(e)); }
+      }
+    } catch (e) { lines.push("child about:blank iframe: " + describe(e)); }
+    try { lines.push("parent.document: " + presence(g.parent.document)); } catch (e) { lines.push("parent.document: " + describe(e)); }
+    try { lines.push("parent.__TAURI_INTERNALS__: " + presence(g.parent.__TAURI_INTERNALS__)); } catch (e) { lines.push("parent.__TAURI_INTERNALS__: " + describe(e)); }
+    try { lines.push("top.location.href: " + String(g.top.location.href)); } catch (e) { lines.push("top.location.href: " + describe(e)); }
+    try { const w = g.open(urls[1][1]); lines.push("window.open(ipc://): " + (w ? "OPENED" : "null (refused)")); } catch (e) { lines.push("window.open(ipc://): " + describe(e)); }
+    try { lines.push("localStorage: " + presence(g.localStorage)); } catch (e) { lines.push("localStorage: " + describe(e)); }
+  }
+  try {
+    const w = new g.Worker(urls[1][1]);
+    lines.push("new Worker(ipc://): constructed (" + typeof w + ")");
+    try { w.terminate(); } catch (_) { /* */ }
+  } catch (e) { lines.push("new Worker(ipc://): " + describe(e)); }
+  if (spawnNested) {
+    if (typeof g.Worker !== "function") lines.push("nested blob Worker: absent (" + typeof g.Worker + ")");
+    else {
+      const source = "(" + gsm14Attempts.toString() + ")(" + JSON.stringify(marker + "N") + ", false).then((l) => postMessage(l), (e) => postMessage(['nested crashed ' + e]));";
+      lines.push(...await new Promise((resolve) => {
+        try {
+          const n = new g.Worker(URL.createObjectURL(new Blob([source], { type: "text/javascript" })));
+          const timer = setTimeout(() => { n.terminate(); resolve(["nested blob Worker: timeout (120 s)"]); }, 120000);
+          n.onmessage = (e) => { clearTimeout(timer); n.terminate(); resolve(["nested blob Worker: started"].concat(e.data.map((l) => "nested: " + l))); };
+          n.onerror = (e) => { clearTimeout(timer); resolve(["nested blob Worker: error event (" + (e.message || "no message") + ")"]); };
+        } catch (e) { resolve(["nested blob Worker: " + describe(e)]); }
+      }));
+    }
+  }
+  return lines;
+}
diff --git a/apps/learnloop-tauri/src/gsm14/gsm14Harness.ts b/apps/learnloop-tauri/src/gsm14/gsm14Harness.ts
new file mode 100644
index 0000000000..2c732be14a
--- /dev/null
+++ b/apps/learnloop-tauri/src/gsm14/gsm14Harness.ts
@@ -0,0 +1,97 @@
+// ---- G-SM14 RERUN PROBE HARNESS (scratch branch probe/g-sm14-compartment, never landed) ----
+// In the MAIN window: (1) run the verified corpus through the production compartment
+// (createSketchWorker -> portRunner -> withWatchdog, as SketchFigure does), timing it and
+// comparing every tested digest; (2) in one more compartment, after a real start-up, ask the
+// frame to run the probe in the frame document, in a fresh blob Worker it makes (CSP only) and
+// its nested Worker, and in the real sketch Worker (and its nested Worker); (3) try the frame's
+// navigation paths; (4) one control from the main window; then report through gsm14_report
+// (from the main window, never from the compartment).
+import { invoke } from "@tauri-apps/api/core";
+import parity from "../screens/reader/figures/sketch/sketchParityCorpus.json";
+import { createSketchWorker } from "../screens/reader/figures/sketch/sketchCompartmentClient";
+import { portRunner, withWatchdog, WATCHDOG_MS } from "../screens/reader/figures/sketch/sketchRunner";
+import { readSchedule, type SketchProgram } from "../screens/reader/figures/sketch/sketchScene";
+
+const describe = (caught: unknown) => (caught instanceof Error ? `error ${caught.name}: ${caught.message}` : `error ${String(caught)}`).slice(0, 200);
+type Tested = { values: number[]; steps: number[]; digests: string[] };
+type Verified = { name: string; program: SketchProgram & { code: string; clock?: { dt: number } }; sketch: { seed: number; tested: Tested[]; readSteps?: number[] } };
+
+async function realRuns(lines: string[]) {
+  for (const item of (parity as unknown as { verified: Verified[] }).verified) {
+    let paused = false;
+    const handle = createSketchWorker();
+    const runner = withWatchdog(portRunner(handle), WATCHDOG_MS, () => { paused = true; });
+    const timings: number[] = [];
+    const timed = async <T,>(call: () => Promise<T>) => { const start = performance.now(); const value = await call(); timings.push(performance.now() - start); return value; };
+    let matched = 0;
+    let compared = 0;
+    try {
+      const startedAt = performance.now();
+      await runner.load(item.program.code);
+      const loadMs = performance.now() - startedAt;
+      const names = item.program.parameters.map((parameter) => parameter.name);
+      for (const entry of item.sketch.tested) {
+        const params = Object.fromEntries(names.map((name, i) => [name, entry.values[i]]));
+        await timed(() => runner.init(params, item.sketch.seed));
+        let at = 0;
+        for (const index of item.sketch.readSteps ?? readSchedule(item.program)) {
+          if (index > at) { const from = at; await timed(() => runner.step(params, item.program.clock!.dt, from, index - from)); at = index; }
+          const read = await timed(() => runner.read(params, index));
+          const position = entry.steps.indexOf(index);
+          if (position >= 0) { compared += 1; if (read.digest === entry.digests[position]) matched += 1; }
+        }
+      }
+      lines.push(`REAL ${item.name}: digests matched ${matched}/${compared}; first load (frame + Worker start-up + engine compile + load) ${loadMs.toFixed(1)} ms; other calls ${timings.length}, max ${Math.max(...timings).toFixed(1)} ms; watchdog ${WATCHDOG_MS} ms; paused=${paused}`);
+    } catch (caught) {
+      lines.push(`REAL ${item.name}: FAILED ${describe(caught)} (matched ${matched}/${compared}, paused=${paused})`);
+    }
+    runner.dispose();
+  }
+  lines.push(`REAL compartments left in the page after dispose: ${document.querySelectorAll("iframe[data-sketch-compartment]").length}`);
+}
+
+async function probe(lines: string[]) {
+  const handle = createSketchWorker() as unknown as ReturnType<typeof createSketchWorker> & {
+    gsm14Send(message: unknown): void; gsm14Frame: HTMLIFrameElement; gsm14Result?: (lines: string[]) => void; gsm14Note?: (line: string) => void;
+  };
+  const runner = portRunner(handle);
+  const notes: string[] = [];
+  handle.gsm14Note = (line) => notes.push(line);
+  const code = "function init(p){return 1} function view(s,p){return {viewport:{x:[0,1],y:[0,1]},elements:[]}} function probes(s,p){return {s:s}}";
+  await runner.load(code);
+  await runner.init({}, 1);
+  const read = await runner.read({}, 0);
+  lines.push(`PROBE compartment real start-up: load+init+read OK (probes ${JSON.stringify(read.probes)})`);
+  const result = await new Promise<string[]>((resolve) => {
+    const timer = setTimeout(() => resolve(["PROBE: TIMEOUT (600 s)"]), 600_000);
+    handle.gsm14Result = (got) => { clearTimeout(timer); resolve(got); };
+    handle.gsm14Send({ kind: "gsm14" });
+  });
+  lines.push(...result);
+  let loads = 0;
+  handle.gsm14Frame.addEventListener("load", () => { loads += 1; });
+  handle.gsm14Send({ kind: "gsm14-navigate" });
+  await new Promise((resolve) => setTimeout(resolve, 5000));
+  for (const note of notes) lines.push(`FRAME-NAV ${note}`);
+  lines.push(`FRAME-NAV frame load events in the 5 s after the navigation attempts: ${loads}`);
+  runner.dispose();
+}
+
+async function control(lines: string[]) {
+  try {
+    const response = await fetch("ipc://localhost/plugin%3Aapp%7Cversion?gsm14=C1", { method: "POST", body: "{}", headers: { "Content-Type": "application/json" } });
+    lines.push(`CONTROL C1 (main-window fetch, no key): OK status=${response.status} body=${JSON.stringify((await response.text()).slice(0, 80))}`);
+  } catch (caught) {
+    lines.push(`CONTROL C1 (main-window fetch, no key): ${describe(caught)}`);
+  }
+}
+
+export async function runGsm14Probe(): Promise<void> {
+  const lines: string[] = [];
+  lines.push(`main: location.origin=${window.location.origin} userAgent=${navigator.userAgent}`);
+  lines.push(`main: __TAURI_INTERNALS__=${typeof (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__} webkit.messageHandlers.ipc=${typeof (window as unknown as { webkit?: { messageHandlers?: { ipc?: unknown } } }).webkit?.messageHandlers?.ipc}`);
+  try { await realRuns(lines); } catch (caught) { lines.push(`REAL harness ${describe(caught)}`); }
+  try { await probe(lines); } catch (caught) { lines.push(`PROBE harness ${describe(caught)}`); }
+  await control(lines);
+  await invoke("gsm14_report", { lines });
+}
diff --git a/apps/learnloop-tauri/src/main.tsx b/apps/learnloop-tauri/src/main.tsx
index 9d56cac617..8cdc875688 100644
--- a/apps/learnloop-tauri/src/main.tsx
+++ b/apps/learnloop-tauri/src/main.tsx
@@ -17,3 +17,8 @@ ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
   </React.StrictMode>
 );
 
+
+// G-SM14 rerun probe (scratch branch probe/g-sm14-compartment, never landed).
+setTimeout(() => {
+  void import("./gsm14/gsm14Harness").then((harness) => harness.runGsm14Probe());
+}, 4000);
diff --git a/apps/learnloop-tauri/src/screens/reader/figures/sketch/sketch.worker.ts b/apps/learnloop-tauri/src/screens/reader/figures/sketch/sketch.worker.ts
index 089c3a0534..bae53f9035 100644
--- a/apps/learnloop-tauri/src/screens/reader/figures/sketch/sketch.worker.ts
+++ b/apps/learnloop-tauri/src/screens/reader/figures/sketch/sketch.worker.ts
@@ -11,3 +11,16 @@
 import { startSketchWorker, type WorkerScopeLike } from "./sketchWorkerCore";
 
 startSketchWorker(self as unknown as WorkerScopeLike);
+
+// ---- G-SM14 RERUN PROBE (scratch branch probe/g-sm14-compartment, never landed) ----
+// The frame asks the real sketch Worker (after its normal start-up: engine verified, globals stripped)
+// to try every path; addEventListener is EventTarget's, never stripped.
+import { gsm14Attempts } from "../../../../gsm14/attempts.js";
+(self as unknown as EventTarget).addEventListener("message", (event) => {
+  const data = (event as MessageEvent).data as { gsm14?: unknown } | null;
+  if (!data || typeof data !== "object" || data.gsm14 !== "probe") return;
+  void (gsm14Attempts("W", true) as Promise<string[]>).then(
+    (lines) => (self as unknown as { postMessage(message: unknown): void }).postMessage({ gsm14: "result", lines }),
+    (caught) => (self as unknown as { postMessage(message: unknown): void }).postMessage({ gsm14: "result", lines: [`crashed ${String(caught)}`] }),
+  );
+});
diff --git a/apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.ts b/apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.ts
index 43c3eb676e..1f8d8cd698 100644
--- a/apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.ts
+++ b/apps/learnloop-tauri/src/screens/reader/figures/sketch/sketchCompartment.ts
@@ -95,6 +95,10 @@ export function createSketchCompartment(inputs: CompartmentInputs): WorkerLike {
   };
 
   control.port1.onmessage = (event) => {
+    // ---- G-SM14 RERUN PROBE (scratch branch, never landed): the probe's results and notes.
+    const raw = event.data as { kind?: string; lines?: string[]; line?: string } | null;
+    if (raw && raw.kind === "gsm14-result") { (handle as unknown as { gsm14Result?: (lines: string[]) => void }).gsm14Result?.(raw.lines ?? []); return; }
+    if (raw && raw.kind === "gsm14-note") { (handle as unknown as { gsm14Note?: (line: string) => void }).gsm14Note?.(String(raw.line)); return; }
     const notice = parseFrameNotice(event.data);
     if (!notice || state === "ended") return;  // anything else is dropped
     if (notice.kind === "connected") {
@@ -140,6 +144,8 @@ export function createSketchCompartment(inputs: CompartmentInputs): WorkerLike {
     frame.contentWindow.postMessage({ kind: "connect" }, "*", [control.port2]);
   }, { once: true });
   frame.src = SKETCH_FRAME_PATH;
+  // ---- G-SM14 RERUN PROBE (scratch branch, never landed)
+  Object.assign(handle, { gsm14Send: (message: unknown) => control.port1.postMessage(message), gsm14Frame: frame });
   doc.body.appendChild(frame);
   return handle;
 }
```
