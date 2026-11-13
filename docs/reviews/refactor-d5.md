# Refactor D5: constant gates in the substrate, rebuild, doctor, and the canonical-state predicate

Step D5 of arc D (`docs/specs/refactor_strategy_v3.md` §2.6), on branch `refactor/d5-constant-gates-substrate`, based on main `41387e1236` (D4 landed; the floor `OLDEST_SUPPORTED = mvp-0.58` is enforced at every door, the head is `mvp-0.59`). Structure track: no served or persisted value changes for a vault at or above the floor. The method is D4's (`docs/reviews/refactor-d4.md`).

## 1. Step 0, before any deletion

### (a) The count

`scripts/refactor_measures.py` at the base, floor `mvp-0.58`: 83 gate sites (`x in *_VERSIONS`), 75 constant at the floor, 8 varying (the facet-belief successor's `FACET_BELIEF_FIX_VERSIONS` / `FACET_BELIEF_CORRECTION_VERSIONS`, `mvp-0.59` only: live branches, not this step's). Of the 75, this step's files hold 19 (S1-S19 below) plus D4's three left-overs (L1-L3). The classifier counts only `in` tests against a set; it does not see `is_canonical_state_vault`'s 32 calls (a predicate over `CANONICAL_STATE_VERSIONS`), which are listed separately (§1(d)).

Every set tested at these sites (`CANONICAL_STATE_VERSIONS`, `P0_PROJECTION_VERSIONS`, `REGRADE_CONTRACT_VERSIONS`, `RECURRENCE_GROUP_VERSIONS`) holds both `mvp-0.58` and `mvp-0.59` (checked by importing them), so each gate takes its successor branch on every vault that opens.

### (b) The replay question: can a dead branch still run?

