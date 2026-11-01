# Reader follow-ups Nov 1

Stage `reader-followups-nov1`, branch `reader/followups-nov1` (base `2eb4bf6e61`, worktree
`learnanything-astrafix`). Four queued Reader/curriculum follow-ups, each with fail-first tests that name the
finding they close. **No migration, no successor, no config key, no new parameter; kill switches unchanged.**
Nothing here changes persisted meaning (scoring, scheduling, projections, serving): items 1 and 2 refuse more
requests at the boundary, item 3 narrows when the automatic C1 refresh may send or keep a judgment, item 4
bounds a transport request. No paid or live model call was made: every model in the tests is a fake, the
adapter tests run the real `openai` SDK over an in-memory httpx transport, and the Python run outside pytest
(the desktop catalog scripts) ran under `env -i` with empty, existing `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`. Cost: $0.

## 1. Whole-comparison provenance on the S3/S4 surfaces (RW4d's queued follow-up)

RW4d's record (`reader-workbench-RW4d.md`, open items): "the direct `compare_sources` RPC and
`instructional/tools.py` `_comparison_view` check only the displayed passages ... RW4d's own reads and writes
withhold the whole comparison."

- **Change.** `instructional.sources.refuse_withheld_comparison(vault, repository, comparison_id)` asks RW4d's
  own helper, `reader.source_objects.withheld_comparisons` (not a copy), and raises
  `PolicyRefused("comparison_withheld")` in RW4d's words when any contributing passage (sources, counterparts,
  dropped pins, the tutor question the comparison was asked for) is exam or held out now, or the provenance
  cannot be read (fail closed). A call that compared nothing (no comparison id) has nothing to withhold. It is
  applied:
  - on the **direct `compare_sources` RPC** (`handlers/source_service.py`): `comparison_withheld`, as
    `reader.library_compare` already says it;
  - on the **tutor's tool run** (`tools.execute_tool`, before `_comparison_view`): the run row is recorded
    `failed` with the code, and `run_source_tool` answers `comparison_withheld`. The view's per-passage filtering
    stays for everything else;
  - on **`find_sources(intent="compare")`** (`propose_sources`), which carries the whole comparison on its
    manifest. This covers the `find_sources` RPC, the tutor's `find_sources` tool with `intent="compare"` and the
    remote sources call (each already maps `PolicyRefused`).
- **Consequences, by RW4d's rulings.** Dropped pins count as contributing passages, so a direct comparison that
  pins exam material (or a passage that does not exist) is refused whole. A tutor comparison whose question
  passage became held out between the answer and the press is refused whole.
- **Tests.** `tests/test_whole_comparison_provenance_surfaces.py` (8):
  `…direct_rpc_refuses_a_comparison_whose_dropped_pin_is_exam_material`,
  `…direct_rpc_refuses_a_comparison_pinning_held_out_material`, `…direct_rpc_is_unchanged_with_nothing_protected`,
  `…rule_fails_closed_on_the_direct_rpc`, `…tutor_run_whose_question_passage_is_held_out_is_refused_whole`,
  `…tutor_run_with_nothing_protected_is_unchanged`, `…find_sources_compare_intent_applies_the_rule`,
  `…an_agent_callers_comparison_is_not_withheld_as_unresolvable` (the gate finding).

## 2. Extraction-qualified span keys on the reading-only Reader RPCs (CA6b landing open item 1)

CA6b's landing record (open item 1): "Extraction-qualified span keys for the reading-only RPCs, where the
reading id is the only provenance on the wire: `workbench.open` (problem spans, source exercise),
`reader.ask`, `set_answer_mode`, `route_intent`, `active_question`, both figure requests,
`reader.library_ask` and `enqueue_request`."

