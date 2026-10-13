# Migration-head fixture

This is a copy of the small conic-sections vault upgraded through migration
185. Migration 167 adds the learner-field F1 read model
(`facet_outcome_observations`, `question_classifications`); migration 168 adds
PF-a activity-family membership events, proposals and family memory state;
migration 169 adds the practice index (`facet_dossiers`,
`practice_index_proposals`, `practice_eval_queries`,
`practice_index_evaluations`); migration 170 adds the Slice 1 M2
blind-grading/diagnosis split (`blind_grade_records`, `attempt_diagnoses`,
`diagnosis_context_receipts`, `diagnosis_feedback`,
`diagnosis_would_merge_log`, `diagnosis_wait_receipts`, `post_attempt_jobs`,
and the `diagnostic_augmentation_receipts.grader_mode` column); migration 171
adds mobile M1 capture (`capture_inbox`, `capture_routes`, `mobile_devices`,
`mobile_pairings`, `mobile_pairing_attempts`, `mobile_pairing_guard`,
`mobile_request_log`); migration 172 adds the Slice A Phase 6 placement
receipts (`assumption_decisions`, `assumption_returns`,
`placement_quick_checks`); migration 173 adds the quick check's
presentations (`placement_quick_check_items` and
`placement_quick_checks.request_id`); migration 174 adds Slice A
Phase 5a's PF-b generation tables (`pf_candidates`, `item_skeletons`,
`item_fingerprints`); migration 175 (router R0) labels judgment-call receipts
(`model_call_receipts.judge`, `question_set_version`, `state_hash`) and
rebuilds `judgment_ledger` so it records the Decider's verdicts as
`judge = 'decider'`; migration 176 adds Slice 2 T1's recurrence groups with
authority (`hypothesis_recurrence_groups`, `hypothesis_recurrence_review`,
`hypothesis_recurrence_state`, `recurrence_escalations`,
`judgment_work_claims`, `recurrence_guard_cases`) and rebuilds
`diagnosis_feedback` so it accepts the `escalation:` ratings; migration 177
adds Slice 2 T6's FTS5 keyword index over source blocks (`source_block_fts`,
DERIVED, with its insert, delete and update triggers on
`source_document_blocks`; the delete paths match the block's identity as well
as its rowid); migration 178 adds the stuck prompt's
`practice_attempts.declared_stuck` flag; migration 179 rebuilds the
append-only `reveal_events` (same columns, indexes and triggers) so its
`source_kind` CHECK also accepts `answer_display`; migration 180 adds
daily-loop DL1's finite plan (`daily_plans`, WORKFLOW, and the
`attention_blocks` plan columns `daily_plan_id`, `plan_ordinal`, `lane`,
`chosen_by`, `decision_ref`, `reading_json` with the unique
`idx_attention_blocks_plan`; built as DL1's 174 and renumbered at its merge)
and rebuilds the learner field's DERIVED `facet_outcome_observations` (same
columns, key and index) so its `serving_origin` CHECK also accepts
`daily_plan` (owner decision 2026-10-12); migration 185 rebuilds the
append-only `grading_clarifications` (same columns, index and trigger) so its
`trigger` CHECK also accepts `route_check_disagreement` (mvp-0.15's
proofs-and-explanations route check; built on grading/proof-alternatives as
185 while main's merge chain added 181-183, so expect renumbering).
Built from `migration_head_180` (renamed) with only 185 applied
(checkpointed, rollback journal, `integrity_check` ok, `foreign_key_check`
clean). It pins
current-head schema coverage while the original populated fixture and the
other vaults remain at historical versions for upgrade-path tests.

The database is kept in rollback mode (`PRAGMA journal_mode=DELETE`) so the
tracked file is self-contained, with no committed data in a WAL companion.
