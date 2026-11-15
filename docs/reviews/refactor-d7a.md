# Refactor D7, batch 1, part 1: kill switches at or below the floor (grading, attempts)

Step D7 batch 1 of arc D (`docs/specs/refactor_strategy_v3.md` §2.6), on branch `refactor/d7a-switches-grading-replay`, based on main `b4c8fbad98` (D6 part 2 landed). The rule is ADR-019's (owner, Nov 12; L7): when every live vault is at or past a tag, its gates and kill switches go, except a short kept-because list. The precondition holds: on Nov 14 the owner ran `scripts/vault_report.py` on the three live vaults (all at `mvp-0.58`) and the five retired ones, and no vault sets any tagged switch. Structure track: for every vault the owner has, each switch removed here is at its default, so removing it with its off-branch changes nothing that vault computes.

**This landing is part of the batch.** It removes seven of the batch's fifteen switches, in five commits: `teacher.weight.learned` and `.source`, `practice.reschedule_cold_after_assist`, `practice.attempt_keeps_content_state`, `hints.fold_follows_attach`, `proof_check.enabled` and `required_method.enabled`. What remains of the batch, and why, is in §8.

Inventory: `docs/reviews/refactor-d7-inventory.md` §1.1, §1.4 (the teacher's weight rows), §2.1, §4 batch 1.

## 1. Step 0, per switch

Line numbers are the base's (`b4c8fbad98`). "Whole-config digest" is `content_key(identity_dump(config))` (`tests/test_retired_config_identities.py`), which every switch enters; `RETIRED_FIELDS` keeps it (§3). No switch removed here is named by `projection_switches`, a receipt's switch snapshot, `objective_settings`, `followup_switch_snapshot` or `draw_inputs`, and none is listed in `tests/successor_switches.py` (its `SWITCHES_BY_TAG` holds only D6 part 2's successors), so no test reached a predecessor through that helper for any of them.

### `teacher.weight.learned`, `teacher.weight.source` (mvp-0.41)

- **Reads:** `teacher/checks.py:146` (`vault.config.teacher.weight`), `:167` (`not learned` → the type's configured mass, rule `fixed`), `:169` (`source == "pool"` conjunct). Nothing else in `src/`, `apps/` or `scripts/` reads either; the parameter registry rule (`params/parameter_registry.py:1947`) and the vault generator's field descriptions (`db_generate_reference.py:1413`, `:1418`) name them.
- **Off code:** the `fixed` arm and the conjunct; `LW.RULE_FIXED` (`learner/lesson_weight.py:135`) was written only by that arm. `fixed_mass` stays in the receipt (computed for every check).
- **Replay:** reads each check's recorded `lesson_checks.mass_applied` (`lesson_weight.lesson_check_mass`), never the switches; the weight update (`lesson_weight.py:1018`) reads only `learned` and `pool` rows. A rebuild's result does not depend on them.
- **Tests:** off-only, two (§4).

### `practice.reschedule_cold_after_assist` (mvp-0.38)

- **Reads:** `diagnosis/remediation.py:1128` (`reschedule_cold_after_assist_active`, getattr default **False**, also needs `serve_eligibility.help_converts_active`); one caller, `_reschedule_assisted_cold_retry` (`:1209`).
- **Off code:** the predicate's switch conjunct only: off, the function returns before scheduling, and the predecessor's behaviour (the next serve withdraws the retry) is the serve path's, which also runs for every attempt the reschedule does not act on. It stays.
- **Replay:** none (replay passes no vault; `followup_tasks` is workflow state).
- **Tests:** one off-equals-predecessor test, two twins, one test that reached CA2-at-its-tag through it (§4).

### `practice.attempt_keeps_content_state` (mvp-0.37)

- **Reads:** `attempts/attempts.py:1388` (`attempt_keeps_content_state`, getattr default True); one caller (`:3306`) → `_persist_attempt_application(keep_content_state=)` → `Repository.record_attempt_outcome(keep_content_state=)` (`db/repositories.py:6020`), whose only caller that is.
- **Off code:** `record_attempt_outcome`'s full-upsert arm and the parameter's plumbing. `_upsert_practice_item_state_record` stays: replay's `replace_attempt_derived_outcome` (`:6264`) is its other caller.
- **Replay:** none (replay keeps the full upsert).
- **Tests:** two off-only (a gate test and an off-reopens test), two off-only controls (§4).

### `hints.fold_follows_attach` (mvp-0.42)

- **Reads:** `attempts/hint_fold.py:239` (`fold_follows_attach`, getattr default **False**, ledger D7-3); two callers, the sidecar's `submit_attempt` (`practice.py:1463`) and `submit_dont_know` (`:1659`), both as `_server_hint_fold(any_session=...)`.
- **Off code:** `any_session` is the switch carried down: `ServerHintFold.any_session`, `read_fold`, `refolded_draft`, `attach_keyed` (no keyed attach unless set), `help_assists.server_fold`, `_fold_rows`, `fold_row_count`, `attach_keyed_fold` (passed `True`). Its only producer is the predicate. `_fold_rows`' predecessor branch (a keyed fold in the submit's own session) is reached only with `any_session` false and a key; the workbench's `fold_row_count` call is keyless, where both definitions are the same clauses in another order. So the parameter goes everywhere with the branch.
- **Replay:** never folds (re-applies stored `hints_used` and `primed`).
- **Identity:** `learnloop hints report --json` echoes `config.hints` (no pin; one test assertion, §4).
- **Tests:** the switch's off arms, and F10's interrupted attach (§4).

### `proof_check.enabled` (mvp-0.17/0.20), `required_method.enabled` (mvp-0.25): one pair

- **Reads:** `attempts/grading_support.py:252` (`route_rules_active`, default True), `:263-265` (`method_rules_active`, needs the first), `:271-274` (`route_rules_version`); callers `attempts/attempts.py:2123` (`regrade_reads_contract`) and `:2171` (`_blind_grading_plan`). Both switches are read only through these; `required_method` needs `proof_check`, so they go together.
- **Off code:** `route_rules_version`'s `own-route-v1` and `None` arms and `regrade_reads_contract`'s guard. The rules-free grading path stays: `diagnosis.grading_support = false` (an untagged switch) reaches it (`attempts.py:2170`). `ROUTE_RULES_VERSION` (`own-route-v1`) and its text stay: stored blind records name it, and `reference_policy(route_rules=True)` maps to it.
- **Replay:** reads the recorded blind record (rules, outcome, calibration identity), never either switch.
- **Tests:** two predicate tests, two "the kill switch grades exactly as the predecessor" tests, an off-prompt test, an off arm; five tests that pinned `own-route-v1` through `required_method` off; two no-rules tests; one replay test that wrote its predecessor grade through the switch (§4).

## 2. What went

| commit | switch | what |
|---|---|---|
| `c074d9b6c6` | `teacher.weight.learned`, `.source` | every check enters at the learned mass, pooled where the teacher forecast the node; `[teacher.weight]` retired whole; `LW.RULE_FIXED` deleted |
| `1489b5019d` | `practice.reschedule_cold_after_assist` | the predicate is CA2's rule and the no-vault answer |
| `cc6ec6f74e` | `practice.attempt_keeps_content_state` | a live attempt always writes only the scheduling columns; the predicate and `keep_content_state` go |
| `8bf09c20ae` | `hints.fold_follows_attach` | the keyed fold always reads by the key alone and attaches in the attempt's transaction; `any_session` goes |
| `debed5c3e6` | `proof_check.enabled`, `required_method.enabled` | new blind grades always carry `own-route-v2`; `route_rules_active`, `method_rules_active`, `route_rules_version` go; `[proof_check]` and `[required_method]` retired whole |

In each commit: the field into `RETIRED_FIELDS` (removed by `D7`; `TeacherConfig`, `PracticeConfig` and `HintsConfig` now keep retired fields; a section left empty is removed and retired on its parent, as arc C's `[locks]`), the kill-switch table row (`config/kill_switches.py`) and its kept-because line (`tests/test_kill_switches.py`), the registry rule, the vault generator's field and section descriptions, the tag's comment in `algorithm_versions.py` (each now says its switch went once every vault was past the tag), and the effective-defaults golden regenerated for exactly the removed lines. No desktop or phone code reads any of these seven (searched `apps/`).

**Deletion proof** (strategy §2.1) for what went beyond the predicates: `attempt_keeps_content_state`, `fold_follows_attach`, `any_session`, `route_rules_active`, `method_rules_active`, `route_rules_version`, `RULE_FIXED`, `TeacherWeightConfig`, `ProofCheckConfig`, `RequiredMethodConfig` were searched over `src/`, `scripts/`, `tests/`, `apps/` and the vault's `_scripts/` as names and strings: no function-local or `importlib` import, no `METHOD_REGISTRY`, Typer, `MODULE_INVENTORY` or `_reg_const` entry, no frontend or phone caller; the test references are edited (§4).

## 3. Identities and stored snapshots

- **The whole-config digest and C1.** A new test pins, for the default config and for `SWITCHES_TOML` (a `learnloop.toml` setting all fifteen of the batch's switches away from their defaults), `content_key(identity_dump(config))`, the sha256 of `identity_dump(config.mastery)` and the two predictor version hashes that dump the mastery section, against digests recorded on `b4c8fbad98` from a `git archive` extract (`test_a_config_setting_the_removed_switches_keeps_every_identity`). It passes at every commit, since a switch still present dumps as it did and a removed one is put back by `RETIRED_FIELDS` with the value the file set. `test_a_vault_that_still_sets_a_removed_switch_loads_and_the_switch_reads_nothing` opens a vault whose config sets them (`load_vault`): it loads, no model has a removed field, and only the identity dump shows the value. `_pre_arc_c_shape` (the arc C digest tests' independent shape) adds the batch's fields at their defaults.
- **`tests/test_identity_pins.py`:** unmoved at every commit; nothing written with `--write`.
- **Snapshots:** none of the seven is written into a receipt, a decision record or `projection_switches`. `weight_inputs.rule` records the rule a check used, not the switch (stored `fixed` rows keep their meaning; no update reads them). The only echo is `hints report`'s section dump, which nothing compares; it stops listing the key.

## 4. Tests

The rules as D4-D6's, with the brief's: an off-only test goes with its branch; a test whose subject was "off equals the predecessor exactly" goes; a twin keeps its on side; a test that reached a predecessor through the switch keeps its successor's assertions at the head.

**Deleted** (each with its subject):
- `test_teacher_te1_weight::test_parametric_source_drops_the_pool`: `source = "parametric"` gives the learned mass alone.
- `test_teacher_te1_lesson::test_with_the_learned_weight_off_a_check_enters_at_the_types_configured_mass`: `learned = false` gives 0.5, rule `fixed`.
- `test_cold_retry_reschedule::test_off_the_assisted_retry_is_left_open_exactly_as_the_predecessor`: off equals mvp-0.37 exactly (with its helper `_predecessor_state`); the gate test's `tag-switch-off` case; the shadow-rebuild test's `off` case.
- `test_attempt_content_state_successor::test_the_gate_is_its_switch` (2 cases: the predicate), `::test_off_the_answer_reopens_the_row_as_the_predecessor`; the rebuild test's `tag-switch-off` case.
- `test_attempt_content_state_race::test_switched_off_the_retiring_sync_is_still_undone_as_the_predecessor` and `test_pr4_superseded_claims_landing::test_landing_i_control_switched_off_the_same_session_reopens_the_retired_row`: the predecessor's race, as controls.
- `test_help_fold_attach_successor`: the `tag-off` cases of the fold and priming tests, the off arm of the same-session test, the off case of the rebuild test (with its "predecessor's state" schedule tolerance).
- `test_hint_h2b_fix3::test_r1_f10_an_interrupted_answer_box_attach_never_lets_a_problem_take_the_hint`: needs the predecessor's keyed attach after the commit, which the successor does inside the attempt's transaction (its comment said it goes with the switch).
- `test_route_rules_in_grader::test_active_only_with_the_switch_on` (the predicate), `::test_the_kill_switch_grades_exactly_as_mvp016` (off equals mvp-0.16), and the prompt test's kill-switch arm.
- `test_required_method_grading::test_active_only_with_both_switches_on` (the predicates), `::test_off_the_prompt_is_the_predecessors_byte_for_byte`, `::test_the_kill_switch_grades_exactly_as_the_predecessor` (both off equals mvp-0.24), and `test_every_other_regrade_still_reads_the_item_as_it_is_now`'s `kill_switch` case.

**Every assertion changed, and why:**

| test | before | after | why |
|---|---|---|---|
| `test_reader_ca2_one_ask::test_a_hinted_cold_retry_is_practice_with_help_and_never_consumes_the_measurement` | the retry stays `pending`/`served`, the episode `cold_scheduled` | the retry is `expired` (withdrawn at submit), the episode `abandoned` | it reached CA2 as at its tag through the reschedule's switch; at the head the reschedule withdraws the retry, and this repair has no third surface, so it ends unmeasured. "Never consumes the measurement" is asserted unchanged |
| `test_followups_nov2_help_fold::test_the_keyless_window_still_reads_its_own_session_only` | a keyed `read_fold` without `any_session` folds 1 (the predecessor) | a keyed `read_fold` folds 2 | the predecessor's keyed definition is gone; the keyless assertion is unchanged |
| `test_hint_telemetry` (the `hints report` JSON) | lists `fold_follows_attach: true` | not listed | the report dumps the section as configured |
| `test_route_rules_in_grader` (5 tests that set `[required_method] enabled = false` to grade under `own-route-v1`: the prompt test, `test_live_an_unlocated_mark_down_on_a_divergent_route_is_unassessed`, `test_a_ruled_grade_is_calibrated_under_the_rules_identity_and_so_is_its_regrade`, `test_cli_dry_run_plans_one_grading_call`, `test_f4_the_graders_route_verdict_reaches_the_judgment_ledger_and_regrades_supersede_it`) | `own-route-v1`, `+own-route-v1` | `own-route-v2`, `+own-route-v2` | no writer grades under v1 now; their items have no required method, so every outcome they assert (unassessed criteria, holds, verdicts, one call) is the same under v2 |
| `test_cold_retry_reschedule::test_mvp038_…`, `test_attempt_content_state_successor::test_mvp037_…`, `test_help_fold_attach_successor::test_mvp042_…` | the field's default and its registry rule | removed (the chain assertions stay) | the field and rule are gone |
| `test_curriculum_c0b_landing::test_iii_check_once_commitments_are_never_touched_by_the_cold_retry_reschedule` | on equals off | the on side's assertions | twin |
| `test_teacher_te2_landing_r1._regrade_identity` | computed from `route_rules_version(vault)` | the `own-route-v2` constant | the function is gone (T4: plain values) |

**Same assertions, other route:**
- `test_route_rules_in_grader::test_f4_no_route_verdict_without_the_rules` and `::test_f5_a_regrade_without_the_rules_supersedes_the_held_verdict` (renamed from `…_with_the_rule_switched_off_…`): grading without the rules now goes through `diagnosis.grading_support = false` (`NO_POLICY`), the one rules-free path left; every assertion stands (no verdict; a rules-free regrade supersedes the held verdict with `not_checked`).
- `test_required_method_grading::test_grades_recorded_at_the_predecessor_replay_unchanged_at_the_successor`: rows built, not written. No writer grades a method item under mvp-0.20's rules, so the item is graded before it has a required method (mvp-0.20's outcome: the method criterion unassessed), then gains one, as an accepted repair gives it; the rebuild leaves the projection and the four tables unchanged and the criterion unassessed, as before. The record says `own-route-v2` where the original's said `own-route-v1`.
- Renamed with their on side: `test_help_fold_attach_successor::test_the_rollover_hint_is_counted_and_attached_in_the_attempts_transaction`, `::test_worked_help_on_the_rollover_primes`, `::test_a_same_session_keyed_hint_is_counted_and_attached`; `test_route_rules_in_grader::test_the_prompt_carries_the_rules_and_names_them`; `test_cold_retry_reschedule::test_the_gate_is_ca2s_rule`.

**New:** the three identity and loading tests of §3 (`test_retired_config_identities.py`).

**The census** (a scratch plugin wrapping `version_floor.may_open_below_floor`), over the 17 test files this landing edited, base code and tests against this branch: **89 test cases opened a vault below the floor at the base, 73 now (-16)**, in 10 files then and 8 now. The 8 cases the branch has and the base lacks are the same tests renamed or unparametrized (§4) at their old tags; none opens a new old vault. The 73 left are successor tests whose vaults sit at their own tag (`mvp-0.20`, `mvp-0.25`, `mvp-0.35`, `mvp-0.37`, `mvp-0.38`, `mvp-0.42`, …) for their chain and upgrade assertions: they wait on the re-tagging step, not on a switch this landing removes. The allowance stays.

Edits made by a script rather than the Edit tool: every source and test edit above was an exact-pattern replacement in a Python script that asserts each pattern occurs exactly once (or a block cut between two unique markers); `ruff check --fix --select F401` removed imports a deleted test left unused in five files.

## 5. Proof

**P-shadow.** `/home/saturn/Documents/thinking/learnanything-ad1/fixtures-local/owner-copies-mvp058` (three vaults at `mvp-0.58`), fresh copies with `copy_tree_with_databases` under `fixtures-local/d7a/{before,after}/`; `before` upgraded to the head and shadow-rebuilt by the base code (`b4c8fbad98`, a `git archive` of `src/` and `migrations/` on `PYTHONPATH`), `after` by this branch at `debed5c3e6`; then a real `learnloop rebuild-derived-state` on each side. Counts only; the copies are deleted.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| `learnloop upgrade`, both | `mvp-0.58 -> mvp-0.59` | same | same |
| shadow facet / mastery / schedule changed | 0 / 0 / 0 (80 / 21 / 99 unchanged) | 0 / 0 / 0 (3 / 18 / 77) | 0 / 0 / 0 (7 / 34 / 32) |
| `schedule_effects` due dates moved (items, cards) | 0, 0 | 0, 0 | 0, 0 |
| the two shadow reports, marker id, `as_of` and hashes aside | equal | equal | equal |
| every table of the two upgraded copies, row by row (ULIDs, stamps and hex digests normalized) | 402 tables, 19,442 rows: none differ | 402, 10,426: none | 402, 23,877: none |
| the same after the shadow | none differ | none | none |
| the same after a real rebuild on each side | 19,749 rows: none differ | 10,498: none | 23,719: none |

None of the seven is read by replay, and the rebuild comparison agrees.

**Old rows at the floor and the head.** `fixtures/mvp017_route_check_replay` copied, retagged to `mvp-0.58` and to `mvp-0.59`, rebuilt live twice by the base code and by this branch: after the first and the second rebuild, at both tags, every table is equal row by row except one `attempt_debug_payloads` row (`att_02_svd_fail`), whose only differences are the causal hypothesis ULID replay mints (used as a dictionary key, which the normalization does not reach) and the diagnosis-receipt id hashed from it, as in D5 and D6. The second rebuild grows the ledgers on both codes alike (D-36).

**Goldens.** The grade-application golden (`tests/goldens/grade_application`) and the due-queue goldens ran unchanged in the sweep (§6). The effective-defaults golden lost exactly the seven removed lines (`git diff b4c8fbad98 -- tests/goldens/effective_defaults.toml`: seven deletions, nothing added). The CLI snapshot (`tests/cli_surface.json`) did not change: no CLI parameter names these switches.

**The owner lane** (`-m owner_vaults`, 31 files, on copies made with the gate's `owner_copy_make.py` under `fixtures-local/owner-lane-d7a`, deleted after): 92 passed, 8 skipped, as at D6 part 2. No owner-lane test was edited.

**Measures** (`scripts/refactor_measures.py`, base `b4c8fbad98` against `debed5c3e6`):

| measure | base | this landing |
|---|---|---|
| ADR-019's kept-because list | 94 | 87 |
| tagged switches in `TAGGED_SWITCHES` | 95 | 88 |
| `mvp-0.N` literals: code / docstring / comment | 280 / 348 / 600 | 272 / 335 / 592 |
| `config/schema.py` lines | 5,104 | 5,015 |
| raw lines; code lines (all four packages) | 615,161; 432,582 | 614,906; 432,488 |
| functions over 200 lines | unchanged | unchanged |
| `src/` lines (diff) | | +104, -359 |
| test lines (diff) | | +257, -500 |
| comments naming a stage artifact | 2,385 | 2,381 (structure golden lowered) |

## 6. Gates run

All under the empty-home wrapper in 5 GB scopes.
- Each commit: the tests naming its switch, predicate or module (58 to 132 files), with the identity, retired-config, kill-switch and effective-defaults tests: green.
- **The sweep:** `scripts/affected_tests.py --base b4c8fbad98` selects the whole suite (`db/repositories.py` changed), so every test file ran, 1,418 files in 15 chunks of 100 at `-n 4 -m "not arc_close"` behind `flock /tmp/learnloop-fullsuite.lock`, on `debed5c3e6`: **30,620 passed, 103 skipped, 13 xfailed, no failure**, first time through.
- `test_identity_pins`, `test_retired_config_identities`, `test_architecture`, `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_structure_ratchets`, `test_kill_switches`: green (in the sweep and on the tip).
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken. `scripts/check_gate_partition.py`: 30,856 collected, landing 30,796 + arc_close 60.
- Vault: references regenerated once after the source commits (`9d7fffd98e`); the generator does not delete a section note whose section is gone, and counts notes against sections, so `Config - proof_check` and `Config - required_method` were deleted by hand in that commit. A second `generate_all.py` changed nothing. The two hand-written leaf counts (`Reference/Configuration/Configuration.md`, `Reference/Database/Database.md`: 1,182 to 1,175 leaves, 80 to 78 sections) follow. Validators: `db_validate_reference`, `module_validate`, `validate_vault` pass; `desktop_validate` fails on its activation-audit and lifecycle counts with no file under `apps/` or `Reference/Desktop/` changed from the base (as D6 recorded at its base).
- Not run (the orchestrator's): the durability lane (`test_attempt_content_state_race` carries the marker and ran here under the fast lane's patches), `--fresh-connections`, the arc-close lane, vitest (no frontend file changed).

## 7. Bug ledger

- **D7-1** (replay-read switches not recorded): unchanged by this landing; none of the seven is read by replay. Settled for `replay.ledger_bounded` and `mastery.claim_fixes_enabled` when they go (§8).
- **D7-3** (predicates reading a missing field as off): `fold_follows_attach` is gone with its switch, and so is `reschedule_cold_after_assist_active`'s getattr default of False, a fourth such read the row did not name. `claim_fixes_live` and `decision_active(None)` remain for their switches.
- **D7-5** (dead code): nothing of it belonged to these seven; the desktop's `ask.coldHelpConverts` goes with `ask.cold_help_converts`.

No new bug was found.

## 8. What remains of the batch, and judgment calls

**Not removed here:**
- `diagnosis.split_enabled` and `diagnosis.shadow`: **held by D-32**. `tests/test_sim_teach_back.py:86` sets `[diagnosis] split_enabled = false` because the simulator provider cannot isolate `blind_grading` (ledger D-32, open, due at arc D's close), a real open bug and not a predecessor comparison; that file belongs to the parallel step (`learnanything-k90`). The pair goes after that step lands. About 25 other test files set the split off to get a joint-graded attempt (D4's ports); they need a builder for joint rows when the pair goes.
- `stuck_prompt.enabled`: not started. Its readers at this tip are `attempts/stuck.py:69` and its callers `attempts/attempts.py:2864`, `cli/app.py:3460`, `tui/screens/practice.py:92`, `sidecar/context.py:1051` (the desktop's `practice.stuckPrompt`), `sidecar/handlers/practice.py:1394`, `:1648`; the desktop reads it in `algoConfig.ts`, `PracticeScreen.tsx` and `DialogueProbe.tsx`, and its removal also removes the TUI's `dont_know` door and the non-stuck tail of `submit_dont_know` (the RPC stays: an empty stuck answer). About 15 Python and 12 desktop test files touch it.
- `ask.cold_help_converts` (with the desktop's dead `ask.coldHelpConverts`, D7-5) and `eligibility.enabled` with the pre-eligibility cold lane and hold: not started (the inventory's rows stand).
- `replay.ledger_bounded` and `mastery.claim_fixes_enabled`: the batch's replay-read pair, each to go alone in the next landing, as the brief orders.

**Judgment calls:**
1. **The landing stops after seven switches**, at a clean boundary, rather than carrying the batch's larger removals (the stuck prompt's desktop and TUI doors, the eligibility predecessor, the split) into one review.
2. **`hints.fold_follows_attach` takes the `any_session` parameter with it**, through the store and the sidecar, because its only producer was the predicate; the keyless window's clauses are the same set.
3. **`proof_check.enabled` and `required_method.enabled` are one commit**: the second is read only through the first's predicate, and both collapse into the constant `own-route-v2`.
4. **Sections left empty are removed** (`[teacher.weight]`, `[proof_check]`, `[required_method]`) and retired on their parent, as arc C did with `[locks]`; a vault that sets one loads with the table kept as an unread extra.
5. **Tests that pinned `own-route-v1` grade under v2** rather than being deleted: their subject is the own-route rules' outcomes, which v2 keeps for items without a required method.
6. **The no-rules tests move to `diagnosis.grading_support = false`**, the rules-free path that stays.
7. **CA2's hinted-retry test asserts the head's withdrawal**: its vault has no third surface, so the episode ends; "never consumes the measurement" is unchanged.
8. **`LW.RULE_FIXED` is deleted** although stored rows may say `fixed` (only a vault that ran with the switch off has them, and none does): no reader compares against the constant, and the module's comment now says what such a row means.

## 9. Docs

- ADR-019 says what a removed switch's field becomes, what the kept-because list is for, and that this batch began the removals (94 to 87).
- `Concepts/Algorithm Versions and Reproducibility` and `Maps/LearnLoop Pipeline Map` say the own-route and method switches went with the floor; `Concepts/Attempt Processing` and `Concepts/Learning System` name none of the seven and are unchanged. The playbook's two dated records (route-check-in-grader, method-explicit items) are history and are left as written.
- Ledger rows D7-1, D7-3 and D7-5 say what this landing settles (§7).
