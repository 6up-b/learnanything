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

## Re-review (Codex job 20261031-161149-XHPVFU, verdict REOPENED)

The re-review confirmed F1 and F3 fixed, reopened F2 and raised F11. Both were reproduced by
failing tests before the fix (5 tests failed on `42e57aeb4`), then fixed in `80c3efd21`.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | verification held every scene of both runs | confirmed fixed (no change) | `1b1dfbef7` | re-review: the largest-grid memory and 40,000-point output-budget tests pass |
| F2 | High | claim checks unbounded: pairs claims charged at the series' index reach, pairs loops never looked at the clock | fixed | `80c3efd21` | `test_a_pairs_claim_is_charged_for_its_probes_own_x` (the 4,000-pairs x=10,000 reproduction, now refused before it runs), `test_a_small_pairs_claim_is_charged_at_least_its_evaluations`, `test_a_pairs_claim_loop_stops_at_the_deadline` (expired deadline, 40 pairs), `test_claim_loops_look_at_the_clock_by_work_not_only_by_entry_count` |
| F3 | Medium | a series bound to a line claimed the drawn x values | confirmed fixed (no change) | `24a766791` | re-review: the displaced-x reproduction gives a probe-only check |
| F11 | Medium | an element that changes type between settings got a false attribute label | fixed | `80c3efd21` | `test_an_element_that_changes_type_gets_no_attribute_label` (polyline at the default and heat cells elsewhere: no label and the line listed not covered; heat cells at every setting keeps the `values` label) |

**F2 fix.** `sketch.claim_entry_work` now takes the probe shape. A series index keeps its declared
reach from `var_from` by `var_step`. A pairs probe's x is its own first coordinate, so statically
a sum over it is charged its most terms (`MAX_SUM_TERMS`). At check time
`sketch_verify.check_claim` charges each pairs check at the least and greatest x that point read
actually has, before anything is evaluated: the reproduction is charged about 1.7e9 steps and
refused against the 20,000,000-step budget. Every claim loop (series, pairs and the RK4 runs of
`follows`) now calls `_Budget.before(index, work)`. It looks at the clock on the first iteration,
then every 256 iterations, and whenever 4,096 charged steps have run since the last look (the new
`keep` constant `figure_sketch_verify:_TICK_WORK`, classified in the registry). A single grammar
evaluation still can't be interrupted. It was charged first, though, so it is at most the claim-work
cap (a few seconds), well inside the 60 s wall clock.

**F11 fix.** A bound element gets a check-line label only when it has exactly one scope at every
tested setting: either one attribute, or the whole element. Mixed scopes (`y` at some settings,
`values` at others; or whole at some and an attribute at others) leave the element out of the
check. The check line then speaks for the probe, and the element is listed as not covered.

### Re-review gate

| command | result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| reproduction before the fix: `uv run pytest -q tests/test_sketch_verify.py -k "pairs or changes_type or clock_by_work"` | 5 failed, 1 passed (as expected) |
| `uv run pytest -q tests/test_sketch_verify.py` (after the fix) | 68 passed |
| `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6` on the files below | **396 passed** |

Every pytest ran inside the 5G memory-capped scope. The frontend, src-tauri, migrations and schema
are unchanged, so no npm, vitest, cargo, durability or DB-reference run was needed. Following the
owner's 2026-10-17 rule, the full suite was not run; it runs once, in the landing gate.

**Targeted pytest files:** `tests/test_sketch_verify.py` (changed), `tests/test_sketch_hostile.py`,
`tests/test_sketch_service.py`, `tests/test_sketch_engine.py`, `tests/test_sketch_parity.py`,
`tests/test_sketch_scene_parity.py`, `tests/test_figure_verification.py`, `tests/test_figures_show_me.py`,
`tests/test_figures_show_me_codex_review.py`, `tests/test_figure_grammar.py`, `tests/test_registry_audit.py`
(1 new `keep` constant), `tests/test_architecture.py`, `tests/test_public_tip_guards.py`.

## Round 3 (final Sol verify, Codex job 20261031-162057-T76XSt, verdict REOPENED)

