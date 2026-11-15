# K9.0b: the robust completion gate fixes (D-39)

Step K9.0b of the K9 diagnosis strategy, ledger D-39's fix, on branch `fix/k9.0b-robust-gate`, based on main `ed96d1b9d0`. Behaviour track under `docs/algorithm-change-playbook.md`. The investigation, the measurements and the design are K9.0's (`docs/reviews/refactor-k9.0.md`); the orchestrator decided both fixes, no new tag, an own kill switch, and the planted suite's shape. D-32 and D-41 are not started (a later step).

**Result.** Both fixes are in `mvp-0.59` behind `probe.episode.robust_gate_fixes` (default true), read through one predicate over one tag set. In the configuration where the gate decides, the planted types are named 39, 37, 32, 30 and 33 times in 40 (robust_initial_grasp, unfamiliar, surface_only, schema_without_transfer, confuses_with) and no episode abstains (K9.0: 37, 38, 24, 0, 34 and 164 of 200). At `mvp-0.58` and with the switch off the runs are K9.0's table exactly, seed for seed. Where value of information decides (a vault's default) no episode ends differently. A rebuild and the upgrade do not re-decide a recorded episode. On copies of the owner's three vaults nothing moves: no recorded history there is one the fixes act on.

## 0. Step 0: callers, where the gate decides, what moves

### 0.1 Every caller

Line numbers at the tip.

| Function | Caller | What it does with the result | Takes the fix? |
|---|---|---|---|
| `robust_composition.evaluate_selection` (`:378`) | `probe_robust.robust_selection` (`:305`), from `probe_episodes._robust_gate_verdict` (`:3272`) | the gate's decision; logged by `_record_robust_selection_forecast` (`:3276`) where the gate decides | yes, `distinct_instruments=robust_gate_fixes_on(config)` |
| | `instructional/valuation.value_problem` (`:979`) | first pick of a same-shape valuation; its verdict and checks go on the valuation receipt | yes, threaded from `discriminating.value_request` (`:155`) |
| | `evsi_calibration/policies.decide_eig` (`:274`), `_robust_gate_abstains` (`:326`) | the EVSI calibration simulation's `eig` and `incumbent` policies | no: no vault or tag there, and inert (each question's ensemble seeds on its own question id, `simulate.py:210`, `multisim.py:228`, so no two are identical). D-44 for the incumbent's gate |
| `evaluate_series_selection` (`:478`) | `valuation.value_problem` (`:989`), later picks conditioned on earlier ones | the same receipt | yes |
| | `evaluate_selection_credible_sets` (`:572`) | | yes, passes its flag through |
| `evaluate_selection_credible_sets` (`:555`) | `valuation.value_problem` (`:983`), mixed credible sets | the same receipt | yes |
| `probe_episodes._robust_gate_verdict` (`:3227`) | `_robust_completion_override` (`:3222`), called where the gate decides (`_evaluate_completion`, `:2963`) and as the value stop's counterfactual (`:2993`, `record_forecast=False`) | ends the episode / the counterfactual verdict | yes: `robust_gate_completion(decision, stop_only=...)` (`:3282`) |
| | `robust_gate_counterfactual` (`:3197`), from `probe_episodes.py:1615` (the learner-opened item's value receipt) and `scheduling/scheduler.py:1128` (the committed presentation's value receipt) | the counterfactual on value CONTINUE receipts | yes (same function) |

No caller's output reaches a compared identity: `tests/test_identity_pins.py` passes unchanged, the `voi_forecasts` receipt key (`probe_robust_selection:{episode}:{observations}:{chosen}`) keeps its chosen slot (the collapse keeps the best-ranked copy, so the winner never changes), and the valuation receipts and value receipts are stored JSON that no hash covers.

### 0.2 Where the gate decides and where it is only recorded

