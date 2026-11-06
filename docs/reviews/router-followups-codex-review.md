# Router objective follow-up batch: Codex review (`router/ro-followups`)

Review job `/home/saturn/.cache/codex-agent/jobs/20261105-215240-rNmMSZ` (gpt-6.1-sol) on the batch at
`122e47603b` (base `e7a7d7734f`, successor mvp-0.50). Three Medium findings, all reproduced first with a failing test
and fixed; none rejected. No model request added, no paid call, no schema change (head 246), synthetic vaults only.

## Review

### Findings

| Id | Severity | Title | Verdict | Commit | Test (fails on the pre-fix source) |
|---|---|---|---|---|---|
| F1 | Medium | The carried-valuation kill switch leaves the new fitting behaviour active | fixed | `fb2442fb96` | `tests/test_rofu_carried.py::test_the_switch_turned_off_after_carriers_exist_reads_the_predecessors_transitions` |
| F2 | Medium | The unconditional merged sessions can change serving below the successor tag | fixed | `235b7218fc` | `tests/test_rofu_speed.py::test_a_deadline_admits_more_draws_merged_so_the_default_is_the_per_block_loop`, `::test_the_numeric_policy_merges_only_at_the_tag_with_its_switch` |
| F3 | Medium | Early published answers lose their carried valuation permanently | fixed | `1b7c1f3285` | `tests/test_rofu_carried.py::test_an_early_publication_served_keeps_its_carried_valuation` |

**F1.** Reproduced on a synthetic mixture vault at mvp-0.50 (the no-model branch, 8 boundaries, carriers in the
log): with `carried_in_prefetch = false` set afterwards, `tail_data.logged` still returned rows with
`carried_source = "later_prefetch"`. Fix: `logged` applies `_with_late_carried` only when
`tail_data.carried_in_prefetch_on(config)` (the tag, the objective serving and the switch); the chooser's `_carry_on`
asks the same predicate, so the serving and the reading side cannot disagree. The test turns the switch off after
carriers exist and compares with the predecessor's reading of the same traces (`_with_late_carried` as the
identity): the transitions (decision, generator, reward, `next_v_tail`, `next_phi`, cutoff kind), the censoring
counts and the fits are equal, and the censoring differs from the switch-on reading (the late records were lifting
`cutoff_unmatched`).

**F2.** Reproduced: the same 22-topic synthetic decision (5 candidates incl. a probe, seed `s`), a clock charging one
unit per FSRS update, a budget of 2.5 first batches (16,205 units), refining up to 64 draws:

| Path | Completed draws | Numeric choice |
|---|---:|---|
| Per-block loop (mvp-0.49) | 16 | `stop_for_today` |
| Merged sessions | 64 | `a` |