- **Server.** Each of those inputs takes `span_keys` (`extraction:span`; `workbench.open`'s source exercise
  and `figure.request`'s anchor too). The one guard is reused: `require_identity(...,
  reading_span_keys=...)` calls the new `source_identity.require_reading_span_keys`. With keys sent:
  - a key naming another reading than the request's is refused (`span_key_reading`), so a span id another book
    also has cannot be attributed to this one;
  - a bare id sent without its key is refused (`span_key_missing`), so the keys are the passages, not a
    decoration;
  - a key that names no reading is refused (`span_key`), and each keyed span must be a block of the reading
    (`span`).

  Nothing is written on a refusal (the typed `span_extraction_mismatch`, which the Reader already shows as
  "That passage belongs to another reading; reopen it."). A request with **no** keys is checked by membership
  as before. That keeps older callers and the CLI/tests working.
- **Desktop.** `readerShared.passageKeys(reading, spanIds)` names each passage with the reading it was taken
  in, and every app call to those RPCs sends `spanKeys` beside the bare ids:
  - Ask: the exchange's book (`about`, or the open render);
  - `AskOverlay`: its target;
  - answer mode: the open render;
  - intent box, active reading, figures (region included) and library ask: their pane's reading;
  - workbench "check me": the check's own `reading`;
  - exercises: the exercise's reading, and a source exercise's own.

  `reader.enqueue_request` has no desktop caller. No false refusal is possible on these flows: each key's
  reading is the reading the request names, and each key covers the bare ids sent.
- **Honest scope.** On today's desktop the keys are formed from the passage's `SourceIdentity` at the call
  site. For the pane-scoped hooks (intent box, active reading, figures) that is the same pane reading the
  request names, so the server check guards hand-crafted or mixed requests and pins the wire contract, as the
  CA6b round-6 raw-selection precedent does. The check's own reading is a genuinely separate statement for
  "check me". Stamping each selection with the reading it was captured in is listed below as an open question.
  It would let a stale selection under a changed render be caught on the client's own evidence, but it is a
  refactor of the selection setters and every hook that takes span ids.
- **Tests.** `tests/test_reader_qualified_span_keys.py` (31), on the CA6b round-6 `twins` (two books that both
  have `s0..s2`):
  - the helper test;
  - for each of the 10 requests (the 9 RPCs, `workbench.open` twice): a colliding id keyed to the other book
    is refused with nothing written, and a bare id without its key is refused;
  - keys naming the request's own reading, and no keys, pass the guard.

  Vitest: the exact-argument expectations of 12 files now carry the keys
  (`sideBySideIntent`, `comparePointTableCodexReview`, `nextStepFold`, `rw1bReview`, `figuresWithReadingPath`,
  `figures/{advancedPanels,FigureInline,libraryOfferSettle,readerFigures,showMe,tutorOfferPress}`, and
  `tutorBoundAsk` through the shared fixture `readerBoundOffersOnlyAsk.json`). That fixture's pytest replay
  (`test_reader_rw1c_review.py::test_the_desktops_offers_only_bound_ask_refuses_tools_when_cold`) now sends
  `spanKeys` through the real handler.

## 3. Curriculum C1 round-5 ruling follow-ups (a) and (b)

From the C1 record's round-5 ruling (verify `20261101-034720-G33NFM`, both Low).

- **(a) "pass the precheck's resolved route into judge()".**
  - `deliverable_path.path_route(..., plan_only=True)` resolves the path judge's route once in
    `refresh_for_plan`. It checks that route (`ChatRoute.plan_only_problem`: `not_plan_route`) and passes it into
    `judge(route=...)`, which sends on exactly that route.
  - `ChatRoute(plan_only=True)` also holds the **exact client that sends** to the plan. A resolved (or injected)
    client whose `provider_type` is not `chatgpt_plan` raises `RouteUnavailable("not_plan_route")` before any
    request.
  - The Guide's own judgment (`plan_only=False`) keeps its route rules.
  - `plan_refresh_route_problem` keeps its signature.
- **(b) "evaluate the gate inside the same snapshot validation".**
  - `SC.CoverageGuard(gate=...)` asks the caller's gate of the snapshot it validates. The gate's verdict counts
    only if that snapshot is still the published generation. A reload between the gate's read and the admission
    is read again, and a gate that cannot be read admits nothing.
  - A closed gate raises `SC.GateClosed` (a `ProtectionChanged`, so no layer retries or relabels it), and
    `judge` reports it as `switched_off`. `_GatedGuard` is gone; `deliverable_path._GateOff` is `SC.GateClosed`.
  - `still_wanted` now receives the snapshot's vault (`None` before the claim: the vault as it is now). The
    sidecar's `gate_on(now_vault=None)` reads its loaded vault only when none is given.
  - The two round-5 tests' gates take that argument.
- **Tests.** `tests/test_curriculum_c1_round5_followups.py` (6):
  - `…a_the_refresh_resolves_its_route_once_and_judge_sends_on_it` (one resolution of `deliverable_path_judge`;
    before, two);
  - `…a_a_metered_client_behind_a_plan_route_sends_nothing` (the planned route is the plan, the resolution hands
    back a metered client: 0 calls, `not_plan_route`; before, 1 call);
  - `…a_a_guide_judgment_keeps_its_route_rules`;
  - `…b_a_reload_right_after_the_gates_read_cannot_slip_into_the_admission` (a provider with the sidecar's
    `snapshot`/`admit`; the reload that turns C1 off lands right after the gate's read: 0 calls; before, the
    request was sent and only the write was refused);
  - `…b_the_gate_reads_the_admitted_snapshots_vault`;
  - `…b_an_unreadable_gate_admits_nothing`.

## 4. A total transport deadline in the OpenAI-compatible chat adapter (RW6b part 2, F3 / ruling R3)

RW6b part 2's open item 1: "The request timeout is per network operation, so a narrator that freezes or dies
mid-request can be taken over while its response still arrives ... An abortable total deadline belongs to the
AI transport layer."

- **Change (`ai/providers/openai_chat.py`, so `openrouter` too).**
  - Each physical request is sent on a worker thread (contextvars copied). The caller waits for it at most the
    attempt's timeout (the remaining time of the loop's deadline, floor `_MIN_ATTEMPT_SECONDS`).
  - Past that, the request is aborted and the attempt fails with `TotalDeadlineExceeded` (a `TimeoutError`;
    the existing retry loop never retries past its deadline). An httpx response hook (`_arm_deadline`, on the
    SDK's own `DefaultHttpxClient` defaults) tracks the response stream so the abort closes it, and a body still
    arriving raises `ReadTimeout` at its next chunk.
  - An abandoned worker's late answer is never returned or metered.
  - `transport=` is a constructor test seam (an in-memory httpx transport). With the offline stand-in `openai`
    module the suite uses elsewhere (no `DefaultHttpxClient`), the deadline is not armed and those tests are
    unchanged.
- **reader_digest.** `narration_lease_seconds(t) = ceil(openai_chat.enforced_total_seconds(t)) +
  CLAIM_LEASE_SECONDS`, documented as the enforced bound plus the claims' liveness margin (`keep`, unchanged).
  This equals the old number for every `t > 0`; the claim comment now says what is enforced. A live holder's
  request is aborted at the route's timeout, so a dribbling response can no longer hold the claim or run past
  the lease. A frozen or dead process cannot abort anything; that worst case stays R3's (fenced, at most one
  duplicate metered charge within `digest.max_daily_cost_usd`).
- **Tests.** `tests/test_chat_total_transport_deadline.py` (5), all through the real adapter and SDK over
  `httpx.MockTransport`:
  - `…a_dribbling_response_is_aborted_at_the_total_deadline`: a valid completion dribbled over ~5 s with every
    read inside the per-operation timeout. The call fails within the bound + 0.75 s, one physical request, its
    stream closed before the body ended, no worker left;
  - `…a_prompt_response_is_unchanged`;
  - `…the_bound_is_the_attempts_timeout_with_its_floor`;
  - `…the_narration_lease_is_the_enforced_bound_plus_the_claim_margin`;
  - `…a_dribbling_narration_request_ends_inside_its_lease_and_publishes_nothing`: `narrate_digest` with the real
    adapter as its client, `ai.timeout_seconds = 1`, priced. Each physical request is aborted within the bound
    and inside the lease, and no narrative is published.

## Fail-first evidence

The new test files were run against the base sources (`git archive 2eb4bf6e61 src migrations` on
`-o pythonpath=`, tests from the tip): **46 failed, 3 passed** of the 49 at that point. The 3 that pass on the
base are the deliberate "unchanged" pins (`…direct_rpc_is_unchanged_with_nothing_protected`,
`…tutor_run_with_nothing_protected_is_unchanged`, `…a_guide_judgment_keeps_its_route_rules`). By item:
- **1:** the refusals did not happen (`DID NOT RAISE`), and the base never consulted RW4d's helper (the
  fail-closed case).
- **2:** the base has no `require_reading_span_keys`, and refuses `spanKeys` as an unknown field. A colliding id
  sent bare is accepted by the base's membership check: that is the gap.
- **3:** two route resolutions; a metered client sends (1 call); the reload slips into the admission (1 call);
  the gate is never handed the snapshot.
- **4:** no `transport=` seam and no `enforced_total_seconds` on the base. Before, a dribbling response held the
  request for as long as the body took; the per-operation timeout never fired.

The 7th item-1 test (the agent-caller regression below) was written after the gate found the bug.

**Gate finding fixed in-stage.** The targeted run failed 2 tests in
`test_tool_results_withhold_answers.py`. RW4d's `comparison_passages` read every non-tutor caller's ref as a
reading, and every tool run's ref as a question. An agent's comparison (ref `cli`) was therefore
"unresolvable" and refused whole by item 1's new checks (and, after the run row existed, on every later read).
The helper now reads only a Reader caller's ref as a reading and only tutor runs as questions; other callers'
refs name no passage. This was fixed in RW4d's helper, not forked:
`test_rw4d_followup_an_agent_callers_comparison_is_not_withheld_as_unresolvable`. A tutor or Reader comparison is
unchanged: RW4d's own suites pass.

## Gate

Every pytest, vitest and npm command ran in `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G`, one at a time, with pytest at `-n 6` at most and vitest at `--maxWorkers=4`. The big
targeted run waited behind `flock /tmp/learnloop-fullsuite.lock`. `TMPDIR` was the stage scratch directory,
outside the worktree.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **36 kept, 0 broken** (on the final tip) |
| targeted pytest, 337 files (below), `-n 6` | **6485 passed, 2 failed, 11 skipped, 2 xfailed** (15 min 48 s); the 2 are the gate finding above |
| after the fix: every test file naming `run_tool`, `run_requested_tool`, `run_source_tool`, `comparison_passages`, `withheld_comparisons`, `kept_comparisons`, `library_compare`, `source_objects` or `compare_sources` (51 files, including the 2 failing ones and `test_whole_comparison_provenance_surfaces.py`) | **1329 passed, 1 skipped** |
| earlier iteration runs (kept for the record): `test_curriculum_*`, `test_deliverable_*`, `test_section_coverage*`, `test_coverage_*`, `test_judge_routes` | 295 passed |
| durability lane | not run: no migration, no DB/connection code |
| `npm install`; `npm run typecheck` | ok; clean |
| vitest, 100 files (below) | **1068 passed** (100 files). The first run, before the expectations were updated, had 41 failures in 12 files, all exact-argument assertions missing `spanKeys` |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check` | not needed: nothing under `src-tauri` changed |
| DB reference scripts | not needed: no schema change |
| `desktop_generate.py` / `desktop_validate.py` (under `env -i`) | regenerated on the committed tree; validation passed (295 TS / 287 entry-build / ACTIVE 300, unchanged: no new file) |

