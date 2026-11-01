# Reader RW5d P2b, the Manim half: rich tiers and progressive delivery (stage record)

- **Spec:** `docs/specs/spec_reader_show_me_figures_v1.md` rev 2 (owner-approved, Q1-Q27 decided). This stage builds
  the **Manim half** of phase P2b only: §7.2's `tiers_allowed`, §8.4's `FigureAuthorOutputV3`, §8.6's rich job, §6.8's
  progressive delivery, §9b.3 (the concept pipeline reused, the hardened sandbox, the standing opt-in), §9b.4's Manim
  row and §9b.5's Manim rows. **The `js_animation` half is not built** (it needs G-SM14 in the real webview, an owner
  permission): `js_animation` is absent from every menu behind `learnloop.figures.rich.JS_ANIMATION_BUILD_FLAG = False`
  and is recorded below as the remaining half.
- **Branch:** `reader/rw5d-p2b-manim` in `learnanything-merge2`, base `2eb4bf6e61`.
- **Migration:** none. P1's `224_figure_requests.sql` carried `tiers_allowed_json`, `build_mode`, `tier` (CHECK includes
  `manim`), `runtime_digest`, `media_file_name`, `fuller_of_id` and `checks_json`.
- **Successor:** none (spec §14, P2b: content and display; nothing in scoring, scheduling, projection or serving reads
  a rich figure; its help counting is P3's).
- **Kill switch:** `figures.rich_tiers_enabled` (default **on**, Q18). Off: the author's contract, prompt and reuse key
  are V2's (or V1's) byte for byte, no rich menu entry, no rich keys in any view or in the prompt contract, the two new
  RPCs refuse, and stored rich figures list as *can't show this kind here*. The Manim tier additionally needs the
  learner's standing opt-in (`figures.manim_opt_in = "standing"`, unset by default), so on a fresh vault nothing
  changes until the learner presses *allow*.
