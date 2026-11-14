# Refactor RE2: one retrievability function

Step RE2 (`docs/specs/refactor_strategy_v3.md` arc F; `docs/specs/spec_recognition_and_effort_v1.md` §6), on branch `refactor/re2-one-retrievability`, based on main `c85993a087`. Structure track: no served or persisted value changes, to the last bit. Why the owner wants one read function: RE8's `S_eff` changes what a retrievability read returns, and must do so in one place while FSRS's own update, fitting and evaluation keep reading plain stability.

## 1. Step 0: every definition and every call site

Line numbers are the base's (`c85993a087`).

### (a) The definitions

The strategy (written at an older tip) names four: `scheduling/fsrs.py`, `daily_plan/reentry.py:64`, `daily_plan/objective_inputs.py:419` and `router_objective/memory.py:274`. At this base only two of them hold the formula.

| # | where | form | formula | clamps | result |
|---|---|---|---|---|---|
| F1 | `scheduling/fsrs.py:55` `forgetting_curve(stability, elapsed_days, weights=FSRS6_DEFAULT_WEIGHTS)` | scalar, Python floats | `decay = weights[20]`; `factor = 0.9 ** (1 / -decay) - 1`; `(1 + factor * max(elapsed_days, 0.0) / stability) ** (-decay)`. `0.9` is FSRS-6's: the curve passes 0.9 at `elapsed = stability`. `decay` is weight 20, the pinned FSRS-6 default (`FSRS6_DEFAULT_WEIGHTS`, py-fsrs v6.3.1) or a vault's fitted set (`params/fitted_params.resolve_fsrs_weights`, 21 finite floats). | `stability is None or <= 0` gives `0.0`; elapsed below 0 reads as 0; result through `numeric.clamp(·, 0, 1)` (`max(0, min(1, x))`) | a Python `float`; `**` is CPython's float power (the C library's `pow`) |
| F2 | `router_objective/memory.py:274` `Fsrs.retrievability(self, stability, elapsed)` | vectorized, numpy | the same expression, operation for operation, on float64 arrays: `np.asarray(·, dtype=np.float64)` on both inputs; `factor` from `self.weights[20]` as in F1 | stability floored at `1e-12` before dividing, then `np.where(raw > 0, value, 0.0)` (so `<= 0` and NaN give 0); elapsed `np.maximum(·, 0.0)`; result `np.minimum(np.maximum(·, 0.0), 1.0)` (`np.clip` without its per-call overhead) | a float64 `ndarray`; `**` is numpy's `power` ufunc |
| — | `daily_plan/reentry.py:64` `retrievability(stability, last_review, at, weights)` | not a copy | converts two timestamps to elapsed days (`max((at - last).total_seconds() / 86400.0, 0.0)`) and calls F1 | `None` when there is no stability or no parseable last review | `float` or `None` |
| — | `daily_plan/objective_inputs.py:428` (the closure `retrievability` in `_combiner_with_traces`) and `:531` (`check_sensors`) | not copies | each wraps F2 for one value: `float(Fsrs(w).retrievability(np.array([s]), np.array([e]))[0])` | F2's | `float`, with F2's bits |

Related, not a retrievability read (left alone, §4): `scheduling/fsrs.py:138` `interval_for_retention` and `scheduling/intent/recall_targets.py:53` `ratio` invert the curve (days until recall falls to a target); both re-derive `0.9 ** (1 / -decay) - 1`.

