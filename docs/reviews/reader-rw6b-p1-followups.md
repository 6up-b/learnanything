# Reader RW6b part 1: cold follow-ups (`reader/rw6b-followups`, base `5b3f66059`)

Builds `spec_reader_workbench_v1` §9.3-§9.6 (UX §4.8-4.9, S15, D36; wireframe W12): the owner's "short
unfamiliar problem". Not in this part: the narrative (`reader_digest` route) and the router-card section (part 2).

**Spend: $0. No model or paid calls.** Tests use fakes only (a fake `find_practice` that composes the REAL
`value_candidates`). No manual runs on vault copies were needed: nothing in this stage needs a paid command to
verify an external interface, because the one model call (relevance) is `find_practice`'s existing routed, capped
`practice_rerank`. No owner vault, `~/learnloop-vaults`, `~/learnloop-retired` or `~/learnloop-books` was opened.
The reference scripts ran from the worktree. The predecessor's first generator run and my first rerun were plain
`uv run`. The final validator run used `env -i` with empty, existing `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR` under `fixtures-local/rw6b-env/`. The scripts read the tracked fixture and write docs, and
make no network calls.

**Resumed 2026-10-31.** The orchestrator's session restarted mid-implementation. I kept the predecessor's commits
`d2a5362dd`, `a24c29219` and `7d758bada` and committed its uncommitted work as `0272008a8`: the head-fixture rename,
the 5 paths, the test head bumps and the regenerated reference. Then I checked it, finished it and ran the gate.

## What was built, against the spec

