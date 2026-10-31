# Reader RW5d P2 (the sketch tier): Codex review record

- **Stage:** `reader-rw5d-p2-sketch`, branch `reader/rw5d-p2-sketch` in `learnanything-ad1` (stage record:
  `docs/reviews/reader-rw5d-p2-sketch.md`).
- **Review:** Codex (gpt-6.1-sol), job `20261031-152100-1GF2xM`, on `1cb765078`. Verdict: do not land. It raised three
  High findings (resource safety, and the truth of displayed checks) and seven Medium ones.
- **Live calls:** none. Every test uses fakes. Python outside pytest ran only under `env -i` with empty, existing `HOME`,
  `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` and `LEARNLOOP_FIGURE_MODELS=off`, for engine timing probes. No vault was opened.
- **Migration:** none. **Successor:** none.

## Review

Each finding was reproduced before it was fixed, by a test that fails on the reviewed code. For F7, F8, F9 and the
frontend findings, the new tests were run against the `1cb765078` file and failed, then passed on the fix.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Verification can retain more than 5 GiB outside the sandbox | fixed | `1b1dfbef7` | `test_sketch_verify.py::test_the_largest_legal_grid_is_verified_one_point_read_at_a_time` (81 grid points × 9 times × 2 runs; tracemalloc peak < 8 MiB; the old lists held ~150 MB at this size), `::test_scenes_at_the_point_cap_over_the_largest_grid_hit_the_output_budget` (1,458 scenes at the 40,000-point cap: refused by the output budget; peak < 96 MiB) |
| F2 | High | Claim evaluation bypasses the engine's work and time caps | fixed | `1b1dfbef7` | `::test_a_claim_whose_work_exceeds_the_budget_is_refused_before_it_runs` (the review's `sum(x,k,0,10000)` over 4,000 entries: refused before the first evaluation runs), `::test_claim_steps_are_counted_soundly`, `::test_verification_stops_at_its_wall_clock`, `test_sketch_engine.py::test_a_call_never_starts_past_the_callers_deadline` |
| F3 | High | A checked series can be drawn at unrelated x-coordinates | fixed | `1b1dfbef7`, `24a766791` | `::test_a_series_line_drawn_at_unrelated_x_is_not_claimed_as_the_equation` (the review's exact case: the check names the value, and `line` is *not covered*), `::test_a_series_line_drawn_at_its_index_is_claimed_whole`, `::test_an_invariant_over_a_series_line_speaks_for_its_y_values_only`, `::test_a_heat_map_bound_series_is_checked_in_its_cell_values_only`; vitest "words a partial check as the attribute it checked" |
| F4 | Medium | Parameter changes can interleave initialization with an old frame | fixed | `24a766791` | vitest "never draws a superseded frame when a slider moves while a step is in flight", "… when a new sample is drawn while a step is in flight" (step answers held back, as a slow Worker's would be) |
| F5 | Medium | Prediction playback does not reproduce the graded observation | fixed | `1b1dfbef7`, `24a766791` | `test_sketch_verify.py::test_prediction_target_steps_are_where_the_answers_are_graded`, `test_sketch_service.py::test_a_sketch_prediction_carries_the_step_it_is_graded_at`; vitest "plays a run_to prediction to its graded step and stops there" (2,000 steps: old 20, now 5), "plays a parameter-change prediction with its change to t_max", "goes straight to the graded step under reduced motion, with no animation", "computes the graded step like the verifier when the view predates it" |
| F6 | Medium | The values table omits most of the declared data | fixed | `24a766791` | vitest "lists every entry of a series and both coordinates of every point, a page at a time" (entries 49, 75 and 100-119; the path's point 119 as x and y), and the updated "shows the declared probes in the values table (t)" |
| F7 | Medium | One sketch's timeout interrupts other concurrent sketches | fixed | `1b1dfbef7` | `test_sketch_engine.py::test_one_sketchs_timeout_does_not_stop_a_concurrent_one`, `::test_another_stores_epoch_tick_does_not_trap_a_running_call` (fails on the old runner: B trapped after 0.05 s), `::test_the_epoch_clock_runs_only_while_an_engine_is_open` |
| F8 | Medium | Engine-upgrade verdicts never reach judgment_ledger | fixed | `24a766791`, `70979eb47` | `test_sketch_service.py::test_an_engine_reverification_is_a_verifier_judgment_recorded_once` (fails on the old service: no second row), `::test_a_failed_reverification_is_recorded_as_failed` |
| F9 | Medium | Prediction submission discards the upgraded verification report | fixed | `24a766791` | `::test_a_prediction_an_upgrade_made_decidable_can_be_answered` (fails on the old service: "no such prediction"), `::test_a_prediction_an_upgrade_dropped_is_refused` |
| F10 | Medium | The committed third-party binary conflicts with the stage instruction | rejected | — | It conflicts with an owner decision, and the stage note's own clause covers it. See below; open question for the owner. |

### What changed, finding by finding

- **F1: streamed verification** (`sketch_verify.py`).
  - Each point read is parsed, validated (scene, probes), checked against the bindings and checked against every claim
    as it arrives, then dropped. Only a 32-byte SHA-256 of its text is kept, keyed by (point, step), for step 3's
    comparison with the second run.
  - Memory therefore holds one scene at a time, whatever the grid.
  - A new `keep` guardrail, `SKETCH_MAX_VERIFY_OUTPUT_BYTES` (256 MiB of engine output over both runs, extra reads
    included), bounds the parsing and checking time. Past it, the sketch fails at `runs` ("too large to verify").
  - The steps still decide in order: a failed run, then determinism, then bindings, then claims.
- **F2: claim work is budgeted before it runs** (`sketch.py`, `sketch_verify.py`).
  - `expression_steps` counts the nodes one evaluation visits, and never under-counts:
    - a sum's body is counted once per term, using its bounds' widest reach (parameter ranges, `t` in [0, t_max], a
      series index over its declared reach), or `MAX_SUM_TERMS` when code can't tell;
    - an integral's body is counted once per allowed integrand evaluation.
  - `claim_entry_work` turns that into the cost of one entry's check:
    - one evaluation for `equals` and `distribution`;
    - twelve RK4 stages of `dx` and `dy` per path step for `follows`.
  - The cost is stored on the compiled claim. Before each check, verification charges cost × entries against
    `SKETCH_MAX_CLAIM_WORK` (20,000,000 steps, `keep`; about 0.2 µs a step was measured on carson). Past it, the sketch
    fails at `claims` ("more computation than verification may do") before the evaluation starts.
  - Grid size and time samples are covered because every point read is charged.
  - **Wall clock:** `SKETCH_VERIFY_SECONDS` (60 s, `keep`; spec §8.4 "ready in tens of seconds") is a deadline on the
    whole verification:
    - it is checked between point reads and every 256 iterations of a claim loop;
    - it is passed to the engine as `SketchEngine.deadline`, so no call runs past it and none starts after it.
- **F3: a check speaks only for what it checked.**
  - In an `equals` claim over a series, a bound line counts as covered only if its i-th x value is
    `var_from + i·var_step` at every point read (within the claim's tolerance). Otherwise the check names the value,
    not the line, and the line is listed as *not covered*.
  - In every other partial case the check records the attribute it covered: a series-bound line's y values, a heat
    map's cell values, a circle's radius, or an invariant's y values over a pairs probe.
  - These go in a new `partial` list of `{element, attribute}` on each check. The desktop words it, for example "the
    y values of the drawn ‘line’ are bounded". The words are closed and code-owned.
- **F4: one queue and a run token** (`SketchFigure.tsx`).
  - Every engine call (init, frame, prediction playback) is queued in order behind the previous one.
  - Each run (an init at some parameters and seed, or a new runner) increments a token. A queued or in-flight
    operation from a superseded run never reads, steps or commits.
  - The run's own parameters and engine step are kept in a ref, so a frame always steps the run it belongs to.
- **F5: the step a prediction is graded at.**
  - `sketch_verify.prediction_target_step` is now the single definition. `prediction_outcome` uses it, and each sketch
    prediction in the view carries it as `targetStep`.
  - After an answer, the desktop restarts the verifier's run: the defaults with the change, and the verified seed.
  - It then plays to exactly that step and stops there. Playback chunks never pass the target.
  - Under reduced motion no interval starts: the run is stepped straight to the target and drawn once.
- **F6: the values table.**
  - A scalar shows its value.
  - A series lists every entry (index, value), and a path lists every point (index, x, y).
  - Long probes are paged `TABLE_PAGE` (50, `keep`, display) entries at a time, with previous and next buttons and a
    caption giving the range shown.
- **F7: timeouts are per store** (`sketch_engine.py`).
  - Every store compiled from the cached `wasmtime.Engine` shares its epoch, so the epoch is now a shared clock,
    `_EpochClock`: one thread ticks it every `EPOCH_TICK_SECONDS` (0.05 s, `keep`) while any instance is open.
  - Each call's deadline is its own allowance (`CALL_SECONDS`, or less before the caller's deadline), counted in
    ticks from its start.
  - The first open instance starts the clock thread, and the last one closed stops and joins it, so the thread-leak
    guard stays clean.
  - The per-call `threading.Timer`, which advanced the shared epoch by one, is gone. (A per-call thread was also
    tried; under the thread guard's start recording it cost ~13 KB and a thread spawn per call, so the clock is held
    per instance.)
- **F8: re-verification receipts.**
  - When an engine upgrade re-verifies a stored sketch, a `figure_verified` judgment (judge `verifier`) is appended
    before delivery and supersedes the figure's last verdict on that question.
  - Its `input_hash` is `reverify_hash(spec_json, engine)`, so it is written once per (figure, engine), however often
    the figure is listed or the process restarts.
  - Its rationale names both engine digests, the check count or reason, and the digest of the report the delivery
    uses.
  - The read is `store.figure_verdicts`, ordered by `rowid` (append order: `created_at` has one-second resolution).
    A read-only repository delivers without writing.
- **F9:** `shown_figure` now returns the rechecked row. Prediction admission and delivery both use the fresh report's
  `dropped_predictions`.

### F10, rejected (open question for the owner)

The spec decides this, and the stage note's own wording allows it:

- **The spec.** Spec rev 2 is owner-approved. §9.3 "Packaging" says *"the artifact is tracked under
  `apps/learnloop-tauri/` assets, which the public-tip guard allows (G8)"*, and Q2 is the owner's decision. The fix
  instructions say to reject a finding that conflicts with the owner's decisions.
- **The stage note.** It requires that *"any vendored artifact needs a licence note and must pass G8"*, and it says
  to *prefer* a build script plus a pinned hash. The artifact meets all of that:
  - it is LearnLoop's own build: LearnLoop's harness linked with MIT, BSD-2, CC0 and Apache-2.0-with-LLVM-exception
    sources, every licence in `sketch-engine/LICENSES.txt`;
  - it comes from a checked-in reproducible script with digest-pinned inputs;
  - it is pinned in three places;
  - G8's exception is narrowed to this one path, and only beside its notice;
  - it is 869 KB, well under 5 MB.
- **What untracking would cost.** Every test, and the desktop's Vite `?url` import, would need a local clang 23
  build, and the build needs the network.

**Offline, as asked:** offline production is **not** established. A clean-cache rebuild downloads three pinned inputs,
including a 119 MB wasi-sysroot tarball, into `~/.cache/learnloop-build/sketch-engine/`. Once that cache is filled, a
rebuild is offline (`build.py --check` reproduced the digest).

If the owner prefers an untracked artifact, the change is:

- a bootstrap step;
- the G8 exception removed;
- the Python and TS tests failing with an actionable message ("run sketch-engine/build.py") instead of skipping;
- `engine_ready()` keeping the tier off honestly.

### Claims the review said don't hold: now addressed

- *"Bindings hold exactly" for drawn coordinates:* series bindings still compare y values only, as before. What
  changed is that a check no longer speaks for a series-bound line's x values unless they are the claim's index, and
  partial checks name the attribute (F3).
- *Sandbox caps bound machine consumption:* Python's side now has its own memory (streaming), work (claim budget),
  output and wall-clock bounds (F1, F2).
- *The drawing is always "init, then n steps":* now holds under asynchronous Worker answers (F4).
- *The values table supplies the declared data:* now holds (F6).
- *"No DB code changed":* `db/stores/figures.py` did change, in P2 and again here (`figure_verdicts`). The durability
  lane was run on the store-touching tests (gate below).

### Not run in this step (unchanged landing blockers)

- **G-SM14** (the real Linux webview IPC probe from inside the sketch Worker): still a merge blocker. It needs the
  desktop webview, which this step did not run.
- **B3 reconfirmation:** `src-tauri` is unchanged, so `cargo check` was not run. The landing gate's `cargo check`
  re-confirms it.

## Gate (this step; the full suite runs once at landing)

Every pytest, vitest and npm command ran in `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`,
one at a time, pytest at `-n 6` at most and vitest at `--maxWorkers=4`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| Targeted pytest, `-n 6` (files listed below) | **6636 passed, 1 skipped** |
| Durability: `pytest -n 6 --durable-sqlite tests/test_sketch_service.py tests/test_figures_rpc.py tests/test_figures_migration.py tests/test_figure_requests_migration.py tests/test_figure_predictions.py` | **60 passed** |
| `npm install`, `npm run typecheck` | ok, 0 errors |
| `npx vitest run --maxWorkers=4 src/screens/reader/figures src/screens/reader/figuresWithReadingPath.test.tsx src/screens/attentionBudget.test.tsx` | **13 files, 330 passed** (`sketch/SketchFigure.test.tsx` 19, 8 of them new) |
| `npm run frontend:build` | built; emits `sketch.worker-*.js` and `sketch-engine-*.wasm` |
| `cargo check` | not run: nothing under `src-tauri` changed |
| DB reference scripts | not run: no schema change |
| Earlier iteration | the first consolidated run: 6635 passed, 1 failed (`test_a_failed_reverification_is_recorded_as_failed`, the test's ledger read ordered by `created_at, id`, which ties within a second); fixed in `70979eb47` and passed 6× in a row alone before the final run |

**Targeted pytest files (the final run):**

- **New or changed in this step:** `tests/test_sketch_engine.py`, `tests/test_sketch_verify.py`,
  `tests/test_sketch_service.py`.
- **The other sketch files:** `tests/test_sketch_hostile.py`, `tests/test_sketch_parity.py`,
  `tests/test_sketch_scene_parity.py`.
- **Every figure file:** `tests/test_figure_grammar.py`, `test_figure_offers.py`, `test_figure_panels.py`,
  `test_figure_predictions.py`, `test_figure_property.py`, `test_figure_region.py`,
  `test_figure_requests_migration.py`, `test_figure_revisions.py`, `test_figure_verification.py`,
  `test_figures_codex_review.py`, `test_figures_final_round.py`, `test_figures_fix_round2.py`,
  `test_figures_fix_round3.py`, `test_figures_fix_round4.py`, `test_figures_fix_round5.py`,
  `test_figures_migration.py`, `test_figures_rpc.py`, `test_figures_rw5b_fix_round2.py`, `test_figures_rw5b_review.py`,
  `test_figures_scope_redesign.py`, `test_figures_show_me_codex_review.py`, `test_figures_show_me.py`,
  `test_figures_switch_off.py`.
- **Contracts and guards:** `tests/test_architecture.py`, `test_registry_audit.py` (5 new `keep` constants
  classified), `test_public_tip_guards.py`, `test_codex_tool_lockdown.py`, `test_batch3_landing.py`,
  `test_sqlite_file_copies.py`, `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`,
  `test_sidecar_serializer_snapshot.py`, `test_cli_help_snapshot.py`, `test_sidecar_registry.py`,
  `test_coordinated_migrations.py`, `test_table_roles.py`, `test_tracked_fixture_databases.py`,
  `test_reader_report.py`, `test_salience_firewall.py`.

**New `keep` constants (registry):**

- `figure_sketch:SKETCH_MAX_CLAIM_WORK`, `SKETCH_MAX_VERIFY_OUTPUT_BYTES` and `SKETCH_VERIFY_SECONDS`;
- `figure_sketch_engine:EPOCH_TICK_SECONDS`;
- `figure_sketch_verify:_TICK_EVERY`.

`TABLE_PAGE` (desktop, display) is labelled `keep` in place. None of them is a model or decision parameter.
