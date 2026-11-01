# Reader RW5d P2: the sketch tier (stage record)

- **Spec:** `docs/specs/spec_reader_show_me_figures_v1.md` rev 2 (owner-approved, Q1-Q27 decided). This stage builds phase
  P2 only: the P2 row of §16 and §9 (the sketch tier), with §8.4 (`FigureAuthorOutputV2`), §8.5 (reuse, engine upgrades,
  "not right?") and §6.6 (the sketch on any host).
- **Branch:** `reader/rw5d-p2-sketch` in `learnanything-ad1`, base `5b3f66059`.
- **Migration:** none. P1's `224_figure_requests.sql` carried `tier`, `program_version`, `engine_sha256`,
  `runtime_digest` and `checks_json`.
- **Successor:** none (spec §14: content and display; nothing in scoring, scheduling, projection or serving reads a
  sketch).
- **Kill switch:** `figures.sketch_enabled` (built default on, Q5; **ships off** at landing until G-SM14 passes, see "Landing onto main"). Off, the author's contract, prompt and reuse key are
  RW5b's/P1's byte for byte, no `figure_tier` row is written, and a stored sketch lists as "can't draw this yet".
- **Live calls:** none. Every model call in the tests is a fake (`AuthorFake` answers `("sketch", program, why)`). Python
  outside pytest ran only under `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` and
  `LEARNLOOP_FIGURE_MODELS=off`, and only to build corpora, time the engine and recompute config fingerprints. No vault
  was opened.
- **Downloads:** the three pinned build inputs below (fetched once into `~/.cache/learnloop-build/sketch-engine/`, outside
  the repository, each checked against the SHA-256 its upstream release publishes) and the `wasmtime==50.0.1` wheel via
  `uv lock` (hash in `uv.lock`). Nothing unpinned was downloaded.

## What P2 ships

### The engine (§9.2, §9.3 "Packaging", Q2)

QuickJS-ng compiled to one WebAssembly reactor, `apps/learnloop-tauri/src/screens/reader/figures/sketch/sketch-engine.wasm`
(869,346 bytes, SHA-256 `7fc7671506ec276c1c4e338afafb86b0d1ff3b397f901813b62715d7e274cbfe`), run byte for byte by both
hosts.

- **Build script:** `apps/learnloop-tauri/sketch-engine/build.py`, with the harness `sketch_engine.c` (LearnLoop's own
  code) and `engine.lock.json`. Inputs, each pinned by the digest its GitHub release publishes:
  - `quickjs-amalgam.zip`, QuickJS-ng v0.17.0's own amalgamated source (MIT);
  - `wasi-sysroot-34.0.tar.gz`, wasi-libc headers and static libraries (only `include/wasm32-wasip1/`, `crt1-reactor.o`
    and `libc.a` are extracted);
  - `libclang_rt-34.0.tar.gz`, compiler-rt builtins for wasm32.

  The compiler is the system `clang` 23 with `wasm-ld`. The script refuses another clang major, because it decides the
  bytes. Flags are in the lock file: `-O2 -DNDEBUG -fno-ident`, prefix maps, `--strip-all --stack-first`, a 1 MiB
  shadow stack and `--max-memory` 96 MiB.
- **Reproducible:** `build.py --check` rebuilt the identical digest four times on carson (after each harness change). A
  digest change needs `--update-pin`, then the two other pins (`learnloop.figures.sketch_engine.ENGINE_SHA256`,
  `sketchEngine.ts`'s `ENGINE_SHA256`). Tests keep the three equal.
- **Licences:** `apps/learnloop-tauri/sketch-engine/LICENSES.txt`. It has QuickJS-ng's MIT text and holders (all of the
  amalgam is MIT; its Unicode tables are under the Unicode License v3), wasi-libc (used under MIT), musl's MIT,
  cloudlibc's BSD-2-Clause and dlmalloc's CC0. compiler-rt is Apache-2.0 WITH LLVM-exception; that exception waives the
  notice requirement for embedded object code, and the notice names it anyway.
- **G8:** `.wasm` is not one of the app-asset suffixes, so `tests/test_public_tip_guards.py` gains a narrow allowlist
  (`APP_WASM`). Exactly this one path is allowed, and only beside a tracked notice that names it (new test
  `test_every_tracked_wasm_is_the_listed_engine_with_its_notice`). The file is well under 5 MB.
- **The harness ABI** (`sk_buffer`, `sk_load`, `sk_init`, `sk_step`, `sk_view`, `sk_probes`, `sk_limits`): JSON or
  source text goes in through one buffer, and JSON text or a code-written message comes back. Each `sk_load` starts a
  fresh runtime. The context gets `BaseObjects`, `Eval`, `JSON`, `MapSet` and `TypedArrays` only:
  - never `Date`, `RegExp`, `Proxy`, `Promise`, `WeakRef`, `performance` or a module loader;
  - `Math.random`, `queueMicrotask`, `SharedArrayBuffer` and `Atomics` are deleted;
  - `rand()` is the only randomness: splitmix64, reseeded before every entry point from (seed, phase, step index), so a
    run depends only on the parameters, the seed and the step count, never on how a host chunked its calls (tested).

  **State never leaves the engine.** `init` keeps its result, `step` replaces it, `view` and `probes` read it, and `p` is
  re-parsed for every step so a program can't mutate it across steps.
