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
| §9.3 item 5, scheduling | `plan_session` | Each check becomes a `test_me_later` commitment (`one_check_pending`) with `due_hint`. Its provenance is `{via: "reader_followup", summary_id, purpose, novelty, valuation_ref, inquiry_root_event_ids, anchor_span_ids, extraction_id, source_id, restoration_label, question}`. DL2's dated branch already reads `due_hint` (`scheduling/intent/serving.py`). Planning is idempotent per session. A budget or judge stop leaves the digest `incomplete`, and the next plan re-asks only the unfinished questions. A re-asked search passes the question's live checks to the valuation as `already_chosen`, so it adds a check only if it still clears the stop given them, and it never retires one (Codex re-review round 3). Rescheduling reads the live checks: an item whose check was retired or satisfied can be scheduled again as a fresh generation (idempotency key per digest, question, item and generation), but not one the learner undid. A check several questions select is created once. Its `chosen` line carries its licensing list (`licensing`: each question's key, intent and what the gate and re-valuation read), written at publication and changed in the same transaction as the line (round 6). |
| §9.3 item 6, money | `followup_spend` | A metered relevance call reserves in both `followups.max_daily_cost_usd` and `source_service.max_daily_cost_usd`, so whichever cap is reached first stops it. Minutes are the plan's (maintain lane). |
| §9.3 item 7, re-valuation | `revalue_pending`, wired in `prepare_queue_build` via `handlers/reader_followups.prepare_followups` | Runs once per local day before the plan, with no model call (`discriminating.value_request` for the committed item). A check is retired with its reason when its question was answered since (an unaided success on the claim, or every named episode closed) or when it is below the stop. An abstention, an exclusion or an unknown keeps the check. A check the learner restored is left alone. A check several questions license stays while any of them needs it: it is retired as answered or below the stop only when that holds for every open licensing question. Answered state lives only in re-valuation. Exposure and repair ownership, at serve and at re-valuation, are the serve-time gate's: the strictest rule over ALL the line's licensing questions, answered or not (round 6). A `related` worked example excludes the check when any licensing question is a retention question. A repair owns it only when it owns every licensing question. An exposure retires it and re-asks every licensing question. A licensing question no longer in the receipt is pruned from the line's list. Only a missing digest row or chosen line is damage: the check is held (`licensing_unreadable`), and re-valuation retires it and re-asks its own question. |
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

## Landing onto main (2026-10-31)

The branch `reader/rw6b-followups` (stage tip `7ec6cdd4e`, base `5b3f66059`) landed in `learnanything-dl2`. I merged
`main` twice: first `94494b4cc` (Curriculum C0b with migration 228, Reader CA3/CA4/CA5a, the RW5d P2 sketch tier
with its default off, and the Codex 0.165 lockdown), then `2c3507003` (Reader CA5, which reached main during the
gate). Main was neither fast-forwarded nor pushed. The successor keeps **mvp-0.39** (after mvp-0.38). Migration
**227** keeps its number beside main's 228: the runner is set-based.

### Commits and conflicts

| Commit | What |
|---|---|
| `b5fb1d9c9` | `--no-ff` merge of `94494b4cc`. **Fixtures:** I took main's `migration_head_228` and dropped the branch's `migration_head_227` rename entirely. `migration_head_226` was deleted on both sides. **Migration pins** (43 test files plus the 2 reference scripts and `sanitize_migration_head_fixture.py`) are resolved mechanically. Fixture paths and `SCHEMA_HEAD` are 228, the chains list `…, 226, 227, 228`, and the "nothing else changed" diffs subtract both `RW6B_ADDED_OBJECTS` and `C0B_ADDED_OBJECTS`. `tests/test_reader_session_digests_migration.py` now pins the head at 228 with 227 present. **`config/template.py`:** every snapshot from mvp-0.9 to mvp-0.37 keeps main's CA5a/CA3/CA4/C0b/RW5d-P2 notes, and mvp-0.9 also keeps RW6b's `[followups]` note. I rebuilt mvp-0.38's block (RW6b's note plus main's) and mvp-0.39's block (main's keys listed as "in it too"). **All 30 fingerprints** were recomputed with `defaults_fingerprint_for_version`, with the template `.pyc` cleared before and after; a recheck found 0 mismatches. 432 generated reference notes were taken from main's side and regenerated next. **Auto-merged:** the algorithm chain, the upgrade CLI and sidecar completers, the parameter registry, the mobile allowlist and the RPC lists. |
| `9c913711c` | Head fixture rebuilt (below). DB/config reference regenerated: 1082 effective leaves in 76 sections, 358 table notes, with the prose counts corrected by hand. `db_validate_reference.py` errors []. |
| `5d366d533` | Interaction tests: `tests/test_reader_rw6b_landing.py`, 5 tests (below). |
| `75044d17e` | `--no-ff` merge of `2c3507003` (Reader CA5). **Conflicts:** `template.py` only. Every snapshot keeps CA5's note beside RW6b's, and mvp-0.39's block lists CA5's `hide_everywhere`/`hidden_sources`. All 30 fingerprints were recomputed again (0 mismatches). CA5 has no migration. |
| `6eb2f5106` | DB/config reference regenerated: **1084 effective leaves in 76 sections** (main's 1079 plus RW6b's 5 `[followups]` keys), 358 table notes. `db_validate_reference.py`: **errors []**; `validate_vault.py` passes (1168 notes, 1166/1166 reachable). |

`git diff main` lists no tracked database besides the head fixture and nothing under `fixtures-local/`.
`.gitignore` is unchanged.

### Migration and head fixture

`fixtures/migration_head_228/state.sqlite` was rebuilt from **main's** tracked, sanitized `migration_head_228`, which
already had 228 applied:
- a backup-API copy under `fixtures-local/head228-rw6b/` had only `227_reader_session_digests.sql` applied, through
  `apply_migrations` under `UPGRADE_SCRATCH_COPY`;
- then `wal_checkpoint(TRUNCATE)` gave (0, 0, 0), `journal_mode=DELETE` (header bytes 1/1), `integrity_check` ok
  and `foreign_key_check` empty;
- it was copied into place with the backup API, with no companion files.

Compared with main's fixture, only `reader_session_digests`' five objects were added and only `schema_migrations`
gained a row (227). Every other definition and row is identical, so the sanitized content carries over. The head
now holds 226 + 227 + 228. The README has a section for this rebuild. The 5 hard-coded paths already named 228.
`reader_session_digests` stays WORKFLOW in `table_roles`.

### Interactions (`tests/test_reader_rw6b_landing.py`; every model a fake)

All 5 tests passed on their first run against the product code. The only edits were to my own harness. **No product
change.**

- **(i) C0b's Check once commitments beside RW6b's follow-ups.**
  - Setup: on the RW6b vault at mvp-0.39, one follow-up, plus a *check me later* (`deliverable_path`) and an *Am I
    ready?* (`deliverable_ready`) check on other items, written exactly as `deliverable_path.create_check` writes
    them.
  - All three are due checks in DL2's one maintain-lane view and are servable. The serve-time gate returns `None`
    for both C0b checks.
  - An exposure since creation on every candidate (an impression in another proposal) holds the follow-up
    (`seen_in_proposal`). It leaves each Check once **identical** to its state with `followups.enabled = false`.
  - **Finding (DL2's own rule, no change):** `create_check` picks the LO's first unattempted item, which can be the
    item a follow-up already checks. The learner's newer Check once then decides that item: the follow-up is
    `replaced` and the Check once is served cold. A separate test pins this.
- **(ii) The mvp-0.38 reschedule keeps repair ownership.**
  - Setup: the rows `reschedule_assisted_cold_retry` leaves. The assisted retry is `expired`, and one fresh
    `cold_retry` on another surface keeps the primed source attempt, with its context marked.
  - At planning, the claim gets no retention question: the note is `cold_retry_pending` with the fresh task.
  - An existing follow-up is held (`repair_retry_owns`, naming the fresh task). Re-valuation retires it as
    `RETIRE_REPAIR_OWNS`.
- **(iii) CA5a's peek writes the exposure the gate reads.**
  - `record_span_exposures(..., context="library")` is the call `reader.correspondent_peek` makes. Run on the
    item's source span after valuation, it holds the follow-up as `source_exposed`, citing those exposure event
    ids.
  - Main has no side-by-side read yet. RW5d figures write no `source_exposure` rows: they are generated content,
    not source text.
- **(iv) Covered by existing tests that pin the latest tag; both pass in the full suite.**
  - An interrupted mvp-0.38 activation followed by `upgrade --to mvp-0.39`:
    `test_reader_followups_successor.py::test_an_interrupted_mvp038_activation_then_upgrade_to_mvp039_completes_it`
    and the attach-refusal case.
  - The denial-log archive happens exactly once per upgrade command, direct or chained from mvp-0.35, and a refused
    run archives nothing: `test_pr4_superseded_claims_landing.py::test_landing_iii_*`, which asserts
    `LATEST_ALGORITHM_VERSION == "mvp-0.39"`.

### Regeneration

- **DB/config reference:** regenerated and validated after each merge, as above.
- **Defaults fingerprints:** all 30 recomputed after each merge.
- **CLI help snapshot, sidecar serializer snapshot, desktop RPC contract and mobile allowlist:** all pass as merged.
  RW6b's five RPCs stay desktop-only beside CA5's. Nothing else needed regenerating.

### Gate (`env -i` with empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR`; logs in `fixtures-local/landing/logs/rw6b/`)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` (wasmtime 50.0.1 added), `uv pip install pypdfium2`; `lint-imports --no-cache` | **36 kept**, 0 broken, both after the first merge and on the final tip |
| Targeted run after the first merge (135 files: every test file either side changed since the base, the upgrade chain, snapshots, references, RPC/serializer pins, mobile allowlist; `-n 6`, 5G) | **2332 passed**, 12 skipped, 3 xfailed (22 min 50 s, under load from a parallel landing) |
| Targeted run after the second merge (the test files CA5 changed, the landing and successor tests, snapshots, config, registry, template, cold-retry, C0b landing, CA5a, public-tip guards, migrations, table roles, the PR-4 archive test; `-n 6`, 5G) | **611 passed** (2 min 39 s) |
| Full suite at `6eb2f5106` (`flock`, 10G/2G scope, `pytest -n 8 --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml`) | **22,866 passed, 1 failed**, 89 skipped, 47 xfailed. pytest 2,122.1 s (35:22); wall 35 min 25 s after a 37 min wait for the lock. The failure, `test_stuck_prompt.py::test_kill_switch_restores_dont_know_exactly` (field mass 0.7 vs 0.6786), **passed 3/3 alone**. It is timing-sensitive under load, and neither its file nor its code is touched by this branch. An earlier full run, started before CA5 reached main, was stopped at 46% to merge CA5 and was not counted. |
| Durability (`-m durability`, 5G, `-n 6`) | **177 passed**, 1 skipped (58.7 s; wall 60 s). Run in its own 5G scope without the lock: the lock queue held three other landings, and this lane is about a minute long. |
| Owner lane (`-m owner_vaults`, 5G, `-n 6`; fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}` in `fixtures-local/owner-lane-rw6b/`) | 83 passed, **2 failed**, 4 skipped (50.0 s; wall 51 s). The failures are exactly the expected `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies[arxiv_v2]`. |
| Frontend (`apps/learnloop-tauri`) | `npm install` ok; `npm run typecheck` clean (13 s); whole vitest (`--maxWorkers=4`, 5G): **238 files, 2206 passed** (54 s); `npm run frontend:build` ok; `cargo check --manifest-path src-tauri/Cargo.toml` ok |

### Parity on owner copies (`fixtures-local/landing-rw6b/`)

**Setup.**
- Fresh backup-API copies of the three mvp035 owner copies were taken. Routes were neutralized to the
  `127.0.0.1:9` blackhole with key variables unset, and rewrite/rerank/dense/embeddings were turned off.
- Main's code (`git archive 2c3507003`) and the merged branch's code (`git archive 6eb2f5106`) each came with their
  own `migrations/`.
- Everything ran under `env -i` with an empty `HOME`, `CODEX_HOME` and config dir. Audit hooks logged every process
  start and refused any non-loopback socket. **The audit log stayed empty: no process start and no socket connect
  in any run.**
- Only counts, hashes and status codes were recorded. Drivers: `scripts/rw6b_{a,b,b2,c,d,e}.sh`.

**(a) `upgrade --to mvp-0.38`, main's code vs the branch's.**
- Each side ran the upgrade, a primary sidecar load and `rebuild-derived-state`.
- The branch's databases differ from main's only by migration 227's five objects: an empty `reader_session_digests`
  plus a `schema_migrations` row. `sql_diffs` is empty, there are no added columns, and the row differences are
  exactly the main-vs-main noise floor (`a_main2`).
- fk 0/0 and integrity ok.
- Shadow is **0/0/0** on both sides for all three copies. `doctor` is identical (57/1, 102/48, 76/47 issues/errors,
  the known content errors).

**(b) `upgrade --to mvp-0.39` (from the mvp-0.38 copies) and a bare upgrade from mvp-0.35.**
- **The upgrade:** it prints `mvp-0.38 -> mvp-0.39` and leaves no journal. A bare `upgrade` from mvp-0.35 prints
  `mvp-0.35 -> mvp-0.39`.
- **Learner state:** 0 LOs moved, 0 schedules moved, and every row of the predecessor is preserved. The activation
  rewrites the derived facet tables with equal counts, refreshes `parameter_registry` (352 rows), and adds one
  rebuild receipt and one manifest.
- **Serving:** Today is **identical** after the version stamp (525,266, 740,827 and 344,204 bytes). The daily plan
  picks the same blocks and items. Only the router card's version-bearing hashes move (`content_hash`, `card_hash`,
  `snapshot_hash`), checked mechanically.
- **Shadow:** right after the upgrade, every changed row differs **only** in its `algorithm_version` stamp (21/18/34
  LOs), as with the mvp-0.38 upgrade. After `rebuild-derived-state`, which the upgrade itself prints as the next
  step, the shadow is **0/0/0** for the direct and the chained upgrade.
- **The first Today, as copied:** none of the three copies has a reader session (no `reader_view_opened`), so
  nothing waits and nothing is planned. The Today build takes 0.06–0.22 s, and shadow is 0/0/0 afterwards.
- **The first Today, with one seeded ended session with activity:** the session was seeded through product APIs at
  T = 2026-10-30 15:00Z: a visit, a `work_through` workbench session with the book visible and two steps, and, on
  probability and arxiv_v2, a self-graded attempt with one hint. Today was then built through `get_today_queue`
  at 2026-10-31 13:00Z.
  - Today returned in **0.28/0.11/0.11 s** (linear_algebra/probability/arxiv_v2) while `reader-followups` started in the background, so planning never
    blocks Today.
  - The job raised one `discriminate` question (an open probe episode) on each copy.
  - **No model call:** linear_algebra's relevance judge did not run ("metered rerank route without
    `practice_index.rerank_price_per_million`"), so its digest stays `incomplete` and is re-asked at the next
    build. On probability and arxiv_v2 the pool was empty, so the digest is `planned` with no check.
  - **0 follow-up commitments.** Coming up renders 0/0/0. A second Today the same day behaves the same.
  - Shadow is **0/0/0** both before and after the Today build.
- **0 new `model_call_receipts` rows** in any of the 69 databases (probability's 56 historical rows are unchanged).

**(c) `followups.enabled = false` at mvp-0.39 reproduces mvp-0.38.**
- Comparisons ran on the plain copies and on copies seeded with the same reader session.
- The Today queue (`build_due_queue`, three session modes) and the sidecar's Today summary are **identical** to the
  mvp-0.38 copy after the version stamp on all six pairs.
- The daily plan is identical apart from the router card's version-bearing hashes.
- With the switch off, the seeded session plans nothing: no digest and no commitment.

**(d) An interrupted mvp-0.39 activation** (the process dies right after the config publication, before the
activation commits): the label reads mvp-0.39 and the journal stands.
- `upgrade --to mvp-0.39` completes it. A second run is refused: "vault is already mvp-0.39".
- The desktop start (`SidecarContext.load`) completes it.
- After completion, the database equals the clean upgrade's with 0 normalized row differences and 0 LOs moved.
- The attaches that may not complete it refuse with the journal message: `Repository`, `open_vault_repository`,
  the secondary sidecar attach and the remote `check_schema`.
- `doctor` **refuses** too (`InterruptedActivation`, printed as an uncaught traceback). This is main's behaviour:
  `ops/doctor.py` and `Repository.attach` are unchanged by this branch.

**(e) `ad report --json`.** There are no new denials: the guard reads `denials: 0` on every copy before and after
the upgrade and after the Today builds. Each upgrade command archives the log exactly once:
- probability's 6 historical denials are archived once by the mvp-0.38 upgrade (`…archived-mvp-0.35-to-mvp-0.38-…`);
- the later mvp-0.39 upgrade on those copies has nothing new to archive and writes none;
- the chained bare upgrade archives once as `…archived-mvp-0.35-to-mvp-0.39-…`.

### Orchestrator landing ruling

The last Sol verify (job 20261031-213011-RfteNw) confirmed every earlier finding fixed. It raised one remaining
Medium:
- A regrade of a sibling attempt that lands DURING re-valuation's valuation window can make a `below_stop`
  retirement of a shared check stale. The guard compares the digest row, not outside evidence. This can retire a
  check that a reopened retention question still needed. Manual restore recovers it.

The ruling accepts it as LOW under the owner's proportionate bar:
- It needs a concurrent regrade of exactly the sibling that answered the question, inside a seconds-long window.
- The harm is one follow-up check not scheduled. It never serves an exposed check cold and never writes wrong
  evidence, and the learner can restore the check.
- This was the ninth review round on concurrency in the same subsystem.

It is recorded as an open item, with the suggested future fix: include the answering attempts' grade/revision ids in
the snapshot comparison.

The verifier also raised a Low: the production valuer may persist an idempotent calibration-channel snapshot before
the guard.

### Owner notes

- **Upgrade steps:**
  - back up the vaults;
  - close the desktop app, the MCP server and the phone page;
  - run `learnloop upgrade --to mvp-0.39` (a bare `learnloop upgrade` targets it; from mvp-0.35 it chains);
  - then run `learnloop rebuild-derived-state`, as the upgrade prints. The shadow is 0/0/0 only after that step.
- **Kill switch:** `[followups] enabled = false`. Off plans exactly as mvp-0.38 (parity (c)), and existing checks
  stay listed and can be undone. `formative_questions_enabled` is on and `generate_when_nothing_fits` is off.
- **The first Today after upgrading** plans the reader sessions that ended in the last 14 days, in the background.
  Each question is one paid relevance call (`practice_rerank`), within `followups.max_daily_cost_usd` ($0.50) and
  the source-service cap. Today itself is never blocked.
  - Your three vault copies have no reader sessions, so there is nothing to plan on them now.
  - A metered rerank route without `practice_index.rerank_price_per_million` skips the relevance judge. The session
    then stays `incomplete` and is retried at later builds, with no call.
- New vaults start at mvp-0.39.

### Open items

1. **F8:** the deferred textbook-exercise import.
2. **A formative-only retention question** with no FSRS state and no practiced attempt is dated at
   `followups.max_wait_days`, labelled `capped`. The alternative is a seeded, learned fallback prior.
3. **Generation stays off** (`generate_when_nothing_fits`) until PF exposes a source-anchored request API.
4. **Decision-mode seeding is one measurement.** It is not a conditional EVSI over the seeded check's branches.
5. **The paging bound is conservative.**
6. **A check whose digest row is gone stays held** (`licensing_unreadable`). Re-valuation retires it and re-asks.
7. **The accepted Low race** (the ruling above). Suggested fix: compare the answering attempts' grade/revision ids in
   the re-valuation snapshot.
8. **The production valuer may write an idempotent calibration-channel snapshot before the guard** (the verifier's
   Low).
9. **Landing observations:**
   - A C0b Check once on the follow-up's own item replaces the follow-up, by DL2's rule (see (i)).
   - `doctor` on an interrupted activation refuses with an uncaught traceback rather than a clean message. This is
     main's behaviour.
   - `test_stuck_prompt::test_kill_switch_restores_dont_know_exactly` is timing-sensitive under load.
