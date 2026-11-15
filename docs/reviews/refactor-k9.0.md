# K9.0: the planted-type simulation on the robust probe path (D-39)

Step K9.0 of the K9 diagnosis strategy (`docs/reviews/k9-diagnosis-strategy-2026-11-14.md`, "Added at landing"), ledger D-39 with D-32 beside it. Investigation first. Base `main` 3405215424, branch `refactor/k9.0-planted-sim`.

**Verdict: (a), a real fault in what vaults compute; in the sim's configuration it explains all of the failure the gate measures, and on the default path, where value of information decides instead, what remains is (c) plus a design question.** The robust completion gate ends an unstable probe episode as `couldnt_reliably_distinguish` whenever the robust selector calls its *pick* fragile, even when its own stop rule says the next observation is worth 9 to 25 times its minutes. In the planted runs the pick is fragile above all because the runner-up is a second item of the same card: two items with identical ensembles, so the winner's advantage is exactly zero and can never be positive. Every episode of four of the five planted types ends at the first check, after two answers; `schema_without_transfer` is named 0 times in 40 and `surface_only` 24 in 40. With the gate corrected in a scratch counterfactual, nothing abstains and every type is named at least 30 times in 40. The planted learner is not at fault (b explains nothing measurable). Five trials are too few to tell a rate (c), but that is not why the gate fails in the sim's configuration. As a vault serves by default (value of information on), the gate decides no episode; the value stop ends most episodes at the same point by its own rule, and the rates are surface_only 24/40 and schema_without_transfer 27/40: there the five-seed failure (surface_only 2/5) is sampling noise around a rate equal to the threshold, and whether label accuracy is the right test of a value-stopped episode is for the owner (§5, Q-b). The step stopped before any change to `src/learnloop/diagnosis/`, as the brief says: this record hands back the design. D-32 (step 4) and the sibling fixes (step 5) were not started.

The ledger said "surface_only 2 in 5; the others pass". That was wrong: in the same five seeds `schema_without_transfer` is diagnosed 0 times in 5 (and 0 in 40), and the test's failure message showed it. Both are the same fault.

## 1. Measurements

