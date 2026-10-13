# Value-of-information successor, v2 (voi-v2)

Stage `voi-v2`, branch `serving/voi-stopping`, worktree `learnanything-voi`,
from `1b094b73` (the successor after its Codex review and re-review,
`docs/reviews/voi-stopping.md` and `voi-stopping-codex-review.md`). Two parts:

* **A.** the three findings the final Codex verify left open (F2 and F10
  reopened, F12 new), each reproduced first;
* **B.** the robust changes of the multi-family EVSI study
  (`docs/reviews/evsi-multisim.md` §6.1 on the `evsi/calibration` branch at
  `95d51782`), each behind its own switch at the study's recommendation.

*The Codex review of this stage (F10, F13, F14, F15) and its fixes are in
`docs/reviews/voi-v2-codex-review.md`; the passages below that it revised
say so.*

Owner decisions in force (2026-10-12/13): the recommended defaults recorded
in each spec are accepted (the owner may override any); frictionless defaults
(honest labels, generous defaults, live changes behind kill switches, no
shadow stage); EIG/EVSI decide probing and follow-ups with no artificial count
caps, calibrated from data. The successor keeps its placeholder label
**`mvp-0.17`** and migration numbers **187/188** (relabelled at the merge onto
main, where mvp-0.17 is the proof check); the three switches are config under
that successor. No paid call was made.

## 1. What changed

| Commit | What |
|---|---|
| `6208b504` | The branch's decisions pinned **before** any change (`tests/voi_restore_golden.json`, `tests/voi_restore_scenarios.py`) |
| `100ad407` | F2, F10, F12 |
| `17819ec0` | The study's ranks 1-3 behind `voi_stopping.robust_gate_with_value`, `lookahead_max_checks`, `robust_quantile`; registry, defaults snapshots; the plan's chip-tap re-plan also values probes against the new minutes left (F10) |
| `76de2206` | The rank 3 `rank_feasible` test pins a non-abstaining case |
| `f71ece3b` | Rank 1's counterfactual also on a committed value-continue receipt |
| `1cd941f7`, `af9b35c9` | DB and config references regenerated (759 leaves), the second time at the final code commit |
| `9864e9c1` and the next | This review (and a pointer from `voi-stopping.md`) |

| Site of change | Default | Restores the branch exactly |
|---|---|---|
| `voi_stopping.robust_gate_with_value` (rank 1) | `false` | `true` |
| `voi_stopping.lookahead_max_checks` (rank 2) | `3` (1 to 4) | `1` |
| `voi_stopping.robust_quantile` (rank 3) | `0.25` (0 < q ≤ 0.5) | `0.10` |

## 2. Part A: the final verify's findings

Each was reproduced first with a test against the unchanged code (the
failures are recorded below), then fixed. The tests live in
`tests/test_voi_v2.py`.

### F2 [High, reopened]: the predictive objective is recomputed on each posterior branch

