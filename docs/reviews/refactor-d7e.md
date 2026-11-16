# Refactor D7, batch 3, part 1: kill switches at or below the floor (Today: the plan, the router frame, reading paths, intent, capture)

Step D7 batch 3 of arc D (`docs/specs/refactor_strategy_v3.md` §2.6), on branch `refactor/d7e-switches-today`, based on `250b0e16fe` (batch 1 part 4, the diagnosis split pair, merged with main). The rule, the precondition and the conventions are batch 1's (`docs/reviews/refactor-d7a.md` §1-§9): ADR-019's rule (owner, Nov 12; L7), and the owner's run of `scripts/vault_report.py` on Nov 14 (no live or retired vault sets any tagged switch). For every vault the owner has, each switch removed here is at its default, so removing it with its off branch changes nothing that vault computes.

**This landing is the batch's first boundary.** It removes seven of the batch's fourteen switches, the brief's group 1: `adaptive_difficulty.generation_contract`, `router.probe_tie_admission`, `intent.enabled` and `intent.recall_targets_enabled`, `followups.enabled`, `reading_paths.plan_uses_path`, `curriculum.plan_uses_path`. What remains is in §9. Line numbers are the base's (`250b0e16fe`). **Part 2** (the batch's second landing: the lesson-suggestion pair, `teacher.probes`, `data_capture.serving`) follows §11, as §12-§22.

Inventory: `docs/reviews/refactor-d7-inventory.md` §1.3, §1.4, §4 batch 3. Each row's class was checked at this tip before its removal: all seven are class A (a predecessor nothing needs, no identity that `RETIRED_FIELDS` cannot hold).

## 1. Which tests reached a predecessor through `tests/successor_switches.py`

Before any test was touched, the whole landing lane (1,429 test files, 15 chunks of 100 at `-n 4 -m "not arc_close"` behind `flock /tmp/learnloop-fullsuite.lock`) ran with a scratch plugin that deleted the rows of `router.probe_tie_admission` and `intent.enabled` from `SWITCHES_BY_TAG` and recorded, per test, which of the batch's six helper keys `serve_as_at` would have written with the original table. (`adaptive_difficulty.generation_contract`'s source edit was in the tree for the later chunks; its only effect in that run was the two `test_retired_config_identities` failures that `_pre_arc_c_shape` then fixed.)

| key in the helper | tests it was written for | files | tests that failed without it |
|---|---:|---:|---:|
| `router.probe_tie_admission` | 340 | 64 | 5 |
| `intent.enabled` | 898 | 123 | 4 (one of them also through probe ties) |
| `router.lesson_suggestions.enabled` (group 2) | 1,125 | 154 | not removed |
| `router.lesson_suggestions.in_objective` (group 2) | 1,515 | 223 | not removed |
| `teacher.probes` (group 2) | 1,497 | 217 | not removed |
| `data_capture.serving` (group 2) | 1,186 | 167 | not removed |

The failures, all of them (8 cases in 2 files), and what became of each:
- `test_intent_codex_rereview::test_f2_at_the_predecessor_commitments_change_nothing`: **deleted** (off equals mvp-0.27: commitments change nothing below the tag).
- `::test_f2_below_the_tag_a_paused_items_cold_retry_is_still_served`: **twin, on side kept** (`test_f2_a_paused_items_cold_retry_waits`).
- `::test_f2_the_intent_control_is_off_below_the_tag`: **twin, on side kept** (`test_f2_the_intent_control_is_on`: `get_intent` answers `enabled: true`).
- `::test_f2_the_gate_reads_the_version_and_the_switch` (written both keys): **deleted** (the predicate).
- `test_router_probe_ties::test_a_probe_near_tie_carries_a_true_propensity_only_at_the_successor`: **twin, on side kept** (`test_a_probe_near_tie_carries_a_true_propensity`).
- `::test_kill_switch_serves_the_predecessors_probe_offer_exactly`: **deleted** (off equals mvp-0.14).
- `::test_teach_back_items_are_probe_near_ties_at_the_successor[mvp-0.14--False]`: the case **deleted** with the switch-off case; the test keeps its successor case, unparametrized (`test_teach_back_items_are_probe_near_ties`).
- `::test_a_greedy_probe_presentation_carries_no_exploration_mark`: **moved to the head**; its vault was at mvp-0.14 only to get a greedy build (the predecessor never displaced a probe); at the head a roll above the rate gives the same greedy build, and every assertion stands.

The other 335 probe-tie and 894 intent cases pass without their predecessor: their old tag was only how they were built (or holds another successor's switch, still listed), so they were left as they are; how many still open a vault below the floor is the census's (§7). Then the two rows left the helper with their switches (`8614d97f81`, `4ddb8d9e9b`). Its own test needed one change: the duplicate-table check used `[intent]`, a table the helper no longer writes, and now uses `[teacher]` (`teacher.enabled` stays in the helper). The other five switches of this part were never in the helper.

## 2. Step 0, per switch

"Whole-config digest" is `content_key(identity_dump(config))`, which every switch enters and `RETIRED_FIELDS` keeps (§4). None of the seven is named by `projection_switches`, `objective_settings`, `followup_switch_snapshot`, `draw_inputs` or `router_settings`. None is read by replay or a rebuild's replayer (§5's real rebuilds agree).

### `adaptive_difficulty.generation_contract` (mvp-0.30)

- **Reads:** one predicate, `successor.generation_contract_on` (`switch_on(config, "generation_contract")`: AD's master switch and the field), through `generation.contract_on` (`generation.py:128`) and its callers: `commission_point` (`:185`), `queue_commission_generation` (`:292`, which also asked `successor_active`), `practice_generation._ad_material_view` (`:530`), `_ad_commissioned_rung` (`:551`), the commission job `jobs._handle_ad_commission` (`:3450`).
- **Off code:** none of its own: with the contract off, every caller takes the incumbent's target path, which AD's master switch off (class C, kept) also takes. So the conjunct goes: `contract_on` is `successor_active` (AD on). `generation_contract_on` and the `SWITCHES` entry go; `successor.settings` (test-only, ledger D7-5) loses the key with `SWITCHES`.
- **Monitoring:** no AD flag recommends it (`monitoring.FLAG_SWITCHES`), as the inventory found.
- **Stored:** the commission job's no-op result said `skipped_reason: "generation_contract off"`; it now says `"adaptive_difficulty off"` (the only way to reach it). Nothing reads the reason.
- **Surfaces:** no desktop, phone or sidecar reader.

### `router.probe_tie_admission` (mvp-0.15)

- **Reads:** `scheduler.probe_ties_admitted` (`:1160`, getattr default **False**, ledger D7-3's kind) in `_exploration_support` (`:1195`) and the offer trace (`:1331`).
- **Off code:** the predecessor's probe exclusion (`_exploration_support`'s two conjuncts) and `_is_probe_intent`, used only there. Deleted.
- **Stored:** the offer trace's `exploration.probe_ties_admitted` is held by the three due-queue goldens (`true`), so the trace keeps writing the constant `True`. The trace's `config_snapshot["router"]` dumps the live `RouterConfig` and loses the key; it enters the `today_offer` decision's `snapshot_hash`, an audit hash nothing recomputes (the router agreement report reads `snapshot_hash` only for decisions both models answered, never `today_offer`), and every router field added since moved it alike.
- **Surfaces:** none.

### `intent.enabled` and `intent.recall_targets_enabled` (mvp-0.29), one pair

- **Reads:** `serving.intent_enabled` (`:118`, getattr default **False**) in `intent_serving` (`:647`), `intent/report.py:24`, the sidecar's `get_intent` and `_require_enabled` (`handlers/intent.py:56`, `:67`); `recall_targets_enabled` in `intent_serving` (`:650`, `:736` into `IntentServing.recall_targets_enabled`, read by `target_for` `:357`), `daily_plan/intent_cost.py:72`, `daily_plan/reentry.py:144` and `intent/report.py:27`. The sub-switch is meaningful only under the first, so they go together.
- **Off code:** `intent_serving`'s early return (the predecessor's serving is what `intent_serving` returning `None` gives, which stays: it is the no-commitment path); the sub-switch's ternaries (every item at 0.90); `get_intent`'s off answer and the two writes' refusal (`intent_disabled`). `IntentServing.recall_targets_enabled` goes.
- **Stored and echoed:** `get_intent` keeps answering `"enabled": true`, the constant every vault saw, because the desktop's `IntentControl` reads it (`apps/learnloop-tauri/src/components/IntentControl.tsx:80`); the desktop is unchanged. `learnloop plan report`'s `intent` block stops echoing `enabled` and `recall_targets_enabled` (nothing compares them; no pin or golden holds them).
- **What the learner sees today with it on, and after:** desktop: the intent control on every scope (Master, Learn, ..., deadlines) and the cost line: unchanged (the response is the same). Phone: never reads intent's RPCs (desktop-only, allowlist). Serving and the plan: unchanged on every owner vault (§5: the due queue and a built plan on each copy are byte-equal).
- **Registry:** the intent recall targets' rule rationale named the sub-switch. A rewording moved five rows of every upgraded copy's `parameter_registry` mirror (P-shadow caught it), so the rationale keeps its bytes with a comment saying why (`895213968a`).

