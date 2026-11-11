# Refactor C1: dead modules with no registry tie

Arc C's first step ("delete what's proven dead"), `docs/specs/refactor_strategy_v3.md` §2.5. Branch
`refactor/c1-dead-modules`, based on main `88607cb3fe` (arcs A and B closed, T1 landed). C3 and C4 run in parallel
from the same base, so nothing in `apps/`, the sidecar handlers, `ai/providers/` or `codex_lockdown` is touched here.

## Step 0: the evidence at `88607cb3fe`

Written before any deletion.

### Method

Two scripts, both in `docs/reviews/artifacts/refactor-c1/`, run from the worktree root:

- **`c1_scan.py`** counts every identifier-shaped token in every text file under `src/` (all four packages:
  `learnloop`, `learnloop_sidecar`, `learnloop_mobile`, `learnloop_mcp`), `tests/`, `scripts/`, the vault's
  `_scripts/`, `apps/` (the Tauri app's TS, TSX and Rust, the phone's JS) and `pyproject.toml`: code, strings and
  comments alike. So a name in a `METHOD_REGISTRY` string, a Typer command name, a `MODULE_INVENTORY` path, a
  `_reg_const` key, an `importlib` target, a TS `invoke` string or an `__all__` entry all count as a reference. It
  over-approximates reach (any same-named definition, or a mention in a comment, keeps a name alive), which is the
  safe direction. A candidate is a definition whose name occurs once in `src` (its own `def`) and nowhere else.
- **`c1_closure.py`** builds the module import graph over `src/`: module-level and function-local imports,
  `TYPE_CHECKING` blocks included, plus an edge for every string constant naming a module (dotted, short, or as the
  `src/learnloop/...py` path `MODULE_INVENTORY` uses). It walks from two root sets: every entry point (all of
  `learnloop_sidecar`, `learnloop_mobile`, `learnloop_mcp`, `learnloop.cli`, `learnloop.tui`) and the replay,
  rebuild and upgrade roots (`substrate.rebuild_orchestrator`, `substrate.shadow_rebuild`,
  `substrate.canonical_projection`, `attempts.attempts`, `daily_plan.engine`, `ops.doctor`, `db.migrate`).

Dynamic dispatch by a computed name was searched separately: every `getattr` whose name isn't a literal (171 sites in
`src`), `globals()`, `__import__`, `import_module` and `importlib` (72 lines). The computed names are spend caps
(`f"max_{name}"`), report fields, and the registry's own module table; the `__getattr__` forwarders
(`adaptive_difficulty/claims.py:102`, `hints/map_builder.py:654`, `handlers/daily_plan.py:322`) forward a name a caller
spells out, and `source_refs._repo_call` takes a literal method name. None builds a name that the scan would miss.
`migrations/`, `fixtures/`, `integrations/`, `deploy/`, `samples/`, `README.md` and the vault's hand-written notes
name none of the candidates.

### The closure