- **Live calls:** none. Every model call in the tests is a fake (`AuthorFake` for `figure_author`, `RichAuthorFake` for
  `figure_rich_author`); the renderer and the declared-function runner are injected in the job tests. Python outside
  pytest ran only under `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, to recompute config
  fingerprints, regenerate the desktop catalog and probe the sandbox with synthetic code. No vault was opened; no paid
  command was run; no Manim render ran.

## What the Manim half ships

### The menu and the V3 contract (§7.2, §8.4; G-SM20)

- `learnloop.figures.rich.tiers_allowed(vault, sketch=...)`: `grammar` always; `sketch` with the sketch tier (switch and
  engine); `js_animation` only with the build flag (off); `manim` only with `figures.rich_tiers_enabled`, Linux, `bwrap`
  on PATH, Manim installed (`manim_runtime`, probed once per process per command) and `figures.manim_opt_in ==
  "standing"`. The figure service also requires a way to start the durable job (`spawn_rich`, the sidecar's queue); a
  host with none (the CLI) gets P2's menu.
- With a rich tier on the menu the author's contract is `FigureAuthorOutputV3` (`status`, `why_this_tier`, `spec_json`,
  `sketch_json`, `rich_json`, `unsupported_*`) under `+rich-v1[<menu>]`. The status sentence is replaced by
  `routes.tier_menu_text(menu)`: one neutral sentence per offered medium in the spec's order (cost, latency, what can be
  checked), then the spec's "Choose the medium that best explains this idea ..." sentence. Unavailable media are not
  named at all. **Golden prompt test** `tests/test_figure_rich_contract.py::test_the_menu_is_neutral_facts_in_order_golden`
  pins the text and asserts no ranking word.
- **With no rich tier on the menu the contract is P2's (or RW5b's) byte for byte** (instructions, prompt version,
  output model and reuse key; parametrized test). This is how "V3 off" reads in code: V3 is used exactly when a rich tier
  is on the menu, so a vault with the switch on but no opt-in, or off Linux, keeps every reuse key it had.
- The receipt: every V3 build appends `figure_tier` with the verdict (five values), `why_this_tier` as the rationale; the
  request row records `tiers_allowed`. A rich-only build's receipt is appended against its request (`left_kind`
  `figure_request`) when the author's choice is accepted, whatever its job does next (Codex review F10). A status off the menu or an empty `why_this_tier` is a problem for the second
  attempt.
- Reuse key (§8.5): with a rich tier on the menu it also names `tiers_allowed` and the Manim tier's versions
  (`manim-fig-v1`, the Manim version and the sandbox profile `bwrap-hardened-v1`). Like the panels and sketch
  precedent, a shown figure of the same input built under another menu is reused (no second payment).

### The rich author route (§12.1, Q16)

- New AITask `figure_rich_author` (routing list, operation map, `ai.routing.figure_rich_author` config field, code-default
  route `chatgpt_medium`, the concept animation route's tier; legacy Codex table `codex_medium`), an isolated tool-free
  turn on `figures.FigureRoute` (refused before any request when the provider can't isolate it, tested), the figure
  envelope (`OWNER_KINDS` gains it) and `METERED_PRICE_SETTINGS["figure_rich_author"] = "figures.price_per_million"`.
  Its own disclosure row (`figures_rich`).
- The rich author writes `FigureManimOutputV1`: **a subclass of the concept pipeline's `ManimAnimation`** (scene_code,
  scene_class, title, narration_md) plus `declared_json` (functions, claims, plotted_from). The prompt sends the
  concept pipeline's own `CONCEPT_ANIMATION_PROMPT` as `manim_rules` and its `CONCEPT_ANIMATION_SCENE_SCAFFOLD`, with
  the figure author's context (passages, the learner's request, its grounding), the brief and the animation settings
  (pacing band, resolution, fps, `latex_enabled`).

### The rich job (§8.6; G-SM21, G-SM22, G-SM26)

- A durable job on the sidecar's ingest queue (`figure_rich`, handler `content/pipeline/jobs.handle_figure_rich`,
  `IngestJobs.enqueue_figure_rich` / `retry_figure_rich`), leases, heartbeats and `report()` cancellation; phases
  `writing`, `checking`, `rendering` (the pending line names them).
- Body `learnloop.figures.rich.run_rich_job`: the switch, the opt-in and the runtime rechecked first (a withdrawn opt-in
  or switch stops it with nothing stored); held-out material rechecked before the rich call (the one predicate, over the
  input's spans, keys and home); one `FiguresGate` (`rich_build_key`: vault, switches, route, cap, price, opt-in)
  around every request; at most `MAX_RICH_ATTEMPTS` (2) rich calls; the second carries code's words (validator
  violations, a failed claim with its values, the pacing lint, render stderr). The pacing repair is the second attempt;
  a repair that comes back invalid renders the valid first scene (the concept pipeline's rule). One stderr repair when an
  attempt is left.
- **The concept pipeline, called as a library (no copies):** `validate_scene_code`, `lint_scene_pacing`/`pacing_band`,
  `render_scene` (with `resolve_manim_command`, `[animation] quality` and `timeout_seconds`), and the store, refactored
  into `concept_animation.store_video_bytes` (remux faststart, content-addressed `media/animations/sha256-<hex>.mp4`,
  duration probe) which `_store_video` now calls too. The declared-function checks run in
  `pf_sandbox.run_sandboxed_python`, which wraps the same `_sandboxed_command` profile.
- **Writes no row until it ends:** a stored rich figure (`tier` manim, `spec_version` `manim-fig-v1`, the same
  `input_hash` as the request, `fuller_of_id` naming the quick figure, `media_file_name`, `runtime_digest`,
  `checks_json`; `figure_verified` receipt; for a rich-only request also the `figure_tier` receipt and the request's
  `figure_id`) or a stored failure. Cancelled, interrupted, plan-waiting or stopped jobs write none, so **no row is ever
  wedged**: a job running at a restart is recovered by the queue as `failed(interrupted)` and the line reads *the fuller
  animation couldn't be built · why ▸ (interrupted when LearnLoop stopped)* (test simulates the expired lease and runs
  `recover_stale_leases`).
- **Origin (SM9, §12.3):** the sidecar takes `plan_fallback.unit_token(...)` in the pressed request; a granted press's job
  gets that token and its action (`figure.request`), so the grant covers it; without a grant the job is created with
  neither (it belongs to no action: no offer collected, no grant honoured). A plan that is down ends the job `failed`
  with code `waiting_for_plan` (retryable, no row); the line says *the fuller animation is waiting for the ChatGPT plan*,
  and a later `reader.figures` read requeues it at most once per `PLAN_WAIT_RETRY_SECONDS` (300 s, keep). Responses
  name the job as `richJobId`, never a batch key, so the dispatcher never relays a batch offer for it (tests assert no
  `fallbackAvailable` in the responses and no kept batch offer).

### Progressive delivery (§6.8; G-SM21)

- A rich status may carry a quick spec or sketch (Q20): verified and stored at once like any figure (a failing one is
  dropped and the rich half carries on), then the rich job starts. `figure_view` of a quick figure carries
  `fuller: {state, phase, reason, richJobId, figure}` (`pending` | `waiting_for_plan` | `ready` | `failed` | `cancelled`).
  `reader.figures` lists the rich figure only through its quick one: **one figure line, two versions.**
- With no quick figure, the build answers `{figure: null, rich: <pending line>}`; `reader.figures` returns
  `richPending` lines; the same input asks no second call while its job is pending or waiting (its request is still
  recorded). Once stored, the rich figure lists on its own line and later requests reuse it.
- Desktop: `RichFigure.tsx` (`RICH_FRAME` code-owned copy, `ManimFigureBody`, `FullerLine`, `RichPendingLine`,
  `ManimOptInLine`), wired in `FigureInline.tsx`/`FiguresUnder` and `useFigures.ts` (`RICH_POLL_MS` 5 s polling only while
  a rich build runs; `cancelRich`; the opt-in state). *open ▸* swaps the frame's content, *◂ the quick version* swaps
  back; collapsed, the cue sits on the figure's own line (*· a fuller animation is ready*). No toast, count, badge
  elsewhere or focus move (vitest asserts focus stays and no alert/status role appears). Events `fuller_version_opened`,
  `quick_version_opened` (client) and `rich_build_cancelled` (server), salience-only.
- **The shared player:** `components/AnimationPlayer.tsx`, lifted out of `ConceptAnimationSection.tsx` (blob-URL fetch over
  `llmedia://`, codec hints, retry); the inspector imports it.