**Reproduction** (the reviewer's): four equally likely hypotheses `(X, Y)`;
held-out targets depend only on `X`; A reveals `X` (1 minute), B reveals
`(X, Y)` (2 minutes); each alone is worth the same normalized predictive
term (1; the test uses one exact and one 80%-accurate target on `X`). At
`1b094b73` B's conditional term after A
was **0.5** (the hypothesis information `ln 2` over `ln 4`, scaled), worth 30
minutes, and the plan admitted both
(`assert 0.5 == 0.0 ± 1.0e-12`; through the plan's admission B took the
maintain lane).

**Fix.** The conditional valuation now evaluates the same objective the probe
was ranked on, on each expected posterior branch:

* `probe_episodes.EligibleInstrument.predictive_targets` keeps the held-out
  `(instrument, slot map)` targets its §7.4 predictive EIG was computed over
  (not logged);
* `voi_stopping.hypothesis_channel_body` adds the targets' label-keyed rows
  (`targets`) for a predictive-objective probe; the scheduler hands them over
  as before (`ScheduledItem.hypothesis_channel`, never persisted);
* `voi_stopping.predictive_information` is
  `instrument_predictive_information_gain` on label-keyed rows (same
  conventions: the belief over the labels the check covers, each target's
  predictive over the labels it covers);
* `HypothesisChannel` carries `targets`; with them its information on a
  branch is the predictive EIG on that branch (`at`), `scale` = reward term /
  standalone predictive EIG, so the first check still reproduces the logged
  term exactly. Receipts label it
  `expected_posterior_branches:predictive_objective`. A body without targets
  (none is written any more) keeps the old, labelled approximation.

After the fix B is worth **0** minutes given A and is not admitted; on every
eligible instrument of the real probe vault the channel's standalone value
equals the episode's own `predictive_eig` (relative 1e-9).

Tests: `test_after_a_check_reveals_x_one_revealing_x_and_y_adds_no_predictive_information`,
`test_the_greedy_admission_does_not_admit_a_check_whose_targets_are_already_known`,
`test_the_predictive_information_matches_the_probe_episodes_own_objective`.

### F10 [Medium, reopened]: admission against the minutes the plan can use

**Reproduction** (the reviewer's, through the real admission, split and
chooser): a 20-minute plan, a 15-minute requested item, overlapping project
probes A (12 minutes) and B (5). At `1b094b73` the plan planned only the
request (`assert {'pi_req'} == {'pi_b', 'pi_req'}`): A was admitted against the
whole budget, B's conditional value fell to 0, and with 5 minutes left the
chooser stopped.

**Fix** (`daily_plan/engine.py`):

* `_select_requests` (the request rule, now shared by the build and the
  pre-pass) and `_usable_probe_minutes`: on a **build** the probes are valued
  against the budget less the requested items reserved before the split
  (computed from a classification without the probes; a requested project
  probe is valued with the other probes); none when the plan's lanes exclude
  maintain;
* on a **refresh** (`advance`, `_live_context`) against the plan's minutes
  left, never `record.budget`, less requests a crash left unplaced; the probes
  the plan already holds (planned, not yet answered) are conditioned on first
  and not charged again (`greedy_information_admission(preselected=...)`,
  receipt reason `already_planned`);
* on a **chip tap** (`set_minutes`) against what the new budget leaves after
  the planned blocks.

The maintain lane's share is not used as a bound: idle lanes release their
minutes to maintain first (`redistribute`), so a probe that fits the usable
minutes can be planned; a probe that fits but is not chosen is re-valued at
the next boundary, conditioned only on what was actually planned.

*Revised by the Codex review (`voi-v2-codex-review.md`): the build selects
its requests once, requested probes and ordinary requests under one rule,
and a requested probe chosen as a request is conditioned on, not valued
(F14); a refresh values only the probes the plan can still take, never a
skipped, answered or out-of-universe one (F10).*

Tests: `test_project_probes_are_admitted_against_the_minutes_left_after_requests`
(planned = request + B; B's receipt has 5.0 minutes and `none_chosen`; A
`does_not_fit_plan_minutes`),
`test_a_refresh_admits_against_the_minutes_left_and_conditions_on_planned_probes`,
`test_a_minutes_change_values_probes_against_the_new_minutes_left` (30 − 20
planned = 10, neither the old budget nor the old minutes left),
`test_the_usable_minutes_are_what_the_requests_and_lanes_leave`.

### F12 [Medium]: legacy follow-up receipts after migration 188

**Reproduction:** a `decision_features` follow-up row carrying
`context_json.voi_stopping` (the format `6e558328` wrote) on a database at
187, then migration 188: `followup_receipts(attempt)` returned `[]`.

**Fix: a backfill in migration 188** (placeholder number, so the migration
itself is edited; data only, the schema is unchanged). Each legacy row becomes
its attempt's decision 1 in `followup_value_decisions`: id
`'legacy_decision_features:' || decision_features.id` (stable),
`source_attempt_id` = the row's `decision_id`, the learning object from the
body (else the attempt), outcome, verdict, manual override (from
`manual_trigger`), refs, need, candidate count, forecast version, algorithm
version and time from the row; the body is kept with `backfilled_from:
decision_features.context_json.voi_stopping`. mvp-0.16 follow-up rows (no
body) are not copied. The reader still reads only the table, so a legacy
decision counts once, and a later decision on the same attempt is ordinal 2.
A database that already applied the old 188 (only this branch's development
copies under `fixtures-local/`) is not backfilled; the owner's vaults have
never run 188.

Test: `test_migration_188_backfills_a_legacy_follow_up_receipt_once` (the real
incremental migrator from 187; a suppression and a manual queue backfilled;
an mvp-0.16 row ignored; a new decision is ordinal 2; three rows in all).

## 3. Part B: the multi-family study's ship list

The study modelled the successor at `086c24c0`. The fixes above change no
probe-episode valuation (F2 changes the teach-back and project-probe greedy
admission's hypothesis term, F10 the plan, F12 receipts), so its evidence
applies to this code. Every evidence cell below is quoted from
`evsi-multisim.md` §6.1.

| Rank | Change | Switch (default) | Evidence row it rests on | Code |
|---:|---|---|---|---|
| 1 | The robust completion gate does not end an episode while value decides | `robust_gate_with_value = false` | `A1` directional at 0.9/30: +0.07 to +2.00 minutes per episode when put back into the package (3/4 certified); +0.43 to +1.35 at 0.7/30 in three families, `nrm` −0.10 [−0.34, 0.14]. It never saves a measurable minute. Worst-case regret 2.79 → 1.50. Holds under the reveal stress (+1.38 [0.37, 2.37]) | `probe_episodes._evaluate_completion`, `robust_gate_applies`, `value_decides_episode`, `robust_gate_counterfactual`; `voi_stopping.with_robust_gate_counterfactual` |
| 2 | Value the best 2-3 checks jointly when no single check pays | `lookahead_max_checks = 3` | `A3` directional at 0.9/30 (−0.43 to −2.78, 3/4 certified, `nrm` included) and at 0.7/30 (−0.02 to −0.93). Where checks are weak it costs +0.19 [0.02, 0.51] (`lca`) and +0.20 [0.02, 0.47] (`cdm`) at fitted/30, within the 0.2-minute bound. Without it worst-case regret rises 1.50 → 3.24; ships under the minimax rule | `scheduling/evsi.robust_batch_evsi`, `BatchEVSI`, `joint_conditionals`; `voi_stopping.value_candidates` → `_lookahead` |
| 3 | `robust_quantile` 0.10 → 0.25 in the successor's value gate | `robust_quantile = 0.25` | `C6a` directional: at the 10th percentile the members under-predict the value checks realize in every cell with value in every family (28 of 28), and the 25th percentile is closer in 26. `C6` directional: 0.25 never costs minutes and saves 0.32 (`cdm`, lookahead) and 0.28–0.33 (`lca`, `cdm`, one-step rule) with the CI below 0. Simulated on the lookahead and one-step rules at 0.9/10, not inside the package | `voi_stopping.VoiSettings`, `value_candidates` (to `rank_feasible`, the robust EIG, the batch), `heuristic_parameters` |

Ranks 1 and 2 together are the study's `voi_p_with_fallback`: "the lowest mean
regret of the 15 arms (0.09 minutes per episode) ... and the second-smallest
worst case (1.28, against 3.86 for the successor as built and 3.60 for
today's serving)".

### Rank 1: the gate while value decides

`robust_gate_applies(vault, repository, qualifying)`: true where value does
not decide (`value_decides_episode` false: the site off, below the successor,
an observation in a calibration session), so the kill-switch path keeps
today's gate exactly; where value decides, only with the switch on. Off (the
default), an unstable value-decided episode ends on its value stop (or a
stability stop) and:

* the **value stop's receipt** (`probe_episodes.completion_detail_json`)
  carries `former_cap.robust_completion_gate` = `{name:
  probe_episodes._robust_completion_override, switch:
  voi_stopping.robust_gate_with_value, verdict, would_bind}` (the gate is
  evaluated only on a stop), folded into `former_cap.would_bind` as the
  episode maximum is, so `cap_comparison` reads `agree` when both stop;
* a **committed value-continue receipt** (the scheduler's presentation
  commit and the sidecar/TUI door) carries the same counterfactual where the
  posterior is unstable, so `cap_comparison = later` marks exactly the
  observations the gate would have prevented (once per committed
  observation). This goes one step beyond the study's wording so the live
  calibration report can score both sides of rank 1.

`episode_maximum_binds` now reads `not value_decides_episode(...)` (the same
rule, one place).

Tests: `test_the_robust_gate_does_not_end_an_episode_while_value_decides`;
`test_the_gate_still_ends_an_episode_where_value_does_not_decide_or_the_switch_is_on`
(switch on, site off, kill switch off, mvp-0.16);
`test_a_calibration_session_keeps_the_robust_gate`;
`test_a_value_stop_records_the_gates_verdict_as_a_counterfactual`;
`test_a_value_continue_past_the_gate_carries_its_verdict_on_the_committed_receipt`;
`test_in_the_real_probe_vault_the_gate_no_longer_ends_a_paying_episode` (no
monkeypatch: the pinned golden's third episode ended
`couldnt_reliably_distinguish` after two answers while value paid; at the
default it keeps asking).

### Rank 2: the lookahead

In `value_candidates`, when a decision is at stake, `rank_feasible` did not
abstain and no single candidate continues, `_lookahead` values the top `k`
of `rank_feasible`'s ranking (k = 2, then 3, up to `lookahead_max_checks`;
feasible candidates only) with `evsi.robust_batch_evsi(candidates,
loss_table, *, k, quantile)`: per credible-set member the product of the k
`P(E | H)` tables (conditionally independent given the hypothesis), its EVSI,
then the robust quantile, as `evsi_calibration/policies.py:_paying_batch`
does. The first batch whose robust value exceeds its checks' summed minutes
cost pays. Only one check continues (the site serves one observation): the
site's own choice when it is in the batch (its first candidate: on a probe
episode the eligible order, the highest predictive information rate when the
§7.4 objective is adequate, else the highest hypothesis EIG), else the batch's
top-ranked check, as `decide_package` serves. That check's value, cost and
method become the batch's (`robust_evsi_lookahead_<k>`,
`robust_evsi_batch_clears_minutes_cost`), its own single-check values kept in
`detail.single_check`; the other batch members keep theirs and are tagged
`lookahead_batch`.

