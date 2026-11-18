# E1. Switches split

Base `c65d146285`, branch `refactor/e1-switches-split`. Step 0 was recorded from HEAD before changing the source or its callers.

## Step 0

R is objective/plan serving, T is attempt availability and the evidence admission rules bundled with it, P is due-date or projection state, and X is supporting metadata or an imported dependency.

| Class | Top-level name(s) | What they decide |
|---|---|---|
| T | `LEARNER_REPORT_PREFIX` | Prefix that marks a learner's report as attributed opinion. |
| T | `AVAILABLE_AT_SQL` | Unaliased SQL expression for the availability time. |
| T | `RECEIVED_AT_RECORDED`, `RECEIVED_AT_INFERRED` | Labels for a receipt written at ingestion and one inferred during migration. |
| T | `available_at_reads_on`, `self_report_not_validated_on` | Whether a cutoff uses receipt time and whether reports are excluded from validated evidence, respectively. |
| T | `available_at`, `attempt_time_sql`, `known_at` | Receipt time with occurrence fallback, the gated SQL expression, and the corresponding loaded-row time. |
| T | `validated_resolution_ids` | Which resolution IDs count as validated history. |
| P | `interval_factor_removed` | Whether FSRS due dates omit the surprise interval factor. |
| P | `INTERVAL_FACTOR_SNAPSHOT_KEY`, `FACET_BELIEF_FIXES_SNAPSHOT_KEY` | Rebuild receipt keys for the interval factor and facet-belief fixes. |
| P | `projection_switches` | Which projection settings the rebuild receipt records at this algorithm version. |
| R | `objective_on`, `objective_scores_on`, `sensors_in_value_on` | Objective serving, comparison-score availability, and the sensor correction to value. |
| R | `stop_coin_rate`, `pick_open_share` | Exploration rates for the stop coin and deliberately open misconception picks. |
| R | `CHECKS_EMBEDDED`, `CHECKS_RATE`, `CHECKS_OFF`, `check_mode`, `calibrated_weight_on` | Check modes and frequency, and whether checks inform the mixture weight. |
| R | `fitted_models_on`, `learned_tail_on`, `followup_on`, `monotone_combiner_on` | Which fitted models, residual tail, follow-up feature, and combiner form serve. |
| R | `FOLLOWUP_GENERATOR_SWITCHES`, `followup_generator_switches` | Keys and evaluated values that identify the follow-up generator. |
| R | `FOLLOWUP_SWITCHES`, `followup_switch_snapshot` | Keys and evaluated values that identify the prefetch boundary. |
| R | `SEED_NEUTRAL_SWITCHES`, `SEED_NEUTRAL_OBJECTIVE_KEYS`, `SEED_NEUTRAL_IDENTITY_KEYS` | Speed and preference inputs named by the boundary but omitted from its draw seed. |
| R | `COMMON_DRAW_OBJECTIVE_KEYS`, `COMMON_DRAW_IDENTITY_KEYS`, `MISS_CAUSE_OFFER_KEY` | Miss-cause settings, marks and the offer card field that share draws across settings. |
| R | `lesson_offers_on`, `failure_share_to_other_policy_on`, `lessons_compete_with_followups_on` | Whether offers serve, where a failed policy's share goes, and whether offers enter the follow-up competition. |
| R | `learner_preferences_on`, `workbench_is_open_item_on` | Whether the plan offers learner picks and treats a workbench problem as open. |
| R | `lesson_sources_follow_diagnosis_on`, `lesson_candidate_after_cold_miss_on` | Which source context a served lesson gets and which missed topics can be offered. The first is a plan handoff switch read by the lesson brief. |
| R | `preferences_inform_router_on`, `miss_cause_sensor_on`, `miss_cause_in_value_on` | Whether preference and miss-cause signals reach the router and whether miss cause enters numeric value. |
| X | `__all__` | The module's explicit public export inventory. |
| X | `annotations`, `Iterable`, `Mapping`, `Any`, `FACET_BELIEF_FIX_VERSIONS` | Future-annotations directive, types, and the algorithm-version set imported by the projection predicate. |

Direct imports at the base, including attribute reads through a module alias. Files that only name the module in text are marked.