### Declared-function checks (§9b.4; G-SM26)

- `learnloop.figures.manim_figure`: `parse_declared`/`parse_figure`; `extract_functions` keeps, by AST, only the declared
  top-level defs and the module constants they read, with `math`/`numpy` imports; anything else (a Manim name, `self`,
  an undeclared helper, its own import, `global`, private attributes, decorators, a signature unlike the declaration)
  makes the function **not checkable: its claims are dropped from the check list, never failed**. The extracted module
  never names manim (asserted by the test runner and by the real-sandbox test).
- Claims `equals` (the grammar oracle, `CLAIM_REL_TOL`, the sketch tier's tolerance) and `invariant` (`finite`,
  `nonnegative`, `bounded`) on each argument's min, midpoint and max (at most 81 points). A failed claim, a non-finite
  value, an exception at a grid point, an expression the grammar refuses or a sandbox that can't run is a failure (the
  second attempt, then *not shown*). `plotted_from` is AST-checked against Manim's plot calls; only then does the line
  say *the curve is drawn from f*.
- Check lines are written by code from closed fields; every Manim figure ends *the video itself is not checked frame by
  frame*; the badge is *AI-made video · not checked against the book* (or *· not checked* with no checks, *· not from
  your books* with grounding none). Never "matches the book".

### Sandbox hardening (§9b.3, §9b.5, Q17)

- `concept_animation._sandboxed_command` gains `HARDENED_BWRAP_FLAGS` = `--unshare-user --disable-userns --cap-drop ALL`
  (`--disable-userns` requires the mandatory `--unshare-user`; `--unshare-all` only tries it). One profile, so the
  inspector's renders and the PF sandbox get it too (Q17 recommends the inspector follow).
- `capped_scope_prefix()`: a figure render runs under `systemd-run --user --scope --quiet -p MemoryMax=4GiB -p
  MemorySwapMax=0 -p CPUQuota=200% -p TasksMax=512` when a user scope can start here (probed once with `true`), else
  `prlimit --as=4GiB`; background renders (P5) add `ionice -c3` and `nice -n 19`. `render_scene(wrapper=...)` prepends it.