### `followups.enabled` (mvp-0.39)

- **Reads:** `reader_followups.followups_enabled` (`:155`, getattr default True) in `plan_session` (`:826`), `sessions_to_plan` (`:1137`), `revalue_pending` (`:1265`), `exposure_refresh_waiting`'s sibling (`:1452`), `coming_up` (`:1857`, echoed as `enabled`), the digest's `sessions_to_summarize` (`reader_digest.py:728`), and the sidecar's `prepare_followups` (`:75`) and `_require_on` (`:143`, before `reader.followup_restore`).
- **Off code:** the early returns; `sessions_to_summarize`, `summarize_ended_sessions` and `NOT_PLANNED_KEY` (the summary-only digest rows written for the narrative while follow-ups were off: their only callers were the sidecar's off arm); `_require_on` and the `followups_disabled` refusal. Deleted. A summary-only row a vault might hold (none on the copies: none of them ever turned the switch off) is an `incomplete` digest, which planning treats as any unfinished session, as before.
- **Echoed:** "Coming up" stops writing `enabled` (the timeline RPC and the recap card's `coming_up`); the desktop's `ReaderComingUpDto.enabled` was declared and never read: removed in the same commit with its test fixture (typecheck, vitest over `src/screens/reader`: 123 files, 1,482 tests).
- **What the learner sees, and after:** desktop: "Coming up" on the Reader card and Wrap up, the undo and restore actions: unchanged. Phone: none of these RPCs.

### `reading_paths.plan_uses_path` (mvp-0.32)

- **Reads:** `engine.reading_path_plan_active` (`:203`; getattr default **False**) with its four callers, and the receipts at `:4197` and `:4385`.
- **Off code:** shared. `_reading_path_switched_off` and the predecessor's reading order are also reached by `reading_paths.enabled = false` (the Guide's own feature switch, kept), so only the conjunct and the receipt key go.
- **Stored:** plan receipts (`split_json["reading_path"]`, workflow rows) recorded the switch at a transition (`transition.switch`, `moves[].switch`); nothing reads them back. They stop writing `plan_uses_path` and keep `enabled`.
- **Learner-facing text:** the reading-path disclosure (`ai/disclosures.py`) said "with reading_paths.plan_uses_path on, today's plan reads the labels"; it now says "today's plan reads the labels". No hash or pin holds disclosure text.

### `curriculum.plan_uses_path` (mvp-0.40)

- **Reads:** `engine.deliverable_plan_active` (`:223`, getattr default **False**, five callers including the sidecar's deliverable refresh gate), `deliverable_path.plan_refresh_reason` (`:1825`), and the receipt at `:4387`.
- **Off code:** shared with `curriculum.enabled` (class C, kept), as above: the conjuncts, the refresh reason's second line and the receipt key go.
- **Surfaces:** no desktop or phone reader; the sidecar's snapshot names neither plan switch.

## 3. What went

| commit | what |
|---|---|
| `b3d4fc623f` | the retired-config identity test for this batch (§4), recorded at the base and green there |
| `206a3a82a0` | `adaptive_difficulty.generation_contract` |
| `8614d97f81` | `router.probe_tie_admission` (and its helper row) |
| `4ddb8d9e9b` | `intent.enabled` and `intent.recall_targets_enabled` (and intent's helper row) |
| `30f6fea7e8` | `followups.enabled` (with the desktop's dead `ReaderComingUpDto.enabled`) |
| `d794e6f1b0` | `reading_paths.plan_uses_path` |
| `0a61836d96` | `curriculum.plan_uses_path` |
| `bf69152232` | the structure golden lowered (comments naming a stage artifact 2,374 to 2,371) |
| `99da63620e` | the vault's references regenerated (1,171 to 1,164 effective leaves) |
| `895213968a` | the intent recall targets' registry rationale keeps its bytes (§2) |

In each removal commit: the field into `RETIRED_FIELDS` (`removed_by` `D7`; `AdaptiveDifficultyConfig`, `RouterConfig`, `IntentConfig`, `FollowupsConfig`, `ReadingPathsConfig` and `CurriculumConfig` now keep retired fields; no section was left empty), `_pre_arc_c_shape` in `tests/test_retired_config_identities.py`, the kill-switch table row and its kept-because line, the registry rule (`followups.enabled`'s share of a rule, `reading_paths.plan_uses_path`, `curriculum.plan_uses_path`; the others had none of their own), the vault generator's field descriptions (`router.probe_tie_admission`, `intent.enabled`, `curriculum.plan_uses_path`), the tag's comment in `algorithm_versions.py`, and the effective-defaults golden (exactly the removed lines).

**Deletion proof** (strategy §2.1): `generation_contract_on`, `probe_ties_admitted`, `_is_probe_intent`, `intent_enabled` (the scheduling one; the sidecar's `reader_intent.intent_enabled` is another switch's and stays), `_require_enabled`, `followups_enabled`, `sessions_to_summarize`, `summarize_ended_sessions`, `NOT_PLANNED_KEY`, `_require_on`, `followups_disabled` searched over `src/`, `scripts/`, `tests/`, `apps/` and the vault's `_scripts/` as names and strings: no function-local or `importlib` import, no registry, Typer or `MODULE_INVENTORY` entry left.

## 4. Identities and stored snapshots

- **The retired-config identities.** `TODAY_SWITCHES_TOML` sets all fourteen of the batch's switches away from their defaults; `test_a_config_setting_todays_removed_switches_keeps_every_identity` pins, for the default config and that file, the whole identity dump and the sha256 of each touched section's identity dump, recorded at `250b0e16fe` with every switch present (the commit passed there on a `git archive` extract: 18 passed). The loading test now also loads a vault that sets all fourteen. **With each new entry removed** from `RETIRED_FIELDS` (a mutation, not committed), seven runs, the file fails six tests each time: both cases of the batch-1 and of this batch's identity test, `test_the_config_identity_reproduces_both_recorded_digests` and `test_an_embedding_compare_report_is_named_as_before_arc_c`. Restored: 18 passed.
- **`tests/test_identity_pins.py`:** unmoved at every commit; nothing written. C6 (`draw_inputs`) does not name any of these switches.
- **Snapshots, per switch:** `probe_tie_admission`: the trace's `probe_ties_admitted` keeps writing `True` (golden). `intent.*`: `get_intent`'s `enabled: true` kept (desktop reader); the plan report's two echoes stop. `followups.enabled`: "Coming up"'s `enabled` stops (no reader). The two `plan_uses_path`: the receipts stop writing the key. `generation_contract`: none stored.

## 5. Proof

**P-shadow** (`learnanything-ad1/fixtures-local/owner-copies-mvp058`, fresh `copy_tree_with_databases` copies; base `250b0e16fe` from a `git archive` of `src/` and `migrations/` on `PYTHONPATH`, branch at `895213968a`; counts only; copies deleted):

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| `learnloop upgrade`, both | `mvp-0.58 -> mvp-0.59` | same | same |
| shadow facet / mastery / schedule changed | 0 / 0 / 0 (80 / 21 / 99 unchanged) | 0 / 0 / 0 (3 / 18 / 77) | 0 / 0 / 0 (7 / 34 / 32) |
| `schedule_effects` due dates moved (items, cards) | 0, 0 | 0, 0 | 0, 0 |
| the two shadow reports, marker id, `as_of` and hashes aside | equal | equal | equal |
| every table of the two upgraded copies, row by row | 402 tables, 19,442 rows: none differ | 402, 10,426: none | 402, 23,877: none |
| the same after the shadow | none differ | none | none |
| the same after a real `rebuild-derived-state` on each side | 19,749 rows: none differ | 10,498: none | 23,719: none |
| Today on a copy of the rebuilt vault at 2026-11-15 12:00Z: `read_due_queue` (ids, priorities, components), the intent report (the two echoes aside), a built plan (split, admission, blocks) | byte-equal | byte-equal | byte-equal |

The first branch run (`0a61836d96`) found `parameter_registry` different in five rows on every copy: the intent recall targets' rationale (§2). Restored, and the branch side rerun: none differ.

**Old rows at the floor and the head** (`fixtures/mvp017_route_check_replay`, retagged to `mvp-0.58` and `mvp-0.59`, two live rebuilds per code, branch at `895213968a`): every table equal row by row after each rebuild at both tags except the one `attempt_debug_payloads` row of `att_02_svd_fail`, equal with replay's minted ids, stamps and digests normalized, as in batch 1.

**P-draw.** The router's pinned draws and the due-queue goldens ran unchanged at the default switches: `tests/test_due_queue_golden.py` (its three goldens) in each commit's gate and in the sweep; the router mixture, objective and lesson-suggestion files (which read `tests/pinned_draws.py`'s pins) in the sweep (§6). No golden or pin was regenerated.

**Goldens.** The effective-defaults golden lost exactly seven lines (`adaptive_difficulty.generation_contract`, `curriculum.plan_uses_path`, `followups.enabled`, `intent.enabled`, `intent.recall_targets_enabled`, `reading_paths.plan_uses_path`, `router.probe_tie_admission`) and gained none. The CLI snapshot did not change. The grade-application, due-queue and figure goldens ran unchanged in the sweep.

**The owner lane** (`-m owner_vaults`, 31 files, copies made with the gate's `owner_copy_make.py` under `fixtures-local/owner-lane-d7e`, deleted after): 92 passed, 8 skipped, as at part 4 of batch 1. One owner-lane test was edited (`test_plan_follows_path::_fixture_parity`, §6).

## 6. Tests

**Deleted** (each with its subject):
- `test_router_probe_ties::test_the_gate_is_the_switch` (the predicate), `::test_the_kill_switch_keeps_the_predecessors_probe_exclusion_exactly` (off), `::test_kill_switch_serves_the_predecessors_probe_offer_exactly` (off equals mvp-0.14), `::test_without_probe_candidates_the_successor_serves_exactly_as_mvp014` (2 cases: mvp-0.15 against mvp-0.14 with no probe, on and off; both sides now run the same code), the two non-successor cases of `::test_teach_back_items_are_probe_near_ties_at_the_successor`; `test_scheduler::test_selection_propensities_greedy_when_disabled_or_singleton_or_probe`'s probe-ties-off block.
- `test_intent_codex_rereview::test_f2_at_the_predecessor_commitments_change_nothing`, `::test_f2_the_gate_reads_the_version_and_the_switch`; `test_intent_codex_review::test_f2_with_intent_off_commitments_change_nothing_in_the_ranked_list_or_the_plan` and the intent-off half of `::test_f10_the_headline_leaves_out_excluded_los_and_items`; `test_intent_exclusion::test_with_intent_off_commitments_change_nothing_served`; `test_intent_rpc::test_with_intent_off_the_control_answers_off_and_refuses_writes`; the two switched-off halves of `test_intent_recall_targets::test_the_kill_switches`.
- `test_reader_followups::test_the_kill_switch_creates_nothing_and_runs_no_revaluation`; `test_reader_followups_successor::test_switched_off_the_today_queue_is_the_predecessors` (plan parity off) and the off case of the gate test; `test_reader_digest_narrative::test_with_follow_ups_off_an_ended_session_is_summarized_and_narrated`, `::test_no_summary_row_with_narration_off_or_follow_ups_live` (2 cases), `::test_the_queue_build_narrates_a_session_with_follow_ups_off` (the summary-only rows, with their helpers); the follow-ups-off half of `test_curriculum_c1_landing::test_i_…`.
- `test_ad23_fix_r8::test_a_withheld_items_metadata_never_reaches_an_ad_generation_target`'s contract-off arm; `test_ad2_serving::test_generation_prompt_has_no_band_language_under_successor`'s switch-off case.
- The `plan_uses_path_off` cases of `test_rw7b_codex_review_fixes::test_f1_switching_off_…` and `test_rw7b_fix_round2::test_an_auto_completed_plan_…`; the `plan_uses_path` and `rw7b` cases of `test_curriculum_c1_fix_round5::test_m2_…`; `test_plan_follows_path::test_g47_off_every_plan_build_is_the_predecessors`'s switch-off case and `test_curriculum_c1_plan_follows_path::test_gc4_off_every_plan_build_is_rw7bs`'s (each now a one-case test, below); the switch-off case of the head fixture-copy loop.

**Every assertion changed, and why:**

| test | before | after | why |
|---|---|---|---|
| `test_router_probe_ties::test_a_greedy_probe_presentation_…` | vault at mvp-0.14, draws `(0.0, 0.0)` | vault at mvp-0.15 (the head's code), draws `(1.0, 0.0)` | its old tag only made the build greedy; a roll above the rate does at the head; the assertion stands |
| `test_router_probe_ties::test_teach_back_items_are_probe_near_ties` | parametrized, `admitted` | `probe_ties_admitted is True`, propensity > 0 | twin: the successor case |
| `test_router_probe_ties::test_the_draw_can_displace_a_probe`, `::test_a_probe_near_tie_carries_a_true_propensity` | the off/mvp-0.14 side asserted the exclusion | removed | twins: on sides kept |
| `test_intent_codex_rereview::test_f2_a_paused_items_cold_retry_waits`, `::test_f2_the_intent_control_is_on` | a below-the-tag side | removed | twins |
| `test_intent_codex_rereview::test_f2_new_vaults_start_…` | `intent_enabled(config)` | removed | the predicate is gone; the version assertion stays |
| `test_intent_plan::test_with_no_commitment_intent_changes_nothing_and_the_plan_build_is_one` (was `…_equals_intent_off`) | a vault with intent off as the oracle | `intent_serving(...) is None` for a vault with no commitment, and two such vaults build the same plan | intent off was the oracle; with no commitment intent reads nothing by construction (the serving module's own guarantee), which is what the oracle stood for |
| `test_intent_recall_targets::test_identity_at_090_…_with_no_commitment` (was `…_with_intent_off`) | commitments on both vaults, intent off on one | commitments only on `on`; `off` has none | the oracle is the no-commitment serve, the predecessor's path that stays; every uncommitted item's priority and components must match |
| `test_intent_recall_targets::test_a_master_target_brings_a_review_forward_and_a_pause_excludes` (was `test_the_kill_switches`) | then the recall targets off, then intent off | the on half | twin |
| `test_reader_followups_successor::test_planning_and_revaluation_run` (was `…_gated_by_the_switch`) | parametrized on/off | the on case | twin |
| `test_reader_followups_successor::test_mvp039_…` | `FollowupsConfig().enabled`, its registry rule | removed (the chain stays) | field and rule gone |
| `test_vault_report::test_the_report_names_…` | sample switch `followups.enabled` | `curriculum.enabled` (`mvp-0.40`) | the report lists table switches; the sample had to be one that stays |
| `test_successor_switches::test_a_tests_own_switch_is_never_overwritten` | the duplicate-table case used `[intent]` | `[teacher]` | the helper no longer writes `[intent]` |
| `test_cli_generate_practice::test_populate_goal_dry_run_…`, `test_contract_commissioning::test_legacy_learning_object_keeps_the_mastery_band_rung` | `adaptive_difficulty.generation_contract = false` | `adaptive_difficulty.enabled = false` | same assertions, other route: the incumbent's target path, which AD's master switch (kept) reaches |
| RW7b's switched-off tests (`test_rw7b_codex_review_fixes` F1 ×4, `test_rw7b_fix_round2` ×4) and C1's (`test_curriculum_c1_*`: every `RW7B_OFF` and `C1_OFF`) | `plan_uses_path = false` | `reading_paths.enabled = false` / `curriculum.enabled = false` | same assertions, other route: the transition, reopening, withdrawal and refresh code is the feature switches' off branch too, and stays |
| `test_curriculum_c1_plan_follows_path` (2 tests) | `move["switch"]` named `plan_uses_path` | `{"enabled": False, "curriculum": {"enabled": False}}`, `{"enabled": False}` | the receipts stop writing the removed key, and the route is now the feature switch |
| `test_curriculum_c1_codex_review_fixes::test_f2_c1_back_on_…` | rewrote `plan_uses_path = false` to true | rewrites `[curriculum] enabled = false` to true | other route |
| `test_plan_follows_path::test_g47_with_the_guide_off_no_plan_build_follows_a_path` (was `…_off_every_plan_build_is_the_predecessors`) | equal to the predecessor's tag with the switch off | no `reading_path` in the plan state, and the on vault's differs | the predecessor's tag reached it only through the switch; the Guide off is the predecessor's code now and the test asserts what it gives |
| `test_curriculum_c1_plan_follows_path::test_gc4_with_the_curriculum_off_every_plan_build_is_rw7bs` | equal to the predecessor's tag with C1 off | a v1 receipt, never v2, and the on vault's differs | as above |
| `test_plan_follows_path::test_g47_a_rebuild_shows_zero_projection_deltas_…` | rebuilt with the switch on, then off | rebuilt twice | twin: the on side (no projection delta, no path read) |
| `test_plan_follows_path::_fixture_parity` (owner lane) | the predecessor's tag with the switch off as baseline | the Guide off as baseline; on equals it | as above |
| `test_plan_follows_path::test_the_plan_follows_a_path_only_with_the_guide_and_the_plan_on`, `test_curriculum_c1_plan_follows_path::test_the_plan_follows_the_deliverable_only_with_…` | the field's default, its registry rule, the switch's case | the feature switches' and the plan's cases | field and rule gone |
| `test_reading_paths::test_on_by_default_…` | the section's keys included `plan_uses_path` | not | field gone |
| `test_ad23_fix_r8`, `test_ad2_serving` | a contract-off arm | removed (the `mvp-0.29` case stays: AD's master switch off through the helper) | twins |

Edits made by a script rather than the Edit tool: most source and test edits were exact-pattern replacements in Python one-offs that assert each pattern occurs exactly once (or a block cut between two unique markers), kept in the step's scratch directory; the `C1_OFF`/`RW7B_OFF`/`OFF` renames in the curriculum and RW7b test files were a regex replace over those files; `ruff check --fix --select F401` removed the imports deleted tests left unused.

## 7. Gates run

All under the empty-home wrapper in 5 GB scopes.
- Each commit: the tests naming its switch, predicate or module (and, for the two helper switches, every file the discovery run recorded the key for), with the identity, retired-config, architecture, layout, effective-defaults, CLI-snapshot, kill-switch, structure, successor-switch and vault-report tests: `generation_contract` 89 files (1,854 passed); probe ties 87 (1,966 passed); intent 186, in two chunks behind the lock (3,967 passed); follow-ups 85 (1,939 passed) plus vitest; reading paths 71 (1,612 passed after one port, `test_reading_paths`); curriculum 71 + 118 (3,371 passed); the registry fix 49 (890 passed).
- **Memory:** the `generation_contract` set (all `test_ad*` files) was killed at `-n 4` and `-n 6` by the 5 GB cap (`oom-kill` on the scope, so pytest printed no summary and exited 143); it ran green at `-n 2`. The sweep's chunks did not hit it.
- Desktop: `tsc --noEmit` clean; vitest over `src/screens/reader` (123 files, 1,482 tests). `node_modules` came from `npm ci --offline --ignore-scripts` inside the wrapper with `npm_config_cache` pointed at the user's npm cache (no real `HOME`).
- **The sweep:** `scripts/affected_tests.py --base 250b0e16fe` selects 1,336 test files (with the standard files); all ran in 14 chunks of 100 at `-n 4 -m "not arc_close"` behind `flock /tmp/learnloop-fullsuite.lock`, on `eaf0faa2dc`: **28,800 passed, 98 skipped, 12 xfailed, no failure or error**, first time through. The grade-application, due-queue and figure goldens and the pinned-draw router files ran in it unchanged.
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken. `scripts/check_gate_partition.py`: 30,978 collected, landing 30,913 + arc_close 65.
- Vault: references regenerated once (`99da63620e`; the two hand-written leaf counts 1,171 to 1,164; no section went); a second `generate_all.py` changed nothing. Validators: `db_validate_reference`, `desktop_validate`, `module_validate`, `validate_vault` all pass.
- Not run (the orchestrator's): the durability lane, `--fresh-connections`, the arc-close lane, the full vitest suite, `cargo check`, `npm run frontend:build`.

## 8. The census and the measures

**The census** (batch 1's scratch plugin around `version_floor.may_open_below_floor`), over the 31 test files this part edited, base code and tests (a `git archive` of `250b0e16fe`) against this branch: **124 test cases opened a vault below the floor at the base, 104 now (-20)**, in 17 files then and 16 now. The 6 cases the branch has and the base lacks are the same tests renamed or unparametrized (§6) at their old tags. The 104 left (`test_reader_followups` 35, `test_reader_digest_narrative` 25, `test_intent_codex_review` 11, `test_reader_rw6b_landing` 5, `test_plan_follows_path` 4, nine others 24) are tests whose vaults sit at an old tag for their own setup (the reader follow-up fixtures' tag, the intent fixtures'): they wait on the re-tagging step, not on a switch this part removed. (The base run had unrelated failures because the extract carries no `apps/` or `scripts/`: `test_mobile_allowlist`, two `test_reading_paths` tests, `test_vault_report`.)

**Measures** (`scripts/refactor_measures.py`, base `250b0e16fe` from a `git archive` committed to a scratch repository, against this branch):

| measure | base | this part |
|---|---|---|
| ADR-019's kept-because list | 82 | 75 |
| tagged switches in `TAGGED_SWITCHES` | 84 | 77 |
| `mvp-0.N` literals: code / docstring / comment | 268 / 311 / 577 | 259 / 305 / 576 |
| `config/schema.py` lines | 4,970 | 4,945 |
| raw lines; code lines (all four packages) | 614,406; 432,046 | 614,162; 431,898 |
| functions over 100 lines; over 200 | 474; 73 | 474; 73 |
| `enabled` booleans in `config/schema.py`; effective config leaves | 118; 1,179 | 115; 1,172 (the vault's catalog: 1,171 to 1,164) |
| comments naming a stage artifact | 2,374 | 2,371 |
| `src/` lines (diff) | | +169, -413 |
| test lines (diff, goldens aside) | | +223, -549 |

## 9. Bug ledger

- **D7-1:** none of the seven is read by replay (the real rebuilds are equal row by row). `data_capture.serving`, batch 3's replay-read switch, is in its second part.
- **D7-2:** unchanged: `router.lesson_suggestions.*` are in the second part.
- **D7-3:** four more reads of a missing field as off went with their switches: `probe_ties_admitted`, `intent_enabled`, and the `plan_uses_path` conjuncts of `reading_path_plan_active`, `deliverable_plan_active` and `plan_refresh_reason`.
- **D7-5:** nothing of it belonged to these seven.
- **D7-9:** unchanged.

No new bug was found.

## 10. What remains of the batch, and judgment calls

**Not removed here** (the brief's groups 2 and 3): `router.lesson_suggestions.enabled` and `.in_objective` (D7-2: `RouterLessonSuggestionsConfig` forbids extra keys, so its section must keep retired keys, with a loading test), `teacher.probes`, `data_capture.serving` (the `router_outcomes` replayer reads it), then `plan.enabled`, `router.enabled`, `router.restraint`. The discovery run (§1) already recorded which tests the helper writes their keys for, so each later group's predecessor run can be limited to those files.

**Judgment calls:**
1. **Two pairs reach their predecessor through a kept feature switch.** The `plan_uses_path` switches' off code is also the Guide's and the curriculum's off branch, so their tests move to those switches with every assertion (as batch 1 moved the no-rules tests to `diagnosis.grading_support = false`); `generation_contract`'s two incumbent-path tests move to AD's master switch, although their comments had said they would go with the switch.
2. **`get_intent` keeps `"enabled": true`** (the desktop reads it) instead of the desktop losing its branch; the plan report's and "Coming up"'s echoes stop (no reader), the latter with the desktop's unread DTO field.
3. **The offer trace keeps `probe_ties_admitted: True`** for the due-queue goldens; the router config dump in the trace and `snapshot_hash` lose the key, as with every router field change.
4. **The intent registry rationale keeps its stale words** (`895213968a`), because the parameter registry mirrors rationales into vault rows and P-shadow requires every row equal; rewording it is a later, deliberate change.
5. **The intent oracles** (`intent off`) became the no-commitment serve, which the serving module guarantees is the predecessor's path by construction; the two parity tests against an older tag became one-case tests of what the feature switch off gives.
6. **The helper-written cases that pass without their predecessor (335 for probe ties, 894 for intent, overlapping) were left at their tags**: their old tag is either their own setup or still holds a listed successor; the census counts what remains.
7. **`successor.settings`** (test-only, D7-5) was left; it simply lost the removed key from `SWITCHES`.

## 11. Docs

- ADR-019: the kept-because list went to 75 with this part, and what a removed switch's tests do when its off branch is a kept feature switch's.
- `Concepts/Attempt Processing` and `Concepts/Learning System` name none of the seven and are unchanged; the generated Config notes regenerated.
- Ledger rows D7-1, D7-3 and D7-5 updated.

---

# Part 2: `router.lesson_suggestions.enabled` and `.in_objective`, `teacher.probes`, `data_capture.serving`

The batch's second landing (the brief's group 2), built on part 1's tip `1101a99480`, which is this part's base: line numbers below are its. The rule, the precondition and the conventions are part 1's. Each row was checked at the base before its removal: all four are class A (the off code is a predecessor nothing needs, or shared with a switch that stays; no identity names them by value; `RETIRED_FIELDS` holds the whole-config digest). Group 3 (`plan.enabled`, `router.enabled`, `router.restraint`) is not started.

## 12. Which tests reached a predecessor through `tests/successor_switches.py`

Part 1's discovery run recorded which tests the helper writes each of the four keys for (§1's table: 223 files in their union). Before any source or test was touched, those 223 files ran (3 chunks at `-n 4 -m "not arc_close"` behind the lock) with part 1's scratch plugin deleting all four rows from `SWITCHES_BY_TAG`: **54 cases in 32 files failed**. The removals then went one switch (or the pair) per commit, and each commit's own run (source edited, tests not yet ported) failed exactly its share of them, which attributes each to one switch:

| switch (commit) | discovery cases it took the predecessor of | files |
|---|---:|---:|
| `teacher.probes` (`641206a0f0`) | 16 | 9 (`test_teacher_te2_lessons` 4, `test_reader_rw5d_p4b_teacher_visuals` 3, `test_teacher_te2log_episodes` 2, `_node_held` 2, `_report` 1, `test_teacher_te2_successor` 1, `_sidecar` 1, `test_followups_batch5_recap_protection` 1, `test_teacher_te1b_suggestions` 1: its config now always carries `te2`) |
| the lesson-suggestion pair (`3a2d552c18`) | 8 | 6 (`test_ro6_serving` 3, `test_ro6_codex_rereview` 1, `test_te3b_clock`, `_features`, `_population`, `_successor` 1 each) |
| `data_capture.serving` (`128128b911`) | 30 | 17 (`test_plan_determinism` 6, `_landing` 3, `test_data_capture_successor` 3, `_a2_measurement` 2, `_a1_prefilter`, `_a5_not_ready_floor`, `_a6_delayed_pick`, `_report` 1 each, `test_reading_paths` 2, `test_voi_v2` 2, `test_router_r2b_serving` 2, `test_router_r2a_landing`, `_r2a_serving`, `_r2c_retrieval`, `_g4_restraint` 1 each, `test_teacher_exam_question_guard` 1, `test_curriculum_c1_codex_review_fixes` 1) |

Each commit's run also failed the tests that name the switch or its predicate directly (the field and predicate tests, the off-only tests, `test_teacher_te2_review_fixes::test_f6_…`, which set `teacher.probes` itself). Every failing case is in §17, with what became of it. The other cases the helper wrote these keys for (about 1,450 by the discovery's count, overlapping) pass without their predecessor: their old tag is their own setup or still holds a listed successor, so they were left at it. Then the four rows left the helper with their switches (and the helper's imports of `TEACHER_PROBES_`, `LESSON_SUGGESTIONS_`, `LESSON_OFFERS_` and `DATA_CAPTURE_ALGORITHM_VERSION`). Its own test needed no change.

## 13. Step 0, per switch

None of the four is named by `projection_switches`, `objective_settings`, `followup_switch_snapshot`, `followup_generator_switches`, `draw_inputs` or `router_settings` (`lesson_offers_on` reaches `objective_settings["lessons_compete_with_followups"]` through `lessons_compete_with_followups_on`, and at the defaults that value is `True` before and after: the pins are unmoved, §15).

### `teacher.probes` (mvp-0.51)

- **Reads:** one predicate, `teacher.te2.on` (`te2.py:52`: lessons on and the field, getattr default **False**, ledger D7-3's kind), with ten callers: `service._te2_now` (`:400`), `_te2_turn` (`:406`), `open_lesson` (`:681`), `take_turn`'s close (`:932`), `_view_te2` (`:2535`, `:2553`), `open_lessons` (`:2571`), the sidecar's `_teacher_dto` (`context.py:1047`) and `lesson.goal` (`handlers/lesson.py:300`), and the follow-up job's `lesson_probe.enabled` (`followup_run/lesson_probe.py:55`).
- **Off code:** with lessons on and the switch off: `open_lesson`'s typed-goal refusal (`teacher_unavailable`, `:684`) and the sidecar's (`:301`); `build_brief`'s `te2=False` path, the v1 brief (`brief.py:880-888`), and `_probe_headers` (`:420-436`, only caller `:888`). `build_brief`'s only caller is `open_lesson`, after `require_active`, so the `te2` parameter goes and every new brief is `lesson_brief_v2`. What stays: `te2.on` is lessons on (the conjunct goes, as `generation_contract`'s did), and every path that `teacher.enabled = false` (class C, kept) reaches; the continuation of a lesson opened before TE2 (`lesson_te2(state)` reads the stored brief's version), and the readers of a stored v1 brief's probe items (`brief.py:131`, `:475`).
- **Stored and echoed:** the sidecar's `teacher.te2` keeps being sent, now `True` whenever `teacher` is (the desktop's `lessonGoals` reads it: `apps/learnloop-tauri/src/app/algoConfig.ts`, comment only); the brief's `version` is `lesson_brief_v2` for every new lesson, as for every owner vault with the switch on.
- **What the learner sees today with it on, and after:** desktop: "What do you want to learn?", "Continue your lesson", lesson probes and gaps: unchanged (same config payload, same code paths). Phone: no lesson RPCs (desktop-only). Not read by replay: a lesson probe's attempt is an existing attempt type.

### `router.lesson_suggestions.enabled` (mvp-0.43) and `.in_objective` (mvp-0.53), one pair

- **Reads:** `enabled` in `lesson_suggestion.suggestions_enabled` (`:110`; five callers: `today_suggestion` `:522`, `respond` `:636`, `suggestions_active` `:131`, `router_card` `:372`, the sidecar's `_teacher_dto` `:1046`) and in `router_objective_switches.lesson_offers_on` (`:298`); `in_objective` only in `lesson_offers_on` (`:298`, getattr default **False**), whose callers are `lesson_offer.offers_on`, `objective_inputs._lessons_on`, `policy`'s lesson-offer builder, `scores`' clock, `tail_data.features_version`, `lesson_suggestion._model`'s `with_offers` and `lessons_compete_with_followups_on`. `in_objective` is meaningful only beside `enabled` (both gate lesson offers), so they go together.
- **Off code:** none of their own: every off path is also reached by the router off, its decision log off or lessons off (`suggestions_enabled`'s other conjuncts), or by the objective off (`lesson_offers_on`'s `objective_on`), which stay. So only the conjuncts go.
- **The section refuses unknown keys** (ledger D7-2). `RouterLessonSuggestionsConfig` is `extra="forbid"`; it now subclasses `KeepsRetiredFields`, and `KeepsRetiredFields`' wrap validator gives the handler the input without the model's retired keys wherever the model forbids extras (`retired._without_retired_keys`): a vault setting either key loads, only an identity dump shows the value, and a misspelt key is still refused. Every other retired-aware model ignores or keeps the key itself, and its plain dump is unchanged, so the step is skipped there.
- **Stored:** none of the two is written anywhere by value; the trace's `config_snapshot["router"]` dumps the live `RouterConfig` (its nested section loses the two keys), inside a `snapshot_hash` nothing recomputes, as in part 1.
- **What the learner sees, and after:** desktop: the Today suggestion card, lesson offers in the plan, "Learn it with the tutor": unchanged (`teacher.suggestions` is sent on the same conditions with the defaults). Phone: none of these RPCs. Not read by replay.

### `data_capture.serving` (mvp-0.44)

- **Reads:** `data_capture.gates.serving_on` (`gates.py:22`, getattr default **False**) at sixteen sites: the plan's measurement slots (`engine.py:1730`), a decision's frozen objective (`:3781`), the follow-up's objective (`:5019`, and `followup_run/router.py:349`), `measurement.settle` (`:446`), the mixture's `not_ready` branch (`router_chooser.py:424`), its objective freeze (`:487`), the restraint's `not_ready` branch (`:718`), the reading-exposure sweep (`reading_exposures.py:290`), VOI's full candidate receipts (`voi_stopping.py:1145`, `:1197`), the teacher's delayed-check picker (`teacher/delayed.py:139`, `:185`), the AD report's delayed definition (`adaptive_difficulty/report.py:656`), the capture report's echo (`ops/capture_report.py:538`), and `router/outcomes.outcome_version_for` (`:238`), whose callers are the rebuild's `router_outcomes` replayer (`substrate/rebuild_orchestrator.py:556`), the router's similar-decision retrieval (`router_retrieval.py:158`), the capture report (`capture_report.py:140`) and `why/outcomes_now.py:26`.
- **Off code:** the predecessor's deterministic `not_ready` returns in the mixture and the restraint (`router_chooser.py:424-426`, `:718-721`), `_frozen_objective`'s and `settle`'s early returns, the band-middle-by-LO pick in `teacher.delayed.pick` and `picked_for`'s off arm (`delayed.py:139-149`, `:185-186`), the sweep's early return, and `outcome_version_for`'s v2 answer. Deleted. Kept: `pick` (another caller, `teacher/checks.py:125`) now always reads the item's own prediction; version 2's derivation stays as `derive_router_outcomes`' default argument (tests call it so; no vault derives under it); VOI's `MAX_RECORDED_CANDIDATES` and the `record_all` / `record_all_candidates` defaults stay (every production site passes `True`); the AD report's `delayed_definition` parameter stays (passed `True`). `outcome_version_for(config)` keeps its signature and answers `router_outcomes_v3`: the replayer calls it, and `substrate/rebuild_orchestrator.py` belongs to the parallel arc-D close fix, so it is untouched.
- **What a rebuild computes with it on** (what every owner vault has): the `router_outcomes` replayer derives every decision's outcomes as `router_outcomes_v3` (R_cold under the shared delayed-completion definition, with the Reader's exposures), which is exactly what it derives now. §16's real rebuilds are equal row by row on all three copies (the one copy with router outcomes holds three `router_outcomes_v3` rows on each side).
- **Stored and echoed:** `router_outcomes.outcome_version` is `router_outcomes_v3` as before. The capture report stops writing `switches.serving` and its "serving changes on" words (nothing compares them; no pin or golden holds them). The VOI receipt cap's registry rationale names the switch and keeps its bytes, with a comment saying why (it is mirrored into vault rows, part 1 §2's lesson).
- **What the learner sees, and after:** desktop and phone: the plan's "Check once" measurements and the mixture's no-model draws are as with it on; the phone's measurement holding is unchanged (`test_data_capture_phone`). The sidecar's queue comment no longer names it.

## 14. What went

| commit | what |
|---|---|
| `641206a0f0` | `teacher.probes` |
| `3a2d552c18` | `router.lesson_suggestions.enabled` and `.in_objective` (with D7-2's loading fix and test) |
| `128128b911` | `data_capture.serving` |
| `00bc34052a` | the vault's references regenerated (1,164 to 1,160 effective leaves) |

In each removal commit: the field into `RETIRED_FIELDS` (`removed_by` `D7`; `RouterLessonSuggestionsConfig` and `DataCaptureConfig` now keep retired fields, `TeacherConfig` already did; no section was left empty), `_pre_arc_c_shape`, the kill-switch table row and its kept-because line, the registry rules (`teacher.probes`' share of TE2's rule, both lesson-suggestion rules), the vault generator's descriptions (`router.lesson_suggestions.enabled`, the `data_capture` section), the tags' comments in `algorithm_versions.py`, the helper's row, and the effective-defaults golden (exactly the removed lines).

**Deletion proof** (strategy §2.1): `serving_on`, `_probe_headers`, the `te2=` keyword of `build_brief`, `teacher_unavailable` with the typed-goal message, `lesson_suggestions.enabled`, `in_objective` and `data_capture.serving` searched over `src/`, `scripts/`, `tests/`, `apps/` and the vault's `_scripts/` as names and strings: no function-local or `importlib` import, no registry, Typer or `MODULE_INVENTORY` entry left (`teacher_unavailable` stays: the teacher's model being unavailable raises it, `service.py:1257`).

## 15. Identities and stored snapshots

- **The retired-config identities.** Part 1's `TODAY_SWITCHES_TOML` already sets all four away from their defaults and its digests were recorded at `250b0e16fe`, so `test_a_config_setting_todays_removed_switches_keeps_every_identity` needed no new line; `_pre_arc_c_shape` gained the four fields. **With each new entry removed** from `RETIRED_FIELDS` (mutations, not committed): `TeacherConfig.probes` and `DataCaptureConfig.serving` fail six tests each (`test_the_config_identity_reproduces_both_recorded_digests`, `test_an_embedding_compare_report_is_named_as_before_arc_c`, both cases of the batch-1 and of this batch's identity test); each lesson-suggestion entry fails eight (those six, the loading test and the new section test, because the forbidding section then refuses the key). Restored: 19 passed.
- **D7-2, fail first.** A new test, `test_the_lesson_suggestions_section_still_refuses_an_unknown_key_but_loads_its_retired_ones`, validates the section with both retired keys (plain dump without them, identity dump with them), refuses a misspelt key, and loads a `learnloop.toml` that sets both. With `KeepsRetiredFields` handing the forbidding model its raw input (`model = handler(data)`, a mutation): that test, `test_a_vault_that_still_sets_a_removed_switch_loads_and_the_switch_reads_nothing` and the `switched` case of this batch's identity test fail (a vault setting either key no longer loads). Restored: green.
- **`tests/test_identity_pins.py`:** unmoved at every commit; nothing written. C3-C6 do not move (`lessons_compete_with_followups` is `True` at the defaults before and after).
- **Snapshots, per switch:** `teacher.probes`: the sidecar's `teacher.te2` keeps `True` (desktop reader); briefs are `lesson_brief_v2`. The lesson-suggestion pair: none stored. `data_capture.serving`: `outcome_version` keeps `router_outcomes_v3`; the capture report's `switches.serving` echo stops.

## 16. Proof

**P-shadow** (`learnanything-ad1/fixtures-local/owner-copies-mvp058`, fresh `copy_tree_with_databases` copies; base `1101a99480` from a `git archive` of `src/` and `migrations/` on `PYTHONPATH`, branch at `128128b911`; counts only; copies deleted):

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| `learnloop upgrade`, both | `mvp-0.58 -> mvp-0.59` | same | same |
| shadow facet / mastery / schedule changed | 0 / 0 / 0 (80 / 21 / 99 unchanged) | 0 / 0 / 0 (3 / 18 / 77) | 0 / 0 / 0 (7 / 34 / 32) |
| `schedule_effects` due dates moved (items, cards) | 0, 0 | 0, 0 | 0, 0 |
| the two shadow reports, marker id, `as_of` and hashes aside | equal | equal | equal |
| every table of the two upgraded copies, row by row | 402 tables, 19,442 rows: none differ | 402, 10,426: none | 402, 23,877: none |
| the same after the shadow | none differ | none | none |
| the same after a real `rebuild-derived-state` on each side | 19,749 rows: none differ | 10,498 (3 `router_outcomes_v3` rows each side): none | 23,719: none |
| Today on a copy of the rebuilt vault at 2026-11-15 12:00Z: `read_due_queue`, the intent report, a built plan | byte-equal | byte-equal | byte-equal |

This is `data_capture.serving`'s rebuild proof (the `router_outcomes` replayer read it): unchanged. No registry row moved this time (the rewritten rules are config rules of paths no copy sets; the one mirrored rationale kept its bytes).

**Old rows at the floor and the head** (`fixtures/mvp017_route_check_replay`, retagged to `mvp-0.58` and `mvp-0.59`, two live rebuilds per code, branch at `128128b911`): every table equal row by row after each rebuild at both tags except the one `attempt_debug_payloads` row of `att_02_svd_fail`, equal with replay's minted ids, stamps and digests normalized, as in part 1.

**P-draw.** The router's pinned draws and the due-queue goldens ran unchanged at the default switches: `tests/test_due_queue_golden.py` in each commit's gate and in the sweep, the pinned-draw router files in the sweep (§18). No golden or pin was regenerated. The tests that had reached the old deterministic `not_ready` pick now name the staged rule, which is what that pick was (§17); none of them is a pinned-draw subject.

**Goldens.** The effective-defaults golden lost exactly four lines (`data_capture.serving`, `router.lesson_suggestions.enabled`, `router.lesson_suggestions.in_objective`, `teacher.probes`) and gained none. The CLI snapshot did not change. The grade-application, due-queue and figure goldens ran unchanged in the sweep. The structure golden is unchanged (no number moved: `--write` wrote the same file).

**The owner lane** (`-m owner_vaults`, 31 files, copies made with the gate's `owner_copy_make.py` under `fixtures-local/owner-lane-d7e`, deleted after): 92 passed, 8 skipped, as at part 1. No owner-lane test was edited (two edited files, `test_router_r2a_serving` and `test_router_r2b_serving`, hold owner-lane tests elsewhere in the file; they ran).

## 17. Tests

**Deleted** (each with its subject):
- `teacher.probes`: `test_teacher_te2_lessons::test_switch_off_or_below_the_tag_gives_te1s_lesson_byte_for_byte` (2 cases: off equals TE1), `::test_typed_goals_need_the_switch` (the refusal); `test_followup_single_use::test_the_teachers_probe_headers_leave_it_out` (called the deleted `_probe_headers`; no brief lists a vault item now).
- The pair: `test_te3b_successor::test_the_switch_defaults_on_and_is_classified` (the field and its rule); `test_teacher_te1b_suggestions::test_off_nothing_is_drawn_or_written`'s `switch_off` case.
- `data_capture.serving`: `test_data_capture_a1_prefilter::test_the_voi_flag_follows_the_successors_switch` (the predicate); `test_data_capture_a2_measurement::test_settle_is_a_no_op_with_the_switch_off` (off), `::test_below_the_tag_or_switched_off_nothing_is_frozen_or_arranged` (2 cases: off equals mvp-0.43); `test_data_capture_a5_not_ready_floor::test_below_the_tag_or_switched_off_it_is_the_predecessors`; `test_data_capture_a6_delayed_pick::test_below_the_tag_or_switched_off_the_smallest_id_wins_as_before` (2 cases); `test_data_capture_codex_rereview::test_f1_no_receipt_with_both_switches_off` (off); `test_data_capture_successor::test_switched_off_at_the_tag_the_plan_and_its_rows_are_the_predecessors` (2 cases); `test_plan_determinism_landing::test_staged_plans_at_mvp024_…`'s three `mixture_not_ready` cases (mvp-0.24's deterministic no-model mixture: the mixture now draws there); `test_router_g4_restraint::test_with_no_model_set_up_a_placeable_follow_up_joins_deterministically` (the predecessor's deterministic restraint; A5's floor on the restraint is `test_data_capture_a5_not_ready_floor::test_the_restraint_keeps_the_floor_on_not_ready_too`).

**Every assertion changed, and why:**

| test | before | after | why |
|---|---|---|---|
| `test_teacher_te2_successor` (3 tests) | the field's default, its rule, the gate below the tag and switched off | the keep bound and its rule; the gate on with lessons on, off with lessons off | field and rule gone; twin |
| `test_teacher_te2_lessons::test_today_lists_open_lessons_…` | below the tag: no card, close refused | removed | twin: on side kept |
| `test_teacher_te2_sidecar::test_the_config_carries_the_te2_key_with_lessons` (was `test_below_the_tag_the_goal_rpc_refuses_…`) | refusal and no key below the tag | the key with lessons | twin |
| `test_teacher_te2_review_fixes::test_f6_today_can_close_a_te1_lesson_left_open_before_te2` | a TE1 lesson made with the switch off | a lesson whose stored brief is given the v1 shape (`as_opened_before_te2`, `tests/teacher_te2_probes_helpers.py`) | no lesson opens as TE1 now; one opened before still continues, and that is the subject |
| `test_followups_batch5_recap_protection::test_an_item_the_earlier_lesson_was_shown_…` | the first teacher tag's lesson listed `pi_det_1` in its brief | the earlier lesson's stored brief lists it (`as_opened_before_te2`) | as above: the recap check reads a stored v1 brief's items, which stays |
| `test_reader_rw5d_p4b_teacher_visuals` (3 tests), `test_teacher_te2log_episodes` (2), `_node_held` (2), `_report` (1) | pinned the first teacher tag for TE1's prompt, schema and family | at the head: the same prompt, schema and family with TE2's paragraph beside (`T2.turn_model`, `T2.instructions`, `T2.prompt_version`, `+teacher_te2_v1`) | the subject is visuals or episodes; every lesson opens under TE2 |
| `test_teacher_te1b_suggestions::test_without_the_decision_log_the_desktop_config_has_no_suggestions` (was `…_with_the_switch_off_…`) | `router.lesson_suggestions.enabled = false` | `router.log_decisions = false`; both sides carry `te2` | same assertions, other route; `te2` is always sent with lessons |
| `test_teacher_te1b_review_fixes::test_the_learners_answers_…` | suggestions off by the field | by the decision log | other route |
| `test_te3b_successor::test_the_gate_reads_on_and_off_with_the_objective_or_lessons_off` | below the tag and the two fields off | the objective off and lessons off | twin, kept routes |
| `test_te3b_clock::test_the_gate_reads_lessons_on_the_clock_with_lessons_on`, `test_te3b_features::test_ro6s_features_…` | `in_objective = false` / the older tag | `teacher.enabled = false` | other route (no offers without lessons) |
| `test_te3b_population::test_with_lessons_off_the_same_database_is_valued_without_lessons` (was `test_switch_off_or_below_the_tag_values_the_same_database_as_mvp052`) | off and the older tag equal each other; on moves | lessons off against on: minutes, population, features version, offer builder move; lessons off draws no card | off-equals-predecessor went; the twin's on assertions kept against the kept route (two added for the on side: the offer builder is present, the off side has no card) |
| `test_te3b_population::test_the_population_holds_…` | the older tag's population lacks the LO | removed | twin |
| `test_te3b_codex_review` F2 | `in_objective = false` mid-run | lessons off mid-run | other route: the offer is withdrawn and the objective's next boundary decides without offers |
| `test_te3b_codex_review` F3 (3 tests) | `in_objective = false` | `router_objective.enabled = false` | other route: the daily card where the objective does not serve; F3's subject |
| `test_ro6_serving` (3), `test_ro6_codex_rereview::test_f3_…` | `LT.NAMES` (14 features) at RO6's own tag | `LT.NAMES_LESSON` (15), and `rebuilt_features` at the vault's served features version | their tag is their setup; lesson offers serve there now, so the features carry the lesson indicator |
| `test_data_capture_successor` (2) | `serving` default and gate; v2 below the tag | `receipts`' default and gate; v3 at any tag | the switch went; rebuild proof at the unit level |
| `test_data_capture_a2_measurement::test_a_decision_before_its_objective_could_be_frozen_…` | a run at mvp-0.43 left decisions with no objective | a stored pre-0.44 stop decision inserted as a row | no decision is written without an objective now; old vaults hold such rows, and the subject is reading them |
| `test_data_capture_report` (2) | `switches == {receipts, serving}`; v2 below the tag | `switches == {receipts}`; v3 at an older tag, receipts counted | the echo stopped; the outcomes are v3 for every vault |
| `test_data_capture_phone` | set `serving = True` | removed | the field is gone |
| `test_plan_determinism` (templates) | the router-on templates reached the deterministic `not_ready` pick | `router.mode = "staged"` | same assertions, the staged rule's route (what that pick was) |
| `test_router_r2a_landing::_real_queue_world`, `test_curriculum_c1_codex_review_fixes::test_f1_after_a_refresh_…` | the same | `router.mode = "staged"` | same; in the C1 test the floor's pinned draw would otherwise stop the plan before its reading |
| `test_router_r2b_serving::test_staged_mode_…` | R2a's twin at its tag with no models | R2a's twin with `mode = "staged"` | R2a's frame is the staged rule |
| `test_router_r2b_serving::test_with_no_model_set_up_the_plan_says_the_models_are_not_set_up` (was `…_the_rule_chooses_deterministically`) | deterministic and equal to R2a | the rows are the mixture's and the plan says the models are not set up | the deterministic half was the predecessor |
| `test_router_r2a_serving::test_router_outcomes_replay_twice_with_no_model_call` | `router_outcomes_v2` | `router_outcomes_v3` | every vault's outcomes are v3 |
| `test_router_r2c_retrieval::test_only_matured_…` | `similar_decisions(vault=…)` with no repository | `repository=env.repository` (as its one production caller passes) | v3 needs the Reader's exposures, which need the repository |
| `test_reading_paths` (2 tests) | the plan equal to a76c8358a's golden | equal to the same fixture built again with no path, depth or override (`_twin_plan`); the queue, guide and contract goldens unchanged | the golden's plan was decided by the predecessor's deterministic no-model rule; the twin shows the same subject (display only) |
| `test_voi_v2` (2, through `tests/voi_restore_scenarios.summarize_body`) | every logged candidate summary | the first `MAX_RECORDED_CANDIDATES` | the golden was pinned when a receipt kept six; every receipt keeps all now (receipt size, never a decision) |
| `test_teacher_exam_question_guard::test_a_lesson_with_no_reserved_text_is_byte_identical_…` | two lessons with random ids | the same ids in both (`S.new_ulid` patched per lesson) | the lesson id seeds the delayed checks' tie draw (A6): both lessons must draw the same item, whatever the guard does |
| `test_successor_switches`, `test_kill_switches`, `test_retired_config_identities` | the four keys | removed; `_pre_arc_c_shape` gains them | fields gone |

Edits made by a script rather than the Edit tool: as in part 1, exact-pattern replacements in Python one-offs that assert each pattern occurs once (or cut a test between two unique markers), kept in the step's scratch directory; `ruff check --fix --select F401` removed two imports the deleted tests left unused.

## 18. Gates run

All under the empty-home wrapper in 5 GB scopes.
- Each commit: the tests naming its switch, predicate or module, the discovery's failing files and the standard files (identity, retired-config, architecture, layout, effective-defaults, CLI-snapshot, kill-switch, structure, successor-switch, vault-report): `teacher.probes` 86 + 11 files (1,556 + 386 passed); the pair 89 files (1,959 passed); `data_capture.serving` 194 files in two chunks behind the lock (4,397 passed, after the ports; the last port, `test_router_r2c_retrieval`, then green on its own).
- Desktop: `tsc --noEmit` clean after each touched commit; vitest over every test file that reads `algoConfig`, `lessonGoals` or `lessonSuggestions` (85 files, 787 tests); once, by a shell slip, the whole vitest suite (286 files, 2,874 tests), all passing. The only desktop edits are two doc comments in `algoConfig.ts`.
- **The sweep:** `scripts/affected_tests.py --base 1101a99480` with the standard and edited files selects 1,333 test files; all ran in 14 chunks of 100 at `-n 4 -m "not arc_close"` behind `flock /tmp/learnloop-fullsuite.lock`, on `00bc34052a`: **28,738 passed, 101 skipped, 12 xfailed, no failure or error**, first time through. The grade-application, due-queue and figure goldens and the pinned-draw router files ran in it unchanged.
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken. `scripts/check_gate_partition.py`: 30,958 collected, landing 30,893 + arc_close 65.
- Vault: references regenerated once (`00bc34052a`; the two hand-written leaf counts 1,164 to 1,160, in `Configuration.md` and `Database.md`); a second `generate_all.py` changed nothing. Validators: `db_validate_reference`, `desktop_validate`, `module_validate`, `validate_vault` all pass.
- Not run (the orchestrator's): the durability lane, `--fresh-connections`, the arc-close lane, the full vitest suite as a gate, `cargo check`, `npm run frontend:build`.

## 19. The census and the measures

**The census** (part 1's plugin), over the 39 test files this part edited, base code and tests (a `git archive` of `1101a99480`) against this branch: **220 test cases opened a vault below the floor at the base, 190 now (-30)**. The 11 cases the branch lists and the base does not are the same tests renamed or unparametrized at their old tags (§17). What is left (`test_data_capture_codex_rereview` 23, `test_router_r2b_serving` 20, `test_data_capture_a2_measurement` 19, `test_plan_determinism_landing` 16, `test_teacher_te1b_suggestions` 15, `test_plan_determinism` 12, `test_router_g4_restraint` 11, `test_router_r2a_serving` 10, sixteen others 64) are tests whose vaults sit at their own successor's tag (data capture's, the router frame's, TE1b's): they wait on the re-tagging step, and the router-frame ones also on group 3 (`router.enabled`, `router.restraint`) and batch 4 (`router.mode`). (The base run had two failures because the extract has no `apps/` or `scripts/`: `test_reading_paths`, as in part 1.)

**Measures** (`scripts/refactor_measures.py`; base: part 1's tip measurement at `895213968a`, whose source equals `1101a99480`'s; branch at `128128b911`):

| measure | base | this part |
|---|---|---|
| ADR-019's kept-because list | 75 | 71 |
| tagged switches in `TAGGED_SWITCHES` | 77 | 73 |
| `mvp-0.N` literals: code / docstring / comment | 259 / 305 / 576 | 253 / 304 / 572 |
| `config/schema.py` lines | 4,945 | 4,939 |
| raw lines; code lines (all four packages) | 614,162; 431,898 | 614,075; 431,823 |
| functions over 100 lines; over 200 | 474; 73 | 474; 73 |
| `enabled` booleans in `config/schema.py`; effective config leaves | 115; 1,172 | 114; 1,168 (the vault's catalog: 1,164 to 1,160) |
| comments naming a stage artifact | 2,371 | 2,371 |
| `src/` lines (diff) | | +169, -256 |
| test lines (diff, goldens aside) | | +275, -413 |

## 20. Bug ledger

- **D7-1:** `data_capture.serving`, batch 3's replay-read switch, is gone; the rebuild derives what it derived with it on (§16). The other three are not read by replay.
- **D7-2:** fixed in `3a2d552c18` (§13, §15).
- **D7-3:** three more reads of a missing field as off went with their switches: `serving_on`, `te2.on`'s `probes` conjunct and `lesson_offers_on`'s two conjuncts.
- **D7-5:** nothing of it belonged to these four.
- **D7-9:** unchanged.

No new bug was found.

## 21. What remains of the batch, and judgment calls

**Not removed here** (group 3): `plan.enabled`, `router.enabled`, `router.restraint`. Part 1's discovery run recorded no helper key for them (they were never in the helper); their tests name them directly.

**Judgment calls:**
1. **`KeepsRetiredFields` strips retired keys only where the model forbids extras** (D7-2). A general strip would have changed the plain dump of `LearnLoopConfig` (`extra="allow"`), which keeps an old table as an unread extra; the forbidding section is the only one that needs it, and a misspelt key there is still refused.
2. **`teacher.probes`: `build_brief` loses its `te2` parameter and `_probe_headers`**, since its only caller opens lessons only with lessons on. Two tests that need a lesson opened before TE2 give a lesson's stored brief that shape (`as_opened_before_te2` rewrites the open turn's payload, which has no update trigger) instead of opening one through the deleted path.
3. **The sidecar keeps sending `teacher.te2: true`** with `teacher.lessons` (the desktop reads it) rather than the desktop losing its branch, as part 1 kept `get_intent`'s `enabled`.
4. **The lesson-suggestion pair and `teacher.probes` remove conjuncts, not branches**: their off paths are reached by the router, its log, lessons and the objective, which stay. Tests that used the fields to reach those paths use those switches (`router_objective.enabled` for "where the objective does not serve", which batch 4 may revisit).
5. **`data_capture.serving`: `outcome_version_for` stays, answering v3**, because the rebuild orchestrator (another step's file) calls it; version 2's derivation, VOI's six-summary cap and the AD report's `delayed_definition` parameter stay as default arguments that no production caller uses. Removing them is a later, deliberate cleanup (their tests and the VOI cap's mirrored registry row would move).
6. **The old deterministic `not_ready` pick is reached through `router.mode = "staged"`** in the tests whose subject is a staged plan (plan determinism, R2a's frame, the C1 reading); the tests whose subject was that pick itself went. `router.mode` is batch 4's; those tests will need the staged rule another way then.
7. **`test_reading_paths`' a76c8358a plan golden became a twin comparison** (the golden's plan carried the removed path's labels: "the models aren't set up, so the plan's usual rule chose", `router_mixture_v1`); the queue, guide and contract goldens are unchanged.
8. **`test_voi_v2`'s restore golden compares the first six logged candidate summaries**, the receipt size it was pinned with, rather than being regenerated.
9. **`test_teacher_exam_question_guard` pins its lesson ids** so both lessons draw the same delayed-check tie (the draw is seeded by the lesson id); without the pin the two lessons would pick different items half the time.

## 22. Docs

- ADR-019: the kept-because list went to 71 with this part, the replay-read switch's rebuild, and the forbidding section's retired keys.
- `Concepts/Attempt Processing` and `Concepts/Learning System` name none of the four and are unchanged; the generated Config notes regenerated (`Config - data_capture`, `Config - router`, `Config - teacher`).
- Ledger rows D7-1, D7-2 (fixed), D7-3 and D7-5 updated.
