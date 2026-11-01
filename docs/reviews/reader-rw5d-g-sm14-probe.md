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