The verify confirmed F1 and F3 fixed and reopened F2 (High) and F11 (Medium). F2 was the second round of the same
class: the pre-estimate fell short again. Following the orchestrator's direction, the estimate is no longer
refined. The claim work cap is enforced by **metering** instead.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F2 | High | `follows` claims estimated at the animation's `t_max`; RK4 reaches `(path_length-1)*h` | fixed (metering) | this commit | `test_sketch_verify.py::test_a_follows_claim_is_charged_every_evaluation_it_runs` (the reviewer's repro: still `illustrative`; the budget's work equals the counted `G.evaluate` calls, over 2,000 per check where the estimate charged 288), `::test_a_follows_claim_past_the_cap_is_stopped_where_the_cap_is` (the 4,000-point variant: refused as too much computation after at most cap+1 evaluations, in 4.5 s with a counting wrapper on every call; the wall clock is 60 s), `::test_the_meter_stops_one_evaluation_at_the_cap_and_at_the_clock`, `::test_charged_work_is_at_least_the_evaluations_run_for_random_claims` (60 random claims: equals on scalar/series/pairs and follows, with sums, integrals, piecewise and nesting); round 2's pairs, series and sum tests unchanged and green |
| F11 | Medium | a stored report from the old verifier is delivered with its false attribute label | fixed | this commit | `test_sketch_service.py::test_a_report_from_an_older_verifier_is_reverified_before_it_is_shown` (a synthetic stored row as the round-2 verifier wrote it: same engine, no verifier version, a false `walkers`/`y` label; re-verified by code before listing, no model call, the label gone and `walkers` not covered, one ledger verdict across a restart), `::test_a_report_from_this_verifier_and_engine_is_not_reverified`, `::test_a_verifier_version_bump_reverifies_a_current_engines_report`. Against `edee0f536`'s `service.py` the first and third fail (no re-verification; the stored report delivered as is) |

**The metering design (F2).**

- `grammar.evaluate(node, env, definitions, meter)` takes an optional `grammar.Meter`. Every node it evaluates is
  charged one step at the point of evaluation, before the node is evaluated. That includes each condition node of a
  `piecewise` (`_truth`), every term of a `sum`, every integrand evaluation of an `integral` and each expansion of a
  definition. The hot path is an increment and one comparison against `meter.due`. When `used` passes `limit`,
  `Meter.exhausted()` runs. Every `every` steps, `Meter.checkpoint()` runs. Either may raise, and nothing in the
  evaluator catches, so evaluation stops right there, even in the middle of a 10,001-term sum. Without a meter, the
  values are unchanged; the grammar corpus and the TS-parity tests pass.
- `sketch_verify._Budget` is now a `Meter`, with limit `SKETCH_MAX_CLAIM_WORK` and a checkpoint every `_TICK_WORK`
  (4,096) steps. `exhausted()` raises the same typed refusal as before (`_Failed("claims", "the claims need more
  computation than verification may do …")`). `checkpoint()` looks at the 60 s deadline, which stays as a backstop
  and now also interrupts a single long evaluation. Every grammar evaluation a claim check runs is metered to it:
  `equals` (scalar, series, pairs), both `follows` RK4 runs (all four stages, `dx` and `dy`), and `distribution`.
  `budget.work` is the metered count.