- The declared-function harness sets one BLAS thread before importing numpy (OpenBLAS otherwise exceeds the 1 GiB
  address-space cap at import).
- **Hostile corpus for the Manim sandbox** (`tests/test_manim_sandbox_hostile.py`, real bwrap, skipped where it is not
  installed, as `tests/test_pf_sandbox.py`): network and DNS denied; a synthetic vault file, a checkout file,
  `~/.bashrc` and `/etc/shadow` unreadable; writes outside scratch and to `/usr` denied; `CapEff` zero; a new user
  namespace refused; only the sandbox's own processes in `/proc`; a 1 GiB allocation under a 256 MiB cap raises
  `MemoryError`; a runaway declared function is stopped by the sandbox clock. At the extraction layer
  (`tests/test_manim_figure_checks.py`): path escapes, `/proc` probes, network, subprocess, fork bombs, dunder tricks,
  `global`, `Path.home()` and `eval` are never extracted, and the scene validator refuses the imports before any render.
  Fork bombs are not run against the real sandbox (TasksMax is asserted on the scope instead).

### The standing opt-in (§9b.3, Q17)

- `figures.manim_opt_in` (`standing` | `declined` | unset) and `manim_opt_in_at` (date). RPC `figure.manim_opt_in
  {choice: allow | decline}` writes them with `apply_config_updates` and reloads; *allow* is refused where Manim can't
  run here. The prompt contract carries `figures.rich.manimOptIn` (`ask` | `standing` | `declined` | `unavailable`); the
  desktop shows *LearnLoop can make narrated animations ... · allow · not now* once, inline, under the first press's
  passage, never in the background. *not now* writes `declined` and is not asked again. No render without the standing
  opt-in (the menu never has Manim, and the job stops if it was withdrawn).

### Report tier rows (§8.4)

- `build_reader_report(figure_rich_enabled=...)` (the CLI passes `figures.enabled and figures.rich_tiers_enabled`): the
  `tiers` block also appears with the rich tiers on and gains `rich`: built by tier and verification, how many followed a
  quick figure, the median build seconds per rich tier (request to stored row: the p50 the *usually about N min* line
  will read), `why_this_tier` by verdict, fuller and quick versions opened, rich builds cancelled.

### Registry, config, catalog

