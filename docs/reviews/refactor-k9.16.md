# K9.16: retire causal shadow selection

2026-11-16. Removal complete; continuation proof results are recorded below. The orchestrator resolved the first worker's stop with the isolated-ID comparison: the removal changes only shadow ID consumption, not production behavior or any random-ID distribution. No identity pin or behavioral golden was moved. K9-6 remains open for robust EIG seed sensitivity, not as a landing blocker.

Removed: shadow selector/prior/unavailable helper and exclusive imports/constants; readiness report; orchestrator context, call and failure record; repository writer; CLI command; measurement-health member/import and its stale readiness comment; retired VOI site and its report adapter. Documentation generator inventories no longer name the deleted report. No frontend reader or DTO member was found, so no frontend file changed.

Retained: four valuation functions (AST identical), their constants including the historical SHADOW-named loss regime and calibration labels, receipt table/migration/role/readers, nine other VOI sites and recorder/stores, offline harness, both calibration reports apart from the retired branch, scheduling EVSI, VOI stopping, predictive EIG and every config field. EvsiConfig now describes its live readers. The only hand-written vault note changed is Concepts/Diagnosis and Remediation.md (test inventory). Generated Reference notes were untouched. Shared tests/causal_shadow_selection_helpers.py is unchanged and unrenamed: other suites still import it; names and synthetic fixture IDs remain stable.

## The differential

First comparison: scratch test_k916_differential.py calls the seven existing test functions under t.sh with tests.conftest loaded, fresh synthetic vaults, pinned SystemClock/provenance datetime and deterministic shared/independent ULID streams. Existing pytest draw pins remain active. Dumps include every SQLite table; table_roles classifies 397 tables per vault: RAW_LEDGER 166, WORKFLOW 100, DERIVED 27, RECEIPT 96, COMPAT 8. Five additional FTS storage tables are also compared. Before and a repeated before are identical. After passes all seven original journey assertions.

Compare first without normalization. Then align generated ULIDs by allocation order, dropping only allocations made within record_shadow_selection; surviving allocation stacks and counts agree. Compare JSON including embedded IDs, retaining all other values. Learning-outcome rows are aligned by source/outcome attempt keys because their hash-derived primary keys moved. No hashes are recomputed or suppressed. Only shadow receipt rows, retired-site forecast rows, and exact shadow-failure records are eligible exclusions; only nine shadow receipt rows actually disappeared. No retired forecast rows or shadow failures existed in these journeys. All other row counts agree.

Journey: removed allocations / shifted surviving ULIDs / raw differing tables / differing tables after ULID alignment (of 397):
- test_causal_disambiguation_end_to_end_acceptance: 2 / 54 / 41 / 16.
- test_cold_verification_is_carried_through_the_followup_task: 1 / 81 / 36 / 10.
- test_not_now_persists_and_the_next_call_does_not_reoffer: 2 / 2 / 2 / 0.
- test_reviewed_active_candidate_produces_the_disambiguation_offer: 1 / 0 / 0 / 0.
- test_serving_the_pinned_probe_reuses_its_presentation: 1 / 54 / 16 / 2.
- test_take_the_quick_check_over_rpc_pins_the_probe: 1 / 10 / 5 / 0.
- test_teach_me_now_starts_the_repair_under_recorded_authorisation: 1 / 1 / 1 / 0.

All tables not listed as differing in scratch comparison.json compare equal, including the five FTS tables. Across seven vaults: 2,678/2,779 registered table instances equal before ID normalization and 2,751/2,779 after; 35/35 FTS instances equal. The remaining differences are hash-derived IDs/references, administration snapshot hashes (four rows), repair forecast input hashes (two rows), and the serving channel pin (one presentation and its probe_selection forecast). No chosen item, status, outcome score, or chosen arm changed after aligning corresponding entities. The robust EIG score did change.

Serving RPC, both probe_presentations.selection_components_json.channel_pin and voi_forecasts.forecast_json.channel_pin:
- decision_context_hash: 0db1bf536d0a663ad51c1ea3f079fa37 -> 0ef218c57d8ddf07f544744b61b05c0e.
- ensemble_seed: 15479279091090457264 -> 7171396014149413133.
- robust_eig_per_second: 2.6664508909623556e-05 -> 4.689629030874119e-05.
The shifted episode ID enters probe_robust.instrument_ensemble decision context. Individual ensemble samples are not persisted by these journeys and were not separately captured; the first comparison therefore triggered the original stop. The isolated-ID proof below resolves its cause. Full changed rows, IDs and hashes are in scratch comparison.json; summarize_comparison.py prints unique changes.

