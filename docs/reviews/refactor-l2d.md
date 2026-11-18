# L2d repository store split

Base `f08b859d9b35fb88413e1bf8555f2f7c551cf60c` on `refactor/l2d-stores-3`. The facade went from **8,574 to 3,025 lines** and from **248 to 52 direct methods**. Repository inherits all 196 moved methods. Call sites are unchanged.

Scratch directory, abbreviated S below

```text
/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/73b37aee-2550-41c4-88a8-8730b0f3c0c0/scratchpad/refactor-l2d
```

## Store membership and ownership

| Module | Mixin | Methods | Definition lines | Cut lines | File lines |
| --- | --- | ---: | ---: | ---: | ---: |
| `content.py` | `ContentStoreMixin` | 69 | 1,721 | 1,819 | 1,837 |
| `questions.py` | `QuestionStoreMixin` | 29 | 917 | 960 | 977 |
| `practice_state.py` | `PracticeStateStoreMixin` | 54 | 1,186 | 1,254 | 1,283 |
| `facet_projection.py` | `FacetProjectionStoreMixin` | 30 | 1,019 | 1,089 | 1,120 |
| `maintenance.py` | `MaintenanceStoreMixin` | 14 | 290 | 313 | 328 |
| `records.py` | Shared declarations | 0 | 112 | 135 | 363 → 498 |

Definition lines include decorators and assignments. Cut lines include adjacent comments and whitespace. `store_members.json` lists every method and `move_manifest.json` records every moved span.

- **Content** owns `agent_runs`, `apply_intents`, `change_batches`, `concept_animations`, `content_events`, `proposed_patch_item_dependencies`, `proposed_patch_items`, `proposed_patches`, `queue_state`, `rung_variant_requests`, `synthesis_generation_needs`, `synthesis_manifests`, `synthesis_runs`, `synthesis_shard_results` and `vault_epigraphs`. `synthesis_run_introducing_entity` moved with its proposals and synthesis tables.
- **Questions** owns `learner_claims`, `question_events`, `question_promotion_requests`, `question_promotions` and `reveal_events`.
- **Practice state** writes `ability_transition_events`, `decision_features`, `elicitation_events`, `fitted_parameters`, `item_parameter_state`, `learning_object_mastery`, `practice_item_quality_state`, `practice_item_state`, `scheduler_explanations`, `session_checkpoints` and `sessions`. It also reads attempts, labels, surprise and scheduler slate records. The scheduler slate transaction lives in the facade.
- **Facet projection** writes `capability_residual_state`, `derived_state_rebuilds`, `facet_capability_evidence`, `facet_merges`, `facet_recall_state`, `facet_uncertainty` and `subject_identifiability_watermarks`, and reads `evidence_facet_recall_state`. The existing `stores/facet_identity.py` owns the identity action and registry-save ledgers, writes `facet_merges` rows for identity actions and supplies settled merge rows. The new mixin houses the Repository merge lookup, resolution and insertion methods, including their existing delegation to that store.
- **Maintenance** owns `maintenance_notices`, `parameter_bind_events`, `parameter_registry`, `parameter_registry_manifests` and `parameter_sensitivity_certificates`.

Besides the requested groups, the older map still matches 18 direct `session_ownership` methods and three direct `failure_triage` readers. Thirteen session methods moved to practice state. They are `create_session`, `fetch_session`, `most_recent_open_session`, `latest_session_minutes`, `session_day_streak`, `end_session`, `session_learner_answers`, `update_session_checkpoint`, `fetch_session_checkpoint`, `open_session_checkpoints_except`, `clear_session_checkpoint`, `clear_practice_checkpoint_for_item` and `acknowledge_practice_checkpoint`. The session learner answers are the per-session elicitation budget input. The existing ownership mixin handles cross-device ownership and handoffs. Five session/attempt queries and all three triage readers remain for the reasons below. `repository_core` is the facade group. Three direct method names are absent from the map and remain in the facade.

## Helpers, row classes and imports

`row_serialization.py` still provides the canonical `_json` and `_loads`. This batch added 12 declarations to the existing neutral `records.py`. `_ProjectionTable` and the three `_FACET_RECALL_PROJECTION`, `_FACET_CAPABILITY_PROJECTION` and `_CAPABILITY_RESIDUAL_PROJECTION` descriptors are shared by facet writers and the facade's rebuild stamp metadata. `FacetUncertaintyState` and `_facet_uncertainty_state` serve the facet store and `find_record`. The scheduler and practice-state readers share `_decode_elicitation_event`, `_decode_decision_features`, `_decode_scheduler_explanation` and `_decode_scheduler_slate_candidate` with `find_record`. Content readers share `_decode_proposal_batch` and `_decode_proposal_item` with it.

