Step 0: completed by the first worker; its 0(d) stop was overruled by the
orchestrator. Proceeded with deletion after reading its record and spot-checking
references, method callers, the receipt classification, and all registry manifest
readers in src/, tests/, scripts/ and apps/. No compared registry-manifest hash
reader was found. No live production module caller was found. No new stop.

Read the strategy's K9.15 and Q3 rows, CLAUDE.md's Tests section, and the identity
rules in docs/specs/refactor_strategy_v3.md before auditing.

Step 0(a): searched src/, apps/, scripts/, tests/, the architecture vault's
_scripts/, and pyproject.toml. failure_triage: 72 matching lines in 24 files;
FailureTriage and failureTriage: zero. The registry has the string-based inventory
entry and three registrations. Five test files import the module:
tests/test_failure_triage.py, tests/test_failure_triage_causal_gate.py,
tests/test_causal_attribution_p2.py, tests/test_causal_p2_acceptance.py, and
tests/test_p2_acceptance.py. No production function caller was found. Other
matches concern live route/event storage or comments describing the dead reader.
No module reference was found in the desktop app, sidecar, CLI, or entry points.
The generator match classifies tables by their failure_triage prefix.

There is no __all__. Independently searched every public top-level definition:
TRIAGE_ROUTES_SCHEMA_VERSION, TRIAGE_CONFIDENCE_BUCKET_EDGES,
TRIAGE_DOMINANCE_SHARE, TRIAGE_REASONS, UNKNOWN_REASON,
TRACE_CONSISTENCY_STATES, TIER_ONE_BASIS_DETERMINISTIC, TIER_ONE_BASIS_LEGACY,
TIER_ONE_BASIS_CAUSAL, TriageError, CausalSupportNormalization,
normalize_causal_support, TriageResult, triage, decide, override, triage_status.
Common-name searches include unrelated implementations and ordinary prose; these
are not module callers. Exact search output is in the assigned scratch directory,
step0-symbol-references.txt. No failure_triage spelling matched Concepts/ or
Decisions/ handwritten notes.

Step 0(b): append_failure_triage_event has four callers, all in failure_triage.py
(774, 821, 923, 990), and no test caller. failure_triage_event has two module
callers (909, 981) and five test calls: test_causal_p2_acceptance.py (178, 682,
1172), test_failure_triage.py (215), test_failure_triage_causal_gate.py (595).
Neither method has another production caller.

Stored registry rows (step 0(c) and the ruling)

parameter_registry.refresh iterates decision_specs, hashes each effective value,
and calls Repository.upsert_parameter_registry_entry; it never removes absent
specs. Existing TRIAGE_CONFIDENCE_BUCKET_EDGES and TRIAGE_DOMINANCE_SHARE decision
rows stay unchanged, including updated_at. TRIAGE_ROUTES_SCHEMA_VERSION is
structural and never written by refresh; any preexisting row is also left alone.
freeze_manifest refreshes, reads stored decision rows, hashes them, and inserts a
receipt through Repository.insert_parameter_registry_manifest. ops/upgrades.py
calls it when freezing a predecessor. The insertion is idempotent by
algorithm_version, not manifest_hash; existing frozen versions are never rewritten.

The first worker measured a fresh in-memory registry at fixed defaults/version:
390 decision parameters, a584d43269b8d3a5ed7590441b1c0dc8, before removal;
388 decision parameters, 29e21c66eb82dfa44a93fc0795fad81d, after removal.
Only the two decision keys disappear; common values are identical. Existing
vaults keep their rows and frozen receipts, and retained rows appear in later
manifests. This is a RECEIPT (db/table_roles.py), not a compared identity:
nothing keys, compares, deduplicates or reuses by its manifest_hash. Its only
repository readers are the algorithm-version idempotence check and getter;
test_registry_audit reads entries_json, not a hash comparison. A fresh vault's
receipt correctly lists the remaining parameters. The identity rule protects
compared identities, so this receipt difference is allowed by the ruling.
No stored rows were migrated or removed. Added exactly one ledger row, K9-5:
open, low, no learner-visible effect; missing-spec row cleanup is deferred to a
registry follow-up due at K9 package close.

