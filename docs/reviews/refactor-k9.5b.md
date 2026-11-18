# K9.5 part 2: diagnosis journey golden and move coverage

Tests and review records only. No commit made; the orchestrator owns the landing gate.
All content is synthetic, from the existing test helpers. No model service, network,
owner vault, credential file, main checkout, or generated architecture note was read or changed.

## 1. Scope and snapshot contract

Read the strategy K9.5 and §§4.3–4.4, part 1's handoff and identity helpers,
K10.4's record and actual figure golden/normalizer, CLAUDE.md's test contract,
and the causal, sidecar, probe, robust-gate, FG1, held-grade/regrade, gap and recurrence tests.
The identity helpers deliberately stop at write arguments; these journeys use real databases.

“Diagnosis-owned” means tables written by the two moving modules or their package,
including writes delegated through repository/store APIs and post-attempt hooks. Ownership
is not the table-role enum (which classifies replay policy). To avoid missing indirect or
ambiguous ownership, `TABLES = tuple(sorted(TABLE_ROLES))`: **every registered table** is
watched, including `decision_records`, grading, workflow, exposure, judgment and model-call rows.
The complete registry inventory is below. FTS shadow tables and SQLite internals are not
separate registered tables. Empty tables are watched but omitted from the compact row diff.

Each case has two independent synthetic vaults, each with a fresh MonkeyPatch scope.
`Journey.capture` reads every registered table in rowid order through the repository's
reused connection. Setup rows are included. Subsequent checkpoints keep additions,
changes (both before and after) and removals, following K10.4's `written` mechanics.
JSON columns are decoded. `decision_state_receipts.state_z` is decompressed and its JSON
compared in full; other blobs keep their full hex bytes, never just a length.
These are checkpoint row deltas, not an SQL statement/transaction log: intermediate writes
that are overwritten or removed inside a single checkpoint are not independently captured.

The writer is opt-in (`DIAGNOSIS_JOURNEY_WRITE_GOLDEN=1`), takes a lock on the golden itself,
and reads/merges/rewrites under that lock, as the figure golden does. JSON has newlines but
no indentation to stay comfortably below the tracked-file limit. Comparison uses the same
`check_golden` helper. No existing golden or pin was rewritten.

## 2. Cases and helpers

The five statuses are `deferred_machine_checks`, `safe_common_repair_available`,
`blocked_pending_review`, `needs_disambiguation`, and `started`.

| Cases | What the journey drives; existing shared helpers |
|---|---|
| `causal_deferred_machine_checks` | Unmapped arm → status → queued backfill → factor resolved → sweep closes orphan; `causal_orchestrator_helpers._vault`, `_seed_factor` |
| `causal_safe_common_repair_available` | Two arms with one repair → repair episode and skip receipt; same helpers |
| `causal_blocked_pending_review` | Divergent repairs without instrument → blocked receipt → commissioning obligation → explicit discharge; same helpers |
| `causal_needs_disambiguation` | Reviewed active candidate → offer; `_activate_probe_candidate`, `admit_probe_instrument_card` |
| `causal_started` | Teach-now authorization starts repair; same helpers |
| `causal_decline` | Offer → Not now → no reoffer, durable preference and negative receipt; same helpers |
| `cold_pass`, `cold_fail` | Real ambiguous attempt, reviewed candidate, accept/pin, matched feature, factor resolution, prescribed/taken repair, fresh cold retry two days later; `causal_p2_acceptance_helpers._acceptance_vault`, `_divergent_failure`, `_mint_reviewed_candidate`; real attempt/remediation/followup APIs |
| `fg1_ask_now`, `fg1_wait` | Real miss/post-attempt workflow, fixed fake author, direct handler open/contract, answer and release; `followup_journey_helpers._journey`, `_generate`, `_call`, `_answer`, `_forced`; `AuthorFake` through `StructuredClientFake`. Ask-now uses the real no-plan router arm; wait supplies the existing public router decision fake, then the boundary state transition. Wait exposes the answer, so its probe cannot resolve the factor |
| `value_stop`, `budget_stop` | Repeated committed/submitted probes and block settlement to the value stop or four-observation maximum; `voi_stopping_helpers._long_probe_vault`, `_answer_probe`, `_minutes`. Budget case explicitly disables VOI. Those historical helper fixtures carry their existing successor-switch settings |
| `mid_check` | Two answers in a three-answer block, deferred normalization/post-attempt work, Stop and teach settles both and releases feedback; `probe_block_end_helpers._setup`, `_submit`, `_misconception_attribution`; same construction as `test_teach_handoff_stop_settles` |
| `held_release` | Committed probe → held grade with inert observation → real adjudication release → segment closure; `probe_episodes_helpers._setup`, `held_grade_evidence_helpers._held_apply`. Public contract/peek/serving gates and item commit are called |
| `regrade` | Committed probe answer → real `regrade_attempt` through `regrade_contract_replay_helpers._regrade` / `PointsGrader`; probe dual writes and regrade audit, not just a direct summary update |
| `text_prerequisite` | Tutor names eigenvector gap → judge/drafter → created prerequisite, commitment and review-required seed; `learner_text_gaps_helpers._vault`, `_ask`, `_run`, `GapTutor`, `GapLLMFake`, `seed_proposal` |
| `recurrence_judge` | Three differently worded misses → real diagnosis queue, same-cause judge/group, third occurrence escalation; `recurrence_live_helpers._vault`, `STATEMENTS`, `StatementFake`, `FakeEmbeddingClient`, `split_live_helpers.submit`, `drain_jobs` |
| `deterministic_classification` | Automatic full-credit criterion sensor resolves the factor with validator-owned support; repeated hook is idempotent; `causal_p2_acceptance_helpers._offered_probe` plus actual self-grade and followup hook |

No requested case is omitted. This does not claim all alternative branches of these journeys
are covered; their precise gaps are listed in §5. Sidecar calls use registered handler functions
in process, not RPC sockets. FG1's wait selection is supplied, not an end-to-end mixture-policy test.
The held-release/regrade golden records the existing K9-3 limitation; it does not assert that
releasing/regrading retroactively repairs the original episode observation.

### Tables written per case

This includes fixture setup and all captured transitions, not only tables with diagnosis in their name.

