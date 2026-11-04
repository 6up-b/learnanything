# FG1c: fixes for the Codex review (job 20261104-100331-Rd7ddA)

Reviewed `followup/fg1c-marks` at `450c22470d`. Four of five findings fixed; F2 rejected and left for the owner to overrule (see below). Each fix was reproduced first:
`tests/test_followup_fg1c_codex_review.py` had 19 failures against the unfixed code, before any source changed.

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Marks drop the provenance of model-written causes | fixed | `b476193089` | `test_f1_*`: current attempt, history attempt as of its cutoff, snapshot entry, cleared marks |
| F2 | Medium | Serving changes activate without an algorithm successor | rejected | none | Conflicts with `spec_teacher_v1.md` §15.2's decided default, and no list a learner already saw moved. Reasons below |
| F3 | Medium | Probe agreement confuses admission with independence | fixed | `b476193089` | `test_f3_*` |
| F4 | Medium | Delayed agreement accepts marks made after the outcome | fixed | `b476193089` | `test_f4_*` |
| F5 | Medium | Rejecting one cause is scored as rejecting the entire list | fixed | `b476193089` | `test_f5_*` |

## F1

A cause a mark shows is model-written text, so what reads it read it. `followup_serve.marks.marked_causes` names the version and statement of each cause the opinion still shows (a cleared or
superseded mark shows none, and *None of these* names no cause). `provenance.attempt_read` folds them for a history attempt, which also covers a snapshot entry, since the export serves each file through the
same function. `CurrentAttempt.marked_causes` carries them for the attempt being re-diagnosed, and they join `AssembledContext.reads`. They are never rendered a second time, so the context and its hash
are unchanged. `closure` then folds the hypothesis's own record, so its exam dependency reaches the diagnosis's record, and a statement with no record makes that record incomplete.

## F2: rejected

The finding's facts hold: at any tag, with the default-on switch, an updated vault gets a new panel with a shuffled order, and once marks exist the card and the diagnoser's context carry them. Its
conclusion does not follow, for three reasons.

1. **The model inputs are already decided.** `spec_teacher_v1.md` §15.2 ruled on this exact shape, confidence events on the card and in the diagnoser's context: "The change alters model inputs, not persisted
   meaning. **Decided (default, 2026-10-24):** no successor, since the card's content already changes daily." Recorded defaults are accepted (owner, 2026-10-12). A stored card names its input through
   `+marks`, and a diagnosis's context hash is on its receipt. Replay never asks a model.
2. **Nothing a learner already saw was reordered.** `why?`, the causal feedback and the unresolved-cause card keep their order. The shuffle exists only on FG1c's new panel, which has no predecessor order to differ
   from. Router objective §11 calls shuffling "a serving change" to say that RO0, whose gate is "no display order changes", doesn't own it, and it assigns it to FG1 §7. Neither §11 nor §7 asks for a tag, and
   FG1's §10 names one successor, FG1's.
3. **Handoff §0's "what is served" and the playbook's test are about what is practised and what records mean.** The 2026-10-17 rule makes a successor of "which items are served as measurements" or "which new attempts are
   primed". The panel changes neither: it follows §6.0's hold, and `test_marks_change_no_row_outside_their_own_ledger` and `test_a_rebuild_ignores_marks_and_keeps_them` pin that no other row moves. The nearest precedents took no
   successor: `curriculum-c2-notes-linked.md` ("display and learner-voice records only") and handoff line 620 ("retrieval is context").

The tap's removal on the probe lane stays reachable only at FG1's tag, since only there does that lane exist. Predecessor equivalence with the switch off is already pinned (`test_off_means_no_key_no_rows_and_the_same_replies`,
`test_with_the_switch_off_the_card_is_byte_identical_whatever_rows_exist`, `test_the_switch_off_keeps_the_diagnosers_context_as_it_was_whatever_rows_exist`).

**This is a judgement, and the owner can overrule it.** A mark can move a router model's choice through the card, which is the strongest form of the finding. The §15.2 ruling accepts that for attributed text. If the owner wants a tag
anyway, the smallest build is a successor gating `hypothesis_marks_on` for the panel, card and context, with receipts staying additive.

## F3

- **Independence** is the receipt's `admissible_as_independent`. Only an assessed clean answer counts as independent, so NULL ("not assessed") doesn't. An unadmitted clean answer stays independent.
- **The contract** is `DISCRIMINATING_OUTCOMES`, so `matched_multiple` scores nothing. The constant moved from `causal_orchestrator` to the dependency-neutral `causal_activity_policy`, because importing it from the orchestrator broke
  the frozen-cycles contract (`.ops -> .diagnosis`). The orchestrator still exports the same object, and a test pins that.
- **Coverage.** A no-match supports *None of these* only with `declared_keys_observed`. Otherwise it is counted in `none_of_these_on_a_probe_that_did_not_measure_every_cause`. A fully measured no-match on a not-independent answer still counts, in that answer's bucket.

## F4 and F5