| File | Imported names |
|---|---|
| `src/learnloop/adaptive_difficulty/history_card.py` | `attempt_time_sql` |
| `src/learnloop/adaptive_difficulty/outside.py` | `known_at` |
| `src/learnloop/adaptive_difficulty/reading_cache.py` | `followup_on` |
| `src/learnloop/attempts/attempts.py` | `interval_factor_removed` |
| `src/learnloop/confidence_events.py` | `attempt_time_sql` |
| `src/learnloop/config/kill_switches.py` | Text only |
| `src/learnloop/daily_plan/engine.py` | `CHECKS_OFF`, `check_mode`, `lessons_compete_with_followups_on`, `workbench_is_open_item_on` |
| `src/learnloop/daily_plan/learner_action.py` | `learner_preferences_on`, `preferences_inform_router_on` |
| `src/learnloop/daily_plan/lesson_offer.py` | `MISS_CAUSE_OFFER_KEY`, `lesson_offers_on`, `lessons_compete_with_followups_on`, `miss_cause_sensor_on`, `preferences_inform_router_on` |
| `src/learnloop/daily_plan/lesson_suggestion.py` | `lesson_candidate_after_cold_miss_on`, `lesson_offers_on` |
| `src/learnloop/daily_plan/objective_card.py` | `miss_cause_sensor_on`, `preferences_inform_router_on` |
| `src/learnloop/daily_plan/objective_chooser.py` | `CHECKS_OFF`, `COMMON_DRAW_IDENTITY_KEYS`, `COMMON_DRAW_OBJECTIVE_KEYS`, `MISS_CAUSE_OFFER_KEY`, `SEED_NEUTRAL_IDENTITY_KEYS`, `SEED_NEUTRAL_OBJECTIVE_KEYS`, `SEED_NEUTRAL_SWITCHES`, `calibrated_weight_on`, `check_mode`, `failure_share_to_other_policy_on`, `followup_generator_switches`, `followup_on`, `followup_switch_snapshot`, `learned_tail_on`, `lessons_compete_with_followups_on`, `miss_cause_in_value_on`, `miss_cause_sensor_on`, `objective_scores_on`, `preferences_inform_router_on`, `stop_coin_rate` |
| `src/learnloop/daily_plan/objective_inputs.py` | `fitted_models_on`, `followup_on`, `known_at`, `lesson_offers_on`, `miss_cause_in_value_on`, `miss_cause_sensor_on`, `monotone_combiner_on`, `stop_coin_rate` |
| `src/learnloop/daily_plan/policy.py` | `lesson_offers_on`, `lessons_compete_with_followups_on`, `objective_on` |
| `src/learnloop/daily_plan/router_card.py` | `attempt_time_sql`, `objective_on` |
| `src/learnloop/db/stores/lessons.py` | `attempt_time_sql` |
| `src/learnloop/diagnosis/causal_attribution.py` | `pick_open_share` |
| `src/learnloop/diagnosis/split/history.py` | `attempt_time_sql`, `known_at`, `validated_resolution_ids` |
| `src/learnloop/goals/goal_contracts.py` | `objective_on` |
| `src/learnloop/learner_context.py` | `attempt_time_sql` |
| `src/learnloop/ops/capture_report.py` | `miss_cause_sensor_on`, `preferences_inform_router_on` |
| `src/learnloop/ops/doctor.py` | `FACET_BELIEF_FIXES_SNAPSHOT_KEY`, `INTERVAL_FACTOR_SNAPSHOT_KEY`, `projection_switches` |
| `src/learnloop/reader_learner_state.py` | `attempt_time_sql` |
| `src/learnloop/router_objective/checks.py` | `CHECKS_EMBEDDED`, `CHECKS_OFF`, `check_mode` |
| `src/learnloop/router_objective/miss_cause.py` | `attempt_time_sql` |
| `src/learnloop/router_objective/preferences.py` | `attempt_time_sql`, `preferences_inform_router_on` |
| `src/learnloop/router_objective/price.py` | Text only |
| `src/learnloop/router_objective/scores.py` | `attempt_time_sql`, `lesson_offers_on` |
| `src/learnloop/router_objective/tail_data.py` | `followup_on`, `known_at`, `lesson_offers_on` |
| `src/learnloop/router_objective/value.py` | Text only |
| `src/learnloop/substrate/rebuild_orchestrator.py` | `projection_switches` |
| `src/learnloop/substrate/replay.py` | `projection_switches` |
| `src/learnloop/teacher/brief.py` | `lesson_sources_follow_diagnosis_on` |
| `src/learnloop/teacher/diagnosed_sources.py` | `attempt_time_sql` |
| `src/learnloop_sidecar/context.py` | `workbench_is_open_item_on` |
| `src/learnloop_sidecar/handlers/goals.py` | `objective_on` |
| `tests/goldens/structure.toml` | Text only |
| `tests/identity_pins_helpers.py` | `followup_generator_switches`, `followup_switch_snapshot` |
| `tests/successor_switches.py` | `FOLLOWUP_SWITCHES` |
| `tests/test_facet_belief_successor.py` | `FACET_BELIEF_FIXES_SNAPSHOT_KEY`, `INTERVAL_FACTOR_SNAPSHOT_KEY`, `projection_switches` |
| `tests/test_ih2_lessons_compete.py` | `lessons_compete_with_followups_on` |
| `tests/test_ih3_learner_preferences.py` | `learner_preferences_on` |
| `tests/test_ih4_preferences_inform_router.py` | `preferences_inform_router_on` |
| `tests/test_ih5_successor.py` | `failure_share_to_other_policy_on` |
| `tests/test_ih6_workbench_open_item.py` | `SEED_NEUTRAL_SWITCHES`, `workbench_is_open_item_on` |
| `tests/test_ih7_lesson_sources_follow_diagnosis.py` | `lesson_sources_follow_diagnosis_on` |
| `tests/test_ih_lesson_candidate_after_cold_miss.py` | `SEED_NEUTRAL_OBJECTIVE_KEYS`, `SEED_NEUTRAL_SWITCHES`, `lesson_candidate_after_cold_miss_on` |
| `tests/test_kill_switches.py` | Text only |
| `tests/test_ro1_availability.py` | `AVAILABLE_AT_SQL`, `attempt_time_sql`, `available_at` |
| `tests/test_ro1_availability_reads.py` | `AVAILABLE_AT_SQL`, `attempt_time_sql`, `known_at` |
| `tests/test_ro1_interval_factor.py` | `interval_factor_removed` |
| `tests/test_ro1_projection.py` | `INTERVAL_FACTOR_SNAPSHOT_KEY`, `available_at_reads_on`, `interval_factor_removed`, `self_report_not_validated_on` |
| `tests/test_ro1_self_report.py` | `validated_resolution_ids` |
| `tests/test_ro1_successor.py` | `available_at_reads_on`, `interval_factor_removed`, `self_report_not_validated_on` |
| `tests/test_ro4_successor.py` | `objective_on`, `objective_scores_on`, `sensors_in_value_on` |
| `tests/test_ro5_checks.py` | `CHECKS_EMBEDDED`, `CHECKS_RATE` |
| `tests/test_ro5_successor.py` | `CHECKS_EMBEDDED`, `CHECKS_OFF`, `CHECKS_RATE`, `check_mode`, `fitted_models_on`, `pick_open_share`, `stop_coin_rate` |
| `tests/test_ro6_successor.py` | `learned_tail_on` |
| `tests/test_ro6_tail_data.py` | Text only |
| `tests/test_rofu_generator_switches.py` | `FOLLOWUP_GENERATOR_SWITCHES` |
| `tests/test_rofu_learning.py` | `available_at` |
| `tests/test_rofu_successor.py` | `followup_on` |
| `tests/test_rofu_switch_key.py` | `FOLLOWUP_GENERATOR_SWITCHES`, `FOLLOWUP_SWITCHES` |
| `tests/test_rospeed2_connections.py` | `COMMON_DRAW_IDENTITY_KEYS`, `COMMON_DRAW_OBJECTIVE_KEYS`, `FOLLOWUP_GENERATOR_SWITCHES`, `FOLLOWUP_SWITCHES`, `SEED_NEUTRAL_IDENTITY_KEYS`, `SEED_NEUTRAL_OBJECTIVE_KEYS`, `followup_generator_switches` |
| `tests/test_rospeed_ad_link.py` | `FOLLOWUP_GENERATOR_SWITCHES`, `FOLLOWUP_SWITCHES` |
| `tests/test_sg_slip_vs_gap.py` | `miss_cause_in_value_on`, `miss_cause_sensor_on` |
| `tests/test_sg_successor.py` | `COMMON_DRAW_OBJECTIVE_KEYS`, `SEED_NEUTRAL_SWITCHES`, `followup_generator_switches` |
| `tests/test_te3b_successor.py` | `lesson_offers_on` |