Composition with F2 and the predictive path: the batch value is the exact
joint decision value of the product table, never a sum or a scaling of single
values (a check that repeats a revealing one adds nothing; tested), and on a
predictive-objective episode the choice inside the batch follows the
episode's own predictive order (tested on the real 129-member vault, both
rules). The greedy admission of teach-backs and project probes (where F2's
conditional valuation lives) has no decision at stake and never runs the
lookahead (tested).

Implementation notes, for honesty against the simulated rule:

* **Members are paired by index** over the smallest credible set, as the
  study pairs them. Each instrument's ensemble is seeded by its own decision
  context, so a pair is a product of two credible-set draws, not one shared
  channel draw.
* **Vectorized.** The joint table has |E|^k emissions; one member's EVSI is a
  matrix product with `evsi_for_conditionals`' own argmin rule (rounded to 9
  places, the loss table's tie order). On the probe vault's 129-member
  ensembles it equals `evsi_for_conditionals` on `joint_conditionals` member by
  member (|Δ| ≤ 1e-12, with P(action change) and the current action; tested).
  A `probe_episode_decision` with seven candidates took 0.50 / 0.49 / 0.59 /
  0.63 s at `lookahead_max_checks` 1 / 2 / 3 / 4 under load; the first,
  unvectorized version took 2.1 s at 3 and 31.8 s at 4.