Changes

Deleted diagnosis/failure_triage.py (1,054 lines), the registry inventory entry
and three registrations (14 lines), and Repository.append_failure_triage_event
and failure_triage_event (85 lines including separators). Kept both tables,
migrations, table_roles, both route readers, failure_triage_events_for, and
scheduling/action_loss unchanged. Deleted the two dedicated test files (249 and
719 lines), with live coverage ported as below. Comments/docstrings in
causal_attribution, causal_orchestrator, canonical_projection and causal_health
now describe surviving readers/provenance and historical events accurately.
Generated Reference notes were not edited. No handwritten note names the module
explicitly. A generic-triage spot-check found Concepts/Learning System.md claiming
reader dialogue can influence triage; removed that clause (1 added/1 deleted
line). Reader Tutor and Teach-Back.md's routing-prior projection remains true:
the sidecar reader_routing_prior RPC still exposes it for inspection. No other
handwritten Concepts/ or Decisions/ note changed.

File line deltas (added/deleted):
  src/learnloop/diagnosis/failure_triage.py: 0/1054 (deleted)
  src/learnloop/params/parameter_registry.py: 0/14
  src/learnloop/db/repositories.py: 0/85
  src/learnloop/diagnosis/causal_attribution.py: 3/5 (comments)
  src/learnloop/diagnosis/causal_orchestrator.py: 4/6 (docstring)
  src/learnloop/diagnosis/causal_health.py: 3/4 (docstring)
  src/learnloop/substrate/canonical_projection.py: 4/5 (comment)
  tests/test_failure_triage.py: 0/249 (deleted)
  tests/test_failure_triage_causal_gate.py: 0/719 (deleted)
  tests/test_causal_attribution_p2.py: 94/77
  tests/test_causal_p2_acceptance.py: 20/178
  tests/test_p2_acceptance.py: 3/5
  tests/test_triage_routes.py: 31/0 (new)
  docs/learnloop-architecture-vault/Concepts/Learning System.md: 1/1
  docs/reviews/refactor-bug-ledger.md: 1/0 (K9-5)
  docs/reviews/refactor-k9.15.md: this updated record (untracked)

Deleted tests (each exercises only the deleted implementation)

tests/test_failure_triage.py:
  test_dont_know_on_never_exposed_routes_unfamiliar_decisively: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.
  test_expired_memory_trace_routes_lapse_decisively: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.
  test_quarantined_surface_routes_fault_never_a_deficit: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.
  test_high_confidence_signature_takes_intended_route: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.
  test_concentrated_signature_distribution_stays_tier_one: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.
  test_diffuse_signature_distribution_downgrades_to_tier_two: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.
  test_bare_high_confidence_signature_still_routes_tier_one: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.
  test_low_confidence_yields_decision_aid_that_never_auto_commits: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.
  test_ambiguous_cause_defaults_to_unknown_distribution: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.
  test_supplied_p0_distribution_is_used_and_normalized: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.
  test_decide_commits_the_aid_and_routes_the_run: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.
  test_decide_diverging_from_recommendation_logs_an_anchor: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.
  test_override_logs_adjudication_anchor: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.
  test_triage_trace_is_append_only_and_logs_goal_contract_head: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.
  test_retried_triage_is_idempotent_on_the_ledger: Deleted triage routing, decision-aid, override/anchor or append-ledger behavior; its writer and entry points are removed.