The other declarations live with their consumers. `helper_users.json` gives each relocated declaration's individual users.

| Destination | Store-local declarations |
| --- | --- |
| Content | `_proposal_item_identity`, `_non_negative_tokens`, `_decode_synthesis_manifest`, `_decode_synthesis_run`, `_decode_apply_intent`, `_content_event_has_source_grounding` and class member `_CONCEPT_ANIMATION_FIELDS` |
| Questions | `_decode_question_event`, `_decode_question_promotion`, `_decode_question_promotion_request` |
| Practice state | `PracticeItemQualityState`, `_practice_item_state`, `_mastery_state`, `_practice_item_quality_state`, `_decode_ability_transition_event`, `_decode_fitted_parameters`, `_decode_item_parameter_state` |
| Facet projection | `_ProjectionChanges`, `_projection_changes`, `_apply_projection_changes`, `_write_projection_on_change`, `FacetRecallState`, `CanonicalFacetRecallState`, `FacetCapabilityEvidence`, `_facet_recall_state`, `_canonical_facet_recall_state`, `_facet_capability_evidence`, `_capability_residual_row`, `_resolve_merge`, `_reaches`, `_decode_derived_state_rebuild` |
| Maintenance | `_decode_maintenance_notice` |

There were five importing files for `FacetRecallState`, one for `CanonicalFacetRecallState`, four for `FacetUncertaintyState`, three for `PracticeItemQualityState` and zero for `FacetCapabilityEvidence`. The repoints are import-only across **seven src files**, with zero tests, scripts or vault scripts affected by class relocation. `updated_importers.json` lists the paths. The discarded facade imports had zero outside users. The new stores use existing providers, including the records leaf, and have no imports of one another or back-imports to the facade.

## Proofs and inventories

- **P1.** `static_proof.log` proves **240 moved ASTs and spans** identical to HEAD, including 196 methods, one class constant and 43 top-level declarations. The facade retains 52 identical class members and 12 identical top-level declarations. The explicit facade docstring, imports and base additions account for the rest of its diff. The first 363 lines of `records.py` are byte-identical. `mover_replay.log` reproduces the facade, five stores and extended leaf byte for byte.
- **P2.** The real pre-edit `surface_base.json` and `surface_tip.json` agree on 1,058 names, descriptor kinds, signatures and alias identities. SHA-256 of newline-joined sorted names is `b468c21a1a4d55c852d1660225c97339a5fe5a0e45f339f90ce0d41c211c4761`. All 19 prior bases keep their order and the five new ones follow in the table order. Retained dispatch owners are unchanged. The `set_source_wanted_reading` alias still holds the same function as `record_reading_request`. All 25 sentinel defaults bind the canonical records `_UNSET`. Runtime type-hint checks verified the moved and shared return types.
- **P3.** `global_resolution.json` covers **240 global reads**, including nested bodies and relocated helpers, with **zero unexplained mismatches**. For 77 reads of relocated declarations, the comparison verifies the canonical destination object and P1 verifies its definition. The other reads match by identity or constant equality.
- **P4.** `module_patches.json` lists 12 sites for `connect`, `COLLECTION_VERSION`, `create_or_attach_current`, `recurrence_key` and `new_ulid`. The first four have only core readers. The conftest `new_ulid` wrapper returns fixed IDs in the two pinned minting scopes and otherwise delegates. The facade call counter is scoped to `ensure_outcome_schema`, as reviewed in `new_ulid_test_refs.txt`. `new_ulid_audit.json` lists all 25 moved direct callers and zero moved helpers that mint. The closure of the fixed-ID methods is `ensure_outcome_schema`, `insert_calibration_model`, `connection` and the read-only `find_calibration_model_by_hash`. The 25 moved callers import `learnloop.ids.new_ulid`. `moved_method_patch_sites.json` lists 59 sites or loop groups covering 25 distinct moved names. Class and instance patch probes replaced and restored all 196 moved methods.
- **P5.** Registered the five SQL owners. The frozen import edge for `TokenUsage` now names `stores.content → learnloop.ai.usage`. The other import contracts needed no edits. The vault's module inventory already discovers the files and its table inventory follows all inherited mixins and the records leaf. Isolated execution of the inventory function preserved all **254 table mappings**. Vault generators and generated notes were left out of execution.
- **P6.** `source_and_introspection_refs.txt`, `introspection_and_paths.txt` and `qualified_refs.txt` cover src, tests, scripts and vault scripts. The adaptive-difficulty profiler uses module globals and compiled qualnames for its read inventory. Its exact approvals for `mastery_states` and `item_parameter_states` now name the practice-state mixin. The same test had a stale calibration-reader location at HEAD and now names the grading mixin. See L2-2 in the bug ledger. No other consumer uses a moved member's module, qualname or retrieved source. The RO0 question writer guard now names `stores/questions.py`. The facet uncertainty source guard now names the facet projection store and still includes the facade's cross-feature table reset. Migration creation, queue, grading evidence and session report source guards retain their existing coverage.