**Process notes.**
- Two one-line `uv run python -c "import ..."` checks ran outside `env -i`: an import smoke test of the
  handlers, and printing `learnloop.__file__` under the base path. They loaded modules only, opened no vault,
  and made no network call.
- One single-test pytest diagnostic (base sources, the helper test) ran without the memory scope.
- Nothing else ran outside the rules.

**Pytest files (337):** test_ad1_fix_round4.py, test_ad1_migration.py, test_ad23_contract.py, test_ad23_migration.py, test_ad23_t1_routes.py, test_ad3_relatedness.py, test_adaptive_difficulty_ad1.py, test_agent_run_tokens.py, test_ai_config.py, test_ai_runtime.py, test_ai_single_request.py, test_approach_maps.py, test_approach_maps_schema.py, test_architecture.py, test_attach_to_family.py, test_attempt_ai_flow.py, test_attempt_completion.py, test_auto_build_spend_report.py, test_canonical_exercise_serialization.py, test_causal_p2_acceptance.py, test_chat_total_transport_deadline.py, test_cli_help_snapshot.py, test_codex_output_schema.py, test_commitment_arcs.py, test_commitments.py, test_compare_keep_switch_off.py, test_compare_methods.py, test_compare_sources_keep.py, test_compare_sources.py, test_concept_animation_service.py, test_concepts.py, test_config_refactor.py, test_confusable_concepts.py, test_contamination_report.py, test_contract_commissioning.py, test_controller_cutover.py, test_controller_ownership.py, test_coordinated_migrations.py, test_coverage_denominator_boundary.py, test_coverage_on_extract.py, test_cross_seam_exposure.py, test_curriculum_c0b_landing.py, test_curriculum_c1_codex_review_fixes.py, test_curriculum_c1_fix_round2.py, test_curriculum_c1_fix_round3.py, test_curriculum_c1_fix_round4.py, test_curriculum_c1_fix_round5.py, test_curriculum_c1_landing.py, test_curriculum_c1_plan_follows_path.py, test_curriculum_c1_round5_followups.py, test_curriculum_locks.py, test_daily_loop_golden_path_lifecycle.py, test_daily_loop_reader_authored_practice.py, test_daily_loop_reference_adoption.py, test_deferred_regrade.py, test_deliverable_codex_review.py, test_deliverable_curriculum_migration.py, test_deliverable_path.py, test_deliverable_rpcs.py, test_deliverable_scope.py, test_depth_transition.py, test_desktop_rpc_contract.py, test_diagnose_review.py, test_diagnose_review_spend.py, test_diagnosis_input_provenance_landing.py, test_diagnosis_isolation.py, test_diagnostic_augmentation.py, test_diagnostic_pack.py, test_discriminating_search.py, test_dl2_rw4b_keyed_pick_check.py, test_doctor.py, test_dual_authority_administration.py, test_e0_paid_fakes.py, test_e0_review_round1.py, test_e0_review_round2.py, test_e0_review_round3.py, test_e0_review_round4.py, test_embedding_backfill.py, test_embedding_route_isolation.py, test_embedding_store.py, test_exam_protection_identity.py, test_exam_protection.py, test_exam_protection_review.py, test_exercise_arm.py, test_facet_locks_landing.py, test_facet_reword_confirm.py, test_facet_reword_confirm_review.py, test_facet_rewords.py, test_failure_triage_causal_gate.py, test_failure_triage.py, test_family_proposals.py, test_figure_offers.py, test_figure_region.py, test_figures_final_round.py, test_figures_rpc.py, test_figures_rw5b_fix_round2.py, test_figures_rw5b_review.py, test_figures_scope_redesign.py, test_figures_show_me_codex_review.py, test_figures_show_me.py, test_find_sources_intents.py, test_golden_path_assessment.py, test_golden_path_confirm.py, test_golden_path_fixture.py, test_golden_path_run.py, test_graph_edit_proposals.py, test_held_grade_evidence.py, test_help_assists_schema.py, test_help_outcomes.py, test_hint_h2b_fix3.py, test_hint_h2b_fix4.py, test_hint_h2b_rereview.py, test_hint_h2b_review.py, test_hint_outcome.py, test_hypothesis_reference_contract.py, test_import_split_parity.py, test_ingestion_checkpoints.py, test_ingest_jobs.py, test_ingest_runner.py, test_ingest_transcription.py, test_instructional_layering.py, test_integration_backfill.py, test_intent_checks.py, test_intent_codex_review.py, test_intent_exclusion.py, test_intent_fix_round4.py, test_intent_goal_deadline.py, test_intent_orchestrator_rulings.py, test_intent_resolution.py, test_interaction_signals.py, test_intervention_outcomes_replayer.py, test_journey6.py, test_judge_routes.py, test_keep_local_retired.py, test_key_ladder_labels.py, test_learner_claim_application_migration.py, test_learner_claim_superseded_migration.py, test_learner_pick_proposal.py, test_learner_text_gaps_review.py, test_library_ask_expand.py, test_library_ask.py, test_library_ask_review.py, test_library_asks_migration.py, test_library_exercises.py, test_lo_general.py, test_maintenance_feed.py, test_mcp_c1a_narrow.py, test_mcp_c1a_review.py, test_mcp_cli.py, test_mcp_tools.py, test_method_explicit_landing.py, test_migrations.py, test_mobile_allowlist.py, test_model_usage_report.py, test_multimodal_client.py, test_native_media_readiness.py, test_openai_chat_client.py, test_openai_embedding_client.py, test_openrouter_client.py, test_openrouter_video_client.py, test_output_budget.py, test_owner_capture_1025.py, test_p2_acceptance.py, test_p2_leakage_suite.py, test_p3_journeys.py, test_passage_links.py, test_pattern_ladder.py, test_pf_generation.py, test_pinned_span_bridge.py, test_plan_first_transport_grant_scope.py, test_plan_first_transport_offer_grants.py, test_plan_first_transport_offer_grants_r5.py, test_plan_first_transport_paid_roles.py, test_plan_first_transport.py, test_plan_first_transport_today_quiet.py, test_plan_follows_path.py, test_practice_availability.py, test_practice_index_paid.py, test_practice_information.py, test_practice_item_quality_gates.py, test_practice_proposal_caller_columns.py, test_prescription_passages.py, test_probability_cli.py, test_probability_prep.py, test_project_cli.py, test_proposal_impressions.py, test_provider_resolution_parity.py, test_public_tip_guards.py, test_reader_active_reading.py, test_reader_adoption_ownership.py, test_reader_authoring.py, test_reader_branches.py, test_reader_ca1_as_printed.py, test_reader_ca1_astra_codex_review.py, test_reader_ca1_astra_fixes.py, test_reader_ca1_astra_redesign.py, test_reader_ca1_astra_rereview.py, test_reader_ca1_codex_review.py, test_reader_ca2_astra_handoff.py, test_reader_ca2_astra_handoff_recovery.py, test_reader_ca2_codex_rereview.py, test_reader_ca2_codex_review.py, test_reader_ca2_fix_orchestrator.py, test_reader_ca2_one_ask.py, test_reader_ca3_codex_rereview.py, test_reader_ca3_codex_review.py, test_reader_ca3_codex_round3.py, test_reader_ca3_compare_anywhere.py, test_reader_ca3_landing_ca5a.py, test_reader_ca4_landing.py, test_reader_ca4_table_by_point.py, test_reader_ca5a_find_section.py, test_reader_ca5_also_in_books.py, test_reader_ca5_landing.py, test_reader_ca6_side_by_side.py, test_reader_compare_table.py, test_reader_dialogue.py, test_reader_digest_narrative.py, test_reader_find_sources_callers.py, test_reader_followups.py, test_reader_followups_rereview.py, test_reader_followups_review.py, test_reader_followups_round3.py, test_reader_followups_round4.py, test_reader_followups_round5.py, test_reader_followups_round6.py, test_reader_followups_round7.py, test_reader_followups_round8.py, test_reader_followup_valuation.py, test_reader_formative_texts.py, test_reader_guidance.py, test_reader_inquiry_kill_switch.py, test_reader_inquiry_status.py, test_reader_intentions.py, test_reader_intent.py, test_reader_qualified_span_keys.py, test_reader_reconnect.py, test_reader_reconstruct.py, test_reader_rw1b_fix_round4.py, test_reader_rw1b_review.py, test_reader_rw1c_review.py, test_reader_rw2b_fix12.py, test_reader_rw2b_fix4.py, test_reader_rw3a_landing.py, test_reader_rw3b_migration.py, test_reader_rw3b_review_fixes.py, test_reader_rw6b_landing.py, test_reader_rw6b_p2_landing.py, test_reader_rw7a_migration.py, test_reader_session_digests_migration.py, test_reader_source_identity_guard.py, test_reader_tutor_offers.py, test_reader_tutor_retrieval.py, test_reader_tutor_switch_off.py, test_reader_workbench_rw2a.py, test_reading_hardening_landing.py, test_reading_paths.py, test_recurrence_benchmarks.py, test_reference_check_binding.py, test_reference_gate_imports.py, test_registry_audit.py, test_required_method_authority.py, test_required_method_reopened.py, test_required_method_rereview.py, test_required_method_round3_final_verify.py, test_required_method_round3.py, test_required_method_round3_rereview.py, test_required_method_round3_review.py, test_reread_safety_landing.py, test_reread_safety.py, test_retrieval_interventions_write_points.py, test_retrieval_spaces_migration.py, test_roles_judges.py, test_roles_switch_off_legacy_parity.py, test_roles_switch_off.py, test_router_p2_bridge.py, test_router_r2a_landing.py, test_router_r2a_serving.py, test_router_r2bc_landing.py, test_router_r2b_serving.py, test_router_reader_activity.py, test_router_staged_p2.py, test_rw2c_fix_round2.py, test_rw2d_receipts_migration.py, test_rw4d_rw3b_composition.py, test_rw4_kill_switches.py, test_section_coverage_migration.py, test_section_coverage.py, test_section_coverage_review.py, test_section_coverage_rpcs.py, test_sidecar_golden_path_assessment.py, test_sidecar_idle_threads.py, test_sidecar_ingest_m3.py, test_sidecar_reader_p3_slice2.py, test_sidecar_reader.py, test_sidecar_serializer_snapshot.py, test_source_exercise_import.py, test_source_exercise_rpcs.py, test_source_first_needs.py, test_source_ingestion.py, test_source_retrieval_rereview_cost.py, test_source_service_spend_accounting.py, test_source_service_spend_envelopes.py, test_source_sets.py, test_sources_merge_composition.py, test_sources_outcomes_report.py, test_source_space_resolver.py, test_spend_controls.py, test_sqlite_file_copies.py, test_staged_policy.py, test_state_signals.py, test_structured_transport_parity.py, test_subject_registry.py, test_surface_pool.py, test_synthesis_manifests.py, test_t1_batch_origin_migration.py, test_t6_followup_composition.py, test_t6_followup_review.py, test_table_roles.py, test_task_blueprints.py, test_tool_dispatch_policy.py, test_tool_registry.py, test_tool_results_withhold_answers.py, test_tools_cli.py, test_tracked_fixture_databases.py, test_tui_feedback.py, test_tutor_practice_request.py, test_tutor_tool_requests.py, test_ux_phase1_landing.py, test_ux_phase1_review_fixes.py, test_ux_phase1_usability_round1.py, test_ux_phase3_today.py, test_ux_phase4_feedback.py, test_valuation_calibration_fields.py, test_whole_comparison_provenance_surfaces.py, test_workbench_check.py, test_workbench_route_example.py.