`available_at_reads_on`, `self_report_not_validated_on`, `available_at`, `interval_factor_removed`, and the snapshot keys also have internal consumers among the definitions above. There are no direct importers of the receipt-source labels or the report prefix. No importer takes the typing bindings, version-set binding, or `__all__` from this module. Scripts, vault generators, and hand-written vault notes have no imports of the module. The vault's DB generator mentions the underlying config keys as part of the schema description.

## Homes and boundaries

- **T choice.** `db/attempt_availability.py` owns the cutoff for the persisted attempt ledger. Its only imports are standard-library types, and the docstring states the rule EP0t can build on.
  **Alternatives.** Both `adaptive-difficulty-never-writes-evidence` and `infrastructure-does-not-import-domains` block `attempts/availability.py` for current readers. A root leaf would work, but the ledger has a home in `db` and a root file would add to the root-module ratchet.
- **P scheduler choice.** `config/scheduler_switches.py` keeps the interval-factor predicate beside the scheduler's config schema. Both the live attempt fold and projection snapshot read it.
  **Alternatives.** A new leaf in `scheduling` creates an attempts-to-scheduling edge and a substrate-to-scheduling edge in the frozen package graph. Even reusing `scheduling/fsrs.py` leaves the substrate edge. `config/kill_switches.py` is inventory code with no serving readers.