`robust_gate_applies` (`probe_episodes.py:3079`): the gate decides where value of information does not (`value_decides_episode`, `:3059`): the probe-episode site off (`voi_stopping.enabled` or `voi_stopping.probe_episodes` false, the kill-switch path D7 may remove), or the latest observation in a calibration session (`calibration_cap_lifted`); and where value decides only with `voi_stopping.robust_gate_with_value = true` (default false). Elsewhere (a vault's default) the gate's verdict is recorded only: on the value stop's `completion_detail_json` and on the committed presentation's or learner-opened item's value receipt, as `former_cap.robust_completion_gate` (`voi_stopping.with_robust_gate_counterfactual`, `:1333`), which also sets `former_cap.would_bind` and so the receipt's `cap_comparison`. Nothing reads those three fields to decide (they are logged by `voi_forecasting.py:551` and `chain_records.py:190`).

### 0.3 What each fix moves in stored rows

- **Where the gate decides.** Fix 1: an unstable episode whose gate decision is a fragile pick no longer completes `couldnt_reliably_distinguish`; it goes on to the budget, `decision_stable`, `action_equivalent` or a park. So `probe_episodes.completion_reason` and `completion_posterior_json` move, more `probe_presentations`, `probe_observations` and attempts are written per episode, the episode beliefs `persist_episode_beliefs` writes at each block end move (`learner_state_beliefs`), and so does the routing that reads them (the block's route, the diagnosed gap, the first action). `voi_forecasts` rows at `probe_robust_selection` gain one per further block check. Fix 2: the same rows' `verdict`, `abstained`, `lcb_advantage_over_runner_up` and `action_agreement_fraction` change wherever a card's second item was a candidate, and a fragile pick caused by the twin alone becomes `act`.
- **Where value decides.** No episode end moves. The receipts' counterfactual verdict becomes None where the gate's pick was merely fragile (fix 1) or fragile only because of a twin (fix 2), with `would_bind` and `cap_comparison` following.
- **The source valuation.** A receipt whose candidates include identical members (two items of one card) no longer abstains on the twin: `practice_index_proposals.valuation_json`, `reader_session_digests.valuation_json`/`revaluation_json`, `retrieval_interventions.valuation_json`.
- **Replay.** None of it is replayed: `probe_episodes` is a workflow table, `probe_observations` and `probe_presentations` raw ledgers, `voi_forecasts` a receipt (`db/table_roles.py`), and no replayer runs the completion policy (`substrate/rebuild_orchestrator.py` has none). `test_robust_completion_gate.py::test_the_upgrade_to_the_fix_does_not_re_decide_a_recorded_episode`: a planted episode that abstained on a fragile pick at `mvp-0.58`, upgraded to `mvp-0.59` (a whole-vault rebuild with the fixes on) and rebuilt again, keeps every row of those four tables byte for byte.

## 1. The predicate and the switch (`e6570da9c6`)

- `probe.episode.robust_gate_fixes: bool = True`, with a why-comment, in `ProbeEpisodeConfig`. The name follows the sibling in the same tag, `facet_diagnostic.canonical_belief_fixes` (a successor's group of ledger fixes, named for what it fixes), and the place follows the code: the gate is the probe episode's completion policy, whose settings are `probe.episode.*`. `voi_stopping.*` was the other candidate (it holds `robust_gate_with_value`), but that section is the value rule's, and the selector fix reaches the source valuation too.
- `algorithm_versions.ROBUST_GATE_FIX_VERSIONS = FACET_BELIEF_FIX_VERSIONS` (the one tag line) and `diagnosis.probe_robust.robust_gate_fixes_on(config)`, its only reader. Every gated site asks the predicate.
- The kill-switch table row (`config/kill_switches.py`, tag `mvp-0.59`), the registry classification (`params/parameter_registry.py`, structural/operational), the effective-defaults line (`probe.episode.robust_gate_fixes = true`, the golden's only change) and `ADDED_SINCE_BASE` in `test_retired_config_identities.py`.
- Not a projection switch: it changes no derivation a rebuild re-runs, so `router_objective_switches.projection_switches` and doctor's stale-switch check do not name it.
- `robust_composition` stays free of config: its new keyword `distinct_instruments` defaults to false (the predecessor), and each caller passes the predicate, so a caller not listed above keeps `mvp-0.58`'s behaviour by construction.

**To make it `mvp-0.60`** (if a vault reaches `mvp-0.59` before this lands):

1. `src/learnloop/algorithm_versions.py`: a constant `ROBUST_GATE_FIX_ALGORITHM_VERSION = "mvp-0.60"` with its comment after line 935, appended to `SUCCESSOR_CHAIN` after line 993, and line 1038 becomes `ROBUST_GATE_FIX_VERSIONS = successors_from(ROBUST_GATE_FIX_ALGORITHM_VERSION)`. No call site changes.
2. `src/learnloop/ops/upgrades.py` `UPGRADES` (after line 121): `Link(ROBUST_GATE_FIX_ALGORITHM_VERSION, idempotent_projection)` (nothing derived from history moves); `tests/test_upgrades.py` `EXPECTED_ACTIVATIONS` its row.
3. Text: the tag in `config/kill_switches.py:146`, the schema comment (`config/schema.py:285`), the registry rationale (`params/parameter_registry.py:2674`), the docs of commit `1026d8e109`.
4. Goldens and pins, as at `mvp-0.59`: the `algorithms.algorithm_version` line of `tests/goldens/effective_defaults.toml`, the identity pins that move by tag (`python tests/test_identity_pins.py --write`, with the reason), and the version pins naming the latest tag (`test_facet_belief_successor.py`'s first test and its siblings, by the mechanical script the earlier successors used).
5. `tests/test_robust_completion_gate.py`: `TAG` becomes the new constant and `OLD` `FACET_BELIEF_FIX_ALGORITHM_VERSION`, so the twins compare against `mvp-0.59`.

## 2. Fix 1: only a fragile stop ends the episode (`de79d80997`)

`_robust_gate_verdict` now returns `robust_gate_completion(decision, stop_only=robust_gate_fixes_on(config))`: with the fixes, `couldnt_reliably_distinguish` only when `abstained and should_stop`; without, on any abstention, as before. The counterfactual and the logged forecast read the same decision.

- Fail-first: `test_the_gate_does_not_end_a_planted_episode_whose_next_probe_pays` (surface_only seed 12, the gate deciding): at the commit before, the episode ended `couldnt_reliably_distinguish` after two answers (`AssertionError: 'couldnt_reliably_distinguish' != 'couldnt_reliably_distinguish'`); after, it asks on (the gate's first decision is logged `abstained=True, should_stop=False`).
- Twins: `test_at_the_floor_the_gate_still_ends_the_episode_on_a_fragile_pick` (the same run at `mvp-0.58`: ends after two, robust_initial_grasp 0.838, as K9.0 traced), `test_with_the_switch_off_the_episode_is_the_floors_exactly` (the switch off at `mvp-0.59` gives the floor's result and the same gate decisions), and plain-value tests of `robust_gate_completion` both ways.

## 3. Fix 2: distinct instruments (`7d495eb654`)

`_distinct_ranked` drops, from the score-ranked list, every candidate whose members equal an earlier candidate's, before the runner-up is taken and agreement counted, in `evaluate_selection` (ensemble members) and `evaluate_series_selection` (the nats series; `evaluate_selection_credible_sets` passes its flag on). Identity is exact equality of what the selector reads, not the decision-context hash: an ensemble is a function of more than the hash names (the rows and the channel), and equality is cheap at these slate sizes. Keeping the first occurrence keeps the best-ranked copy (with equal members, the one with fewer expected seconds), so the chosen slot never changes.

- Fail-first: `test_the_gate_no_longer_reads_a_cards_second_item_as_its_rival` (schema_without_transfer seed 11, where the twin alone made the pick fragile: agreement passes): at the commit before, the gate's first decision was `couldnt_reliably_distinguish`; after, `act` with a positive margin. The strict xfail `test_a_second_item_of_the_same_card_does_not_make_the_winner_fragile` now passes with the flag, and also equals the lone item's decision.
- Twins: without the flag the twin gives mvp-0.58's decision exactly (`RobustDecision(..., lcb_advantage_over_runner_up=0.0, ..., abstained=True, 'couldnt_reliably_distinguish')`), likewise for identical credible sets and in the valuation (`test_without_the_fix_the_valuation_abstains_on_the_twin`); at the floor the planted twin still makes the pick fragile with margin 0.0. A distinct card stays the runner-up (`test_a_distinct_rival_is_still_compared`).
- The valuation keeps valuing the twin after the first pick, conditionally: to the model a second item of the card is a further independent answer, and it is added while that clears the stop (`test_the_valuation_licenses_a_card_whose_second_item_is_beside_it`). Whether two items of one card should count as independent observations is the instruments' modelling, not this fix.

## 4. The planted suite (`75b37141f5`)

The sim's vault helper (`tests/sim_probe_validation_helpers._vault_with_confusable`) builds at the head (the `mvp-0.6` pin goes) and keeps two of its three switches off, for K9.0 §6's reasons: placement (with it on, state sync opens no episode for a new learning object and the report is empty) and FG1 (`followup.generate_and_serve`: the episode opens but no parametric instance is minted, so nothing is served). Value of information is off where the gate is to decide and on (`value_of_information=True`) where the value stop is.

- (i) **Arc close**, `tests/test_sim_planted_types_forty_seeds.py`: per type, 40 seeds (11-50), label and action accuracy at least 26 (false pass 4.0% at a true rate of 0.5, false fail 5.4% at 0.75), every episode within its budget, and U-021's budget on the same runs, per type (6 of 40, stricter than over all 200). One test per type, so the gate's workers share the runs (about 10 s each in the test lane). Run: 5 passed.
- (ii) **Landing lane**, `tests/test_sim_probe_validation.py` (five seeds per type at the head, the gate deciding; about 7 s): the abstention budget (the strict xfail `test_planted_episodes_abstain_within_the_abstention_budget` passes: 0 of 25) and `test_the_gate_ends_no_episode_whose_next_probe_pays` (from the gate's logged decisions: wherever it said the next probe pays, the episode went on; an episode it ended, it ended on a fragile stop).
- (iii) **Where value decides**, `test_where_value_decides_each_stop_is_the_one_its_numbers_claim` (two seeds per type, about 9 s): no episode abstains, the gate logs nothing, and at each value stop the recorded best next probe and every lookahead batch tried are worth no more than their minutes at the robust lower bound. The regret bar was not taken: computed from what the sim stores, the mean regret of the action taken against the planted type's own action is 1.27 minutes against a probe's 0.74 (per type 0.45 to 4.11), above the stop's own predicted loss on two types; asserting it would assert something false or invent a tolerance. Ledger D-43 (owner).
- The five-seed label-accuracy gate (`test_planted_types_pass_the_checkpoint_gate`, threshold 0.6 on five runs) is replaced by (i): five runs cannot tell a rate (K9.0 §3(c)). Its completion and budget assertions stay, as `test_every_planted_episode_completes_within_its_budget`, which also asserts the report holds every (type, seed).
- `sim/diagnostic_validation.py`'s docstring says the responder stays behavioural, noisier than the cards' rows, and why (answering from the instruments' model would make the simulation circular), and that a seed does not fix the ensembles' draws.

Mutations, not committed. `robust_gate_completion` ignoring `stop_only`: 8 tests fail (the plain-value test, the fail-first, the five-seed budget, the gate check, and four of five forty-seed types; unfamiliar abstains too rarely to fail). `_distinct_ranked` returning its input: 4 fail (the twin-candidates test that was the strict xfail, the credible-set twin, the valuation twin, the planted twin).

### 4.1 Measurements (scratch, the test lane's conftest; 40 seeds per type)

| Configuration | robust_initial_grasp | unfamiliar | surface_only | schema_without_transfer | confuses_with | abstained |
|---|---|---|---|---|---|---|
| `mvp-0.59`, fixes on, gate decides | 39 | 37 | 32 | 30 | 33 | 0 / 200 (every episode at the budget of 4) |
| `mvp-0.58`, gate decides | 37 | 38 | 24 | 0 | 34 | 164 / 200 |
| `mvp-0.59`, switch off, gate decides | 37 | 38 | 24 | 0 | 34 | 164 / 200 |
| `mvp-0.59`, fixes on, value decides | 37 | 37 | 24 | 27 | 34 | 0 |
| `mvp-0.59`, switch off, value decides | 37 | 37 | 24 | 27 | 34 | 0 |

The floor and the switch off equal K9.0's table (§1.1) for all 40 seeds of every type, including the five test seeds, and equal each other run for run (0 of 200 differ in completion, probe count or label). The fixed path equals K9.0's stop-only counterfactual. Value decides: the two switch states differ at 4 of 200 runs, all `unfamiliar`, in probe count (1 or 2), in both directions; two runs of the same configuration differ at 3 and 4 seeds of `unfamiliar` as well, so these are the ensembles' episode-id seeds, not the fix (ledger D-42). By the code no value-decided episode can end differently: the gate's verdict there reaches only the receipt.

## 5. Shadow comparison

Fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp058` (three vaults at `mvp-0.58`) under `fixtures-local/k90b/`, upgraded to `mvp-0.59` and `rebuild-derived-state` run with the base code and with this branch (source tip `52eca8ff7a`). Counts only, in `fixtures-local/k90b/deltas.md` (gitignored, kept for the owner; the copies and the base source are deleted).

- Every table, row by row: 392 of 402 identical on each copy; 6 equal once surrogate ids and write times are left out; 4 (activity observations, grade interpretations, measurement events, raw grade events) equal once the rebuild's regenerated ULIDs are masked, in their foreign keys and inside `payload_json` too. History does not move.
- The K9.0 record's counts: 58 probe episodes in all, every one `pending_items`; 0 completed; 0 value-stop receipts and 0 presentation receipts with a gate counterfactual (so 0 the fixed gate would call differently); 0 episodes completed `couldnt_reliably_distinguish` in any session kind (so 0 with `should_stop` false in their logged forecast); 0 gate forecasts; 0 stored valuation receipts that abstained `couldnt_reliably_distinguish`.

## 6. What changed in tests

- `tests/test_robust_selection_twin_candidates.py`: the strict xfail removed; the test passes `distinct_instruments=True` and also asserts the decision equals the lone item's. Added: the no-flag twin (exact predecessor), the distinct-rival case, the credible-set pair. The module docstring's tense.
- `tests/test_sim_probe_validation.py`: the module fixture runs at the head (was `mvp-0.6`); `test_planted_types_pass_the_checkpoint_gate` (strict xfail, five seeds, 0.6) removed, replaced by the forty-seed arc-close test; its completion assertions kept in `test_every_planted_episode_completes_within_its_budget`; the abstention-budget strict xfail removed (passes); two tests added (§4 ii, iii). `test_planted_confuses_with_is_diagnosed_within_budget` unchanged.
- `tests/sim_probe_validation_helpers.py`: the helper's signature (`version`, `value_of_information`, `switches_off`) and `run_records`. Its other caller, `test_ux_phase4_feedback.py::test_f1l_the_sim_skips_a_covered_instrument_instead_of_aborting_the_run`, now runs at the head and passes.
- New: `tests/test_robust_completion_gate.py`, `tests/test_sim_planted_types_forty_seeds.py`.
- No other assertion changed.

## 7. Gates

- Targeted: `scripts/affected_tests.py --base ed96d1b9d0` names 1,315 files (the schema and `algorithm_versions` are imported nearly everywhere); run in 14 chunks of up to 100 at `-n 4 -m "not arc_close"`, behind the full-suite lock, in a 5 GB scope through the empty-home wrapper, on the source tip `1026d8e109`: **28,550 passed, 101 skipped, 12 xfailed, 0 failed**. The forty-seed file (arc close) ran separately: 5 passed.
- Vault: references regenerated once after the source commits (`6e564dbd1e`); a second `generate_all.py` on the clean tree changed nothing. `db_validate_reference.py` asked for the prose leaf count (1183, `7ea30730b6`) and then passed; `module_validate.py` and `validate_vault.py` pass; `desktop_validate.py` fails as it does at the base (it hard-codes 324 TypeScript files at `:196`, the tree has 326; nothing under `apps/` or the Desktop notes changed here). `scripts/check_gate_partition.py`: 30,898 collected, landing 30,833 + arc_close 65.
- `test_identity_pins`, `test_retired_config_identities`, `test_architecture`, `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_structure_ratchets`, `test_kill_switches`, `test_registry_audit`, `test_upgrades`, `test_facet_belief_successor` and the two step files: 378 passed. No pin moved, no ratchet rose.
- `ruff check` clean; `lint-imports --no-cache` 42 kept, 0 broken.

## 8. What I did not verify

- Calibration-session episodes and `robust_gate_with_value = true` vaults were not simulated (the gate decides there exactly as in the sim's configuration, by `robust_gate_applies`).
- Real histories: the owner copies hold no episode past `pending_items`, so the shadow shows the fixes inert there; their effect is shown only on the synthetic runs.
- Only the one sim vault shape (K9.0 §7).
- The landing gate's full selection, the durability lane, `--fresh-connections`, the rest of the arc-close gate, vitest; no GUI.
