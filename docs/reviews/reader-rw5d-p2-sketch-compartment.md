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
  both lists, including every Referer the first probe saw. *Corrected by the Codex review (F1):* page script can't
  set `Origin` or `Referer` as headers, but Fetch lets a context omit its Referer (`referrer: ""`) or name any
  same-origin URL instead. The guard now also refuses a missing Origin or Referer (the app's document sent both on
  every call in both G-SM14 runs), an Origin that isn't one of the app's, and a Referer not on its Origin; a replaced
  same-origin Referer stays indistinguishable at this layer. The document is authenticated by Tauri's invoke key,
  which only the main frame's init script holds (in a closure); no Worker or frame has it
  (`reader-rw5d-p2-sketch-compartment-codex-review.md`).
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

## Gate (this step; the full suite runs once, in the landing gate)

All in `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, one test command at a time.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: clean.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- **Targeted pytest** (`pytest -n 6`, 105 files: every figure, sketch and Manim test file, the tests that pin the
  figures contract, every test file that reads the defaults snapshot or the parameter registry, and the contract
  tests: config refactor, registry audit, architecture, CLI help snapshot, sidecar contract, desktop RPC contract,
  mobile allowlist, table roles, coordinated migrations, tracked fixture databases, public-tip guards): first run
  **2330 passed, 7 failed, 17 skipped, 3 xfailed** (22 min). The 7: four contract pins that now carry
  `sketch: true` (`test_reader_tutor_switch_off.py` ×2, `test_reading_paths.py` ×2) and the desktop RPC contract's
  parser of `generate_handler!` (×3; the list is now bound to a name and wrapped by the frame guard). Fixed; rerun of
  those three files plus `test_desktop_activation_audit.py` (its activation kinds gain "bundled worker entry"):
  **61 passed**.
  Files: `test_ad1_codex_review_fixes.py`, `test_ad23_owner_decisions.py`, `test_ad23_successor.py`, `test_architecture.py`, `test_attempt_content_state_successor.py`, `test_batch3_landing.py`, `test_cli_help_snapshot.py`, `test_cold_retry_reschedule.py`, `test_compare_keep_switch_off.py`, `test_config_refactor.py`, `test_constraint_engine.py`, `test_coordinated_migrations.py`, `test_curriculum_c1_plan_follows_path.py`, `test_deliverable_codex_review.py`, `test_desktop_rpc_contract.py`, `test_diagnosis_input_provenance.py`, `test_field_workbench_signals.py`, `test_figure_grammar.py`, `test_figure_offers.py`, `test_figure_panels.py`, `test_figure_predictions.py`, `test_figure_property.py`, `test_figure_region.py`, `test_figure_requests_migration.py`, `test_figure_revisions.py`, `test_figure_rich_contract.py`, `test_figure_rich_job.py`, `test_figure_rich_rereview_fixes.py`, `test_figure_rich_review_fixes.py`, `test_figure_rich_rpc.py`, `test_figures_codex_review.py`, `test_figures_final_round.py`, `test_figures_fix_round2.py`, `test_figures_fix_round3.py`, `test_figures_fix_round4.py`, `test_figures_fix_round5.py`, `test_figures_migration.py`, `test_figures_rpc.py`, `test_figures_rw5b_fix_round2.py`, `test_figures_rw5b_review.py`, `test_figures_scope_redesign.py`, `test_figures_show_me_codex_review.py`, `test_figures_show_me.py`, `test_figures_switch_off.py`, `test_figure_verification.py`, `test_grading_cli.py`, `test_intent_codex_rereview.py`, `test_kinship_feature.py`, `test_learner_report_superseded.py`, `test_library_exercises.py`, `test_lp_claim_fixes.py`, `test_manim_figure_checks.py`, `test_manim_sandbox_hostile.py`, `test_method_explicit_upgrade.py`, `test_mobile_allowlist.py`, `test_mvp010_upgrade.py`, `test_mvp011_upgrade.py`, `test_mvp013_upgrade.py`, `test_mvp014_upgrade.py`, `test_mvp015_upgrade.py`, `test_mvp016_upgrade.py`, `test_mvp017_upgrade.py`, `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py`, `test_mvp021_upgrade.py`, `test_mvp022_upgrade.py`, `test_mvp023_upgrade.py`, `test_mvp024_upgrade.py`, `test_open_world_gate.py`, `test_p0_cutover_mvp08.py`, `test_plan_determinism.py`, `test_plan_follows_path.py`, `test_project_report.py`, `test_public_tip_guards.py`, `test_reader_ca2_one_ask.py`, `test_reader_ca4_table_by_point.py`, `test_reader_followups_successor.py`, `test_reader_intentions.py`, `test_reader_intent.py`, `test_reader_rw2b_review.py`, `test_reader_tutor_switch_off.py`, `test_reading_paths.py`, `test_reading_step_switch.py`, `test_rebuild_equivalence_review.py`, `test_recurrence_commands.py`, `test_registry_audit.py`, `test_regrade_contract_successor.py`, `test_regrade_contract_upgrade.py`, `test_router_reader_activity.py`, `test_rw2c_switch_off.py`, `test_sensitivity_certificates.py`, `test_serve_eligibility_review.py`, `test_sidecar_contract.py`, `test_sketch_engine.py`, `test_sketch_hostile.py`, `test_sketch_parity.py`, `test_sketch_sandbox_review.py`, `test_sketch_scene_parity.py`, `test_sketch_service.py`, `test_sketch_verify.py`, `test_source_roles.py`, `test_table_roles.py`, `test_teacher_te0_review_fixes.py`, `test_tracked_fixture_databases.py`, `test_ux_phase2_shell.py`; plus `test_desktop_activation_audit.py` in the rerun.
- No migration and no DB/connection code changed, so no durability lane.
- **Frontend:** `npm install` (adds the `esbuild` dev dependency; already installed), `npm run typecheck` (clean),
  `npx vitest run --maxWorkers=4 src/screens/reader/figures/`: **15 files, 403 passed** (includes the new
  `sketchCompartment.test.ts`, 21 cases, and the changed `sketchProtocol.test.ts`), `npm run frontend:build`
  (clean; `dist/sketch-frame.html`'s script is byte-identical to the source, so its CSP hash holds).
- **Rust:** `cargo check --offline --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` (clean) and
  `cargo test --offline`: **29 passed** (3 new `frame_guard` tests).
- **References:** `db_generate_reference.py` then `db_validate_reference.py` (0 errors; `figures.sketch_enabled`
  now `true`; the other changes are line citations moved by the schema docstring and source-commit headers);
  `desktop_generate.py` then `desktop_validate.py` (passes: 300 TypeScript + 6 Rust modules, ACTIVE 306, with the
  new "bundled worker entry" rule for the Worker that `vite.config.mjs` bundles; the validator's pinned counts
  moved accordingly). `module_validate.py` fails with 1,291 missing-note issues that predate this stage (no Python
  module was added or removed here), so the module catalog was not regenerated.
- **Fingerprints:** recomputed after clearing the config `__pycache__`: first pass 31 changed, second pass 0; parity
  with `sketch_enabled = false` reproduces every base fingerprint.
- **G-SM14 rerun:** PASS (above; full record in `docs/reviews/reader-rw5d-g-sm14-probe.md`).

## Open points

1. The postMessage fallback is removed on Linux (Tauri falls back to it when the custom-protocol fetch fails). If a
   future WebKitGTK ever breaks custom-protocol POSTs, invokes would fail instead of falling back. The rerun showed the
   app working without it; the owner may prefer keeping the fallback and accepting a frame-reachable handler there.
2. Dev mode (`npm run dev`): Vite serves `sketch-frame.html` itself and adds its HMR client script; the frame's meta CSP
   still blocks any connection. Not part of the gate (the gate is the shipped webview).
3. `js_animation` stays behind its build flag; its `llfig://` frame and G-SM14 extension are P2b's JS half.