Codex's 8 vs 32 draws on its own instrument agree in kind: the fixed-draw equality does not cover a deadline. Fix:
`value.MERGED_SESSIONS` is gone; `_Model`, `evaluate`, `baselines` and `gain` take `merged_sessions` (default False,
the per-block loop), and the numeric policy passes `objective_chooser._merged(config)` (the tag, the objective
serving and the new `[router_objective] merged_sessions`, default true) to every rollout of a decision: the
evaluation and its refinement, the LLM correction, the carried valuation, the baselines and the day's gain curve
(the day's price runs inside the same deadline, so it is gated too). The key is a structural kill switch in
`params/parameter_registry.py`; every defaults snapshot is recomputed (41 versions; the frozen mvp-0.49 digest in
`test_rofu_successor.py` still holds with the batch's keys dropped). Serving time at the tag is item 3's (arxiv_v2
shape, 8 draws: 423 ms per-block, 232 ms merged); below the tag, or off, a decision runs the per-block loop again,
so it takes mvp-0.49's time and completes mvp-0.49's draws within its deadline (the test's default run: 16 draws,
the per-block values exactly).

**F3.** Reproduced with a gated LLM (`timeout_seconds = 3`): the second decision served `published_uncorrected`
with `residual.previous.status = carried` and **no** `q_status`, so `_defer_carry` registered nothing and the
transition into it stayed `cutoff_unmatched`. Fix: at the tag with `carried_in_prefetch`, every answer that can serve
carries its own carried valuation (`NumericPolicy.carried`, a field never serialized): an early publication's
residual is pending and its callable is frozen to its own uncorrected inputs and actions (the same factory as the
final answer's, the first batch's draws, the carried cutoff); the final answer carries its own. The serve registers
the one it took, so the handoff no longer depends on whether the serve or the job's completion comes first; the
`DEFERRED` material key (installed only at completion) is gone. Off, or below the tag, the publication is RO6's
exactly (`early_carry` is None, no field set). The test serves the early publication, releases the LLM, lets the jobs
and the next prefetch run, and checks: the published decision's `previous.q_status = not_valued_before_the_serve`,
`deferred_to = next_prefetch`; a later trace's `carried_for` holds it `valued`, with the `q` of an evaluation at the
carried cutoff on uncorrected inputs (no effect slope); the transition into it is valued at `previous_cutoff`
(before: censored).

Other commits of this step: `4944977efb` (four version-pin test files, test-only) and the record (this file, the
corrected claims in `router-followups-nov5.md` and the spec's as-built, the regenerated architecture reference).

### Claims that did not hold (corrected in `docs/reviews/router-followups-nov5.md` and the spec's as-built)

- "Each part that changes serving has its own switch" / "off ... mvp-0.49's exactly": now true for item 3
  (`merged_sessions`, F2) and item 4's reading side (F1); the switches table lists `merged_sessions`.
- "Before the completion event, so a serve always finds it": replaced by "every answer that can serve carries its
  own" (F3).
- "Numerical only": the merged path is a serving change through the deadline (F2); the note in `value.py` says so.

### Spec conformance rows left as recorded

The unbuilt items Codex lists (floor draws as contrasts, the two caches, the κ0 availability covariate and the
goal-date sensor inside `V`, the memory forecast curve and the whole-day return gap, FG1d's pins, RO1's admission
anchor and the upgrade's mastery stamps) are recorded in `docs/reviews/router-followups-nov5.md` with the smallest
way to finish each; this step does not widen scope. Pending carried valuations are process memory (lost on a
restart: the transition stays censored, as mvp-0.49's), as recorded there.

### Gate

Every Python command outside pytest ran under `env -i PATH HOME=<empty> CODEX_HOME=<empty>
LEARNLOOP_CONFIG_DIR=<empty>` (scratch dirs outside the worktree); every pytest under `systemd-run --user --scope
--quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`; the batch under `flock /tmp/learnloop-fullsuite.lock`.
No full suite (the landing gate runs it once).

| Step | Command / selection | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`; `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `uv run lint-imports --no-cache` | 43 kept, 0 broken |
| Reproduce-first | each new test on the pre-fix source | F1: 1 failed (`carried_source` still `later_prefetch` with the switch off); F2: 2 failed (the default evaluation merged; the numeric policy never passed `merged_sessions`); F3: 1 failed (`previous.q_status` None on the served publication) |
| Fixed tests | `tests/test_rofu_carried.py tests/test_rofu_speed.py tests/test_rofu_successor.py tests/test_rofu_scope.py tests/test_rofu_learning.py tests/test_rofu_weeks.py`, `-n 6` | 47 passed |
| Targeted batch | 155 files (`docs/reviews/router-followups-codex-review.targeted-tests.txt`): every test file naming the objective chooser, `value`, `tail_data`, `tail_serve` or the mixture helpers; every `test_ro[0-9]*.py` and `test_rofu_*.py`; every file naming the defaults snapshots, the parameter registry or `RouterObjectiveConfig` (the config defaults snapshot and the version-pin files); the display-label audit (`test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`); `test_architecture` (frozen cycles); `test_cli_help_snapshot`; the process-launch allowlist (`test_ai_tool_isolation`, `test_e0_isolation`, `test_codex_tool_lockdown`, `test_codex_lockdown_round3`); `test_table_roles`, `test_registry_audit`, `test_module_catalog_inventory`, `test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_sidecar_registry`, `test_mobile_allowlist`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_public_tip_guards`, `test_sqlite_file_copies`, `test_data_capture_successor`, `test_config_refactor`; `-n 6` | 2831 passed, 16 skipped, 3 xfailed, 5 failed: four version-pin files the batch's successor commit missed (`test_attempt_content_state_successor`, `test_cold_retry_reschedule`, `test_ad23_successor` x2, `test_batch3_landing`, still naming mvp-0.49 as the latest; fixed test-only in `4944977efb`) |
| Pin files rerun | those four files, `-n 6` | 88 passed, 3 skipped |
| References | `db_generate_reference.py`, `db_validate_reference.py` (1174 effective leaves with `merged_sessions`: errors []), `module_generate.py`, `module_validate.py` (PASS), `validate_vault.py` (passed) | ok |
| Not applicable | no migration or DB/connection code (no durability lane), no frontend, nothing under `src-tauri` | |

Paid routes: none added; no model request, no paid call made in this step.

## Landing ruling R1: the rollouts' review draw (`consistent_review_draw`, `3d018ebf50`)

Item 7's finding, fixed at landing. On `2db795f6d7` (the batch's `5919b5a08c` merged with main `c2e810f940`, docs
only): the rollouts drew a practised topic's practice outcome from AD's predictive `σ(η)` and applied it through
FSRS's lapse branch, while every use is scored on the combiner over `η` and `R` (§8.4).

**Fix.** At the tag with `[router_objective] consistent_review_draw` (default true; a structural kill switch in
`params/parameter_registry.py`), `value._Model._graded` draws a practised topic's result from
`σ(a0 + aA·η + aR·(logit R − η))`, with `R` FSRS's at the elapsed lag and the draw's own coefficients
(`memory.perform`'s formula). Choice made here: the belief also observes the result under that likelihood (its
prediction at `bel`, its slope in `η` `aA − aR`, the one-step Laplace update). Otherwise the belief would read a memory
effect as ability: a success at `R ≈ 1` would move `bel` as though `σ(bel)` had predicted it. An unpractised topic's
first attempt and a probe's observation still read AD's predictive, because the combiner has no `R` for them.
`evaluate`, `baselines`, `gain` and the belief model take `consistent_review_draw` (default False).
`objective_chooser._rollout_options(config)` hands both rollout options (with `merged_sessions`) to every rollout of a
decision, or to none of them. The trace names the draw (`versions.review_draw = review_draw_memory_model_v1`) only
when it serves. All 41 defaults snapshots were recomputed for the new key. The key is not added to RO6's generator
payload, following `combiner_trace_outcomes` and `merged_sessions`. As a result, switching it changes `Q` under the
same generator version.

**The probe** (8 practised topics, `m̄` 30, blocks of 10 minutes and 3 items, 64 draws, seed `k`, `η` sd 0.55,
1 day since the last review; `price.seed_from_gain` with no earlier positive value). The record's script was rerun
unchanged under `env -i`.

| `η`, `S` | Marginal at `m̄`, before (per minute) | After | Average to `m̄`, after | κ0 seed after |
|---|---:|---:|---:|---|
| −0.5, 40 | −0.000219 | −0.000388 | −0.000385 | tail average, 0 |
| 0.5, 40 | −0.000467 | −0.000907 | −0.000049 | tail average, 0 |
| 1.5, 40 | −0.001776 | **+0.000434** | −0.000704 | **day seed, 0.000434** |
| 0.5, 2 | −0.000342 | −0.000443 | +0.000641 | tail average, 0.000641 |
| 1.5, 2 | −0.002159 | **+0.000390** | −0.000195 | **day seed, 0.000390** |

After the fix, κ0's seed gets a positive day-seed value in two of five cases (`η` 1.5 at both `S`). §8.6's floor
would then keep that value on later days. The test pins these numbers and asserts no sign as a law.

What the probe also shows. These are diagnostics, not pinned, and not built: each needs a ruling.

- **At 64 draws the sign is mostly noise.** At 512 draws the marginal is +0.00006, −0.00019, −0.00067, −0.00016,
  −0.00076 before the fix and +0.00015, −0.00026, +0.00007, −0.00022, −0.00019 after. The differences are of the order
  of 1e-4 per minute either way, with mixed signs. Item 7's "negative in every case" partly reflects the 64 draws.
- **The combiner's coefficient draws carry most of what is left.** With the combiner at its prior mean (variance 0,
  64 draws), the marginal is +0.00012, +0.00002, +0.00005, −0.00003, +0.00010 before the fix. After the fix it is
  **positive in all five cases** (+0.00015, +0.00029, +0.00028, +0.00001, +0.00027), and `G` rises with `η`. The
  prior on `aA − aR` is `N(0.5, 0.5)`, variance 0.5 and sd 0.71, because each coefficient's variance of 0.25 adds
  (an earlier version of this line said `N(0.5, 0.5²)`). It puts about 24% of draws at a negative slope in
  `η`. `η` grows by `γ` (0.2) on every practice opportunity without a ceiling, and in the probe reaches about 41 on
  the logit scale by `C + H` (180 days, about 9 practices a day over 8 topics). In those draws `P(perform)` falls
  toward 0 as practice accumulates. With the consistent draw, those draws now lapse in FSRS as well. That is why `G`
  is lower after the fix (by 0.7 to 1.1) and falls with `η` at `S` 40. The smallest finishes, for a ruling: the
  combiner fitted on real rows will narrow the slope's variance on its own. Otherwise the slope could be
  parameterised as positive by construction (a log-normal on `aA − aR`), or `γ`'s effect could saturate (an upper
  bound on `η`'s logit, or `γ` shrinking with `p̄`). Each of these changes every valuation.

Tests (`tests/test_rofu_review_draw.py`). On a full `git archive` of the pre-fix tree (`2db795f6d7`), 16 of the 18
fail. The two that pass are the switch-off and below-the-tag serving cases, which are identities. An earlier version
of this record said "all 18 fail". That run pointed pytest at an archive of `src/` alone, so the serving tests also
failed for want of `migrations/`.

- the probe with the switch off equals the pre-fix source exactly;
- the probe after the fix pins its numbers and the seed;
- with the switch off, three decision-shaped evaluations equal the pre-fix source exactly. Each covers every
  candidate's and the reference's `Q` draws plus the baselines, as a sha256 computed on the pre-fix source: the
  22-topic copy shape, fewer topics than slots, and dated uses in the horizon;
- the draw is `u < memory.perform` for a practised topic and `σ(η)` otherwise, and the belief's update matches;
- a review 10 minutes after a review lapses about 50% of the time under the old draw and under 2% with the switch on;
- the numeric policy passes the switch only at the tag with it on, for every rollout (evaluate, baselines, gain), and
  only then does the trace carry `versions.review_draw`.

| Step | Command / selection | Result |
|---|---|---|
| Merge | `git merge c2e810f940` (docs only) | no conflict, `2db795f6d7` |
| Reproduce-first | the record's probe on the pre-fix source; the new test file on its `git archive` | negative marginal in all 5 cases; 16 failed, 2 passed (the identities) |
| Targeted | 187 files, `-n 6`: the 155 of this review's list, with every `test_rofu_*`, `test_ro6_*`, `test_ro5_*`, `test_ro4_*`, `test_ro0_*`, `test_ro1_availability*`, `test_ro2_ad_raw_document_reads`, `test_followup_*`, the display-label audit (`test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`), `test_cli_help_snapshot`, `test_data_capture_successor`, `test_registry_audit`, `test_architecture`, and every file naming the defaults snapshots, `LATEST_ALGORITHM_VERSION`, mvp-0.49, mvp-0.50 or the batch's version | 3541 passed, 16 skipped, 6 xfailed |
| Durability | `--durable-sqlite`: `test_rofu_review_draw`, `test_rofu_successor`, `test_rofu_speed`, `test_rofu_learning`, `test_registry_audit` | 71 passed |
| Import contracts | `lint-imports --no-cache` | 43 kept, 0 broken |

## Landing ruling R7: practice's learning increment, the rollouts against AD's own model (recorded, nothing built)

**AD's form** (`adaptive_difficulty/state.py`, `View.learn`; `model.py`, `Bank.add_linear` and `Bank.drift`):

- **Practice.** Each practice opportunity adds `γ·w` to the item's cell mean (`w` is the item's weight on the facet).
  In the subject view, each coupled facet's cell also gets `corr·γ·w`.
- **No growth bound.** The update is linear in the number of opportunities, with no ceiling, no saturation and no
  dependence on the current level.
- **Time.** `drift` grows only the cell's variance (`DRIFT_PER_DAY` 0.01 per day). It has no mean reversion, so the
  latent mean never decays.
- **Prediction.** What AD bounds is the predictive, not the growth: `F(η) = g + (1 − g − λ)·E_ε[σ(η − aε)]`, with
  lapse `λ` 0.02, tops out at `1 − λ`.
- **γ.** `γ`'s prior is `N(0.2, 0.01)` (`priors.GAMMA_PRIOR`), and its posterior is RO5's read.

**The rollouts** (`value._Model._practice` and `_practice_batch`) add `γ·mass` to `η` per opportunity: AD's form,
linear and unbounded. The draw's `γ` comes from AD's posterior. So per the ruling nothing is aligned, and no ceiling
is invented here.

**AD-level finding (for the owner and the next AD stage).** On R1's probe (η 0.5 at the start, S 40, 64 draws, R1's
draw and R6's combiner), the tail practises about 9 opportunities a day over 8 topics. The mean true `η` per topic
climbs at about 0.23 a day:

| Day | η (true) | Belief | P(perform), mean of the draws |
|---:|---:|---:|---:|
| 0 | 0.76 | 0.72 | 0.847 |
| 7 | 2.40 | 2.29 | 0.911 |
| 30 | 7.79 | 7.44 | 0.970 |
| 90 (`C`) | 21.86 | 20.88 | 0.992 |
| 150 | 35.93 | 34.35 | 0.995 |

By `C + H` (180 days) it reaches about 42. A latent this far out on the logit scale, with no forgetting and no
saturation, means any coefficient that weights `η` dominates the forecast. R6 removes the sign problem this created,
but not the scale.

Differences between the rollouts and AD, recorded and not built (each changes every valuation):

- the rollouts' belief variance does not drift by `DRIFT_PER_DAY`;
- the rollouts' predictive is `σ(η)`, not AD's `F(η)` with its guess and lapse;
- coupled facets' transfer is not simulated.

## Landing ruling R6: the combiner, monotone in ability by construction (`58b727566e`)

`logit P = a0 + aA·η + aR·(logit R − η)·[practised]`: `η`'s slope is `aA` for an unpractised topic and `aA − aR` for
a practised one.

**What changed.** At mvp-0.50 the combiner takes `memory.FORM_MONOTONE`. This applies at the tag with the objective
serving (`router_objective_switches.monotone_combiner_on`). It was built in `58b727566e` with **no switch**, because the
ruling says "behind the tag only". On the orchestrator's answer it now has one: `[router_objective]
monotone_combiner` (`0ad1ebe661`; structural, default true, in RO6's generator payload per R8). Off, or below the tag,
the combiner is RO4's linear one.

- **Parameters.** They are `(a0, log aA, log b)` with `b = aA − aR`, under a diagonal Gaussian. Both slopes are
  therefore log-normal and positive in every draw, and `aR = aA − b` is derived (either sign).
- **Both slopes, not one.** The ruling names `aA − aR`, but "P(perform) cannot fall as eta rises" also needs `aA > 0`
  for unpractised topics, so both are positive. My choice.
- **Prior.** It is moment-matched to the linear prior's own marginals: `aA` has mean 1 and variance 0.25; `aA − aR`
  has mean 0.5 and **variance 0.5** (sd 0.71). Correction: the ruling quotes "N(0.5, 0.5^2)", which was my
  misstatement of the linear prior; its actual spread is variance 0.5. The orchestrator's answer keeps the match to
  the actual marginals. `aR` is no longer independent of `aA`: its implied variance is 0.75, not 0.25.
- **Fit.** `fit_combiner` fits in the same form when handed the monotone prior. It runs damped Newton on `θ`, with
  Fisher scoring where the observed Hessian is not negative definite, and takes the Laplace variance from the
  observed Hessian at the mode. `objective_inputs._combiner_prior` hands the monotone prior to RO5's checks fit,
  item 2's trace-fed fit, and the prior with `fitted_models` off.
- **Draws and the belief world.** `Combiner.coefficients(z)` draws the natural `(a0, aA, aR)`; its linear branch is
  the old expression, so it is bitwise mvp-0.49's below the tag. `Combiner.at_mean()` gives the belief world's point,
  where a log-normal slope's mean is `exp(μ + σ²/2)`.
- **Trace.** At the tag, the trace's `memory_model` adds `form` and `coefficients_at_mean`.

**Step 4.** With `monotone_combiner` off, the combiner is RO4's linear one, so the every-switch-off identity holds
for the combiner too. Its reproduce-first: the serving test with the switch off at the tag fails on a full archive
of `342b991297` (the combiner stays monotone), while the tag-on and below-tag cases pass.

**R1's probe, marginal gain at `m̄` per minute** (with R1's review draw throughout):

| `η`, `S` | 64 draws, linear (before) | 64 draws, monotone (after) | 512 draws, linear | 512 draws, monotone |
|---|---:|---:|---:|---:|
| −0.5, 40 | −0.000388 | +0.000611 | +0.000146 | +0.000493 |
| 0.5, 40 | −0.000907 | +0.000709 | −0.000261 | +0.000628 |
| 1.5, 40 | +0.000434 | +0.000468 | +0.000073 | +0.000523 |
| 0.5, 2 | −0.000443 | +0.000510 | −0.000221 | +0.000554 |
| 1.5, 2 | +0.000390 | +0.000478 | −0.000186 | +0.000520 |

**What the probe shows after R6.**

- With the monotone combiner, κ0's seed is the day's seed in every case at both draw counts: 0.00047 to 0.00071 per
  minute.
- `G` rises with `η` again (64 draws: 15.554, 15.677, 15.766 at `S` 40), and is higher than the linear combiner's by
  2.6 to 2.9.
- The 64-draw and 512-draw marginals now agree to within about 1.2e-4.

For reference, the mvp-0.49 draw with the linear combiner gives: 64 draws −0.000219, −0.000467, −0.001776, −0.000342,
−0.002159; 512 draws +0.000060, −0.000194, −0.000667, −0.000164, −0.000764.

**Tests** (`tests/test_rofu_monotone.py`):

- the linear prior has about 24% negative practised slopes, and the monotone prior none, with the moments matched;
- the linear form is bitwise mvp-0.49's;
- no draw of a fitted posterior has a negative slope, including on adversarial rows where the linear fit finds one;
- the fit recovers known slopes, and its gradient vanishes at the mode;
- `P(perform)` is non-decreasing in `η` on every rollout draw;
- the probe is pinned at 64 and 512 draws, linear and monotone, with no sign asserted;
- the trace names the form at the tag only.

On a full `git archive` of the pre-fix tree (`b5d3d738ad`), 9 of the 12 fail. The 3 that pass are the two pins of the
linear form and the below-tag serving case. `58b727566e`'s message says 10 of 12; that run used an archive of `src/`
alone.

## Landing ruling R8: the batch's serving switches in RO6's generator payload (`0767b917bd`)

`router_objective_switches.FOLLOWUP_GENERATOR_SWITCHES` = `combiner_trace_outcomes`, `merged_sessions`,
`consistent_review_draw`, `scope_extension`.

- **Recorded and read the same way.** At the batch's tag, the trace records them as they served
  (`versions.serving_switches`). `tail_data.generator` reads them from the trace, and `objective_chooser.generator_now`
  from the config (`followup_generator_switches`), so the serve's generator and the trace's are one.
- **Below the tag.** No key is added, so RO6's payload keeps its bytes.
- **`carried_in_prefetch`** stays out. Strictly, it does reach serving: it changes which transitions feed the learned
  tail's fit, and so `ŵ` and the residual. But it does so as more data does, not as a change of the logger's
  definition.
- **R6's monotone combiner** needed no entry while it was the tag alone. Since its switch (`0ad1ebe661`)
  `monotone_combiner` is in the list, and so is R9's `ad_predictive_link` (`8a19c2698b`), making six switches.
- **No other switch of the batch** changes a decision's `V` or `μ`.

Tests (`tests/test_rofu_generator_switches.py`):

- at the defaults, one generator across decisions, equal to the one each decision was served under (`residual.generator`);
- each switch's flip is a new generator version (parametrized over the list, now six);
- `carried_in_prefetch` off leaves the generator unchanged;
- below the tag there is no key, and the payload is RO6's.

On a full `git archive` of the pre-fix tree (`f7a21cf602`, with the switch list inlined), 5 fail and the 2 identities
pass.

### Gate after R6-R8

| Step | Command / selection | Result |
|---|---|---|
| Targeted | 189 files, `-n 6` in a 5G scope: step 0's 187, `test_rofu_monotone`, `test_rofu_generator_switches`, and every test file naming `generator_payload`, `tail_data`, `fit_combiner` or `Combiner` | 3560 passed, 16 skipped, 6 xfailed |
| Durability | `--durable-sqlite`: `test_rofu_monotone`, `test_rofu_generator_switches`, `test_rofu_review_draw`, `test_rofu_learning`, `test_rofu_scope`, `test_ro6_landing` | 70 passed |
| Import contracts | `lint-imports --no-cache` | 43 kept, 0 broken |
| Not regenerated yet | the architecture reference (config leaves for `consistent_review_draw`, the module pages for `memory`, `value`, `tail_data`, `router_objective_switches`, `objective_chooser`, `objective_inputs`) | step 2 |

## Landing ruling R9: AD's own predicted success in the rollouts (`ad_predictive_link`, `8a19c2698b`)

**AD's predictive.** AD predicts success as `F(η) = g + (1 − g − λ)·E_ε[σ(η − a·τ0·ε)]`
(`adaptive_difficulty.model.residual_success`) on its latent ability. The lapse `λ` is 0.02, so `F` tops out at
0.98, and AD's practice adds `γ` to that latent.

**mvp-0.49's rollouts.** They read `σ(η)` on `η = logit p̄` and added `γ` there, so after practice they drew
successes above what AD itself predicts.

**What changed.** At the tag with `[router_objective] ad_predictive_link`, `value.AdLink` takes AD's lapse, residual
spread and Gauss-Hermite rule. `objective_inputs._ad_link` hands them in, so `value` stays a leaf. `g` is 0, for a
valued topic's unseen constructed item.

- The decision's `p̄` enters as `F⁻¹(p̄)`, so `γ`, reading's dose and a lesson all add on AD's latent. The decision's
  `η` variance is read as the latent's, since AD's posterior is on its latent.
- An unpractised topic's attempt (under either draw) and a probe's observation draw from `F(η)`.
- The combiner's `η` input, which was `logit p̄`, is now `logit F(η)`. At the combiner's prior mean an unpractised
  topic therefore reads `F` alone, and R1's practised draw reads the combiner over `logit F(η)` and `R`.
- The belief's Laplace step uses the same prediction and its slope in `η`.
- The trace names it (`versions.ad_link`).

**Its own switch, my judgment.** It is separable from `monotone_combiner`: one is the link to AD's predictive, the
other the combiner's coefficient sign. Each can be turned off and diagnosed alone, and both are in R8's generator
list. Belief-variance drift and coupled-facet transfer stay recorded as AD-level findings (R7's section).

**Reproduce-first.** I ran `scratchpad/rofu-landing/repro_r9.py` on a full archive of `0ad1ebe661` and on this tree.
Each row is an unpractised topic whose `p̄` is AD's `F` at the given latent, after ten practices (`γ` 0.2 each):

| AD latent | AD predicts | Pre-fix rollouts | After the fix |
|---:|---:|---:|---:|
| −1 | 0.6828 | 0.7565 | 0.6821 |
| 0.5 | 0.8767 | 0.9123 | 0.8753 |
| 2 | 0.9525 | 0.9737 | 0.9525 |
| 4 | 0.9760 | 0.9936 | 0.9770 |
| 40 | 0.9800 | 0.9977 | 0.9808 |

`tests/test_rofu_ad_link.py` fails to collect on the pre-fix tree (there is no `AdLink`).

**R1's probe** (R1's draw, R6's combiner), marginal gain at `m̄` per minute, `σ` (before) and `F` (after):

| `η`, `S` | 64 draws, before | 64 draws, after | 512 draws, before | 512 draws, after |
|---|---:|---:|---:|---:|
| −0.5, 40 | +0.000611 | +0.000355 | +0.000493 | +0.000382 |
| 0.5, 40 | +0.000709 | +0.000601 | +0.000628 | +0.000424 |
| 1.5, 40 | +0.000468 | +0.000344 | +0.000523 | +0.000274 |
| 0.5, 2 | +0.000510 | +0.000316 | +0.000554 | +0.000437 |
| 1.5, 2 | +0.000478 | +0.000402 | +0.000520 | +0.000288 |

- κ0's seed is the positive day seed in every case at both draw counts: 0.00027 to 0.00060 per minute.
- `G` is about 0.6 lower than with `σ`, because `F` stops at 0.98.
- 64 and 512 draws agree within 1.8e-4.
- Both sides are pinned: the `σ` side in `test_rofu_monotone`, the `F` side in `test_rofu_ad_link`.

**Cost.** The copy-shaped evaluation (22 topics, 5 candidates including a probe, 8 draws, merged, R1's draw, R6's
combiner) takes 270 ms with `σ` and 431 ms with `F` (median of 5). The 32-node quadrature runs on every `P(perform)`.

**Tests** (`tests/test_rofu_ad_link.py`):

- the link equals AD's `residual_success` to 1e-15, and its inverse and its slope check out;
- `p̄` enters as AD's latent and reads back as itself;
- an unpractised attempt and a probe draw from `F` under either draw;
- the belief's step is the Laplace step under `F`;
- no link gives mvp-0.49's path;
- the probe is pinned at 64 and 512 draws;
- the numeric policy reads the link only at the tag with its switch, and only then does the trace name it.

### Gate after the R6 switch and R9

| Step | Command / selection | Result |
|---|---|---|
| Targeted | 192 files, `-n 6` in a 5G scope: the 189 above, `test_rofu_ad_link`, and every file naming `residual_success`, `AdLink` or `ad_link` | 3610 passed, 16 skipped, 6 xfailed |
| Durability | `--durable-sqlite`: `test_rofu_ad_link`, `test_rofu_monotone`, `test_rofu_generator_switches`, `test_rofu_review_draw`, `test_rofu_successor`, `test_rofu_learning` | 81 passed |
| Import contracts | `lint-imports --no-cache` | 43 kept, 0 broken |
| Not regenerated yet | the architecture reference (config leaves for `consistent_review_draw`, `monotone_combiner`, `ad_predictive_link`; the changed modules' pages) | step 2 |