- `budget_stop` (47 tables; checkpoints: setup, answer_1, answer_2, answer_3, answer_4): `ability_transition_events`, `activity_administrations`, `activity_card_versions`, `activity_cards`, `activity_exposure_events`, `activity_families`, `activity_family_versions`, `activity_observations`, `activity_surface_lifecycle_events`, `activity_surfaces`, `attempt_completion_work`, `attempt_debug_payloads`, `attempt_feedback_metadata`, `attempt_surprise`, `causal_activity_classification_events`, `decision_records`, `error_events`, `failure_triage_routes`, `grade_interpretations`, `grader_calibration_alphas`, `grader_calibration_models`, `hypothesis_recurrence_state`, `hypothesis_sets`, `learning_object_mastery`, `learning_outcome_labels`, `measurement_events`, `mobile_pairing_guard`, `outcome_schema_versions`, `outcome_schemas`, `p2_ladder_policies`, `p2_ladder_stages`, `practice_attempts`, `practice_item_quality_state`, `practice_item_state`, `probe_episodes`, `probe_family_calibrations`, `probe_family_templates`, `probe_instrument_cards`, `probe_item_calibrations`, `probe_item_family_links`, `probe_observations`, `probe_presentations`, `probe_state_segments`, `queue_state`, `raw_grade_events`, `schema_migrations`, `voi_forecasts`.
- `causal_blocked_pending_review` (10 tables; checkpoints: setup, factor_and_instrument, status, commissioning_pending, commissioning_resolved): `causal_hypotheses`, `causal_machine_checks`, `causal_probe_decision_receipts`, `failure_triage_routes`, `mobile_pairing_guard`, `p2_ladder_policies`, `p2_ladder_stages`, `queue_state`, `schema_migrations`, `unresolved_cause_factors`.
- `causal_decline` (19 tables; checkpoints: setup, factor_and_instrument, status, declined): `causal_blind_prediction_bundles`, `causal_hypotheses`, `causal_probe_candidate_events`, `causal_probe_candidates`, `causal_probe_decision_receipts`, `causal_probe_preference_events`, `failure_triage_routes`, `hypothesis_sets`, `mobile_pairing_guard`, `p2_ladder_policies`, `p2_ladder_stages`, `practice_item_state`, `probe_family_templates`, `probe_instrument_cards`, `probe_item_family_links`, `probe_manipulation_audits`, `queue_state`, `schema_migrations`, `unresolved_cause_factors`.
- `causal_deferred_machine_checks` (10 tables; checkpoints: setup, factor_and_instrument, status, backfill_pending, backfill_closed): `causal_hypotheses`, `causal_machine_checks`, `causal_probe_decision_receipts`, `failure_triage_routes`, `mobile_pairing_guard`, `p2_ladder_policies`, `p2_ladder_stages`, `queue_state`, `schema_migrations`, `unresolved_cause_factors`.
- `causal_needs_disambiguation` (18 tables; checkpoints: setup, factor_and_instrument, status): `causal_blind_prediction_bundles`, `causal_hypotheses`, `causal_probe_candidate_events`, `causal_probe_candidates`, `causal_probe_decision_receipts`, `failure_triage_routes`, `hypothesis_sets`, `mobile_pairing_guard`, `p2_ladder_policies`, `p2_ladder_stages`, `practice_item_state`, `probe_family_templates`, `probe_instrument_cards`, `probe_item_family_links`, `probe_manipulation_audits`, `queue_state`, `schema_migrations`, `unresolved_cause_factors`.
- `causal_safe_common_repair_available` (10 tables; checkpoints: setup, factor_and_instrument, status): `causal_hypotheses`, `causal_probe_decision_receipts`, `failure_triage_routes`, `mobile_pairing_guard`, `p2_ladder_policies`, `p2_ladder_stages`, `queue_state`, `remediation_episodes`, `schema_migrations`, `unresolved_cause_factors`.
- `causal_started` (20 tables; checkpoints: setup, factor_and_instrument, status): `causal_blind_prediction_bundles`, `causal_hypotheses`, `causal_probe_candidate_events`, `causal_probe_candidates`, `causal_probe_decision_receipts`, `causal_probe_preference_events`, `failure_triage_routes`, `hypothesis_sets`, `mobile_pairing_guard`, `p2_ladder_policies`, `p2_ladder_stages`, `practice_item_state`, `probe_family_templates`, `probe_instrument_cards`, `probe_item_family_links`, `probe_manipulation_audits`, `queue_state`, `remediation_episodes`, `schema_migrations`, `unresolved_cause_factors`.
- `cold_fail` (68 tables; checkpoints: setup, offered, accepted, matched_and_resolved, repair, cold_fail): `ability_transition_events`, `activity_administrations`, `activity_card_versions`, `activity_cards`, `activity_exposure_events`, `activity_families`, `activity_family_versions`, `activity_observations`, `activity_surface_lifecycle_events`, `activity_surfaces`, `assessment_contract_versions`, `attempt_completion_work`, `attempt_debug_payloads`, `attempt_feedback_metadata`, `attempt_surprise`, `causal_activity_classification_events`, `causal_blind_prediction_bundles`, `causal_cold_outcomes`, `causal_cold_verifications`, `causal_discriminating_observations`, `causal_hypotheses`, `causal_probe_candidate_events`, `causal_probe_candidates`, `causal_probe_decision_receipts`, `causal_repair_class_definitions`, `cold_measurement_opportunities`, `cold_measurement_opportunity_decisions`, `coldness_receipts`, `decision_records`, `error_events`, `facet_capability_evidence`, `facet_recall_state`, `failure_triage_routes`, `followup_tasks`, `followup_value_decisions`, `forecast_receipts`, `grade_interpretations`, `grader_calibration_alphas`, `grader_calibration_models`, `grading_evidence`, `hypothesis_recurrence_state`, `hypothesis_sets`, `learning_object_mastery`, `learning_outcome_labels`, `measurement_events`, `mobile_pairing_guard`, `outcome_schema_versions`, `outcome_schemas`, `p2_ladder_policies`, `p2_ladder_stages`, `practice_attempts`, `practice_item_quality_state`, `practice_item_state`, `probe_episodes`, `probe_family_templates`, `probe_generation_needs`, `probe_instrument_cards`, `probe_item_family_links`, `probe_manipulation_audits`, `probe_presentations`, `probe_state_segments`, `queue_state`, `raw_grade_events`, `remediation_episodes`, `schema_migrations`, `text_write_provenance`, `unresolved_cause_factors`, `voi_forecasts`.
- `cold_pass` (67 tables; checkpoints: setup, offered, accepted, matched_and_resolved, repair, cold_pass): `ability_transition_events`, `activity_administrations`, `activity_card_versions`, `activity_cards`, `activity_exposure_events`, `activity_families`, `activity_family_versions`, `activity_observations`, `activity_surface_lifecycle_events`, `activity_surfaces`, `assessment_contract_versions`, `attempt_completion_work`, `attempt_debug_payloads`, `attempt_feedback_metadata`, `attempt_surprise`, `causal_activity_classification_events`, `causal_blind_prediction_bundles`, `causal_cold_outcomes`, `causal_cold_verifications`, `causal_discriminating_observations`, `causal_hypotheses`, `causal_probe_candidate_events`, `causal_probe_candidates`, `causal_probe_decision_receipts`, `causal_repair_class_definitions`, `cold_measurement_opportunities`, `cold_measurement_opportunity_decisions`, `coldness_receipts`, `decision_records`, `error_events`, `facet_capability_evidence`, `facet_recall_state`, `failure_triage_routes`, `followup_tasks`, `forecast_receipts`, `grade_interpretations`, `grader_calibration_alphas`, `grader_calibration_models`, `grading_evidence`, `hypothesis_recurrence_state`, `hypothesis_sets`, `learning_object_mastery`, `learning_outcome_labels`, `measurement_events`, `mobile_pairing_guard`, `outcome_schema_versions`, `outcome_schemas`, `p2_ladder_policies`, `p2_ladder_stages`, `practice_attempts`, `practice_item_quality_state`, `practice_item_state`, `probe_episodes`, `probe_family_templates`, `probe_generation_needs`, `probe_instrument_cards`, `probe_item_family_links`, `probe_manipulation_audits`, `probe_presentations`, `probe_state_segments`, `queue_state`, `raw_grade_events`, `remediation_episodes`, `schema_migrations`, `text_write_provenance`, `unresolved_cause_factors`, `voi_forecasts`.
- `deterministic_classification` (57 tables; checkpoints: setup, accepted, auto_classified_and_resolved, hook_repeated): `ability_transition_events`, `activity_administrations`, `activity_card_versions`, `activity_cards`, `activity_exposure_events`, `activity_families`, `activity_family_versions`, `activity_observations`, `activity_surface_lifecycle_events`, `activity_surfaces`, `assessment_contract_versions`, `attempt_completion_work`, `attempt_debug_payloads`, `attempt_feedback_metadata`, `attempt_surprise`, `causal_blind_prediction_bundles`, `causal_discriminating_observations`, `causal_hypotheses`, `causal_probe_candidate_events`, `causal_probe_candidates`, `causal_probe_decision_receipts`, `causal_repair_class_definitions`, `decision_records`, `error_events`, `facet_capability_evidence`, `facet_recall_state`, `failure_triage_routes`, `grade_interpretations`, `grader_calibration_alphas`, `grader_calibration_models`, `grading_evidence`, `hypothesis_recurrence_state`, `hypothesis_sets`, `learning_object_mastery`, `learning_outcome_labels`, `measurement_events`, `mobile_pairing_guard`, `outcome_schema_versions`, `outcome_schemas`, `p2_ladder_policies`, `p2_ladder_stages`, `practice_attempts`, `practice_item_quality_state`, `practice_item_state`, `probe_episodes`, `probe_family_templates`, `probe_instrument_cards`, `probe_item_family_links`, `probe_manipulation_audits`, `probe_presentations`, `probe_state_segments`, `queue_state`, `raw_grade_events`, `schema_migrations`, `text_write_provenance`, `unresolved_cause_factors`, `voi_forecasts`.
- `fg1_ask_now` (65 tables; checkpoints: setup, authored_ready, opened, answered_and_released): `ability_transition_events`, `activity_administrations`, `activity_card_versions`, `activity_cards`, `activity_exposure_events`, `activity_families`, `activity_family_versions`, `activity_observations`, `activity_surface_lifecycle_events`, `activity_surfaces`, `assessment_contract_versions`, `attempt_completion_work`, `attempt_debug_payloads`, `attempt_feedback_metadata`, `attempt_surprise`, `causal_blind_prediction_bundles`, `causal_discriminating_observations`, `causal_hypotheses`, `causal_machine_checks`, `causal_probe_candidate_events`, `causal_probe_candidates`, `causal_repair_class_definitions`, `decision_records`, `derived_state_rebuilds`, `error_events`, `facet_capability_evidence`, `facet_recall_state`, `facet_uncertainty`, `failure_triage_routes`, `followup_generation_jobs`, `followup_workflow_events`, `followup_workflows`, `generated_probe_burns`, `generated_probe_items`, `grade_interpretations`, `grader_calibration_alphas`, `grader_calibration_models`, `grading_evidence`, `hypothesis_recurrence_state`, `hypothesis_sets`, `learning_object_mastery`, `learning_outcome_labels`, `measurement_events`, `mobile_pairing_guard`, `model_call_receipts`, `outcome_schema_versions`, `outcome_schemas`, `p2_ladder_policies`, `p2_ladder_stages`, `practice_attempts`, `practice_item_quality_state`, `practice_item_state`, `probe_episodes`, `probe_family_templates`, `probe_instrument_cards`, `probe_item_family_links`, `probe_manipulation_audits`, `probe_presentations`, `probe_state_segments`, `queue_state`, `raw_grade_events`, `schema_migrations`, `text_write_provenance`, `unresolved_cause_factors`, `voi_forecasts`.
- `fg1_wait` (75 tables; checkpoints: setup, authored_waiting, opened, answered_and_released): `ability_transition_events`, `activity_administrations`, `activity_card_versions`, `activity_cards`, `activity_exposure_events`, `activity_families`, `activity_family_versions`, `activity_observations`, `activity_surface_lifecycle_events`, `activity_surfaces`, `assessment_contract_versions`, `attempt_completion_work`, `attempt_debug_payloads`, `attempt_feedback_metadata`, `attempt_surprise`, `causal_blind_prediction_bundles`, `causal_discriminating_observations`, `causal_hypotheses`, `causal_machine_checks`, `causal_probe_candidate_events`, `causal_probe_candidates`, `causal_repair_class_definitions`, `commitment_events`, `commitment_target_versions`, `commitment_versions`, `commitments`, `decision_objectives`, `decision_records`, `decision_state_receipts`, `depth_envelope_versions`, `depth_policy_versions`, `derived_state_rebuilds`, `error_events`, `facet_capability_evidence`, `facet_recall_state`, `facet_uncertainty`, `failure_triage_routes`, `followup_generation_jobs`, `followup_workflow_events`, `followup_workflows`, `generated_probe_burns`, `generated_probe_items`, `grade_interpretations`, `grader_calibration_alphas`, `grader_calibration_models`, `grading_evidence`, `hypothesis_recurrence_state`, `hypothesis_sets`, `learning_object_mastery`, `learning_outcome_labels`, `measurement_events`, `mobile_pairing_guard`, `model_call_receipts`, `outcome_schema_versions`, `outcome_schemas`, `p2_ladder_policies`, `p2_ladder_stages`, `practice_attempts`, `practice_item_quality_state`, `practice_item_state`, `probe_episodes`, `probe_family_templates`, `probe_instrument_cards`, `probe_item_family_links`, `probe_manipulation_audits`, `probe_presentations`, `probe_state_segments`, `queue_state`, `raw_grade_events`, `router_decision_bindings`, `router_decisions`, `schema_migrations`, `text_write_provenance`, `unresolved_cause_factors`, `voi_forecasts`.
- `held_release` (32 tables; checkpoints: setup, presented, held, released, segment_closed): `ability_transition_events`, `assessment_contract_versions`, `attempt_completion_work`, `attempt_debug_payloads`, `attempt_feedback_metadata`, `attempt_surprise`, `blind_grade_records`, `causal_activity_classification_events`, `decision_records`, `failure_triage_routes`, `grader_calibration_alphas`, `grader_calibration_models`, `grading_evidence`, `hypothesis_sets`, `learning_object_mastery`, `mobile_pairing_guard`, `outcome_schema_versions`, `outcome_schemas`, `p2_ladder_policies`, `p2_ladder_stages`, `practice_attempts`, `practice_item_state`, `probe_episodes`, `probe_family_templates`, `probe_instrument_cards`, `probe_item_family_links`, `probe_observations`, `probe_presentations`, `probe_state_segments`, `queue_state`, `schema_migrations`, `voi_forecasts`.
- `mid_check` (52 tables; checkpoints: setup, answered_pi_svd_define_001, answered_pi_svd_define_002, stopped_and_settled): `ability_transition_events`, `activity_administrations`, `activity_card_versions`, `activity_cards`, `activity_exposure_events`, `activity_families`, `activity_family_versions`, `activity_observations`, `activity_surface_lifecycle_events`, `activity_surfaces`, `attempt_completion_work`, `attempt_debug_payloads`, `attempt_feedback_metadata`, `attempt_surprise`, `causal_activity_classification_events`, `causal_hypotheses`, `decision_records`, `error_events`, `facet_uncertainty`, `failure_triage_routes`, `grade_interpretations`, `grader_calibration_alphas`, `grader_calibration_models`, `hypothesis_recurrence_state`, `hypothesis_sets`, `learning_object_mastery`, `learning_outcome_labels`, `measurement_events`, `misconception_transition_events`, `misconceptions`, `mobile_pairing_guard`, `outcome_schema_versions`, `outcome_schemas`, `p2_ladder_policies`, `p2_ladder_stages`, `practice_attempts`, `practice_item_quality_state`, `practice_item_state`, `probe_episodes`, `probe_family_calibrations`, `probe_family_templates`, `probe_instrument_cards`, `probe_item_calibrations`, `probe_item_family_links`, `probe_observations`, `probe_presentations`, `probe_state_segments`, `queue_state`, `raw_grade_events`, `schema_migrations`, `text_write_provenance`, `voi_forecasts`.
- `recurrence_judge` (70 tables; checkpoints: setup, diagnosed_1, diagnosed_2, diagnosed_3): `ability_transition_events`, `activity_administrations`, `activity_card_versions`, `activity_cards`, `activity_exposure_events`, `activity_families`, `activity_family_versions`, `activity_observations`, `activity_surface_lifecycle_events`, `activity_surfaces`, `agent_runs`, `assessment_contract_versions`, `attempt_completion_work`, `attempt_debug_payloads`, `attempt_diagnoses`, `attempt_feedback_metadata`, `attempt_surprise`, `blind_grade_records`, `causal_hypotheses`, `causal_repair_class_definitions`, `decision_records`, `diagnosis_context_receipts`, `diagnosis_would_merge_log`, `diagnostic_augmentation_receipts`, `discrimination_profile_matches`, `embedding_vectors`, `error_events`, `facet_capability_evidence`, `facet_recall_state`, `facet_uncertainty`, `failure_triage_routes`, `followup_generation_jobs`, `followup_value_decisions`, `forecast_receipts`, `grade_interpretations`, `grader_calibration_alphas`, `grader_calibration_models`, `grading_evidence`, `hypothesis_recurrence_groups`, `hypothesis_recurrence_state`, `hypothesis_sets`, `judgment_ledger`, `judgment_work_claims`, `learner_state_beliefs`, `learner_text_gap_jobs`, `learning_object_mastery`, `learning_outcome_labels`, `measurement_events`, `misconception_transition_events`, `misconceptions`, `mobile_pairing_guard`, `model_call_receipts`, `outcome_schema_versions`, `outcome_schemas`, `p2_ladder_policies`, `p2_ladder_stages`, `post_attempt_jobs`, `practice_attempts`, `practice_item_quality_state`, `practice_item_state`, `probe_episodes`, `probe_family_templates`, `probe_generation_needs`, `probe_state_segments`, `queue_state`, `raw_grade_events`, `recurrence_escalations`, `schema_migrations`, `text_write_provenance`, `voi_forecasts`.
- `regrade` (56 tables; checkpoints: setup, presented, answered, regraded): `ability_transition_events`, `activity_administrations`, `activity_card_versions`, `activity_cards`, `activity_exposure_events`, `activity_families`, `activity_family_versions`, `activity_observations`, `activity_surface_lifecycle_events`, `activity_surfaces`, `agent_runs`, `assessment_contract_versions`, `attempt_completion_work`, `attempt_debug_payloads`, `attempt_feedback_metadata`, `attempt_surprise`, `blind_grade_records`, `causal_activity_classification_events`, `content_events`, `decision_records`, `facet_capability_evidence`, `facet_recall_state`, `facet_uncertainty`, `failure_triage_routes`, `grade_interpretations`, `grader_calibration_alphas`, `grader_calibration_models`, `grading_evidence`, `hypothesis_recurrence_state`, `hypothesis_sets`, `judgment_ledger`, `learning_object_mastery`, `measurement_events`, `mobile_pairing_guard`, `outcome_schema_versions`, `outcome_schemas`, `p2_ladder_policies`, `p2_ladder_stages`, `post_attempt_jobs`, `practice_attempts`, `practice_item_quality_state`, `practice_item_state`, `probe_episodes`, `probe_family_calibrations`, `probe_family_templates`, `probe_instrument_cards`, `probe_item_calibrations`, `probe_item_family_links`, `probe_observations`, `probe_presentations`, `probe_state_segments`, `queue_state`, `raw_grade_events`, `schema_migrations`, `text_write_provenance`, `voi_forecasts`.
- `text_prerequisite` (22 tables; checkpoints: setup, asked, prerequisite_created): `agent_runs`, `assessment_contract_versions`, `decision_features`, `failure_triage_routes`, `hypothesis_recurrence_state`, `judgment_ledger`, `judgment_work_claims`, `learner_gap_commitments`, `learner_text_gaps`, `learning_object_mastery`, `mobile_pairing_guard`, `model_call_receipts`, `p2_ladder_policies`, `p2_ladder_stages`, `practice_item_state`, `proposed_patch_items`, `proposed_patches`, `question_events`, `question_promotions`, `queue_state`, `schema_migrations`, `text_write_provenance`.
- `value_stop` (46 tables; checkpoints: setup, answer_1): `ability_transition_events`, `activity_administrations`, `activity_card_versions`, `activity_cards`, `activity_exposure_events`, `activity_families`, `activity_family_versions`, `activity_observations`, `activity_surface_lifecycle_events`, `activity_surfaces`, `attempt_completion_work`, `attempt_debug_payloads`, `attempt_feedback_metadata`, `attempt_surprise`, `causal_activity_classification_events`, `decision_records`, `error_events`, `failure_triage_routes`, `grade_interpretations`, `grader_calibration_alphas`, `grader_calibration_models`, `hypothesis_recurrence_state`, `hypothesis_sets`, `learning_object_mastery`, `measurement_events`, `mobile_pairing_guard`, `outcome_schema_versions`, `outcome_schemas`, `p2_ladder_policies`, `p2_ladder_stages`, `practice_attempts`, `practice_item_quality_state`, `practice_item_state`, `probe_episodes`, `probe_family_calibrations`, `probe_family_templates`, `probe_instrument_cards`, `probe_item_calibrations`, `probe_item_family_links`, `probe_observations`, `probe_presentations`, `probe_state_segments`, `queue_state`, `raw_grade_events`, `schema_migrations`, `voi_forecasts`.

