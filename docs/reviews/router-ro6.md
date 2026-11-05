# Router objective RO6: a learned tail (`router/ro6-learned-tail`)

Spec: `docs/specs/spec_router_objective_v1.md` §10 (as built: §10.1), §3.2, §4 rows 9 and 12, §8.9. Base `5f02be6eb2`
(RO5's branch: mvp-0.48, no migration; RO5 is landing now and this branch merges main after it, at the landing).
Successor **mvp-0.49** (`ROUTER_LEARNED_TAIL_ALGORITHM_VERSION`), rechecked at landing. **No migration.** Fakes only:
no paid call was made in this stage, no real request was sent, no owner vault was opened, no tracked working vault was
touched, no manual run touched a copy (none was needed: every measurement below is on a synthetic vault in a test).

## What exists

| Part | Where |
|---|---|
| Successor, upgrade (projection activation, journalled), defaults snapshot, the keys and the gate | `algorithm_versions.py`, `router_learned_tail_upgrade.py`, `config/schema.py` (`RouterObjectiveConfig.learned_tail`, `residual_prior_sd`, `residual_weight_prior_sd`), `config/template.py` (every snapshot recomputed; dropping RO6's keys reproduces mvp-0.48's base value), `router_objective_switches.learned_tail_on`, `params/parameter_registry.py` (two rules, four module constants), the openers (`cli/runtime.py`, `learnloop_sidecar/context.py`), `cli/app.py` |
| (1) Features and trajectories | `router_objective/learned_tail.py` (`belief`, `vector`, `NAMES`), `router_objective/tail_data.py` (`logged`, `rebuilt_features`, `transitions`, `generator`) |
| (2) The fitted Q evaluation of a frozen logger version | `learned_tail.fit` (FQE's fixed point under the labelled prior), `tail_data.fits` (one fit per generator version, its own transitions) |
| (3) How it enters: `Ṽ = V_tail + ŵ·V_residual`, `ŵ` | `router_objective/tail_serve.py`, `learned_tail.residual_weight`, `tail_data.contrasts`, `daily_plan/objective_chooser.run_numeric` (`learned_tail=True` from the objective's block decisions), `_trace` (the `residual` section and the four terms), `router_objective/trace.explain` (one plain line) |
| (4) Partial-history weights | `learned_tail.partial_history`, `tail_data.cross_check`, `tail_data.predicted_improvement` |
| (5) The report | `router_objective/tail_report.py`; `learnloop router objective-report`'s `learned_tail` section at the tag |
| The window's observed return (for the contrasts) | `router_objective/scores.py` (`window_uses`, `observed_return`, `observed_returns`; RO5's `score_decision` factored, behaviour unchanged) |
| (7) Specs | `spec_router_objective_v1.md` §10.1, status, §13; `spec_action_router_v1.md` §7.3's RO6 note |

## For the owner before landing: what it costs and how it is enabled

- **Enabled at the tag by default**, where RO4's objective serves. `learnloop upgrade` (default target) moves a vault
  from mvp-0.48; nothing recorded changes. `[router_objective] learned_tail = false` serves mvp-0.48 exactly (tested
  against mvp-0.48 with the draw and the numeric policy's seed pinned,
  `tests/test_ro6_serving.py::test_below_the_tag_and_switched_off_serve_mvp_048_exactly`).
- **Until randomized contrasts accumulate it changes nothing served**: `ŵ` starts at zero, so the numeric policy's
  argmax is RO5's (asserted at every decision of the serving test); the trace and the report fill in.
- **Paid routes: RO6 adds no model request.** No call per day.
- **Learner minutes: none.** RO6 adds no arm; it reads RO5's coin and checks.
- **Latency** (the only added serving work, inside the numeric policy's job before the rollouts): on the synthetic
  three weeks, median 22.5 ms and at most 96 ms per decision over 94 decisions; it grows with the number of traces
  (see "Not built").

## Choices where the spec was open, or the code had moved (the smallest alternative, recorded)

Codex review (job 20261105-125456-EfabRp, `docs/reviews/router-ro6-codex-review.md`) superseded parts of choices 5-9
and the cross-check: fourteen features (the cutoff's span added), the residual's inputs snapshotted at the decision's
moment, dated uses placed by their moment, the next state valued at the decision's own cutoff through the next
decision's trimmed rollouts (no average-rate move-back), the coin's cohort kept whole with per-arm observation
weights, the return reader as of its cutoff, and the window products over the complete sequence. The text below is
the stage as first built.

1. **No migration, no fits table.** The fit is recomputed from the traces and RO0's receipts as of each decision and
   frozen into that decision's trace (`residual`: the fit's standardization and coefficients, its version, size,
   noise and conditioning, `ŵ` with its slope and rank, each candidate's features, `V_tail`, `V_residual`, `Ṽ`), which
   is the receipt of the fit as of that decision. The trace rounds floats to six places, so the fit's numbers and the
   features are stored as exact strings and `V_residual` recomputes to float precision.
2. **Generator version** = the objective's, tail's and terminal's versions, `H`, the LLM policy's schema, the mix's
   seeds (`w₀`, `ℓ_L`, `ℓ_Q`, `s₀`) and floor `ε`, the algorithm version and RO6's feature version. The LLM's model id is
   not in it (a failed call's trace has none, which would make spurious change points); the report's comparators keep
   model ids apart, as RO4's. Smallest change if wanted: carry the last answered model id forward into the key.
3. **"Refit after every mixture change"**: the fit is refit at every decision (so after every change of `w`, `ŵ` or
   version); `π_ref` at each next state is that decision's logged served distribution (the mix under the stop coin),
   so a moving `w` within a version is part of the frozen logger's record. Serving uses the current version's own fit,
   or with none of its transitions yet the latest earlier version's ("version `k+1` uses the result").
4. **"Never fitted to TD loss alone"**: read with the report's reasoning ("never accept a tail on TD loss"): the fit is
   TD's fixed point plus a labelled Gaussian prior, and its share of the value is set only by `ŵ` from randomized
   contrasts, never by its TD fit.
5. **Model class**: Bayesian linear regression (ridge) on thirteen standardized features, no intercept (with no
   discount `Σ_a′ π = 1` cancels any level, which is unidentified and irrelevant to a decision). Why: one learner's
   log is one long dependent trajectory of hundreds of decisions a month; a deep net would fit noise and could not be
   read; a linear residual's every term is in the trace (§8.4's "linear first", T7 for anything richer).
6. **Features**: RO0 row 9's mastery numbers and pending reports, read at serve time by `decision_state`'s own readers
   and at fit time from RO0's receipt; the FSRS feature is the lag `log(1 + elapsed/S)` (monotone in retrievability),
   not `R` itself, because a trace does not hold the FSRS weights `R` needs. For mvp-0.47 traces (no `goal_dates`)
   days to go comes from the evaluation window's dated uses only.
7. **The reward**: §3.2's `R` estimated from what was observed: minus the objective's attention cost over the
   interval, plus each completed randomized check administered in it at `c_L·Y/r` (unbiased for the undated uses'
   `Σ c_L·P` given the checks' exact `r` and the pooled completion rate as of the interval's end), plus each dated use
   whose date falls in it at `ω·Y`. A population topic the day's draw could not reach has `r = 0` and contributes
   nothing (RO5's scores share this). No baseline is subtracted (it would move the target).
8. **§3.2's time and terminal handling**: one cutoff per decision; the next state's `V_tail` is moved back to it by
   `(C′ − C)·T_{C′}/H` (the reference row's net continuation per day at the horizon's end); a next decision past `C`
   (a gap of at least `H` days) is censored `past_cutoff`, not bootstrapped through `T_C`.
9. **`ŵ` "by slope and rank"**: the slope is `b` in `Ĉ ≈ a·ΔV_tail + b·ΔV_residual` with `a` flat (the realized
   contrast is over the 14-day window, the predicted ones over the cutoff, so the tail's contrast is not on `Ĉ`'s
   scale) and `b ~ N(0, 1²)` (labelled); the rank is Spearman's correlation of `ΔV_residual` with the forced arms'
   contrast less the tail's part, read as `P(rank > 0)` (normal approximation; one half with fewer than three forced
   arms). `ŵ = clip(E[b], 0, 1)·P(rank > 0)`: no threshold, no minimum sample; the clip is structural (0: no residual,
   1: the fit at its own scale). The mix's own floor draws are randomized too and are not used (the spec names the coin
   and the checks); adding them is the smallest way to more contrasts.
10. **The mid-block follow-up** (`plan_interrupt`, `insert_now` / `continue_current`) gets no residual: a different
    action space with its own sequence values; its traces are not states of the plan-block chain either (a
    transition's reward covers what happens between two block decisions, interrupts included).
11. **RO5's landing changes** named in the brief (a structural as-of cutoff for completion and scores, an adaptive
    return-slope integral, the coin skipping the opening boundary, FG1's follow-up gate on the two-policy mix) are not
    in this base, and the hard rules forbid merging here. RO6 reads `checks.resolve`, `checks.completion`,
    `checks.administered`, `scores.window_cost`, `scores._day_prices` and the new `scores.observed_returns` (which
    reuses `scores`' own as-of context): the landing's merge should rerun `tests/test_ro6_*.py` and, if the as-of
    cutoff changes those signatures, pass the same cutoff through `tail_data.transitions` and `scores._context`.

## Not built, and the smallest way to finish

- **n-step targets and δ_FV** (the report's FQE advice): one-step backup only. Smallest finish: a `k`-step target over
  the chain in `tail_data.transitions` and `δ_FV` from the logged design in the report.
- **Caching closed transitions**: every decision refits from all traces (parsed traces are cached per process; the
  rewards are recomputed). Linear in the log: 22.5 ms median at 94 decisions here. Smallest finish: cache each
  transition's reward by its two decision ids once its interval's checks are past their local date and no dated use is
  awaiting an import.
- **The mix's floor contrasts in `ŵ`** (choice 9).
- **A contextual `ŵ`** or a richer kernel: deliberately not built (§11; T7 first).

## A few simulated weeks (copy-shaped synthetic vault)

`tests/test_ro6_tail_data.py::test_a_few_weeks_on_a_copy_shaped_synthetic_vault` with `LEARNLOOP_RO6_DAYS=21`: RO5's
copy-shaped vault (six practised topics, four unseen items each), both policies answering (fake LLM), the default arms
(the coin 0.05 each way, one embedded check a day), one day a week without a session, answers graded by a seeded ~70%
learner. 94 traced block decisions.

| Measure | Value |
|---|---|
| Transitions | 93 of 94 decisions (1 censored `no_later_decision`; returns: 1 `no_later_session`); one generator version, features frozen at all 94 |
| The fit | n 93, 13 coefficients, noise σ² 4.81 (the checks' `c/r` terms dominate), condition 3.4e5 |
| Serving time added per decision | median 22.5 ms, max 96 ms (the residual's whole step: features, fit, contrasts, `ŵ`), n 94 |
| `ŵ`'s path (each day's last decision) | 0.0 from 10-12 to 10-25 (no window closed); 10-26 0.0 (4 contrasts), 10-27 0.100 (7: rank undefined, slope noise), 10-28 0.053 (11), 10-30 0.034 (18), 10-31 0.011 (22), 11-01 0.0025 (29); as of the end 0.0021 (36 contrasts, 2 forced; slope 0.004, sd 0.35; `P(rank > 0)` one half) |
| The residual's share of `Ṽ` per candidate | median 0, max 3.0e-4 (427 candidate values); the argmax moved 0 times |
| Partial-history cross-check | one step: −0.0025 (se 0.0044, ESS 31.8 of 36, largest weight 2.56); the fit's own projection of the step +0.0020 over 94 decisions: within the weighted interval, so no disagreement to report |

What it says: with the default coin, randomized contrasts arrive at about one forced arm a week once windows close, so
`ŵ` stays near zero and moves on noise first (10-27's 0.10 with seven contrasts), which the report shows beside its
count, slope sd and rank. As §8.7 says of `w`: a faster weight needs more randomized contrasts, not a looser estimator.

## The gate (this step)

The full suite, the whole durability lane and the whole vitest run are the landing gate's. No frontend or `src-tauri`
file changed, so no npm, vitest or cargo step applies. No schema change, so the DB reference was regenerated only for
the configuration leaves (1167 to 1170) and validated.

| Step | What ran | Result |
|---|---|---|
| Setup | `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | ok |
| Import contracts | `uv run lint-imports --no-cache` | 43 kept, 0 broken (no ignore added) |
| Version pins | the 65 test files naming mvp-0.48, the latest version, the chain's tail or RO5's opener, `-n 6` | 1169 passed, 69 failed (pins), 12 skipped, 6 xfailed; fixed in 46 files, the failed tests rerun with RO6's new files, the availability reads and the registry audit: 127 passed, 5 failed (sets ending in `LATEST_ALGORITHM_VERSION`); fixed, those rerun with `test_ro6_serving.py` and the CLI help snapshot: 94 passed, 6 skipped, 1 xfailed |
| RO regression and contract set | `test_ro1_availability`, `test_ro1_interval_factor`, `test_ro1_projection`, `test_ro1_self_report`, `test_ro4_*.py`, `test_ro5_*.py`, `test_ro0_gate`, `test_data_capture_successor`, the display-label audit (`test_router_why_copy`, `test_key_ladder_labels`, `test_measurement_state_labels`, `test_rw5c_labels`), `test_architecture` (frozen cycles, the SQL-owner rule), `test_table_roles`, `test_registry_audit`, the process-launch allowlist (`test_ai_tool_isolation`, `test_e0_isolation`, `test_codex_tool_lockdown`), `test_module_catalog_inventory`, `test_sqlite_file_copies`, `test_public_tip_guards` | 648 passed, 1 skipped |
| Targeted batch (after the commits) | 164 files: every test file added or changed since the base, every test file naming the objective chooser, the router objective, `objective-report`, `policy_for` or the mixture helpers, every `test_ro*.py`, and the contract set (`test_desktop_rpc_contract`, `test_sidecar_serializer_snapshot`, `test_sidecar_registry`, `test_mobile_allowlist`, `test_coordinated_migrations`, `test_tracked_fixture_databases`, `test_cli_help_snapshot` and the set above), `-n 6` under the shared lock | 2632 passed, 20 skipped, 3 xfailed, 1 failed: `test_ro0_rows9_13_decision_state.py::test_receipts_hold_ids_and_numbers`, a ULID that happened to contain an LO's two-letter title ("R1") at mvp-0.24, unrelated to RO6; the file rerun three times: 14 passed each |
| Durable SQLite | `--durable-sqlite` on the four `tests/test_ro6_*.py` | 34 passed |
| References | `db_generate_reference.py` / `db_validate_reference.py` (head 246, 1170 leaves: errors []), `module_generate.py` / `module_validate.py` (PASS; stamp-only churn left out), `validate_vault.py` (passed) | ok |

Every test ran inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one run at a
time. Every script outside pytest (the fingerprints, the CLI help snapshot's `--write`, lint-imports, the reference
scripts) ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

## Files RO6 added or changed tests in (for the landing gate)

`tests/test_ro6_successor.py`, `test_ro6_learned_tail.py`, `test_ro6_serving.py`, `test_ro6_tail_data.py`;
`test_ro1_availability_reads.py` (RO6's three readers named; the price's span read's reason mentions RO6's rewards);
pins moved in `test_ad23_successor.py`, `test_attempt_content_state_successor.py`, `test_batch3_landing.py`,
`test_cold_retry_reschedule.py`, `test_curriculum_c1_landing.py`, `test_curriculum_c1_plan_follows_path.py`,
`test_data_capture_successor.py`, `test_field_workbench_signals.py`, `test_followup_successor.py`,
`test_help_fold_attach_successor.py`, `test_intent_codex_rereview.py`, `test_learner_report_superseded.py`,
`test_lp_claim_fixes.py`, `test_method_explicit_upgrade.py`, `test_mvp011_upgrade.py`, `test_mvp013_upgrade.py` to
`test_mvp018_upgrade.py`, `test_mvp020_upgrade.py` to `test_mvp024_upgrade.py`, `test_plan_follows_path.py`,
`test_pr4_superseded_claims_landing.py`, `test_reader_ca2_one_ask.py`, `test_reader_followups_successor.py`,
`test_reading_step_switch.py`, `test_rebuild_equivalence_review.py`, `test_recurrence_commands.py`,
`test_regrade_contract_successor.py`, `test_required_method_grading.py`, `test_ro1_successor.py`,
`test_ro4_successor.py`, `test_ro5_successor.py`, `test_route_rules_in_grader.py`, `test_serve_eligibility_review.py`,
`test_teacher_te1_successor.py`, `test_teacher_te1b_suggestions.py`; `cli_help_snapshot.json`.

## Commits

`6efe5dc164` (parts 1 and 2: features, trajectories, the fit), `017c3ed22d` (parts 0 and 3 to 6: the successor, the
residual in serving with `ŵ`, the trace, the report, the tests), `06b924b3ca` (part 7: specs and references), and
this record.