Other changed non-ID hashes, before → after:

- Acceptance administration snapshots:
  d7d95c83bdbef968de8006a092742b66 → 4ae79c8cb8341e74c81b42f69bcf50e4
  8e0d8414bbd7793d4839ad0e499b1bce → 8a9af7af0034e91559a3478862c9b880
- Cold-verification administration snapshots:
  654469ae397f12ce953ae746b6ec25ee → 73a732cd59205265be691e43dd11227b
  b565544c32ee71125ad17003c2608ae3 → 41c2057adb5ba1d34706054fd4089028
- Acceptance forecast inputs_hash:
  d4d6c0b78e4170a146a5436e551448ea2f6f25e6c93363ea2e7175d39f2ef62a →
  8f3709f181d37e1a639fc14f26f01f1934de7f0883be1a88acceaa4dc06d2ba0
- Cold-verification forecast inputs_hash:
  78cd9e4e03b9fe6be3609a6110075ce4e07aff9d5d4e2d32301a2c855d334d67 →
  5dee0973551f8f3eb749da3cccdacb61edcf36d942d4fabdbdb9e8df79515408

Hash-derived IDs also moved: acceptance has one each of dr_, ccv_, cco_, cpc_, cdo_, crf_ and three lol_ identities; cold verification has one each of dr_, ccv_, cco_, crf_ and lol_. All changed values and their referencing rows are retained in S/comparison.json; S/summarize_comparison.py prints each unique before/after value. No additional persisted seed or draw-dependent scalar differences were found.

Isolated-ID comparison (orchestrator evidence): `/home/saturn/.claude/projects/-home-saturn-Documents-thinking-learnanything/a22010cc-5149-4947-a2b8-247f18b8f1a0/scratchpad-backup/k916-proof/`, `test_k916_isolated.py`. The orchestrator reran the same seven journeys at BASE, handing back the ID stream unchanged whenever `record_shadow_selection` draws an ID. Compared RAW, without any ID normalization, against the first worker's after dumps: all surviving IDs identical (acceptance 136, cold verification 89, not now 11, reviewed candidate 9, serving RPC 90, quick-check RPC 80, teach me now 11), and 2,814/2,814 table instances equal after removing only the nine retired shadow receipts: 1,162 RAW_LEDGER, 700 WORKFLOW, 189 DERIVED, 56 COMPAT, 672 RECEIPT, 35 FTS. No other row or stored value differs, including decision_records and voi_forecasts. These results were supplied by the orchestrator; this continuation inspected the isolated harness and did not rerun BASE.

This isolates every first-comparison seed, score, hash-derived ID and snapshot/input hash difference to the shifted fixed ID sequence. Production IDs are fresh randomness; removing shadow allocations changes neither behavior nor its distribution. No chosen items changed in either comparison. Individual ensemble samples were not separately captured in the first comparison; the isolated comparison has identical stored seeds and scores without normalization. The robust EIG estimate's 2.67e-05 versus 4.69e-05 seed sensitivity at the configured ensemble size remains K9-6, for the robust probe path, with no fix here.

Vault-script verification: module_generate.py drops only `learnloop.diagnosis.causal_selection_audit` from EVALUATION_MODULES and MODULE_WORKFLOW_OVERRIDES; module_validate.py drops only its source path from EXPECTED_EXPLICIT_STATUS. These three inventory entries would otherwise describe/require a module that no longer exists. No other script changes were present; nothing needed reverting.

AST check (scratch ast_check.py, git show HEAD versus current file, ast.dump without positions): build_causal_loss_table, likelihood_regime_for_candidate, duration_estimates_for_repair_classes, _stable_emission_key: 4/4 identical.