| Spec | Where | Notes |
|---|---|---|
| §9.3 item 1, open questions | `instructional/reader_followups.py` `open_questions` | Questions come from RW6a's typed summary (`recap.session_summary`). A claim needing an independent check is a `retention` question. Rival explanations are `discriminate` questions: open probe episodes, facet `hypothesis_marginal`, gaps named this session. Formative records add questions only with `followups.formative_questions_enabled`, and they never change a prior. No learner state is written. |
| §9.3 item 2, candidates | `constraints_for`, `default_search` | `find_practice` (`instructional.practice.propose_practice`) is called with the exact filters `unattempted_only`, `exclude_family_ids` (the families whose answers this session revealed, from `reveal_events`) and `exclude_revealed_families`, plus `intent`, `target_hypotheses` and `system_initiated=True`. All of these already exist on main (`PracticeConstraints`, `value_candidates` under `source_service.discriminating_search`), so nothing was rebuilt. Relevance (`practice_rerank`) is the only model call, and it goes through the existing routed and capped path. The novelty label comes from exact facts only: `same_surface` when the candidate shares a family with an item worked in the session, otherwise "a new problem". "New application" is never claimed. |
| §9.3 item 3, valuation | inside `find_practice` (`instructional.valuation.value_candidates`) | Existing machinery: EIG, EVSI, `robust_composition`, then `evsi.rank_feasible` with greedy conditional selection and its stop rule. There is no count cap. λ, the burden and the nat-to-minutes scale are `robust_composition`'s, read from there. Only `act`/`measure` checks from a licensing regime (`licenses_system_check`) are dated; an `item_point` value is shown but never dated. |
| §9.3 item 4, dating | `date_for`, `retention_due` | A discriminating check is dated for the next local day. A retention check is dated at the practiced item's effective due (DL2 §5.3, through the intent view). With no FSRS state, it uses the scheduler's own first interval for that attempt's rating (`fsrs.initial_stability` at the intent target, else `recall_targets.STORED_RETENTION`). The date is never today and never later than `followups.max_wait_days`. **`followups.fallback_days` is not a key**; see "No made-up constants". |
| §9.3 item 5, scheduling | `plan_session` | Each check becomes a `test_me_later` commitment (`one_check_pending`) with `due_hint`. Its provenance is `{via: "reader_followup", summary_id, purpose, novelty, valuation_ref, inquiry_root_event_ids, anchor_span_ids, extraction_id, source_id, restoration_label, question}`. DL2's dated branch already reads `due_hint` (`scheduling/intent/serving.py`). Planning is idempotent per session. A budget or judge stop leaves the digest `incomplete`, and the next plan re-asks only the unfinished questions. A re-asked search passes the question's live checks to the valuation as `already_chosen`, so it adds a check only if it still clears the stop given them, and it never retires one (Codex re-review round 3). Rescheduling reads the live checks: an item whose check was retired or satisfied can be scheduled again as a fresh generation (idempotency key per digest, question, item and generation), but not one the learner undid. A check several questions select is created once and its `chosen` line lists every licensing question (`questions`). |
| §9.3 item 6, money | `followup_spend` | A metered relevance call reserves in both `followups.max_daily_cost_usd` and `source_service.max_daily_cost_usd`, so whichever cap is reached first stops it. Minutes are the plan's (maintain lane). |
| §9.3 item 7, re-valuation | `revalue_pending`, wired in `prepare_queue_build` via `handlers/reader_followups.prepare_followups` | Runs once per local day before the plan, with no model call (`discriminating.value_request` for the committed item). A check is retired with its reason when its question was answered since (an unaided success on the claim, or every named episode closed) or when it is below the stop. An abstention, an exclusion or an unknown keeps the check. A check the learner restored is left alone. A check several questions license stays while any of them needs it: it is retired as answered, repair-owned or below the stop only when that holds for every licensing question. Exposure, at serve and at re-valuation, is judged by the strictest rule across the open licensing questions (a `related` worked example excludes it when any open one is a retention question; round 4, F16). An exposure retires it and re-asks every licensing question (round 3). |
| §9.3 item 8, nothing fits | `plan_session` | `no_item` is recorded on the question with `generation: {requested: false, reason}`. **`followups.generate_when_nothing_fits` defaults off**: PF Phase 5a has no source-anchored request API to call, so wiring it was not cheap. Reported here as the spec allows. |
| §9.3 item 9, the way back | provenance, then DL2's `intent/checks.restoration_link` | DL2 already renders "Back to where you studied this: <LO>" from `inquiry_root_event_ids` and `anchor_span_ids` (tested: `test_the_provenance_carries_the_way_back_and_dl2_renders_it`). |
| Labelled, with undo | `coming_up`, `undo_followup`, `undo_all`, `restore_followup`; `ComingUp.tsx`, `RecapCard.tsx`, `WrapUpPanel.tsx` | A dated timeline shows the next three, then "later ▸" with no number. "Why" says the purpose and "LearnLoop's estimate". Undo takes an optional reason, stored on a `learner_card` verdict (`judgment_ledger`, task `reader_followup_undo`) and never sent to learner-text gaps. Undo all and restore work. On the card, retirements read as good news, and the wording says how the question was answered. |
| Receipt | `reader_session_digests.valuation_json` | Holds the questions with what raised them, the constraints, each question's outcome (`checks`, `no_item`, `no_check`, `unavailable`, `incomplete`), the full `value_candidates` receipt, and the chosen checks in order. Each chosen check carries `probe_eig`, `evsi_assignment` (R1's names), point EIG, LCB minutes, expected minutes, the predicted P(E), its date basis and its why. The receipt also records module versions. Replay never re-values. |
| §9.4 data | `migrations/227_reader_session_digests.sql`, `db/stores/reader_digests.py` | The table is WORKFLOW in `table_roles` (a paid step stands behind it; never re-run on rebuild). Columns: `summary_json`, `followup_commitment_ids_json`, `valuation_json`, re-valuation columns, and the narrative columns (`narrative_md`, `cited_event_ids_json`, `model`, `prompt_version`), which stay empty in part 1. |
| §9.6 kill switches | `FollowupsConfig` | `followups.enabled` (default on): when off, nothing is created and no re-valuation runs, but existing checks stay listed and can still be undone. Also `followups.formative_questions_enabled` (on) and `followups.generate_when_nothing_fits` (off). |
| mvp-0.38 interaction | `pending_cold_retry` | A claim whose repair `cold_retry` is pending or served (same attempt, or an item on the claim's LO carrying the facet) gets no retention follow-up. The receipt notes `cold_retry_pending`. |

Desktop RPCs: `reader.followups`, `reader.followup_undo`, `reader.followup_undo_all`, `reader.followup_restore`
and `reader.followups_plan`. They are desktop only, pinned in `test_mobile_allowlist.py`. `reader.recap` and
`reader.wrap_up` now carry `coming_up`.

## No made-up constants

- λ, the burden and the nat-to-minutes scale are read from `diagnosis/robust_composition.py`, where they are already
  labelled heuristic. RW6b adds no valuation number.
- **`followups.fallback_days` (3) was not added.** The retention date comes from FSRS: the effective due, else the
  scheduler's own first interval for the attempt's rating at its retention target.
- I replaced a bare `0.90` in the no-intent-view fallback with the scheduler's `STORED_RETENTION`.
- Only one case has nothing to date from: a formative-only retention question with no practiced attempt and no
  FSRS state. That date is the time cap, labelled `basis: no_fsrs_state` / `no_practiced_item` with `capped: true`
  on the receipt. This is the one place a guardrail stands in for a date. See open question 2.
- Keep guardrails are registered in `params/parameter_registry.py` as structural/operational:
  - `followups.max_wait_days` (14): the anti-nag time cap;
  - `followups.max_daily_cost_usd` (0.50): the owner's spending authority.
- The three switches are registered as kill switches.
- `NEXT_SHOWN = 3` is D36's display limit.

## Successor: none (for the reviewer to confirm)

> **Superseded by the Codex review's ruling (F4):** the successor `mvp-0.39` is built, with `followups.enabled` as
> its kill switch. See `reader-rw6b-p1-followups-codex-review.md`. The text below is the stage's original position.

Per §9.3 "Why no successor", RW6b adds content (commitments the learner can undo) behind `followups.enabled`. DL2
serves those commitments exactly as it defines them, with no serving, scoring, scheduling or evidence change.
`evsi.rank_feasible` decides only which commitments to create. The defaults snapshots of every algorithm version
move only because the effective config gains `[followups]`, and the comment in `config/template.py` records why.

The reviewer is asked to rule on the spec's own caveat: uncapped checks could change the maintain lane's
composition. If the ruling is that this needs a successor, the plan is `mvp-0.39` after `mvp-0.38` with the
journalled-activation pattern, whose `followups.enabled = false` state equals mvp-0.38 (plan parity). It is not
built.

**Rebuild `--shadow` with follow-ups present is 0/0/0** (`test_rebuild_shadow_is_zero_with_follow_ups_present`):
- a digest, two commitments and an undo are present;
- mastery, facet and schedule diffs are all 0;
- the live database is unchanged;
- digest rows are identical before and after.

## Fixes made on resume (my own review of the predecessor's work)

1. `retention_due`: the bare `0.90` became `recall_targets.STORED_RETENTION`.
2. `test_architecture::test_sql_writes_stay_in_registered_owner_modules` failed because the new store
   `db/stores/reader_digests.py` was not registered as an SQL owner. It is registered now.
3. The DB reference generator had no `followups` section, so it raised `KeyError`. I added it, regenerated
   `Config - followups.md`, and updated the prose counts (1071 leaves in 75 sections; 354 table notes).
4. The card's "Since last time" said "you solved one like it on <retirement date>" for every retirement, including
   ones where the rival explanations were settled. It also kept offering undo for a retirement the learner had
   restored. Now `recap.retired_checks` returns `answered_by` and `solved_at` and drops restored retirements, and
   the card says "…on <solve day>" or "…the explanations it was to tell apart are settled". Tested fail-first in
   pytest and vitest.
5. `undo_followup` retired a check whose attempt had already answered it (`satisfied` became `stopped`). Undo now
   acts only on `one_check_pending`. Tested fail-first.

## Head fixture

`fixtures/migration_head_226` was renamed to `fixtures/migration_head_227` as a git rename; every companion file is
byte-identical. It was rebuilt from the tracked sanitized 226 state on a backup-API copy with only 227 applied, then
`journal_mode=DELETE` (header bytes 1/1), `integrity_check` ok, no `-wal`/`-shm`. Its README has the 227 entry.
The 5 hard-coded paths were updated: 3 tests, plus `db_generate_reference.py` (3 mentions) and
`db_validate_reference.py`. `scripts/sanitize_migration_head_fixture.py`'s usage line was updated too.

## Gate (this step; targeted only, per the owner's 2026-10-17 rule)

Every pytest, vitest, npm and cargo command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G --`, with pytest at `-n 6`.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken (run before and after the fixes) |
| `pytest -n 6` over 94 files (list below) | 1 failed (fix 2), 1872 passed, 12 skipped, 9 xfailed |
| `pytest -n 6 tests/test_architecture.py tests/test_reader_followups.py` (after fix 2) | 56 passed |
| `pytest -n 6` over 13 recap/contract files (after fix 4) | 498 passed |
| `pytest -n 6 tests/test_reader_followups.py tests/test_reader_followup_valuation.py tests/test_reader_session_digests_migration.py` (final) | 46 passed |
| `pytest -m durability` over the migration test files, `tests/test_migrations.py`, `tests/test_coordinated_migrations.py`, `tests/test_tracked_fixture_databases.py` and `tests/test_reader_followups.py` | 3 passed |
| `pytest --durable-sqlite` over the 3 new test files | 44 passed |
| `npm install`, `npm run typecheck` | ok, no errors |
| `npx vitest run --maxWorkers=4` over 11 files (list below) | 54 passed |
| `npm run frontend:build` | built |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | ok |
| `db_generate_reference.py`, `db_validate_reference.py` | 355 notes (354 tables + catalog); validator `errors: []` |

**The 94 files of the targeted pytest run:**
- added or changed on this branch: `test_reader_followups.py`, `test_reader_followup_valuation.py`,
  `test_reader_session_digests_migration.py`, `test_mobile_allowlist.py`, and the 44 head-bump files
  (`test_ad1_migration.py`, `test_ad23_migration.py`, `test_approach_maps_schema.py`, `test_diagnosis_replay.py`,
  `test_exam_protection_review.py`, `test_help_assists_schema.py`, `test_hint_telemetry.py`,
  `test_learner_claim_application_migration.py`, `test_learner_claim_superseded_migration.py`,
  `test_library_asks_migration.py`, `test_method_explicit_upgrade.py`, `test_migrations.py`,
  `test_mvp010_upgrade.py` … `test_mvp024_upgrade.py`, `test_pfc_unverified_unassessed.py`,
  `test_plan_determinism.py`, `test_plan_follows_path.py`, `test_public_tip_guards.py`,
  `test_reader_ca2_fix_orchestrator.py`, `test_reader_rw3b_migration.py`, `test_reader_rw7a_migration.py`,
  `test_reading_step_switch.py`, `test_rebuild_orchestrator.py`, `test_recurrence_commands.py`,
  `test_regrade_contract_upgrade.py`, `test_retrieval_spaces_migration.py`, `test_route_rules_in_grader.py`,
  `test_rw2d_receipts_migration.py`, `test_section_coverage_migration.py`,
  `test_session_ownership_migration.py`, `test_shadow_rebuild.py`, `test_t1_batch_origin_migration.py`);
- `commitments.retire` callers: `test_commitments.py`, `test_intent_resolution.py`, `test_activity_families.py`,
  `test_assumed_known.py`, `test_daily_loop_reference_adoption.py`, `test_rebuild_equivalence.py`,
  `test_rebuild_equivalence_review.py`, `test_rebuild_closed_row_answer.py`, `test_learner_report_superseded.py`,
  `test_pr4_superseded_claims_landing.py`;
- recap and wrap-up: `test_reader_recap.py`, `test_reader_recap_review.py`, `test_reader_recap_review_r3.py`,
  `test_reader_wrap_up.py`, `test_reader_observation_records.py`, `test_intent_codex_review.py`,
  `test_intent_codex_rereview.py`, `test_reader_rw3b_review_fixes.py`;
- Today builds after reader activity (`prepare_followups` runs in every queue build):
  `test_daily_loop_reader_authored_practice.py`, `test_daily_loop_reader_retire.py`, `test_daily_plan_reading.py`,
  `test_reader_rw3a_landing.py`, `test_reading_paths.py`, `test_rw7b_codex_review_fixes.py`,
  `test_daily_plan_build.py`, `test_followups.py`;
- contracts: `test_config_refactor.py`, `test_registry_audit.py`, `test_table_roles.py`, `test_architecture.py`,
  `test_cli_help_snapshot.py`, `test_tracked_fixture_databases.py`, `test_sqlite_file_copies.py`,
  `test_coordinated_migrations.py`, `test_migration_coordinator.py`, `test_desktop_rpc_contract.py`,
  `test_sidecar_serializer_snapshot.py`;
- defaults snapshots: `test_cold_retry_reschedule.py`, `test_attempt_content_state_successor.py`,
  `test_ad23_successor.py`, `test_batch3_landing.py`, `test_lp_claim_fixes.py`, `test_reader_ca2_one_ask.py`,
  `test_serve_eligibility_review.py`, `test_regrade_contract_successor.py`, `test_field_workbench_signals.py`,
  `test_diagnosis_input_provenance.py`.

**The 13 files of the recap/contract rerun:** `test_ad23_inversion.py`, `test_reader_followups.py`,
`test_reader_followup_valuation.py`, `test_reader_observation_records.py`, `test_reader_recap.py`,
`test_reader_recap_review.py`, `test_reader_recap_review_r2.py`, `test_reader_recap_review_r3.py`,
`test_reader_wrap_up.py`, `test_architecture.py`, `test_sidecar_serializer_snapshot.py`,
`test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`.

**The 11 vitest files:** `screens/reader/ComingUp.test.tsx`, `RecapCard.test.tsx`, `recapCopyBasis.test.ts`,
`WrapUp.test.tsx`, `recapReview.test.tsx`, `recapSwitchOff.test.tsx`, `screens/ReaderScreen.recap.test.tsx`,
`ReaderScreen.recapReview.test.tsx`, `ReaderScreen.parity.test.tsx`, `app/intentCheck.test.ts`,
`components/IntentCheckFeedback.test.tsx`.

## Open questions

1. **Successor.** None, per the spec. The reviewer is asked to confirm, given that uncapped checks enter the
   maintain lane. If not confirmed: mvp-0.39 with off-state parity to mvp-0.38.
2. **The no-FSRS, no-attempt retention date.** This case arises only for formative-only questions. It uses the
   time cap, labelled `capped: true`. The alternative is a registered, seeded `followups.fallback_days` prior.
3. **Background generation** (`generate_when_nothing_fits`) stays off until PF exposes a source-anchored request
   API. `no_item` is recorded.
4. **First Today build after landing.** With `followups.enabled` on by default, the first Today build after
   landing plans every ended reader session from the last 14 days in the background. Each planned question makes
   one `practice_rerank` call, through the existing route and inside both daily caps.
5. **Undoing twice.** Undoing the same follow-up a second time, after a restore, keeps the first verdict's id. The
   second reason is not stored separately. This is minor calibration-data loss.
6. **Decision-mode seeding (round 3; Sol verify note, nonblocking).** In decision mode (`rank_feasible`), a live
   check already chosen in the question's space means nothing is added. This enforces the mode's one-measurement
   behaviour. It is not general conditional EVSI (the value of a second measurement given the first's outcomes).
   A later stage could condition `rank_feasible` on the seeded check's branches, as the information mode does.
