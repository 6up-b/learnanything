# Migration-head fixture

This is a copy of the small conic-sections vault upgraded through migration
172 (this branch has no 171: mobile M1 took 171 on main after this branch's
base, so the head fixture is regenerated with both at merge). Migration 167 adds the learner-field F1 read model
(`facet_outcome_observations`, `question_classifications`); migration 168 adds
PF-a activity-family membership events, proposals and family memory state;
migration 169 adds the practice index (`facet_dossiers`,
`practice_index_proposals`, `practice_eval_queries`,
`practice_index_evaluations`); migration 170 adds the Slice 1 M2
blind-grading/diagnosis split (`blind_grade_records`, `attempt_diagnoses`,
`diagnosis_context_receipts`, `diagnosis_feedback`,
`diagnosis_would_merge_log`, `diagnosis_wait_receipts`, `post_attempt_jobs`,
and the `diagnostic_augmentation_receipts.grader_mode` column); migration 172
adds Slice 2 T1's recurrence groups (`hypothesis_recurrence_groups`,
`hypothesis_recurrence_review`, `hypothesis_recurrence_state`), the
`recurrence_escalations` receipt (with the escalated repair's source and
payload), the guard's registered planted cases (`recurrence_guard_cases`),
the shared judge's work claims (`judgment_work_claims`), and rebuilds
`diagnosis_feedback` so its response also accepts the `escalation:`
usefulness taps. It pins
current-head schema coverage while the original populated fixture and the
other vaults remain at historical versions for upgrade-path tests.

The database is kept in rollback mode (`PRAGMA journal_mode=DELETE`) so the
tracked file is self-contained, with no committed data in a WAL companion.
