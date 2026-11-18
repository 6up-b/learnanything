# L2c repository store split

Base `2b2c2fb155729fa8a1dcf8ceff274e6e6f2c4e95` on `refactor/l2c-stores-2`. At this HEAD, `repositories.py` has **19,673 lines and 609 direct methods**. It now has **8,574 lines and 248 direct methods**. The six new mixins inherit the 361 moved methods into the same interface.

Scratch directory, abbreviated S below

```text
/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/73b37aee-2550-41c4-88a8-8730b0f3c0c0/scratchpad/refactor-l2c
```

## Store membership and ownership

| Module | Mixin | Methods | Definition lines | Exact cut lines | File lines |
| --- | --- | ---: | ---: | ---: | ---: |
| `attempts.py` | `AttemptStoreMixin` | 87 | 2,314 | 2,451 | 2,481 |
| `grading.py` | `GradingStoreMixin` | 28 | 608 | 647 | 663 |
| `causal.py` | `CausalStoreMixin` | 76 | 2,652 | 2,771 | 2,794 |
| `probes.py` | `ProbeStoreMixin` | 78 | 1,987 | 2,124 | 2,150 |
| `learner_model.py` | `LearnerModelStoreMixin` | 55 | 1,752 | 1,831 | 1,857 |
| `remediation.py` | `RemediationStoreMixin` | 37 | 903 | 948 | 964 |
| `records.py` | Shared records and helpers | 0 | 304 | 352 | 363 |

Definition lines include decorators, top-level declarations and class assignments. Cut lines also include adjacent comments and whitespace. `assignment.json`, `move_manifest.json` and `store_members.json` list all members and exact spans.

- **Attempts** writes `assessment_contract_versions`, `attempt_debug_payloads`, `attempt_feedback_metadata`, `attempt_submission_receipts`, `attempt_surprise`, `causal_cold_outcomes`, `causal_cold_verifications`, `certification_cold_probe_outcomes`, `coldness_receipts`, `grading_clarification_responses`, `grading_clarifications`, `grading_evidence`, `learning_outcome_labels`, `measurement_contract_corrections`, `practice_attempts` and `trace_exercised_facets`.
- **Grading** writes `calibration_stream_samples`, `diagnostic_augmentation_receipts`, `discrimination_profile_matches`, `grade_adjudications`, `grade_interpretations`, `observation_events`, `observation_templates`, `outcome_schema_versions` and `raw_grade_events`. It reads `outcome_schemas`, `grader_calibration_models` and `grader_calibration_alphas`, whose pinned writers stay core.
- **Causal** writes `causal_activity_classification_events`, `causal_attribution_reports`, `causal_blind_prediction_bundles`, `causal_discriminating_observations`, `causal_hypotheses`, `causal_machine_checks`, `causal_mechanism_taxonomy_assignments`, `causal_mechanism_taxonomy_retirements`, `causal_mechanism_taxonomy_versions`, `causal_probe_candidate_events`, `causal_probe_candidates`, `causal_probe_decision_receipts`, `causal_probe_preference_events`, `causal_repair_class_definitions`, `causal_shadow_selection_receipts`, `contrast_pair_servings`, `diagnosis_adjudications`, `error_hunt_outcomes`, `missing_vocabulary_notes`, `probe_manipulation_audits` and `unresolved_cause_factors`.
- **Probes** writes `diagnostic_eval_cases`, `diagnostic_eval_runs`, `diagnostic_pack_cards`, `diagnostic_pack_events`, `diagnostic_pack_pins`, `diagnostic_packs`, `diagnostic_surface_generation_needs`, `hypothesis_sets`, `lo_probe_state`, `persona_realism_runs`, `probe_calibration_sessions`, `probe_episodes`, `probe_family_calibrations`, `probe_family_lifecycle_events`, `probe_family_templates`, `probe_generation_needs`, `probe_instrument_cards`, `probe_item_calibrations`, `probe_item_family_links`, `probe_observations`, `probe_presentations`, `probe_regrade_checks` and `probe_state_segments`. Records holds the shared insert for `probe_presentations`.
- **Learner model** writes `attempt_debug_payloads`, `error_events`, `hypothesis_events`, `intervention_needs`, `item_misconception_discrimination`, `learner_state_beliefs`, `misconception_candidates`, `misconception_disposition_events`, `misconception_transition_events` and `misconceptions`.
- **Remediation** writes `cold_measurement_opportunities`, `cold_measurement_opportunity_decisions`, `followup_ratings`, `followup_tasks` and `remediation_episodes`.