- Config: `figures.rich_tiers_enabled` (true), `figures.manim_opt_in`, `figures.manim_opt_in_at`,
  `ai.routing.figure_rich_author`; every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` fingerprint recomputed (31 of 31) with the
  template notes. Parameter registry: a `_ConfigRule` for the three keys; module inventory `figure_rich`, `figure_manim`
  and `concept_animation` with every numeric constant classified `keep` (including the concept pipeline's two private
  ones, now in the inventory).
- Desktop catalog regenerated (`AnimationPlayer.tsx`, `RichFigure.tsx`, `richFigure.test.tsx`); `desktop_validate.py`
  counts moved to 297 TS / 289 entry-build / ACTIVE 302. Two new Tauri passthroughs (`figure_rich_cancel`,
  `figure_manim_opt_in`), pinned desktop-only in `tests/test_mobile_allowlist.py`.

## Deviations and interpretations (for the reviewer)

1. **"V3 off" means "no rich tier on the menu".** The spec says V3 off = V2 byte for byte. The code uses V3 exactly when a
   rich tier is on the menu; with the switch on but Manim unavailable (no opt-in, off Linux, no bwrap, no Manim, no
   durable queue) the contract and keys are P2's. Reason: no needless reuse-key churn, and an unavailable tier is
   "left out of the menu, not described as worse".
2. **`rich_json` is JSON text**, like `spec_json` and `sketch_json` (the strict output schema stays flat); §8.4 sketches
   it as an object.
3. **Declared function argument ranges** sit on the declaration (`args: [{name, min, max}]`), since a claim needs a grid;
   the spec writes `args: [name]`. Only `shape: scalar` functions are checked in v1 (series/pairs are drawn, not checked).
4. **Default route `chatgpt_medium`** for "the plan's coding-strength tier": the concept animation route's tier, which
   writes the same Manim scenes. Revisit at the owner checkpoint (spec says so).
5. **Plan wait:** "waits for the plan" is implemented as a retryable failed job (`waiting_for_plan`) requeued by a later
   `reader.figures` read (throttled), not a sleeping worker (which would hold the single ingest worker).
6. **"Not right?" on a Manim figure** sends the note and the earlier program to `figure_rich_author` on a rich job
   (spec §8.5; built in the Codex review fixes, F11); "try a different kind of figure" re-runs the tier choice.
7. **The inspector keeps its per-run consent click.** Q17 says the inspector's Linux path follows the standing opt-in; the
   hardened flags apply to it (shared profile), but its consent UI is unchanged in this stage. Open item.
8. **A request that meets a pending rich-only build** is recorded with no figure (its row's `figure_id` stays NULL; the
   rich-only request that started the job is the one named when the figure lands).
9. **Rich-only failures** are stored `failed` rows (listed as *couldn't build a reliable version of this*, with try
   again), like any figure's.

## Gate (this step; the full suite runs once at landing)

Every pytest, vitest, npm and cargo command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G -- ...`, pytest at `-n 6`, vitest at `--maxWorkers=4`, one run at a time.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: done.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken** (`evidence-never-reads-figures` kept).
- Targeted pytest, round 1 (158 files: every figure, sketch, concept animation, PF sandbox and Manim test file, the new
  files, and every test file that names a changed table or contract: `DEFAULTS_SNAPSHOT_BY_ALGORITHM`/fingerprints,
  routing/operation tables, `METERED_PRICE_SETTINGS`, disclosures/judge routes, `build_reader_report`,
  `DEFAULT_HANDLERS`, `_sandbox_bwrap_path`/`pf_sandbox`, `CLIENT_ACTION_EVENTS`, `RoutingConfig`, `OWNER_KINDS`, the
  mobile allowlist, the desktop RPC contract, the registry audit, architecture): **9,070 passed, 8 failed, 12 skipped,
  3 xfailed** (28 min). The 8, fixed:
  - `test_figures_switch_off`, `test_reading_paths` x2: the prompt contract gained `figures.rich` with the switch on by
    default; it now appears only where the Manim tier concerns this machine (`ask` | `standing` | `declined`), so where
    Manim can't run (and in the suite) the contract is P2's key for key.
  - `test_figures_fix_round2` F7: the rich-only reuse lookup is a read of the input's key; it now runs only while the
    rich tiers are on.
  - `test_architecture` (symbolic field reads): `manim_figure.parse_declared` reads the rich author's `claims` key;
    allowed there, like the other domains' claims.
  - `test_judge_routes`, `test_figures_scope_redesign`: the new route's disclosure row and `OWNER_KINDS` (test updates).
  - `test_codex_lockdown_round3`: the one-time `systemd-run --user --scope -- true` probe approved as a launch site
    (`capped_scope_prefix` no longer names `subprocess.run`).
- Round 2: the 7 failing files plus the 5 new ones: **216 passed**. Round 3 (after the fixes), every figure, sketch,
  concept animation, PF sandbox, Manim and reader-report file plus the mobile allowlist, desktop RPC contract and
  registry audit (53 + 6 files): **1,070 passed**.
- New test files: `tests/test_figure_rich_contract.py` (13), `tests/test_figure_rich_job.py` (18),
  `tests/test_figure_rich_rpc.py` (10), `tests/test_manim_figure_checks.py` (22), `tests/test_manim_sandbox_hostile.py`
  (7, real bwrap; bubblewrap 0.13.0 here, so none skipped); fixtures `tests/rich_fixtures.py`, `tests/figure_fixtures.py`
  (`rich=` and V3 answers). Changed test files: `tests/test_mobile_allowlist.py`, `tests/test_judge_routes.py`,
  `tests/test_figures_scope_redesign.py`, `tests/test_architecture.py`, `tests/test_codex_lockdown_round3.py`.