Tests removed (all only exercise retired behavior):
- test_shadow_receipt_rides_the_live_decision_with_typed_arms: receipt production.
- test_commissioned_v2_bundles_reach_arm_b_and_the_prior_refusal_passes_through: shadow rank and readiness.
- test_v1_style_bundles_stay_arm_c_and_never_license_measure: shadow verdict.
- test_evpi_skip_bound_licenses_stop_under_a_skewed_supported_prior: shadow ranking/idempotency.
- test_readiness_report_types_every_empty_denominator: removed report.
- test_readiness_report_counts_multiplicity_and_regimes: removed report.
- test_causal_shadow_records_its_formal_evsi_forecast: retired forecast producer.
- test_measured_loss_switch_charges_unresolved_minutes_in_the_shadow: retired shadow loss consumer. Config and live loss consumers remain.

Test ports/assertion changes:
- test_no_action_mapping_is_a_typed_abstention_not_a_fabricated_route: removed assertions on shadow receipt/body; retained direct loss-table assertions unchanged.
- test_stripping_the_h_other_disposition_demotes_arm_b and test_duration_estimates_carry_honest_provenance: unchanged test bodies and assertions, retained in the existing file.
- test_shadow_failure_and_corruption_cannot_alter_the_live_decision replaced by test_causal_probe_decision_writes_no_retired_shadow_receipts: removed monkeypatches of the deleted writer and three-status/one-shadow assertions; commission a real candidate, assert its live receipt exists and its ID matches the returned status receipt ID, and assert zero shadow receipts and zero retired-site forecasts. The continuation runs this permanent regression test below.
- Two generic report fixtures (test_regret_counts_only_independent_truth, test_one_cold_verification_is_one_repair_outcome) and their aggregate lookup keys now name probe_selection; all expected regret/truth/repair values are unchanged. The first worker changed the fixtures but missed the two lookup keys; the continuation fixed those KeyErrors (K9-7). Removed the unused _arm_b_shadow fixture and its exclusive imports.

Proof commands/results (S is the designated scratch/refactor-k916 directory):
- LEARNLOOP_KEEP_TEST_TMP=1 S/t.sh -p tests.conftest S/test_k916_differential.py -q -m "not arc_close" --basetemp=S/journey-tmp: before 7 passed (2.70s); repeat 7 passed (2.64s); after 7 passed (2.84s). Two initial harness calibration runs also passed 7 each; their only repeat difference was the unpinned provenance timestamp, then fixed in scratch before the authoritative baseline.
- S/py.sh python S/check_repeat.py: all seven baseline databases equal.
- S/py.sh python S/compare_journeys.py: first comparison triggered the resolved stop above; script emits comparison.json/log rather than a pytest assertion.
- S/py.sh python S/ast_check.py: 4/4 identical.
- S/py.sh ruff check tests/test_voi_forecasts.py src/learnloop/diagnosis/causal_orchestrator.py --fix: five unused imports removed; clean.
- git diff --check: passed.
- S/py.sh python tests/test_cli_help_snapshot.py --write: regenerated. Reverted only the compatible pre-existing `why` additions/optional argument from its output; final diff removes exactly causal-selection-readiness (21 lines), with no other contract changes.
- S/t.sh tests/test_registry_audit.py tests/test_architecture.py tests/test_identity_pins.py tests/test_retired_config_identities.py tests/test_test_layout.py tests/test_structure_ratchets.py tests/test_effective_defaults_golden.py tests/test_cli_help_snapshot.py -q -n 4 -m "not arc_close": 378 passed (43.42s). No identity/default golden or pin failed or changed.
- bash S/run_remaining.sh: one chunk of 16 explicit files at -q -n 4 -m "not arc_close"; 234 passed, 2 failed (15.21s). The two failures were the edited generic VOI fixtures' stale aggregate site lookups, corrected without changing expected values. S/remaining-files.txt and S/remaining-continuation.log retain the selection/output.
- S/t.sh tests/test_voi_forecasts.py tests/test_causal_shadow_selection.py -q -n 4 -m "not arc_close": 31 passed (2.57s), including both corrected tests and all four retained helper/firewall cases. Together with the first chunk, all 236 distinct selected tests passed. No tests/test_instructional_valuation*.py exists at this tip; the chunk additionally includes every test file importing learnloop.instructional.valuation (including test_value_candidates.py and test_discriminating_search.py).
- S/t.sh tests/test_causal_shadow_selection.py::test_causal_probe_decision_writes_no_retired_shadow_receipts tests/test_structure_ratchets.py -q -n 4 -m "not arc_close": 4 passed (7.57s), after lowering the ratchet.
- S/py.sh python tests/test_structure_ratchets.py --write: lowered largest_import_component 186 -> 185, modules_in_an_import_cycle 279 -> 278, functions_over_200_lines 73 -> 72. No number rose; the other five counts are unchanged. Retained only those decreases and their two removed members, excluding unrelated pre-existing figures metadata drift from the generated output.
- S/py.sh ruff check: all checks passed (also rerun after the two lookup fixes and readiness comment deletion).
- S/py.sh lint-imports --no-cache: 42 contracts kept, 0 broken.
- S/py.sh python S/ast_check.py: rerun, 4/4 retained functions AST identical.
- S/py.sh python docs/learnloop-architecture-vault/_scripts/validate_vault.py: 11 stale generated-note path errors (deleted causal_selection_audit and pre-existing failure_triage references).
- S/py.sh python docs/learnloop-architecture-vault/_scripts/module_validate.py: 16 stale generated-note/source/test link errors; source coverage 1224/1224, package maps 69/69, YAML 1296/1296, Wikilinks 43425/43425, Markdown links 42661/42673.
- S/py.sh python docs/learnloop-architecture-vault/_scripts/desktop_validate.py: one reproducibility error, stale Reference/_generated.md.
- S/py.sh python docs/learnloop-architecture-vault/_scripts/db_validate_reference.py: 187 generated-reference errors (missing deleted-module paths and stale source-line citations), 397 table notes and 1171 effective config leaves inspected. All four validator logs are under S; generated Reference files remain untouched for orchestrator regeneration.
- git diff --check: passed. No sandbox blocker occurred in this continuation; the complete sidecar RPC journey file passed.