- **P projection choice.** `substrate/projection_switches.py` owns the rebuild receipt's keys and the settings recorded under them. Replay, the rebuild orchestrator, and doctor share the leaf.
  **Alternatives.** Putting this in the scheduler config reader would mix receipt schema with the live interval switch. Putting it in a rebuild coordinator would make replay and doctor load orchestration to read config.
- **R and X.** All 34 router definitions stay in `router_objective_switches.py` (**460 → 311 lines**). The export inventory drops the 14 moved entries. Type imports follow their definitions, and the projection reads the same version set directly.

**Importers rewritten (26 files).** In `src/learnloop/`: root 3, `adaptive_difficulty/` 2, `attempts/` 1, `daily_plan/` 2, `db/stores/` 1, `diagnosis/split/` 1, `ops/` 1, `router_objective/` 4, `substrate/` 2, `teacher/` 1. In `tests/`: 8. Scripts and vault scripts: 0. The remaining edits in callers update documentation or the kill-switch scan.

**Function-local imports.** `ops.doctor._check_projection_switches` moves its three imports to module scope. The destination depends only on the version-set and scheduler-config leaves. The measure confirms it is outside all cycles. Every other local import retains its timing:

| Module or test | Functions with repointed local imports |
|---|---|
| `attempts.attempts` | `_belief_update` |
| `confidence_events` | `learner_events`, `taps_before` |
| `daily_plan.objective_inputs` | `_combiner_with_traces` |
| `db.stores.lessons` | `pending_delayed_checks` |
| `learner_context` | `_traces` |
| `router_objective.miss_cause` | `_between`, `_offer_rows`, `beta_rows`, `latest_misses`, `surprise_reference` |
| `router_objective.preferences`, `router_objective.scores` | `features_at`, `exam_result_known`, respectively |
| `router_objective.tail_data` | `_receipt`, `logged` |
| `substrate.rebuild_orchestrator`, `substrate.replay` | `rebuild_all_derived_state`, `rebuild_derived_state`, respectively |
| `teacher.diagnosed_sources` | `_asked_miss`, `_miss` |
| `test_ro1_availability_reads.py` | `test_the_predicate_is_the_predecessors_column_below_the_tag_or_switched_off` |
| `test_ro1_projection.py` | `test_every_switch_combination_moves_exactly_its_own_part` |
| `test_rofu_learning.py` | `test_the_join_rows_count_one_outcome_once_per_protocol_and_only_when_known` |

**Remaining evidence imports.**

- `adaptive_difficulty/reading_cache.py` reads `followup_on` to gate the objective job's held reading map. This switch enters the follow-up generator and prefetch identities.
- `diagnosis/causal_attribution.py` reads `pick_open_share` to assign the router's deliberately open misconception-pick arm while writing the report.

The direct-only contract `evidence-does-not-import-objective-switches` forbids `attempts`, `learner`, and `substrate` from importing `learnloop.router_objective_switches`. The contract comment names the two remaining readers and no exception is added.

## Proofs

Scratch scripts and logs live in the supplied `refactor-e1` scratch directory (`$S`).