1,300 modules, 15,869 edges. The entry points reach 1,292 modules; the replay, rebuild and upgrade roots reach 1,123.
The eight modules nothing reaches are the five below, `sim/ad_gates` and `sim/ad_synthetic` (kept: the library of
`test_ad23_sim`), and `figures/source_check_harness` (not on C1's list; open item).

| Module | Lines | Importers in `src` | Entry points | Replay / rebuild / upgrade | Other callers | Verdict |
|---|---:|---|---|---|---|---|
| `diagnosis/causal_migration.py` | 121 | none | no | no | `test_causal_migration.py` only | delete with its test file |
| `diagnosis/remediation_intake.py` | 34 | none | no | no | 5 tests in `test_misconception_transitions_intake.py` | delete with those 5 tests; the file's 2 transition tests stay |
| `substrate/compat/card_outcome_replay.py` | 261 | none | no | no | `test_event_sufficiency.py` (all 6 tests), part (c) of `test_p2_acceptance::test_event_replay_equivalence_after_full_walk` | delete with the file and part (c); parts (a) and (b) stay for C5 |
| `scheduling/prequential.py` | 276 | none (the word "prequential" in `adaptive_difficulty` and `field` names other code) | no | no | `test_prequential.py`; `test_shadow_components.py` builds its reports as input data; `test_architecture`'s write-path list; the vault generator's `DORMANT_MODULES` and validator | delete; `test_shadow_components` gets a two-field stand-in (promotion reads only `metrics` and `report_hash`, by `getattr`) |
| `sim/interval_width_viability.py` | 150 | none | no | no | `test_interval_width_viability.py`; three `ignore_imports` lines in `pyproject.toml` | delete with its test file and the three lines |

No frontend, phone or MCP caller: no module name, and no public name of these modules, occurs in `apps/`,
`src/learnloop_mobile` or `src/learnloop_mcp`. No old data reads through them: `card_outcome_replay` and
`interval_width_viability` write nothing; `causal_migration` appended ordinary hypothesis versions that the live
readers load; `prequential` alone wrote a table, `controller_prequential_reports` (RECEIPT), which nothing else reads
or writes and which stays in place for J1.

**`eval_command`** (`cli/app.py:4187`, 13 lines, undecorated): its docstring says "legacy callable for the `learnloop
eval` group callback", but the callback (`cli/evaluation.py:47`, `evaluate_existing`) calls `field_eval` directly. The
name occurs elsewhere only as `cli/ad.py:166`, a different, decorated function (`learnloop ad eval`). Not in
`tests/cli_surface.json`. Delete.

### The 64 leaf definitions

The map gives five examples and the count, not the list, so the list was recomputed at this tip: undecorated (or
non-command-decorated) top-level definitions in `src/learnloop` whose name occurs only at its `def`. That gives 58,
and the vault generator's `UNCALLED_DEFINITIONS` names 10 more that occur only at their `def` and in that table (the
generator hides them from the reference as "deletion candidates"). The map's five examples are all in the 58. Two
of the 68 are kept; 66 go (702 lines).

The same table names three that aren't dead or aren't leaves: `fitted_fsrs_provenance` is called by
`cli/field.py:117` (so the generator hides a live function; the entry is removed), and `load_commitment` and
`retry_outbox` are named by tests (left alone).

| Definition | Lines | src / tests / scripts / apps | Source | Verdict |
|---|---:|---|---|---|
| `ai/execution.py:45` withhold_receipt_input | 17 | 1 / 0 / 0 / 0 | leaf list | owner's list: a receipt-protection seam (`ai/execution.py`); removing it also means removing the `_withhold_input` read path, so it is not a leaf-only change |
| `attempts/attempts.py:599` AttemptServiceNotReady | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `attempts/attempts.py:5638` _evidence_coverage | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `attempts/attempts.py:5642` _hint_dampening | 3 | 1 / 0 / 0 / 0 | leaf list | delete |
| `attempts/observations.py:16` ObservationTemplatesNotReady | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `cli/runtime.py:330` _fallback_provider_for_task | 3 | 1 / 0 / 0 / 0 | leaf list | owner's list, for C4: sits among the Codex-era provider wrappers in `cli/runtime.py` that C4 is editing |
| `content/authoring/authoring_gates.py:117` chain_gates | 8 | 1 / 0 / 0 / 0 | leaf list | delete |
| `content/authoring/exercise_authoring.py:173` _anchor_statement | 6 | 1 / 0 / 0 / 0 | leaf list | delete |
| `content/pipeline/add_source.py:925` AutoBuildPaused | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `content/pipeline/jobs.py:2945` _not_implemented_handler | 7 | 1 / 0 / 0 / 0 | leaf list | delete |
| `content/pipeline/reread.py:146` has_completed_reading | 3 | 1 / 0 / 0 / 0 | leaf list | delete |
| `content/proposals/proposals.py:1300` repair_proposal_item_audit | 45 | 1 / 0 / 0 / 0 | leaf list | delete |
| `content/sources/role_authority.py:207` can_authorize_assessment | 4 | 1 / 0 / 0 / 0 | leaf list | delete |
| `content/sources/source_library.py:147` index_legacy_note | 28 | 1 / 0 / 0 / 0 | leaf list | delete |
| `content/synthesis/source_unit_inventory.py:265` _unit_heading | 7 | 1 / 0 / 0 / 0 | leaf list | delete |
| `content/synthesis/source_unit_selection.py:511` reanchor_selection_to | 56 | 1 / 0 / 0 / 0 | leaf list | delete |
| `daily_plan/view.py:374` now_payload | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `db/stores/hypothesis_marks.py:140` exposures_for_attempt | 3 | 1 / 0 / 0 / 0 | leaf list | delete |
| `db/stores/practice_index.py:101` dossier_count | 4 | 1 / 0 / 0 / 0 | leaf list | delete |
| `db/stores/router.py:399` router_outcome_rows | 3 | 1 / 0 / 0 / 0 | leaf list | delete |
| `diagnosis/diagnostic_pack.py:184` reject_pack_card | 18 | 1 / 0 / 0 / 0 | leaf list | delete |
| `diagnosis/diagnostic_pack.py:228` activate_pack | 17 | 1 / 0 / 0 / 0 | leaf list | delete |
| `diagnosis/misconceptions.py:353` _surface_family_for_attempt | 9 | 1 / 0 / 0 / 0 | leaf list | delete |
| `diagnosis/probe_families.py:72` FamilyGateRejection | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `diagnosis/probe_instance_generation.py:109` InstanceGateRejection | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `diagnosis/probe_targeting.py:712` next_cause_set_instrument | 24 | 1 / 0 / 0 / 0 | leaf list | delete |
| `diagnosis/quick_check.py:175` is_quick_check | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `diagnosis/split/history.py:1408` with_blind_overlay | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `evsi_calibration/eedi.py:332` option_index | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `evsi_calibration/metrics.py:277` quantile_names | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `experiments/contextual_embeddings/anthropic_api.py:118` extract_json | 11 | 1 / 0 / 0 / 0 | leaf list | delete |
| `experiments/contextual_embeddings/bank.py:1075` reference_dependencies | 11 | 1 / 0 / 0 / 0 | leaf list | delete |
| `experiments/contextual_embeddings/plan.py:370` embedding_documents | 9 | 1 / 0 / 0 / 0 | leaf list | delete |
| `figures/rich.py:1130` payload_digest | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `ingest/extractors/base.py:54` assign_span_semantic_hash | 4 | 1 / 0 / 0 / 0 | leaf list | delete |
| `ingest/hashing.py:179` block_type_histogram | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `instructional/reader_followups.py:1871` now_utc | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `learner/recall_coverage.py:435` event_local_severity | 37 | 1 / 0 / 0 / 0 | leaf list | delete |
| `learner/recall_coverage.py:550` build_facet_recall_updates | 31 | 1 / 0 / 0 / 0 | leaf list | delete |
| `learner/recall_coverage.py:636` build_quality_state_update | 31 | 1 / 0 / 0 / 0 | leaf list | delete |
| `router_objective/tail_data.py:922` is_finite | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `scheduling/controller_actions.py:61` is_action | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `scheduling/controller_store.py:104` upsert_constraint_manifest | 22 | 1 / 0 / 0 / 0 | leaf list | delete |
| `scheduling/controller_store.py:412` assignment_row | 6 | 1 / 0 / 0 / 0 | leaf list | delete |
| `scheduling/controller_store.py:494` outcome_windows_for_decision | 10 | 1 / 0 / 0 / 0 | leaf list | delete |
| `scheduling/controller_store.py:506` pending_outcome_windows | 7 | 1 / 0 / 0 / 0 | leaf list | delete |
| `scheduling/progression_policy.py:97` load_progression_policy | 7 | 1 / 0 / 0 / 0 | leaf list | delete |
| `source_retrieval/deliverables.py:341` _goals_path | 4 | 1 / 0 / 0 / 0 | leaf list | delete |
| `substrate/activities.py:742` append_lifecycle | 20 | 1 / 0 / 0 / 0 | leaf list | delete |
| `substrate/activities.py:980` log_affect_tap | 29 | 1 / 0 / 0 / 0 | leaf list | delete |
| `substrate/activity_patterns.py:376` review_pattern_version | 4 | 1 / 0 / 0 / 0 | leaf list | delete |
| `substrate/activity_patterns.py:382` activate_pattern_version | 4 | 1 / 0 / 0 / 0 | leaf list | delete |
| `substrate/activity_patterns.py:658` load_pattern_version | 2 | 1 / 0 / 0 / 0 | leaf list | delete |
| `substrate/card_lineage.py:103` _normalized_components | 5 | 1 / 0 / 0 / 0 | leaf list | delete |
| `substrate/surface_mint.py:476` fail_mint_job | 8 | 1 / 0 / 0 / 0 | leaf list | delete |
| `substrate/surface_pool.py:263` reject_pool_surface | 19 | 1 / 0 / 0 / 0 | leaf list | delete |
| `substrate/surface_pool.py:304` activate_pool | 11 | 1 / 0 / 0 / 0 | leaf list | delete |
| `tutor/tutor_qa.py:458` attempt_key_matches | 12 | 1 / 0 / 0 / 0 | leaf list | delete |
| `curriculum/commitment_arcs.py:308` resume_arc | 7 | 1 / 0 / 1 / 0 | `UNCALLED_DEFINITIONS` (module_generate.py) | delete |
| `curriculum/commitments.py:773` record_depth_transition_committed | 20 | 1 / 0 / 1 / 0 | `UNCALLED_DEFINITIONS` (module_generate.py) | delete |
| `curriculum/commitments.py:795` attach_family | 8 | 1 / 0 / 1 / 0 | `UNCALLED_DEFINITIONS` (module_generate.py) | delete |
| `curriculum/commitments.py:805` detach_family | 8 | 1 / 0 / 1 / 0 | `UNCALLED_DEFINITIONS` (module_generate.py) | delete |
| `curriculum/depth_edge_authoring.py:99` append_template_version | 20 | 1 / 0 / 1 / 0 | `UNCALLED_DEFINITIONS` (module_generate.py) | delete |
| `curriculum/golden_path_run.py:162` next_feasible_action | 4 | 1 / 0 / 1 / 0 | `UNCALLED_DEFINITIONS` (module_generate.py) | delete |
| `curriculum/task_blueprints.py:141` discover_exemplar_candidates | 27 | 1 / 0 / 1 / 0 | `UNCALLED_DEFINITIONS` (module_generate.py) | delete |
| `vault/hashes.py:88` concept_hash | 10 | 1 / 0 / 1 / 0 | `UNCALLED_DEFINITIONS` (module_generate.py) | delete |
| `vault/hashes.py:100` concept_edge_hash | 15 | 1 / 0 / 1 / 0 | `UNCALLED_DEFINITIONS` (module_generate.py) | delete |
| `vault/hashes.py:122` rubric_hash | 2 | 1 / 0 / 1 / 0 | `UNCALLED_DEFINITIONS` (module_generate.py) | delete |

### The 58 `Repository` methods

The map's count reproduces exactly: 58 methods of `Repository` (944 at this tip) whose name occurs only at its
`def` in `src`, 702 lines, 39 of them named by tests. None is decorated, none is named in `apps/`, the phone, the
MCP adapter or a script, and no `getattr` on a repository builds a name. 23 go (233 lines): the 19 no test names, and
four whose tests prove nothing else. The other 35 are kept because tests of live code read or seed state through
them; deleting one would mean rewriting a live test's setup or assertion for no change in production (§4: "a method
moves to its store when a step touches it").

| Method | Lines | Test files | Verdict |
|---|---:|---:|---|
| `db/repositories.py:1449` insert_practice_attempt | 4 | 17 | keep: tests of live code use it (24 test functions, e.g. `reader_cues_helpers.py::_attempt`) |
| `db/repositories.py:1846` insert_grading_evidence | 5 | 5 | keep: tests of live code use it (6 test functions, e.g. `test_assessment_contracts.py::test_observation_id_attaches_once`) |
| `db/repositories.py:2212` supersede_self_grade_rows | 19 | 2 | keep: tests of live code use it (3 test functions, e.g. `test_facet_evidence_timeline.py::test_real_regrade_renders_as_correction_step`) |
| `db/repositories.py:2302` record_deferred_regrade | 70 | 1 | keep: seeds a characterization test of the live posterior |
| `db/repositories.py:2780` active_misconception_facet_ids | 22 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:3470` discrimination_rows_for_item | 9 | 1 | delete with its one assertion in `test_repositories::test_item_misconception_discrimination_upsert_and_math`; the test's upsert and math checks stay |
| `db/repositories.py:3480` discrimination_rows_for_misconceptions | 16 | 1 | as above (two assertions) |
| `db/repositories.py:3577` insert_attempt_surprise | 4 | 1 | keep: tests of live code use it (1 test functions, e.g. `test_cli_generate_practice.py::_seed_diagnostic_surprise`) |
| `db/repositories.py:4127` cold_measurement_opportunity_decision | 16 | 3 | keep: tests of live code use it (5 test functions, e.g. `test_causal_cold_outcomes.py::test_no_independent_surface_records_unmeasurable_and_schedules_nothing`) |
| `db/repositories.py:6583` capability_residual_states | 6 | 2 | keep: tests of live code use it (4 test functions, e.g. `test_capability_residual.py::_by_capability`) |
| `db/repositories.py:6764` upsert_facet_uncertainty_state | 4 | 4 | keep: tests of live code use it (5 test functions, e.g. `test_facet_diagnostics_v03.py::test_single_facet_probe_passes_gate_even_with_multiple_open_facets`) |
| `db/repositories.py:6932` learning_outcome_labels_for_source | 11 | 1 | keep: tests of live code use it (1 test functions, e.g. `test_attempts.py::test_attempt_links_to_scheduler_slate_and_later_retention_label`) |
| `db/repositories.py:7108` parameter_registry_manifest | 7 | 1 | keep: reads the frozen manifests in an upgrade test (arc D's) |
| `db/repositories.py:7409` upsert_item_parameter_state | 4 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:7698` probe_states | 11 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:8439` retire_probe_family_template | 8 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:9384` state_beliefs | 26 | 1 | keep: tests of live code use it (2 test functions, e.g. `test_probe_belief_posterior.py::test_low_score_with_misconception_shifts_posterior_and_persists_belief`) |
| `db/repositories.py:9808` latest_scheduler_explanations_by_session | 11 | 1 | keep: tests of live code use it (3 test functions, e.g. `test_scheduler.py::test_scheduler_persists_bounded_reward_debug_and_rejected_candidates`) |
| `db/repositories.py:9971` daily_attempt_counts | 32 | 1 | delete with `test_goal_pace::test_daily_attempt_counts_is_zero_filled_and_buckets_by_day`, which tests only it |
| `db/repositories.py:12687` goal_contract_drafts_for_goal | 7 | 1 | keep: tests of live code use it (1 test functions, e.g. `test_goal_contracts.py::test_confirm_without_exemplar_raises_and_records_draft`) |
| `db/repositories.py:12931` latest_render_view_for_extraction | 8 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:13467` pending_capture_outbox | 8 | 1 | keep: tests of live code use it (2 test functions, e.g. `test_reader_capture.py::test_capture_is_one_atomic_transaction`) |
| `db/repositories.py:13984` selection_reader_authored_questions | 12 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:13997` inquiry_reader_authored_questions | 12 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:14475` relations_for_object | 8 | 1 | delete; its only test mention is the raw-reader guard's name set in `test_compare_sources_keep.py`, which drops the name |
| `db/repositories.py:14728` arcs_for_source | 7 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:14995` fetch_calibration_model | 6 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:15439` fetch_surface_by_hash | 12 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:15494` retirement_records_for_surface | 7 | 1 | keep: tests of live code use it (1 test functions, e.g. `test_grading_cli.py::test_retire_surface_from_cli_preserves_evidence_and_logs_reason`) |
| `db/repositories.py:15502` retirement_records_for_card_version | 12 | 1 | keep: tests of live code use it (1 test functions, e.g. `test_activity_substrate.py::test_retire_with_reason_records_and_preserves_evidence`) |
| `db/repositories.py:15693` interaction_events_for_attempt | 7 | 2 | keep: tests of live code use it (2 test functions, e.g. `test_activity_backfill.py::test_backfill_logs_attempt_duration_interaction_events`) |
| `db/repositories.py:16241` retire_causal_mechanism_taxonomy_version | 28 | 1 | keep: tests of live code use it (1 test functions, e.g. `test_causal_attribution_p1.py::test_retired_taxonomy_is_never_adopted_by_a_new_receipt`) |
| `db/repositories.py:17270` coldness_receipts_for_task | 13 | 1 | keep: tests of live code use it (2 test functions, e.g. `test_coldness_receipt.py::test_happy_path_snapshot_verification_and_final_receipt`) |
| `db/repositories.py:17284` coldness_receipt_for_verification | 9 | 1 | keep: tests of live code use it (1 test functions, e.g. `test_coldness_receipt.py::test_happy_path_snapshot_verification_and_final_receipt`) |
| `db/repositories.py:19970` due_reading_requests | 8 | 2 | keep: tests of live code use it (2 test functions, e.g. `test_reading_request_sweep.py::test_a_a_transient_scan_failure_is_retried_not_taken_for_nothing_due`) |
| `db/repositories.py:20541` span_reanchors_from | 7 | 1 | keep: tests of live code use it (1 test functions, e.g. `test_span_reanchor.py::test_reanchor_aliases_persist`) |
| `db/repositories.py:20604` backfill_locator_schemes | 27 | 1 | keep: `test_legacy_locators_still_resolve_after_backfill` checks old locators still resolve |
| `db/repositories.py:20717` unit_selections_for_revision | 7 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:20818` held_out_signal_marks | 10 | 2 | keep: tests of live code use it (12 test functions, e.g. `test_coordinated_migrations.py::test_f8_the_coordinator_upgrades_under_its_allowance_and_qualifies`) |
| `db/repositories.py:20872` get_unit_inventory | 6 | 1 | keep: tests of live code use it (1 test functions, e.g. `test_source_inventory.py::test_changed_page_reinventories_only_that_unit`) |
| `db/repositories.py:20928` upsert_exam_profile | 24 | 1 | keep: `test_contested_exam_profile_crud_remains_until_owner_telemetry` holds it for the owner |
| `db/repositories.py:20953` get_exam_profile | 13 | 1 | keep: as above |
| `db/repositories.py:21397` live_maintenance_notice_keys | 6 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:21781` mark_apply_intent_rolled_back | 7 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:21789` apply_intent | 6 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:23124` activity_card_authoring_for_family | 7 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:23649` surface_mint_requests_for_card_version | 20 | 1 | keep: tests of live code use it (4 test functions, e.g. `test_surface_mint.py::test_request_candidates_is_idempotent`) |
| `db/repositories.py:23898` insert_angle_inventory | 22 | 1 | keep: seeds `test_progression` (C2's) |
| `db/repositories.py:24025` lapse_episodes_for_lineage | 15 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:24235` task_blueprint_versions_for | 7 | 1 | keep: tests of live code use it (1 test functions, e.g. `test_task_blueprints.py::test_register_is_content_addressed_idempotent`) |
| `db/repositories.py:24251` task_blueprint_review_events_for | 7 | 1 | keep: tests of live code use it (2 test functions, e.g. `test_task_blueprints.py::test_register_review_activate_triad`) |
| `db/repositories.py:24591` golden_path_run_by_receipt | 6 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:24860` diagnostic_pack_by_slug | 6 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:24883` diagnostic_pack_events_for | 7 | 1 | keep: tests of live code use it (1 test functions, e.g. `test_diagnostic_pack.py::test_cards_enter_candidate_and_review_requires_admission`) |
| `db/repositories.py:25344` practice_pool_by_slug | 6 | 0 | delete (no reference outside its definition) |
| `db/repositories.py:25465` golden_path_artifacts_for | 15 | 4 | keep: read helper of golden-path tests (C5's) |
| `db/repositories.py:26167` diagnosis_adjudications_for_attempt | 15 | 1 | keep: tests of live code use it (1 test functions, e.g. `test_diagnosis_adjudication.py::test_store_is_append_only_and_a_second_opinion_supersedes`) |
| `db/repositories.py:26493` error_hunt_outcome | 7 | 1 | keep: tests of live code use it (5 test functions, e.g. `test_error_hunt_items.py::test_clean_solution_false_positive_writes_a_candidate_not_a_facet_failure`) |

### The test-only definitions

The map's 98 (2,754 lines) are 97 at this tip (2,823 lines). Rule: delete only when the tests that name it prove
nothing else. 13 go (298 lines) beyond the five modules' own; the rest are kept, mostly because a test of live code
uses them as a fixture or a driver.

| Definition | Lines | Test functions | Verdict |
|---|---:|---:|---|
| `ai/providers/codex.py:2103` make_codex_client | 12 | 1 | owner's list, for C4 (`ai/providers/codex.py`) |
| `attempts/calibration_streams.py:166` record_error_intake_sample | 24 | 1 | keep: tests of live code use it (e.g. `test_grade_resolution_pipeline.py::test_confusion_updates_only_from_denominator_bearing_sources`) |
| `attempts/grader_calibration.py:646` validate_promotion | 27 | 1 | owner's list: an unwired guard (exploratory EM may not promote to `live_calibrated`); nothing promotes today, so wire it or drop it when promotion is built |
| `cli/evsi.py:36` evsi_simulate_command | 82 | 1 | keep: a CLI command (reachable by typing it) |
| `cli/facets.py:82` facets_actions | 26 | 0 | keep: a CLI command (reachable by typing it) |
| `cli/families.py:79` families_undo | 29 | 0 | keep: a CLI command (reachable by typing it) |
| `content/authoring/practice_generation.py:1271` generate_cross_source_practice_proposal | 131 | 3 | keep: tests of live code use it (e.g. `ad23_contract_helpers.py::_run`) |
| `content/pipeline/add_source.py:1318` _source_work_active | 2 | 2 | keep: tests of live code use it (e.g. `test_reading_hardening_verify_fixes.py::test_f1_a_cancel_committing_while_a_finished_build_plans_its_follow_on_leaves_nothing_queued`) |
| `content/synthesis/source_unit_selection.py:345` default_exam_use_modes | 8 | 1 | keep: tests of live code use it (e.g. `test_source_sets.py::test_exam_use_modes_persist_at_selection`) |
| `curriculum/commitment_arcs.py:199` advance_arc | 90 | 7 | keep: tests of live code use it (e.g. `test_commitment_arcs.py::test_project_arc_rebuilds_deterministically`) |
| `curriculum/commitments.py:496` remove_target | 26 | 1 | delete with test_commitments::test_target_removal_appends_successor |
| `curriculum/golden_path_run.py:350` advance_canonical | 18 | 1 | keep: C5's module |
| `curriculum/task_blueprints.py:232` activate_blueprint_version | 25 | 1 | keep: tests of live code use it (e.g. `test_task_blueprints.py::test_register_review_activate_triad`) |
| `data_capture/reading_exposures.py:119` _clear_mapping_cache | 4 | 3 | keep: tests of live code use it (e.g. `test_data_capture_landing_review.py::test_f1_a_section_no_lo_named_until_later_reads_the_same_swept_or_not`) |
| `db/migrate.py:95` upgrade_authority | 4 | 4 | keep: tests of live code use it (e.g. `test_coordinated_migrations.py::test_f8_an_indirect_upgrade_outside_the_coordinator_raises_and_leaves_the_file_byte_identical`) |
| `db/stores/embedding_vectors.py:189` EmbeddingVectorStore | 22 | 2 | keep: tests of live code use it (e.g. `test_embedding_store.py::test_paid_vector_identity_and_float16`) |
| `db/stores/families.py:103` current_memberships | 7 | 7 | keep: tests of live code use it (e.g. `test_activity_families.py::test_undo_uses_immutable_plan_not_workflow`) |
| `db/stores/followup_serve.py:391` bindings_for_decision | 5 | 5 | keep: tests of live code use it (e.g. `test_followup_codex_review.py::test_f8_a_transport_failure_retries_under_the_decision_it_drew`) |
| `diagnosis/causal_activity_policy.py:309` resolve_conflicting_classes | 14 | 1 | delete with test_causal_activity_policy::test_resolve_conflicting_classes_is_most_contaminated_wins |
| `diagnosis/causal_attribution.py:1579` hypothesis_mechanism_projection | 25 | 1 | keep: tests of live code use it (e.g. `test_dialogue_causal_join.py::test_a_nonsense_candidate_statement_is_never_rejected`) |
| `diagnosis/causal_migration.py:42` migrate_legacy_causal_basis | 80 | 2 | delete: goes with its module |
| `diagnosis/causal_probe_coherence.py:337` parse_bundle_feature_rows | 6 | 1 | keep: tests of live code use it (e.g. `test_causal_attribution_p2.py::test_empty_feature_row_is_rejected_at_generation_and_skipped_at_read`) |
| `diagnosis/causal_probe_commissioning.py:762` sweep_probe_commissioning | 33 | 1 | delete with test_causal_probe_commissioning::test_sweep_commissions_open_factors_and_reports_each_outcome |
| `diagnosis/failure_triage.py:409` _decisive_reason | 18 | 1 | keep: tests of live code use it (e.g. `test_causal_p2_acceptance.py::test_causal_disambiguation_end_to_end_acceptance`) |
| `diagnosis/followups.py:546` evaluate_negative_surprise_followup | 38 | 3 | keep: tests of live code use it (e.g. `test_followups.py::_evaluate`) |
| `diagnosis/offline_review/report.py:226` _passes | 5 | 9 | keep: tests of live code use it (e.g. `test_followups_batch6_prefetch_decided_once.py::_passes`) |
| `diagnosis/probe_episodes.py:1664` plan_precommitted_block | 151 | 2 | keep: tests of live code use it (e.g. `test_probe_policy.py::test_precommitted_block_commits_all_before_answers`) |
| `diagnosis/probe_episodes.py:3549` abandon_episode | 19 | 2 | keep: tests of live code use it (e.g. `test_attempt_completion.py::test_resumed_completion_routes_to_the_episode_the_attempt_was_applied_under`) |
| `diagnosis/probe_lifecycle.py:263` retire_probe_instance | 26 | 1 | delete with test_probe_lifecycle::test_instance_retirement_deactivates_without_touching_history |
| `diagnosis/probe_targeting.py:764` probe_priority | 123 | 4 | keep: tests of live code use it (e.g. `test_causal_repair_mapping_p2.py::test_authored_divergent_repairs_fill_repair_class_id_end_to_end`) |
| `diagnosis/probes.py:40` parse_misconception_label | 14 | 4 | delete with all of test_misconception_label.py (4 tests) |
| `diagnosis/probes.py:267` enter_probe | 45 | 22 | keep: tests of live code use it (e.g. `test_irt_end_to_end.py::test_decisive_hard_correct_concentrates_posterior_more_than_trivial`) |
| `diagnosis/probes.py:920` probe_eig_component | 16 | 2 | delete with 2 tests of test_probe_eig.py |
| `diagnosis/probes.py:1331` current_hypothesis_set | 23 | 2 | keep: tests of live code use it (e.g. `test_probe_belief_posterior.py::test_probe_posterior_none_when_not_probing`) |
| `diagnosis/remediation_intake.py:13` classify_intake | 22 | 5 | delete: goes with its module |
| `experiments/contextual_embeddings/callers.py:580` FakeRoleCaller | 28 | 22 | keep: `experiments/` is C7's (owner decision 7) |
| `experiments/contextual_embeddings/credentials.py:34` load_env_file | 11 | 3 | keep: `experiments/` is C7's (owner decision 7) |
| `field/predictors.py:513` validate_active_predictor | 5 | 5 | keep: tests of live code use it (e.g. `test_answer_signal_arms.py::test_signal_arms_are_registered_offline_and_can_never_be_active`) |
| `field/signals.py:612` confusion_blocks_fast_track | 13 | 6 | keep: tests of live code use it (e.g. `test_eval_harness.py::test_report2_shares_the_confusion_blocking_predicate`) |
| `followup_serve/gates.py:46` effective_auto_generate_on_entry | 9 | 4 | keep: tests of live code use it (e.g. `test_followup_successor.py::test_new_vaults_get_true_effectively_and_older_templates_stay_as_they_were`) |
| `learner/capability_mapping.py:321` group_proliferation_flag | 18 | 1 | delete with test_km2_canonical::test_group_proliferation_flag |
| `learner/facet_evidence_timeline.py:1016` _observation_events | 14 | 2 | keep: tests of live code use it (e.g. `test_receipt_derivation.py::test_per_observation_itemization_sums_to_banked_credit`) |
| `learner/familiarity.py:133` record_soft_features | 15 | 8 | keep: tests of live code use it (e.g. `test_familiarity.py::test_tight_kinship_single_linkage_caps_independent_groups`) |
| `ops/settings_store.py:130` remove_config_paths | 48 | 1 | delete with test_settings_store::test_remove_config_paths_removes_retired_table_and_is_idempotent |
| `params/sensitivity_certificates.py:372` classify_inert_parameters | 23 | 1 | delete with test_sensitivity_certificates::test_inert_classification_is_class_asymmetric |
| `placement/signals.py:97` taught_first_learning_objects | 11 | 2 | keep: tests of live code use it (e.g. `test_learner_text_gaps_composition.py::test_the_gap_signal_changes_serving_only_at_mvp016_with_its_switch`) |
| `reader/annotations.py:545` reanchor_annotations_for_source | 32 | 2 | keep: tests of live code use it (e.g. `test_annotations.py::test_review_volume_budget_parks_over_budget`) |
| `reader/reader_authoring.py:415` mint_ai_sibling | 40 | 2 | keep: tests of live code use it (e.g. `test_p3_journeys.py::test_journey7_tutor_exchange_to_durable`) |
| `reader/reader_authoring.py:498` record_coach_response | 27 | 1 | keep: tests of live code use it (e.g. `test_reader_authoring.py::test_coach_response_is_corpus_only_salience`) |
| `reader/reader_dialogue.py:1431` StubReaderClient | 37 | 44 | keep: tests of live code use it (e.g. `reader_passage_check_helpers.py::_root`) |
| `scheduling/action_loss.py:379` raw_cell | 6 | 1 | keep: tests of live code use it (e.g. `test_action_loss.py::test_free_constant_entry_fails_registration`) |
| `scheduling/controller_cutover.py:425` cross_seam_exposure_probe | 41 | 2 | keep: C6's module |
| `scheduling/controller_ownership.py:102` rebuild_ownership_head | 55 | 1 | keep: C6's module |
| `scheduling/controller_store.py:311` candidates_for_decision | 10 | 2 | keep: C6's module |
| `scheduling/controller_store.py:354` shadow_predictions_for_decision | 10 | 1 | keep: C6's module |
| `scheduling/controller_store.py:420` assignments_for_experiment | 10 | 3 | keep: C6's module |
| `scheduling/controller_store.py:469` resolve_outcome_window | 15 | 3 | keep: C6's module |
| `scheduling/controller_store.py:486` outcome_window_row | 6 | 1 | keep: C6's module |
| `scheduling/kinship_feature.py:256` score_kinship | 80 | 6 | keep: C6's module |
| `scheduling/prequential.py:185` component_report | 25 | 3 | delete: goes with its module |
| `scheduling/prequential.py:212` composed_selector_report | 23 | 1 | delete: goes with its module |
| `scheduling/prequential.py:269` reports_for | 8 | 2 | delete: goes with its module |
| `scheduling/progression.py:112` next_growth_activity | 43 | 2 | keep: C2's module |
| `scheduling/progression.py:171` ensure_default_evidence_cap_policy | 8 | 1 | keep: C2's module |
| `scheduling/progression.py:199` apply_evidence_cap | 58 | 8 | keep: C2's module |
| `scheduling/progression.py:292` link_retry | 27 | 3 | keep: C2's module |
| `scheduling/progression_policy.py:86` ensure_default_progression_policy | 9 | 3 | keep: C2's module |
| `scheduling/randomization_layer.py:239` micro_randomize | 39 | 3 | keep: C6's module |
| `scheduling/randomization_layer.py:280` commitment_parallel_assign | 36 | 2 | keep: C6's module |
| `scheduling/reentry_adapter.py:214` plan_reentry | 74 | 2 | keep: C2's module |
| `scheduling/shadow_components.py:79` predict_components | 20 | 2 | keep: C6's module |
| `scheduling/shadow_components.py:101` record_shadow_predictions | 28 | 1 | keep: C6's module |
| `scheduling/shadow_components.py:146` promote_component | 58 | 3 | keep: C6's module |
| `scheduling/shadow_components.py:242` component_events | 8 | 1 | keep: C6's module |
| `scheduling/shadow_components.py:257` open_composed_selector_horizon | 26 | 3 | keep: C6's module |
| `scheduling/short_session.py:70` plan_short_session | 48 | 4 | keep: C2's module |
| `sim/grader_confusion.py:76` load_confusion | 4 | 3 | keep: tests of live code use it (e.g. `test_planted_misgrade.py::test_planted_confusion_never_silently_flips_under_wide_authority`) |
| `sim/interval_width_viability.py:112` run_interval_width_viability | 39 | 3 | delete: goes with its module |
| `sim/metrics.py:95` canonical_facet_belief_mae | 46 | 1 | keep: tests of live code use it (e.g. `test_km2_sim_gates.py::test_shared_facet_belief_mae_beats_per_lo`) |
| `substrate/activities.py:607` render_assessment_with_replacement | 53 | 2 | keep: tests of live code use it (e.g. `test_assessment_enforcement.py::test_render_with_replacement_substitutes_fresh_surface`) |
| `substrate/activities.py:956` log_attempt_duration | 22 | 2 | keep: tests of live code use it (e.g. `test_action_loss.py::test_durations_fall_back_to_logged_pooled_then_heuristic`) |
| `substrate/activities.py:1057` author_family_version | 63 | 3 | keep: tests of live code use it (e.g. `test_activity_contract_extensions.py::_author`) |
| `substrate/activities.py:1157` link_cross_purpose_families | 22 | 2 | keep: tests of live code use it (e.g. `test_activity_contract_extensions.py::test_cross_purpose_link_rejects_self_identity`) |
| `substrate/activities.py:1181` pin_card_authoring | 47 | 3 | keep: tests of live code use it (e.g. `test_activity_contract_extensions.py::test_pin_card_authoring`) |
| `substrate/activities.py:1248` inspect_angle_coverage | 13 | 1 | keep: tests of live code use it (e.g. `test_activity_contract_extensions.py::test_inspect_angle_coverage`) |
| `substrate/activity_patterns.py:195` normalize_capabilities | 10 | 1 | delete with test_activity_patterns::test_normalize_capabilities_folds_synthesis_output |
| `substrate/activity_patterns.py:388` list_compatible_patterns | 22 | 1 | delete with test_activity_patterns::test_list_compatible_patterns |
| `substrate/activity_patterns.py:412` candidate_within_bounds | 25 | 1 | owner's list: an unwired guard (an LLM may not invent a pattern's operation, capability or purpose); same call |
| `substrate/activity_patterns.py:553` ensure_builtin_patterns | 16 | 3 | keep: tests of live code use it (e.g. `test_activity_contract_extensions.py::seeded`) |
| `substrate/activity_patterns.py:575` adapt_probe_template_to_pattern | 32 | 1 | delete with test_activity_patterns::test_probe_template_adapter_is_diagnostic_only |
| `substrate/compat/card_outcome_replay.py:152` replay_card_outcome_counts | 34 | 5 | delete: goes with its module |
| `substrate/families.py:380` recover_family_operations | 4 | 3 | keep: tests of live code use it (e.g. `test_activity_families.py::test_interrupted_apply_can_abort_after_owner_edit`) |
| `substrate/surface_mint.py:144` claim_next_mint_job | 21 | 10 | keep: tests of live code use it (e.g. `test_item_fingerprints.py::test_generic_rotation_claims_never_take_pf_generation_jobs`) |
| `substrate/surface_pool.py:432` request_spare_mint | 21 | 1 | keep: tests of live code use it (e.g. `test_surface_pool.py::test_generator_outage_does_not_block_in_flight_practice`) |
| `teacher/service.py:463` _family | 2 | 13 | keep: tests of live code use it (e.g. `test_attach_to_family.py::_family`) |
| `vault/hashes.py:28` learning_object_hash | 16 | 1 | delete with the learning-object half of test_irt_difficulty::test_difficulty_source_is_excluded_from_content_hash (the practice-item half stays) |
| `vault_lock.py:98` read_lock_holder | 9 | 2 | keep: tests of live code use it (e.g. `test_source_ingestion.py::test_ingest_creates_a_new_subject_while_holding_the_vault_lock`) |