**Vitest files (100):** app/App.fixRound2.test.tsx, app/App.fixRound3.test.tsx, app/App.fixRound4.test.tsx, app/App.fixRound5.test.tsx, app/App.shell.test.tsx, app/App.today.test.tsx, app/App.wrapUpSkim.test.tsx, app/classicIsBase.test.ts, app/keymap.test.ts, app/shellChrome.test.ts, c/AskOverlay.capture.test.tsx, c/AskOverlay.panel.test.tsx, c/AskOverlay.reader.test.tsx, c/AskOverlay.steps.test.tsx, c/AskOverlay.suggestion.test.tsx, c/AskOverlay.test.tsx, c/ShellNav.test.tsx, c/SourceOffers.test.tsx, s/attentionBudget.test.tsx, s/PracticeScreen.adaptiveHandoff.test.tsx, s/PracticeScreen.asPrinted.test.tsx, s/PracticeScreen.ca2OneAsk.test.tsx, s/PracticeScreen.firstHintRestore.test.tsx, s/PracticeScreen.ownerCapture1025.test.tsx, s/PracticeScreen.test.tsx, s/PracticeScreen.workbench.test.tsx, s/reader/alsoInBooksReader.test.tsx, s/reader/checkOffer.test.ts, s/reader/compareKeepSwitchOff.test.tsx, s/reader/compareKeep.test.tsx, s/reader/comparePointTableCodexReview.test.tsx, s/reader/comparePointTable.test.tsx, s/reader/compareScopeCodexReview.test.tsx, s/reader/compareScope.test.tsx, s/reader/figures/advancedPanels.test.tsx, s/reader/figures/figureGrammar.test.ts, s/reader/figures/FigureInline.test.tsx, s/reader/figures/libraryOfferSettle.test.tsx, s/reader/figures/readerFigures.test.tsx, s/reader/figures/showMe.test.tsx, s/reader/figures/sketch/SketchFigure.test.tsx, s/reader/figures/sketch/sketchSandboxReview.test.tsx, s/reader/figures/tutorOfferPress.test.tsx, s/reader/figuresWithReadingPath.test.tsx, s/reader/findSectionByPoint.test.tsx, s/reader/findSectionReader.test.tsx, s/reader/intentBoxInShell.test.tsx, s/reader/IntentBox.test.tsx, s/reader/intentSwitchOff.test.tsx, s/reader/libraryAskJobs.test.tsx, s/reader/libraryAskSwitchOff.test.tsx, s/reader/libraryAsk.test.tsx, s/reader/libraryExercisesReader.test.tsx, s/reader/libraryExercises.test.tsx, s/reader/libraryRoles.test.tsx, s/reader/nextStepFold.test.tsx, s/reader/paletteAskPostures.test.tsx, s/reader/paletteAsk.test.tsx, s/reader/readerHooks.parity.test.tsx, s/reader/readerWorkbenchExercise.test.tsx, s/reader/readerWorkbenchQueue.test.tsx, s/reader/readerWorkbenchResume.test.tsx, s/reader/readingPathsReader.test.tsx, s/reader/readingPathsRefresh.test.tsx, s/reader/readingPathsSwitchOff.test.tsx, s/reader/recapSwitchOff.test.tsx, s/reader/rw1bReview.test.tsx, s/ReaderScreen.branches.test.tsx, s/ReaderScreen.checkOffer.test.tsx, s/ReaderScreen.cuesSwitchOff.test.tsx, s/ReaderScreen.discoveredCuesReview.test.tsx, s/ReaderScreen.discoveredCues.test.tsx, s/ReaderScreen.doseOffer.test.tsx, s/ReaderScreen.followsLearner.test.tsx, s/ReaderScreen.guide.test.tsx, s/ReaderScreen.inquiryOff.test.tsx, s/ReaderScreen.inquiry.test.tsx, s/ReaderScreen.k7.test.tsx, s/ReaderScreen.marginMarksReview.test.tsx, s/ReaderScreen.marginMarks.test.tsx, s/ReaderScreen.parity.test.tsx, s/ReaderScreen.pdfSelection.test.tsx, s/ReaderScreen.preparing.test.tsx, s/ReaderScreen.quickcheck.test.tsx, s/ReaderScreen.recapReview.test.tsx, s/ReaderScreen.recap.test.tsx, s/ReaderScreen.review.test.tsx, s/ReaderScreen.rw2cExample.test.tsx, s/ReaderScreen.workbench.test.tsx, s/reader/sideBySideCorrespondence.test.tsx, s/reader/sideBySideIntent.test.tsx, s/reader/sideBySideReader.test.tsx, s/reader/tutorBoundAsk.test.tsx, s/reader/tutorExercises.test.tsx, s/reader/tutorReader.test.tsx, s/reader/tutorSwitchOff.test.tsx, s/reader/voices.test.tsx, s/RepairOverFeedback.phase4.test.tsx, s/today/TodayPlace.test.tsx, s/workbench/switchOff.test.tsx.
(`s/` = `src/screens/`, `c/` = `src/components/`.)