## Landing onto main

Prepared in `learnanything-astrafix` on `reader/rw5d-p2-sketch-compartment` (stage tip `b7530c0435`). The
orchestrator fast-forwards main and pushes. No GUI was launched apart from the smoke window below, and no model,
network or Codex call was made. Every pytest, vitest, npm and cargo run was in a `systemd-run --user --scope` (5G; the
full suite 10G). Python outside pytest ran under `env -i` with empty, existing `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`, and `TMPDIR` was outside the worktree.

### Step 0: the orchestrator's scoped verify remainder (`5c246bbc0b`)

Sol's scoped verify (`20261101-153827-RFAdme`) found one conditional regression. On Windows and macOS, Tauri 2.11.2
falls back to `window.ipc.postMessage` when a custom-protocol fetch fails, and builds that invoke's headers from the
message's `options.headers`, which LearnLoop leaves empty. The guard therefore refused legitimate top-document calls
there. The fix is in `frame_guard.rs`:
- The header rules take a `Platform`. `Linux` (the build's `PLATFORM` under `cfg!(target_os = "linux")`, where
  `main.rs` unregisters the fallback) still refuses an absent Origin or Referer.
- `FallbackRegistered` (Windows, macOS) never refuses an absent or empty header. It still refuses a present one that
  is an explicit `null` or foreign Origin, or a Referer naming a worker, frame or foreign page, or disagreeing with the
  Origin.