tests/test_failure_triage_causal_gate.py:
  test_unmapped_and_open_set_mass_stays_in_the_denominator: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_two_hypotheses_on_one_reason_aggregate: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_open_set_row_never_credits_a_mapped_reason: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_missing_score_on_a_concrete_hypothesis_is_incomplete: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_negative_score_is_clamped_and_flagged: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_all_none_scores_produce_zero_mass_and_no_dominance: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_ties_and_residual_maxima_name_no_dominant_reason: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_authority_approval_reads_the_causal_attribution_vocabulary: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_receipt_presence_alone_does_not_downgrade_the_legacy_route: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_unapproved_authority_cannot_promote: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_incomplete_support_blocks_promotion_but_not_the_legacy_arm: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_causal_veto_downgrades_an_otherwise_legacy_valid_route: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_promotion_requires_positive_trace_evidence_not_mere_absence: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_no_receipt_keeps_the_pure_legacy_behaviour: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_deterministic_triggers_report_their_own_basis: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_snapshot_uses_the_merged_signature_map_and_keeps_open_set_rows: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_a_discriminating_observation_overlays_scores_but_not_always_authority: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_provisional_distribution_keeps_the_residual_bucket_visible: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_supplied_distribution_still_takes_precedence: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_zero_mass_causal_support_falls_through_to_the_signature_fallback: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_triage_records_tier_one_basis_on_the_result_and_the_event: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.
  test_alternatives_surface_the_residual_bucket_and_its_hypotheses: Deleted normalizer, snapshot adapter, provisional alternatives or tier-one gate behavior; no serving caller exists for that gate.

tests/test_causal_attribution_p2.py:
  test_triage_signature_authority_is_an_and_gate_not_a_replacement: calls only the removed _decisive_route; the live rung_divergence_gate tests stay unchanged.
tests/test_causal_p2_acceptance.py:
  test_dominance_veto_is_reachable_through_the_real_triage_entrypoint: synthetic support tested only the removed triage entry point and its event payload.

Ported tests and every changed assertion

- test_route_table_is_seeded_data_over_ten_reasons and
  test_only_false_belief_and_unknown_reopen_a_diagnostic_episode moved to
  tests/test_triage_routes.py using create_basic_vault and the live repository.
  The first compares the reasons with an explicit ten-name set instead of the
  removed TRIAGE_REASONS tuple; len == 10 and the reopening set are unchanged.
- test_legacy_receipt_states_are_unknown_and_cannot_promote became
  test_legacy_receipt_states_are_unknown in test_causal_attribution_p2.py.
  It calls live receipt_trace_consistency directly, checks each of three ids
  equals unknown, and covers both receipt-level bool values. Removed the dead
  snapshot's trace_consistent assertion and the dead gate's promotion/legacy
  routing assertions; the shared schema-2 reader contract remains tested.
- test_real_receipt_from_apply_attempt_does_not_force_tier_two became
  test_real_receipt_from_apply_attempt_has_no_validator_support in that file.
  Same real attempt authoring; reads diagnosis_receipt directly instead of the
  removed snapshot. Preserves unavailable_single_attempt, nonempty hypotheses,
  and all-None scores; also asserts nonempty support_scores. The deleted
  normalizer's authority/dominance and gate's legacy-route assertions go.
- test_causal_disambiguation_end_to_end_acceptance retains all live repair,
  classification, posterior and cold-verification assertions. Removes only
  triaged.tier == one, triaged.decisive, triaged.tier_one_basis == legacy,
  event basis == legacy, causal_support_available == True and
  causal_support_authority_approved == False: these assert removed triage code.
  Real receipt authority/all-None assertions and the live causal repair gate stay.
- test_a_deterministic_sensor_earns_validator_owned_and_reaches_triage renamed
  to test_a_deterministic_sensor_earns_validator_owned_and_resolves_the_factor.
  All live sensor, classification, authority, factor resolution, idempotence and
  health assertions stay; only promoted.tier == one, basis == causal_authority
  and the triage event's authority-approved assertion go with the dead consumer.
- test_causal_lane_health_watches_both_tails_and_pins_the_tier_one_basis seeds
  a synthetic historical row via SQL instead of invoking the deleted writer.
  tier_one_events >= 1 becomes == 1 (stronger); basis uses the historical literal
  legacy_dominance instead of the removed constant. All other health assertions
  are unchanged; failure_triage_events_for is still exercised on stored events.
- test_event_replay_equivalence_after_full_walk uses GPR.advance to instructing
  instead of triage. The setup assertion drops equality to tr.routed_to and keeps
  projected state == instructing. Run replay/certification assertions stay intact.