- No migration and no DB/connection code: no durability-marked run needed (none touched).
- Frontend (`apps/learnloop-tauri`): `npm install`; `npm run typecheck` clean; `npx vitest run --maxWorkers=4
  src/screens/reader/figures/ src/components/ src/screens/ReaderScreen`: **79 files, 857 passed** (new
  `richFigure.test.tsx`, 8); `npm run frontend:build` built; `cargo check --manifest-path src-tauri/Cargo.toml` finished.
- References: desktop catalog regenerated and validated (297/297 TS + 5/5 Rust, ACTIVE 302, reproducible);
  `db_generate_reference.py` rerun (config leaves 1091 -> 1095; prose counts updated), `db_validate_reference.py`
  errors `[]`, `validate_vault.py` passed. The Python module catalog is not regenerated (it is already partial at base:
  474/1105 modules, and `module_generate.py` asks for package descriptions that predate this stage).

## Open points for the landing and the owner

- **The JS half** (`js_animation`): `llfig://`, the frame, CSP, prelude, shelf (KaTeX, d3, three.js), loop-guard
  instrumentation in the sealed engine, crash marker, host channel, model-export checks and in-frame probe agreement,
  G-SM23/24/25. Needs G-SM14 in the real Linux webview (owner permission); until then `JS_ANIMATION_BUILD_FLAG = False`.
- **Owner checkpoint (not part of this stage):** the rich-tier review's report; three real requests built on the plan
  (the spec asks for three `js_animation` and two `manim`; with JS off, the Manim ones), their measured latencies, the
  owner's yes or no on the feel. Needs `figures.manim_opt_in = "standing"` (or *allow* in the Reader) on a
  `fixtures-local` copy.
- **Adversarial review of the Manim hardening** before merge (spec §9b.5), against the hostile corpus above.
- *usually about N min* on the pending lines is not shown yet (the report now has the p50; the desktop does not read it).
- The concept inspector's consent click (deviation 7).
- Codex review fixes: `docs/reviews/reader-rw5d-p2b-manim-codex-review.md`.
- The `SketchFigure.test.tsx` "draws a new sample with another seed" test timed out once (2,021 ms) when the whole
  figures folder ran in parallel with 4 workers; it passes alone (19/19). Pre-existing timing sensitivity, not touched.

## Landing onto main

The branch `reader/rw5d-p2b-manim` (worktree `learnanything-merge2`; stage, Codex review round 1 and the re-review
fixes, stage tip `82224fa284`) is merged with main `0708e12a18` (substrate facet write-on-change). The orchestrator
fast-forwards main and pushes.

### Codex state (job `20261101-104837-N0cgtR`)

F1, F2, F3 (High), F12 and F13 CONFIRMED-FIXED; F4-F11 fixed in round 1. F14 REOPENED only for the case where a failed
animation correction ages out of the newest-500 rich jobs window (ruled Low, R1 below).

### Merges and regeneration

| commit | what |
|---|---|
| `06439a8a28` | Merge of main `0708e12a18` (four commits of the substrate facet write-on-change stage: `db/repositories.py`, a new test file, two review records). **No conflicts.** Main touched no config, template, parameter registry, schema, frontend or `src-tauri` file, so no fingerprint was recomputed and no snapshot note merged. |
| `0ed3be17c7` | References and the desktop catalog regenerated on the merged tree. `db_generate_reference.py` (358 table notes, 359 notes restamped to the merge; main's `repositories.py` change moves 4 "None found by exact static reference scan" lines and one source path), `db_validate_reference.py` errors `[]`, `validate_vault.py` passes (1365 notes, 1363/1363 reachable). `desktop_generate.py` (297 TS/TSX + 5 Rust notes): the re-review's `tests/test_figure_rich_rereview_fixes.py` now appears among `figureSpec.ts`'s cross-boundary contracts (the stage's catalog predated that file). `desktop_validate.py` passes byte for byte (297/297 TS + 5/5 Rust, ACTIVE 302 = 289 entry-build + 2 compiler-implicit + 6 vitest-support + 5 native-entry). |

Main's tip was still `0708e12a18` just after the gate (re-read after the owner lane), so no second merge was needed and
nothing was rerun for one.

### Gate (at `0ed3be17c7`)