## 3. Determinism and what remains a value

`freeze_wall` and `freeze_ids` are reused from the figure helper. Each case runs with ULID
sequences 104 and 401. `pinned_draws.push/pop` resets the router draw scope for each twin.
The additional ID-seeded draw boundaries are pinned explicitly: robust composition's seed
function (one indexed seed per distinct context, preserving the channel hash), prior-analysis
assignment, history forecast draw, delayed-check pick, and the judge's blind pair presentation
order (stable content-hash order). No production function in either moving module is patched.
The robust RNG seed patch is a new private-name patch in a nonmoving module, included in T4's
measurement; its production derivation already has part 1's value pin. These are fixed draws,
not a measurement of seed sensitivity (the existing K9-6 issue).

The normalizer first removes real wall-clock timestamps within three days of the actual clock,
measured durations (`DURATION_KEYS`, `latency_seconds`, `waited_ms`, `fit_ms`) and the temporary
vault root path. Fixed clock timestamps remain literal. It then compares the twins recursively.
Only changed identifier-shaped substrings (ULIDs, UUIDs and the observed hash lengths) may
become `<id:N>` tokens. Equal hashes/IDs remain values. The map is bijective and used everywhere,
including JSON mapping keys; a changed reference cannot alias two IDs onto one token. Rows
remain in write order. `blind_bundle_ids` and `blind_bundle_ids_json` are set-valued arrays whose
production hash sort changes with minted IDs; those two arrays alone are sorted by token after
alignment. Other list order is preserved.