No helper was edited. No assertion on surviving behavior was loosened.

Proof

All commands use the assigned scratch t.sh (tests, explicit paths, -q -n 4,
one command at a time) or py.sh (other Python/tools). Outputs are in that same
scratch directory. No live data, network, paid model, or other model session.

1. t.sh tests/test_registry_audit.py tests/test_architecture.py
   tests/test_identity_pins.py tests/test_retired_config_identities.py
   tests/test_test_layout.py tests/test_structure_ratchets.py
   tests/test_effective_defaults_golden.py tests/test_cli_help_snapshot.py -q -n 4:
   378 passed (44.29s), exit 0. Identity pins unchanged. All eight ratchet values
   equal their goldens: 186, 279, 46, 35, 35, 73, 2374, 184; no lowering needed.
2. t.sh tests/test_causal_attribution_p2.py tests/test_causal_p2_acceptance.py
   tests/test_p2_acceptance.py tests/test_triage_routes.py
   tests/test_voi_merge_composition.py -q -n 4:
   56 passed (4.52s), exit 0. Covers every edited/added test file and every
   surviving test file mentioning failure_triage. No edited helper dependents.
3. py.sh python scripts/affected_tests.py: exit 0, prints tests (whole suite).
   Reasons include Repository imported by conftest and the deleted module/tests;
   its default-main comparison also names the prior figures/service.py deletion,
   which this step did not change. The brief forbids running the whole suite,
   so used its explicit text-based fallback rather than passing tests to t.sh.
   Selected all 161 tests/test_*.py files mentioning voi_stopping, causal_health,
   causal_attribution, probe_episodes or parameter_registry (expanded path list
   in scratch affected-fallback.txt).
   Initial t.sh run used -q -n 4 without a marker filter. It was interrupted
   (exit 130) at 89%, with no final counts, after accidentally including the
   EVSI arc-close simulation. CLAUDE.md says only the arc-close gate runs those
   tests. The interrupted output is proof-affected.txt; it is not a pass.
   Second attempt: same 161 paths, -q -n 4 -m 'not arc_close'
   --tb=short --junitxml=<scratch>/affected-results.xml: interrupted (exit 130)
   at 89%, no final counts. Third attempt: same 161 paths, -q -n 4
   -m 'not arc_close' --tb=short -o faulthandler_timeout=120: interrupted
   (exit 130), no final counts. The diagnostic dumps identify unchanged
   Starlette TestClient.__enter__ -> AnyIO portal startup waits in
   tests/mobile_v2_plan_helpers.py:63 and
   tests/instruct_handoff_ih0_helpers.py:130 (the latter from
   test_ih6_workbench_open_item.py:669). The original pause cannot be attributed
   to the arc-close simulation: it recurred with that node excluded.

   Static test-helper import tracing identifies three selected files reaching
   those TestClient setups: tests/test_mobile_v3_probes.py,
   tests/test_ih6_workbench_open_item.py and
   tests/test_ih4_preferences_inform_router.py. Their complete results remain
   unverified. Read both helpers: startup waits before application lifespan,
   on unchanged code with no deleted triage API call. The exact environment
   cause of these hangs was not isolated; no product bug or regression was
   established and no assertion or helper was changed to get past them.

   Fourth attempt: explicit 158 remaining paths from scratch
   affected-without-testclient.txt, -q -n 4 -m 'not arc_close' --tb=short
   -o faulthandler_timeout=120: exit 1; 11623 passed, 34 skipped, 1 xfailed,
   22 failed in 303.67s. These 22 failures are sandbox restrictions, not counted
   as regressions. Twelve fail in socket.socket creating local fake HTTP
   servers: PermissionError [Errno 1] Operation not permitted. Ten in
   test_reader_rw2b_review.py derive from workbench.symbolic.run_checks falling
   back with sandbox_failed because bubblewrap cannot create a NETLINK_ROUTE
   socket. Reading those tests and the unchanged symbolic -> pf_sandbox path
   shows the failures would remain without this deletion; the direct socket
   failures occur in fake-server setup before exercising product behavior.