- `refusal_on` and `refusal_reason_on` take the platform as a parameter, so both branches are tested on Linux.
- The `main.rs` wrapper prints one stderr line per refusal (`frame_guard: refused command=… reason=…`).

Four new Rust tests: `linux_refuses_absent_headers`; `with_the_fallback_registered_absent_headers_pass` (including
the fallback's empty header map); `with_the_fallback_registered_an_explicit_frame_or_foreign_origin_is_refused`;
and `this_build_uses_its_platforms_rules`. Details are in the codex-review record, "Orchestrator scoped verify
remainder, fixed".

### Merges

1. **`5fae2f76d6`, main `e9693b3700`** (curriculum C2, migration 229). Conflicts:
   - `main.rs`: the frame-guard wrapper kept; C2's six `notes_*` commands added to its handler list.
   - `desktop_validate.py`: counts combined (302 TypeScript/TSX, 6 Rust, 292 entry-build + 2 bundled-worker,
     ACTIVE 308).
   - `config/template.py`: snapshot notes and hashes only. Both sides' notes kept; all 31 fingerprints recomputed
     with `defaults_fingerprint_for_version` after clearing `.pyc` (first pass 31 changed, second pass 0).
   - Generated references (442 files): main's side taken, then regenerated.
2. **`6ba2340e04`, main `ea1366fff5`** (Reader follow-ups Nov 1b and curriculum C3; head still 229).
   - The only non-generated conflict was `config/template.py`, again snapshot notes and hashes only. C3's notes were
     kept beside the sketch notes; recomputed, the second pass changed 0.
   - The generated references (446 files) were taken from main and regenerated.
   - The figures area (nov1b's `figures/labels.py`, the service's `worded_row`, `trust_env`) merged without a
     conflict.

**Parity at both merges:** setting `figures.sketch_enabled` back to false in every version's composed defaults
reproduces main's fingerprint at all 31 versions, and `FiguresConfig().sketch_enabled` is `True`.

**Regeneration at both merges:** `db_generate_reference.py` ran, `db_validate_reference.py` reported `errors: []`,
and `validate_vault.py` passed (1,374 notes). `desktop_generate.py` ran and `desktop_validate.py` passed (302/302 +
6/6, ACTIVE 308, byte-for-byte).

### Gate

| check | tree | result |
|---|---|---|
| `lint-imports --no-cache` | `5fae2f76d6`, `6ba2340e04` | 37 kept, 0 broken (both) |
| full pytest (`-n 8 --dist worksteal`, 10G scope, the fullsuite lock) | `5fae2f76d6` | **23358 passed, 0 failed**, 90 skipped, 47 xfailed (42:33) |
| durability lane (`-m durability -n 6`) | `5fae2f76d6` | 179 passed, 1 skipped |
| owner lane (`-m owner_vaults -n 6`, `LEARNLOOP_OWNER_VAULTS` = fresh backup-API copies of `owner-copies-mvp035` in `fixtures-local/landing-compartment/`) | `5fae2f76d6` | **83 passed, 2 failed, 4 skipped**: exactly the two known failures, `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies::…[arxiv_v2]` |
| targeted pytest after the second merge (`-n 6`, 90 files: every figure, figures, sketch and Manim test file, every test file main changed in `e9693b3700..ea1366fff5`, every file reading the defaults snapshot, and the contract tests) | `6ba2340e04` | **2167 passed, 0 failed**, 18 skipped, 3 xfailed |
| frontend: `npm install`, `npm run typecheck` | both | clean |
| whole vitest (`--maxWorkers=4`) | `5fae2f76d6` | 248 files, 2389 passed |
| whole vitest (`--maxWorkers=4`) | `6ba2340e04` | 2396 passed, 1 failed: `FeedbackScreen.test.tsx` › "keeps the old Next where no live queue applies" (a keypress spy, under heavy machine load; this branch doesn't touch that screen). Rerun alone 3 times: 11/11 each time |
| `npm run frontend:build` | both | clean |
| `cargo check --offline`, `cargo test --offline` | both | clean; 35 passed |

The full suite was not rerun after the second merge. Its only Python resolution was the snapshot data in
`template.py`: notes kept from both sides and hashes recomputed by `defaults_fingerprint_for_version`. The targeted
run covers every test that reads those snapshots.

### GUI smoke (final tree `6ba2340e04`; one window, 2026-11-01 17:55:29–17:56:20 -05:00)

Under the owner's 2026-11-01 permission for a real desktop window for this sandbox check, with the same conditions as
the G-SM14 rerun:
- **Build:** `npm run frontend:build`, then `cargo build --offline --features custom-protocol` (a debug binary with
  embedded assets, served at `tauri://localhost`).
- **Vault:** a throwaway synthetic one. It is the figure-test vault (`build_figure_vault(sketch=True)`) with one
  stored, verified sketch, the random-walk program of the parity corpus, built through the fake author: its only
  receipt is `fake_figures`, made at build time.
- **Environment:** `env -i`, with `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR` and the XDG dirs at empty scratch
  dirs (still empty afterwards); `LEARNLOOP_AI_PROVIDER=landing-none` (no such profile); `RUST_LOG=debug`; the
  sidecar debug log on; and only the Wayland/X/DBus display variables.
- **Driver:** the page was driven through WebKit's remote inspector, `WEBKIT_INSPECTOR_HTTP_SERVER=127.0.0.1:9228`,
  loopback only. Its two loopback listeners (9228 and an internal port) were the process's only sockets. The
  inspector was the one addition to the rerun's conditions. Through it the driver clicked Reader → "Introduction to
  Probability" → "▸ interactive version" → skip (the prediction) → play.
- **Close:** the app was closed by its own pid. No LearnLoop or sidecar process remained.

What the logs and the page showed:
- **The app starts:** the sidecar log shows `rpc.ping`, `initialize`, `load_vault` and the Today calls.
- **The main window's ordinary invokes pass the guard:** 42 `rpc.request` and 42 `rpc.response` over 36 methods
  (including `load_vault`, `get_today_queue`, `reader.render_view`, `reader.figures` and `reader.prompt_contract`).
  There was no `rpc.error`, no warning or error line, and **0 `frame_guard` lines**.
- **The sketch draws through the compartment:** the page has one `iframe` with `src="/sketch-frame.html"`,
  `sandbox="allow-scripts"` and `referrerpolicy="no-referrer"`. The figure's SVG has 203 drawn shapes and the label
  reads "checked by LearnLoop: 2 checks, listed inside". After play, the step counter went `t = 0 / 100` →
  `t = 47 / 100` → `t = 100 / 100`, with no paused or failure wording.
- **Receipts:** the vault's receipts are unchanged (the one fake build-time row).

An earlier window on `5fae2f76d6` (15:57:46–15:59:57, the same method) showed the same: 44/44 RPCs, 0 `frame_guard`
lines, and the walk played to 100/100.

### Smoke on fresh owner copies (`fixtures-local/landing-compartment-smoke/`, final: main `ea1366fff5` vs `6ba2340e04`)

**Setup:**
- **Copies:** fresh backup-API copies of the three mvp035 owner copies.
- **Neutralized:** every route at the `127.0.0.1:9` blackhole, key variable unset; rewrite, rerank, dense and
  embeddings off.
- **Code:** `git archive` of each side with `src/`, `migrations/` and `tests/`, plus the pinned
  `sketch-engine.wasm`. The engine is needed because the contract offers the sketch only when it is ready; a first
  run without it showed no difference at all and was discarded.
- **Steps on each side:** a bare `upgrade` mvp-0.35 → mvp-0.40, the primary load, `migrate_vault` (head 229, 0
  applied) and `rebuild-derived-state`.
- **Run conditions:** under `env -i`, with an audit hook refusing non-loopback sockets and Codex starts.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Today (3 queue variants, frozen clock) | **identical** (525,266 bytes) | identical (740,827) | identical (344,204) |
| daily plan dump | **identical** (84,723 bytes) | identical (124,048) | identical (32,460) |
| `reader.figures` (3 / 2 / 4 real readings) + `reader.prompt_contract` | **1 difference: `prompt_contract.figures.sketch` absent → `true`**; every listing identical (no stored figures), reads write nothing | same | same |
| `rebuild --shadow --json` (branch copy) | **0/0/0**, live unchanged | 0/0/0 | 0/0/0 |

- **Receipts:** 12 databases compared with their base copies, **0 new `model_call_receipts`**. Probability's
  historical 42 completed and 14 failed are unchanged in every copy.
- **Sockets and processes:** the audit log stayed empty, so the hook saw no process start and **no socket connect of
  any kind**; nothing was refused.
- **Earlier run:** the same smoke against main `e9693b3700` with `5fae2f76d6` gave the same results.

### Orchestrator rulings (verbatim)

- R1: "F1's replaced same-origin Referer half is rejected: Tauri's main-frame-only invoke key is the document-authenticated channel and G-SM14 showed no Worker or frame holds it; a second LearnLoop token adds nothing (proportionate bar). Accepted."
- R2: "Linux runs without WebKit's postMessage IPC fallback (unregistered so frames cannot reach it). Accepted; if a future WebKitGTK breaks custom-protocol POSTs, invokes fail visibly rather than fall back. Owner note."
- R3: "Loopback http origins (the dev server) stay allowed in every build; acceptable because a loopback page must already be running locally and still lacks the invoke key."

### Open items

1. **`js_animation`:** stays behind `JS_ANIMATION_BUILD_FLAG`. Its own G-SM14 extension (the `llfig://` frame) must
   run when that tier is built.
2. **Module catalog:** `module_validate.py` still reports the 1,291 missing-note issues that predate this stage. The
   module catalog wasn't regenerated (no Python module was added or removed here).
3. **The Windows/macOS header filter** is a filter, not authentication: on the postMessage fallback the headers are
   whatever the message names. The invoke key stays the document's authentication (R1).
4. **Owner note (R2):** with the fallback unregistered on Linux, a WebKitGTK that broke custom-protocol POSTs would
   make invokes fail visibly.
5. **Vitest flake:** `FeedbackScreen.test.tsx` › "keeps the old Next…" failed once under load and passed alone 3/3.
   It is not this branch's.
6. **Not merged:** the probe branches `probe/g-sm14` and `probe/g-sm14-compartment` (scratch, never landed).