The advertised structure writer ran through `py.sh`. `inventory_proof.log` then used the same writer with the exact untracked destinations included. All totals stay **84, 220, 46, 35, 35, 71, 2370, 184** in golden order. Stage comments move from the facade **5 → 2** to content **0 → 1** and questions **0 → 2**. The post-commit measures should count 52 direct Repository methods and 72 tracked store Python files including `__init__.py`, up from 67. The orchestrator can verify the tracked inventory after commit.

For an unedited worktree at the base, run `bash "$S/tools/run_move.sh"` with the reviewed `assignment.json`. The copied mover gained opt-in append-only relocation to existing neutral leaves and addition of a facade module docstring. The proof now checks the original leaf prefix and replays from the HEAD version of that leaf. The sentinel proof uses its actual base provider even when the facade import is pruned. To replay this batch without changing the worktree, run `"$S/py.sh" python "$S/tools/replay_mover.py"`. The batch required no manual placement.

## Verification

All tests used `t.sh` with explicit paths, one command at a time. The fixed filename selection matched 145 files in three chunks. None matched the five predeclared exclusions, which were `test_mobile_v3_probes.py`, `test_ih6_workbench_open_item.py`, `test_ih4_preferences_inform_router.py`, `test_mobile_rpc.py` and `test_mobile_v4_reader.py`.

| Command | Result |
| --- | --- |
| `$S/t.sh tests/test_structure_ratchets.py tests/test_architecture.py tests/test_test_layout.py tests/test_identity_pins.py tests/test_registry_audit.py tests/test_repository_scopes.py tests/test_outcome_schema_ids.py tests/test_diagnosis_journey_golden.py -q -n 3` | 415 passed initially and on the final rerun |
| `bash "$S/select_tests.sh" 1 3`, initial | 718 passed, 1 skipped, 2 failures including the facet source guard corrected above |
| `bash "$S/select_tests.sh" 1 3`, final | 719 passed, 1 skipped, 1 socket failure |
| `bash "$S/select_tests.sh" 2 3` | 537 passed, 3 skipped, 4 expected failures |
| `bash "$S/select_tests.sh" 3 3` | 254 passed |
| `$S/t.sh tests/test_ro0_codex_verify.py tests/test_ro1_availability_reads.py tests/test_session_ownership.py tests/test_attempt_write_order.py tests/test_field_cli.py tests/test_triage_routes.py -q -m 'not arc_close' -n 3 -o faulthandler_timeout=45` | 99 passed |
| `$S/t.sh tests/test_ad_guard_reachable_reads.py -q -m 'not arc_close' -n 3 -o faulthandler_timeout=45` | Initially 4 passed and 1 failed at the stale calibration-reader location. All 5 passed after the three qualified names were updated. |
| Same adaptive-difficulty failure selected by node ID with `-o "pythonpath=$S" -p l2d_baseline_overlay -q -n 2 -o faulthandler_timeout=45` | Reproduced the stale calibration-reader failure with HEAD production modules. |
| `$S/py.sh ruff check` | Passed |
| `$S/py.sh lint-imports --no-cache` | 1,289 modules, 14,422 dependencies, 42 kept and zero broken |

Feature totals are **1,510 passed, 4 skipped, 4 expected failures and one unverified socket case**. The three explicit file manifests and the individual logs are in S. Each feature chunk used `-q -m "not arc_close" -n 3 -o faulthandler_timeout=45`. The facet composition case needs a loopback HTTP server. Socket creation failed with `Operation not permitted`, and `sandbox_failed_ids.txt` contains the exact node ID. There were zero bubblewrap failures in the selected tests. The full landing gate, the five excluded files and the arc-close cases in the feature selection remain unverified. L2-2 is a test inventory correction. `git diff --check` passed and `.pytest_tmp` has no `run-*` directories. `file_changes.tsv` contains the final line counts and diffs by path.

## What is left in repositories.py

Counts in parentheses are physical definition lines including decorators. `residue.tsv` gives each declaration's start line. The module has a seven-line docstring and 78 import lines. The imports cover future annotations and stdlib (9 lines), support providers from `hint_window`, `activation_journal`, `recurrence`, `outcome_contract`, `clock`, `db.connection`, `db.migrate`, `db.row_serialization` and `ids` (9 lines), shared records (34 lines) and the mixin bases (26 lines). The `Repository` class header takes 26 lines.

