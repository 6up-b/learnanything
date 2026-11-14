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

Both definitions run over a grid (the script in the orchestrator's scratch, `grid_compare.py`): elapsed in {0, 5e-324, 1e-300, 1e-12, 1e-9, 1e-6, 0.001, one second, one minute, 0.5, 0.999, 1, 1.5, 2.7, 3, 7, 10, 30.4, 100, 365.25, 1000, 1e4, 1e6, 1e9, 1e15, 1e300, -0.0, -1e-9, -0.5, -1, -1e6} by stability in {5e-324, 1e-300, 1e-15, 1e-13, 1e-12, 1e-11, 1e-9, 1e-6, 0.001, 0.01, 0.1, 0.212, 0.5, 1, 1.2931, 2.3065, 8.2956, 10, 36.5, 100, 1000, 1e4, 1e6, 1e9, 1e300, 0, -0.0, -1e-9, -1}, at decays {0.1542 (the default), 0.0658, 0.1, 0.2, 0.4, 0.5, 0.8}; F2 called on one-element arrays, on the whole grid as one array, and on float32 inputs; plus `None`, NaN and infinite inputs; plus a dense grid of 2,000,000 random pairs in the range a vault produces (stability log-uniform in [0.001, 1e5], elapsed 0, fractional, up to 30 days, up to ten years, and whole seconds) at four decays. numpy 2.5.1 on this machine (carson) reports AVX-512F.

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