Numbers must agree: scores, posterior masses, counts and seeds are never generically scrubbed.
The sole derived-size exception is a differing `decision_state_receipts.stored_bytes`: zlib's
length changes with minted IDs, while the decompressed JSON is still compared fully. Only a
size observed to differ in the twins gets `<id-compressed-bytes>`. Fixed-input hashes, seeds,
prompt versions, literal synthetic IDs and model output text stay in the golden.
A content ID that incorporates a minted ID necessarily becomes a token; part 1's fixed-input
pins cover its hash algorithm. This golden cannot independently detect every hash-algorithm
change to an ID-carrying value. The fixed-input manipulation audit mutation below is detected.

Initial development found unpinned ID-seeded draws and hash-sorted bundle order. One pre-final
FG1 setup comparison differed. A still-literal measured `fit_ms` field was then normalized;
the original differing row was not captured, so that attribution was not proved.
The final FG1 cases now drive the authored workflow rather than only seeded ready/wait states.

Golden: **3,236,789 bytes** (3.09 MiB), 18 cases × two vaults. Marked `slow` conservatively; normal serial runtime is about 7.5 seconds, monitoring 13.27 seconds.

## 4. Fail-first

Scratch `mutate_journey.py` saves the original bytes outside the worktree, asserts one replacement,
runs only the selected golden case through `t.sh`, and restores the saved bytes in `finally`.
Each failed specifically with “CASE: stages differs from the golden”, not a fixture exception.

| Scratch edit | Case | Result |
|---|---|---|
| Swap source and candidate IDs in the manipulation audit's content-identity mapping (`causal_probe_coherence.audit_manipulation_contract`) | `causal_needs_disambiguation` | 1 failed, 0.95 s |
| Write `repair_status="started"` instead of the calculated status in `_status_for_factor`'s receipt (return value unchanged) | `causal_safe_common_repair_available` | 1 failed, 0.96 s |
| Omit `_final_receipt(outcome, cold_verification_id=...)` in `record_cold_verification_from_task` | `cold_pass` | 1 failed, 1.24 s |

The three targeted case bodies/values are unchanged by the subsequent FG1 expansion and JSON
whitespace change. `git diff --stat -- src` was empty after each restoration and at final inspection.
No git checkout/restore/reset/add/commit command was used.

## 5. Coverage of the moves

Scratch `journey_monitor.py` uses Python `sys.monitoring` LINE callbacks, restricted to the two
absolute module paths, while the full golden runs through `t.sh`. No coverage dependency.
`coverage_report.py` relocates the strategy groups to this tip's definitions and uses compiled
code line tables (`dis.findlinestarts`, recursively including comprehensions/nested functions)
as the executable denominator. RESUME's definition line, comments, blank lines and class field
annotations are not executable function-body lines. Handwritten methods are listed individually;
generated dataclass methods have no source lines to move. The line ranges below are at this tip.

The strategy's read/machine-check/offer/discrimination/cold groups and completion/presentation/
evidence/control groups are included, including their private helpers. Core lifecycle, posterior
and instrument functions that stay in `probe_episodes` are excluded. So are the planned deletions
`plan_precommitted_block`, `abandon_episode` and duplicate `_content_id` copies in the other two
modules. Shared constants and dataclass fields move but are not function line coverage targets.

**Totals:** 97 functions/methods; 3,963 physical lines in their definition spans; **2,058 executable lines to move, 1,476 reached, 582 unreached with a reason, 0 unreached without a reason.**

A reason is an explicit coverage limitation, not a claim that the branch is dead. No normal branch is declared dead merely because these journeys miss it. Failed-store paths were not injected; longform/dialogue, stale/contaminated input, additional stop rules and expired unattempted retries remain follow-up coverage opportunities.