`store_write_tables.json` records literal SQL write targets. `store_tables.json` also includes touched tables from the fine-group map. Core transactions and existing stores retain their own access.

## Retained core

- Connection and initialization scopes `__init__`, `attach`, `_initialize`, `connection`, `in_atomic`, `atomic`, `pinned` and `find_record`. `connection` is the sole existing-base override. `ensure_outcome_schema` and `insert_calibration_model` remain core for the test fixtures. They have no exclusive private helper. The read-only `find_calibration_model_by_hash` has independent callers and moved to grading.
- Patched facade globals keep their readers core. `create_or_attach_current` is used by `__init__`. `connect` is used by `connection`, `atomic` and `pinned`. `COLLECTION_VERSION` is used by `_insert_practice_attempt` and `record_scheduler_slate`. `recurrence_key` is used by `_projected_causal_candidates`, `misconception_candidate_by_normalized`, `misconception_candidates_for_learning_object`, `update_misconception_candidate` and `causal_hypotheses_for_learning_object`.
- Current direct cross-group straddlers touching this batch stay core. They are `_link_attempt_to_scheduler_candidate`, `active_interpretation_for_observation`, `active_probe_presentation_for_session`, `calibration_duel_pairs`, `chosen_candidate_outcomes`, `consumer_pins_for_versions`, `deactivate_practice_item_serving`, `end_open_sessions_except`, `expired_cold_retry_tasks_without_outcome`, `find_record`, `gate_training_rows`, `most_recent_ended_at`, `pending_grade_reviews`, `probe_observations_for_episode`, `qualifying_probe_observation_count_for_session`, `record_deferred_regrade`, `record_learner_claim_application`, `record_scheduler_slate`, `replace_attempt_derived_outcome`, `requested_practice_item_ids`, `reset_learning_object_derived_state` and `review_session_rows`. Their fine and coarse groups, plus the straddlers outside this batch, are in `core_retained.json`.
- The two same-group straddlers in this batch moved. `open_unresolved_cause_factors` joins two causal fine groups. `surfaced_belief_withdrawals` joins learner beliefs and misconceptions. `synthesis_run_introducing_entity` is a same-group straddler for the later proposals batch. `clear_derived_projection_tables` accepts a caller-selected table set and stays core.
- Three methods are absent from the older map and stay core. They are `rebuild_stamp_snapshot`, `keep_unchanged_rebuild_stamps` and `grade_head_review`.

## Helpers and row classes

`row_serialization.py` stays the canonical home of `_json` and `_loads`. Each new store uses those providers as needed. `_row_opt` stays with its sole misconception decoder. Grading owns `_decode_diagnostic_augmentation_receipt` because it writes that table. Learner model imports the decoder for its bulk reader. This is the only import between the six new mixins.

The neutral `records.py` includes the shared row types below, `_UNSET`, `_projection_id`, the probe-presentation insert, and the decoders for attempts, causal hypotheses, errors, follow-up tasks, hypothesis sets, intervention needs, learning outcome labels, misconception candidates, observation events/templates, scheduler slates, surprise and probe states/presentations/observations. Their core and store consumers are listed by name in `helper_users.json`. All 65 relocated top-level declarations and their individual users are in that file. Records imports the standard library and `row_serialization`. Its shared types preserve one class object for both core and stores and avoid changing dozens of callers. Its shared probe-presentation writer preserves the caller's transaction.

| Destination | Row classes and counts of importing files outside the facade |
| --- | --- |
| `records.py` | `PracticeItemState` (10), `MasteryState` (58), `ItemParameterState` (3), `ProbePresentationRecord` (2), `ProbeStateRecord` (1), `ProbeObservationRecord` (0) |
| `attempts.py` | `GradingEvidenceRecord` (3) |
| `learner_model.py` | `ActiveErrorEvent` (6), `MisconceptionRecord` (6), `ItemMisconceptionDiscrimination` (5) |
| `probes.py` | `ProbeEpisodeRecord` (6), `ProbeCalibrationSessionRecord` (2), `ProbeStateSegmentRecord` (0), `ProbeFamilyTemplateRecord` (0), `ProbeInstrumentCardRecord` (0), `ProbeItemFamilyLinkRecord` (0), `ProbeGenerationNeedRecord` (0) |