Harness: `run_probe_validation` per (type, seed), driven from a scratch script through the env -i wrapper (`measure_k90.py`, outside the checkout, not committed), on a vault built as `tests/sim_probe_validation_helpers._vault_with_confusable` builds it. Seeds 11-50 for every type (40 each; 11-15 are the test's own). The script reproduces the test exactly: its first five seeds give the test's numbers, run for run (checked against the pytest run with `--runxfail`). Each run about 5-7 s. "Probes" are qualifying observations; "ended" is the episode's `completion_reason`.

### 1.1 The sim's own configuration (placement, FG1 and value of information off; the test's vault; seeds 11-50)

| Planted | Named correctly (label = action) | 95% interval | Named instead | Probes | Ended |
|---|---|---|---|---|---|
| robust_initial_grasp | 37/40 (0.93) | 0.80-0.97 | surface_only 2, recall_without_mechanism 1 | 2 (all 40) | couldnt_reliably_distinguish 40 |
| unfamiliar | 38/40 (0.95) | 0.83-0.99 | surface_only 2 | 4 (36), 2 (4) | observation_budget_exhausted 36, couldnt_reliably_distinguish 4 |
| surface_only | 24/40 (0.60) | 0.45-0.74 | robust_initial_grasp 12, recall_without_mechanism 3, other_or_unknown 1 | 2 (all 40) | couldnt_reliably_distinguish 40 |
| schema_without_transfer | 0/40 (0.00) | 0.00-0.09 | recall_without_mechanism 27, surface_only 7, other_or_unknown 3, robust_initial_grasp 3 | 2 (all 40) | couldnt_reliably_distinguish 40 |
| confuses_with | 34/40 (0.85) | 0.71-0.93 | surface_only 3, robust_initial_grasp 3 | 2 (all 40) | couldnt_reliably_distinguish 40 |

164 of 200 episodes (82%) end on the abstention; U-021's budget (`robust_composition.ABSTENTION_BUDGET_FRACTION`) is 15%. The test's five seeds: 20 of 25.

Running the same vault at the head's tag instead of the old pin (`mvp-0.6`) gives the same runs on the five seeds checked: the tag no longer matters on this path.

### 1.2 As a vault serves by default

**The sim cannot run with every default on, and was not forced.** With placement on (`placement.enabled`, the default), state sync opens no episode for a new learning object, so `run_probe_validation` finds no open episode and returns an empty report (checked: every run empty). With FG1 on (`followup.generate_and_serve`) the episode opens but `generate_instances_for_episode` mints no parametric instances, so it has nothing to serve: 0 observations, never completes. Both are what the sim needs to exist, not what decides the diagnosis. Value of information is the one default that changes how an episode ends, and the sim runs with it on (placement and FG1 off):

| Planted | Named correctly | 95% interval | Named instead | Probes | Ended |
|---|---|---|---|---|---|
| robust_initial_grasp | 37/40 (0.93) | 0.80-0.97 | surface_only 2, schema_without_transfer 1 | 2 (39), 4 (1) | value_of_information_stop 40 |
| unfamiliar | 37/40 (0.93) | 0.80-0.97 | other_or_unknown 2, surface_only 1 | 1 (34), 2 (3), 3 (3) | value_of_information_stop 40 |
| surface_only | 24/40 (0.60) | 0.45-0.74 | robust_initial_grasp 12, recall_without_mechanism 3, schema_without_transfer 1 | 2 (36), 3-5 (4) | value_of_information_stop 36, action_equivalent 3, decision_stable 1 |
| schema_without_transfer | 27/40 (0.68) | 0.52-0.80 | surface_only 7, robust_initial_grasp 6 | 2 (10), 3-6 (30) | decision_stable 20, value_of_information_stop 20 |
| confuses_with | 34/40 (0.85) | 0.71-0.93 | surface_only 3, robust_initial_grasp 3 | 2 (all 40) | value_of_information_stop 40 |

No episode abstains here: the gate does not decide while value does. On the test's five seeds this path gives surface_only 2/5 and schema_without_transfer 3/5 (the others 5/5), so the five-seed gate would still fail on surface_only, whose 40-seed rate is exactly the threshold.

### 1.3 Counterfactual gates (scratch only, patched in the measuring process; production unchanged)

Two candidate fixes, applied by wrapping `probe_robust.robust_selection` in the measuring process only:

- **stop-only**: a fragile pick no longer ends the episode; only a fragile *stop* (the stop rule fires and the winner is not robust) does. This is the library's own comment for the branch ("Do not stop; park for a better instrument").
- **distinct**: candidates with identical ensembles (same family, card and coarse rows) are collapsed before ranking, so a second item of the same card is never the runner-up.

Named correctly, out of 40 (seeds 11-50), in the sim's configuration:

| Planted | As is | stop-only | distinct |
|---|---|---|---|
| robust_initial_grasp | 37 | 39 | 37 |
| unfamiliar | 38 | 37 | 39 |
| surface_only | 24 | 32 | 24 |
| schema_without_transfer | 0 | 30 | 25 |
| confuses_with | 34 | 33 | 34 |
| abstained (of 200) | 164 | 0 | 133 |
| probes per episode | 2 (4 for unfamiliar) | 4 (every episode, budget) | 2 in 133, 4 in 67 |

stop-only on the test's five seeds: surface_only 3/5, schema_without_transfer 4/5, confuses_with 4/5, the others 5/5: the five-seed gate would pass, by a margin of one run on three types.

## 2. Reading the failing runs

Traces: `trace_k90.py` (scratch) wraps `eligible_instruments`, `planted_response`, `robust_selection` and the value decision in the measuring process and reads the stored observation rows. Seeds 11, 12, 13, 15 of `surface_only` and 11, 12, 13 of `schema_without_transfer`, the sim's configuration.

Every run serves the same two probes first; only the planted learner's draws differ.

| Probe | Chosen because | surface_only learner | schema_without_transfer learner |
|---|---|---|---|
| 1. `minimal_recall` | highest predictive information rate (0.01025 nats/s against perturbation 0.00980, contrast 0.00925; `eligible_instruments`, `diagnosis/probe_episodes.py:1019-1029`) | card alias surface_only -> robust_initial_grasp: modal `correct_recall`, answers 4 | alias -> robust_initial_grasp: same |
| 2. `contrast_confusable` | rate 0.00627 against perturbation 0.00527; recall now carries the redundancy penalty 0.6 | own slot `surface_only`: modal `correct_weak_reason` (0.577), the responder answers weak 65%, correct 20%, low 15% | no slot of its own; the episode's slot map and `_effective_slot` both use `other_or_unknown` (modal `other_systematic_error`) |

Probe 1 moves nothing between surface_only and robust_initial_grasp (the card says it cannot separate them; the ratio 0.2603/0.1934 stays 0.3229/0.2399). Probe 2 decides: a weak answer puts surface_only at 0.61 (seed 11) or 0.57 (seed 15); a full answer puts robust_initial_grasp at 0.838 (seeds 12, 13). For schema_without_transfer the low answer leaves recall_without_mechanism 0.371 against schema_without_transfer 0.310: the two are still tied, and only `perturbation` (which aliases recall_without_mechanism to surface_only and schema_without_transfer to robust_initial_grasp) separates them.

Completion is evaluated when a block closes (`diagnosis/probe_blocks.py:441-447`); the default block is two observations (`probe.block.default_block_observations`), so the first check comes after the second answer. The posterior is unstable (top below 0.85), so `_evaluate_completion` asks the robust gate (`diagnosis/probe_episodes.py:2959-2963`), and the gate abstains:

| Run | Posterior top | Gate's pick | lcb advantage | agreement | should_stop | gate's robust EVSI of the pick (min; 60 min per nat of q10 EIG) | cost (min) | Verdict |
|---|---|---|---|---|---|---|---|---|
| surface_only 11 | surface_only 0.61 | perturbation | **0.0** | 0.75 | False | 15.0 | 0.83 | couldnt_reliably_distinguish |
| surface_only 12 | robust 0.84 | contrast | -0.00055 | 0.81 | False | 9.6 (contrast) / 8.3 (perturbation) | 0.75 | couldnt_reliably_distinguish |
| surface_only 13 | robust 0.84 | contrast | -0.00058 | 0.85 | False | 8.9 / 7.2 | 0.75 | couldnt_reliably_distinguish |
| surface_only 15 | surface_only 0.57 | perturbation | **0.0** | 0.80 | False | 16.8 | 0.83 | couldnt_reliably_distinguish |
| schema 11, 12, 13 | recall_without_mechanism 0.37 | perturbation | **0.0** | 0.95-0.96 | False | 18.3-19.2 | 0.83 | couldnt_reliably_distinguish |

The two remaining items of each family come from one card, so their ensembles are identical (same q10 to five digits): `decision_context_hash` names the card and version, not the item (`diagnosis/probe_robust.py:190-198`). The winner's per-draw advantage over its twin is exactly zero, so `robust_winner = lcb_advantage > 0.0` is false (`diagnosis/robust_composition.py:394-400`, `:428`). In the schema runs the agreement gate passes (0.95 >= 0.90) and the twin alone causes the abstention. `evaluate_selection` returns `abstained=True, should_stop=False, verdict='couldnt_reliably_distinguish'` for that branch (`:446-451`, whose comment says "Do not stop; park for a better instrument"), and `_robust_gate_verdict` completes the episode on any `abstained`, without reading `should_stop` (`diagnosis/probe_episodes.py:3275-3276`). (The gate's value is the information proxy, `VALUE_PER_NAT_MINUTES` times the 10th-percentile EIG, `robust_composition.py:407-412`; the value stop of §2.1 prices the same probe by what it would change in the first action, and finds less. "Pays" in this record means by the gate's own rule.)

With the gate corrected (stop-only), the same seeds run to the budget of four: probe 3 is `perturbation`, which a surface_only learner answers with `surface_bound_error` (65% modal, fired as a signature) and a schema_without_transfer learner answers correctly; schema 11-13 end at schema_without_transfer 0.66, 0.87, 0.55. Seeds 11 and 13 of surface_only still end on robust_initial_grasp because the responder answered perturbation correctly (8%) or contrast fully (20%): the learner's noise, at the budget.

### 2.1 On the default path the value stop decides, and it stops at the same place

With value of information on, the gate no longer decides (`robust_gate_applies`, `diagnosis/probe_episodes.py:3077-3093`); the value stop does. After probe 1 it continues (EIG proxy 21.7 minutes, `value_uncertain` because `rank_feasible` abstains on a downstream action flip). After probe 2 it stops on `lcb_evsi_below_minutes_cost`: the decision-value EVSI of perturbation is 0.61 minutes (seed 11) and 0.18 (seed 12) against its 0.83-minute cost (`diagnosis/voi_stopping.py:1078-1086`). That EVSI is the minutes a better first action would save, priced by `action_loss.build_loss_table` from action durations (`voi_stopping.py:550-590`); the actions of surface_only (`varied_surface_practice`) and robust_initial_grasp (`shifted_surface_practice`) are priced as cheap to confuse. Where the confusion is dear the value rule keeps asking: schema_without_transfer against recall_without_mechanism (transfer practice against mechanism instruction) runs 3-6 probes in 30 of 40 episodes and half end `decision_stable` (§1.2). This is the value rule working as designed, not the fault above; but it means the checkpoint gate (per-type label accuracy, regardless of what a mistake costs) is not the right question for an episode that value decides. That is a design question for the owner (§5), not something this step settles. Every value stop's receipt also records what the gate would have said (`former_cap.robust_completion_gate`, `voi_stopping.with_robust_gate_counterfactual`), and that counterfactual carries the same fault.

## 3. Verdict, with how much each explains

- **(a) The robust completion gate: all of the gate failure in the sim's configuration.** 82% of planted episodes abstain at the first check while the next observation pays 9-25 times its cost. Corrected (stop-only), the abstention rate falls to 0 of 200 and the per-type rates become 0.98, 0.93, 0.80, 0.75 and 0.83 (robust_initial_grasp, unfamiliar, surface_only, schema_without_transfer, confuses_with), every episode at the budget of four. Two parts:
  - (a1) the twin tie: `evaluate_selection` compares the winner with a second item of the same card (and `evaluate_series_selection`, the credible-set sibling, compares every pair of members, so identical series also give a non-positive lower quantile). Alone (distinct) it lifts schema_without_transfer from 0 to 25 of 40 and abstentions fall from 164 to 133; surface_only stays at 24, because its fragile picks are mostly real near-ties between two different paying instruments (contrast against perturbation, seeds 12 and 13), which (a2) is about.
  - (a2) the adapter: `_robust_gate_verdict` ends the episode on a fragile pick, not only on a fragile stop. The value path already treats a fragile ranking as "value uncertain, keep measuring" (`voi_stopping.py:1093-1097`, `scheduling/evsi.py:433-457`: `rank_feasible` abstains only when it would not stop, and the episode then keeps asking on the EIG proxy), so the two stop rules disagree on what a fragile ranking means.
- **(b) The planted learner: nothing measurable.** The robust path serves the same instruments, the same card rows and the same fine-outcome posterior as the point path did (`episode_posterior` replays `instrument_observation_likelihoods`, `diagnosis/probe_episodes.py:1924`, `:2022`; the coarse robust posterior is only a snapshot, `:2688-2702`). `_effective_slot` lands where the episode's frozen slot map lands in every traced probe (surface_only on recall -> robust_initial_grasp by the card's alias; schema_without_transfer on contrast -> other_or_unknown, as the slot map says). One divergence, the same on both paths: the responder is noisier than the card's rows (20% full answers where the contrast card's surface_only row says 9.6%; 8% correct where perturbation's says 4.3%). It lowers every rate a little; it does not make the robust path stop.
- **(c) Five trials: true, and secondary.** Passing 3 of 5 happens with probability 0.68 at a true rate of 0.6, 0.50 at 0.5 and 0.32 at 0.4, so the five-seed gate cannot tell surface_only's 0.60 from a pass. It is not why the test fails: schema_without_transfer is 0 in 40. After a fix the gate needs a larger sample: 40 runs per type with a threshold of 30 (0.75) fails a type whose rate is 0.6 with probability 0.965 and passes one at 0.85 with probability 0.97 (false pass 3.5%, false fail 3.0% per type). But the corrected rates (stop-only) put schema_without_transfer at 30/40 and surface_only at 32/40, so that bar would fail a correct path about half the time; the bar has to come from what the owner wants to tell apart. If it is "at most a coin flip" (0.5) against "about what the corrected path does" (0.75): 40 runs, threshold 26 (0.65): false pass 4.0% at 0.5, false fail 5.4% at 0.75 per type. At about 5 s a run, that is about 17 minutes for five types: an `arc_close` simulation whose size is the point, not a landing-gate test.