- **P1.** `prove_e1.py` finds 14/14 moved definitions AST-identical to `git show HEAD:src/learnloop/router_objective_switches.py`, and the old module loses exactly those definitions. The 34 remaining router definitions match. The docstring and imports change, and the class X `__all__` list drops exactly the moved entries. `audit_tip.py` verifies all 48 moved-name import bindings reach their expected home and scope. It also checks that 28 caller files match the base once imports and qualified doc references are normalized. The separate kill-switch inventory edits keep all three new files in its scan. The affected structural assertion keeps its original failure message byte for byte.
- **P2.** `base-globals.json` was captured before editing. A same-process comparison against the HEAD module verifies 21 global reads across eight functions. External objects use identity, including `FACET_BELIEF_FIX_VERSIONS`. Moved internal reads resolve to their corresponding function or literal in the new home. Annotations and signatures match.
- **P3.** `base-values.json` and `tip-values.json` are byte-equal for all eight functions and six constants. Both sides use the config model's defaults and a config with all four moved switches flipped. Each is also exercised at the latest tag so the facet-belief receipt key is covered. Cases include delayed receipts, occurrence fallback, unaliased and aliased SQL, learner-report filtering, and both projection snapshot shapes.
- **P4.** `base-audit.txt` screens 1,887 test Python files for monkeypatch, mock patch and assignment targets. It found zero on this module or its names. No mutation target was repointed and T4 required no conversion. The three whole-module test aliases read only R names.
- **P5.** The scratch-only copy of `scripts/refactor_measures.py` also enumerates untracked source. Largest component **84 → 84**, modules in any cycle **220 → 220**. No module joined or left either set. Root modules **35 → 35**. `measure-base.json` and `measure-tip.json` contain the membership and edges. The fail-first test temporarily added `from learnloop.router_objective_switches import objective_on` in `learner/__init__.py`. The linter exited 1 with **42 kept, 1 broken**, naming the new contract and import. The temporary addition was reverted byte for byte.
- **P6.** `tests/test_architecture.py` discovers the leaves dynamically. No frozen local domain edge is displaced or created, so `tests/architecture_function_local_domain_imports.txt` needs no changes. The module generator discovers the new files and their imports. The DB generator's inventory describes the same config keys and names no moved function's module. No hand-written vault note names the old home of a moved member. No vault generator ran and the generated Reference files were left untouched.

## E2 handoff

The chooser still reads failure-share routing, check mode/calibration, the stop-coin rate, and the follow-up and sensor gates. A pure choice needs those inputs resolved upstream and must preserve the failure fallback and the coin's draw order. `followup_switch_snapshot` contributes to the prefetch boundary, `followup_generator_switches` to the generator payload, and the seed-neutral/common-draw keys filter what enters the numeric seed. Keep those identities and exact propensities at fixed draws. Availability and projection settings now have their own homes upstream of the choice.

## Validation

- `$T tests/test_identity_pins.py tests/test_architecture.py tests/test_test_layout.py tests/test_structure_ratchets.py tests/test_cli_help_snapshot.py tests/test_diagnosis_journey_golden.py -q -n 3`: **408 passed** in 57.12 s (`core-tests.txt`). The identity tests, their helpers, and all goldens are byte-identical to HEAD.
- `bash "$S/focused_tests.sh" 1`: `$T` with 36 explicit paths, `-q -m "not arc_close" -n 3 -o faulthandler_timeout=45`. **1,134 passed, 40 warnings** in 173.09 s (`focused-1.txt`, which begins with the full command). The script found 38 substring matches under `tests/test_*.py` and omitted the two known startup hangs below. The warnings are numeric overflow, divide-by-zero, and invalid-division warnings in the existing AD-link comparison cases.
- `$PY ruff check`: all checks passed (`ruff.txt`).
- `$PY lint-imports --no-cache`: **43 kept, 0 broken** after restoring the fail-first edit (`imports.txt`).
- `git diff --check`: passed. Final `.pytest_tmp` check found no `run-*` directories.

Matching files unverified because they hang at startup in the sandbox: `tests/test_ih4_preferences_inform_router.py` and `tests/test_ih6_workbench_open_item.py`. The other listed startup hangs, `tests/test_mobile_v3_probes.py`, `tests/test_mobile_rpc.py`, and `tests/test_mobile_v4_reader.py`, did not match the selection and were not run. No sandbox failure occurred in the executed tests, so there are no failed node IDs to hand off. Socket and bubblewrap paths, `arc_close` cases, the full suite, and the orchestrator's landing gate remain unverified.

**Existing behavior found during the move.** `probe_empty_receipt.py` shows that SQL admits a synthetic row with empty `received_at` before occurrence and the loaded-row predicate excludes it, on both HEAD and the tip (`empty-receipt.txt`). Logged as E-1 in the bug ledger for EP0t or arc E's close. No behavior fix is in this move. No stop condition triggered.