The facade binds `PracticeItemState`, `MasteryState`, `ItemParameterState` and `ProbePresentationRecord` for its own code, so their existing imports still work. `record_annotations.log` confirms the runtime type hints resolve to those same classes. The facade uses the other two shared probe types through the moved decoders. `ProbeStateRecord` has one repointed importer. Feature-only definitions have one home. The import-only changes cover **20 src files, 5 test files, 0 scripts and 0 vault scripts**. They include the external user of `OBSERVATION_CHANNEL_BLIND_PROBE`. `updated_importers.json` gives the exact paths, and `importer_change_proof.log` verifies the other ASTs in those files. The 12 unused imports removed from the facade have zero external import or attribute users.

## Proofs

- **P1** `static_proof.log` compares HEAD with the destinations. All **426 moved ASTs and source spans** are exact. The residue has **249 identical class members and 55 identical top-level declarations**, with exact removal and preserved ordering. Mover replay produces byte-identical facade, store and records files.
- **P2** `surface_base.json`, `surface_tip.json` and `runtime_proof.log` show identical 1,058 names, descriptor kinds, signatures and alias identities. The SHA-256 of newline-joined sorted names is `b468c21a1a4d55c852d1660225c97339a5fe5a0e45f339f90ce0d41c211c4761`. The existing thirteen bases keep their order. The new six follow in the table order. Resolution owners of every retained attribute and the `set_source_wanted_reading` alias pair are unchanged. All 25 sentinel defaults bind the same canonical `_UNSET` as their function globals. The signature comparison normalizes its per-import address.
- **P3** `global_resolution.json` has **452 reads and zero unexplained mismatches**. This includes nested code plus relocated helpers and defined class methods. Of these, 124 rows use a relocated AST-identical object and compare against its canonical destination. The rest match by identity or constant equality. `store_edges.log` checks imports at all scopes and confirms the new modules have no cycle or facade back-import.
- **P4** `module_patches.json` lists 12 sites for five globals, including `new_ulid`. `new_ulid_test_refs.txt` records `rg -n new_ulid tests`. The only counter on the facade runs `ensure_outcome_schema`, and the conftest wrapper fixes IDs only in its two minting scopes. `new_ulid_audit.json` lists all 57 moved direct callers and zero moved helper callers. The minting closure is the two pinned methods, `connection`, and the non-minting `find_calibration_model_by_hash`. Every moved ID caller imports `learnloop.ids.new_ulid` directly. `moved_method_patch_sites.json` expands 44 sites or loop groups covering 41 moved names. `patch_probes.json` proves class and instance patch/restore for all 361 names.
- **P5** Registered six SQL-owning stores and `records.py`. The vault table inventory follows all imported mixins and now also reads the imported records leaf for the shared SQL helper. Isolated execution of the inventory function preserves **254 table mappings**. Module discovery is automatic. The vault generators and generated notes were untouched by execution. Import contracts required no edits.
- **P6** `introspection_refs.txt` and `source_text_refs.txt` contain the searches across src, tests, scripts and vault scripts. No moved member is read through `__module__`, `__qualname__` or `inspect.getsource`. The grading-evidence append-only source guard now checks both the core and attempts store, covering all three existing updates. The occurrence-time allowance in `test_ro1_availability_reads.py` follows five methods to attempts and one to remediation. Core, figure, question, facet and queue source guards still point to their original owners.

## Inventories and replay

The advertised `$S/py.sh python tests/test_structure_ratchets.py --write` ran first. `inventory_proof.log` then used the same writer with precisely the seven untracked files included. The only total lowered is functions over 200 lines, **72 → 71**, because HEAD already shortened `resolve_grade`. The remaining totals are **84, 220, 46, 35, 35, 2370, 184** in golden order. Per-file stage comments move from `repositories.py` **6 → 5** to `stores/attempts.py` **0 → 1**. These are the expected post-commit values. The direct-method measure is 248 and the tracked store module count will rise from 61 to 67 after the orchestrator commits.