| Destination | Function at tip | Reached / executable | Unreached lines | Why not added / boundary not driven |
|---|---|---:|---|---|
| K9.6 reads | `causal_orchestrator:342 _content_id` | 4 / 4 | — | — |
| K9.7 machine checks | `causal_orchestrator:471 _machine_check_id` | 8 / 8 | — | — |
| K9.7 machine checks | `causal_orchestrator:485 backfill_obligation` | 18 / 18 | — | — |
| K9.7 machine checks | `causal_orchestrator:520 instrument_commissioning_obligation` | 13 / 13 | — | — |
| K9.7 machine checks | `causal_orchestrator:548 enqueue_backfill_obligation` | 9 / 9 | — | — |
| K9.7 machine checks | `causal_orchestrator:574 sweep_machine_checks` | 47 / 55 | 608, 618, 666-668, 680-682 | Old factors without H_OTHER / already reviewed candidates; exception logging needs a failing expiry or deferral store. The new cases cover both obligations and orphan closure. |
| K9.7 machine checks | `causal_orchestrator:688 _close_orphan_checks` | 14 / 15 | 699 | A pending check outside the swept kinds needs an unrelated machine-check fixture. |
| K9.7 machine checks | `causal_orchestrator:716 close_satisfied_backfills` | 4 / 14 | 731-738, 740, 742 | A mapping filled while its old backfill remains pending needs a stale-check fixture; this journey closes its factor instead. |
| K9.7 machine checks | `causal_orchestrator:746 resolve_machine_check` | 2 / 2 | — | — |
| K9.7 machine checks | `causal_orchestrator:761 pending_machine_checks_for_factor` | 12 / 15 | 789-791 | LO-wide checks without a factor are not produced by these factor-specific journeys. |
| K9.6 hard stops | `causal_orchestrator:798 record_learner_preference` | 12 / 19 | 811, 814-817, 819-820 | Invalid preference / missing factor or case arguments; normal decline and teach-now are covered. |
| K9.6 hard stops | `causal_orchestrator:835 learner_preference` | 7 / 7 | — | — |
| K9.6 reads | `causal_orchestrator:855 open_factors_for_hypothesis` | 13 / 14 | 862 | Missing hypothesis input is rejected/empty; all journey hypotheses exist. |
| K9.6 reads | `causal_orchestrator:878 _durable_case_factor` | 0 / 13 | 894, 896-897, 899-908 | Legacy receipt-linked cases without a live factor need an older case fixture. These journeys mint live factors. |
| K9.6 reads | `causal_orchestrator:911 _case_repair_class_id` | 2 / 5 | 925-927 | Receipt fallback for a case with no hypothesis repair mapping; the journeys use explicit mapped hypotheses. |
| K9.6 reads | `causal_orchestrator:932 _unmapped_case_obligation` | 0 / 14 | 941-951, 954-956 | Case-level backfill without a live factor needs an unmapped legacy case; factor backfill is covered. |
| K9.6 reads | `causal_orchestrator:960 diagnosis_receipt` | 7 / 8 | 964 | Empty attempt id; all journey receipts name an attempt. |
| K9.6 reads | `causal_orchestrator:973 _receipt_repair_class_id` | 0 / 15 | 982-996 | Old receipt shapes and repair-class fallbacks require receipt-only legacy cases. |
| K9.6 reads | `causal_orchestrator:999 _repair_class_by_hypothesis` | 8 / 9 | 1005 | Malformed / unmapped cause arm skipped; the separable-pair fixture supplies concrete mapped arms. |
| K9.6 reads | `causal_orchestrator:1013 _avoided_overteaching_minutes` | 25 / 26 | 1058 | Fallback when no per-class costs can be recovered needs a costless repair fixture. |
| K9.6 reads | `causal_orchestrator:1066 _probe_burden_minutes` | 10 / 12 | 1078, 1086 | Invalid/missing authored duration fallback; fixtures use valid durations. |
| K9.6 reads | `causal_orchestrator:1089 _recent_diagnostic_burden` | 6 / 6 | — | — |
| K9.6 reads | `causal_orchestrator:1114 _discrimination_inputs` | 28 / 39 | 1139, 1146, 1148, 1152, 1157-1163 | Malformed discrimination, zero pairs and exclusively inseparable pairs require a non-discriminating candidate fixture; these accepted candidates separate two causes. |
| K9.8 offer | `causal_orchestrator:1917 ProbeOffer.as_dict` | 10 / 10 | — | — |
| K9.6 hard stops | `causal_orchestrator:1931 _causal_origin` | 1 / 1 | — | — |
| K9.6 hard stops | `causal_orchestrator:1935 causal_origin` | 0 / 1 | 1938 | Public origin formatting wrapper; the causal offer uses the internal formatter. No write of its own. |
| K9.6 hard stops | `causal_orchestrator:1941 causal_origin_factor` | 0 / 2 | 1944-1945 | Origin parser for callers outside the chosen service/handler paths; no write of its own. |
| K9.6 hard stops | `causal_orchestrator:1948 episode_conflict_reason` | 5 / 8 | 1966, 1968, 1970 | Conflicting observed/open episode and incompatible origin branches require a previously administered competing episode. |
| K9.6 hard stops | `causal_orchestrator:1974 _probe_episode_conflict` | 5 / 6 | 1980 | Missing LO; all cases supply a valid learning object. |
| K9.8 offer | `causal_orchestrator:1987 _answer_shown` | 2 / 2 | — | — |
| K9.8 offer | `causal_orchestrator:2006 _OfferRefusedAtCommit.__init__` | 0 / 2 | 2007-2008 | Commit-time eligibility race requires a reveal inserted between offer and commit. No concurrent writer in these journeys. |
| K9.8 offer | `causal_orchestrator:2011 accept_probe_offer` | 8 / 8 | — | — |
| K9.8 offer | `causal_orchestrator:2043 _accept_probe_offer` | 84 / 142 | 2083-2084, 2097-2100, 2108, 2113-2117, 2124-2128, 2144-2149, 2157-2162, 2173-2185, 2216, 2220-2224, 2245-2250, 2266-2267, 2285, 2287 | Refusals: gone/resolved factor, declined offer, pending checks, absent/stale decision or candidate, unavailable item/hypothesis set, competing episode, eligibility race. Also repeat acceptance reuse. Requires stale/racing inputs beyond these accepted offers; not claimed dead. |
| K9.8 offer | `causal_orchestrator:2290 defer_probe_offer` | 9 / 9 | — | — |
| K9.8 offer | `causal_orchestrator:2313 request_teaching_now` | 14 / 14 | — | — |
| K9.8 discrimination | `causal_orchestrator:2345 pinned_causal_probe` | 5 / 6 | 2350 | Unknown presentation; every classified answer has a real committed presentation. |
| K9.8 discrimination | `causal_orchestrator:2356 classify_probe_response` | 20 / 24 | 2380-2381, 2390-2391 | No pin or no bundles; these journeys pin reviewed bundles. |
| K9.8 discrimination | `causal_orchestrator:2428 DiscriminatingObservation.outcome` | 0 / 1 | 2429 | Read-only convenience property; persisted outcome is compared directly. |
| K9.8 discrimination | `causal_orchestrator:2432 DiscriminatingObservation.observation_id` | 1 / 1 | — | — |
| K9.8 discrimination | `causal_orchestrator:2435 DiscriminatingObservation.as_dict` | 9 / 9 | — | — |
| K9.8 discrimination | `causal_orchestrator:2448 _measured_hypotheses` | 22 / 27 | 2478, 2481, 2486-2487, 2492 | Unknown hypothesis, missing bundle, empty/cohort-incompatible feature rows; authored bundles are well formed. |
| K9.8 discrimination | `causal_orchestrator:2504 _observation_support_scores` | 9 / 10 | 2519 | No measured hypothesis / empty classification fallback; selected instruments measure both concrete hypotheses. |
| K9.8 discrimination | `causal_orchestrator:2531 _probe_production_admissibility` | 17 / 18 | 2548 | Missing/mismatched attempt and administration metadata; committed, submitted answers have consistent metadata. |
| K9.8 discrimination | `causal_orchestrator:2579 record_learner_embedded_prediction` | 0 / 38 | 2612-2618, 2620-2624, 2628-2647, 2649-2654 | Separate tutor embedded-prediction channel, requiring a learner prediction and frozen discriminating bundle context. Explicitly outside these probe-answer journeys. |
| K9.8 discrimination | `causal_orchestrator:2658 record_probe_classification` | 84 / 90 | 2721, 2729-2730, 2753, 2756, 2802 | Missing pin, empty features, repeated/ambiguous/open-set/contaminated classification guard arms not all produced by the chosen sensor outputs; FG1 wait does cover exposed evidence refusal. |
| K9.8 discrimination | `causal_orchestrator:2850 deterministic_probe_features` | 21 / 24 | 2876, 2890, 2894 | Unknown/unassessed criterion and alternate feature names need differently authored sensors; the automatic case uses full-credit correctness. |
| K9.8 discrimination | `causal_orchestrator:2907 auto_classify_pinned_probe` | 31 / 36 | 2933, 2947, 2956, 2961, 2965 | Already recorded / no presentation / held or unparseable sensor / inseparable bundles. Journeys exercise some declines and a successful deterministic classification, not every malformed sensor. |
| K9.7 cold | `causal_orchestrator:2979 cold_verification_context` | 32 / 65 | 3004, 3020-3025, 3027, 3029-3033, 3035-3036, 3038-3040, 3048-3052, 3054-3055, 3057-3058, 3060-3061, 3066, 3068, 3073, 3075 | Fallback chain from candidate/debug receipt and missing repair/surface/affordance data; these cold tasks carry the complete remediation chain. |
| K9.7 cold | `causal_orchestrator:3089 record_cold_verification_from_task` | 68 / 105 | 3144-3148, 3169, 3189-3191, 3193-3194, 3200-3205, 3207, 3209-3210, 3222-3227, 3230, 3232-3233, 3249-3253, 3255-3257 | Final-receipt/chain failures, missing repair/source, contamination, precondition and ValueError handlers. Clean scheduled retries exercise success/failure, not every refusal or broken chain. |
| K9.7 cold | `causal_orchestrator:3268 sweep_expired_cold_retries` | 7 / 77 | 3293-3297, 3299-3305, 3307-3310, 3312-3315, 3317-3320, 3322-3324, 3326-3327, 3329-3333, 3335-3338, 3340, 3342-3343, 3345-3346, 3348-3350, 3352-3356, 3358-3359, 3364-3373, 3375-3376, 3378-3382 | No unattempted overdue cold retry: both cold journeys answer within the schedule. Requires a separate task left unanswered past expiry (including unavailable/changed items); not dead. |
| K9.10 presentations | `probe_episodes:1206 RoutineDisplayCovered.__init__` | 0 / 3 | 1207-1209 | Requires a routine disclosure covering a proposed probe; these instruments are fresh. |
| K9.10 presentations | `probe_episodes:1217 probe_eligibility` | 4 / 4 | — | — |
| K9.10 presentations | `probe_episodes:1230 routine_display_covers_item` | 1 / 1 | — | — |
| K9.10 presentations | `probe_episodes:1243 refuse_routine_display_covered` | 3 / 5 | 1257-1258 | Fresh instruments never raise the answer-shown refusal; needs a pre-commit reveal. |
| K9.10 presentations | `probe_episodes:1261 commit_presentation` | 23 / 24 | 1302 | Superseding an unanswered active presentation requires a second commit before the first answer; these journeys consume each presentation first. |
| K9.10 presentations | `probe_episodes:1318 record_presentation_forecast` | 11 / 23 | 1355-1366 | VOI admission payload envelope: the helper commits instruments directly without the scheduler exploration payload; requires a scheduler-committed value-admitted presentation. |
| K9.10 presentations | `probe_episodes:1370 presentation_commit_payload` | 47 / 49 | 1394, 1396 | Malformed/missing hypothesis/posterior and alternate selection metadata; normal commits have the locked set and belief. |
| K9.10 presentations | `probe_episodes:1458 _robust_channel_pin` | 16 / 18 | 1468, 1477 | Legacy episode with no channel hash, or missing stored channel; all fresh episodes pin a channel. |
| K9.10 presentations | `probe_episodes:1493 serve_presentation` | 5 / 8 | 1509-1511 | Invalidation and re-raise when a routine display covers the answer between commit and serve; these fresh instruments have no such disclosure. |
| K9.10 presentations | `probe_episodes:1515 probe_serving_block_reason` | 9 / 13 | 1532, 1540-1541, 1548 | Calibration cap lift and spent session/onboarding count caps need a capped session fixture. |
| K9.10 presentations | `probe_episodes:1552 probe_value_block_reason` | 15 / 21 | 1575, 1578, 1581, 1586, 1596, 1598 | Cap lift, missing hypothesis/posterior, ineligible item, admission counterfactual and value refusal alternatives; the direct committed item is eligible. |
| K9.10 presentations | `probe_episodes:1601 commit_item_presentation` | 14 / 17 | 1621, 1633, 1635 | Item outside slate / answer-shown race; current fixture item is eligible. |
| K9.10 presentations | `probe_episodes:1800 validate_presentation_for_submission` | 18 / 27 | 1814, 1817, 1823, 1825, 1827, 1829, 1831, 1836-1837 | Wrong item, missing/ended/reused presentation, episode or state-segment mismatch, ignored episode and exposure guards require invalid or stale submissions. |
| K9.11 evidence | `probe_episodes:2075 record_episode_evidence` | 34 / 35 | 2119 | Missing posterior/set or absent open episode guard; real submitted episodes supply both. |
| K9.11 evidence | `probe_episodes:2155 record_presentation_activity_classification` | 22 / 23 | 2191 | Missing practice attempt guard; activity follows a committed attempt. |
| K9.11 evidence | `probe_episodes:2206 _presentation_contamination` | 5 / 8 | 2211, 2213, 2217 | Alternate incidental/embedded or pre-revealed contamination shapes; ordinary committed probes and FG1 exposure cover the selected forms. |
| K9.11 evidence | `probe_episodes:2221 _record_presentation_activity_fact` | 23 / 23 | — | — |
| K9.11 evidence | `probe_episodes:2267 _robust_observation_snapshot` | 12 / 14 | 2283, 2288 | Legacy/no-channel and missing stored channel; all fresh episodes have their pinned channel. |
| K9.11 evidence | `probe_episodes:2300 _dual_write_probe_grade` | 40 / 43 | 2328, 2379-2380 | Missing presentation/card early return and best-effort exception logging need stale metadata or a failing ledger. |
| K9.11 evidence | `probe_episodes:2383 dual_write_presentationless_probe_grade` | 0 / 10 | 2399-2408 | A diagnostic answer with no presentation is a separate incidental path; all requested probe answers carry presentations. |
| K9.11 evidence | `probe_episodes:2412 dual_write_regraded_probe_grade` | 31 / 47 | 2443, 2447, 2449-2458, 2460, 2462, 2466, 2470 | Missing observation/card, fallback item/contract, unassessed or invalid grade and unavailable raw event branches. One assessed real regrade is covered. |
| K9.11 evidence | `probe_episodes:2494 _record_presentation_observation` | 158 / 178 | 2512, 2521, 2532, 2536, 2541, 2586, 2597-2598, 2600, 2628-2632, 2653, 2704, 2737-2740 | Early returns for missing/duplicate/mismatched rows, absent set/likelihood/channel and longform/alternate assessment features. Requires stale submissions or a longform instrument rather than these short answers. |
| K9.11 evidence | `probe_episodes:2756 _attempt_rubric_score` | 3 / 4 | 2759 | Missing practice attempt; real answers are persisted first. |
| K9.11 evidence | `probe_episodes:2763 _assess_longform_trace` | 10 / 23 | 2784, 2786, 2791, 2796-2799, 2801-2802, 2804-2805, 2807-2808 | Validated/freeform step traces and assessed-step outcomes need a longform item with a trace contract; the chosen instruments are short-answer. |
| K9.11 evidence | `probe_episodes:2811 _observation_features` | 11 / 14 | 2825, 2827, 2835 | Additional error families/trace signatures need alternative rubric errors or longform traces. |
| K9.9 completion | `probe_episodes:2839 persist_episode_beliefs` | 22 / 22 | — | — |
| K9.9 completion | `probe_episodes:2877 _evaluate_completion` | 41 / 82 | 2886, 2919, 2933, 2944, 2953, 2956-2958, 2985-2989, 2991-2998, 3000-3001, 3007-3009, 3011, 3014-3015, 3017-3025, 3027-3029 | Terminal guard; action-equivalent, robust abstention, exhausted-slate parking, stable-posterior breadth/dialogue units and strong-claim fast path. Value/count/mid-check stops intentionally cover different stopping rules; these alternatives need additional beliefs, instruments or claims. |
| K9.9 completion | `probe_episodes:3032 voi_probe_site_active` | 2 / 2 | — | — |
| K9.9 completion | `probe_episodes:3038 value_decides_episode` | 7 / 8 | 3054 | Active calibration session retains the count rule; no calibration session is opened here. |
| K9.9 completion | `probe_episodes:3058 robust_gate_applies` | 4 / 4 | — | — |
| K9.9 completion | `probe_episodes:3077 _latest_observation_session` | 6 / 6 | — | — |
| K9.9 completion | `probe_episodes:3088 episode_maximum_binds` | 1 / 1 | — | — |
| K9.9 completion | `probe_episodes:3105 _plausible_actions_agree` | 17 / 21 | 3131, 3137, 3140, 3144 | Empty/unknown hypothesis or aligned intervention alternatives require an action-equivalent posterior and route catalog. |
| K9.9 completion | `probe_episodes:3147 robust_gate_counterfactual` | 4 / 13 | 3167-3172, 3174-3176 | Continuing value decision after qualifying evidence with gate outranked, plus stable/unstable alternatives. Helper checks the serving gate before answering; completion uses its own counterfactual path. |
| K9.9 completion | `probe_episodes:3179 _robust_completion_override` | 2 / 2 | — | — |
| K9.9 completion | `probe_episodes:3206 _robust_gate_verdict` | 23 / 28 | 3218, 3234, 3240, 3255-3256 | No pinned channel, no candidates, and logging an authoritative gate forecast; current gate evaluations either lack breadth or are counterfactual. |
| K9.9 completion | `probe_episodes:3261 robust_gate_completion` | 2 / 5 | 3273-3275 | Fragile pick versus fragile stop under the gate-fix switch needs a tuned robust selection. These fixed draws do not cover every abstention verdict. |
| K9.9 completion | `probe_episodes:3278 _record_robust_selection_forecast` | 0 / 20 | 3294-3296, 3298-3302, 3304-3313, 3315-3316 | Authoritative robust gate with breadth and remaining candidates; chosen stops are value/count based. Logging exception additionally requires a failing forecast writer. |
| K9.9 completion | `probe_episodes:3319 _surface_key` | 0 / 4 | 3335-3338 | Only used by stable-posterior breadth completion; these stops occur earlier. Missing item additionally needs stale vault state. |
| K9.9 completion | `probe_episodes:3341 _complete` | 11 / 12 | 3352 | Completion without a posterior; production journeys pass the computed posterior. |
| K9.9 completion | `probe_episodes:3369 _complete_on_value_stop` | 12 / 12 | — | — |
| K9.9 completion | `probe_episodes:3400 _value_of_information_stop` | 10 / 11 | 3432 | Gate/site/candidate refusal alternative not selected by the fixed value case. |
| K9.11 controls | `probe_episodes:3450 stop_diagnosing_and_teach` | 27 / 29 | 3463, 3480 | No open episode or still-unanswered active presentation at stop. The mid-check case stops after two committed answers. |
| K9.9 completion | `probe_episodes:3508 close_diagnostic_segment` | 17 / 18 | 3529 | Invalidate an unanswered active presentation; selected segment is closed after its answer. |
| K9.9 completion | `probe_episodes:3546 _set_target_decision` | 7 / 7 | — | — |
| K9.11 controls | `probe_episodes:3584 episode_contract` | 17 / 18 | 3597 | No in-progress episode; contract is read before submission. |
| K9.11 controls | `probe_episodes:3619 next_probe_item` | 16 / 22 | 3634, 3637, 3647, 3659-3661 | No episode/set/candidates and causal discriminating-instrument preference; the peek case is an ordinary episode with a nonempty slate. |