Every Python run under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, `TMPDIR` outside the
worktree, `LEARNLOOP_AD_MODELS=off`; every pytest under `flock /tmp/learnloop-fullsuite.lock` inside `systemd-run
--user --scope` (full suite 10G, the rest 5G); vitest, npm and cargo in a 5G scope. No live model call, no Manim render.

- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- **Full pytest** (`-n 8 --dist worksteal`, 10G): **23234 passed, 90 skipped, 47 xfailed, 0 failed** (36:44). The only
  new skip is `test_manim_sandbox_hostile.py::test_the_real_capped_scope_launches_the_sandbox_without_the_session_bus`
  ("no user systemd scope can start here": `env -i` drops the session bus).
- **Real scope and bubblewrap, with the session bus:** `tests/test_manim_sandbox_hostile.py`, `tests/test_pf_sandbox.py`,
  `tests/test_concept_animation_service.py`, `tests/test_sidecar_animation.py` once more with `DBUS_SESSION_BUS_ADDRESS`
  and `XDG_RUNTIME_DIR` passed through (`-n 6`): **53 passed, 0 skipped** (the real capped scope + bwrap launch ran;
  the shared hardened profile, R5, under the PF sandbox and the inspector's service).
- **Durability lane** (`-m durability`, `-n 6`): **178 passed, 1 skipped**.
- **Owner lane** (`-m owner_vaults`, `-n 6`, fresh backup-API copies, `learnloop.db.copies.copy_tree_with_databases`,
  of `learnanything-ad1/fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}` in the gitignored
  `fixtures-local/landing-p2b/`): **83 passed, 2 failed, 4 skipped**, the expected counts. The failures are exactly the
  two known ones, `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and
  `test_placement_fixture_copies::…[arxiv_v2]`; the skips are the retired vaults with no copy.
- **Frontend** (`apps/learnloop-tauri`): `npm install` ok; `npm run typecheck` clean; the whole vitest
  (`--maxWorkers=4`): **246 files, 2353 passed** (the `SketchFigure.test.tsx` timing note above did not recur);
  `npm run frontend:build` ok.
- `cargo check --manifest-path src-tauri/Cargo.toml`: finished.

No unexpected failure, so nothing was rerun alone.

### Smoke on fresh owner copies (`fixtures-local/landing-p2b-smoke/`, driver `scripts/smoke.sh`)

**Setup.** Fresh backup-API copies of the three mvp035 owner copies, neutralized under each side's own code
(`neutralize3.py`: every route at the `127.0.0.1:9` blackhole, key variable unset; rewrite, rerank, dense and
embeddings off). Main's code is `git archive 0708e12a18` and the branch's `git archive 0ed3be17c7`, both with `src/`
and `migrations/`. Each copy, under its own side's code: a bare `upgrade` (**mvp-0.35 → mvp-0.40**, head 228), the
desktop start (`SidecarContext.load`, primary), `migrate_vault` (0 applied), `rebuild-derived-state`. Then, each on
a further copy: the Today queue (3 variants, frozen clock), the daily plan dump (frozen clock, deterministic ids) and
`figures_smoke.py` (reads only: `reader.prompt_contract`, `reader.figures` on every reading with a ready render view
of a reader-enabled source, and the author's menu `tiers_allowed`; table counts before and after). Every process ran
under `env -i` with empty `HOME`, `CODEX_HOME` and config dir and an audit hook that logs every process start and
refuses non-loopback sockets and Codex process starts. Nothing was requested, built or rendered.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| upgrade, desktop start, rebuild-derived-state (main and branch) | mvp-0.35 → mvp-0.40, ok (70 attempts replayed) | same (3) | same (3) |
| Today, branch vs main | **identical** (525,266 bytes) | identical (740,827) | identical (344,204) |
| daily plan dump, branch vs main | **identical** (84,699 bytes) | identical (124,024) | identical (32,436) |
| readings listed by `reader.figures` | 3 | 2 | 4 |
| `figures` arrays, branch vs main | identical (each empty: the copies hold no stored figure and no figure request) | same | same |
| `richPending`, branch | `[]` on every reading (absent on main) | same | same |
| author's menu (branch) | `grammar` (+ `sketch` with the sketch tier): **no `manim`, no `js_animation`** | same | same |
| `figure_rich` jobs; tables changed by the reads | 0; none (main and branch) | same | same |
| prompt contract `figures`, branch vs main | branch adds only `rich: {manimOptIn: "ask"}` | same | same |
| `rebuild --shadow --json` (branch copy) | **0/0/0**, live unchanged | 0/0/0, live unchanged | 0/0/0, live unchanged |

- **The prompt contract's Manim entry:** it appears because the Manim tier concerns this machine (Linux, `bwrap` on
  PATH; Manim is a core dependency), with the opt-in never asked (`ask`). It is the stage's designed state for a fresh
  or upgraded vault here: the desktop would show *allow · not now* once on a press. With no opt-in, Manim is on no
  menu (row above), so nothing a learner sees changes until *allow*; where Manim can't run the key is absent (stage
  record). The check reads `manim_runtime_state(probe=False)`: no Manim probe process ran.
- **Model call receipts:** across the 12 smoke databases compared with their base copies, **0 new**. probability's 56
  historical rows (42 completed, 14 failed) are unchanged in each copy.
- **Audit:** the audit log was never written, so there was no process start (no Manim, bwrap, systemd-run or Codex
  process) and no socket connect of any kind.
- No Manim render ran and nothing was rendered on owner data.

### Orchestrator rulings (verbatim)

- R1 (F14 remainder): "Ruled Low under the proportionate protection bar: it needs 500 newer rich (Manim) jobs after an unresolved failed correction, which are opt-in, minutes-long builds; the earlier animation stays shown. Queued follow-up: discover unresolved correction failures from durable figure/request rows instead of the job window."
- R2: "The §9b.4 rule that model-written free text (narration, title, what it shows, assumptions) must not read like a check label is not built in this stage. Queued as a follow-up to land before the owner gives the Manim opt-in; owner note. The sketch tier's impersonates check keeps covering names and ids."
- R3: "figure.rich_retry on a build with no stored figure requeues the same job and generation (a paid answer is recovered, not re-asked); 'try again' after a stored failed figure starts a new generation. Accepted."
- R4: "figures.rich_tiers_enabled defaults on (Q18) but Manim stays off every menu until the standing opt-in, so a fresh or upgraded vault changes nothing. Accepted. js_animation stays absent behind JS_ANIMATION_BUILD_FLAG until G-SM14 (owner permission)."
- R5: "The shared bwrap profile hardening (--unshare-user --disable-userns --cap-drop ALL) now also applies to the PF sandbox and the concept inspector. Accepted; the full gate covers them."

### Owner items

1. **The three-real-requests checkpoint:** three real figure requests built on the plan (the spec asks for three
   `js_animation` and two `manim`; with the JS half off, the Manim ones), their measured latencies and the owner's yes
   or no on the feel, with the rich-tier report. It needs `figures.manim_opt_in = "standing"` on a `fixtures-local`
   copy, so it waits for item 2.
2. **The Manim opt-in, after R2's follow-up:** the §9b.4 label-wording rule over a Manim figure's model-written free
   text lands first; only then should *allow* be given (in the Reader, or `figures.manim_opt_in = "standing"`).
3. **G-SM14 for `js_animation`:** the real Linux webview check (owner permission); until then
   `JS_ANIMATION_BUILD_FLAG = False` and the JS half (stage record, open points) is not built.

### Open items

1. **R1's follow-up (queued):** find unresolved failed animation corrections from the durable figure and request rows,
   not the newest-500 rich jobs window.
2. **R2's follow-up (queued, before the opt-in):** the §9b.4 label-wording rule over narration, title, what it shows
   and assumptions.
3. From the stage record, unchanged: *usually about N min* on the pending lines (the report has the p50; the desktop
   does not read it yet); the concept inspector keeps its per-run consent click (deviation 7); the adversarial review
   of the Manim hardening against the hostile corpus (spec §9b.5); the default rich author route `chatgpt_medium`
   (deviation 4), to revisit at the owner checkpoint.
4. Pre-existing on main, not part of this landing: the Python module catalog (`module_generate.py` /
   `module_validate.py`) is stale (end-of-queue docs workflow).