`router/outcomes.py::delayed_outcomes_after` replaces `next_delayed_outcomes` (this stage's own, with no other caller). It returns every delayed presentation after the attempt under the shared definition, with `presented_at`.

- **Scored opinion.** Walking those in order, the report scores the opinion held strictly before the first presentation that had one, read with `latest_marks` over the rows before it. Hindsight can't replace it, a taken-back mark isn't held, and a mark made after one delayed
  answer binds to the next.
- **Retrospective marks.** A mark made or changed after a delayed answer goes in `marked_after_a_delayed_answer`, by reading, against the newest answer it could have seen, unscored. A mark that came after one delayed answer and before another counts in both places: scored against the later, apart against the earlier.
- **Ruling the list out** takes *None of these*, or *Not it* on every cause of the list as the newest mark displayed it, compared by stable identity. A cause left unmarked, or added since, wasn't rejected. Partial rejection is `rejected_some_causes`, reported and never scored.

The plain report's line and `DELAYED_AGREEMENT_LABEL` say so. `test_the_report_measures_marks_against_delayed_performance` marked with the real clock, which is after its own later answer under the frozen test clock, so it now marks with that clock.

## Gate

Every pytest command inside the memory-capped scope, at `-n 6`, behind the lock. Python and lint runs outside pytest under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | done |
| `lint-imports --no-cache` | 43 kept, 0 broken; frozen cycles kept |
| Targeted, 93 files (below) | 2700 passed, 0 failed, 1 skipped, 2 xfailed (5:14) |
| `module_generate`, `module_validate`, `validate_vault` | pass; 1:1 module coverage |

The full suite runs at the landing. The 93 files include the stage's display-label audit (`test_measurement_state_labels.py`), CLI help snapshot, process-launch list (`test_codex_lockdown_round3.py`), and the contract tests for the desktop RPC, mobile allowlist, serializer, architecture, table roles, coordinated migrations and tracked fixtures.

Files: test_ad23_fix_review.py, test_ai_compare.py, test_architecture.py, test_causal_activity_policy.py, test_causal_cold_outcomes.py, test_causal_factor_deferral.py, test_causal_orchestrator.py, test_causal_p2_acceptance.py, test_causal_probe_commissioning.py, test_causal_repair_sidecar_rpcs.py, test_causal_shadow_selection.py, test_chatgpt_plan_landing.py, test_chatgpt_plan_workspace.py, test_cli_help_snapshot.py, test_codex_lockdown_round3.py, test_coldness_receipt.py, test_cold_retry_reschedule.py, test_common_repair_delivery.py, test_config_refactor.py, test_coordinated_migrations.py, test_data_capture_a2_measurement.py, test_data_capture_a4_delayed_completion.py, test_data_capture_codex_rereview.py, test_data_capture_codex_review.py, test_data_capture_landing_review.py, test_data_capture_report.py, test_desktop_activation_audit.py, test_desktop_rpc_contract.py, test_diagnosis_context.py, test_diagnosis_contract.py, test_diagnosis_history_modes.py, test_diagnosis_input_provenance_landing.py, test_diagnosis_input_provenance.py, test_diagnosis_pipeline.py, test_diagnosis_replay.py, test_dialogue_causal_join.py, test_exam_protection.py, test_figures_help.py, test_followup_codex_review.py, test_followup_fg1c_codex_review.py, test_followup_generate_e2e.py, test_followup_journey.py, test_followup_live_shape.py, test_followup_rival_factor.py, test_followup_router.py, test_followups_batch6_review_fixes.py, test_followup_successor.py, test_forecast_receipts.py, test_held_grade_composition.py, test_hint_evidence.py, test_hypothesis_marks_context.py, test_hypothesis_marks_migration.py, test_hypothesis_marks.py, test_intent_fix_round4.py, test_learner_blindness_relax_codex_review.py, test_learner_blindness_relax.py, test_learner_text_gaps_rereview.py, test_measurement_state_labels.py, test_mobile_allowlist.py, test_mobile_handoff.py, test_pfc_unassessed_readers.py, test_pfc_unverified_unassessed.py, test_placement_opening_probes.py, test_public_tip_guards.py, test_reader_rw2b_fix11.py, test_reader_rw2b_fix14.py, test_reader_rw2b_fix15.py, test_reader_rw3a_landing.py, test_reader_workbench_rw2a.py, test_receipt_exactness.py, test_reference_gate_imports.py, test_remediation_cold_retry.py, test_required_method_round3_review.py, test_router_coldness_covariates.py, test_router_g4_restraint.py, test_router_outcomes.py, test_router_presentations.py, test_router_r2b_agreement.py, test_router_r2bc_landing.py, test_router_r2c_retrieval.py, test_serve_eligibility.py, test_sidecar_serializer_snapshot.py, test_table_roles.py, test_teacher_te0_confidence_events.py, test_teacher_te0_fix_round2.py, test_teacher_te0_review_fixes.py, test_teacher_te1b_landing_r2.py, test_teacher_te1b_review_fixes.py, test_teacher_te1b_suggestions.py, test_tracked_fixture_databases.py, test_ux_phase4_feedback.py, test_workbench_assistance.py, test_workbench_trace.py.

No frontend, `src-tauri`, migration or DB/connection code changed, so npm, vitest, cargo, the durability lane and the DB reference scripts didn't apply. No real model call, no vault opened, no paid command.