- **Caps, compiled in** (`sk_limits` reports them; both hosts' constants are tested equal):
  - memory: `SKETCH_MEMORY_BYTES` 64 MiB (`JS_SetMemoryLimit`);
  - work: a deterministic budget in QuickJS interrupt ticks (each tick is 10,000 interrupt polls at calls and loop
    back-edges). `SKETCH_FUEL_PER_CALL` is 16 ticks per entry-point invocation, each step its own call, with the
    interrupt counter reset at each start so the cap is identical in every host;
  - serialization: its own budget, `SKETCH_SERIALIZE_TICKS` 48. Writing a scene at the 40,000-point cap with the
    non-finite-naming replacer is real work, and a getter or `toJSON` left in a result runs under this budget;
  - a JS recursion guard on the shadow stack (192 KiB);
  - output at most 4 MiB.

### The sidecar runner (§9.3)

`src/learnloop/figures/sketch_engine.py` runs the same bytes under `wasmtime` 50.0.1, in-process.

- It refuses a missing artifact, a digest mismatch, or a module importing anything beyond the five WASI functions
  wasi-libc links. Each of those is answered by a deny-all shim: `clock_time_get` ENOSYS; `fd_close`, `fd_fdstat_get` and
  `fd_seek` EBADF; `fd_write` keeps at most 4 KiB of error text.
- Backstops for native work the interpreter can't interrupt (a huge BigInt power): fuel per call (`WASM_FUEL_PER_CALL`),
  a store memory limit (96 MiB), a 1.5 MiB wasm stack (wasmtime caps it below its 2 MiB async stack) and an epoch
  deadline. The deadline uses a per-call `threading.Timer` that is cancelled and joined before the call returns, so the
  thread-leak guard is clean.
- A trap marks the instance broken, and it is never called again.
- Compiled modules are cached per (path, pin) and closed at exit.
- Statuses: `ok`, `error`, `work_cap`, `memory_cap`, `stack`, `no_program`, `output`, `input`.

**Measured (carson, a call at the cap; median of 5).** These are recorded for `SKETCH_FUEL_PER_CALL`:

| Loop at the cap | V8 (Node 26, vitest) | wasmtime (sidecar) |
|---|---|---|
| tight arithmetic | 2.4 ms | 2.4 ms |
| array push | 4.7 ms | 4.7 ms |
| object allocation per iteration | 28.6 ms | 28.6 ms |

At 48 ticks, the first value tried, the same three took 8.2 / 7.5 / 56.7 ms (V8) and 6.6 / 13.4 / 85.5 ms (wasmtime).
16 ticks brings a typical call at the cap inside one frame (16 ms) and the allocation-heavy worst case to about two.
That budget is still about 160,000 loop iterations per call. The spec's sizing examples fit easily: hundreds of walkers,
a 64×64 automaton, a few thousand Monte Carlo samples. The good corpus verifies in 0.01-0.2 s per sketch. The desktop's
WebKitGTK (JavaScriptCore) was not timed: no webview was run in this stage.

### The desktop runtime (§9.3, §6.6)

- `sketchEngine.ts` is the engine host: plain TypeScript with no DOM. It checks the pin with Web Crypto, falling back to
  a pure-TS SHA-256 in an insecure context, refuses extra imports and provides the same deny-all shim.
- `sketch.worker.ts` is the dedicated Worker. It fetches the tracked wasm through Vite's `?url`, which `frontend:build`
  emits as an asset, verifies and instantiates it, then removes its own `fetch`, `XMLHttpRequest`, `WebSocket`,
  `importScripts`, `indexedDB` and `caches`. From then on it only relays `load`, `init`, `step` and `read`.
- `sketchRunner.ts` has `workerRunner` (the app), `hostRunner` (tests) and `withWatchdog`. The watchdog allows
  `SKETCH_FRAME_MS × SKETCH_WATCHDOG_FRAMES` = 480 ms per call; past that, the Worker is terminated and the sketch shows
  *paused — this simulation is too slow here · step ▸*. The CSP is unchanged by P2. **Corrected in fix round 4**
  (the independent sandbox review): this line used to say `connect-src 'self'`, which is incomplete. The app's CSP
  (`src-tauri/tauri.conf.json`) is `script-src 'self' 'wasm-unsafe-eval'`, `worker-src 'self' blob:` and
  `connect-src 'self' ipc: http://ipc.localhost llpdf: http://llpdf.localhost llmedia: http://llmedia.localhost`. A
  same-origin Worker therefore inherits a `connect-src` that names the IPC endpoints. The program inside the engine
  can't reach any of this (it has no bindings), but the Worker itself is not an opaque-origin compartment. See G-SM14
  under the sandbox review and the open points.

### Schemas and both validators (§9.1)

`src/learnloop/figures/sketch.py` defines:

- **`SketchProgramV1`**: strict keys and the caps. Parameters are validated as `ifs-v1`'s; probes, bindings and
  predictions must name declared things; every claim expression is parsed by the grammar with its names resolved.
- **`scene_problems` / `probe_problems`**: closed element kinds, a closed style palette, finite numbers everywhere, ids,
  and the element, point and cell caps. Nothing in a Scene can express HTML, CSS, a URL or an image.

`sketchScene.ts` is the desktop's half. `sketchSceneCorpus.json`, generated by `tests/sketch_scene_corpus.py`, holds 27
scene and 6 probe cases with the sidecar's exact problem messages. vitest asserts the TS validator returns the same
messages, case for case.

### Verification, steps 1-5 (§9.5)

`src/learnloop/figures/sketch_verify.py`:

1. Structure (the schema, then the code loads and defines `init`, `view`, `probes`, and `step` with a clock).
2. Runs on RW5a's parameter grid and, with a clock, at 9 times from 0 to `t_max`; every scene and probe is validated.
3. Deterministic: a second run in a fresh engine, the grid reversed, with extra `view`/`probes` reads, must match as
   text.
   *(Fix round 4 changed steps 2 and 3: every run is a freshly loaded program reading one schedule, and the report
   carries per-read digests the desktop compares. See the codex-review record's "Sandbox review (Astra)".)*
4. Bindings hold exactly: a bound element's coordinates equal its probe's values.
5. Claims are checked by the grammar's Python evaluator:
   - `equals` within 1e-9 relative (scalar, series over `var`, or pairs y over x);
   - `follows` against the grammar's RK4 at the path's step, with the tolerance `ODE_SAFETY` × the half-step Richardson
     difference plus 1e-9;
   - `invariant` as RW5a's property checks;
   - `distribution` within z·SE, z for `MC_FALSE_ALARM` 1e-6 two-sided.

Outcomes:

- `failed`: never shown; the second author attempt gets code's problems.
- `illustrative` with check lines: each check names the bound elements (ids) or the probe, the stated equation as the
  grammar parsed it (marked AI-stated) and the settings tested. Drawn elements no check covers are named as
  *not covered*.
- No claims at all: *nothing in it checked*.

The random walk gives exactly the spec's example: "at 27 tested settings", with the walkers *not covered*. Predictions
(`direction`, `choice`) are decided by code in the engine; undecidable ones are dropped.

### The author, the receipt, the service (§8.4, §8.5)

- **`FigureAuthorOutputV2`** (`status`, `spec_json`, `sketch_json`, `why_not_spec`, `unsupported_*`) runs under
  `+sketch-v1` (after any `+show-me-v1`). Its instructions replace RW5a's status sentence with the spec's preference
  sentence ("If the declarative spec can express it, write the spec. Write a sketch only for what it cannot express…")
  and add `SKETCH_TEXT`, the program's contract with the caps substituted.
  - Off: `author_instructions()` is `AUTHOR_INSTRUCTIONS`, the output model is V1, and `request_hash` without
    `sketch=True` is P1's (tested).
  - The tier is offered only when the switch is on and the engine is ready on this machine (`sketch_enabled` = switch +
    `engine_ready()`, §7.2).
- **Receipts:** every build with the tier on appends a `figure_tier` judgment beside `figure_verified`: judge `llm`,
  verdict `spec | sketch | unsupported | invalid`, rationale `why_not_spec` or the unsupported reason, plus the model and
  prompt version.
- **Storage:** a sketch is stored as `tier` sketch, `spec_version` `sketch-v1`, the canonical program in `spec_json`,
  `kind` illustrative, `engine_sha256`, `runtime_digest` `sketch-engine-v1:<sha>` and `checks_json`.
- **Reuse:** the key gains `{program_version, engine_sha256}`, and lookups read both spec versions.
  - Flipping the panels or the tier reuses a shown figure that can be drawn now; it is never paid for again.
  - `figure_requests.tiers_allowed_json` records `["grammar","sketch"]`.
- **Engine upgrades** (G-SM13): a shown sketch whose `engine_sha256` differs is verified again by code before it is
  shown (`sketch_rechecked`, remembered per (figure, engine) in-process, the row never rewritten). If it now fails, it
  shows *couldn't run under this version · rebuild*, failed, with no program sent, and it can't be predicted on.
- **"Not right?"** sends the earlier program as `earlier_version.sketch_json` with the note. The desktop prefills the
  note on an error: *this simulation hit an error at these settings: a=0.4, b=0.8 (init: Error: blew up)*. With the tier
  off, revising or predicting on a sketch is refused (`sketch_disabled`).
- **Grounding none:** a sketch quotes nothing (`_ungrounded_sketch`) and is labelled *AI-written simulation · sandboxed
  · not from your books*.

### The renderer (§6.6, §9.1)

- **`SketchScene.tsx`** draws the closed elements as SVG primitives from their fields. Text is a text node in the model's
  voice (italic, inside the frame); colours come from the closed palette; heat cells are rects. A handle is a draggable
  circle bound to parameters, which the host clamps and steps.
- **`SketchFigure.tsx`** provides:
  - sliders and numeric fields;
  - *▸ play* on the program's clock, or *step ▸* under reduced motion; nothing moves until pressed;
  - *↺ restart*, and *↻ new sample* for seeded programs (a host-drawn 32-bit seed);
  - the values table (`t`) of the declared probes;
  - *ⓘ how this runs*, the paused and error states, the prediction block, "not right?" and the code-owned check lines
    with *not covered*.

  Any parameter or seed change restarts the run, so what is drawn is always "init, then n steps", the shape verification
  covered.
- **`FigureInline.tsx`** renders a `tier: "sketch"` figure with `SketchFigure`. Its collapsed line shows the sketch badge
  and "N checks, listed inside".

### Other changes

- `figures.sketch_enabled` (`config/schema.py`).
- The 29 defaults fingerprints were recomputed (`config/template.py`; every version moves only because the effective
  config gains the key).
- Registry: a `_ConfigRule` for the switch, and the 28 new module constants, all `keep` (caps, tolerances, sandbox
  limits) or identities (two WASI errno values, `VERIFY_SEED`), in three new inventory modules.
- Prompt contract `figures.sketch` (only while on).
- Client events `sketch_paused` and `sketch_error`, with field `error_kind` (kinds, never text).
- The report's `figures.tiers` block (only while on): built by tier and verification, verdicts, `why_not_spec` reasons
  counted, pauses and errors.
- `pyproject.toml`: `wasmtime==50.0.1`.
- `tests/figure_fixtures.py`: `build_figure_vault(sketch=False)`. RW5a/b's and P1's tests run with the tier off, the
  RW5b-byte-for-byte path they pin. `AuthorFake` fills V2's fields and answers sketches.

## Deviations and interpretations (for the reviewer)

1. **`span_id`, not `span_key`.** `assumptions` and `source_claims` quote with `span_id`, as `ifs-v1` and P1's retrieved
   passages (`extraction_id:span_id`) already do. The quote check is RW5a's.
2. **G-SM10's "an unbound drawn path".** An unbound element is *not covered* by design (§9.5), not refused. The planted
   cases refused at step 4 are "a bound path drawn off its probe" and "a binding to an element never drawn". The unbound
   case is tested as *not covered*.
3. **`choice` predictions** observe a series probe with one label per entry; the answer is the largest entry, with ties
   dropped. A parameter-change prediction compares at the first step without a clock and at `t_max` with one; `run_to`
   compares step 0 with the step at that time.
4. **Play** drives the clock only. A parameter's `animate` flag isn't swept for sketches (the grammar's sweep stays the
   grammar's).
5. **Serialization budget** (48 ticks), separate from the call budget. It wasn't in the spec's list; it is needed so a
   scene at the point cap can be written.
6. **The wording rule** (§9.5's "schema walk"). The only model-written words that reach the code-owned lines are
   identifiers: parameter, probe and variable names and element ids. They may not contain LearnLoop's check words
   (`check`, `verif`, `learnloop`, `sandbox`, `book`, `tested`, `proof`, `correct`). This is a code-owned display rule,
   not a judgment.
7. **Hidden state across calls** is caught by step 3's reversed, extra-read second run, not prevented. See the review
   below.

## Sandbox review (§9.4; "find a way for a sketch to reach anything but its return value, or to make the frame claim a check that didn't run")

The adversary is the author's output: a model following injected text, or a bad program. This review was done in this
stage. The spec also asks for the independent Codex (or Opus) review before merge, and the workflow runs that next.

| Path tried | What stops it | Evidence |
|---|---|---|
| Reach the page, the app, IPC, network, storage or timers from the program (`fetch`, `XMLHttpRequest`, `WebSocket`, `importScripts`, `postMessage`, `window`, `document`, `__TAURI_INTERNALS__`, `ipc`, `webkit`, `WebAssembly`, `setTimeout`, `queueMicrotask`, `Promise`, `Proxy`, `RegExp`, `Date`, `performance`, `crypto`, `console`, `std`, `os`, …: 42 names) | The interpreter has no host bindings. The context is built raw with five intrinsics; four globals are deleted. The global object holds only the program and `rand`. | `test_nothing_outside_the_interpreter_is_reachable`; hostile corpus cases 1-2 in both hosts |
| `import()`, a static `import`, `new Function`, `eval` to find a wider realm | No module loader and no Promise: `import()` throws and a module source fails to load. `eval` and `Function` return the same sealed global. | `test_dynamic_import_and_module_loading_fail_inside_the_engine`; corpus "eval and Function stay sealed" |
| Reach the Worker's JS from the program | It is a different realm: wasm linear memory, with no imports but the shim. The Worker also drops its own network and import globals after loading. | design; `sketch.worker.ts` |
| The shim as a channel (files, clock, randomness, environment) | Five functions: EBADF, ENOSYS, and `fd_write` as a 4 KiB text sink. A module importing anything else is refused before instantiation, in both hosts. | `test_the_module_imports_only_what_the_deny_all_shim_answers`; `SketchEngineHost.create` |
| Prototype pollution of the host's objects | Results cross as JSON text, `JSON.parse`d in each host (`__proto__` stays an own key there), then validated field by field. Unknown keys are refused, and nothing is `Object.assign`ed from engine data. | `test_prototype_pollution_stays_inside_the_engine`; vitest "parses a polluted result as plain data". **Finding:** a JSON-module import turns `"__proto__"` into a prototype, so the vitest corpus is read with `?raw` + `JSON.parse`. Engine data must never be imported as a module or merged with `Object.assign`. |
| Infinite loops in each entry point; a loop that catches the interrupt | The uncatchable interrupt fires at the deterministic tick budget, per call, in both hosts. Getters and `toJSON` run under the serialization budget. | `test_an_endless_loop_in_any_entry_point_hits_the_work_cap` ×4; corpus "an endless loop that catches"; `test_getters_and_tojson_run_under_a_budget` |
| Native work the interpreter can't interrupt (BigInt power, huge typed arrays) | Memory cap. In the sidecar, wasmtime fuel and an epoch deadline (the instance is then discarded); in the desktop, the 480 ms watchdog terminates the Worker. | `test_a_trapped_instance_is_never_called_again`; vitest "pauses a sketch whose call outlives the watchdog" |
| Deep recursion | The shadow-stack guard raises a status `stack` error before the native wasm stack is exhausted (wasmtime 1.5 MiB; V8 default). | `test_memory_and_recursion_have_their_own_statuses`; corpus "deep recursion" |
| Memory bombs, giant strings | `JS_SetMemoryLimit` 64 MiB, then the store limit (96 MiB, wasm `--max-memory`). | corpus "a memory bomb"; `test_a_giant_string_hits_the_memory_cap` |
| Oversized scenes | Element, point and cell caps in both validators, the 4 MiB output cap and the serialization budget. | `test_an_oversized_result_is_refused_by_the_engine_or_the_validator`; the cap tests in both languages |
| NaN and Infinity anywhere | They cross as the strings `"NaN"`, `"Infinity"` and `"-Infinity"`, and both validators name them. Steps 2 and 4 refuse them; the desktop shows the error state. | corpus "NaN and Infinity everywhere"; planted "NaN at one grid corner"; vitest "refuses to draw a scene the validator rejects" |
| Markup, links, images or styles in a scene | No element kind or key can express them (unknown keys are refused), text is a React text node, and colours come from a closed palette. | scene corpus cases ("markup at the top level", "an image element", "a link on text", "an event in a style", "axes with markup keys"); vitest "draws text as text, never as markup" |
| Text imitating LearnLoop's badge | Text draws inside the frame, in italics, in the model's voice. The badge and check lines are worded by code from closed fields and identifiers; identifiers can't carry the check words. | `test_text_that_imitates_a_badge_never_reaches_the_check_lines`; wording-rule cases in both validators |
| A claimed check that didn't run, or speaks for more than it checked | Check lines come from verification's own records. A claim over an unbound probe names no element, and every drawn element it doesn't cover is listed. A failed claim is never shown. Every sketch says *not checked against the book*. | `test_a_tautological_claim_speaks_only_for_what_it_checks`; planted "claim off by a constant" |
| A different engine (tampered or swapped) | The SHA-256 pin is checked in both hosts before instantiation; the build script pins its inputs. | `test_a_digest_mismatch_refuses_to_load`; vitest "refuses an engine whose digest is not the pin" |
| Nondeterminism between verifier and desktop | One engine, the same bytes; seeding by (seed, phase, step); NaN canonicalization in wasmtime. The parity corpus is text-identical in V8 and wasmtime. | `test_the_parity_corpus_is_what_the_pinned_engine_returns`; `sketchParity.test.ts` (5 cases) |

**Residuals, stated honestly:**

- **(a) Hidden state.** A program can keep top-level `let` state across calls within one load. Step 3 catches
  order-dependence along the grid and in extra reads, but not a dependence that happens to agree in both runs.
  **Superseded in fix round 4:** the independent review turned this residual into a false check (a program counting
  its own starts). Every `init()` now runs on a freshly loaded program in both hosts, every run reads one schedule,
  and the desktop compares the verifier's digests. See the codex-review record's "Sandbox review (Astra)".
- **(b) Engine escape.** Escaping needs a bug in QuickJS's interpreter that corrupts wasm linear memory, then a bug in
  WebKit's or wasmtime's WebAssembly isolation. That is not realistic for model output (the proportionate bar).
- **(c) G-SM14 not run.** It needs the real desktop webview on Linux: can a request to the IPC endpoint be made from
  inside the sketch Worker? The program can't reach the Worker's globals at all. The gate is about the Worker itself,
  and the Worker drops its network globals after load. It still has to be run in the real webview before merge; if Tauri
  doesn't refuse it, the Worker moves into an opaque-origin frame, as the spec says. The independent review's
  conclusions and the fallback recipe are under open point 1.
- **(d) A correct-by-its-own-claims sketch of a wrong idea.** As for any AI explanation: labelled AI-written, with
  "not right?".

## Gate (this step; the full suite runs once at landing)

Every pytest, vitest, npm and cargo command ran in `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G`, pytest at `-n 6` at most, and vitest at `--maxWorkers=4`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok (adds `wasmtime==50.0.1`) |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| `build.py --check` (reproducibility) | reproduced `7fc76715…74cbfe` |
| New: `tests/test_sketch_engine.py`, `test_sketch_verify.py`, `test_sketch_hostile.py`, `test_sketch_parity.py`, `test_sketch_scene_parity.py`, `test_sketch_service.py` | 102 passed (part of the final run below) |
| Final consolidated run: the 6 new files; every `test_figure_*` / `test_figures_*` file (RW5a/b and P1); architecture, registry audit, public tip guards (G8, +1 test), sqlite file copies; reader activity, salience firewall, reader cues (+ CLI report), reader intent, reader tutor offers, library ask, compare-sources keep (the report and event modules); desktop RPC contract, mobile allowlist, CLI help snapshot, activity contract extensions, sidecar registry, serializer snapshot, coordinated migrations, table roles, tracked fixture databases | 6653 passed |
| Every test that pins the defaults fingerprints (32 files: config refactor, the mvp0.10-mvp0.24 upgrade files, successor and landing files, plan determinism, CA2, cold retry, ...) | 683 passed, 12 skipped, 3 xfailed |
| Earlier iterations (before the final changes) | 6380 passed and 2 failed (an architecture token rule on the recheck, a hostile case stopped by the work cap first), both fixed; contract set 392 passed / 3 skipped; 453 legacy figure tests passed with the fixture's tier off |
| `-m durability` | not run: no migration and no DB/connection code changed |
| `npm install`, `npm run typecheck` | ok, 0 errors |
| `npx vitest run --maxWorkers=4 src/screens/reader/figures src/screens/reader/figuresWithReadingPath.test.tsx src/screens/attentionBudget.test.tsx` | 13 files, 322 passed (new: `sketch/sketchParity.test.ts` 23, `sketch/sketchScene.test.ts` 35, `sketch/SketchFigure.test.tsx` 11) |
| `npm run frontend:build` | built; emits `sketch.worker-*.js` and `sketch-engine-*.wasm` |
| `cargo check` | not run: nothing under `src-tauri` changed |
| DB reference scripts | not run: no schema change |

## Open points for the landing and the owner

1. **G-SM14 (merge gate):** run the IPC probe from inside the sketch Worker in the real desktop webview on Linux. If it
   isn't refused, move the Worker into an opaque-origin frame before P2 ships (§9.4, §16). The independent sandbox
   review (gpt-6-astra, fix round 4) left G-SM14 **unverified**, with these conclusions:
   - A model sketch has no route to the Worker's globals without breaking the interpreter/wasm boundary.
   - The Worker is not an opaque-origin compartment: the app CSP explicitly permits `ipc:` and `http://ipc.localhost`
     (the corrected description above).
   - Locally cached, Cargo-locked Tauri 2.11.2 / Wry 0.55.1 source supports a **low likelihood** of a successful IPC
     call from this Worker: the normal bridge is window-based, and an invocation needs the initialization key, which
     nothing in the Worker protocol transfers.
   - Linux frame isolation still needs the real probe. Wry's WebKitGTK message handler attributes messages by the
     webview's URI, so a frame-URL check alone should not be assumed sufficient.
   - **The fallback recipe**, if the probe is not refused: an iframe with `sandbox="allow-scripts"` and **without**
     `allow-same-origin`, a restrictive CSP in it including `connect-src 'none'`, and the Worker created **inside**
     that frame. The pinned wasm bytes are transferred to it over a narrowly validated private message channel (the
     fix-round-4 protocol validation, `sketchProtocol.ts`, is the shape); generic IPC is never forwarded. Probe the
     native WebKit message handlers (`window.webkit.messageHandlers`) as well as fetch-based IPC; if those remain
     reachable from the frame, use a separate webview with no capabilities.
   The review did not count the missing probe alone as a demonstrated escape. It remains the spec's outstanding merge
   gate.
8. **Toolchain pinning (follow-up, Astra finding 4, Low).** `build.py` pins every download by digest and refuses an
   output whose digest differs from `engine.lock.json`, but it checks only Clang's major version and does not pin
   `wasm-ld`. Another toolchain can produce different bytes, and the ordinary build then refuses them (it never ships
   them). Pin the exact compiler and linker distribution, or a build image, in a follow-up.
2. **B3:** `src-tauri` is unchanged, so `cargo check` wasn't run. The spec lists "B3 re-confirmed" under P2's needs: the
   landing gate's `cargo check` re-confirms it.
3. **Owner checkpoint:** the sandbox review (above, plus the Codex review) and five real sketches from the owner's
   subjects (probability, linear algebra, ML). No real sketch was built here: the stage ran with no live calls.
4. **The tracked binary.** The spec (§9.3, Q2) tracks the artifact under the app's assets. It is committed with its
   notice, its build script and a three-way pin, with G8 narrowed to that one path. The alternative is a build-only
   artifact, with tests skipping when it is absent and the desktop needing a build step. That would weaken the "no
   silent skips" gates, so it was not taken; the orchestrator may decide otherwise.
5. **The build downloads a 119 MB sysroot tarball** (pinned by digest, cached outside the repository) to extract about
   1 MB from it. Only a rebuild needs it; tests and the app use the tracked artifact.
6. **Cross-spec notes (§20):** to record at landing. In `spec_mcp_frontend_v1.md` §9.3, add Q13's one-line amendment
   (the sealed verifier is "the sandbox runs it"). In `ux_reader_workbench_v1.md` §4.7 / §11.2, the label becomes
   *AI-written simulation · sandboxed*.
7. **The engine digest is in the reuse key** (§8.5). An engine upgrade therefore makes a repeated request build again
   (paid), while stored sketches are re-verified for listing.

## Landing onto main (2026-10-31)

- **Main at landing:** `6a8256517` (Curriculum C0b; includes Reader CA3, CA4, CA5a). Reader CA5, CA6 and RW6b part 1
  (mvp-0.39, migration 227) were landing in parallel and had not reached main when this landing finished.
- **No migration, no successor.** Owner copies stay at mvp-0.35 → `upgrade --to mvp-0.38`, as before this stage.

### The default-off decision (orchestrator, 2026-10-31)

The spec's merge gate **G-SM14** (an IPC probe from inside the sketch Worker in the real Linux Tauri webview) has **not**
been run: it needs a GUI window and the owner's permission, and this landing launched no app or window. So P2 **ships
off until G-SM14 passes; the owner turns it on with `figures.sketch_enabled = true` after running the probe (recipe
below).**

- `FiguresConfig.sketch_enabled` defaults to `false` (`config/schema.py`, docstring says why). The template is
  decision-only and never carried the key, so no template text changed. The registry entry (structural, operational
  kill switch) is kept unchanged.
- Every defaults snapshot moved only by the house recompute (the effective config gains `figures.sketch_enabled =
  false` at every version). Nothing else in earlier versions' snapshots was rewritten.
- "Off" is exactly what the stage built for off: the author's contract, prompt and reuse key are RW5b's/P1's byte for
  byte, no `figure_tier` row is written, a stored sketch lists as *can't draw this yet*, and the prompt contract has no
  `figures.sketch` key (main's contract byte for byte).

### G-SM14 probe recipe (for the owner or a permitted agent)

**What it answers.** Can code running inside the sketch Worker, in the real desktop webview on Linux (WebKitGTK via
Wry), reach the app's IPC? The program inside the engine has no bindings at all; this gate is about the Worker itself,
which is a same-origin Worker under the app CSP (`connect-src` names `ipc:` and `http://ipc.localhost`).

**How to run it** (a dev build; nothing is committed):
1. In a scratch branch, add a debug-only message to `sketch.worker.ts` (for example `{"kind": "probe"}`), handled
   **after** the Worker's normal start-up (after it has verified the wasm and deleted `fetch`, `XMLHttpRequest`,
   `WebSocket`, `importScripts`, `indexedDB` and `caches`). The handler tries, each in `try/catch`, and posts back one
   line per attempt (`ok` / the error name):
   - `fetch("ipc://localhost/plugin:app|ping")` and `fetch("http://ipc.localhost/plugin:app|ping", {method: "POST"})`
     through any surviving reference (`self.fetch`, `globalThis.fetch`, `Object.getPrototypeOf(self).fetch`,
     `WorkerGlobalScope.prototype.fetch`);
   - `new XMLHttpRequest()` to both URLs, and `new WebSocket("ws://ipc.localhost")`;
   - `self.__TAURI_INTERNALS__`, `self.__TAURI__`, `self.ipc`, `self.webkit?.messageHandlers` (each: present or
     absent);
   - `new Worker(...)`/`importScripts(...)` of a `blob:` URL that calls `fetch` to the IPC URL (a nested context with
     fresh globals).
2. Wire a dev-only button (or the devtools console) to send the probe to a live sketch Worker, run
   `LEARNLOOP_VAULT=<a throwaway vault> npm run dev` on Linux, open a figure with a sketch so the Worker is running,
   send the probe, and read the lines. Also run the same attempts once from the devtools console of the Worker itself.
3. Keep a log of the Rust side (`RUST_LOG=debug`) to see whether any IPC request reached a command handler.

**Success (G-SM14 passes):** every attempt fails (`TypeError`/`NetworkError`/CSP refusal or "absent"), and no IPC request
reaches the Rust side. Record the lines in this stage record, then set `figures.sketch_enabled = true`.

**Failure:** any attempt reaches an IPC handler (even one that then refuses for lack of the initialization key), or a
Tauri/WebKit handler is reachable. Then P2 stays off and the Worker moves into an opaque-origin compartment before it is
turned on (spec §9.4, §16), per the independent (Astra) review's **fallback recipe**:
- an iframe with `sandbox="allow-scripts"` and **without** `allow-same-origin`, with a restrictive CSP inside it,
  including `connect-src 'none'`, and the Worker created **inside** that frame;
- the pinned wasm bytes transferred to it over a narrowly validated private message channel (the shape of
  `sketchProtocol.ts`'s fix-round-4 validation); generic IPC is never forwarded;
- probe the native WebKit message handlers (`window.webkit.messageHandlers`) from the frame as well as fetch-based IPC
  (Wry's WebKitGTK handler attributes messages by the webview's URI, so a frame-URL check alone is not assumed
  sufficient); if those remain reachable from the frame, use a separate webview with no capabilities.
- Then rerun this probe from inside the new compartment.

### Commits and conflicts

| Commit | What |
|---|---|
| `66387ad86` | `--no-ff` merge of `6a8256517`. **Conflicts:** `config/template.py` only: every default snapshot (mvp-0.9 … mvp-0.38) keeps main's CA5a/CA3/CA4/C0b notes and P2's note. **All 29 fingerprints** recomputed with `defaults_fingerprint_for_version` (template `.pyc` cleared before and after; a recheck found 0 mismatches), with `sketch_enabled` already `false`; dropping `figures.sketch_enabled` from each version's effective config reproduces main's hash at **every** version (29/29). **Auto-merged:** `params/parameter_registry.py` (both sides' rules), `config/schema.py`, `api/dto.ts`, `tests/test_figures_switch_off.py` (CA3/CA4's contract pops beside P2's), `tests/test_public_tip_guards.py` (G8: P2's one-path wasm allowance beside main's changes). Main's head fixture move to `migration_head_228` needed nothing here (P2 has no migration and names no head path). Same commit: the default flip. |
| `3c6a83f16` | Tests for the shipped default (below). |
| `1c07df896` | DB/config reference regenerated; `ux_reader_workbench_v1.md` cross-spec notes (§20). |
| `f9eeba937` | This record's header: the kill switch ships off. The full suite ran at this tip. |
| (next) | This landing section. |

### Interactions

- **(i) Off, the shipped default = main.**
  - `test_figures_switch_off::test_figures_on_adds_only_its_key_and_its_action` now pins that with figures on and the
    sketch tier at its default, the contract's `figures` is main's `{predictions, region, revisions, offers, showMe}`
    (no `sketch` key). New `test_sketch_on_adds_only_its_flag`: turned on, the contract gains `figures.sketch = true`
    and nothing else.
  - New `test_sketch_service::test_the_shipped_default_is_off_and_never_loads_the_engine`: a vault that never set
    the key gets RW5b's contract, no `figure_tier` row, and `engine_ready`/`_compile` are never called (both patched
    to raise). New `test_sidecar_start_imports_neither_wasmtime_nor_the_engine` (a subprocess: importing the sidecar
    server and registry loads neither `wasmtime` nor `sketch_engine`).
  - **Fail-first:** with the schema default put back to `true`, the shipped-default test and the contract test fail;
    with `false` all pass.
  - The stage's own off tests (contract, prompt and reuse key byte for byte; stored sketch lists as *can't draw this
    yet*; revise/predict refuse `sketch_disabled`) pass unchanged.
  - Against main's own code on owner copies (smoke below): the prompt contract and `reader.figures` for every
    extraction are byte-identical, and no `wasmtime`/engine library is mapped into the sidecar process.
- **(ii) On (tests only): never "checked".** Code forces a sketch's `kind` to `illustrative` (`service.py`
  `_store_sketch`), and its label is the code-owned `SKETCH_LABEL` *AI-written simulation · sandboxed · not checked
  against the book* (`test_a_sketch_answer_is_verified_stored_and_shown_with_its_check_lines`; `SketchFigure.test.tsx`
  pins the badge and *(drawn, not checked)*). RW5c's checked label is unbuilt and nothing in P2 claims it.
- **(iii) Reader surfaces.** The whole vitest (234 files) passes on the merge, including CA3's compare scope, CA4's
  table by point, CA5a's find-section and the figure components (the inline slot, `figuresWithReadingPath`). CA5 (the
  rest) and CA6 were not on main yet: when they land after this, their landing reruns the whole vitest over P2's figure
  components.

### Regeneration

- `db_generate_reference.py` (433 notes rewritten, mostly the source-commit stamp; `figures.sketch_enabled` now
  `false`), the two prose counts moved to **1077** effective leaves (P2's key on main's 1076); `db_validate_reference.py`
  **errors []**; `validate_vault.py` passes (1166 notes).
- CLI help, RPC/serializer pins and the mobile allowlist needed no change (their tests pass on the merge).
- §20 cross-spec notes recorded: `ux_reader_workbench_v1.md` §4.7 gains the sketch badge row, §11.2's label becomes
  *AI-written simulation · sandboxed* (both say it ships off until G-SM14). `spec_mcp_frontend_v1.md` §9.3 already
  carries the Q13 amendment.

### Gate (`env -i` with empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR`; logs in `fixtures-local/landing/logs/`)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` (wasmtime 50.0.1 from the lock); `lint-imports --no-cache` | **36 kept**, 0 broken |
| `sketch-engine/build.py --check` (inputs already cached; nothing downloaded) | reproduced `7fc76715…74cbfe` |
| After the merge, targeted contract run (switch-off pins, sketch service and sandbox review, config refactor (fingerprints), vault template, CLI help, serializer snapshot, registry audit, public-tip guards, mobile allowlist; `-n 6`, 5G) | 429 passed, 1 failed (`test_figures_on_adds_only_its_key_and_its_action`: the default flip; updated, see interactions (i)); then 9/9 and the two new shipped-default tests pass |
| **Full suite** at `f9eeba937` (`flock`, 10G/2G scope, `pytest -n 8 --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml`) | **22,708 passed, 0 failed**, 89 skipped, 47 xfailed. pytest 2,066.2 s (34:26); wall **34 min 29 s** after a 27 min 27 s wait for the lock. No flake reruns were needed |
| Durability (`-m durability`, 5G, `-n 6`) | **176 passed**, 1 skipped (64.1 s; wall 65 s) |
| Owner lane (`-m owner_vaults`, 5G, `-n 6`; fresh backup-API copies of `fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}` in `fixtures-local/owner-lane-rw5d/`) | 83 passed, **2 failed**, 4 skipped (61.7 s; wall 62 s). The failures are exactly the expected `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies[arxiv_v2]`; the skips are the vaults with no copy |
| Frontend (`apps/learnloop-tauri`) | `npm install` ok (run once outside the 5G scope by mistake; an install, no tests); `npm run typecheck` clean (14 s); whole vitest (`--maxWorkers=4`, 5G): **234 files, 2152 passed** (57.8 s; wall 58 s); `npm run frontend:build` ok (emits `sketch.worker-*.js` and `sketch-engine-*.wasm`, 869.39 kB); `cargo check --manifest-path src-tauri/Cargo.toml` ok (B3 re-confirmed; `src-tauri` unchanged by P2) |

### Smoke on owner copies

- Fresh backup-API copies of `fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}`, twice (one
  set for the branch, one for main's code from `git archive 6a8256517 src migrations`), in `fixtures-local/smoke-rw5d/run2/`.
  `env -i`, AI base URLs at `127.0.0.1:9`, `LEARNLOOP_FIGURE_MODELS=off`, `LEARNLOOP_COVERAGE_MODELS=off`; the sidecar
  ran as a real process under audit hooks refusing non-loopback sockets and process starts (**they logged nothing**).
  Counts and digests only. Driver: `fixtures-local/landing/smoke_rw5d/smoke.py`.
- **Upgrade:** `mvp-0.35 -> mvp-0.38` (rc 0) and `rebuild-derived-state` (rc 0) on both sides; branch and main copies
  have **identical table counts** (no migration in P2); no table lost rows except arxiv_v2's FTS5 internals
  (`source_block_fts_data`/`_idx`, as in every landing); integrity ok.
- **Figures with the tier off:** the copies hold **0 stored figures** (so "unchanged" is 0 → 0, row digest
  unchanged). `reader.prompt_contract` plus `reader.figures` for every extraction: **5/5, 5/5, 13/13 byte-identical
  to main's code**; the contract's figure flags are main's (no `sketch`). No `wasmtime` or engine library was mapped into
  the sidecar process after the calls.
- **`rebuild --shadow`: 0/0/0** on all three, after the upgrade and at the end.
- **Receipts:** **0** `model_call_receipts` rows added (0 real, 0 fake). Spend $0. Nothing under `~/learnloop-vaults`,
  `~/learnloop-retired` or `~/learnloop-books` was opened or listed.

### Owner notes

- **Turning it on:** after G-SM14 passes (recipe above), set `[figures] sketch_enabled = true` in the vault's
  `learnloop.toml`. With the tier on, the author may answer with a sketch; "show me" and *make this explorable* then
  build sketches where the grammar can't, labelled *AI-written simulation · sandboxed · not checked against the book*.
- **The committed engine:** `apps/learnloop-tauri/src/screens/reader/figures/sketch/sketch-engine.wasm`, **869 KB**
  (869,392 bytes), QuickJS-ng 0.17.0 compiled to wasm32, with its notices in
  `apps/learnloop-tauri/sketch-engine/LICENSES.txt` (QuickJS-ng, MIT; wasi-libc from wasi-sdk 34; compiler-rt builtins
  from LLVM 23.1.0) and a three-way pin (`engine.lock.json`, the Python and TS constants). G8 allows exactly that one
  path.
- **Rebuilding it** (`build.py`, or `build.py --check`) needs a **119 MB** pinned wasi-sysroot download (cached under
  `~/.cache/learnloop-build/sketch-engine/`) plus a local Clang and `wasm-ld`; tests and the app use the tracked
  artifact. `--check` reproduced the pinned digest here from the cache.

### Open items

1. **G-SM14** (above): the merge gate the spec names; the tier stays off until it passes.
2. **Toolchain pinning:** `build.py` checks only Clang's major version and does not pin `wasm-ld`; pin the exact
   compiler/linker distribution or a build image.
3. **Verification read cost:** about 110 engine reads per grid point (the one read schedule shared by verification,
   grading and playback); fine at today's grids, worth watching if grids grow.
4. **Digests cover samples and graded steps** only; reads outside them are not compared by the desktop.
5. **Withdrawal is per session, not recorded:** when the desktop's digests differ from the verifier's, the checks are
   withdrawn for that session but nothing is written.
6. **Stricter bindings:** the Worker protocol and shim could be narrowed further (the review's follow-up list).
7. **Owner checkpoint:** five real sketches from the owner's subjects (probability, linear algebra, ML), after the tier
   is on; none was built here (no live calls).