* **Cost** is the sum of each check's `lambda_time × minutes + burden`
  (§6.1's wording); the study's code adds the burden once. Identical while
  `BURDEN_COST = 0`.
* **Reach.** *Superseded by the Codex review (F15): the lookahead acts at
  probe episodes only (`voi_stopping.LOOKAHEAD_SITES`), as the study
  simulated (its §7.1); §6.2 waits for live calibration at the follow-up
  and teach-back sites. A batch also holds one check per canonical surface
  group (F13).* As first built, `value_candidates` was shared, so the
  lookahead also acted at the follow-up site.
* **Depth** is bounded at 4 in the schema: the joint table grows as |E|^k; a
  valuation depth, not a count of observations.

The forecast body records the batch: `lookahead = {max_checks, quantile,
ranking, paid, tried: [{k, refs, evsi_point_minutes, evsi_robust_minutes,
cost_minutes}], and when paid k, batch, method, chosen_ref, chosen_rule
(site_choice_in_batch | batch_top_ranked), site_choice_ref, the batch's
point / robust / UCB EVSI, cost, member_count, current_action,
p_action_change (member 0), emission_count}`, recorded wherever the decision
already is (the offer's `voi_decisions`, the committed presentation, the
completion detail, the follow-up receipt) and also when no batch paid.

Tests: `test_robust_batch_evsi_is_the_robust_quantile_of_the_joint_evsi_per_member`,
`test_the_batch_value_equals_the_product_tables_evsi_on_the_real_credible_sets`,
`test_when_no_single_check_pays_a_paying_pair_continues_with_its_forecast`
(EVSI 0 alone, 0.33 minutes for the pair against 0.2),
`test_the_lookahead_tries_three_checks_when_two_do_not_pay` (and 2 and 1
stop), `test_the_lookahead_does_not_run_when_a_single_check_pays_or_rank_abstains`,
`test_the_batch_serves_the_sites_own_choice_when_it_is_in_the_batch`,
`test_the_lookahead_on_a_predictive_objective_episode_serves_the_incumbents_pick`,
`test_greedy_admission_never_runs_the_lookahead`.

### Rank 3: the value gate's robust quantile

`VoiSettings.robust_quantile` (from `[voi_stopping]`) is passed to
`EV.rank_feasible(..., quantile=)`, to the robust EIG
(`robust_quantile(member_eigs, q)`) and to the batch. `heuristic_parameters`
reports `{name: robust_quantile, value, provenance: evsi_multisim, source:
voi_stopping.robust_quantile, note: "docs/reviews/evsi-multisim.md §6.1
rank 3 (0.10 restores robust_composition.ROBUST_QUANTILE)"}` at the study's
value (`heuristic` otherwise), and `lookahead_max_checks` likewise where a
decision is at stake. `robust_composition.ROBUST_QUANTILE` stays 0.10 for the
mvp-0.8 paths (tested). It reaches the follow-up site's valuation too (shared
`value_candidates`).