### Connection scopes and minting

- Scopes and initialization. `__init__` (13), `attach` (18), `_initialize` (8), `connection` (7), `in_atomic` (6), `atomic` (43) and `pinned` (31), with module declarations `_roll_back_after` (21) and `_PinnedConnection` (76). `connection` is the sole direct override of a prior base. The constructor reads the patched `create_or_attach_current`. The three connection scopes read patched `connect`.
- Record dispatch. `find_record` (37) dispatches identifier lookups across attempts, causal, content, facet projection, grading, learner model, practice state, probes and questions.
- Fixed-ID minting. `ensure_outcome_schema` (16) and `insert_calibration_model` (77) use the facade `new_ulid` fixture seam.

### Other readers of patched module names

- `recurrence_key`. `_projected_causal_candidates` (169), `misconception_candidate_by_normalized` (38), `misconception_candidates_for_learning_object` (30), `update_misconception_candidate` (149) and `causal_hypotheses_for_learning_object` (51).
- `COLLECTION_VERSION`. `record_scheduler_slate` (181) spans practice state and probes. Its module helper `_learning_object_id_from_target_scope` (5) serves that transaction. `_insert_practice_attempt` (89) binds the attempt to a plan presentation through module helper `_bindable_plan_presentation` (25).

### Cross-feature transactions and reads

| Groups spanned | Remaining methods and definition lines |
| --- | --- |
| Activity and goals | `record_depth_transition_atomic` (130) |
| Activity, goals and task blueprints | `confirm_golden_path_atomic` (255) |
| Activity and grading | `active_interpretation_for_observation` (11), `pending_grade_reviews` (36), `grade_head_review` (27, unmapped) |
| Activity and probes | `consumer_pins_for_versions` (36) |
| Activity and reader | `capture_local_transaction` (124) |
| Attempts and content | `record_deferred_regrade` (70) |
| Attempts, content, goals and questions | `requested_practice_item_ids` (73) |
| Attempts, facet projection, learner model and practice state | `reset_learning_object_derived_state` (52) |
| Attempts, learner model and practice state | `replace_attempt_derived_outcome` (128) |
| Attempts and practice state | `calibration_duel_pairs` (26), `chosen_candidate_outcomes` (18), `most_recent_ended_at` (42), `end_open_sessions_except` (27), `session_attempt_counts` (24), `session_attempt_rows` (25), `review_session_rows` (31) |
| Attempts, practice state and probes | `_link_attempt_to_scheduler_candidate` (47) |
| Attempts and probes | `qualifying_probe_observation_count_for_session` (23), `probe_observations_for_episode` (47) |
| Attempts and questions | `record_learner_claim_application` (17) |
| Attempts and remediation | `expired_cold_retry_tasks_without_outcome` (19), `gate_training_rows` (25) |
| Goals, reader, reading requests and source documents | `delete_source_artifact` (150) |
| Practice state and probes | `active_probe_presentation_for_session` (19) |
| Practice state and remediation | `deactivate_practice_item_serving` (45) |

`BlueprintNotReviewed` (10) and `GoalAlreadyConfirmed` (12) belong to the retained golden-path transaction. The two session-window report methods in the table read the session span before querying attempts, so the same cross-feature reason applies to them as to the map's session straddlers.

### Shared and compatibility declarations

- Rebuild coordination. `clear_derived_projection_tables` (29) accepts the caller's validated subset of derived tables. The unmapped `rebuild_stamp_snapshot` (14) and `keep_unchanged_rebuild_stamps` (34) coordinate facet recall, capability evidence, residual state and subject watermarks. Their module declarations are `_RebuildStamps` (9), `_REBUILD_STAMPED_TABLES` (14), `CANONICAL_STAMPED_TABLES` (3) and `REBUILD_STAMPED_TABLES` (1).
- Row bindings. The facade defines no row classes. It uses the existing `records.py` types `MasteryState` (58 external importing files), `PracticeItemState` (10), `ItemParameterState` (3) and `ProbePresentationRecord` (2) in core methods and retains those bindings.
- Reading auto-build. `source_auto_build_state` (15) and `advance_source_auto_build_generation` (28) manage the generation used for apply and undo. The prior reading-request pilot owns the pending-request lifecycle on the same row.
- Legacy failure triage. `failure_triage_routes` (11), `failure_triage_route_for_reason` (8) and `failure_triage_events_for` (7) remain together pending the planned triage deletion. Their route and event ledgers have no matching owner in these five stores.
- Module constants. `OBSERVATION_CHANNEL_LEARNER_QUESTION` (1) is imported by causal discrimination and its test. `ITEM_WINDOW_QUESTION_CONTEXTS` (1) is the existing alias of the shared hint-window policy.