## Commits

- `d00d7593c1`: item 1 (helper, RPC, tool run, `find_sources(compare)`; tests).
- `780e611e82`: item 4 (adapter deadline, narration lease; tests).
- `6cb737bb81`: item 3 (route passed into `judge`, plan-only on the client, gate in the guard's snapshot; tests;
  the round-5 tests' gates take the snapshot's vault).
- `e54b064acd`: item 2, server (inputs, guard; tests).
- `0e255d2058`: item 2, desktop (`passageKeys`, call sites, vitest expectations, the bound-ask fixture and its
  pytest replay).
- `49491f0a3e`: desktop catalog regenerated on the committed tree.
- `71f0760ec3`: the gate finding (RW4d's helper and non-Reader/tutor callers; regression test).
- this record.

## Open questions

1. **Per-selection provenance on the desktop (item 2).** Should each Reader selection be stamped with the
   reading it was captured in? That would make `spanKeys` a second, independent statement in every flow, so a
   stale selection under a changed render or another pane is refused on the client's own evidence. The cost is
   a frontend refactor of the selection setters and every hook that takes span ids. Should keys then become
   required (bare ids refused)? That would also close the hand-crafted-RPC case CA6b's round-6 ruling rated Low.
2. **Item 1's reach.** `find_sources(intent="compare")` was included beyond the two named surfaces, because it
   carries the whole comparison on its manifest. Is that wanted? (The remote/MCP sources call maps the refusal
   to `SourcesUnavailable("comparison_withheld")`.)
3. **Item 4's reach.** The total deadline is enforced in the OpenAI-compatible adapter only (the metered
   routes). The ChatGPT-plan, Codex, Decider and HTTP-adapter transports keep their own timeouts. The plan is
   unmetered, so R3's duplicate-charge concern does not apply to it.