Exempt (strategy, spec §6), left as they are: `scheduling/fsrs_fitting.py:91` (`fit_fsrs_weights`: the curve's prediction against each observed review outcome, inside the log-loss the fit minimizes) and `scheduling/evaluation.py:394` (the held-out calibration report of a weight set: predicted recall against outcomes). Both evaluate the curve itself at plain stability and keep calling F1 directly.

### (b) Every call site

Elapsed is `max((now - last).total_seconds() / 86400.0, 0.0)` unless said. Weights "fitted" means `resolve_fsrs_weights(repository)` (the fitted set when one is active, else the defaults).

| site | form | weights | elapsed, rounding | feeds |
|---|---|---|---|---|
| `scheduling/fsrs.py:128` `apply_review` | F1 | caller's | the review's elapsed days | FSRS's own update: the memory state stored on every review (persisted, replayed). Plain stability by design (RE8 §1). |
| `learner_context.py:1572` | F1 | fitted | as above; `float(...)` | the chat context's topics below the retention target, lowest recall first (display) |
| `daily_plan/reentry.py:71` (via `retrievability`, called at `:125`, `:128` and from `daily_plan/headline.py`) | F1 | caller's (fitted) | from timestamps, as above | the re-entry panel's solid and slipped counts and names; Today's headline (display) |
| `daily_plan/router_card.py:548` | F1 | **defaults** (no weights passed) | as above; the LO mean rounded to 4 places | the router card's `recall_now` (display). Ledger RE2-2. |
| `goals/goal_projection.py:404`, `:405` | F1 | the projection's `fsrs_weights` (fitted) | elapsed to `now` and to the goal's horizon, not clamped at the call (F1 clamps); baseline floored at `1e-6`, the ratio clamped | each supporting item's retention ratio in the goal projection (a goal's readiness forecast) |
| `scheduling/family_memory_model.py:77` | F1 | the model's | from the observation's time; result clamped to `[1e-9, 1 - 1e-9]` | the field memory arm's predicted recall (field evaluation) |
| `scheduling/review_log.py:154` `predicted_retrievability_by_attempt` | F1 | caller's | the observation's elapsed days | each attempt's predicted recall from the item's earlier reviews: `field/outcomes.fsrs_predicted_retrievability` (a derived table, written by rebuild) and `router/outcomes` (a router outcome's `predicted_retrievability`) |
| `scheduling/scheduler.py:3073` | F1 | the scheduler's (fitted) | as above | `1 - R`, the due queue's forgetting-risk component (served ranking) |
| `sim/runner.py:1009` | F1 | defaults (the simulator's) | as above | the simulator's recall prior |
| `router_objective/decision_state.py:115` | F1, handed in as the `forgetting_curve` argument of `prepare` (router_objective sits below scheduling) | fitted | as above; stored rounded by `_round` | the decision receipt's item rows `r` (persisted with the decision) |
| callers handing F1 to `decision_state.prepare`: `daily_plan/engine.py:3784`, `daily_plan/lesson_suggestion.py:541`, `followup_run/router.py:309`, `learnloop_sidecar/handlers/queue.py:793`, `:806` | — | — | — | as above |
| `learnloop_sidecar/handlers/knowledge_map.py:566` | F1 | fitted | `now` is today's UTC midnight | each facet's weighted retention on the knowledge map (display) |
| `router_objective/memory.py:295` `Fsrs.review` | F2 | `Fsrs.weights` | the rollouts' lag per draw | the vectorized FSRS update inside the objective's rollouts (FSRS's own update, over draws) |
| `router_objective/value.py:765`, `:856`, `:893` | F2 | `Inputs.fsrs_weights` (fitted) | per draw | `P(perform)` per draw and topic in the numeric policy's rollouts (the `Q̄` that chooses the served block) |
| `daily_plan/objective_inputs.py:429` | F2, one value | fitted | from the check row's frozen stability and elapsed plus the realized lag | the combiner's trace-joined rows (`router_objective/combiner_data.rows:181`), the combiner fit that the numeric policy then reads |
| `daily_plan/objective_inputs.py:531` `check_sensors` | F2, one value | fitted | median stability and median elapsed of the LO's practised items | a randomized check's frozen sensors, stored in the plan record (`daily_plan/engine.py:3665`) and read back by the combiner fit |
| `scheduling/fsrs_fitting.py:91`, `scheduling/evaluation.py:394` | F1 | the candidate set | the review's elapsed days | exempt (above) |

Neither `learnloop_mobile`, `learnloop_mcp`, `scripts/` nor the TypeScript frontend computes the curve. `teacher/brief.py:330` and `field/outcomes.py:740`, which the RE spec lists, read stored or replayed values (`practice_item_state.retrievability`, `review_log`'s predictions) and compute nothing.

Tests: `test_fsrs.py:34-36` (F1's shape), `test_held_grade_composition.py:151`, `:154`, `test_router_coldness_covariates.py:202`, `test_evaluation.py:120`, `test_fsrs_fitting.py:40`, `test_ro4_value.py:164` and `test_rofu_speed.py:171` (F2 against F1, to `abs=1e-12` or `pytest.approx`), `rospeed_ad_link_helpers.py:68`, `:84`, `:100` and `test_rofu_review_draw.py:159` (F2), `test_ro0_rows9_13_decision_state.py:151`, `:157` and `test_ro0_codex_review.py:320` (F1 handed to `decision_state.prepare`); `test_rofu_learning.py:154` is a stub returning 0.8, not a copy.

### (c) The types

No site passes a torch tensor, a float32 array or a numpy scalar: the scalar sites pass Python floats (stability from SQLite `REAL`, weights from `resolve_fsrs_weights`, a tuple of Python floats), F2's callers pass float64 arrays (F2 converts anything else to float64 first). Every stored stability is at least `S_MIN = 0.001` (`apply_review` floors it; the initial stabilities are floored too), so F2's `1e-12` floor never engages on a value a vault holds.

## 2. The difference table

Both definitions run over a grid (`grid_compare.py` in the step's scratch directory, outside the repository; run through the isolation wrapper): elapsed in {0, 5e-324, 1e-300, 1e-12, 1e-9, 1e-6, 0.001, one second, one minute, 0.5, 0.999, 1, 1.5, 2.7, 3, 7, 10, 30.4, 100, 365.25, 1000, 1e4, 1e6, 1e9, 1e15, 1e300, -0.0, -1e-9, -0.5, -1, -1e6} by stability in {5e-324, 1e-300, 1e-15, 1e-13, 1e-12, 1e-11, 1e-9, 1e-6, 0.001, 0.01, 0.1, 0.212, 0.5, 1, 1.2931, 2.3065, 8.2956, 10, 36.5, 100, 1000, 1e4, 1e6, 1e9, 1e300, 0, -0.0, -1e-9, -1}, at decays {0.1542 (the default), 0.0658, 0.1, 0.2, 0.4, 0.5, 0.8}; F2 called on one-element arrays, on the whole grid as one array, and on float32 inputs; plus `None`, NaN and infinite inputs; plus a dense grid of 2,000,000 random pairs in the range a vault produces (stability log-uniform in [0.001, 1e5], elapsed 0, fractional, up to 30 days, up to ten years, and whole seconds) at four decays. numpy 2.5.1 on this machine (carson) reports AVX-512F.

| inputs | F1 against F2 | reachable from a supported vault? |
|---|---|---|
| stability >= `S_MIN`, elapsed >= 0, finite | **differ by one ulp on about 5.3%** of the dense grid (105,578 of 2,000,000 at the default decay; 104,410, 105,710 and 106,452 at 0.1, 0.5 and 0.8), equal elsewhere; never more than one ulp. F2 on a one-element array and on a long array agree with each other everywhere. | **yes**: every vault |
| 0 < stability < `1e-12` | differ by much more (F2 floors the stability at `1e-12`: at stability 1e-15 and elapsed 1e-12 F1 gives 0.3457, F2 0.9000000003) | no: stored stability >= `S_MIN` |
| `1e-12` <= stability < `S_MIN` | the same one-ulp differences only | no |
| stability `None`, 0, negative | equal (0.0) | yes (`None` for a card never reviewed): equal |
| stability NaN | F1 1.0 (`clamp` returns `high` for NaN), F2 0.0 | no: SQLite stores NaN as NULL and FSRS makes none from finite inputs |
| elapsed NaN | F1 1.0, F2 NaN | no: elapsed comes from subtracting two parsed timestamps |
| elapsed negative or `-0.0` | equal (1.0) | yes (a clock skew): equal |
| elapsed infinite | equal (0.0) | no |
| float32 inputs | F2 converts to float64 first, so the same as F1 on the converted values, up to the one-ulp difference above | no site passes float32 |

**The one-ulp difference is the power function, not the code.** The two expressions are the same operations in the same order (`factor * elapsed / stability` is rounded identically by IEEE arithmetic in both); the last step is `x ** -decay`, which F1 takes from the C library's `pow` and F2 from numpy's `power` ufunc, and numpy dispatches `power` on float64 to its own SIMD kernel on a CPU with AVX-512 (on another CPU it may call the C library and agree). So F2's last bit depends on the machine, and on this machine F1 and F2 disagree on about one input in twenty, in the last bit.

That is a finding (ledger RE2-1), not something this step unifies: the two forms keep their own results bit for bit. Where it reaches: the rollouts' `P(perform)` (`value.py`, a Monte Carlo over parameter draws, where one ulp is far below the draws' noise but could in principle flip an exact tie), the vectorized FSRS update inside the rollouts, and the two single-value reads in `objective_inputs` (the check sensors stored in the plan record, the combiner's trace join), which therefore differ in the last bit, on some inputs, from the same quantity read by every scalar site (the decision receipt's `r`, rounded, hides it except at a rounding boundary).

**The other difference that reaches a served value is the weights, not the curve** (ledger RE2-2): `daily_plan/router_card.py:548` calls F1 without weights, so the router card's `recall_now` uses the FSRS-6 defaults while every other read uses the vault's fitted set. None of the three owner copies has a fitted set (`fitted_parameters` empty), so they agree today; a vault that runs `learnloop fit` sees the card disagree with the knowledge map and the queue.

## 3. What changed

**One expression, three entry points, all in `scheduling/fsrs.py`.**

- `_curve(stability, elapsed_days, decay)`: FSRS-6's curve, `(1 + (0.9 ** (1 / -decay) - 1) * elapsed / stability) ** (-decay)`, written once. It takes Python floats or float64 arrays and does no clamping.
- `forgetting_curve(stability, elapsed_days, weights)`: F1's clamps over `_curve`. Still the curve at plain stability, for FSRS itself: `apply_review`, `fsrs_fitting` and `evaluation` (the exempt modules, unchanged).
- `retrievability(stability, elapsed_days, weights)`: the scalar read. Today its body is `forgetting_curve(...)`. It is the place RE8's effective stability goes, so FSRS's update keeps reading plain stability.
- `retrievability_array(stability, elapsed_days, weights)`: F2's clamps (the `1e-12` floor, `np.where`, `np.minimum(np.maximum(...))`) over `_curve`.

`old_vs_new.py` (scratch) runs the base's two definitions, copied verbatim, against the tip's entry points over the grid above (with NaN and infinity on both axes, `None`, float32, 1-D, 2-D, one-element and scalar inputs, seven decays) and 2,000,000 dense pairs. That is 2,014,396 comparisons, with **0 differences in any byte**.

**The copy deleted.** `router_objective/memory.py:274` `Fsrs.retrievability` is gone. Deletion proof (§2.1), at this tip: its callers were `Fsrs.review` (`memory.py:295`), `value.py:765`, `:856`, `:893` and `objective_inputs.py:429`, `:531`. All of them now call `retrievability_array` with the same weights. Nothing else names it: no `getattr` or string dispatch, no sidecar registry or Typer entry, and no frontend, phone or MCP caller (the `retrievability` field in `apps/.../dto.ts` is a stored column's name). Replay and upgrade reach the rollouts only through `value.py`. Tests that read it were ported to call `retrievability_array` with plain values (T4): `rospeed_ad_link_helpers.py` (the reference copies of the old `value.py` methods), `test_rofu_review_draw.py:159`, `test_rofu_speed.py:169` and `test_ro4_value.py:164`. Each check still compares the same values against the same expected values, at the same tolerance.

**Why the rollouts call the function and not a method.** The first version kept `Fsrs.retrievability` as a one-line delegate. That added two Python frames to a call the numeric policy makes about 10,800 times per evaluation (64 draws, 22 topics). In-process A/B over 80 alternating evaluations: median +0.2%, minimum +0.7%. Calling `retrievability_array` directly leaves one added frame, the shared `_curve`. That frame is the irreducible cost of one expression shared by a scalar and an array form, and it is below what the measurements can resolve (§5).

**The objective's two one-value reads keep the array form.** `objective_inputs.py:429` (the combiner's trace join) and `:531` (`check_sensors`) call `retrievability_array` on one-element arrays, as before. A switch to the scalar form would move the stored sensors by up to one ulp (RE2-1). A comment at each site says so.

**`decision_state.prepare`'s injected callable is renamed** from `forgetting_curve` to `retrievability`, along with its five callers (`daily_plan/engine.py`, `daily_plan/lesson_suggestion.py`, `followup_run/router.py`, and `learnloop_sidecar/handlers/queue.py` twice) and its three test calls (`test_ro0_rows9_13_decision_state.py:151`, `:157`, `test_ro0_codex_review.py:320`: the keyword only; `:320` with a one-line `sed` of that exact text). It stays injected because router_objective sits below scheduling. The local variable `retrievability` in `_item_rows` became `recall`.

**Call-site swaps** (each `forgetting_curve` becomes `retrievability`, same arguments): `learner_context.py`, `daily_plan/reentry.py` (`fsrs.retrievability`, since the module's own `retrievability` adapter keeps its name for `daily_plan/headline.py`), `daily_plan/router_card.py`, `goals/goal_projection.py` (two), `scheduling/family_memory_model.py`, `scheduling/review_log.py`, `scheduling/scheduler.py:3073` (a call-site swap only, the import line and one call: the parallel due-queue step's file), `sim/runner.py`, `learnloop_sidecar/handlers/knowledge_map.py`.

**Import contracts.** `router_objective.memory -> scheduling.fsrs` and `router_objective.value -> scheduling.fsrs` join `frozen-cross-package-cycles`'s ignore list with the reason: `fsrs` imports only numpy and `learnloop.numeric`, so these edges cannot form a runtime cycle. The same reason already covers `field.memory`, `attempts.attempts`, `goals.goal_projection`, `params.fitted_params`, `sim.runner`, `substrate.administration_adapters` and `substrate.card_lineage` into `fsrs`. `fsrs.py` now imports numpy; every entry point (CLI, sidecar) already had numpy loaded before it.

**Left alone, and why.**
- `scheduling/fsrs_fitting.py` and `scheduling/evaluation.py` (exempt): the fit's log-loss and the calibration report evaluate the curve itself at plain stability and keep calling `forgetting_curve`.
- `daily_plan/reentry.py:64` and `objective_inputs.py`'s closure are adapters (timestamps to elapsed days; one value through the array form), not copies. They stay as callers.
- The curve's inverse, `fsrs.interval_for_retention` and `scheduling/intent/recall_targets.ratio`, computes days until a target recall, not a read of recall. RE8's stability cancels out of `ratio`. The guard allows `recall_targets.py` by name, with that reason.
- RE8's open question, for its step: `review_log.predicted_retrievability_by_attempt` (field outcomes, rebuilt on replay) and `family_memory_model` (the field memory arm) now read through `retrievability`. If RE8 changes the read, those derived rows change on rebuild, which RE8 §1's "replay of FSRS unchanged" may or may not intend. `memory.Fsrs.review` (the rollouts' vectorized FSRS update) reads `retrievability_array` too. Under RE8's rule ("FSRS's own updates stay plain") it would need the plain curve over arrays, which does not exist yet (no speculative entry point here).

## 4. The guard

`tests/test_one_retrievability.py`:
- An AST check over every file under `src/` (all four packages) and `scripts/`. It fails on an import, name or attribute reference to `forgetting_curve`, or on a definition of `forgetting_curve` or `retrievability_array`, outside `scheduling/fsrs.py`, `fsrs_fitting.py` and `evaluation.py`. It also fails on the curve's arithmetic (weight 20 read, a power whose exponent negates the decay, or `0.9 ** ...`) outside `fsrs.py` and `scheduling/intent/recall_targets.py`. Each allowance carries its reason, and the failure message says where a read goes instead. A second test fails when an allowance is no longer needed.
- **Fail-first:** run over the base's tree (`git show c85993a087:<file>` for every tracked `.py` under `src/` and `scripts/`, `failfirst.py` in scratch), the check names 33 places: all 30 references to `forgetting_curve` at the call sites above, and the memory model's copy three times (weight 20, `0.9 **`, the negated decay). Synthetic snippets (that copy, a direct import, `fsrs.forgetting_curve`, `** -weights[20]`) are flagged. A read through `retrievability` and two other powers (`2.0 ** (-elapsed / halflife)`, `d ** (-w[12])`) are not.
- **Plain values:** known values pinned at the base (four at the default decay, one at 0.5), the scalar exactly, the array form to one ulp; the curve at 0.9 when elapsed equals stability; the edges (elapsed 0 and negative gives 1, stability `None`, 0, negative or NaN gives 0, the power law's long tail stays positive, float32 in gives float64 out); the read equal to `forgetting_curve` bit for bit (2,000 pairs); the array form equal to the scalar within one ulp element by element (4,000 pairs at four decays, RE2-1) and byte-equal to itself one value at a time; broadcasting as the rollouts call it ((64, 22) stability against (64, 1) times).

## 5. Proof

**No value moved.**
- The base's two definitions (copied verbatim) and the tip's entry points agree byte for byte on 2,014,396 inputs (§3).
- The numeric policy's rollouts (`value.evaluate` on `test_rofu_speed`'s copy-shaped decision: 22 topics, 64 draws, seed `s`, per-block and merged) give the same digest of every candidate's `q_draws` and terms at the base and the tip, in the same process and across processes.
- One queue build per copy (`build_due_queue`, a read: no session, `persist_explanations=False`, frozen clock) gives the same digest of every item's id, priority and components at the base and the tip, on the linear_algebra (43 items) and arxiv_v2 (32 items) copies.
- `decision_state.prepare` on each queue's first 20 candidates gives the same receipt content at the base and the tip, with `LEARNLOOP_CODE_REVISION` fixed (the receipt names the commit).

**P-draw.** The draw-for-draw harness of `docs/reviews/router-speed2.md` is not in the repository (as an earlier step found), and `tests/goldens/due_queue` is not on this base. Instead: the pinned-draw router tests (every `test_ro*`, `test_rofu*`, `test_rospeed*`, daily-plan, objective and scheduler test, §6) pass unchanged, and the rollouts' digest above is equal at fixed draws.

**Replay on the head fixture.** A backup-API copy of `fixtures/migration_head` was rebuilt live at its own tag (`rebuild_all_derived_state` under the tests' below-floor allowance, frozen clock), twice with the base's code (`git archive c85993a087 src` on `PYTHONPATH`) and once with the tip's. Of 402 tables (941 rows, 11 non-empty derived tables), 381 are byte-equal between the two base runs, and the tip equals the base on all 381. The other 21 differ between two base runs as well (fresh ids: activity cards and observations, grade interpretations, measurement events, `derived_state_rebuilds`, ...). On those 21 the tip's row counts equal the base's.

**P-shadow.** The three copies in `learnanything-ad1/fixtures-local/owner-copies-mvp058` (at `mvp-0.58`) were copied twice with `copy_tree_with_databases` under `fixtures-local/re2/{before,after}/`. Each set was upgraded to `mvp-0.59` and run through `learnloop rebuild --shadow --json`: `before` with the base's code, `after` with the tip's. Counts only; the copies are deleted.
- `learner_state_diff`: identical before and after on all three (facet 80/3/7 unchanged, mastery 21/18/34, schedule 99/77/32; nothing added, changed or removed).
- `schedule_effects`: no due date moved, live database unchanged. The whole report is equal apart from run stamps.
- A row-by-row comparison of the two upgraded databases differs only in ids and timestamps. One other difference was the timing harness's own: the `before` copies had queue builds run on them, and `due_followup_tasks` lazily marks an expired follow-up task, as its docstring says.

**Identity pins** unmoved: `test_identity_pins` and `test_retired_config_identities` pass with no `--write`. **Structure ratchet:** `test_structure_ratchets` passes with no number risen.

**Latency.** All measured on this machine. The timing script (`timing.py`, scratch) ran once with the base's code and once with the tip's, both with `LEARNLOOP_CODE_REVISION` fixed. Times in microseconds per call are the best of 9 repeats. Times in seconds are min and median of 7 runs (evaluations) or 5 runs (queue builds and receipts).

| measure | base | tip |
|---|---|---|
| array read, 1 value (µs) | 3.885 | 3.882 |
| array read, 64 values | 4.112 | 4.113 |
| array read, 256 values | 5.092 | 5.078 |
| array read, 64 × 22 | 9.091 | 9.070 |
| scalar read (µs) | 0.230 | 0.253 |
| array reads per evaluation | 10,815 | 10,815 |
| rollouts, per-block, 64 draws (s, min / median) | 0.5900 / 0.5991 | 0.5897 / 0.5942 |
| rollouts, merged sessions | 0.3654 / 0.3696 | 0.3671 / 0.3698 |
| queue build, linear_algebra | 0.0140 / 0.0147 | 0.0141 / 0.0149 |
| queue build, arxiv_v2 | 0.0195 / 0.0198 | 0.0188 / 0.0190 |
| decision receipt, linear_algebra | 0.0079 / 0.0087 | 0.0080 / 0.0080 |
| decision receipt, arxiv_v2 | 0.0084 / 0.0092 | 0.0080 / 0.0081 |

Alternating whole processes, base then tip with the order swapped each round, 12 rounds of 8 evaluations: base median 0.5988 s (min 0.5860), tip median 0.6003 s (min 0.5900). That is +0.25% median and +0.7% min, with the same digest. The base's own runs spread over about 4%. Expected from the one added frame: about 0.1 µs times 10,815 calls, about 1 ms, or 0.15%. The scalar read adds two frames (`retrievability`, then `forgetting_curve`, then `_curve`), about 0.02 µs. Its callers make at most one call per queue item or per candidate, so a queue build doesn't show it. The first version (a delegating `Fsrs.retrievability` method) measured +0.2% median in-process over 80 alternations and was replaced (§3).

## 6. Tests and gates

- `scripts/affected_tests.py` on the diff without `pyproject.toml` (which alone selects the whole suite) selects 1,399 of the test files: `fsrs.py` is imported almost everywhere. All 1,399 ran under `-m "not arc_close"`, in chunks of 100 at `-n 4` behind the full-suite lock. The first set was every scheduler, router-objective (`ro*`, `rofu*`, `rospeed*`), daily-plan, objective, re-entry, goal-projection, router-card, queue, FSRS and evaluation test, plus the gate's named tests (`test_identity_pins`, `test_retired_config_identities`, `test_architecture`, `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_structure_ratchets`, `test_one_retrievability`). Result: **30,580 passed, 104 skipped, 10 xfailed (the existing strict ones), 0 failed**.
- `lint-imports --no-cache`: 42 kept, 0 broken. `ruff check`: clean. The four vault validators pass. `check_gate_partition.py`: 30,855 collected, landing 30,795 plus arc_close 60.
- Vault references were regenerated once after the source commits (24 generated notes, `Reference/Modules` and the router objective's config fields, whose cited lines moved). A second run changes nothing.

**Assertions changed: none.** Tests edited without touching what they check:
- `test_ro0_rows9_13_decision_state.py` and `test_ro0_codex_review.py`: the `prepare` keyword `forgetting_curve=` became `retrievability=`.
- `test_ro4_value.py:164`, `test_rofu_speed.py:169`, `test_rofu_review_draw.py:159` and `rospeed_ad_link_helpers.py` (three lines in its reference copies): `fsrs.retrievability(s, e)` became `retrievability_array(s, e, fsrs.weights)`, with the same values compared at the same tolerances.

Not run: the `arc_close` tests (only the arc-close gate runs them), the durability lane and the full suite (the orchestrator's landing gate).