4. py.sh ruff check: exit 0, all checks passed.
5. py.sh lint-imports --no-cache: exit 0, 42 contracts kept, 0 broken.
6. git diff --check: exit 0, clean.
7. py.sh python, minimal run_sandboxed_python probe with a fixed print-only
   harness: Python exit 0; sandbox result exit 1, stderr exactly
   "bwrap: loopback: Failed to create NETLINK_ROUTE socket: Operation not permitted".
   No sandbox restriction was bypassed. The final ratchet-current probe also
   passed with all eight values unchanged; no golden or identity was written.

Sandbox-limited test nodes (12 direct socket denials, 10 bubblewrap denials):
  tests/test_probability_prep.py::test_decider_end_to_end_through_the_fake_endpoint
  tests/test_probability_prep.py::test_rate_limits_retry_within_caps_and_malformed_answers_fail_closed
  tests/test_reader_rw2b_review.py::test_f2_false_or_domain_dependent_identities_are_never_checked_as_holding
  tests/test_reader_rw2b_review.py::test_f2_exact_identities_and_decimals_keep_their_labels
  tests/test_reader_rw2b_review.py::test_f3_an_unrelated_checked_expression_never_validates_the_learners_step
  tests/test_reader_rw2b_review.py::test_f3_the_learners_own_expression_is_checked_and_decides_the_step
  tests/test_reader_rw2b_review.py::test_f10_a_check_appends_the_models_and_the_verifiers_verdicts_with_the_row
  tests/test_reader_rw2b_review.py::test_f14_a_hints_checkable_claim_is_verified_and_labelled_checked
  tests/test_reader_rw2b_review.py::test_f14_a_claim_that_does_not_hold_is_reasked_once_naming_it
  tests/test_reader_rw2b_review.py::test_f14_a_claim_failing_twice_falls_to_the_next_step_without_it
  tests/test_reader_rw2b_review.py::test_f3r_the_whole_written_relation_is_what_is_checked
  tests/test_reader_rw2b_review.py::test_f3r_an_operator_is_checked_on_its_written_operand_and_names_on_their_definitions
  tests/test_sidecar_tutor_qa.py::test_preview_tutor_opening_after_stop_diagnosing
  tests/test_sidecar_tutor_qa.py::test_preview_tutor_opening_without_decision_degrades_silently
  tests/test_sidecar_tutor_qa.py::test_sidecar_promote_tutor_question_dedup_route_is_idempotent
  tests/test_sidecar_tutor_qa.py::test_sidecar_promote_tutor_question_gap_rejected_in_library_context
  tests/test_sidecar_contract.py::test_sidecar_submit_attempt_never_falls_back_to_codex_when_routed_ai_unavailable
  tests/test_sidecar_contract.py::test_sidecar_canonical_codex_profile_wins_when_legacy_input_differs
  tests/test_sidecar_tutor_qa.py::test_sidecar_ask_rate_transcript_and_limit
  tests/test_sidecar_tutor_qa.py::test_sidecar_submit_attempt_counts_question_hint_equivalents
  tests/test_sidecar_tutor_qa.py::test_sidecar_save_tutor_answer_note_and_facet_question_counts
  tests/test_sidecar_tutor_qa.py::test_sidecar_ask_is_rejected_during_teach_back

Not verified: the three TestClient file results listed above, the excluded
arc-close multisim node, full landing gate, full suite, real-vault state, shadow rebuild or
planted-learner draw replay. No learner data or vault was read. No generated
architecture Reference was regenerated (orchestrator owns that). No commit,
staging, migration, identity-pin regeneration or structure-golden write occurred.
Sandbox limits are the 22 failures above. TestClient hangs are separately
unresolved; read-only git commands succeeded. No source-deletion stop, compared
identity change, ratchet rise, or new product bug beyond the required K9-5 residue
was found. The orchestrator still owns the full landing gate and Reference regen.