## Landing onto main

The branch `reader/followups-nov1` (worktree `learnanything-astrafix`, stage tip `09d5d3e8c8` after the Codex fix
round and re-review fix round) lands onto main. The orchestrator fast-forwards main and pushes. Codex state at landing:
F1 [High] CONFIRMED-FIXED (job `20261101-101104-SYlL5G`); F2 [Medium] REOPENED only for the HTTPS-proxy TLS-in-TLS
read path (ruled Low, R1 below).

### Merges

- `13bc3f75bf`: main `0708e12a18` (substrate facet write-on-change: `src/learnloop/db/repositories.py`, its test and
  its two records) merged into the branch (a merge, not a rebase). No file is touched by both sides, so there was no
  conflict. Main's tip was still `0708e12a18` before the full gate and again before this record was committed.
- No regeneration was needed beyond the desktop catalog: no schema, config key or template change, so the DB and
  config reference scripts were not run. `desktop_generate.py` then `desktop_validate.py` (under `env -i`) on the
  merged tree: **validation passed** (295/295 TypeScript/TSX + 5/5 Rust, 24 area maps, ACTIVE=300, reproducible
  byte-for-byte); the regeneration changed no file.

### Gate (at `13bc3f75bf`)

Every Python run under `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, `TMPDIR` outside
the worktree. Every pytest run inside `systemd-run --user --scope` (full suite 10G/2G swap, the rest 5G/1G) under
`flock /tmp/learnloop-fullsuite.lock`; every npm/vitest run in a 5G scope, vitest `--maxWorkers=4`. No live model call.

- `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- **Full pytest** (`-n 8 --dist worksteal`, `faulthandler_timeout=600`): **23158 passed, 89 skipped, 47 xfailed, 0
  failed** (37:09).