Rebuild replays attempts written under every older tag, under today's tag. Every site below except S13 and the stamp half of S19 reads **the vault's current tag** (`vault.config.algorithms.algorithm_version`, or the `algorithm_version` argument the projection's callers pass from it): below the floor it is dead, whatever tag a replayed row was written under. Where a vault's tag can come from was proven in D4 §1(b) and is unchanged at this base: `load_vault` refuses below the floor and a keyless config (ADR-019); doctor, the MCP server's and phone host's attach, and journals below the floor are refused the same way; a shadow rebuild's forced tag is refused below the floor (`shadow_rebuild.build_candidate_config`); `learnloop upgrade` sets the vault's tag to the table's links, which start at the floor; configs built in code (`LearnLoopConfig()`, tag `mvp-0.6`) reach none of these sites in production (`params/parameter_registry` reads numeric leaves only, `substrate/activities._algorithm_version` is a stamp, ledger D-23); the two harnesses that build their own vault below the floor (`learnloop goldenpath bootstrap`, `learnloop recall-calibration`) are refused by it (D-24).

**A tag this code does not know** (ledger D-31): such a vault opens and today every gate here, and `is_canonical_state_vault`, reads it as below every tag, so it is served the pre-`mvp-0.7` (per-LO, legacy) model. After this step those sites serve it the head's branch. No supported vault holds such a tag, and the head's canonical state is what a newer checkout's vault actually holds, so this does not make D-31 worse for a supported vault; the door fix stays D-31's.

**The tracked fixtures.** `fixtures/migration_head` names `mvp-0.6` and `fixtures/mvp017_route_check_replay` `mvp-0.17`; both open only under the tests' below-floor allowance (D1). After this step a test that opens either at its own tag runs the head's projection path; D4 §4 already showed the `mvp-0.17` fixture rebuilds to the same rows at its tag and at the floor for the attempt path.

### (c) Every gate site in this step's files

Classes as D4: **(a)** a pure tag gate: the gate and its dead branch go. **(b)** tag and kill switch: only the tag half goes; the switch and its off-branch stay for D7. **(c)** a reader of old rows by shape, a marker or a row's own stored tag: kept. **(d)** kept for a later step, with the reason.

Line numbers are the base's (`41387e1236`).

| # | site | set | constant at `mvp-0.58` | dead branch (below the tag) | class |
|---|---|---|---|---|---|
| S1 | `substrate/canonical_projection.py:319` `load_canonical_projection_snapshot` | `P0_PROJECTION_VERSIONS` | yes | the projection reads the v1 observation ledger (no administration, interpretation, adjudication or quarantine lineage) | (a) |
| S2 | `substrate/canonical_projection.py:329` same | `P0_PROJECTION_VERSIONS` | yes | no effective-observation references are loaded | (a) |
| S3 | `substrate/canonical_projection.py:351` same | `REGRADE_CONTRACT_VERSIONS` | yes | no contract-unrecorded hold (`frozenset()`) | (a) |
| S4 | `substrate/canonical_projection.py:671` `project_canonical_facet_state` | `CANONICAL_STATE_VERSIONS` | yes | no canonical projection at all | (a) |
| S5 | `substrate/canonical_projection.py:675` `use_p0` | `P0_PROJECTION_VERSIONS` | yes | raw attempt-type mass (no reliability discount), no adjudicated-outcome override, the coarse outcome schema not loaded | (a) |
| S6 | `substrate/canonical_projection.py:734` `regrade_contracts` | `REGRADE_CONTRACT_VERSIONS` | yes | every non-superseded row across epochs, under the first cited contract; no unrecorded-contract hold | (a) |
| S7 | `substrate/canonical_projection.py:1219` `project_capability_residuals` | `CANONICAL_STATE_VERSIONS` | yes | no residual activation | (a) |
| S8 | `substrate/canonical_projection_rollout.py:83` `refresh_canonical_projection_on_startup` | `CANONICAL_STATE_VERSIONS` | yes | no startup refresh, no baseline marker | (a) |
| S9 | `substrate/p0_projection.py:47` `activate_p0_projection` | `P0_PROJECTION_VERSIONS` | yes | raises `ValueError` (a precondition) | (a) |
| S10 | `substrate/administration_adapters.py:331` `purpose_adapter_path_live` | `P0_PROJECTION_VERSIONS` (or the module constant `P1_PURPOSE_ADAPTERS_ENABLED`, `False`, no config) | yes | the attempt hot path applies its FSRS review unconditionally (an ineligible observation still rewrites the card) | (a) |
| S11 | `substrate/rebuild_orchestrator.py:441` `_run_identifiability` | `CANONICAL_STATE_VERSIONS` | yes | the replayer clears its table and writes no identifiability watermark | (a) |
| S12 | `substrate/recurrence_groups.py:85` `recurrence_active` | `RECURRENCE_GROUP_VERSIONS` | yes | no recurrence groups | (b): switch `recurrence.enabled` |
| S13 | `substrate/recurrence_groups.py:447` `_source_judgments` | `DECIDER_TIER1_VERSIONS` | not a vault tag | — | (c): the tag stored in a same-cause judgment's own `rationale` (strategy §2.6 names it) |
| S14 | `ops/doctor.py:452` `_merge_mvp06_facet_recall_aliases` | `CANONICAL_STATE_VERSIONS` | yes | under `--fix-state`, folds aliased rows of the per-LO `evidence_facet_recall_state` in place | (a) |
| S15 | `ops/doctor.py:1881` `_check_mvp07_canonical_state` | `CANONICAL_STATE_VERSIONS` | yes | the unregistered-canonical-facet check does not run | (a) |
| S16 | `ops/doctor.py:1915` `_mvp07_facet_severity` | `CANONICAL_STATE_VERSIONS` | yes | facet-registry issues are warnings, an empty registry is skipped | (a) |
| S17 | `ops/doctor.py:1981` `_check_facet_contract_completeness` | `CANONICAL_STATE_VERSIONS` | yes | only a facet declaring part of its contract is checked, as a warning | (a) |
| S18 | `ops/doctor.py:2838` `_check_pre_first_practice_identifiability` | `CANONICAL_STATE_VERSIONS` | yes | no identifiability check | (a) |
| S19 | `db/repositories.py:26689` `_guard_legacy_facet_write` | `CANONICAL_STATE_VERSIONS` on the row's stamp | the writers stamp the vault's tag | the per-LO legacy write passes (a row stamped with a pre-canonical tag) | gate half (a) once its writers are gone (L3); the `FACET_BELIEF_FIX_VERSIONS` half reads the row's own stamp: (c) |
| L1 | `learner/facet_evidence_timeline.py:425` `_with_p0_masses` | `P0_PROJECTION_VERSIONS` | yes | the timeline carries no P0 mass map | (a), with S1-S6 in one commit |
| L2 | `learner/facet_evidence_timeline.py:848` `_observation_events_by_facet` | `REGRADE_CONTRACT_VERSIONS` | yes | epochs ordered by first-seen stamp and accumulated across epochs; no unrecorded-contract hold | (a), with S1-S6 in one commit |
| L3 | `learner/facet_state_reader.py:56` `is_canonical_state_vault` | `CANONICAL_STATE_VERSIONS` | yes | the legacy (`mvp-0.6`) per-LO facet state, at each caller (§1(d)) | (a), caller by caller |

**Constant gates of the same sets outside this step's files**, left: `content/proposals/patches.py:648`, `:1111` (`CANONICAL_STATE_VERSIONS`; D6's files), `diagnosis/probe_robust.py:60` (`P0_PROJECTION_VERSIONS`; D6), and the sidecar's `handlers/serializers.py:358` and `handlers/workbench.py:156` (`CANONICAL_STATE_VERSIONS` tested directly, not through the predicate; they snapshot the presented contract): (d), for D6 with the rest of the package-level gates. They are not callers of `is_canonical_state_vault`.