- The static estimate (`CompiledClaim.entry_work` × entries, with round 2's pairs reach) is kept only as an early
  refusal, `_Budget.foresee`. It refuses before anything runs when `used + estimate > cap`, and charges nothing.
  Correctness does not depend on it. A short estimate (as in this finding) just means the meter stops the check at
  the cap instead.
- The per-iteration clock looks are removed, because the meter does them: `_Budget.before` and the `keep` constant
  `figure_sketch_verify:_TICK_EVERY` (unregistered). `check_claim` still looks at the clock on entry.

**F11 fix.**

- `sketch_verify.VERIFIER_REPORT_VERSION = "sketch-verify-v2"` is stored in every report as `verifier_version`.
  Bump it whenever verification semantics change. It is registered as a `version` constant.
- `service.sketch_rechecked` re-verifies by code (no model call) when the stored engine digest **or** the stored
  verifier version differs from the current one. A report without one is from before it existed.
- The in-process recheck cache is keyed by (figure, engine, verifier version).
- The ledger's `reverify_hash` includes the verifier version, so there is one verdict per (figure, engine, verifier).
  The rationale names both engines and both verifier versions.
- The rechecked report carries the new `verifier_version`.
- The build-reuse key is unchanged on purpose. Adding the version would make a verifier bump trigger a model
  rebuild, while delivery re-verifies a reused figure anyway.

### Round 3 gate

| command | result |
|---|---|
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| F11 reproduction: the new service tests against `edee0f536`'s `service.py` | 2 failed, 1 passed (as expected) |
| `pytest -n 6` over `tests/test_sketch_*.py`, `tests/test_figure_*.py`, `tests/test_figures_*.py`, `test_registry_audit.py`, `test_architecture.py`, `test_public_tip_guards.py` | **636 passed** in 91 s |
| `pytest -n 6` over `test_sidecar_serializer_snapshot.py`, `test_desktop_rpc_contract.py`, `test_reader_report.py`, `test_salience_firewall.py`, `test_mobile_allowlist.py` (the report gains a key) | 5826 passed |

Every pytest ran inside the 5G memory-capped scope, behind the shared lock. No frontend, src-tauri, migration or
schema change, so no vitest, npm, cargo, durability or DB-reference run. No model calls; fakes only.

**Open questions.**

1. The early refusal still estimates an `integral` at its integrand cap (`MAX_INTEGRAND_EVALS` = 200,000
   evaluations of the body per entry). So an integral claim over more than about 100 entries is refused before it
   runs, even when the adaptive rule would take a few hundred evaluations. That was already so in round 2. With
   metering, the estimate could be dropped or made optimistic without risk. Keep it as is?
2. A metered claim check that runs to the cap costs about 4 to 5 s of CPU before it is refused (20,000,000 steps).
   That is within the 60 s wall clock and the spec's "tens of seconds", but it is still spent.

## Sandbox review (Astra)

The spec-required **independent sandbox review** (gpt-6-astra, Codex job `20261031-174433-4pdCOX`, read-only, against
`5b3f66059..0f73a7f1c`) found no practical sandbox escape, learner-data exposure or unbounded-resource path. It
**reopened** on one reproduced false verification label. Its controls that checked out: the artifact (869,392 bytes,
SHA-256 equal to all three pins), the wasm's five imports and their deny-all shims, the data-only engine boundary, the
compiled caps (64 MiB QuickJS memory, 192 KiB recursion stack, 16 call ticks, 48 serialization ticks, 4 MiB output,
96 MiB wasm maximum), the sidecar's wasmtime 50.0.1 controls, the desktop's digest check and 480 ms watchdog, the
renderer's allowlists, and the reports' provenance.

### Findings and what changed (fix round 4)

**1. High: runtime history defeated verification and produced a false code-owned check.** The verifier loaded a
program once and called `init()` across the parameter grid; the desktop initialized the default first on a fresh
engine. The reviewer's program (parameter `a`, min 0, default 1, max 2; `init` returns 9 on its first start at `a = 1`,
1 otherwise; a circle `dot` of that radius bound to probe `radius`; claim `radius equals 1`) was verified as
"the radius of the drawn ‘dot’ is 1 at 3 tested settings" while the page drew radius 9.

- **Every `init()` runs on a freshly loaded program, in both hosts.** `SketchEngine.init` (Python) and
  `SketchEngineHost.init` (TypeScript) reload the program's text (`sk_load`: a new QuickJS runtime) before calling
  `init`. The engine is unchanged (same bytes, same digest). A run's history is now "a freshly loaded program, init,
  then its own calls", whatever ran before: a program counting its starts sees its first start every time, in
  verification, grading and the desktop alike.