## 4. What changed

- `267fcda6ab` (tests only): `tests/test_robust_selection_twin_candidates.py` (new): the separating card alone acts (passes); with its second item beside it the selector abstains (strict xfail, D-39), with plain values (`rc.build_ensemble`, `rc.evaluate_selection`). `tests/test_sim_probe_validation.py`: `test_planted_episodes_abstain_within_the_abstention_budget` (new, strict xfail, D-39) asserts U-021's budget on the existing module fixture (20/25 abstain now; no extra runtime); the checkpoint gate's xfail reason names the mechanism. No assertion changed; no source changed.
- This record, the ledger (D-39 to owner with the design, D-32's status, new row D-40), the K9 strategy's K9.0 line.

Fail-first evidence: both new xfails fail with `--runxfail` at the base (`RobustDecision(lcb_advantage_over_runner_up=0.0, action_agreement_fraction=1.0, should_stop=False, abstained=True, verdict='couldnt_reliably_distinguish')`; `assert (20 / 25) <= 0.15`).

## 5. The design handed back

**What is wrong.** (a1) A tie with an identical instrument is read as a fragile winner. (a2) A fragile pick ends the episode as "couldn't reliably distinguish" although the stop rule says the next observation pays; the library's comment for that branch says the opposite, and the value path treats the same situation as "keep measuring".

**The smallest fix.**
1. (a2) `_robust_gate_verdict` (`diagnosis/probe_episodes.py:3275`): return `couldnt_reliably_distinguish` only when `decision.abstained and decision.should_stop`. A fragile pick returns None, and the episode continues to its other rules (decision stable, the budget, the park when nothing is left). One condition. This alone is the stop-only counterfactual.
2. (a1) `evaluate_selection` (`diagnosis/robust_composition.py:387-426`): rank distinct instruments. Collapse candidates whose ensembles are identical (in this code: same `decision_context_hash`, which already names card, version, slot map and posterior) before taking the runner-up and counting agreement, so a card's second item is never its own rival. The same in `evaluate_series_selection` (`:454-521`) for identical series. With (1) in place this changes no episode end in these runs (none reached a fragile stop); it makes the gate's `stop` vs `couldnt_reliably_distinguish` and the logged robust forecasts honest, and it is what `tests/test_robust_selection_twin_candidates.py` asks for.

**What it moves for a vault.**
- Where the gate decides: an episode in a calibration session (value does not decide there, `value_decides_episode`), a vault with `voi_stopping.robust_gate_with_value = true`, and the value-of-information kill-switch path (which D7 may remove). There, unstable episodes keep asking instead of abstaining after two answers: more `probe_presentations`, `probe_observations` and attempts per episode, a different `probe_episodes.completion_reason` / `completion_detail_json` (budget, decision_stable or a park in place of `couldnt_reliably_distinguish`), different persisted episode beliefs (`persist_episode_beliefs`) and the routing that reads them (`probe_blocks` route, the diagnosed gap and first action).
- On the default path (value decides): no episode ends differently. What moves is the receipt: `former_cap.robust_completion_gate.verdict` on value decisions (`probe_episodes.py:1614-1616`, `:2987-2995`) stops saying `couldnt_reliably_distinguish` where the pick was merely fragile; and with (2), the `voi_forecasts` rows the gate logs at `probe_robust_selection` (`_record_robust_selection_forecast`) and the robust `evaluate_selection` callers in `instructional/valuation.py:973` and `evsi_calibration/policies.py:274`, `:326` see different advantages, agreement and verdicts when candidates repeat a card.
- History: nothing replays differently; recorded completions and receipts keep their meaning.

**Persisted meaning?** Under the playbook's 2026-10-17 rule (a change to which items are served as measurements is a successor with a kill switch even when replay is unchanged), (1) is a behaviour change of the episode's stop: a successor tag and kill switch, unless the owner rules that the D6/D7 direction (fewer tags) covers it. The shadow comparison needs no rerun for the receipt half: on copies of the owner's vaults, count value-stop receipts whose recorded gate counterfactual is `couldnt_reliably_distinguish` and recompute it with (1) and (2); for the calibration-session half, list the owner's episodes that completed `couldnt_reliably_distinguish` with `should_stop` false in their logged robust forecast. (2) alone changes logged forecasts and the valuation's robust verdicts: serving only where value decides, persisted meaning where the gate decides.

**Open owner questions.** Q-a: take (1), (2) or both, and under a successor or as a fix of the current tag. Q-b: what should the planted-learner suite assert for an episode that value decides: per-type label accuracy (which the value stop does not try to maximise: §1.2), or regret in minutes against the planted type's own action, or label accuracy under the count-capped path only. Q-c (from (b)): should the planted responder answer from the card's own rows (exactly what the instruments model) or stay "behavioural" and noisier, as now; either way, say which in the module docstring.

## 6. D-32 and the siblings (steps 4 and 5)

Not started: the brief stops the step on (a). Sibling list (step 5), for the step that resumes:

| Where | What it turns off | Would it pass with the default? |
|---|---|---|
| `tests/sim_probe_validation_helpers._vault_with_confusable` (used by `test_sim_probe_validation.py` and `test_ux_phase4_feedback.py::test_f1l_the_sim_skips_a_covered_instrument_instead_of_aborting_the_run`) | `placement.enabled`, `followup.generate_and_serve`, `voi_stopping.enabled` (and pins `mvp-0.6`) | No: with placement or FG1 on the sim has no episode or no instruments (§1.2). Value of information on: runs, ends on the value stop (§1.2 table) |
| `tests/test_sim_teach_back.py:86` | `diagnosis.split_enabled = false` | No: D-32 |
| `learnloop sim probe-validation` / `probe-pilot` (`cli/sim.py:42-70`, `:102-112`) | nothing; runs the vault as it is | It prints PASS: on a default vault the report is empty and `ValidationReport.passes` is `all()` over nothing. New ledger row D-40 |

No other `tests/test_sim_*.py` or `src/learnloop/sim/` module sets placement, FG1, value of information or the split off.

## 7. What I did not verify

- Not run on real histories: the owner's vaults were not opened (the brief's synthetic scope); whether real episodes abstain this way is unknown, though the receipts' recorded gate counterfactual would show it.
- The counterfactuals patch `probe_robust.robust_selection` in the measuring process; they are not the fix and were not run through the episode adapter change itself, the landing gate or any other test.
- Calibration-session episodes (where the gate decides by default) were not simulated.
- Only one vault shape (the basic vault's one learning object with one confusable, three generated families). The `minimal_counterexample` family, which targets schema_without_transfer, generates no instance in this vault; a vault where it does would separate schema_without_transfer earlier.
- The scratch scripts (`measure_k90.py`, `trace_k90.py`, `summary_k90.py`) and their outputs are in the session scratch directory, not in the repository.
