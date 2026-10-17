# Migration-head fixture

This is a copy of the small conic-sections vault upgraded through migration
207. Migration 167 adds the learner-field F1 read model
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
`daily_plan` (owner decision 2026-10-12); migration 181 adds router R1's
decision ledger (`router_decisions`, RAW_LEDGER, append-only) and its outcome
cache (`router_outcomes`, DERIVED; built as R1's 176 and renumbered at its
merge); migration 182 adds learner-text gaps (`learner_text_gaps` and
`learner_text_gap_reversals`, RAW_LEDGER, append-only; `learner_text_gap_jobs`,
WORKFLOW; `learner_gap_check_advances` and `learner_gap_commitments`,
RECEIPT; built as the branch's 177 and renumbered at its merge); migration
183 adds facet identity's action ledger (`facet_identity_actions`, WORKFLOW:
each judge-applied merge or absorb with the facets.yaml entries before and
after it and its undo; built as the branch's 172 and renumbered at its
merge); migration 184 adds EVSI calibration Part B's `voi_forecasts`
(RECEIPT, append-only by trigger: the forecast every live
value-of-information decision ran on; built as the branch's 184 with 181-183
reserved, so it kept its number at its merge); migration 185 (reader
workbench RW1a) gives `reader_authored_questions` its quick-check scopes
(`scope_kind`, `question_style` with all five values, `anchor_span_ids_json`,
`inquiry_root_event_id`, `self_check`, and the unique partial index
`idx_reader_authored_questions_inquiry`; columns only, no rebuild; built as
RW1a's 189 with 184-188 held for branches in flight, and renumbered at its
merge); migration 186 rebuilds the append-only `grading_clarifications` (same
columns, index and trigger) so its `trigger` CHECK also accepts
`route_check_disagreement` (mvp-0.17's proofs-and-explanations route check;
built on grading/proof-alternatives as 185 with the placeholder tag mvp-0.15
while main's merge chain added 181-184, it kept 185 at its merge after 184,
where its tag became mvp-0.17, and was renumbered 186 when it landed after
RW1a's 185). Migrations 187-195 add the canonical-sources service
(spec_source_practice_and_probes_v1; built on sources/canonical-practice as
184-192 and renumbered at its merge after main's 184-186): 187 the proposal
callers (`practice_index_proposals.caller`, `caller_ref`, `intent`) and the
append-only `instructional_impressions`; 188 textbook-exercise imports
(`source_exercise_imports`, WORKFLOW), the append-only `reference_key_checks`
and `practice_attempts.reference_status` (the certification gate, C3,
mvp-0.18); 189 `source_comparisons` (WORKFLOW); 190
`practice_index_proposals.valuation_json` and `provisional_json`; 191
`source_exercise_imports.need_id`; 192 the append-only tool receipts
`source_tool_calls` (RECEIPT); 193 the append-only `retrieval_interventions`
(RAW_LEDGER) and their DERIVED outcome join `retrieval_intervention_outcomes`
(one replayer); 194 the daily cap's shared reservations `source_service_spend`
(WORKFLOW); 195 rebuilds it for the spend accounting (`legacy`,
`lease_expires_at`, `resolved_by`, the `released` state) and indexes
`model_call_receipts` by `started_at` and `parent_call_id`.
Migrations 196-197 come from facet locks removed and the facet authority
chokepoint (facets/locks-and-depends-on and merge/facet-locks; built there as
188, then 185-186, and renumbered at their landing after main's 185-195): 196
rebuilds `facet_identity_actions` (same columns, rows and indexes) so its
CHECKs also accept `action = 'reword'` (a facet version a proposal apply, a
Library save or the owner's one-tap confirm wrote, the old entry kept for the
undo; a `proposed` reword is one held for the owner's confirm) and
`origin IN ('proposal', 'registry')` (facet locks removed, owner 2026-10-12);
197 adds `facet_registry_saves` (WORKFLOW: the write-ahead intent of a Library
save or a confirm that records the owner's manual-authority verdicts, settled
by recovery from facets.yaml; Codex re-review 2 of the facet authority
chokepoint, F7).
Migrations 198-199 come from UX Phase 1 (`ux/phase1-first-run`; built there as
186-187 while main's chain held 181-183, and renumbered at their landing after
main's 184-197): 198 adds `source_artifacts.keep_local` (the learner's "Keep
this book on this computer") and the WORKFLOW table `source_auto_build_state`
(a book's automatic-build generation, advanced by Undo, and the reading
position a running build could not act on yet); 199 makes that position one
durable request per book, adding `source_auto_build_state.wanted_revision`,
`wanted_attempts` and `wanted_retry_at`.
Migrations 200-201 come from value-of-information stopping (successor
mvp-0.21, `serving/voi-stopping`; built there as 187-188 with the placeholder
tag mvp-0.17 and renumbered at their landing after main's 184-199): 200
rebuilds `probe_episodes` (same columns, rows and indexes) so its
`completion_reason` CHECK also accepts `value_of_information_stop` and adds
the nullable `completion_detail_json` (the stop decision with its forecast);
201 adds `followup_value_decisions` (RECEIPT, append-only by trigger: one row
per follow-up value decision, with its own id, per-attempt ordinal and
source-attempt link) and backfills it from legacy `decision_features`
follow-up rows that carry a `voi_stopping` body (none here).
Migration 202 comes from router R2a (successor mvp-0.23, `router/r2a`, the
staged frame on Today; built there as 205, a placeholder number, and
renumbered 202 at its landing after main's 200-201): it
rebuilds the append-only `router_decisions` (same columns, rows, indexes and
triggers, plus an index on `controller_decision_id`) so its `decision_kind`
CHECK also accepts `plan_interrupt` (R2c); adds `router_outcomes.action_binding`,
`r_next_reference_status` and `r_cold_reference_status` (DERIVED); adds the
append-only `plan_presentations` (RAW_LEDGER: one row per plan item served,
the exact decision -> presentation -> attempt receipt) and
`practice_attempts.plan_presentation_id` with its partial unique index; and
adds `router_decision_payloads` (WORKFLOW: the learner-state card each
decision stored).
Migration 203 comes from the chat frontend's C1a (`mcp/c1-read-context`, the
MCP adapter; built there as 210, a placeholder number, and renumbered 203 at
its landing after main's 202): it rebuilds `interaction_events` (same columns,
rows and indexes) so its `kind` CHECK also accepts `chat_tool_call` (one row
per MCP tool call a chat host made) and its `origin` CHECK also accepts
`chat_host`.
Migration 204 comes from exam protection by extraction identity
(`fix/reread-safety`, docs/reviews/exam-protection-identity.md; built there as
225, a placeholder number, and renumbered 204 at its landing after main's
203): it adds `source_held_out_signal_marks` (RAW_LEDGER, never updated by
trigger: the held-out signals each fresh inventory marked on the reading its
model run read, with its revision and the role it was made under) and
backfills it from `source_unit_inventories` (none here).
Migration 205 comes from diagnosis input provenance
(`diagnosis/input-provenance`, spec_mcp_frontend_c1 §4.8,
docs/reviews/diagnosis-input-provenance.md; built there as 204, a placeholder
number, and renumbered 205 at its landing after re-read safety's 204): it adds
`text_write_provenance` (RAW_LEDGER, append-only by trigger: one row per write
of a model-written text, or per grading, naming what it was written from),
`error_event_lineage` (RAW_LEDGER, append-only by trigger: the error events a
regrade re-minted and the ids they replace, or a retired id with no
replacement, Q9) and `question_events.assessment_contract_version_id` (the
item contract a learner question was asked about, Q10; NULL on every row this
fixture already had). Both tables are empty here.
Migration 206 comes from saved diagnosis forecasts
(`diagnosis/forecast-receipts`, docs/reviews/diagnosis-forecast-receipts.md;
built there as 230, a placeholder number, and renumbered 206 at its landing
after diagnosis input provenance's 205): it adds `forecast_receipts` (RECEIPT,
append-only by trigger: one forecast per row, written in the transaction of
the decision that made it, with its exact binding or the reason it has none;
no rows here).
Migration 207 comes from reader workbench RW2a (`reader/rw2a`, the resumable
scratchpad, docs/reviews/reader-workbench-RW2a.md): it adds
`workbench_sessions` (WORKFLOW: a problem worked in steps, opened at once
before its exercise import binds it, with every CHECK'd column created with
all its values, the assessment contract it shows and the answer box's hints
carried into steps, and the serve it answers) and `workbench_steps` (RAW_LEDGER, append-only by trigger:
versions, tombstones and undos under the client's idempotency key). Both
tables are empty here. Rebuilt after the stage's Codex review added
`assessment_contract_version_id` and `carried_hints` to 207, and again after
its re-review added `scheduler_candidate_id` and `plan_presentation_id` (the
serve a problem answers, kept across a resume); each time the same chain: a
backup-API copy of the base's `migration_head_206` with only the revised 207
applied.
Built as a backup-API copy of `migration_head_206` (itself a backup-API copy
of `migration_head_205` with only 206 applied, that of
`migration_head_204` with only 205 applied, that of `migration_head_203`
with only 204 applied, that of `migration_head_202` with only 203 applied,
that of `migration_head_201` with only 202 applied, that of
`migration_head_199` with only 200-201 applied, that of `migration_head_197`
with only 198-199 applied, that of `migration_head_195` with only 196-197
applied, and that of `migration_head_186` with 187-195 applied) with only 207
applied through `learnloop.db.migrate.apply_migrations` under the test suite's
upgrade allowance (`UPGRADE_TEST_HELPER`; checkpointed with
`wal_checkpoint(TRUNCATE)`, rollback journal, `integrity_check` ok,
`foreign_key_check` clean), then copied into place with the backup API, with
no companion files; `migration_head_206` was renamed to this directory. It
pins current-head schema coverage while the original populated fixture and
the other vaults remain at historical versions for upgrade-path tests.

The database is kept in rollback mode (`PRAGMA journal_mode=DELETE`) so the
tracked file is self-contained, with no committed data in a WAL companion.