## 6. T4 measurement (no ratchet added)

Strategy §2.19 T4 says the private-patch/getsource counts join M0's structure golden.
`tests/goldens/structure.toml` and the measuring test have no such counters at this tip.
The new ledger row is open, owner the orchestrator.

Scratch `measure_t4.py` parses all Python files below `tests/`. It counts syntactic
monkeypatch/setattr/mock.patch sites targeting a private attribute of an actual `learnloop`
module, resolving import aliases and module re-exports. Class/instance attributes, test modules,
`learnloop_sidecar` and public names are excluded. A loop is one site, not one site per iteration.
All 72 dynamic-attribute sites were reviewed: seven additional sites can target a private module
name (facet authority, facet actions, attempt core, mobile plan, reader RW4b, reading hardening,
teacher probes). One further site uses `student_server.W`, the dynamically returned worker module; it is counted too. They are explicitly listed in the script with concrete targets. The output
`t4_measurement.json` lists every counted location. The two requested numbers are **453 private
patch sites** and **23 assertions data-dependent on `inspect.getsource`**, following assignments
within each function. There are **29 getsource call sites**, a different metric; calls used for
helpers/parameterization are not themselves assertions. This is a static, site-based inventory,
not a count of runtime parametrized invocations. No ratchet, source or existing test was changed.