### (d) L3: `is_canonical_state_vault` and every call

At the base the predicate has 32 calls and one wrapper (`attempts/grading.py:284`, a lazy indirection with the same name). Each reads the vault's current tag, so each `False` branch is dead at the floor. What each dead branch does:

| # | call | dead branch (the legacy vault) |
|---|---|---|
| C1 | `attempts/attempts.py:3296` | `_persist_attempt_application(write_legacy_facet_state=True)`: the per-LO `evidence_facet_recall_state` rows and the legacy `facet_uncertainty` rows are persisted (the legacy writer the strategy names, `attempts.py:3322` in its numbering) |
| C2 | `attempts/attempts.py:4264` | an attempt's facet priors read from the per-LO table (`repository.facet_recall_state`) |
| C3 | `attempts/attempts.py:5294` | the don't-know attribution keeps the legacy names (`recall_failure`, `scaffold_failure`) |
| C4 | `attempts/grading.py:373` `builtin_error_type_defaults` | the five legacy builtin severities |
| C5, C6 | `attempts/grading.py:1941`, `:1961` `_grading_error_taxonomy` | the grader's prompt offers the five legacy error types and their selection policy; legacy seed names are not filtered |
| C7 | `attempts/grading.py:1997` `_normalized_recall_error_type` | a grader's legacy error name is not mapped to its mechanism |
| C8-C16 | `learner/facet_state_reader.py:106`, `:363`, `:376`, `:391`, `:417`, `:463`, `:468`, `:521`, `:533` | the read-site wrappers call the legacy repository methods (per-LO recall rows, every stored uncertainty row whatever its stamp) |
| C17, C18 | `learner/capability_grid.py:122`, `:221` | the grid reports `supported=False`; no blueprint readiness |
| C19 | `learner/recall_coverage.py:645` | no canonical reader is built (each facet reads through the wrapper's legacy branch) |
| C20 | `learner/facet_diagnostics.py:395` | the per-cell mass falls back to facet-level mass |
| C21 | `learner/facet_evidence_timeline.py:1191` `ready_derivation` | no Ready derivation (`None`) |
| C22 | `daily_plan/headline.py:71` | no capability cells read for the headline classes |
| C23 | `diagnosis/misconceptions.py:280` | the statement-matching registry normalization instead of the compositional one |
| C24, C25 | `diagnosis/probe_instance_generation.py:244`, `:307` | no compositional pair; no mechanism ids among the misconception ids |
| C26, C27 | `goals/goal_certification.py:114`, `:219` | no demonstrated capabilities; no recipe gaps |
| C28 | `goals/goal_projection.py:709` | no blueprint readiness |
| C29 | `scheduling/selection_rewards.py:438` | the flat recall blend for a blueprint-bearing LO |
| C30 | `learnloop_sidecar/handlers/facet_detail.py:267` | no canonical reader |
| C31 | `learnloop_sidecar/handlers/knowledge_model.py:92` | `supported: false` in the facet timeline DTO |
| C32 | `learnloop_sidecar/handlers/facets.py:74` | facet rows keyed by their raw id, not the canonical one |

No string dispatch names the predicate (no `METHOD_REGISTRY`, Typer, `MODULE_INVENTORY` or `_reg_const` entry; no frontend or phone caller: the frontend reads the DTO fields `supported` / `modelVersion`, which keep their values at the floor). Two tests name it: `test_learner_read_model_pinning` (asserts a basic vault is canonical) and `test_today_headline` (patches `headline.is_canonical_state_vault` to `True`, T4).

### (e) The old-row readers, kept

Every reader in these packages that interprets a row by its shape, a marker or its own stored tag. None is a tag gate on the vault; each stays whatever the floor.

| site (base lines) | what it reads | why it stays |
|---|---|---|
| `substrate/canonical_projection.py:364` `_historical_contract` and the fallback at `:757-779` (the strategy's `:736`) | rows citing no contract, or mixed contracts | evidence written before contract lineage (`mvp-0.7`) or by a pre-contract regrade folds against the live item's rubric |
| `substrate/canonical_projection.py:745` `current_epoch(attempt_evidence)` | grading epochs; a revision-less only grade by shape | the regrade-contract reading of rows written before `mvp-0.26` (the gate around it, S6, goes; the reader is the kept branch) |
| `substrate/canonical_projection.py:826` `unassessed_evidence_row`, `:946` `unverified_evidence_row` | the evidence row's attribution block and its interpretation key | PF-c rows written under or before the unassessed rule replay as written |
| `substrate/canonical_projection.py:586` `_adjudicated_score_fraction` | an adjudication heading the interpretation chain | adjudications recorded before ruling A carry their direction only there |
| `substrate/canonical_projection.py:955-957` | a row without an `observation_id` | the unresolved-cause factor keys such a row `attempt:criterion:0` |
| `substrate/canonical_projection.py:170` `p0_effective_evidence_mass` | an attempt with no active interpretation | a pre-P0.2 attempt contributes zero reliable mass (fail-closed) |
| `learner/facet_evidence_timeline.py:916-931` | the epoch's contract, else the live item's rubric | the timeline's twin of the projection's fallback |
| `learner/facet_evidence_timeline.py:808` `_decoded_attribution` | a row without attribution | legacy rows decode to `None` |
| `grading_epochs.py` (`current_epoch`, `ordered_epochs`, `only_grade`) | revision-less rows, epochs citing no contract | shared by replay, the projection and the timeline (D4) |
| `learner/facet_state_reader.py:168` `current_facet_uncertainty`, `:470`, `:535` | a stored uncertainty row's own `algorithm_version` | row tags (and the set varies at the floor) |
| `db/repositories.py:26687` (S19's other half) | the stamp of an uncertainty row being written | the successor's rows are admitted by their own tag |
| `substrate/recurrence_groups.py:447` (S13) | a judgment's stored `algorithm_version` | a row marker |
| `substrate/compat/activity_backfill.py` (rebuild's `_run_activity_substrate`, `rebuild_orchestrator.py:311`) | attempts and presentations with no activity rows | rebuild backfills the activity ledger for rows written before it; strategy: keep |
| `substrate/family_memory.py:23` `PROJECTION_LEGACY_FALLBACK` (`current_content`) | outcome rows without a content snapshot | rebuild's family memory replays them against current content |
| `substrate/activities.py:279` `resolve_legacy_item` | an item with no family/card/surface | rebuild and the activity backfill resolve it idempotently |
| `diagnosis/error_taxonomy_map.map_legacy_error_type` (called at C3, C5-C7) | an error type stored under a legacy name | maps stored legacy names to mechanisms on read |
| `attempts/attempts.py:1437`, `:1519`, `:1525`, `:1534`, `:1568` (D4's list) | stored grading source, blind record, hold, epochs | replay re-enters the live lane |
| `fixtures/mvp017_route_check_replay` | rows written at `mvp-0.17` | pins the regrade and hold readers; its tests must pass |

### (f) The paths the strategy names for deletion

- **The pre-canonical projection path** (the map's LEGACY-ONLY row: `canonical_projection.py:311` and `db/repositories.py:26940` in its numbering): S1-S6 plus S19's gate half. Reached only through the vault's tag (S1, S4) or a writer's stamp (S19); `load_canonical_observation_ledger` (the v1 ledger) has other readers (`diagnosis/probe_targeting.py:374`, `learner/residual_diagnostics.py:48`, and it is the base of the v2 ledger), so only the projection's use of it goes. The map's two reaches ("the head fixture at mvp-0.6 uses it; a shadow override can reach it") are closed: the shadow override by D1, and the head fixture opens only under the tests' allowance.
- **`substrate/compat/`** holds `activity_backfill.py` (rebuild imports it, `rebuild_orchestrator.py:311`) and a README: not unused, kept.
- **The `facet_uncertainty` and `evidence_facet_recall_state` writers.** `evidence_facet_recall_state`'s writers: the attempt step's persistence when `write_legacy_facet_state` (C1, only on a legacy vault), `replace_attempt_derived_outcome` / `record_attempt_outcome` (the same rows, passed by C1), and `merge_facet_recall_aliases` (S14, doctor's `--fix-state` on a legacy vault). Each is reached only through C1 or S14. `facet_uncertainty`'s writers: C1 (legacy) and the facet-belief successor's (`write_facet_uncertainty`, the successor's switch, varying): the successor's stays, the legacy one goes. The two tables stay (J1's list): rows already in them are read by the class (c) readers above.

## 2. What went, by area

This landing takes the projection with L1 and L2, then the rest of the substrate, the rebuild orchestrator and doctor. **L3 (`is_canonical_state_vault` and its 32 calls) and S19 (the repository guard's gate half, which only becomes removable once L3's legacy writer is gone) are handed back for the next landing** (§7).

| site | outcome | commit |
|---|---|---|
| S1-S7, L1, L2 | gate and dead branch gone; the projection always reads the v2 ledger with its effective-observation references, loads the coarse outcome schema, discounts mass through `p0_effective_evidence_mass`, applies the adjudicated-outcome override, reads each attempt's current epoch and skips the contract-unrecorded ones, and runs the residual pass; the timeline always attaches its P0 mass map and orders epochs through `grading_epochs.ordered_epochs`, each epoch read whole (its first-seen-stamp ordering and the cross-epoch accumulation went with L2's branch) | `1864ac12e7` |
| S8, S9, S11 | gate and dead branch gone | `5d1b639b54` |
| S10 | `purpose_adapter_path_live` deleted; `hot_path_applies_practice_review` loses `algorithm_version`; the module constant `P1_PURPOSE_ADAPTERS_ENABLED` (its only other input, `False`, set by nothing) and its `_reg_const` entry go | `5d1b639b54` |
| S12 | tag half gone; `recurrence_active` is the switch `recurrence.enabled` alone | `5d1b639b54` |
| S14-S18 | gate and dead branch gone; `_mvp07_facet_severity` (constant `"error"`) and `_merge_mvp06_facet_recall_aliases` deleted, with `Repository.merge_facet_recall_aliases` and `_merged_facet_recall_state` (their only caller was S14) | `faf9b17909` |
| S13 | kept (c) | — |
| S19, L3 | handed back | — |

**Deletion proof** (strategy §2.1) for what went beyond the gates: `purpose_adapter_path_live`, `P1_PURPOSE_ADAPTERS_ENABLED`, `_mvp07_facet_severity`, `_merge_mvp06_facet_recall_aliases`, `merge_facet_recall_aliases`, `_merged_facet_recall_state` were searched over `src/`, `scripts/`, `tests/` and `apps/` as names and strings: no function-local or `importlib` import, no `METHOD_REGISTRY`, Typer or `MODULE_INVENTORY` entry, no frontend caller; the one string dispatch was `P1_PURPOSE_ADAPTERS_ENABLED`'s `_reg_const` row in `params/parameter_registry.py`, removed with it (no identity pin reads the registry). The function-local edge `administration_adapters -> assessment_contracts` left `tests/architecture_function_local_domain_imports.txt` (the inventory test requires a stale edge to go). No version set in `algorithm_versions.py` was removed (D6's).

## 3. Tests

The rules as D4's (§3 there).

**One self-grade no longer certifies.** The largest class of failures (54 of 57 in the first sweep) is one mechanism: below `mvp-0.8` the projection weighed an answer by its attempt type alone, so a test vault pinned at `mvp-0.7` (`km3_projections_helpers`, `goal_certification_any_of_helpers`, `certification_cold_probe_helpers`, `graph_editor_reads_helpers`, `km2_write_path_helpers`' vault, and others) certified a cell with one full-marks self-grade. On every vault that opens, the mass is discounted by the grade's certainty bound, about 0.70 for a cold-calibrated self-grade, below `DEMONSTRATED_CREDIT = 1.0`; the same tests on the base code with their vault moved to the head fail the same way (checked for `test_km3_projections` and `test_sidecar_knowledge_model`). These tests' subject is what the readers do with banked credit, not how credit is banked, so they reach the same banked credit through a live path: `tests/certain_grade_helpers.make_grade_certain` appends the owner's point adjudication of the grade's own leading class (bounded trust 1, certainty 1; the direction agrees with the ledger, so no evidence revision is written) and re-projects. With certainty 1 the mass is the attempt type's, exactly what the old path banked. Applied in: `certification_cold_probe_helpers._certify`, `km3_projections_helpers._attempt`, `graph_editor_reads_helpers._blueprint_ctx`, and in `test_certification_cold_probe` (three tests that certify directly), `test_goal_certification_any_of._demonstrate`, `test_reader_recap_review._solve`, `test_reader_recap_review_r2` (one test, two attempts), `test_sidecar_knowledge_model._seed_blueprint_vault`, `test_km2_write_path::test_near_clones_globally_discounted`, `test_probe_targeting::test_integration_condition_probes_coordination_not_components`, `test_instrument_servability_journeys::test_the_certification_cold_probe_selects_an_instrument_as_its_held_out_item`, `test_sidecar_contract::test_knowledge_field_is_recipe_topological_and_uses_pooled_ready`. `km2_write_path_helpers._attempt` now returns its result. These vaults keep their tags (the re-tagging step owns those); no assertion changed. All 41 test files that import a changed helper pass.

**Every assertion changed, and why:**

| test | before | after | why |
|---|---|---|---|
| `test_unresolved_cause_gate::test_cold_calibration_still_discounts_certification_credit` | baseline credit from the same answer on an `mvp-0.7` vault | baseline from the same answer at the head with its grade point-adjudicated as `success` | the raw-grade baseline was the deleted branch; the assertion `0 < p0_credit < raw_credit` is unchanged |
| `test_receipt_exactness::test_timeline_final_credit_equals_banked_ledger_credit` | arms `mvp-0.7`, `mvp-0.8`; at `mvp-0.7` a fixture with an eligible attempt must bank credit | arms `OLDEST_SUPPORTED`, the head; a fixture with an eligible attempt whose interpretation has a positive certainty bound must bank credit | both folds take the P0 channel at every tag; the non-vacuity check now names the attempts that can bank on that path (the head fixture's attempts predate interpretations and bank zero, as the docstring already said of `mvp-0.8`) |
| `test_hot_path_eligibility_cutover::test_ineligible_observation_leaves_mvp08_scheduling_untouched` (was `..._but_legacy_writes`) | also: an `mvp-0.6` vault writes unconditionally | that arm removed | the legacy unconditional write was S10's dead branch |
| `test_administration_adapters::test_hot_path_defers_to_practice_eligibility` (was `..._gate_on_...`) | monkeypatched `P1_PURPOSE_ADAPTERS_ENABLED = True` | no patch | the constant is gone; the eligibility assertions are unchanged |
| `test_recurrence_groups::test_the_kill_switch_gates_the_projection` (was `test_the_successor_and_...`) | also: `mvp-0.10` with the switch on reads no groups | that tail removed | the tag half is gone; the switch half is unchanged |
| `test_recurrence_live::test_with_the_switch_off_there_is_no_judge_and_no_escalation`, `test_recurrence_deferral::test_with_the_switch_off_the_verdict_changes_nothing` (were `test_below_the_successor_...`) | the predecessor reached through `mvp-0.10` | through `[recurrence] enabled = false` | same assertions, the predecessor through its switch |

**Deleted (only subject a deleted branch):** `test_administration_adapters::test_hot_path_gate_default_off_is_unconditional`; `test_hot_path_eligibility_cutover::test_eligible_practice_attempt_is_byte_identical_legacy_vs_mvp08`; `test_doctor::test_doctor_fix_state_merges_registered_facet_alias_state`; `test_recall_coverage_interventions::test_facet_recall_alias_merge_sums_beta_state` (the repository method's own test); `test_km1_doctor::test_empty_registry_is_skipped_on_legacy`, `::test_unregistered_facet_is_warning_on_legacy`.

**Strict xfails, each the fail-first test of a queued fix:** `test_rebuild_orchestrator::test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear` (D-34: it compared the umbrella rebuild with the direct replay on the head fixture at `mvp-0.6`, where neither wrote the canonical rows; at every tag that opens they write them, with different stamps; the same on the base code with the fixture at the head) and the new `test_projection_timeline_agreement::test_the_timeline_drops_what_a_held_uncited_regrade_holds` (D-33).

**Added:** `tests/test_projection_timeline_agreement.py`: on a head vault, the timeline's final Demonstrated equals the projection's banked credit over a cold-calibrated self-grade (mass discounted), a grade revised by an adjudication (two epochs), and a grade built as written before contract lineage (`as_graded_before_contracts`: rows citing no contract, keyed by stamp), after a rebuild; and the strict xfail above for a regrade built as written before regrade contracts (`as_regraded_before_contracts`, D4's construction). The kept readers it reads through: the contract fallback (the uncited rows), `current_epoch` / `ordered_epochs` (revision-less rows; the revised attempt), `p0_effective_evidence_mass` (the cold self-grade), the contract-unrecorded hold (D-33's case, through replay). `fixtures/mvp017_route_check_replay` is read through the rest by its own tests (`test_mvp017_route_check_replay`, all passing) and by §4's comparison.

## 4. Proof

**P-shadow.** `/home/saturn/Documents/thinking/learnanything-ad1/fixtures-local/owner-copies-mvp058` (three vaults at `mvp-0.58`), copied with `copy_tree_with_databases` under `fixtures-local/d5/{before,after}/`; `before` upgraded to `mvp-0.59` and shadow-rebuilt by the base code (`41387e1236`, a `git archive` of `src/` and `migrations/` on `PYTHONPATH`), `after` by this branch at `faf9b17909` (the last source commit). Counts only; the copies are deleted.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| `learnloop upgrade`, both | `mvp-0.58 -> mvp-0.59` | same | same |
| shadow facet / mastery / schedule changed, both | 0 / 0 / 0 (80 / 21 / 99 unchanged) | 0 / 0 / 0 (3 / 18 / 77) | 0 / 0 / 0 (7 / 34 / 32) |
| `schedule_effects` due dates moved (items, cards), both | 0, 0 | 0, 0 | 0, 0 |
| replayed attempts | 70 | 3 | 3 |
| live database unchanged by the shadow, both | yes | yes | yes |
| the two shadow reports, marker id, `as_of` and hashes aside | equal | equal | equal |
| every table of the two upgraded copies, row by row (ULIDs, stamps and hex digests normalized) | 402 tables, 19,442 rows: none differ | 402, 10,426: none | 402, 23,877: none |

**Old rows at the floor and the head.** `fixtures/mvp017_route_check_replay` (rows written at `mvp-0.17`: route-check holds, a regrade the check kept held, an adjudication), copied, retagged to `mvp-0.58` and to `mvp-0.59`, rebuilt live twice (`learnloop rebuild-derived-state`) by the base code and by this branch: after the first and after the second rebuild, at both tags, every table of the two copies is equal row by row, ids and stamps normalized, except one `attempt_debug_payloads` row whose only differences are the ULIDs of the causal hypotheses replay mints and the diagnosis-receipt id hashed from them. The second rebuild is not a fixed point on either code (ledger D-35, pre-existing: it appends one more observation chain per attempt).

**Rebuild equivalence.** `test_rebuild_equivalence*`, `test_rebuild_orchestrator` (one test now a strict xfail, D-34), `test_mvp017_route_check_replay`, `test_receipt_exactness`, `test_projection_timeline_agreement`: pass (§5).

**Identity pins** unmoved (`tests/test_identity_pins.py` passes; nothing written with `--write`). `test_retired_config_identities`, `test_effective_defaults_golden` and `test_cli_help_snapshot` pass unchanged.

**Measures** (`scripts/refactor_measures.py` at the enforced floor, base vs tip):

| measure | base | tip |
|---|---|---|
| tag gates: constant at `mvp-0.58` / all (varying) | 75 / 83 (8) | 56 / 64 (8) |
| constant gates in this step's files | 22 (S1-S19, L1-L3) | 3 (S13 kept, S19, L3) |
| `mvp-0.N` literals: code / docstring / comment | 190 / 405 / 642 | 189 / 388 / 632 |
| functions over 200 lines | 81 | 80 (`_observation_events_by_facet` 211 to 193) |
| `project_canonical_facet_state` | 545 lines | 530 |
| `substrate/canonical_projection.py`; `substrate/rebuild_orchestrator.py` | 1,378; 816 lines | 1,345; 804 |
| raw lines; code lines (all four packages) | 615,186; 432,730 | 614,880; 432,509 |
| `Repository` methods | 921 | 920 |

## 5. Gates run

All under the empty-home wrapper in 5 GB scopes.
- **The first sweep** after the projection commit's source change: `scripts/affected_tests.py` on the two changed modules selected 1,028 files, run in 11 chunks of 100 at `-n 4` behind `flock /tmp/learnloop-fullsuite.lock`: 57 failures in 18 files, every one read (§3). Then those files, every file importing a changed test helper (41 files: 800 passed) and the new file: green.
- **Every test file** (`scripts/affected_tests.py` selects the whole suite once `db/repositories.py` changed), 1,405 files in 15 chunks of 100 at `-n 4` behind the lock, on `faf9b17909`: see the tail of this section.
- `test_identity_pins`, `test_retired_config_identities`, `test_architecture`, `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_structure_ratchets`, `test_refactor_measures`: pass.
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken.
- Vault: references regenerated once after the source commits (`8edf95aaee`, line references only); a second `generate_all.py` changed nothing; the four validators pass. `scripts/check_gate_partition.py`: 30,803 collected, landing 30,743 + arc_close 60.
- Not run (the orchestrator's): the durability lane, `--fresh-connections`, vitest, the owner lane, the arc-close lane.

## 6. Bug ledger

- **D-33** (the new agreement test): an attempt whose current epoch cites no contract and that replay holds banks nothing in the projection, while the timeline keeps its earlier epoch's credit (its zeroing correction is emitted only for facets the epoch's rubric `targets` name, and the live item's rubric names none). Pre-existing at the head (the base code fails the same construction). Possibly R1-6's shape. Strict xfail; open, due at arc D's close.
- **D-34** (a rebuild test that ran at `mvp-0.6`): the umbrella rebuild and the direct replay leave different stamps on the canonical facet rows, and one direct producer stamps the wall clock under a fixed clock. Pre-existing at the head. Strict xfail; open, due at arc D's close.
- **D-35** (the `mvp-0.17` fixture check): each live rebuild of the fixture appends another observation chain per attempt (17 rows to each of four ledgers). The same on the base code. Open, due at arc D's close.

## 7. Open items

- **Handed back for the next landing: L3 and S19.** `learner/facet_state_reader.is_canonical_state_vault` (constant `True` at the floor) and its 32 calls at this tip: `attempts/attempts.py:3296` (the legacy writer: `write_legacy_facet_state`), `:4264`, `:5289`, `attempts/grading.py:373`, `:1941`, `:1961`, `:1997` (and the wrapper `:284`), `learner/facet_state_reader.py:106`, `:363`, `:376`, `:391`, `:417`, `:463`, `:468`, `:521`, `:533`, `learner/capability_grid.py:122`, `:221`, `learner/recall_coverage.py:645`, `learner/facet_diagnostics.py:395`, `learner/facet_evidence_timeline.py:1164`, `daily_plan/headline.py:71`, `diagnosis/misconceptions.py:280`, `diagnosis/probe_instance_generation.py:244`, `:307`, `goals/goal_certification.py:114`, `:219`, `goals/goal_projection.py:709`, `scheduling/selection_rewards.py:438`, `learnloop_sidecar/handlers/facet_detail.py:267`, `handlers/knowledge_model.py:92`, `handlers/facets.py:74`. What each dead branch does is §1(d). Things the next step must read before deleting: C5/C6 build the grader's prompt (`_grading_error_taxonomy`), so a pin over a structured prompt built from an in-code `mvp-0.6` config may move; C1's removal leaves `evidence_facet_recall_state`'s only writer `Repository._upsert_facet_recall_state` (reached through `record_attempt_outcome` / `replace_attempt_derived_outcome`'s `facet_recall_states`), after which S19's gate half can go; `diagnosis/misconceptions.py`'s legacy normalization shares helpers with the compositional one; `facet_diagnostics._covered_frontier_fraction` would lose `aggregate_facet_recall`. The tests that run these branches are the ones at `mvp-0.6` (`pin_old_basic_vault`, the head fixture) and `test_today_headline`'s patch of the predicate (T4).
- **For D6:** the same sets tested directly outside this step's files: `content/proposals/patches.py:648`, `:1111`, `diagnosis/probe_robust.py:60`, the sidecar's `handlers/serializers.py:358` and `handlers/workbench.py:156` (§1(c)). The version sets this step's sites tested (`CANONICAL_STATE_VERSIONS`, `P0_PROJECTION_VERSIONS`, `REGRADE_CONTRACT_VERSIONS`, `RECURRENCE_GROUP_VERSIONS`) stay in `algorithm_versions.py`; `RECURRENCE_GROUP_VERSIONS` now has no gate. `Workflows/Build a Study Map.md` still says an apply needs `mvp-0.7` (the proposals gate, D6's).
- **For D7:** `recurrence.enabled`, whose tag half went; its predecessor tests now reach it through the switch.
- **The tests' certain grade** (`tests/certain_grade_helpers.py`): the tests that certified with one self-grade keep their old tags (the re-tagging step's); when they move to the head they keep the helper. A cold-calibrated self-grade never certifies a cell on its own at any tag that opens; that is the head's behaviour, not this step's, and is recorded here because the tests made it visible.
- **The parallel re-tagging step**: this step edited `test_certification_cold_probe`, `test_goal_certification_any_of`, `test_reader_recap_review`, `test_reader_recap_review_r2`, `test_unresolved_cause_gate`, `test_receipt_exactness`, `test_hot_path_eligibility_cutover`, `test_recurrence_*` and the shared helpers named in §3; a merge may conflict there.

## 8. Not verified

- The durability lane, `--fresh-connections`, vitest, the owner lane and the arc-close lane (orchestrator's).
- P-shadow covers the owner copies' histories, which are small (70, 3, 3 attempts) and hold no regrade written before contracts; those rows were checked on the `mvp-0.17` fixture and on rows built by D4's helpers (the new agreement test), not on a real owner history.
- Doctor's output on the owner copies before and after (doctor was not run on them; its changed checks are covered by `test_doctor`, `test_km1_doctor` and the doctor tests in the sweep).
- D-35's growth on a vault whose attempts were written at the head.