- **Durability lane** (`-m durability`, `-n 6`): **178 passed, 1 skipped**.
- **Owner lane** (`-m owner_vaults`, `-n 6`, `LEARNLOOP_OWNER_VAULTS` = fresh backup-API copies,
  `learnloop.db.copies.copy_tree_with_databases`, of `learnanything-ad1/fixtures-local/owner-copies-mvp035/{linear_algebra,
  probability,arxiv_v2}` in the gitignored `fixtures-local/landing-fu-nov1/`): **83 passed, 2 failed, 4 skipped**. The
  failures are exactly the two known ones, `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events`
  and `test_placement_fixture_copies::…[arxiv_v2]`.
- **Frontend:** `npm install` ok; `npm run typecheck` clean; `npm run frontend:build` built (the usual chunk-size
  warning). Whole vitest: the first run had **1 failed, 2341 passed** (245 files):
  `sideBySideCorrespondence.test.tsx` > "(iv) peek, side by side and go there each record once" (line 142, a `waitFor`
  on the also-list focus). The file alone passed **3 of 3** (11/11); the branch changes neither it nor
  `AlsoInBooks.tsx`. A second whole run failed one different test, the known load-timing flake
  `FeedbackScreen.test.tsx` > "keeps the old Next where no live queue applies" (a spy called 0 times; recorded in
  H1's and reread-safety's landings); that file alone passed **3 of 3** (11/11). The third whole run: **245 files,
  2342 passed, 0 failed**. Both are recorded as load-timing flakes.
- `cargo check`: not needed (nothing under `src-tauri` changed).

### Smoke on fresh owner copies (`fixtures-local/landing-fu-nov1-smoke/`, drivers `scripts/prep.sh`, `scripts/rpc.sh`)

**Setup.** Fresh backup-API copies of the three mvp035 owner copies, neutralized under each side's own code
(`neutralize3.py`: every route at the `127.0.0.1:9` blackhole, key variable unset; rewrite, rerank, dense and
embeddings off). Main's code is `git archive 0708e12a18` and the branch's `git archive 13bc3f75bf`, both with `src/`
and `migrations/`. Each copy, under its own side's code: a bare `upgrade` (**mvp-0.35 → mvp-0.40**, head 228), the
desktop start (`SidecarContext.load`), `migrate_vault` (0 applied), `rebuild-derived-state`. Every process ran under
`env -i` with empty `HOME`, `CODEX_HOME` and config dir and an audit hook that refuses non-loopback sockets and Codex
process starts.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| upgrade, desktop start, rebuild-derived-state (main and branch) | mvp-0.35 → mvp-0.40, ok (70 attempts) | same (3) | same (3) |
| Today (3 queue variants, frozen clock), branch vs main | **identical** (525,266 bytes) | identical (740,827) | identical (344,204) |
| daily plan dump (deterministic ids), branch vs main | **identical** (84,711 bytes) | identical (124,036) | identical (32,448) |
| readings with a ready render view / span ids shared by two books | 3 / 160 | 2 / 10 | 4 / 125 |

**Reading-only Reader RPCs (item 2)** (`rpc_smoke.py`, through the sidecar's own handlers on a further copy of each
side's rebuilt vault, real reader data). The request names book A's reading and a span id that book B also has.

| RPC | another reading's key (`B:span`) | own key (`A:span`) | no keys, branch | no keys, main |
|---|---|---|---|---|
| `reader.set_answer_mode` | refused `span_extraction_mismatch` / `span_key_reading`, nothing written | ok (`interaction_events`) | ok | ok |
| `reader.ask` | refused, `span_key_reading`, nothing written | passes the guard; `provider_unavailable` (blackhole, before any write) | same | same |
| `reader.route_intent` (empty text: no model call) | refused, `span_key_reading`, nothing written | ok, nothing written | ok | ok |
| `reader.active_question` (`why_step`) | refused, `span_key_reading`, nothing written | ok (`interaction_events`) | ok | ok |

Identical on all three vaults. "Nothing written" is every table's row count unchanged. The no-key outcomes (outcome,
code, tables changed) are identical between main's and the branch's code on every vault.

**`compare_sources` (item 1).** A comparison needs two model steps (the passage verification and the comparison
call). With routes at the blackhole they end before a comparison is stored, so nothing would reach RW4d's rule. The
smoke therefore replaces those two steps **in process** with deterministic doubles: every retrieved passage is judged
"answers", and the comparison quotes each passage's first words. The doubles use no client and no network, and do no
metering. Retrieval (the real FTS index), pin admission, storage, reuse and the whole-comparison rule are the real code.
The same doubles ran under main's code.

- **Allowed when nothing is withheld**, on all three vaults: a `reader` caller (ref = a reading) and a `plan` caller
  each make a fresh comparison (2, 2–3, or 10–12 sources), then the same call again reuses it. All 4 cases return `ok`
  with a comparison id (fresh: `reused` false, one `source_comparisons` row; reuse: `reused` true, nothing written).
  Each is identical to main's outcome (8/8 per vault).
- **Exam material:** **no owner copy has exam or held-out material** (`exam_material`: 0 spans, 0 whole readings on
  all three), so the owner data cannot exercise the refusal. As a supplement, a further copy of each side's arxiv_v2
  marked one non-Reader reading's outline role as `exam` (`source_unit_selections.role_override`, one row; the
  import-batch path that `exam_material` reads). The comparisons then leave that reading out (10/11 sources, the same
  on both sides). Pinning one of its passages onto the plan caller's comparison gives:
  - **branch:** refused **`comparison_withheld`**, with no row added;
  - **main:** shown, as a reuse, with the pin dropped as "it is exam material". This is the Codex F1 gap on main.

  The other 8 cases are identical between the two sides.
