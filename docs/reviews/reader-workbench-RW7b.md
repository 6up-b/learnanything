# Reader workbench RW7b: the plan follows the reading path

Stage `reader-rw7b`, branch `reader/rw7b` in `learnanything-dl2`, base `fa2eb72f8` (main with T1, AD2+AD3 `mvp-0.30`,
RW2d `mvp-0.31`, local retrieval P1 (migration head 220), UX3, TE0 and S0). Spec: `docs/specs/spec_reader_workbench_v1.md`
§10.2, G47 and §13's test list (`test_plan_follows_path.py`); UX `ux_reader_workbench_v1.md` §4.11 ("the plan's reading
block names the section the path chose and why"); DL1 `spec_daily_loop_v1.md` §6.10; the learner field's F3 (a change to
what is served is a successor with receipts).

## 1. What changed

DL1's reading block (`daily_plan.reading.next_reading_target`, called once when a plan is built) now opens the next
unfinished **core** or **prerequisite** section of the source's reading path instead of the next section in the
predecessor's order:

* **The order stays the predecessor's.** The path narrows it, it does not replace it: U4's "continue from the furthest
  section read" (or DL1's book order with `plan.reading_from_furthest = false`), the front-matter rule and the exam filter
  run first, then only the path's plannable sections remain (`section_filter`, a per-reading predicate threaded through
  `next_reading_target`). "Continue from the furthest" still counts every section read into, a skipped enrichment
  section included.
* **The labels are the Guide's.** `source_retrieval.reading_paths.plan_path` reads RW7a's rows at the learner's depth
  (`depth_choice`: the newer of the Guide's choice and DL2's mapped intent): the judge's rows **for the current state
  key only**, with the honest-label rule (`honest_label`) re-applied at today's LO statuses and the learner's choices on
  top. One rule, `effective_label`, is now shared by the Guide's `path_view` and the plan (a pure extraction; RW7a's
  golden guide output is unchanged).
  * `core` and `prerequisite` are planned; `enrichment`, `already_shown`, `assumed` and a "skip it" never are; "read it
    anyway" makes a section core.
  * **A stale path is not followed** (Codex review F2; RW7a's handoff default): when only an older state was judged (a
    changed goal, LO status, section list or role), the reading keeps the predecessor's order and the receipt names the
    path `stale`; no model is called (the Guide re-judges on its next open). So a stored `already_shown`, `assumed` or
    `enrichment` whose state moved never steers the plan.
  * A fresh judgment names every sendable section (its key hashes the section list); a section it does not name (only
    a withheld one) is never planned through the path, so the plan never says "on your reading path" for a section the
    Guide does not list.
* **Where there is no path**, nothing changes: a reading with no depth chosen, or nothing judged at that depth, keeps
  the predecessor's order (so does a stale path, recorded). A path that cannot be read (an exception) does the same and is recorded as `unreadable`.
* **Exam protection only tightens.** A reading held out whole (or whose exam predicate cannot be read) is `withheld`:
  followed, it plans nothing. A withheld section is never the path's step, even in DL1's exact selection
  (`reading_rule = "dl1"`, where the predecessor has no exam filter).
* **A source whose core path is finished offers no reading** ("enrichment is never planned"); the next as-you-read
  source is tried.
* **No model in the plan.** The plan never calls the judge; it reads stored rows once, at its build. Serving, AD's slot
  phases and the reading step read the plan's record.