- **One read schedule** (`sketch.read_steps`, the desktop's `readSchedule`): play's ticks (every
  `ceil(total / SKETCH_PLAY_TICKS)` steps and `t_max`, `SKETCH_PLAY_TICKS` = the desktop's `PLAY_TICKS` = 100), the
  checked samples, and every prediction's graded step. Every run reads exactly those steps, `view()` then `probes()`,
  each once and in order, and no other step, whatever the learner presses: verification's first run (all grid points),
  prediction grading (`prediction_outcome` walks the schedule up to the graded step) and the desktop's playback (a play
  tick advances to the next scheduled step; the step button likewise; a reduced-motion jump to a prediction reads every
  scheduled step on the way and commits the last). So a program that changes its state when read passes through the
  same history everywhere. Checks still run at the 9 samples, now chosen with ties going up (`round_half_up`, as
  `Math.round`) so both hosts compute the same steps; the walk's samples are 0, 13, 25, 38, 50, 63, 75, 88, 100.
  Verification's second run reads only the samples with extra reads before each: a program whose reads change later
  values fails as not deterministic. Bindings are now checked at every scheduled read, not only the samples.
- **Digests, compared on the desktop, failing closed.** The report carries `read_steps` and `tested`: per grid point,
  its parameter values (declared order), the checked steps, and `tested_digest` of each read there (SHA-256 of the
  scene text, NUL, the probes text; first 32 hex digits, `TESTED_DIGEST_HEX`). The sketch view sends both
  (`readSteps`, `tested`). Every desktop read carries the same digest (`sceneDigest`, computed in the Worker for the app
  and in-process for the tests). At a tested state (the grid point's exact values, the verified seed, a checked step) a
  different digest calls `withdrawChecks(figureId)`: for the rest of the session the badge is *AI-written simulation ·
  nothing in it checked*, the collapsed line drops its "N checks" and the open sketch shows *checks withdrawn: this run
  differs from the one LearnLoop checked, so nothing in it counts as checked* instead of the check lines. A report with
  checks but no `tested` (made before this round) also shows no checks (it is re-verified anyway, below).
- **`VERIFIER_REPORT_VERSION` = `sketch-verify-v3`**, so every stored report is re-verified by code before it is shown
  (`service.sketch_rechecked`, which now also carries `read_steps` and `tested` into the delivered report).

**2. Medium: prediction playback changed the graded parameter value.** Validation accepted any in-range value and the
sidecar graded it as is; the desktop snapped it with `clampStep`. Now `parse_sketch` refuses a change that is not a
value the controls can be set to (`sketch.control_value`, a port of `clampStep`: min plus a whole number of steps, to
12 significant digits): "prediction 1: a = 0.4 is not a value its control can be set to (min plus a whole number of
steps; the nearest is 0)". The desktop plays the change exactly as given (no re-snapping), so the graded value and the
played value are one value. A stored sketch with an off-step change no longer parses under v3 and shows as
"couldn't run under this version".

**3. Low: Worker hardening and unvalidated messages.** `sketchProtocol.ts` validates both sides of the Worker:
`parseWorkerRequest` (four operations; `id` a positive safe integer; `load` a string within the 32 KiB source cap in
UTF-8 bytes; parameters a plain object of at most 4 identifier-named finite numbers; seed a 32-bit whole number; `dt`
positive and finite; step index and count whole, count at least 1, index + count within `SKETCH_MAX_CLOCK_STEPS`; exact
argument counts) and `answerRequest` (the Worker's handler: an unknown operation is refused with kind `input` and never
reaches the engine; the old fallback to a read is gone). `parseWorkerReply` checks each reply against its request's
operation (entry points as four booleans, nothing for `init`/`step`, scene + probes + a 32-hex digest for `read`;
error kinds from the closed list, messages cut to 600 characters); a malformed reply rejects its call, an unroutable one
is ignored. Global removal in the Worker is described as supplementary hardening, not the boundary.

**4. Low: toolchain pinning.** Recorded only (stage record, open point 8): `build.py` checks Clang's major version and
does not pin `wasm-ld`; the ordinary build already refuses a differing output digest.

**G-SM14** remains unverified; the reviewer's conclusions and the opaque-origin fallback recipe are recorded in the
stage record (open point 1), and its CSP description is corrected (the app CSP permits `ipc:` and
`http://ipc.localhost`).

### Reproductions (fail first)

Run against tip `0f73a7f1c`'s sources (its `src/` exported to a scratch directory and put first on `PYTHONPATH`, with
pytest's `pythonpath` ini cleared; for TypeScript, its `sketch/` directory copied beside the new one with the new tests,
removed afterwards):

- **Python, `tests/test_sketch_sandbox_review.py` + the shared hostile corpus test: 10 failed, 2 passed.** The exact
  repro: `assert 'illustrative' == 'failed'`, with the check `{'kind': 'equals', 'partial': [{'attribute': 'r',
  'element': 'dot'}]}` (the false "radius of the drawn ‘dot’ is 1"). A fresh-start sequence (init `a` = 0, 2, 1, then
  read) gave `{'radius': 1, 'starts': 3}`, not `{'radius': 9, 'starts': 1}`; reads carried into the next run (6, not
  1); the off-step change `a = 0.4` did not raise; the rest failed on the missing schedule, digests and version. The
  two that passed are guards that already held (a program whose every read flips its state fails as not
  deterministic; the corpus has the cases).