## 7. Commands and results

All commands used the supplied wrappers. `S` below means:
`/tmp/claude-1000/-home-saturn-Documents-thinking-learnanything/73b37aee-2550-41c4-88a8-8730b0f3c0c0/scratchpad/refactor-k95b`.

| Command | Result |
|---|---|
| `DIAGNOSIS_JOURNEY_WRITE_GOLDEN=1 $S/t.sh tests/test_diagnosis_journey_golden.py -q` | 18 passed, 9.00 s; final fixture written |
| `$S/t.sh tests/test_diagnosis_journey_golden.py -q` (fresh process 1) | 18 passed, 7.57 s |
| same (fresh process 2) | 18 passed, 7.52 s |
| same (fresh process 3) | 18 passed, 7.53 s |
| `$S/t.sh tests/test_diagnosis_journey_golden.py -q -n 4` | 18 passed, 4.17 s |
| `$S/t.sh tests/test_diagnosis_journey_golden.py -q -o pythonpath="/home/saturn/Documents/thinking/learnanything-k95b/src $S" -p journey_monitor` | 18 passed, 13.27 s; final monitoring corpus |
| `$S/t.sh tests/test_identity_pins.py tests/test_test_layout.py tests/test_structure_ratchets.py tests/test_public_tip_guards.py tests/test_architecture.py -q -n 4` | 378 passed, 24.86 s |
| `$S/py.sh ruff check` | All checks passed, 0.019 s (timed final invocation) |
| `$S/py.sh lint-imports --no-cache` | 42 contracts kept, 0 broken, 0.277 s (timed final invocation) |

Final new files: `tests/test_diagnosis_journey_golden.py` 34 lines,
`tests/diagnosis_journey_helpers.py` 477 lines,
`tests/fixtures/diagnosis_journey_golden.json` 135,211 lines (3,236,789 bytes).
This record and one ledger row are the only documentation changes.
`git diff --check` is clean; `git diff --stat -- src` prints nothing and
`git diff --quiet -- src` returns 0. Existing golden/pin files have no diff.
No new files have been staged; tracked-file checks will see them once the orchestrator adds them.
The new golden's size was checked directly in addition to running the tracked-file guard.

Scratch artifacts: `journey_monitor.py`, `coverage_lines.json`, `coverage_serial.json`,
`coverage_report.py`, `coverage_functions.json`, `measure_t4.py`, `t4_measurement.json`,
`mutate_journey.py`, saved `original_*.txt`, and named test logs. They are outside the worktree.

## 8. Limits and handoff

No full suite or landing gate, owner-vault runs, cross-machine portability, real model transport,
real RPC socket, bubblewrap, background-worker race or failing database was verified. No sandbox
operation failed in this implementation: direct handlers avoided the known socket constraint.
No run was killed, and no killed-run `.pytest_tmp/run-*` directory was left.
The known K9-3 held/regrade observation limitation and K9-6 seed sensitivity remain unchanged.
The only new ledger item is the missing T4 ratchet; no new product bug was established.
The coverage omissions above are deliberate limits of the golden corpus, not evidence of
full behavioral coverage. The orchestrator still owns the full landing gate and commit.

## 9. Registered table inventory

Every name below comes from `src/learnloop/db/table_roles.py` and is selected by each checkpoint.

397 registered tables:

```text
ability_transition_events, activity_administrations, activity_card_authoring, activity_card_state,
activity_card_versions, activity_cards, activity_exposure_events, activity_families,
activity_family_authoring, activity_family_membership_events, activity_family_versions, activity_observations,
activity_pattern_versions, activity_patterns, activity_surface_authoring, activity_surface_lifecycle_events,
activity_surface_reservations, activity_surfaces, ad_attempt_trace, ad_commission_results,
ad_coupling_versions, ad_dose_offers, ad_history_forecast_draws, ad_reading_opportunities,
ad_relatedness_runs, ad_selections, ad_state, agent_runs, angle_inventories, apply_intents, approach_maps,
assessment_contract_versions, assumption_decisions, assumption_returns, attempt_completion_work,
attempt_debug_payloads, attempt_diagnoses, attempt_feedback_metadata, attempt_submission_receipts,
attempt_surprise, attention_block_events, attention_blocks, blind_grade_records, calibration_stream_samples,
canonical_mapping_proposals, capability_aliases, capability_residual_state, capture_inbox, capture_routes,
card_lineage_edges, card_lineages, causal_activity_classification_events, causal_attribution_reports,
causal_blind_prediction_bundles, causal_cold_outcomes, causal_cold_verifications,
causal_discriminating_observations, causal_hypotheses, causal_machine_checks,
causal_mechanism_taxonomy_assignments, causal_mechanism_taxonomy_retirements,
causal_mechanism_taxonomy_versions, causal_probe_candidate_events, causal_probe_candidates,
causal_probe_decision_receipts, causal_probe_preference_events, causal_repair_class_definitions,
causal_shadow_selection_receipts, certification_cold_probe_outcomes, change_batches,
cold_measurement_opportunities, cold_measurement_opportunity_decisions, coldness_receipts,
commitment_arc_events, commitment_arc_versions, commitment_arcs, commitment_events,
commitment_target_versions, commitment_versions, commitments, composed_selector_telemetry_horizons,
concept_animations, confidence_calibration_state, content_events, contrast_pair_servings,
controller_candidates, controller_constraint_manifests, controller_decisions, controller_outcome_windows,
controller_ownership, controller_ownership_events, controller_prequential_reports,
controller_shadow_predictions, controller_snapshots, daily_plans, decision_features,
decision_measurement_events, decision_objectives, decision_records, decision_state_receipts,
deliverable_path_sections, deliverable_scope_inputs, deliverable_scope_resolutions, depth_edge_instances,
depth_edge_template_versions, depth_edge_templates, depth_envelope_versions, depth_milestone_versions,
depth_policy_versions, derived_state_rebuilds, diagnosis_adjudications, diagnosis_context_receipts,
diagnosis_feedback, diagnosis_wait_receipts, diagnosis_would_merge_log, diagnostic_augmentation_receipts,
diagnostic_eval_cases, diagnostic_eval_runs, diagnostic_pack_cards, diagnostic_pack_events,
diagnostic_pack_pins, diagnostic_packs, diagnostic_surface_generation_needs, discrimination_profile_matches,
elicitation_events, embedding_spaces, embedding_vectors, entity_source_links, error_event_lineage,
error_events, error_hunt_outcomes, evidence_facet_recall_state, exam_answers, exam_pool_items,
exam_predictions, exam_sessions, facet_capability_evidence, facet_dossiers, facet_identity_actions,
facet_merges, facet_outcome_observations, facet_recall_state, facet_registry_saves, facet_uncertainty,
failure_triage_events, failure_triage_routes, false_remediation_adjudications, familiarity_kernel_events,
familiarity_kernel_features, familiarity_kernel_models, family_evidence_cap_policies, family_memory_state,
family_proposals, field_signal_receipts, figure_predictions, figure_prefetch_decisions, figure_requests,
figure_source_checks, fitted_parameters, followup_generation_jobs, followup_ratings, followup_tasks,
followup_value_decisions, followup_workflow_events, followup_workflows, forecast_receipts, forecasts,
generated_probe_burns, generated_probe_items, goal_contract_drafts, goal_contract_heads,
goal_contract_versions, goal_lifecycle_events, golden_path_artifacts, golden_path_run_events,
golden_path_runs, grade_adjudications, grade_interpretations, grader_calibration_alphas,
grader_calibration_models, grading_clarification_responses, grading_clarifications, grading_evidence,
help_assists, hypothesis_events, hypothesis_exposure_probe_links, hypothesis_list_exposures, hypothesis_marks,
hypothesis_recurrence_groups, hypothesis_recurrence_review, hypothesis_recurrence_state, hypothesis_sets,
ingest_batches, ingest_job_dependencies, ingest_jobs, instructional_impressions, interaction_events,
interactive_figures, intervention_needs, item_fingerprints, item_forecast_payloads, item_forecast_scores,
item_misconception_discrimination, item_parameter_state, item_serve_inputs, item_skeletons, judgment_ledger,
judgment_work_claims, lapse_episodes, learner_claims, learner_gap_check_advances, learner_gap_commitments,
learner_note_links, learner_notes, learner_state_beliefs, learner_text_gap_jobs, learner_text_gap_reversals,
learner_text_gaps, learner_theta, learning_object_mastery, learning_outcome_labels, lesson_activity_intervals,
lesson_checks, lesson_episodes, lesson_plans, lesson_receipts, lesson_turn_payloads, lesson_turns,
lesson_weight_state, lesson_weight_trace, lessons, library_asks, lo_probe_state, maintenance_notices,
measurement_contract_corrections, measurement_events, misconception_candidates,
misconception_disposition_events, misconception_transition_events, misconceptions, missing_vocabulary_notes,
mobile_devices, mobile_jobs, mobile_pairing_attempts, mobile_pairing_guard, mobile_pairings,
mobile_request_log, model_call_receipts, model_work_checkpoints, notation_mappings, observation_events,
observation_templates, outcome_schema_versions, outcome_schemas, p2_ladder_policies, p2_ladder_stages,
parameter_bind_events, parameter_registry, parameter_registry_manifests, parameter_sensitivity_certificates,
passage_links, persona_realism_runs, pf_candidates, placement_quick_check_items, placement_quick_checks,
plan_presentations, plan_usage_pauses, policy_experiment_assignments, post_attempt_jobs, practice_attempts,
practice_eval_queries, practice_index_evaluations, practice_index_proposals, practice_item_quality_state,
practice_item_snapshots, practice_item_state, practice_pool_events, practice_pool_surfaces, practice_pools,
prefilter_payloads, prefilter_receipts, probe_calibration_sessions, probe_episodes, probe_family_calibrations,
probe_family_lifecycle_events, probe_family_templates, probe_generation_needs, probe_instrument_cards,
probe_item_calibrations, probe_item_family_links, probe_manipulation_audits, probe_observations,
probe_presentations, probe_regrade_checks, probe_state_segments, progression_policy_versions,
proposed_patch_item_dependencies, proposed_patch_items, proposed_patches, question_classifications,
question_events, question_promotion_requests, question_promotions, queue_state, raw_grade_events,
reader_authored_questions, reader_background_requests, reader_capture_outbox, reader_cue_impressions,
reader_path_depths, reader_path_sections, reader_section_progress, reader_session_digests,
reading_exposure_receipts, recurrence_escalations, recurrence_guard_cases, reference_key_checks,
remediation_episodes, retirement_records, retrieval_feedback, retrieval_fusion_posteriors,
retrieval_intervention_outcomes, retrieval_interventions, reveal_events, router_decision_bindings,
router_decision_payloads, router_decisions, router_learner_preferences, router_objective_traces,
router_outcomes, router_suggestion_responses, rung_variant_requests, scheduler_explanations,
scheduler_offer_receipts, scheduler_slate_candidates, scheduler_slates, schema_migrations, section_coverage,
session_checkpoints, session_handoffs, session_receipts, sessions, shadow_component_events,
soft_kinship_features, source_annotation_anchor_segments, source_annotation_anchor_versions,
source_annotation_events, source_annotation_versions, source_annotations, source_artifacts,
source_auto_build_state, source_block_fts, source_block_health, source_comparisons,
source_conflict_resolutions, source_conflicts, source_document_assets, source_document_blocks,
source_document_units, source_exam_profiles, source_exercise_imports, source_exposure_events,
source_extraction_runs, source_held_out_signal_marks, source_locator_schemes, source_object_citations,
source_object_relations, source_object_versions, source_objects, source_render_block_crosswalk,
source_render_views, source_revisions, source_service_spend, source_span_reanchors, source_tool_calls,
source_unit_inventories, source_unit_selections, subject_identifiability_watermarks, submission_intents,
surface_fingerprint_memberships, surface_mint_requests, synthesis_generation_needs, synthesis_manifests,
synthesis_runs, synthesis_shard_results, target_exemplars, task_blueprint_review_events,
task_blueprint_versions, task_blueprints, task_feature_schema_versions, text_write_provenance,
trace_exercised_facets, unresolved_cause_factors, vault_epigraphs, voi_forecasts, workbench_sessions,
workbench_steps
```

## Orchestrator's change before landing: the setup stage records no rows

As handed back, each case's first stage held every row the fresh vault's own seed wrote: the applied migrations
(`schema_migrations`, 391 KB across the 18 cases), calibration priors, the probe family templates, the ladder and
route tables. That was 1.02 MB of the 3.24 MB golden, none of it written by a diagnosis journey, and every new
migration would have rewritten all 18 cases. `Journey` now takes its first snapshot as the baseline and records the
setup stage with nothing written. Every later stage is compared exactly as before.

- Golden: 2,193,491 bytes (88,640 lines), from 3,236,789.
- Rewritten with `DIAGNOSIS_JOURNEY_WRITE_GOLDEN=1`, then three fresh runs: 18 passed each (7.6-7.7 s); with `-n 4`:
  18 passed (4.3 s).
- The three scratch edits above act on later stages, so their results stand; they were not re-run after this change.
- A second change, found by the pre-gate check after the first commit: a decision-state receipt records the
  checkout's commit (`versions.code = "git:<sha>"`), so the `fg1_wait` case failed as soon as HEAD moved. The
  recorder now replaces that one value with a fixed token. The worker's runs could not see this: it never commits.