Tests: `test_the_value_gate_reads_the_configured_robust_quantile` (EIG path:
2.75 against 0.78 minutes for a 1.5-minute check),
`test_rank_feasible_values_the_episode_at_the_configured_quantile` (EVSI
path: 0.90 against 0.48 minutes for a 0.6-minute check).

### The restore values reproduce the branch exactly

`tests/voi_restore_golden.json` was written by the branch at `1b094b73`
**before any change** (`6208b504`): 150 `value_candidates` scenarios (two-
and three-hypothesis beliefs, credible sets of nine members, minutes from
0.05 to 6, with and without routes) and the real probe vault (a Today build;
three episodes answered step by step, one with the robust gate live). Ids are
seeded so the pinned channel's ensembles are the same on every run.
`test_at_their_restore_values_the_switches_reproduce_the_branchs_decisions_exactly`
asserts equality of every decision, reason, method and value (9 decimals),
pure and integration; `test_each_switch_alone_moves_only_its_own_decisions`
shows each switch's own footprint (others at restore): the lookahead changes
1 of 150 scenarios, stop → continue, method `robust_evsi_lookahead_2`; the
quantile moves the robust values of all 150 (every scenario has a credible
set) and flips 18 stops to continues, with no lookahead method. Rank 1's
footprint is `test_in_the_real_probe_vault_the_gate_no_longer_ends_a_paying_episode`.

### No count cap reappears

`test_no_count_cap_reappears`: at the defaults one episode asks a sixth
observation while value pays (past the former maximum 4, the session cap 4
and the lookahead's depth 3), and no `[voi_stopping]` key names a cap or an
observation maximum. The existing F3 tests (`test_value_carries_one_episode_past_its_former_maximum`)
still pass.

## 4. What waits

* **Rank 4, the measured unresolved cost.** Part C
  (`scheduling/unresolved_cost.py`) is on main (`3192d0c9`), not on this
  branch's base: wired at the merge onto main
  (`VoiContext.loss_table` passes `unresolved_minutes` when
  `evsi.measured_loss_enabled`), which stays **off** by default.
* **Rank 5 and §6.3: no change.** The flip-abstention fallback at 60 minutes
  per nat, the serving rule, the stability stops, the lifted episode maximum,
  `PERTURBATION_DELTA` 0.15, the pseudo count 8, `BURDEN_COST` 0,
  `INSTRUMENT_PERTURBATION_CONCENTRATION`, `ROBUST_DRAW_COUNT`,
  `DEFAULT_INTERVENTION_MINUTES`.
* **§6.2 waits for live `voi_forecasts` data:** a site-scoped nat scale where
  nothing is at stake; the gate on the kill-switch path; the lookahead's depth
  beyond 3 and its value at the follow-up and teach-back sites; the card
  vocabulary's rows. Every new decision above records its forecast in the
  branch's existing receipts (`voi_stop_forecast_v1` bodies with the new
  `lookahead` and `former_cap.robust_completion_gate` keys), which main's
  `voi_forecasts` can absorb at the merge.

## 5. Config, defaults, references

* `config/schema.py` `VoiStoppingConfig`: `robust_gate_with_value: bool =
  False`, `lookahead_max_checks: int = 3` (1 to 4), `robust_quantile: float =
  0.25` (0 < q ≤ 0.5); modelled defaults, left out of the decision-only
  template. Act only where value decides (mvp-0.17 with the sites on).