- **TypeScript, the hostile corpus through the desktop's engine host with the committed wasm: 3 failed, 24 passed**:
  "counting its own starts" (`{radius: 1, starts: 3}` for `{radius: 9, starts: 1}`), "repeated restarts at one
  setting", "reads never carry into the next run" (`{reads: 3}` for `{reads: 1}`). `sketchSandboxReview.test.tsx`
  and `sketchProtocol.test.ts` fail to import (`checksWithdrawn`, `sketchProtocol` do not exist there).
- **After the fix:** all of them pass (below). The desktop tests: the reviewer's program on the page draws radius 9
  at the default, its stale digest (what the old verifier read: radius 1 on a second start) withdraws the checks, the
  badge is *nothing in it checked* and no "radius of the drawn" line remains; the random walk played to t_max reads
  exactly the verifier's schedule (101 steps, each once) and every digest at the defaults equals the sidecar's;
  repeated restarts (200, 400, 200, 100, 200 walkers) match the sidecar's digests each time; the read-marking
  program jumped to its prediction under reduced motion reads every scheduled step to 50, shows 383 (13 + 37 × 10)
  and matches the sidecar's digest at 50; a prediction change is played exactly (`{a: 0.4}`, not re-snapped).

### Hostile corpus

`sketchHostileCorpus.json` gains five call-sequence cases run by both hosts (counting its own starts, repeated
restarts at one setting, reads never carrying into the next run, a read-marked state kept within its run and forgotten
by the next), four `verify_cases` the sidecar runs (the counting repro fails at claims; marks-when-read verifies; a
program whose every read flips its state fails as not deterministic; the off-step change is refused) and 24
`worker_messages` the desktop runs (4 accepted, 20 refused).

### Sandbox review gate

Every command ran in `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, behind
`flock /tmp/learnloop-fullsuite.lock`, pytest at `-n 6`, vitest at `--maxWorkers=4`. No model calls; Python outside
pytest (the corpus generators) ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

| command | result |
|---|---|
| Fail-first runs against `0f73a7f1c` | Python 10 failed / 2 passed; TypeScript 3 failed / 24 passed + 2 files unimportable (above) |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| `pytest -n 6` over `tests/test_sketch_*.py`, `tests/test_figure_*.py`, `tests/test_figures_*.py`, `test_registry_audit.py`, `test_architecture.py`, `test_public_tip_guards.py` | **647 passed** in 96 s |
| `npm run typecheck` | 0 errors |
| `npx vitest run --maxWorkers=4 src/screens/reader/figures` | 14 files, **368 passed** |
| `npm run frontend:build` | built; emits `sketch.worker-*.js` (8.45 kB) and `sketch-engine-*.wasm` (869.39 kB) |
| After the last fixture change (the verifier repro made exact: its probes return only `radius`; corpora regenerated): `pytest -n 6 tests/test_sketch_*.py`; `vitest src/screens/reader/figures/sketch` | 144 passed; 5 files, 119 passed |

Not run: `-m durability`, `cargo check` and the DB reference scripts (no migration, connection, schema or `src-tauri`
change). One vitest run with the scratch copy of the old directory alongside (8 files at once) saw "never draws a
superseded frame when a new sample is drawn while a step is in flight" time out its 1 s wait for the held step;
it passed alone (19/19) and in both later runs. Noted as possibly load-sensitive.

### Open questions

1. **The read schedule makes verification read more.** The first run now reads every scheduled step at every grid
   point (play's 101 ticks plus samples and graded steps, about 110 reads per point instead of 9), all validated
   and bound; claims are still checked at the 9 samples. A sketch near the output budget (256 MiB over both runs)
   or the 60 s clock reaches it sooner. The good corpus and the 81-point grid test still pass well within both.
   Acceptable, or should play's ticks drop to the samples' density?
2. **Digests cover the 9 checked samples at every grid point**, not every scheduled read (about 30 kB in the
   report for the largest grid). Comparing at every scheduled read would catch a divergence sooner but would grow
   the report about twelvefold. Keep?
3. **Withdrawal is per session** (module state keyed by figure id), not recorded: a reload shows the checks again
   until a disagreeing read recurs. Recording it (an activity event and the reader report) would need an event and
   allowlist change; not done here. Wanted?
4. **Bindings are now checked at every scheduled read**, not only the samples (stricter: a binding that fails between
   samples now fails verification, where before it passed while the page drew it wrong).
5. **Unchanged:** G-SM14 (the real-webview IPC probe) is still the merge gate, and toolchain pinning is a follow-up.