* **The switch reaches a plan already built** (Codex review F1). When `plan_uses_path` or the Guide's `enabled` is
  turned off after a plan's reading was chosen by the path, the next reconcile (every plan RPC) puts the predecessor's
  reading back while no reading of that plan has started or ended: a staged, unstarted path reading block is ended
  unread (`block_ended` `{"outcome": "displaced", "reason": "reading_path_off", "minutes_counted": 0.0}`; it counts no
  minutes and is no reading of the day), the split's `reading` becomes the receipt's `predecessor`, its full minutes and
  the admitted new minutes are recomputed (the lanes re-split from the build's loads when they moved, with a new epoch),
  and the receipt gains `transition` (when, the switch values, from/to, the minutes before and after, the displaced
  block ids). A reading the learner began, or one already ended, is history and is kept. Recorded once: switching back
  on does not re-read the path. A plan with no receipt (built off) is never touched. A plan that closed by itself
  only for want of the reading the path left out (`complete`, its newest stop the boundary finding nothing feasible,
  no reading in its split and no reading block) is reopened with the predecessor's reading, and the transition's
  `reopened` records the status, stop reason and completion time it had (fix round 2); a plan the learner ended
  ("Done for today", `stopped`) or the chooser stopped with work feasible stays closed. A withdrawn block is no
  reading of the projection either (`simulate_blocks`).
* **The why** (UX §4.11): the chosen target carries `path_label`; the staged frame's reason code is `reading_path_core`
  or `reading_path_prerequisite` ("Next on your reading path: §, central at the depth you chose." / "..., which the
  sections after it build on."; both pass the copy deny-list), and the logged lane reason gains ", core on your reading
  path". `ReadingTarget.as_dict` omits `path_label` when it is None, so a target the path did not choose is stored
  exactly as before.
* The display-only notes RW7a wrote (the module and store docstrings, the config docstring, the `reading_paths`
  disclosure) now say the plan reads the path at RW7b's tag.

## 2. The successor

* **Tag**: `READING_PATH_PLAN_ALGORITHM_VERSION = "mvp-0.32"`, appended to `SUCCESSOR_CHAIN` after RW2d's `mvp-0.31`;
  gate set `READING_PATH_PLAN_VERSIONS`. The number is in that one constant.
* **Gate**: `daily_plan.engine.reading_path_plan_active(vault)`: the plan acts (`plan_active`), the version is in
  `READING_PATH_PLAN_VERSIONS`, `reading_paths.plan_uses_path` is on **and** the Guide's `reading_paths.enabled` is on
  (the plan never follows a path the learner cannot see; open question 1).
* **Kill switch**: `reading_paths.plan_uses_path` (default true; classified in the parameter registry as a structural
  kill switch: the rule is the path's own labels and the learner's choices, with no weight, margin or threshold to learn
  (the 2026-10-24 rule); `PLANNED_LABELS` is the spec's set, not a tuned constant).
* **Upgrade**: `learnloop.reading_path_plan_upgrade.upgrade_to_reading_path_plan` (RW2d's shape): the predecessor, or
  `mvp-0.9` onwards through RW2d's chained upgrade; a tag change plus the idempotent rebuild of the same projection
  namespace; nothing rewritten (RW7a's tables are append-only and their meaning is unchanged). `learnloop upgrade`
  defaults to it; `--to mvp-0.31` still reaches RW2d. The new top-level module is in pyproject's
  experiments-stay-outside-production contract.
* **Defaults snapshots**: every snapshot recomputed (the effective config gains one key, inert below the tag); dropping
  the key reproduces all 22 prior values exactly (checked under `env -i`), and `mvp-0.32` has its own entry.
* **No migration.**

### Landing (renumbering)

If the tag must move (the LP-min claim fixes are also a successor after `mvp-0.31`): the constant in
`algorithm_versions.py`; if the predecessor moved, `PREDECESSOR` and `_upgrade_to_predecessor` in
`reading_path_plan_upgrade.py`; the snapshot key in `config/template.py` (recompute with
`defaults_fingerprint_for_version`) and the "inert below mvp-0.32" comment lines; the literal `mvp-0.32` in the CLI
upgrade docstring, the concept page row and the spec's as-built note; the chain-tail pins in the tests
(`git grep '"mvp-0.32"' tests`; 23 files moved by one link here, see §6); `tests/cli_help_snapshot.json`
(`python tests/test_cli_help_snapshot.py --write`). The receipt version `reading_path_plan_v1` names no tag.

## 3. Receipts

`split_json["reading_path"]` on the plan row (the plan's own WORKFLOW state; replay never reads it):

```json
{"version": "reading_path_plan_v1",
 "predecessor": {"source_id": "...", "extraction_id": "...", "section_id": "sec_eigen", "section_title": "...",
                 "words_left": 27, "partial": false},
 "chosen_by": "path", "label": "prerequisite", "same_as_predecessor": false,
 "paths": [{"extraction_id": "...", "status": "path", "depth": "learn_to_use_it", "input_state_key": "...",
            "fresh": true, "judgment": {"state_key": "..."},
            "sections": [{"section_id": "sec_eigen", "label": "enrichment", "judgment_row_id": "rps_...",
                          "override_row_id": null, "override": null}, "..."]}]}
```

* Each followed path names the key of the learner's state now (`input_state_key`) and the key of the judgment whose
  rows it read (`judgment.state_key`, taken from those rows), with every section's effective label, the judge row and
  the learner's newest override row it came from (Codex review F3), so a later judgment or override cannot change what
  the receipt says was read (the tables are append-only). A `stale` path records `judgment: null` and the newest
  judged key it did not read (`latest_judged_state_key`).
* `transition` (F1, above) is added when the switch took the path's reading back; `transition.reopened` (fix round 2)
  when that also reopened a plan that had closed for want of it.

* `predecessor` is the section the predecessor's order would have chosen (the same call without the path), or null.
* `chosen_by`: `path` (the reading came through a followed path), `order` (from a reading with no path), null (no
  reading). `paths` lists every reading consulted, in visiting order, with its status (`path`, `withheld`,
  `unreadable`, `no_depth`, `not_judged`, `stale`).
* Written **only when a path was in play** (some status other than `no_depth` / `not_judged`): a vault without judged
  paths plans byte for byte as the predecessor even with the successor on. Cheap (one more call of the predecessor's
  function); no table needed, hence no migration.

## 4. G47 evidence

`tests/test_plan_follows_path.py` (19 tests in the default lane, 3 owner-lane parametrizations):

* **What changes** (through `get_daily_plan` and the engine's `_reading_on_path`): enrichment first, a prerequisite
  second: the plan opens the prerequisite, the receipt has the predecessor's `sec_eigen`, the projected block's why says
  "prerequisite on your reading path"; core follows book order and finished sections are passed; enrichment, already
  shown and assumed are never planned and a finished core path offers no reading while the receipt keeps the
  predecessor's section; "read it anyway" makes enrichment core, "skip it" leaves a section out and marks nothing known;
  a stored already-shown that no longer holds leaves the stale path to the order (review F2); no depth, nothing judged and an
  unreadable path keep the order (no receipt where no path was in play); a held-out section is never the path's step
  even in DL1's exact selection; an exam reading plans nothing through its path.
* **Off is the predecessor** (the switch off, and the Guide off): on the same path vault (paths, depths and overrides
  stored), `get_daily_plan`, `get_today_queue`, `next_plan_item` and every `daily_plans`, `attention_blocks` and
  `attention_block_events` row are equal to the predecessor's, up to the ids a build mints, the version label, and two
  hashes computed over those ids (`content_hash` over the plan id, `card_hash`); two builds of one vault at one
  version differ in exactly those two keys (checked). With the successor on, the same comparison differs (the test can
  see the change).
* **Fixture copies**: backup-API copies of the tracked head fixture `fixtures/migration_head_220` at the predecessor,
  at the tag with the switch off, with the Guide off, and on: all equal as above (the copy has no judged path, so on is
  the predecessor too). The owner lane's three working vaults run the same comparison when `LEARNLOOP_OWNER_VAULTS` is
  set (skipped here: the stage never opens the owner's vaults).
* **Zero projection deltas**: a rebuild with the switch on and one with it off leave every DERIVED table equal, and
  neither reads a path (`plan_path` is never called).
* **AD composes** (AD2+AD3's inversion): after the build, serving two plan items (AD's slot phases ran: the test
  asserts it was not vacuous) and reopening the plan never read a path, and every `slot_facts.for_slot` call saw the
  record's path-chosen reading. AD reads only SlotFacts; the plan computes them from its record (`_context` reads
  `split["reading"]`), so the admitted pool AD draws from is the plan's whatever chose the reading. RW7b adds no AD read
  (`reader_path_sections` stays "AD reads no reading path" in AD's column classes) and no plan read inside an AD
  operation (the plan is built outside any).
* The vocabulary (one constant after RW2d, the gate set, the snapshot), the switch (default, classification, the tag,
  the Guide, the plan's own switch), the why codes and their plain copy, `ReadingTarget`'s stored shape, the upgrade
  (direct, chained from `mvp-0.29` and `mvp-0.30`, refused from `mvp-0.8`, CLI default).

**Fail-first.** On the base the new test file cannot import (no tag). A base-compatible probe (four tests importing no
RW7b name, at `LATEST_ALGORITHM_VERSION`: enrichment not planned, "skip it" not planned, the receipt's predecessor
section, and a no-label control), run against `fa2eb72f8`'s `src`, `migrations`, `tests` and `fixtures` extracted with
`git archive` into the scratchpad (`PYTHONPATH` = that tree): **3 failed, 1 passed** (the control). The same file on the
branch: 4 passed. The probe was deleted.

## 5. Calls and cost

No model is called anywhere in RW7b (the plan reads stored labels; the tests use `PathJudgeFake`). No paid call was
made; every script outside pytest (the snapshot check, the CLI help snapshot, the reference generator and validator)
ran under `env -i` with an empty `HOME`/`CODEX_HOME`/`LEARNLOOP_CONFIG_DIR`. Spend: $0.

## 6. Gate (this step; the full suite runs once in the landing gate)

All inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, one run at a time:

* `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
* `uv run lint-imports --no-cache`: 36 kept, 0 broken (run at the start and again after the last change).
* `uv run pytest -n 6` over 183 files: first run **9,638 passed, 8 failed, 21 skipped** (47 min 31 s; the skips are owner-lane and optional-extra lanes). All 8 failures were further chain-tail pins of the same kind (chain slices, version sets written with `LATEST_ALGORITHM_VERSION`, the recurrence set literal) and RW7a's own `[reading_paths]` key list (`test_reading_paths.py`, which now names `plan_uses_path`). After fixing them, the 8 files they were in (`test_method_explicit_upgrade.py`, `test_reading_paths.py`, `test_mvp018_upgrade.py`, `test_mvp022_upgrade.py`, `test_mvp023_upgrade.py`, `test_mvp024_upgrade.py`, `test_recurrence_commands.py`, `test_required_method_grading.py`) were rerun in full: **183 passed**, 0 failed (7 min 49 s). The new file `test_plan_follows_path.py`: 19 passed, 3 skipped (owner lane).
* `db_generate_reference.py` and `db_validate_reference.py`: regenerated (no schema change; the config reference gains
  `reading_paths.plan_uses_path` and line citations moved); the two prose leaf counts moved 1,047 -> 1,048; 0 errors.
* No migration or DB/connection code: no durability run. No frontend or `src-tauri` change: no npm, vitest or cargo
  run.

Chain-tail pins moved by one link (23 test files): negative `SUCCESSOR_CHAIN` indices shifted, version sets ending at
`mvp-0.31` gained `mvp-0.32`, the latest literal and the CLI default's output moved to `mvp-0.32`; RW2d's own test
upgrades with `--to mvp-0.31` and pins its tag as `SUCCESSOR_CHAIN[-2]`.

The files: `test_ad1_codex_rereview_fixes.py`, `test_ad1_codex_review_fixes.py`, `test_ad1_outside_and_cli.py`, `test_ad23_contract.py`, `test_ad23_fix_r5.py`, `test_ad23_fix_r8.py`, `test_ad23_fix_review.py`, `test_ad23_intent_compose.py`, `test_ad23_inversion.py`, `test_ad23_owner_decisions.py`, `test_ad23_pool_membership.py`, `test_ad23_successor.py`, `test_ad2_model.py`, `test_ad2_serving.py`, `test_ad3_monitoring.py`, `test_ad3_reading.py`, `test_ad3_relatedness.py`, `test_ad3_subject_view.py`, `test_adaptive_difficulty_ad1.py`, `test_ad_epoch.py`, `test_ad_guard.py`, `test_ai_config.py`, `test_architecture.py`, `test_assumed_known.py`, `test_block_chooser_interface.py`, `test_chatgpt_plan_provider.py`, `test_chatgpt_plan_workspace.py`, `test_cli_help_snapshot.py`, `test_compare_keep_switch_off.py`, `test_config_refactor.py`, `test_constraint_engine.py`, `test_coordinated_migrations.py`, `test_daily_plan_admission.py`, `test_daily_plan_build.py`, `test_daily_plan_composition.py`, `test_daily_plan_kill_switch.py`, `test_daily_plan_owner_decisions.py`, `test_daily_plan_reading.py`, `test_daily_plan_reentry.py`, `test_daily_plan_replay.py`, `test_daily_plan_review_regressions.py`, `test_daily_plan_rpc.py`, `test_daily_plan_split.py`, `test_decider_landing.py`, `test_desktop_rpc_contract.py`, `test_diagnosis_context.py`, `test_diagnosis_history_modes.py`, `test_diagnosis_input_provenance.py`, `test_dl2_rw4b_keyed_pick_check.py`, `test_duration_estimates.py`, `test_e0_isolation.py`, `test_evsi_staged_binding.py`, `test_exam_protection_identity.py`, `test_exam_protection_landing.py`, `test_exam_protection_review.py`, `test_field_workbench_signals.py`, `test_figures_switch_off.py`, `test_forecast_receipts_landing.py`, `test_forecast_receipts.py`, `test_grading_cli.py`, `test_instructional_layering.py`, `test_intent_codex_rereview.py`, `test_intent_codex_review.py`, `test_intent_exclusion.py`, `test_intent_fix_round4.py`, `test_intent_fix_round5.py`, `test_intent_fix_round6.py`, `test_intent_fix_round7.py`, `test_intent_goal_deadline.py`, `test_intent_orchestrator_rulings.py`, `test_intent_plan.py`, `test_intent_recall_targets.py`, `test_intent_resolution.py`, `test_judge_routes.py`, `test_kinship_feature.py`, `test_km2b_consumer_rekey.py`, `test_learner_pick_proposal.py`, `test_learner_text_gaps_composition.py`, `test_library_exercises.py`, `test_mcp_c1a_landing.py`, `test_mcp_c1a_narrow.py`, `test_mcp_tools.py`, `test_method_explicit_landing.py`, `test_method_explicit_upgrade.py`, `test_mobile_allowlist.py`, `test_model_grade_lane.py`, `test_mvp010_upgrade.py`, `test_mvp011_upgrade.py`, `test_mvp013_upgrade.py`, `test_mvp014_upgrade.py`, `test_mvp015_upgrade.py`, `test_mvp016_upgrade.py`, `test_mvp017_upgrade.py`, `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py`, `test_mvp021_upgrade.py`, `test_mvp022_upgrade.py`, `test_mvp023_upgrade.py`, `test_mvp024_upgrade.py`, `test_open_world_gate.py`, `test_p0_cutover_mvp08.py`, `test_pfc_unverified_unassessed.py`, `test_plan_determinism_landing.py`, `test_plan_determinism.py`, `test_plan_first_transport.py`, `test_plan_follows_path.py`, `test_probability_cli.py`, `test_public_tip_guards.py`, `test_reader_guidance.py`, `test_reader_intentions.py`, `test_reader_intent.py`, `test_reader_recap_review_r2.py`, `test_reader_recap_review_r3.py`, `test_reader_rw2b_review.py`, `test_reader_rw3a_landing.py`, `test_reader_rw3b_protection.py`, `test_reader_rw4b_admission_idempotency.py`, `test_reader_rw4b_fix6.py`, `test_reader_rw7a_migration.py`, `test_reader_tutor_switch_off.py`, `test_reading_paths.py`, `test_reading_step_switch.py`, `test_recurrence_commands.py`, `test_reference_gate_imports.py`, `test_registry_audit.py`, `test_regrade_contract_replay.py`, `test_regrade_contract_successor.py`, `test_regrade_contract_upgrade.py`, `test_required_method_authority.py`, `test_required_method_grading.py`, `test_required_method_reopened.py`, `test_required_method_rereview.py`, `test_required_method_round3.py`, `test_required_method_round3_review.py`, `test_reread_safety_landing.py`, `test_router_card.py`, `test_router_g1_feasibility.py`, `test_router_g4_restraint.py`, `test_router_g7_fallback.py`, `test_router_p2_bridge.py`, `test_router_presentations.py`, `test_router_r1_composition.py`, `test_router_r2a_landing.py`, `test_router_r2a_serving.py`, `test_router_r2b_agreement.py`, `test_router_r2bc_landing.py`, `test_router_r2b_requests.py`, `test_router_r2b_serving.py`, `test_router_r2c_retrieval.py`, `test_router_r2c_teach_back.py`, `test_route_rules_in_grader.py`, `test_router_why_copy.py`, `test_rw2c_switch_off.py`, `test_rw2d_receipts_migration.py`, `test_salience_firewall.py`, `test_sensitivity_certificates.py`, `test_serve_eligibility.py`, `test_serve_eligibility_review.py`, `test_sidecar_serializer_snapshot.py`, `test_source_exercise_rpcs.py`, `test_source_first_needs.py`, `test_source_roles.py`, `test_sqlite_file_copies.py`, `test_stuck_prompt.py`, `test_success_head_cli.py`, `test_success_head.py`, `test_table_roles.py`, `test_teach_back.py`, `test_teacher_te0_confidence_events.py`, `test_teacher_te0_review_fixes.py`, `test_tier1_decider.py`, `test_today_headline.py`, `test_tracked_fixture_databases.py`, `test_ux_phase1_landing.py`, `test_ux_phase1_round2_rereview.py`, `test_ux_phase1_round2_review.py`, `test_ux_phase1_usability_round1.py`, `test_ux_phase2_shell.py`, `test_ux_phase4_feedback.py`, `test_ux_phase4_landing.py`, `test_voi_merge_composition.py`, `test_voi_stopping.py`, `test_voi_v2.py`.

## 7. Open questions

1. **The Guide's switch gates the plan too.** With `reading_paths.enabled` off the plan ignores stored paths, so it never
   follows a path the learner cannot see. The spec names only `plan_uses_path`; the owner may prefer it alone.
2. **Stale paths fall back to the order** (changed by the Codex review, F2, to RW7a's handoff default). When the
   learner state moved since the last judgment the plan keeps the predecessor's order for that reading and records the
   path as `stale`; it never triggers a judgment. A depth set through DL2's intent with no Guide visit has nothing
   judged, so it keeps the predecessor's order until the Guide judges it. Since the key hashes LO statuses, the path
   steers the plan only after a Guide open has judged the current state.
3. **A finished core path offers no reading** from that source (enrichment is never planned, §10.2), even where the
   predecessor would go on to an enrichment section; the learner can still "read it anyway".
4. **The report row** "after RW7b, misses on LOs whose core section was skipped" (§15's reading-path row) is built in
   the Codex review fix step (F4): `learnloop reader report`'s `reading_paths.skipped_core`, through the adapter
   `reading_paths.skipped_section_learning_objects` (the section-to-LO map, read through a read-only attach). A miss is
   an unaided graded attempt on a skipped section's LO after the skip and before the learner's next choice on that
   section, below the association reports' existing success line (`intervention_outcomes.SUCCESS_CORRECTNESS`; no new
   threshold); held grades are no outcome.
5. **The receipt lives in `split_json`**, not a RECEIPT table: the plan is built once a day and its row is the plan's
   own durable record; a table would need a migration the spec says RW7b does not need.

## Landing onto main

(To be written at landing.)