* Parameter registry: `voi_stopping.robust_quantile` and
  `voi_stopping.lookahead_max_checks` classified (decision, threshold,
  heuristic until live data). No new numeric module constant.
* Every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry recomputed (the effective
  config gains three keys; serving below mvp-0.17 unchanged): mvp-0.9
  `5101af00`, 0.10 `6137d272`, 0.11 `b19756b1`, 0.12 `113fa568`, 0.13
  `1ca0e458`, 0.14 `83a44395`, 0.15 `14f5f59f`, 0.16 `08c1f094`, 0.17
  `c19dcada`; the template's `__pycache__` bytecode deleted.
* DB and config references regenerated (759 effective leaves, 308 table notes,
  schema head 188; the prose counts in `Configuration.md` and `Database.md`
  updated); `db_validate_reference.py`: `errors: []`. CLI help unchanged (the
  snapshot test passes). Nothing under `apps/` changed.

## 6. Paid calls

None. Every test uses fakes or local arithmetic; no model route, no network,
$0.00. No manual run was needed: the backup copies under
`fixtures-local/voi-copies/` have no probe episode in progress (the earlier
report), so the switches do not change their Today builds.

## 7. Gate

Run at `af9b35c9` (the code is that of `f71ece3b`; the later commits are
documentation only), `TMPDIR` = the worktree's `fixtures-local/tmp`, the two
suites under `flock /tmp/learnloop-fullsuite.lock` (the lock was held by
another stage first; both waited for it).

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 15 kept, 0 broken |
| `flock … uv run pytest -n auto` | **9,059 passed, 1 failed** of 9,060 (343 s). The failure, `test_sidecar_reader_p3_slice2.py::test_invoke_preset_commit_enqueues_synthesis_and_proposes` (`drain["completed"]` empty), is a background-drain test in code this stage does not touch; it passes alone 3 of 3 and its file passes whole (5 of 5) |
| `flock … uv run pytest -m durability` | **95 passed**, 8,965 deselected (101 s) |
| DB and config references (`db_generate_reference.py`, `db_validate_reference.py`) | regenerated at schema head 188 (759 effective leaves, 308 table notes); validator `errors: []` |
| Frontend (`apps/learnloop-tauri`), `cargo check` | not run: nothing under `apps/` changed |

Stage tests: `tests/test_voi_v2.py` **32 cases** (28 functions): 8 for the
three fixes (F2 3, F10 4 with the chip-tap case, F12 1), 24 for the switches,
the restore golden, the lookahead, the gate and the no-count-cap check; all
pass.
`tests/test_voi_stopping.py` 70 cases (one receipt assertion updated: the
quantile's and the lookahead's provenance is `evsi_multisim`),
`tests/test_mvp017_upgrade.py` 12. Fail-first: the 7 fix tests failed at
`1b094b73` for the reviewer's reasons (0.5 instead of 0; `{'pi_req'}` planned;
no receipt after 188), and 15 of the rank tests failed before the switches
existed (the others pin behaviour that must not move: the gate where value
does not decide, no lookahead where a single check pays or nothing is at
stake, none in the greedy admission). The chip-tap and the committed-receipt
tests were added with their fixes.

## 8. Open questions for the owner

1. **Batch choice among ties.** When every single check's robust EVSI is 0
   (the lookahead's typical case), `rank_feasible` orders them by ref, so the
   batch is the top-k by ref among equals, as in the study. Order ties by the
   site's own information order instead (more informative batches, and the
   site's pick more often inside them), or keep the simulated rule until live
   data?
2. **The lookahead at the follow-up site.** *Answered by the Codex review
   (F15): scoped to probe episodes until per-site calibration; a later
   follow-up rollout gets its own site control.*
3. **Rank 1's continue-side counterfactual** costs one robust-selection
   evaluation per committed observation in a value-decided unstable episode.
   Keep, or record only the stop side as §6.1 words it?
4. **Developer copies with the old 188.** Only copies under `fixtures-local/`
   applied 188 before the backfill; re-copy them from the owner's vaults at
   the merge rather than repair them?
5. The study's own §12 questions stand (shipping rule, the gate, the flip
   abstention, the nat scale, rank 3, Part C, the single-family bound); this
   stage built its recommended answers.

## Landing onto main

Landed as mvp-0.21 (migrations 200/201), with the study's rank 4 wired behind
`evsi.measured_loss_enabled` and every value decision logged to
`voi_forecasts`: see `voi-stopping.md`, "Landing onto main".