The copied mover still cuts spans and derives imports from the same providers. It now wraps long import lists and prunes unused imports in the new modules as well as the core. One original `dataclasses.field` import is retained in each of attempts, causal and records to keep five verbatim field-shadowing lint directives valid. There was no manual member placement. The runtime proof now checks retained dispatch owners and default sentinel bindings, walks globals of moved helpers too, and probes instance patches. For the next batch, set the wrapper paths in a new scratch directory, review `tools/README.md`, populate the new `assignment.json`, and run `bash "$S/tools/run_move.sh"` from the intended unedited worktree. Recheck map names, straddlers, patches, row ownership and imports against that batch's HEAD.

## Verification

Ran one test command at a time through `t.sh`. The first gate included the diagnosis journey golden and identity pins, with both golden files preserved. The fixed feature filename filter matched 245 files. Only `test_mobile_v3_probes.py` matched among the five predeclared exclusions. The other four were `test_ih6_workbench_open_item.py`, `test_ih4_preferences_inform_router.py`, `test_mobile_rpc.py` and `test_mobile_v4_reader.py`.

| Command | Result |
| --- | --- |
| `$S/t.sh tests/test_structure_ratchets.py tests/test_architecture.py tests/test_test_layout.py tests/test_identity_pins.py tests/test_registry_audit.py tests/test_repository_scopes.py tests/test_outcome_schema_ids.py tests/test_diagnosis_journey_golden.py -q -n 3` | 415 passed in 45.48 s |
| Same gate after the final import cleanup and inventory checks | 415 passed in 45.27 s |
| First feature chunk, 60 files with `-n 3` | Interrupted after two FastMCP cases stalled. Exit 130. |
| Feature chunk 1 retry, 60 files with `-n 2` and two exact node deselections | 730 passed, 2 expected failures, 2 socket failures in 70.13 s |
| Feature chunk 2, 60 files with `-n 3` | 817 passed in 194.17 s |
| Feature chunk 3, 60 files with `-n 3` | 600 passed, 2 skipped, 5 warnings in 40.49 s |
| Feature chunk 4, 60 files with `-n 3` | 520 passed, 2 expected failures, 4 socket setup errors in 58.07 s |
| Feature chunk 5, 4 files with `-n 3` | 115 passed in 10.42 s |
| `$S/t.sh tests/test_p0_projection_cutover.py tests/test_ro1_availability_reads.py -q -m "not arc_close" -n 3` | 32 passed in 11.15 s |
| `$S/t.sh -o "pythonpath=$S" -p baseline_overlay <two FastMCP node IDs> -vv -n 2 -o faulthandler_timeout=25` with a 62 s deadline | Both stalled in `_chat_context` against HEAD. Exit 124. |
| `$S/py.sh ruff check` | Passed |
| `$S/py.sh lint-imports --no-cache` | 1,284 modules, 14,366 dependencies, 42 kept and zero broken |

The five completed feature chunks used `-q -m "not arc_close"`, explicit paths in `feature_chunk_1.txt` through `feature_chunk_5.txt`, and the 45-second faulthandler. They total **2,782 passed, 4 expected failures and 2 skipped**. `sandbox_failed_ids.txt` lists the eight unverified cases, including all six local-socket cases that failed with `Operation not permitted`. The two FastMCP cases call `anyio.run` from `_chat_context` in `test_diagnosis_input_provenance_landing.py`. They stalled at the same stack frame with the HEAD versions of the changed production modules loaded from scratch. Logs are `feature_chunk_1_initial.log`, `baseline_hang_tests.log` and the per-chunk logs. The separate bubblewrap probe also returned `Operation not permitted` on its loopback socket. There were no bubblewrap-dependent failures among the selected cases.

The full landing gate, the five predeclared hanging files, and the eight cases above remain unverified here. No production bug was identified and the ledger has no new entry. `.pytest_tmp` is empty and `git diff --check` passes. Detailed added, deleted and final line counts by path are in `file_changes.tsv` in S.