Affected chunk files: tests/test_attempt_chain_records.py, tests/test_causal_orchestrator.py, tests/test_causal_p2_acceptance.py, tests/test_causal_repair_sidecar_rpcs.py, tests/test_causal_shadow_selection.py, tests/test_discriminating_search.py, tests/test_facet_belief_successor_derivation.py, tests/test_facet_locks_landing.py, tests/test_hypothesis_reference_contract.py, tests/test_reader_followups_review.py, tests/test_reader_followups_round3.py, tests/test_robust_completion_gate.py, tests/test_sources_merge_composition.py, tests/test_value_candidates.py, tests/test_voi_forecasts.py, tests/test_voi_merge_composition.py.

The three named TestClient files (test_mobile_v3_probes.py, test_ih6_workbench_open_item.py, test_ih4_preferences_inform_router.py), known socket/bubblewrap-limited tests outside the selected files, full suite/arc-close/durability gates and frontend tests are left for the orchestrator. No kept run directory remains under .pytest_tmp. Strategy v3 has no section 2.20 at this tip (ends at 2.19 before section 3); section 2.1 and the K9.16 diagnosis plan were read. No live learner data, network/model calls, commits or git mutations.

Files changed from HEAD (+/-; this new record excluded):
- docs/learnloop-architecture-vault/Concepts/Diagnosis and Remediation.md: +1/-1.
- docs/learnloop-architecture-vault/_scripts/module_generate.py: +0/-2.
- docs/learnloop-architecture-vault/_scripts/module_validate.py: +0/-1.
- docs/reviews/refactor-bug-ledger.md: +2/-0.
- src/learnloop/cli/app.py: +0/-71.
- src/learnloop/config/schema.py: +2/-2.
- src/learnloop/db/repositories.py: +0/-70.
- src/learnloop/diagnosis/causal_diagnostic_selector.py: +5/-463.
- src/learnloop/diagnosis/causal_orchestrator.py: +0/-33.
- src/learnloop/diagnosis/causal_selection_audit.py: +0/-228.
- src/learnloop/diagnosis/chain_records.py: +1/-1.
- src/learnloop/evsi_calibration/live_report.py: +0/-15.
- src/learnloop/scheduling/voi_forecasts.py: +0/-1.
- src/learnloop_sidecar/handlers/measurement.py: +0/-4.
- tests/cli_surface.json: +0/-21.
- tests/goldens/structure.toml: +3/-5.
- tests/test_causal_shadow_selection.py: +21/-332.
- tests/test_voi_forecasts.py: +7/-73.