- `rebuild --shadow --json` after the RPCs and comparisons (branch copies, including the marked one): **0/0/0** on
  every vault, live unchanged. Also **0/0/0** on each upgraded, rebuilt branch copy before the RPCs.
- **Model call receipts:** across the 20 smoke databases compared with their base copies, **0 new**. probability's 56
  historical rows (42 completed, 14 failed) are unchanged in each copy.
- **Audit:** the audit log was never written, so there was no process start and no socket connect of any kind. No
  Codex process ran.

### Orchestrator rulings (verbatim)

- R1 (F2 remainder): "Ruled Low under the proportionate protection bar and the stuck-loop rule (third round on the transport-deadline class). It needs an HTTPS_PROXY environment variable naming an https:// proxy, which the owner does not configure; the overshoot is bounded by the proxy's per-recv pacing; a duplicate narration needs a priced metered route under digest.max_daily_cost_usd 0.25. Queued as a follow-up: bound nested TLS I/O, or set trust_env=False on the metered adapter's client."
- R2: "find_sources(intent='compare') and the remote/MCP sources call are in scope for whole-comparison withholding: they carry the whole comparison. Accepted."
- R3: "RW4d's comparison_passages reading (only a Reader caller's ref is a reading; only tutor tool runs are questions; agent/plan refs name no passage) is accepted as the intended rule; it removes false refusals."
- R4: "Persisting a reuse call's resolvable dropped pins, unverified sources and tutor question on the shared comparison row follows RW4d's union-across-reuse rule. Accepted; flagged to the owner as a note."
- R5: "Per-selection reading stamps with required span keys are queued as a follow-up (frontend refactor); keys stay optional now."

### Rule slips (recorded by the implementer, see the stage gate's process notes)

1. Two one-line `uv run python -c "import ..."` checks ran outside `env -i`: an import smoke test of the handlers, and
   printing `learnloop.__file__` under the base path. They loaded modules only, opened no vault and made no network
   call.
2. One single-test pytest diagnostic (base sources, the helper test) ran without the memory scope.

In this landing, every run followed the rules. The first desktop catalog command line failed before it ran anything
(the shell did not split the wrapper variable), and was rerun through a wrapper script. Diagnostics outside the drivers
were `sqlite3` reads of the smoke copies, and the one-row `UPDATE` on the two supplementary arxiv_v2 copies described
above.

### Open items

1. **R1 follow-up (queued):** bound nested TLS I/O in `_DeadlineNetworkStream` (a TLS-in-TLS read under an
   environment HTTPS proxy loops `recv` under one timeout: 2.0 s for a 1 s deadline), or set `trust_env=False` on
   the metered adapter's client.
2. **R5 follow-up (queued, frontend refactor):** stamp each Reader selection with the reading it was captured in,
   then make `spanKeys` required on the reading-only RPCs (bare ids refused). Keys stay optional now.
3. **Pre-existing RW4d fresh-path pin persistence:** a fresh comparison stores every dropped pin, including one dropped
   as "no such passage" (`NO_SUCH_PASSAGE`). RW4d's `comparison_passages` cannot resolve that pin, so the stored
   comparison is withheld whole (fail closed) for every later reader. The reuse path no longer writes such a pin
   (Codex review F1). The fresh path is unchanged, as RW4d left it.
4. **Owner note (R4):** a reuse call's resolvable dropped pins, unverified sources and tutor question are now added to
   the shared comparison row (`dropped_pins_json`, `unverified_sources_json`,
   `caller_context_json.reuse_question_event_ids`). This is a write-on-change, with no schema change.

### Second merge (main moved to `82ba4c8dce`, Reader RW5d P2b Manim)

Main moved after the gate above, so the branch was merged with it again (a merge, not a rebase):

- **`178337e59f`** merges main `82ba4c8dce`.
  - The source files both sides touched merged without conflict: `handlers/figures.py`, `api/client.ts`, `api/dto.ts`
    and `figures/useFigures.ts`. Both figure requests keep this branch's `span_keys`. P2b's new figure RPCs
    (`figure.rich_cancel`, `figure.rich_retry`, `figure.manim_opt_in`) take no passages.
  - The only conflicts were 10 generated desktop catalog notes. They were taken from main, then regenerated.
  - `config/template.py` did not conflict, so the defaults fingerprints were not recomputed.
- **`6b0cbdce63`**: the desktop catalog, regenerated on the committed merge (validation passed: 297/297 TS/TSX + 5/5
  Rust, ACTIVE=302, reproducible).
- **`1b7aae36de`**: the DB/config reference, regenerated on the committed tree. The changes are line citations and
  source/test links that this branch moved; `db_validate_reference.py` reports `errors: []`. `module_generate.py` and
  `module_validate.py` fail as on main (the Modules reference has been stale for many stages, with 1,291 issues).
  Neither writes anything.
- **Reruns:**
  - `lint-imports`: 36 kept, 0 broken.
  - Targeted pytest (`-n 6`, 5G scope): **3217 passed, 19 skipped, 3 xfailed, 0 failed** (31:21). The 157 files are
    every test file P2b added or changed, every test file this branch added or changed, and every test file naming
    the figure requests, span keys, `require_identity`, the desktop catalog scripts, the parameter registry or the
    template.
  - `npm install` ok; `typecheck` clean.
  - Whole vitest: **246 files, 2353 passed, 0 failed**.
  - `frontend:build` ok.
- The full pytest suite was **not** rerun: the merge needed no manual resolution in Python, and the only manual
  resolutions were in generated docs. The owner-copy smoke above was run on the first merge and was not repeated.
