# Migration-head fixture

This is a copy of the small conic-sections vault upgraded through migration
173. Migration 167 adds the learner-field F1 read model
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
`placement_quick_checks.request_id`). It pins current-head schema coverage
while the original populated fixture and the other vaults remain at
historical versions for upgrade-path tests.

The database is kept in rollback mode (`PRAGMA journal_mode=DELETE`) so the
tracked file is self-contained, with no committed data in a WAL companion.
