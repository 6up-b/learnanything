# Refactor D7, batch 1, parts 1 to 4: kill switches at or below the floor (grading, attempts, eligibility, the diagnosis split)

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

# Part 2

Branch `refactor/d7b-switches-rest`, based on part 1's tip `b391ed7cc2`. Same rule, precondition and conventions as part 1 (§1-§9 above). This landing removes two more of the batch's switches, `ask.cold_help_converts` and `stuck_prompt.enabled`, and stops at the boundary the brief allows after them: `eligibility.enabled` is blocked on a file this step was told to stay out of (§14), and the two replay-read switches are not started. Line numbers are the base's (`b391ed7cc2`).

## 10. Step 0, per switch

### `ask.cold_help_converts` (mvp-0.35)

- **Reads:** one predicate, `serve_eligibility.help_converts_active` (`serve_eligibility.py:956`, getattr default **False**: a vault without the section, or no vault, read as the predecessor), and its callers: submit (`attempts/attempts.py:2894`, as `submit_decision(help_converts=)`, `:2753`, into `EligibilityInputs.help_converts`, `serve_eligibility.py:403`, read at `:689`); the Reader's unbound cold Ask (`reader/reader_dialogue.py:769`, `:870-871`); the bound Ask (`sidecar/handlers/reader_tutor.py:245`, `BoundAsk.cold_counts_every_question`); a workbench question on a cold item (`sidecar/handlers/tutor_qa.py:446`, `PanelAsk.count_every_question` into `tutor_qa.ask_question(count_every_question=)`); the check's served view (`intent/checks.py:185`, `:209`); the cold-retry reschedule's predicate (`diagnosis/remediation.py:1124`); the sidecar snapshot (`sidecar/context.py:1111`), which the desktop parsed into `ask.coldHelpConverts` and no non-test code read (ledger D7-5).
- **Off code:** submit's refusal of a hinted cold check (`serve_eligibility.py:697-702`); the L6 rule in the three Ask paths (every cold question counts); `served_check`'s `cold_followup` duty (the measured view for a due cold follow-up); `cold_followup_view`'s `None`. With the switch gone: `EligibilityInputs.help_converts`, `submit_decision`'s parameter, `BoundAsk.cold_counts_every_question` and `BoundAsk.cold` (read only by `hint_equivalent`, which is now the ordinary classification whatever the binding), `PanelAsk.count_every_question` and `ask_question`'s `count_every_question`, `_record_cold_hint_equivalent`'s defaults (one caller, which now always passes both), `reschedule_cold_after_assist_active` (its "no vault" answer stays as `_reschedule_assisted_cold_retry`'s own `vault is None` guard), the snapshot key and the desktop flag. `COLD_CHECK_ASSISTED` stays: a declared-primed cold check is still refused with it, and logged decisions name it.
- **What else reaches the off code:** nothing. Every caller passed a loaded vault (the reschedule's no-vault callers, replay and a regrade, keep their guard). Submit's `eligibility.enabled = false` arm (the bare guard, `attempts.py:2897-2903`) refuses a hinted cold retry by itself; it belongs to the eligibility switch and is untouched here.
- **Replay:** none. Replay reads each attempt's stored flags; the rule changes what submit admits and how a new question is counted.
- **Identity:** the whole-config digest only (`RETIRED_FIELDS`). No receipt or `projection_switches` stores it; the snapshot key was live UI state.
- **Tests:** off-only and predecessor tests (§12); none reached a predecessor through `tests/successor_switches.py` (its `SWITCHES_BY_TAG` names none of this part's switches, so neither it nor its test changes).

### `stuck_prompt.enabled` (mvp-0.13)

- **Reads:** `attempts/stuck.py:69` (`stuck_prompt_active`, default True) and its seven callers: submit's refusal of a stuck draft (`attempts/attempts.py:2864`), the CLI (`cli/app.py:3460`), the terminal app (`tui/screens/practice.py:92`), the sidecar snapshot (`sidecar/context.py:1051`, the desktop's `practice.stuckPrompt`), `submit_attempt_on` (`sidecar/handlers/practice.py:1394`) and `submit_dont_know_on` (`:1648`). The desktop read the snapshot in `algoConfig.ts` and `PracticeScreen.tsx` and `DialogueProbe.tsx`.
- **What the learner sees today with it on (every owner vault), per surface, and after:**
  - *Desktop practice card:* an "I'm stuck" control (plain and classic cards), ^d labelled "I'm stuck" and opening the prompt; the same Submit sends the stuck answer. Unchanged: the off arms ("don't know" label, the `submitDontKnow` call) are gone.
  - *Desktop dialogue probe:* an "I'm stuck" button and an empty answer allowed once pressed. Unchanged; the "Don't know" button and its `submitDontKnow` branch are gone.
  - *Terminal app:* ^d opens the stuck prompt; an empty submit records an empty stuck answer (`submit_stuck_empty`). Unchanged; the `dont_know` door (a `dont_know` attempt), reached only with the switch off, is gone, and the binding is named for what it does (`stuck`).
  - *CLI:* `--stuck` accepted; `--attempt-type dont_know` recorded as an empty stuck answer with a note. Unchanged; the refusal of `--stuck` is gone.
  - *Phone:* the phone never read the switch. Its question screen always offers "I'm stuck" and sends `declaredStuck` through `submit_attempt` (`apps/learnloop-mobile/src/practice/QuestionScreen.tsx`); it never calls `submit_dont_know` (allowlisted only). Unchanged.
  - *A client that still calls `submit_dont_know`:* an empty stuck answer, as today.
- **The non-stuck tail of `submit_dont_know` (`practice.py:1695-1748`).** Reached only when `stuck` was false, and `stuck` was the predicate of the vault alone: no item type, probe or surface reached it (a probe takes the stuck branch with `stuck_probe`, an item whose types lack `independent_attempt` takes `hint_fold.attempt_type`). So it is dead and goes; the RPC stays. `DontKnowInput.self_grade` stays, read by nothing, because the params model forbids extra keys and an older client may still send it. `submit_attempt_on`'s route of a stale empty stuck answer to `submit_dont_know_on` (`:1395-1423`) was the switch's own off arm, and with it `submit_dont_know_on`'s `hint_window_fold` parameter (its only non-default caller). `client.submitDontKnow` in the desktop has no caller left and goes.
- **Replay:** reads the stored `declared_stuck` (`attempts.py:1429`), never the switch.
- **Identity:** the whole-config digest only. Nothing stores the snapshot key.
- **Tests:** §12.

### `eligibility.enabled` (mvp-0.27): not removed, see §14.

## 11. What went

| commit | switch | what |
|---|---|---|
| `d38e44156f` | `ask.cold_help_converts` | Reader CA2's one help rule is the only rule; the predicate and everything that carried it go (§10); the desktop's dead `coldHelpConverts` goes (D7-5) |
| `f756285e51` | `stuck_prompt.enabled` | every surface offers "I'm stuck"; the predicate, the desktop's "don't know" paths, the terminal app's `dont_know` door, the CLI refusal and `submit_dont_know`'s non-stuck tail go; `[stuck_prompt]` retired whole |

In each: the field into `RETIRED_FIELDS` (`removed_by` `D7`; `AskConfig` now keeps retired fields; `[stuck_prompt]` is retired whole on `LearnLoopConfig`), the kill-switch table row and its kept-because line, the registry rule (`ask.cold_help_converts`; `stuck_prompt.enabled` had no rule of its own in `params/parameter_registry.py`), the vault generator's descriptions (`stuck_prompt`), the tag's comment in `algorithm_versions.py`, the effective-defaults golden (one line each), and the desktop in the same commit (typecheck and vitest). Kept-because list: 87 to 85.

**Deletion proof:** `help_converts_active`, `help_converts`, `count_every_question`, `cold_counts_every_question`, `reschedule_cold_after_assist_active`, `_cold_help_converts`, `coldHelpConverts`, `stuck_prompt_active`, `stuckPrompt`, `submitDontKnow`, `dont_know` (the TUI method and `action_dont_know`) searched over `src/`, `scripts/`, `tests/`, `apps/` and the vault's `_scripts/` as names and strings: no function-local or `importlib` import, no registry, Typer or `MODULE_INVENTORY` entry left. The sidecar's `submit_dont_know` RPC, `DontKnowInput` and the phone's allowlist entry stay.

## 12. Tests

**Deleted** (each with its subject):
- `test_reader_ca2_one_ask::test_the_rule_is_live_only_with_its_switch` (the predicate); `::test_switched_off_a_hinted_cold_retry_is_refused_as_before` (off refuses help on a cold retry); the off arm of `::test_a_due_cold_follow_up_is_served_with_the_take_step`.
- `test_cold_retry_reschedule::test_the_gate_is_ca2s_rule` (2 cases: the predicate and its no-vault answer, which the replay test still covers: replay schedules nothing).
- `test_intent_fix_round4::test_f15_a_check_with_a_cold_follow_up_is_served_under_that_duty` (the measured view of a due cold follow-up, DL2 as at its tag with CA2 off).
- `test_reader_rw1c_review::test_a_cold_bound_ask_is_a_hint_whatever_its_type_and_its_cold_row` (4 cases: the L6 rule; its comment said it goes with the switch).
- `test_reader_workbench_rw2a::test_a_cold_check_with_the_book_open_is_refused_and_the_session_and_steps_stay` (submit's refusal of help on a cold check, as at mvp-0.27 with CA2 off).
- `test_serve_eligibility::test_the_cli_attempt_refuses_an_assisted_cold_check_without_prompting` (the same refusal through the CLI).
- `test_stuck_prompt::test_the_control_is_offered_and_the_switch_restores_it` (the predicate), `::test_kill_switch_restores_dont_know_exactly` (off equals mvp-0.12), `::test_cli_refuses_stuck_where_it_is_not_offered` (the CLI refusal), and the switched-off half of `::test_a_stuck_draft_is_refused_where_the_control_is_not_offered` (now `test_a_stuck_draft_is_never_dont_know`, the other half).
- `test_stuck_prompt_replay::test_the_kill_switch_never_changes_how_stuck_answers_replay` (on and off rebuild alike: the twin's on side is two rebuilds, which the file's other tests cover).
- `test_tui_practice::test_practice_screen_dont_know_runs_shared_post_attempt_pipeline` (the terminal app's `dont_know` door).
- vitest: `PracticeScreen.test.tsx` "keeps today's don't know control and call when the vault does not offer I'm stuck" and "never restores stuck mode where the vault does not offer it"; `DialogueProbe.test.tsx` "keeps Don't know where the vault does not offer I'm stuck".

**Every assertion changed, and why:**

| test | before | after | why |
|---|---|---|---|
| `test_reader_ca2_one_ask::test_the_successor_is_one_constant_after_rebuild_equivalence` | `AskConfig().cold_help_converts is True`, its registry rule | removed (`panel_enabled`'s stay) | the field and rule are gone |
| `test_reader_ca2_one_ask::test_a_hinted_cold_check_converts` (was `…_the_predecessor_refuses_…_and_the_successor_converts_it`) | refused with `help_converts=False`, converted with `True` | converted | twin: the on side |
| `test_reader_ca2_one_ask::test_the_bound_cold_ask_follows_the_rule` | `substantive or cold_every` | `substantive` (one parameter) | twin; `BoundAsk` has no cold rule now |
| `test_reader_ca2_one_ask::test_the_readers_cold_paths_count_only_a_substantive_question` (was `…_count_a_clarification_only_under_the_predecessor`) | counts `not converts or mechanism`; stored type `other` when off | counts `mechanism`; stored type the tutor's | twin: the on side |
| `test_reader_ca2_one_ask::test_the_snapshot_carries_the_panel` | the snapshot's `ask` has `coldHelpConverts: True` | not listed | the key is gone |
| `test_reader_ca2_codex_review` (workbench question on a cold item; worked help taken first) | parametrized on the switch; off refuses / counts every question | the on side only | twins |
| `test_reader_ca2_codex_review::test_the_answer_box_on_a_cold_item_…` | ran with the switch off | runs at the default | its assertion (a clarification is free) holds either way |
| `test_intent_fix_round4::test_f15_the_serve_chooses_the_variant_server_side_and_one_completion_satisfies_both` | the serve carries `duty: cold_followup`, the measured banner, no help header | no duty, not the measured banner, the help header, `cold` | it reached DL2's F15 duty through CA2's switch; at the head a due cold follow-up is served with the ladder (CA2 §15 Q4). "One completion satisfies both" is asserted unchanged |
| `test_curriculum_c0b_landing::test_iii_…` | `reschedule_cold_after_assist_active(vault) is True` | removed | the predicate is gone; the reschedule's behaviour assertions stand |
| `test_stuck_prompt::test_sidecar_empty_stuck_submission_is_instant_and_routes_to_feedback` | snapshot `practice.stuckPrompt is True` | the snapshot has no `practice` key | the key is gone |
| `test_stuck_prompt::test_tui_ctrl_d_…` | `screen.stuck_prompt is True` | removed | the attribute is gone |
| `test_stuck_prompt_replay::test_a_recorded_stuck_answer_replays_as_stuck_under_an_older_tag` (was `…_with_the_prompt_off`) | wrote `[stuck_prompt] enabled = false`, asserted the predicate false | neither | the key is ignored and the predicate gone; every replay assertion stands |
| `test_stuck_prompt_replay::test_an_attempt_an_older_tag_wrote_…` | `stuck_prompt_active(head)` | removed | the predicate is gone |
| `test_reading_step_switch` | `stuck_prompt_active(switched_off)` | removed | the predicate is gone |
| vitest `PracticeScreen.test.tsx`, `DialogueProbe.test.tsx` | `submitDontKnow` not called | removed | the client method is gone |
| vitest `PracticeScreen.adaptiveOff.test.tsx` (4 file snapshots) | the card as the base rendered it with `stuckPrompt` false | the same card with the "I'm stuck" control and the `^d I'm stuck` key | the snapshots were written with the switch's off value (the test set no `practice` key); a token diff of every frame shows exactly those two differences and nothing else. The test's comment says so |

**Same subject, other route:**
- `test_sidecar_contract::test_sidecar_counts_queued_intervention_followups_in_session_summary`: it made its error-tagged miss with a `dont_know` attempt, reached by turning `stuck_prompt.enabled` off. It now submits a self-graded zero tagged `retrieval_failure` (the tag `dont_know` carried); every assertion stands (the follow-up queued, the triggered action, the summary's count). It still turns `followup.generate_and_serve` and `voi_stopping.enabled` off, for later batches.
- `test_tui_feedback::test_tui_retry_resumes_a_committed_grade_instead_of_recording_another`: its `dont_know` case is now `empty_stuck` (press "I'm stuck", empty box, `submit_stuck_empty`): the retry still resumes the committed grade.

Edits made by a script rather than the Edit tool: most source and test edits were exact-pattern replacements in Python one-offs that assert each pattern occurs exactly once (or a block cut between two unique markers); the desktop's test mocks lost `coldHelpConverts: true`, `practice: { stuckPrompt: true }` and `submitDontKnow: vi.fn()` by a mechanical replace over the files that named them; `ruff check --fix --select F401` removed the imports deleted tests left unused.

## 13. Proof

**The retired-config identities, with each entry removed.** For each of the nine `removed_by = "D7"` entries (part 1's seven and this part's two), `RETIRED_FIELDS` without that one line (a mutation, not committed) makes `test_a_config_setting_the_removed_switches_keeps_every_identity` fail: both cases for a field of a kept model (`TeacherConfig`'s two, `PracticeConfig`'s two, `HintsConfig`, `AskConfig`), the `default` case for a section retired whole (`[proof_check]`, `[required_method]`, `[stuck_prompt]`; the `switched` case passes, because the file's table survives on `LearnLoopConfig` as an unread extra and dumps the same bytes). Restored after each run.

**P-shadow**, as part 1's (§5), base `b391ed7cc2` against this branch at `f756285e51` (counts only; copies deleted):

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| `learnloop upgrade`, both | `mvp-0.58 -> mvp-0.59` | same | same |
| shadow facet / mastery / schedule changed | 0 / 0 / 0 (80 / 21 / 99 unchanged) | 0 / 0 / 0 (3 / 18 / 77) | 0 / 0 / 0 (7 / 34 / 32) |
| `schedule_effects` due dates moved (items, cards) | 0, 0 | 0, 0 | 0, 0 |
| the two shadow reports, marker id, `as_of` and hashes aside | equal | equal | equal |
| every table of the two upgraded copies, row by row | 402 tables, 19,442 rows: none differ | 402, 10,426: none | 402, 23,877: none |
| the same after the shadow | none differ | none | none |
| the same after a real rebuild on each side | 19,749 rows: none differ | 10,498: none | 23,719: none |

**Old rows at the floor and the head** (`fixtures/mvp017_route_check_replay`, retagged to `mvp-0.58` and `mvp-0.59`, two live rebuilds per code): every table equal row by row after each rebuild at both tags except the one `attempt_debug_payloads` row of `att_02_svd_fail`; with replay's minted hypothesis ULIDs normalized in its dictionary keys too, the only differing field is the diagnosis receipt's id (hashed from that ULID), as in part 1.

**Goldens.** The effective-defaults golden lost exactly two lines (`ask.cold_help_converts`, `stuck_prompt.enabled`) and gained none. The CLI snapshot did not change (no CLI parameter names either switch; `--stuck` keeps its contract). The grade-application and due-queue goldens: see §15.

## 14. `eligibility.enabled`: step 0, and why it stops here

**Every reader of the old lane** (base line numbers), as the inventory's hazard asks, before anything is deleted:
- the predicate `serve_eligibility.decision_active` (`serve_eligibility.py:968`, getattr default **False**: no vault, or a config without the section, reads as mvp-0.26);
- the scheduler: the cold lane (`scheduling/scheduler.py:1924`, off arm `_predecessor_defer_revealed_cold_followups`, `:2039-2179`), and the three hold callers `cold_check_hold_until` (`:2218`), `cold_check_serve_hold` (`:2303`) and `cold_check_serve_decision` (`:2327`), whose off arms call `_predecessor_cold_check_hold_until` (`:2226-2283`), which alone calls `reveal_coverage.routine_displays_covering` (`reveal_coverage.py:124`) from the scheduler;
- serving exclusions and doors that reach those holds: the daily plan (`daily_plan/engine.py:2306`, `:4100`, `:5872`), the terminal app's serve (`tui/screens/practice.py:98`), the sidecar's queue (`sidecar/handlers/queue.py:443`, and `deferred_cold_followups` at `:229`, which reads `_cold_task_reveals` with no switch and stays), the CLI's serve (`cli/app.py:3487`), the quick check (`diagnosis/quick_check.py:203`);
- submit: the bare cold guard (`attempts/attempts.py:2878`, off arm `:2897-2903`) and the auto-prime window (`:3253`);
- the probe guard: `diagnosis/probe_episodes.py:1250` (`routine_display_covers_item`, whose off arm is `routine_displays_covering`'s other caller) and `:1271` (`refuse_routine_display_covered`);
- doctor and reports: none read the switch or the old lane.

**Why it stops.** Two of those readers are in `diagnosis/probe_episodes.py`, which this step was told to stay out of (it has just changed on main). And there the predecessor is reachable without the switch: both functions take `vault: LoadedVault | None = None`, so a caller that omits the vault gets mvp-0.26's guard through `decision_active(None)` (ledger D7-3). Every production caller found passes one (`probe_episodes.py:1412`, `:1529`, `:1692`; `causal_orchestrator.py:2033`; `sidecar/handlers/practice.py:646`), and `refuse_routine_display_covered`'s own off arm calls `routine_display_covers_item` without one. Removing the field while leaving those two arms would make `decision_active` read the missing field as off for every vault, which serves the predecessor everywhere; making it a constant while the arms stay would leave dead code in a file this step may not touch. So the switch, its predicate, the scheduler's predecessor functions and `routine_displays_covering` are all left for a landing that may edit `probe_episodes.py` (after K9.0b is on main), with the `vault=None` defaults made required or the off arms deleted in the same commit. About 255 source lines in 9 files; the tests that turn it off: `test_serve_eligibility.py`, `test_serve_eligibility_review.py`, `test_reader_workbench_rw2a.py`, `test_forced_withdrawal_records.py`, `test_device_eligibility.py`, `test_mobile_rpc.py`, `test_ux_phase4_feedback.py`, `test_ux_phase4_landing.py`, and the helper `serve_eligibility_helpers.py`.

`replay.ledger_bounded` and `mastery.claim_fixes_enabled` were not started: this landing hands back at the boundary the brief allows after the small switches, and each of those goes alone with its own rebuild proof.

## 15. Gates run

All under the empty-home wrapper in 5 GB scopes.
- Each commit: the tests naming its predicate, module or surface, with the identity, retired-config, kill-switch, effective-defaults, CLI-snapshot, test-layout, architecture and structure tests: 113 files for `ask.cold_help_converts` (3,331 passed, 2 skipped), 185 files for `stuck_prompt.enabled` in two chunks behind the lock (4,715 passed; one collection error, `test_reading_step_switch.py` still importing `stuck_prompt_active`, fixed in that commit and rerun: 5 passed). Desktop, in each commit: `tsc --noEmit` clean; vitest over every touched test file and `src/screens`, `src/components`, `src/app` (switch 2: 278 files, 2,799 passed).
- **The sweep:** `scripts/affected_tests.py --base b391ed7cc2` selects 1,336 test files; all ran in 14 chunks of 100 at `-n 4 -m "not arc_close"` behind `flock /tmp/learnloop-fullsuite.lock`, on `5374ead19c`: **29,085 passed, 101 skipped, 13 xfailed, 3 errors**. The three errors are teardown thread-guard reports in `test_followup_next_matrix.py` (a background carry thread still draining after the 2 s grace); the file passed whole on a rerun (71 passed). Ledger D7-7. The grade-application and due-queue goldens ran in it unchanged.
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken. `scripts/check_gate_partition.py`: 30,833 collected, landing 30,773 + arc_close 60. `tests/test_structure_ratchets.py`: golden lowered (`c6bc1e17dc`: functions over 200 lines 74 to 73, `submit_attempt_on` no longer one; stage-naming comments 2,381 to 2,378).
- Vault: references regenerated once after the source commits (`5374ead19c`), `Config - stuck_prompt` deleted by hand and the two hand-written leaf counts changed (1,175 to 1,173 leaves, 78 to 77 sections); a second `generate_all.py` changed nothing. Validators: `db_validate_reference`, `module_validate`, `validate_vault` pass; `desktop_validate` fails on its hard-coded source count (expects 324 TypeScript files, finds 326), its activation audit and its lifecycle count, with no TypeScript file added or removed by this branch (the same counts at the base; part 1 recorded the last two).
- The owner lane: §16.
- Not run (the orchestrator's): the durability lane, `--fresh-connections`, the arc-close lane, the full vitest suite (`npm test`), `cargo check`, `npm run frontend:build`.

## 16. The owner lane, the census and the measures

**The owner lane** (`-m owner_vaults`, 31 files, copies made with the gate's `owner_copy_make.py` under `fixtures-local/owner-lane-d7b`, deleted after): 92 passed, 8 skipped, as at part 1. No owner-lane test was edited.

**The census** (part 1's scratch plugin around `version_floor.may_open_below_floor`), over the 17 test files this part edited, base code and tests against this branch: **68 test cases opened a vault below the floor at the base, 59 now (-9)**, in 9 files then and 8 now. The 4 cases the branch has and the base lacks are the same tests renamed or unparametrized (§12) at their old tags. The 59 left (`test_intent_fix_round4` 18, `test_serve_eligibility` 16, `test_reader_ca2_one_ask` 15, the stuck-prompt files 6, four others 4) are successor tests whose vaults sit at their own tag for their chain and upgrade assertions, and `test_serve_eligibility`'s also wait on `eligibility.enabled`; none waits on a switch this part removed. (The base run had two unrelated failures, `test_mobile_allowlist::test_the_clients_retry_policy_is_the_allowlists` and `test_reader_rw1c_review::test_the_desktops_offers_only_bound_ask_refuses_tools_when_cold`, because the base extract carries no `apps/`.)

**Measures** (`scripts/refactor_measures.py`; the base column is part 1's run at `debed5c3e6`, whose `src/` and `tests/` differ from `b391ed7cc2` only in the structure golden):

| measure | part 1 | this part |
|---|---|---|
| ADR-019's kept-because list | 87 | 85 |
| tagged switches in `TAGGED_SWITCHES` | 88 | 86 |
| `mvp-0.N` literals: code / docstring / comment | 272 / 335 / 592 | 268 / 330 / 582 |
| `config/schema.py` lines | 5,015 | 4,989 |
| raw lines; code lines (all four packages) | 614,906; 432,488 | 614,626; 432,306 |
| functions over 200 lines | 74 | 73 |
| `src/` lines (diff from `b391ed7cc2`) | | +116, -396 |
| Python test lines (diff) | | +75, -346 |
| desktop lines (diff, `apps/`) | | +87, -231 |
| comments naming a stage artifact | 2,381 | 2,378 |

## 17. Bug ledger

- **D7-1:** unchanged in substance; neither switch here is read by replay. The row says what is left (the two replay-read switches, not started).
- **D7-3:** `help_converts_active`'s getattr default of False went with its switch (a fifth such read the row did not name). `decision_active(None)` stays with `eligibility.enabled`, and is reachable through the probe guard's `vault=None` defaults (§14).
- **D7-5:** the desktop's `ask.coldHelpConverts` and the snapshot key that fed it are deleted.
- **D7-7 (new):** the sweep's teardown errors in `test_followup_next_matrix.py` (§15).

## 18. What remains, and judgment calls

**Not removed here:** `eligibility.enabled` with the pre-eligibility cold lane and hold (§14: needs `diagnosis/probe_episodes.py`); `replay.ledger_bounded` and `mastery.claim_fixes_enabled` (not started; each alone, with a real rebuild on every copy and the mvp-0.17 fixture after one and two rebuilds); `diagnosis.split_enabled` and `.shadow` (held by D-32, not this part's).

**Judgment calls:**
1. **The landing stops after two switches.** The third, `eligibility.enabled`, cannot be removed without editing `diagnosis/probe_episodes.py`, which this step was told to leave alone; a removal that left its two off arms would serve the predecessor to every vault (the predicate reads a missing field as off). The replay-read switches each go alone, so they were not started behind a blocked one.
2. **`BoundAsk.cold` goes with `cold_counts_every_question`**: under the one help rule nothing reads the binding's cold status (`hint_equivalent` is the ordinary classification either way).
3. **`served_check` no longer computes the cold-follow-up duty** it then discarded; the measured view is reached only by a caller's stricter duty (`diagnostic`).
4. **`submit_dont_know` stays as an RPC** (an older desktop build, the phone's allowlist, the retry policy name it) and records an empty stuck answer, as it did; its `self_grade` field stays and is read by nothing, because the params model forbids extra keys.
5. **The desktop's `client.submitDontKnow` is deleted**: no caller is left, and the phone has its own client.
6. **The terminal app's ctrl+d binding is renamed from `dont_know` to `stuck`**, the action it now always runs.
7. **The adaptive-off file snapshots are rewritten**, not deleted: their subject is "adaptive hints off changes nothing", and the only difference is the stuck control the switch's off value used to hide (a token diff of every frame).
8. **The session-summary follow-up test keeps its subject through a tagged self-graded zero** rather than going with the stuck switch: the summary's count of queued follow-ups had no other positive test.
9. **No `tests/successor_switches.py` change:** neither switch is in its table.

## 19. Docs

- ADR-019: the kept-because list went to 85 with this part.
- `Concepts/Algorithm Versions and Reproducibility`: mvp-0.13's row says its kill switch went with the floor. `Concepts/Attempt Processing` and `Concepts/Learning System` name neither switch and are unchanged.
- Ledger rows D7-1, D7-3, D7-5 updated; D7-7 added.

Rule exceptions: `npm ci --offline` (to give the worktree a `node_modules` for typecheck and vitest) ran with the real `HOME` so npm could read its package cache; it ran no install scripts (`--ignore-scripts`) and nothing else ran outside the wrapper.

# Part 3

Branch `refactor/d7c-eligibility-split`, based on `be034aaec8` (part 2's tip merged with main: parts 1 and 2, the robust gate fixes, the simulation fixes and the arc D close fixes). Same rule, precondition and conventions as parts 1 and 2. This landing removes `eligibility.enabled` with the pre-eligibility cold lane and hold. It does **not** remove `diagnosis.split_enabled` and `diagnosis.shadow`: their step 0 (§21) found readers of stored rows that ask the split switch, which this step was told to stop and report on. Line numbers are the base's (`be034aaec8`).

## 20. `eligibility.enabled` (mvp-0.27)

### Step 0

**The predicate** `serve_eligibility.decision_active` (`serve_eligibility.py:946`, getattr default **False**: no vault, or a config without `[eligibility]`, read as mvp-0.26) and its eleven readers:

| reader | what it passes today | off arm |
|---|---|---|
| submit, `attempts/attempts.py:2871` (`_resolve_attempt_target`) | its `vault: LoadedVault` (every caller loads one) | the unbounded auto-prime window and the bare cold guard (`:2895-2903`) |
| `attempts/attempts.py:3246` (`_apply_attempt_in_transaction`) | its `vault: LoadedVault` | historical writers' window unbounded |
| CLI attempt, `cli/app.py:3487` | `loaded` | no serve decision |
| quick check, `diagnosis/quick_check.py:203` | its vault (read as `vault.practice_items` below) | no reveal reads (the serving exclusions alone) |
| the queue's cold lane, `scheduling/scheduler.py:1924` (`_defer_revealed_cold_followups`, from `_due_queue`) | `_due_queue`'s vault | `_predecessor_defer_revealed_cold_followups` (`:2039-2179`) |
| `cold_check_hold_until` (`:2218`), `cold_check_serve_hold` (`:2303`), `cold_check_serve_decision` (`:2327`) | their callers' vaults: `daily_plan/engine.py:2306`, `:4100`, `:5872` (`env.vault`), `tui/screens/practice.py:98` (`state.vault`), `cli/app.py:3486` (`loaded`), `sidecar/handlers/queue.py:442` (via `revalidate_cold_check`, called at `queue.py:407`, `practice.py:371`, `daily_plan.py:829` with the handler's vault) | `_predecessor_cold_check_hold_until` (`:2226-2283`), the only scheduler caller of `reveal_coverage.routine_displays_covering` |
| `sidecar/handlers/queue.py:443` (`revalidate_cold_check`) | the handler's vault | returns None (no `eligibility` key on the detail) |
| the probe guard, `diagnosis/probe_episodes.py:1250` (`routine_display_covers_item`) and `:1271` (`refuse_routine_display_covered`) | see below | `routine_displays_covering` alone; `refuse_routine_display_covered`'s own off arm called `routine_display_covers_item` **without** a vault |

Doctor and reports read neither the switch nor the old lane. Replay reads each attempt's stored `primed` flag (`attempts/attempts.py:3240`: the auto-prime is skipped on `replace_existing`), never the switch. No identity names it but the whole-config digest; no receipt, decision record or `projection_switches` stores it.

**The D7-3 hazard: every caller of the two guards and of `decision_active`, and what each passes.** Both guards defaulted `vault: LoadedVault | None = None`, and `decision_active(None)` read off, so a caller that omitted the vault got mvp-0.26's guard.

| caller | passes |
|---|---|
| `probe_episodes.py:1412` (`presentation_commit_payload`, the guard every new presentation row passes) | `vault=vault`, its required `vault: LoadedVault`; its callers `commit_presentation` (`:1308`) and the scheduler's slate (`scheduler.py:1140`) pass loaded vaults |
| `probe_episodes.py:1529` (`serve_presentation`, `vault: LoadedVault \| None = None`) | its own `vault`, which its callers set: `probe_episodes.py:1653` (`commit_item_presentation`), `probe_dialogue.py:328`, `sim/diagnostic_validation.py:542`, `sidecar/handlers/practice.py:602`: each a loaded vault (each reads `vault.practice_items` or `eligible_instruments(vault, ...)` first) |
| `probe_episodes.py:1692` (`plan_precommitted_block`) | `vault=vault` (it reads `vault.config.probe.block` first) |
| `causal_orchestrator.py:2033` (`_answer_shown`, `vault=None` default) | its caller `:2157` passes the offer's vault (read as `vault.practice_items` just before) |
| `sidecar/handlers/practice.py:646` | the handler's vault (read as `vault.config.probe.shadow` just before) |
| `probe_episodes.py:1272` (the guard's own off arm) | **no vault**: reached only when the switch was already off |
| `decision_active`'s other ten callers | the loaded vaults in the table above |
| tests | 23 call sites (17 files) of `serve_presentation` passed **no vault** (`tests/probe_episodes_helpers.py:111`, `p2_acceptance_helpers.py:80`, `test_causal_repair_sidecar_rpcs.py:475`, `test_characterization_probe_regrade.py:52`, `probe_block_end_helpers.py:109`, `test_characterization_probe_replay.py:52`, `probe_robust_cutover_helpers.py:46`, `test_probe_orchestration_remainder.py:211`, `:287`, `:442`, `test_p2_leakage_suite.py:193`, `test_probe_audit.py:131`, `test_probe_longform_families.py:306`, `test_probe_policy.py:70`, `:109`, `:113`, `:134`, `test_probe_episodes.py:334`, `test_teacher_te2_landing_r1.py:196`, `voi_stopping_helpers.py:295`, `test_voi_merge_composition.py:540`, `test_ux_phase4_feedback.py:2669`, `:2671`): they served under the predecessor's guard |

**Finding: no production caller passes no vault.** Every owner vault took the head's arm on every probe path; only those test call sites took the predecessor's. So there is no callers' fix commit. The head's arm needs only the repository (`probe_eligibility(repository, item, clock=)`), so with the off arms gone the parameter goes from both guards and from `_answer_shown` and their callers, rather than becoming required. `serve_presentation` keeps a `vault` keyword that nothing reads, because `sim/diagnostic_validation.py:542` passes it and this step stays out of `src/learnloop/sim/` (open item). All the test call sites above now serve under the head's guard, and pass (§22).

### What went (`395268c811`)

`decision_active` and every read; `_predecessor_defer_revealed_cold_followups`, `_predecessor_cold_check_hold_until`, the scheduler's `COLD_CHECK_ROUTINE_DISPLAY` (read only by the off arms; `serve_eligibility.COLD_CHECK_ROUTINE_DISPLAY` stays), `reveal_coverage.routine_displays_covering` (its two callers were the off arms), submit's bare cold guard, the probe guard's off arms and the `vault` parameter of both guards and `_answer_shown`; `RoutineDisplayCovered`'s mvp-0.26 message (one message now; `decision` stays optional). `EligibilityConfig` and `LearnLoopConfig.eligibility`; `[eligibility]` retired whole on `LearnLoopConfig` (`RetiredField("LearnLoopConfig", ("eligibility", "enabled"), bool, True, "D7")`); the kill-switch table row and its kept-because line; the vault generator's field and section descriptions; the tag's comment in `algorithm_versions.py`; the effective-defaults golden (one line). No registry rule, no desktop or phone reader (searched `apps/`). `_cold_task_reveals` stays (`deferred_cold_followups` reads it with no switch). `tests/successor_switches.py` names none of this part's switches, so neither it nor its test changes.

**Deletion proof:** `decision_active`, `_predecessor_defer_revealed_cold_followups`, `_predecessor_cold_check_hold_until`, `routine_displays_covering`, `EligibilityConfig`, the scheduler's `COLD_CHECK_ROUTINE_DISPLAY` searched over `src/`, `scripts/`, `tests/`, `apps/` and the vault's `_scripts/` as names and strings: no function-local or `importlib` import, no registry, Typer or `MODULE_INVENTORY` entry left.

**What a learner saw, and sees:** nothing changes on any owner vault: every path already asked the one decision (the switch at its default, and no production caller reached the no-vault arm).

### Tests

**Deleted** (each with its subject):
- `test_serve_eligibility_review::test_f4_the_gate_reads_the_version_and_the_switch` (the predicate, `decision_active(None)` included).
- `::test_f4_below_the_tag_or_switched_off_the_12_9_case_is_served_as_on_mvp_026` (off equals mvp-0.26: the cold retry served, the bare refusal).
- `::test_f4_below_the_tag_or_switched_off_a_practised_cold_check_is_served` (off: a practised cold check is still served).
- `::test_f4_the_plan_serves_the_12_9_case_as_mvp_026_with_the_switch_off` (the plan's serve off).
- the `switch_off` cases of `::test_f1_…`, `::test_f4_a_probe_of_an_item_submit_would_prime_…`, `::test_f4_q33s_bounded_window_…` (twins; their successor side stays).
- `test_ux_phase4_landing::test_a_cold_check_on_a_direct_open_is_served_as_on_main_unless_a_routine_display_covers_it` (round 6's predecessor scenario on the direct opens, run with the switch off; its comment said it goes with the switch; the successor half is `test_serve_eligibility_review::test_a_cold_check_on_a_direct_open_is_withdrawn_…`).
- `test_reader_workbench_rw2a::test_with_the_eligibility_switch_off_the_old_cold_guard_still_refuses_the_book` (the bare guard; with its helper `_due_cold_check`, used by nothing else).
- the `predecessor` cases (mvp-0.11 with the switch off) of `test_ux_phase4_feedback::test_f1l_the_quick_check_never_presents_an_item_inside_routine_display_coverage` (3 cases: the predecessor's quick check presenting a full tutor answer first).

**Every assertion changed, and why:**

| test | before | after | why |
|---|---|---|---|
| `test_serve_eligibility_review::test_f1_an_auto_primed_draft_is_refused_…` | parametrized; off: the bare message | the successor's message ("still shown when this answer was started") | twin: the on side |
| `::test_f4_new_vaults_start_at_the_successor` (was `…_with_the_switch_on`) | `config.eligibility.enabled`, `decision_active(fresh)` | removed (the version assertion stays) | the field and predicate are gone |
| `::test_f4_a_probe_of_an_item_submit_would_prime_is_refused` | `(presentation is None) is (successor and enabled)` | `presentation is None` | twin |
| `::test_f4_q33s_bounded_window` | `primed is not (successor and enabled)` | `not primed` | twin |
| `test_ux_phase4_feedback::test_f1l_the_quick_check_…` | the `tutor_answer` case at mvp-0.11 presented the item first | removed with its case | the predecessor arm |
| `test_ux_phase4_feedback::test_f1l_the_sim_skips_a_covered_instrument_instead_of_aborting_the_run` (the patched `refuse_routine_display_covered`) | took and forwarded `vault=` | takes and forwards `clock=` only | the guard has no `vault` parameter (a public function patched, not a private name moved) |
| `test_forced_withdrawal_records::test_a_cold_check_served_as_practice_or_displaced_leaves_a_record` | turned the switch off so the plan's pool and serve holds took the predecessor arms and never saw the patched decision | patches `scheduler.cold_check_hold_until` and `cold_check_serve_hold` to hold nothing | the subject is the plan's own revalidation; every assertion stands |
| `tests/serve_eligibility_helpers.py` | `enabled=` on four builders | removed | no caller turns the switch off |

Edits made by a script rather than the Edit tool: most source and test edits were exact-pattern replacements in Python one-offs that assert each pattern occurs exactly once (or a block cut between two unique markers); `ruff check --fix --select F401` removed one import a deleted test left unused.

## 21. `diagnosis.split_enabled` and `diagnosis.shadow`: step 0, and why it stops here

### Every reader, classified

The split switch is read through two predicates, `attempts/blind_grading.split_grading_active` (`blind_grading.py:74`, getattr default True) and `placement/state.diagnosis_can_arrive` (`state.py:135`, the same field, default True); the shadow switch directly. Nothing in `apps/` or the sidecar's snapshot reads either.

| reader (base lines) | kind | what it does with the switch off |
|---|---|---|
| `attempts/attempts.py:704`, `:1050` (the practice door: AI grading with fallback, and the plain AI door) | new answer | grades jointly: `_complete_joint_graded_attempt` (`:2211-2286`), `_augmented_grading_context`, `_joint_sample_count`, `_run_augmented_diagnosis`, `_record_diagnostic_augmentation`; the joint stuck prompt (`:711`, `:1057`) |
| `attempts/attempts.py:978` (`plan_grading_calls`, the CLI dry run) | new answer | plans a joint call (`joint_grading_prompt_tokens`) |
| `attempts/regrade.py:216` | new grade of a stored attempt | a practice attempt without a blind record is regraded jointly; on, it is regraded blind (and gains a blind record); teach-back and an attempt already blind are unaffected |
| `attempts/grading.py:128` (`request_vault_grading_proposal`), `:145` (`vault_grading_run_identity`), `:174` (`vault_grading_calibration_identity`) | new answer (teach-back, exams, the probe audit, the taxonomy regrade, teacher checks and probes, a teach-back regrade) | the joint prompt and identity; `None` as the calibration identity |
| `diagnosis/taxonomy_regrade.py:120` | new answer (labels the check's own calls) | `GRADING_PROMPT_VERSION` |
| `diagnosis/split/jobs.py:314`, `:716`, `:1559` (lease, run, plan a diagnose job) | new work (the diagnosis of a new grade) | holds queued live diagnoses (`Repository.hold_queued_live_diagnoses`, `db/stores/diagnoses.py:885`), releases a leased one (`split_disabled`, `SPLIT_OFF_RECHECK_SECONDS`), plans `hold:split_disabled` |
| `scheduling/scheduler.py:1502` (a serving build with placement on) | new work | stamps the hold (`split_held_at`, write-once) |
| `daily_plan/engine.py:1124` (`_open_problems`) | serving | the repair lane falls back to the recency rule (`REPAIR_RULE_RECENT_ERROR`) |
| `diagnosis/split/jobs.py:147` (`diagnosis.shadow`) and `attempts/post_attempt.py:185`, `:255-256` | new work | on (shadow): a shadow diagnosis of an AI-graded attempt with no blind record; off (the default) nothing |
| **`placement/state.py:951`** via `load_miss_verdicts(diagnosis_live=)` and `load_placement_state_from_connection(diagnosis_live=)`, fed `diagnosis_can_arrive(vault)` by `placement/state.py:1444` (`load_placement_state`), `placement/decisions.py:136`, `:235`, `:346`, `:466`, `:651`, `diagnosis/quick_check.py:357`, **`placement/report.py:99`** (the placement report), **`diagnosis/text_gaps/report.py:108`** (the learner-text gaps report), **`cli/placement.py:53`** | **reader of stored rows** | a blind miss whose live diagnose job is still queued and not yet stamped held reads as decided by today's rule (`split_disabled`, as of now) instead of pending |
| **`diagnosis/split/reports.py:269`** (`m2_report`'s manifest) | **report** | echoes the switch's value (`split_enabled`) |
| `placement/state.py:873` (the stored `split_held_at` stamp) | reader of stored rows | none: it reads the stamp, never the switch; stays |
| replay (`attempts/attempts.py:1509`), `joint_grade_record`, the feedback bundle, doctor | reader of stored rows | none: each reads the attempt's recorded mode (a blind record exists or not) |

**The finding.** `load_miss_verdicts` reads stored rows (`blind_grade_records`, `attempt_diagnoses`, `post_attempt_jobs`) and asks the split switch, through the `diagnosis_live` argument, how to read one of them: a queued, unstamped live diagnose job. Three reports reach it (`placement/report.py:99`, `diagnosis/text_gaps/report.py:108`, the CLI's `placement` command `cli/placement.py:53`), and placement's own state does at every serve. `m2_report` prints the switch. On an owner vault every one of them read the switch at its default, **true** (the owner's report: no vault sets it; the three copies' configs set no `[diagnosis]` key named either switch): a queued job read as pending, and the manifest said `split_enabled: true`. So making the switch the constant true would change nothing those vaults read, but this step was told to stop and report when a reader of stored rows asks either diagnosis switch, and it did. Stored counts on the three P-shadow copies are in §23.

How joint-graded history is read does not depend on the switch anywhere: a joint grade is recognized by the absence of a blind record (`load_miss_verdicts`: "not blind-graded: no diagnosis can arrive, today's rule"; replay; `joint_grade_record`).

### What the removal would take (not started)

- **Source:** the joint arms above with `_complete_joint_graded_attempt`, `_augmented_grading_context`, `_joint_sample_count`, `_run_augmented_diagnosis`, `_record_diagnostic_augmentation`, `diagnostic_augmentation.augment_grading_context`, `diagnostic_history_context` and `record_phase_c_receipt` (their only callers are the joint arm; `run_diagnosis_samples` and `request_grading_proposal` stay for the offline evaluation and M1's baseline), the grading door's joint branches (the calibration identity becomes the blind pair), `hold_queued_live_diagnoses` and the three job sites, `diagnosis_can_arrive` and the `diagnosis_live` parameter (the stored `split_held_at` reading stays), the repair lane's fallback, the shadow trigger. `joint_grade_record`, the joint prompt and joint replay stay.
- **Tests** (28 files set the split off or the shadow on): the off-only and shadow tests go (`test_diagnosis_pipeline::test_kill_switch_restores_joint_grading`, `::test_kill_switch_holds_queued_live_diagnoses`, `::test_shadow_diagnosis_on_a_joint_vault_changes_nothing_live`, the joint tail of `::test_non_practice_graders_…`, `test_daily_plan_owner_decisions::test_repair_falls_back_to_recent_error_only_while_the_split_is_off`, `test_placement_diagnosis_decides::test_no_diagnosis_can_arrive_falls_back_to_todays_rule`'s switch case, `test_reader_guidance::test_joint_guide_plan_never_waits_on_a_shadow_diagnosis`, `test_stuck_prompt::test_an_ordinary_joint_answer_keeps_its_prompt_and_hash_exactly`, the joint arm of `::test_confusion_is_read_and_signalled_in_both_grading_modes`, `test_km4_taxonomy`'s joint prompt-version case); the files whose subject is joint history (`test_active_errors_overlay`, `test_attempt_completion`, `test_diagnosis_card`, `test_diagnosis_async_router`, `test_pfc_unverified_unassessed`, `test_stuck_prompt_replay`, `test_reader_guidance::test_joint_guide_plan_is_unchanged_by_the_overlay_read`, `test_voi_stopping::test_a_joint_vault_lane_is_unchanged`, `test_placement_diagnosis_decides::test_a_joint_grade_falls_back_to_todays_rule`, `test_diagnosis_pipeline::test_a_joint_attempt_regraded_in_a_split_vault_is_graded_blind_and_isolated`, `test_teacher_te2_landing_r1`, `test_teach_back`'s two identity tests) need a builder of joint-graded rows; joint *regrades* as stored history (`test_regrade_contract_successor`'s two `JOINT` tests, `test_route_rules_in_grader::test_f5_a_joint_regrade_supersedes_a_route_verdict`, `test_stuck_prompt::test_a_joint_regrade_rereads_the_stuck_answer_and_supersedes`, `test_ux_phase4_feedback::test_f9f_…`) need a second construction or a decision that their subject goes with the joint regrade; the rest move to blind grading (`test_deferred_regrade`, `test_diagnosis_input_provenance_landing::test_q14_…`, `test_diagnostic_augmentation::test_a_receipt_that_cannot_be_written_…` (whose subject is the joint receipt's transaction: it may go), `test_exam_session`'s joint identity case, `test_learner_text_gaps_review`'s two). This list is a reading of each test's name and switch line, not a per-test port.
- **The builder:** the joint path's writes are all made by functions that stay (`build_grading_context`, `diagnostic_verifier_observations`, `insert_agent_run` with the joint identity, `complete_codex_graded_attempt` inside `grading_in_progress`, `record_stuck_reading_judgment`, `insert_diagnostic_augmentation_receipt`, `record_grading(writer="joint_grader")`, `finish_agent_run`), so a `tests/joint_grading_helpers.py` can write the same rows from a given proposal without a model call; the C4 history it shows (and so the receipt's history ids and the run's context hash) needs `diagnostic_history_context`'s selection, which leaves production with the joint arm and would be copied into the helper. Its rows were not yet compared with a base run.

## 22. Proof (`eligibility.enabled`)

**The retired-config identity, with the entry removed.** `RETIRED_FIELDS` without the `("eligibility", "enabled")` line (a mutation, not committed): `test_retired_config_identities.py` fails three tests, `test_the_config_identity_reproduces_both_recorded_digests`, `test_an_embedding_compare_report_is_named_as_before_arc_c` and `test_a_config_setting_the_removed_switches_keeps_every_identity[default]`; the `switched` case passes, because the file's `[eligibility]` table survives on `LearnLoopConfig` as an unread extra and dumps the same bytes (as for the other sections retired whole). Restored, 16 passed. `SWITCHES_TOML` already set `[eligibility] enabled = false` and `_pre_arc_c_shape` already carried the field, so the test needed no new line; its digests are `b4c8fbad98`'s, and `ADDED_SINCE_SWITCHES_BASE` (the K9.0b default added since) is unchanged.

**P-shadow**, as parts 1 and 2 (§5, §13), base `be034aaec8` (a `git archive` of `src/` and `migrations/` on `PYTHONPATH`) against this branch at `395268c811`; counts only; copies deleted:

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| `learnloop upgrade`, both | `mvp-0.58 -> mvp-0.59` | same | same |
| shadow facet / mastery / schedule changed | 0 / 0 / 0 (80 / 21 / 99 unchanged) | 0 / 0 / 0 (3 / 18 / 77) | 0 / 0 / 0 (7 / 34 / 32) |
| `schedule_effects` due dates moved (items, cards) | 0, 0 | 0, 0 | 0, 0 |
| the two shadow reports, marker id, `as_of` and hashes aside | equal | equal | equal |
| every table of the two upgraded copies, row by row | 402 tables, 19,442 rows: none differ | 402, 10,426: none | 402, 23,877: none |
| the same after the shadow | none differ | none | none |
| the same after a real `rebuild-derived-state` on each side | 19,749 rows: none differ | 10,498: none | 23,719: none |

**Old rows at the floor and the head** (`fixtures/mvp017_route_check_replay`, retagged to `mvp-0.58` and `mvp-0.59`, two live rebuilds per code): every table equal row by row after each rebuild at both tags except the one `attempt_debug_payloads` row of `att_02_svd_fail`, whose only differing fields, with replay's minted ULIDs normalized in its dictionary keys too, are the diagnosis receipt's id (`causal_attribution.diagnosis_receipt.id` and the same receipt in `diagnosis_receipts`), hashed from the minted hypothesis id, as in parts 1 and 2.

**Goldens.** The effective-defaults golden lost exactly one line (`eligibility.enabled = true`) and gained none. The CLI snapshot did not change (no CLI parameter names the switch). The grade-application and due-queue goldens ran unchanged in the sweep (§24). `tests/test_identity_pins.py`: unmoved, nothing written.

## 23. Stored grading history on the three copies (counts only)

Read from each copy after the real rebuild, the same on both sides (`fixtures-local/d7c/{before,after}`):

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| attempts | 70 | 3 | 3 |
| AI-graded (`grading_source` `ai`/`codex`) | 29 | 3 | 0 |
| of those, graded jointly (no blind record) | 29 | 2 | 0 |
| of those, graded blind | 0 | 1 | 0 |
| joint augmentation receipts (`grader_mode` null) / blind | 11 / 0 | 2 / 1 | 0 / 0 |
| diagnose jobs (mode:state) | none | 1 (`live:done`) | none |
| queued live diagnose jobs; `split_held_at` stamps | 0; 0 | 0; 0 | 0; 0 |
| `learnloop.toml` keys `split_enabled` / `shadow`; `[eligibility]` | 0 / 0; 0 | 0 / 0; 0 | 0 / 0; 0 |

So the miss-verdict reader's switch-dependent case (a queued, unstamped live job) has no row to read on any copy, and the stamp it reads instead is absent: the three placement-facing reports read the same with the switch at either value on these copies. The joint history is read by its missing blind record. That is evidence for the next step, not a reason to have gone on.

## 24. Gates run

All under the empty-home wrapper in 5 GB scopes.
- The commit: the 142 test files naming the eligibility decision, its holds, the probe guard, the quick check, exam seeding or a cold retry, with the identity, retired-config, kill-switch, effective-defaults, CLI-snapshot, test-layout, architecture, structure and successor-switch tests, in two chunks at `-n 6` behind the lock: 4,196 passed, 18 skipped.
- **The sweep:** `scripts/affected_tests.py --base be034aaec8` selects 1,324 test files (with the standard files, 1,327); all ran in 14 chunks of 100 at `-n 4 -m "not arc_close"` behind `flock /tmp/learnloop-fullsuite.lock`, on `23c77a5dbd`: **29,013 passed, 101 skipped, 12 xfailed, no failure or error**, first time through. The grade-application and due-queue goldens ran in it unchanged.
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken. `scripts/check_gate_partition.py`: 30,863 collected, landing 30,798 + arc_close 65. `tests/test_structure_ratchets.py`: golden lowered (`d4dd36d763`: stage-naming comments 2,378 to 2,377); green with `test_kill_switches` and `test_identity_pins` after it (223 passed).
- Vault: references regenerated once after the source commit (`23c77a5dbd`); `Config - eligibility` deleted by hand and the two hand-written leaf counts changed (1,174 to 1,173 leaves, 77 to 76 sections); a second `generate_all.py` changed nothing. Validators: `db_validate_reference`, `module_validate`, `validate_vault` pass; `desktop_validate` fails on its hard-coded source count (324 expected, 326 found), its activation audit and its lifecycle count, with no file under `apps/` changed (as part 2 recorded at its base).
- The owner lane (`-m owner_vaults`, 31 files, copies made with the gate's `owner_copy_make.py` under `fixtures-local/owner-lane-d7c`, deleted after): 92 passed, 8 skipped, as at part 2. No owner-lane test was edited.
- Not run (the orchestrator's): the durability lane, `--fresh-connections`, the arc-close lane, vitest, `cargo check` (no frontend file changed).

## 25. The census and the measures

**The census** (parts 1 and 2's scratch plugin around `version_floor.may_open_below_floor`), over the 7 test files this part edited, base code and tests against this branch: **57 test cases opened a vault below the floor at the base, 47 now (-10)**, in 5 files both times. The 6 cases the branch has and the base lacks are the same tests unparametrized (§20) at their old tags. The 47 left (`test_serve_eligibility` 16, `test_serve_eligibility_review` 10, `test_ux_phase4_feedback` 10, `test_forced_withdrawal_records` 6, `test_ux_phase4_landing` 5) are tests whose vaults sit at `mvp-0.27` or another old tag for their own setup (the serve-eligibility helpers pin `mvp-0.27`): they wait on the re-tagging step, not on a switch.

**Measures** (`scripts/refactor_measures.py`, base `be034aaec8` from a `git archive` against this branch):

| measure | base | this part |
|---|---|---|
| ADR-019's kept-because list | 85 | 84 |
| tagged switches in `TAGGED_SWITCHES` | 87 | 86 |
| `mvp-0.N` literals: code / docstring / comment | 271 / 336 / 588 | 270 / 315 / 580 |
| `config/schema.py` lines | 4,994 | 4,974 |
| raw lines; code lines (all four packages) | 615,090; 432,554 | 614,757; 432,362 |
| functions over 100 lines; over 200 | 476; 73 | 475; 73 |
| `src/` lines (diff) | | +61, -394 |
| test lines (diff) | | +40, -228 |
| comments naming a stage artifact | 2,378 | 2,377 |
| effective config leaves | 1,182 | 1,181 (the measures count; the vault's catalog counts 1,173) |

## 26. Bug ledger

- **D7-1:** unchanged in substance; `eligibility.enabled` is not read by replay. What is left: `replay.ledger_bounded`, `mastery.claim_fixes_enabled` (not started) and, if they go, the split pair (not read by replay either).
- **D7-3:** `decision_active(None)` is gone with its switch, and with it the probe guard's `vault=None` defaults (no production caller reached them; §20). `claim_fixes_live` remains.
- **D7-5:** none of it belonged to `eligibility.enabled`.

No new bug was found.

## 27. What remains, and judgment calls

**Not removed here:** `diagnosis.split_enabled` and `diagnosis.shadow` (§21: readers of stored rows ask the split switch; stopped as told); `replay.ledger_bounded` and `mastery.claim_fixes_enabled` (the next step).

**Judgment calls:**
1. **No callers' fix commit.** No production caller of the probe guard or of `decision_active` passed no vault; only test call sites of `serve_presentation` did. So the D7-3 hazard was never live on an owner vault, and the fix is the removal itself.
2. **The guards lose `vault` rather than making it required:** the head's arm reads only the repository. `serve_presentation` keeps an unread `vault` keyword (`del vault`, with a docstring line saying why) because `src/learnloop/sim/diagnostic_validation.py:542` passes it and this step stays out of `sim/`.
3. **`RoutineDisplayCovered` keeps one message**; its `decision` stays optional (a test raises it without one).
4. **The plan-revalidation record test patches the plan's two holds** instead of deleting the test: its subject (the plan's own revalidation leaves a record) had no other test.
5. **Stopping before the split pair.** Every reader of the split switch is classified in §21; the miss-verdict reader and `m2_report` read stored rows or report on them and ask the switch. On the three copies that reader's switch-dependent case has no row (§23), so the constant `true` would read the same there; the call to go on is the orchestrator's.

# Part 4

Branch `refactor/d7d-diagnosis-split`, based on `1d122fee33` (part 3's tip merged with main). Same rule, precondition and conventions as parts 1 to 3. This landing removes `diagnosis.split_enabled` and `diagnosis.shadow`, on the orchestrator's decision on part 3's finding (§21): the miss-verdict reader reads as with the split on, the switch's default on every vault that opens, and `m2_report` stops printing the switch. Line numbers are the base's (`1d122fee33`) unless a line says otherwise.

## 28. Step 0, finished: every reader, and every test file

### Readers of the two switches

The split switch was read through `attempts/blind_grading.split_grading_active` (`blind_grading.py:74`, getattr default **True**, the schema default) and `placement/state.diagnosis_can_arrive` (`state.py:135`, the same); the shadow switch directly. Nothing in `apps/` reads either.

| reader (base line) | kind | with the switch gone |
|---|---|---|
| `attempts/attempts.py:704`, `:1050` (the practice door, fallback and required) | new answer | **goes with the switch**: always `_blind_grading_plan`; `_complete_joint_graded_attempt`, `_augmented_grading_context`, `_joint_sample_count`, `_run_augmented_diagnosis`, `_record_diagnostic_augmentation` deleted; `_grading_run_identity` takes the blind plan only |
| `attempts/attempts.py:978` (`plan_grading_calls`, the CLI dry run) | new answer | **goes**: always `kind="blind"`; `grading.joint_grading_prompt_tokens` (its one caller) deleted |
| `attempts/regrade.py:216` | new grade of a stored attempt | **goes** (the conjunct): a practice attempt with no blind record is regraded blind, as with the split on; the vault-door arm stays for teach-back, and its `StuckGradingProposal` branch goes (the blind door returns `to_grading_proposal`'s `GradingProposal`, never a stuck one: only the joint grader returned one) |
| `attempts/grading.py:128`, `:145`, `:174` (the vault door: teach-back, exams, the probe audit, the taxonomy check, teacher checks and probes) | new answer | **goes**: the blind contract and identities only; `vault_grading_run_identity(context)` and `vault_grading_calibration_identity()` lose the `vault` they no longer read (7 call sites, an exact-pattern script edit) |
| `diagnosis/taxonomy_regrade.py:120` | new answer (the check's own calls) | **goes**: `BLIND_GRADING_PROMPT_VERSION` |
| `diagnosis/split/jobs.py:314`, `:716`, `:1559` (lease, run, plan) | new work | **goes**: the hold, the `split_disabled` release, `SPLIT_OFF_RECHECK_SECONDS`, `hold:split_disabled`; `Repository.hold_queued_live_diagnoses` (`db/stores/diagnoses.py:885`) deleted |
| `scheduling/scheduler.py:1502` (a serving build stamping the hold) | new work | **goes** |
| `daily_plan/engine.py:1124` (`_open_problems`) | serving | **goes**: always the open-diagnosis rule. `lanes.classify_item`'s recency arm stays (§33) |
| `diagnosis/split/jobs.py:147` and `attempts/post_attempt.py:185`, `:255-256` (`diagnosis.shadow`) | new work | **goes**: an attempt with no blind record is never diagnosed (`enqueue_diagnosis` returns at the missing record, as it did with the shadow off) |
| `placement/state.py:951` via `load_miss_verdicts(diagnosis_live=)`, `load_placement_state_from_connection(diagnosis_live=)`, fed by `state.py:1444`, `placement/decisions.py:136`, `:235`, `:346`, `:466`, `:651`, `diagnosis/quick_check.py:354`, `placement/report.py:99`, `diagnosis/text_gaps/report.py:108`, `cli/placement.py:53` | **reader of stored rows (decided)** | reads as with the split on: a queued live job not yet stamped is pending. `diagnosis_can_arrive` and the parameter go from all eleven sites |
| `diagnosis/split/reports.py:269`, `:309` (`m2_report`) | **report (decided)** | the manifest's `split_enabled` key goes; the Markdown manifest line was `- algorithm A, history mode H, split enabled True, embedding model E` and is `- algorithm A, history mode H, embedding model E`. No test or document compares that text |
| `placement/state.py:873` (the stored `split_held_at` stamp) | reader of stored rows | none: it reads the stamp, never the switch; stays |
| replay (`attempts.py:1509`), `replay_grader_identity`, `joint_grade_record`, the feedback bundle, doctor | reader of stored rows | none: each reads the attempt's recorded mode |

No reader of stored rows other than the two decided ones asks either switch (searched `src/`, `scripts/`, `apps/`, the vault's `_scripts/` for both predicates, both field names and `diagnosis_live`).

**Where the joint rule lives.** Joint history is recognized by the missing blind record, never by config: `placement/state.py:831` on the branch (`if latest_record is None:` → `FALLBACK_NOT_BLIND_GRADED`, with a comment saying so), `attempts/attempts.py:1560` (`replay_grader_identity`: no blind record and no blind stamp is the joint identity, `None`), and `diagnosis/split/live.py:483` (the grader mode a diagnosis context reads).

**A regrade of a jointly graded attempt at the head.** With the split on (every owner vault), `regrade_attempt` built the blind plan for any practice attempt without a blind record: it grades blind in an isolated turn, appends a first blind record (`regrade: true`, no `supersedes_id`) and queues the diagnosis in the publication. That is exactly what the branch does (the condition lost only its switch conjunct): `test_diagnosis_pipeline::test_a_joint_attempt_regraded_in_a_split_vault_is_graded_blind_and_isolated` asserts it at the ports commit (switch present) and after the removal. A jointly graded teach-back is regraded through the vault door, blind, under the blind calibration pair, as with the split on (`test_teach_back::test_a_teach_back_regraded_blind_keeps_the_blind_identity_through_rebuilds`).

### The test files, by reading

| file | sort | tests |
|---|---|---|
| `test_active_errors_overlay` | builder | `test_overlaid_read_equals_the_raw_read_on_a_joint_vault` (now `…_on_joint_history`): the shadow diagnosis it also drained goes with `diagnosis.shadow` |
| `test_attempt_completion` | builder | `test_pipeline_keeps_one_hypothesis_version_with_grader_provenance` (2 cases), `test_block_closing_diagnostic_answer_keeps_grader_provenance` (2 cases): the post-attempt pipeline over a stored joint grade, its subject |
| `test_daily_plan_owner_decisions` | delete | `test_repair_falls_back_to_recent_error_only_while_the_split_is_off`: the plan's repair lane with the split off |
| `test_deferred_regrade` | delete | `test_deferred_regrade_validates_repaired_trace_against_learner_answer`: a joint regrade's repair suggestion validated against the answer (a blind grade carries none) |
| `test_diagnosis_async_router` | blind | `test_no_wait_and_no_receipt_without_a_pending_diagnosis`: a right answer, whose blind grade queues no diagnosis |
| `test_diagnosis_card` | builder | `test_joint_vault_feedback_carries_no_diagnosis_status` (now `test_a_jointly_graded_attempts_feedback_carries_no_diagnosis_status`): the feedback of a stored joint attempt; the submit response of a new joint answer and the worker's not starting go |
| `test_diagnosis_input_provenance_landing` | delete | `test_q14_on_a_vault_the_coordinator_upgrades_the_receipt_commits_with_the_grade`: the joint door's in-transaction Phase-C receipt on a coordinator-upgraded vault, and its rollback (the blind door writes its receipt as telemetry, so the subject has no blind form) |
| `test_diagnosis_pipeline` | delete 3 + tail, builder 1 | delete `test_kill_switch_restores_joint_grading` (new answers graded jointly), `test_kill_switch_holds_queued_live_diagnoses` (the worker's hold and release), `test_shadow_diagnosis_on_a_joint_vault_changes_nothing_live` (`diagnosis.shadow`), and the joint tail of `test_non_practice_graders_use_the_blind_contract_in_an_isolated_turn` (the vault door's joint branch); builder: `test_a_joint_attempt_regraded_in_a_split_vault_is_graded_blind_and_isolated` |
| `test_diagnostic_augmentation` | delete | `test_a_receipt_that_cannot_be_written_commits_no_augmented_grade`: the joint door's transaction |
| `test_exam_session` | delete a case | `test_an_exam_answer_is_stamped_with_its_graders_calibration_identity[mvp-0.9]`: a new exam answer graded jointly |
| `test_km4_taxonomy` | blind | `test_taxonomy_regrade_check_no_attribution_regressions`: its canned grader also answers the blind contract (`JointGraderAlsoBlind`); the mechanisms compared are the same |
| `test_learner_text_gaps_review` | blind | `test_f8_a_stuck_answer_is_queued_at_recording_without_a_diagnosis`, and `_created_and_checked` (three f11/f13 tests): self-graded attempts, the switch incidental |
| `test_pfc_unverified_unassessed` | builder | `test_joint_grades_replay_untouched_beside_blind_unverified_ones` |
| `test_placement_diagnosis_decides` | builder 1, stamp builder 2, delete a case + 1, changed 1, new 1 | builder: `test_a_joint_grade_falls_back_to_todays_rule`; stamp: `test_turning_the_split_back_on_does_not_reopen_held_misses` (now `test_a_held_miss_stays_decided_at_its_hold`), `test_a_miss_decided_before_the_hold_keeps_its_diagnosis`; delete: the `split-disabled` case of `test_no_diagnosis_can_arrive_falls_back_to_todays_rule` (an unstamped queued job read with the switch off) and `test_the_first_serving_build_with_the_split_off_records_the_hold` (the scheduler's stamp writer); changed: `test_the_state_loader_requires_the_split_reading_and_the_time` (§30); new: `test_stored_misses_read_as_with_the_split_on` |
| `test_reader_guidance` | builder 1, delete 1 | builder: `test_joint_guide_plan_is_unchanged_by_the_overlay_read` (its shadow assertion goes); delete `test_joint_guide_plan_never_waits_on_a_shadow_diagnosis` (`diagnosis.shadow`'s queued job) |
| `test_regrade_contract_successor` (+ `regrade_contract_successor_helpers.JOINT`) | joint-regrade builder | `test_an_unrecorded_joint_regrade_keeps_the_correctness_it_carries_and_never_fails_a_rebuild`, `test_a_held_unrecorded_grade_is_no_evidence` (its control vault's switch was incidental) |
| `test_route_rules_in_grader` | delete | `test_f5_a_joint_regrade_supersedes_a_route_verdict`: a new joint regrade's verdict write (its docstring: "no shipped door reaches this today") |
| `test_stuck_prompt` | delete 2 + a case, keep a half | delete the `joint` case of `test_confusion_is_read_and_signalled_in_both_grading_modes` (now `test_confusion_is_read_and_signalled`), `test_a_joint_regrade_rereads_the_stuck_answer_and_supersedes`, and the joint-answer half of `test_an_ordinary_joint_answer_keeps_its_prompt_and_hash_exactly`; its context half stays as `test_an_ordinary_grading_context_carries_no_stuck_field` (`grading_prompt` and `grading_context_hash` stay, for the offline review's joint baseline and the builder) |
| `test_stuck_prompt_replay` | builder | `test_a_joint_stuck_reading_survives_rebuild_with_no_model_call` |
| `test_teach_back` | vault-door builder | `test_a_teach_back_grade_is_calibrated_and_replayed_under_its_graders_identity[mvp-0.9-identity1]`, `test_a_teach_back_regraded_blind_keeps_the_blind_identity_through_rebuilds` |
| `test_teacher_te2_landing_r1` | vault-door builder | `test_a_lesson_probe_regraded_blind_after_split_is_switched_on_carries_the_blind_calibration` (now `…_graded_jointly_then_regraded_blind_…`) |
| `test_ux_phase4_feedback` | joint-regrade builder | `test_f9f_a_question_changed_after_its_regrade_is_labelled_never_scored_out_of_the_later_maximum[joint]` |
| `test_voi_stopping` | builder | `test_a_joint_vault_lane_is_unchanged` (now `test_a_joint_attempts_lane_is_unchanged`; its shadow drain goes) |
| `test_followup_codex_review` | delete | `test_f6_a_shadow_vault_has_its_workflows_job_at_once`: with `diagnosis.shadow` on, the workflow's job queues at once (it patched `post_attempt._shadow_diagnosis_enabled`, which is gone) |
| `test_field_split_outcomes` | builder (a bug, D7-8) | `test_blind_grades_diagnoses_and_regrades_keep_the_epoch_contract`: its "joint" vault was blind since D2a |
| `test_sim_teach_back`, `test_reading_step_switch`, `test_teacher_te2_review_fixes` | assertion | each asserted `split_grading_active(...)`; the predicate is gone |
| `test_kill_switches`, `test_retired_config_identities`, the effective-defaults golden | config | the two kept-because lines; nothing (`SWITCHES_TOML` and `_pre_arc_c_shape` already carried both); two lines |
| `diagnostic_augmentation_helpers`, `test_attempt_completion`, `test_tui_feedback` | helper | `fail_after_the_joint_grade_commits` patched `_complete_joint_graded_attempt` and `_complete_blind_graded_attempt`; it is `fail_after_the_model_grade_commits`, the blind door's only |

`tests/successor_switches.py` names neither switch (its table holds only router-objective successors), so neither it nor its test changes.

## 29. The builders, and their proof

`tests/joint_grading_helpers.py` (commits `131489e468`, `a718d77679`) writes joint history as stored data, with no model call:
- `write_joint_graded_attempt(vault, repository, draft, proposal, ...)`: the practice door's joint arm. The draft resolved as submit would (`validate_attempt_draft`), the joint context (the item or its frozen contract, the stuck prompt for a stuck answer, the C2 verifier observations, the C4 history: a copy of `diagnostic_history_context`'s selection, which left production with the joint arm), the grading run with the joint identity, then in one transaction the attempt (`complete_codex_graded_attempt`), a stuck answer's reading, the Phase-C receipt (k = 1, no grader mode) and the `joint_grader` grading record, then the run completed. `proposal` is a `GradingProposal`, a `StuckGradingProposal`, or a function of the joint context (`joint_proposal_of(client)` gives a `ReviewFakeClient`-style fake's joint grade; `write_joint_answer` is `split_live_helpers.submit` for a joint grade).
- `write_joint_regrade(vault, repository, attempt_id, proposal, ...)`: `regrade_attempt`'s joint arm for a practice attempt with no blind record (it calls the regrade's own `_publish_regrade` with no blind record and the joint identity `None`, then the route verdict `not_checked` and a stuck reading).
- `joint_vault_door(monkeypatch)`: inside it, the shared vault door's three functions are their joint bodies (`request_grading_proposal`, the joint run identity, the identity `None`), patched in every module that took them by name, so teach-back, exams, teacher checks and probes write what they wrote with the split off.
- `hold_queued_live_diagnoses(repository, clock=)`: the kill switch's write-once `split_held_at` stamp, the same SQL as the deleted repository method.

**Proof, at the base with the switch present** (`tests/test_joint_grading_builder.py` at `131489e468` and `a718d77679`): the same history written twice in vaults built alike, once through the door and once through the builder, every table compared row by row in insertion order (rowid), with ULIDs, UUIDs, ISO stamps and hex digests replaced by tokens in order of first appearance (so equal rows name the same ids in the same places):
- practice door and regrade: four answers (two wrong, one stuck with a reading, one right) graded through `complete_attempt_with_ai_required` with the split off and the sync pipeline after each, then a self-graded answer, the first joint answer and the stuck one regraded through `regrade_attempt`; against the builders: **every table equal** (the four receipts, the stuck readings, three regrade runs, every derived row the pipeline and the regrades' replays wrote);
- the vault door: a teach-back finished and regraded on a vault with the split off, against the same on a split vault inside `joint_vault_door`: **every table equal**; without the patch the split vault grades blind (the negative control: the fake has no blind answer and the run fails);
- the hold: two queued live diagnoses stamped by `Repository.hold_queued_live_diagnoses` and by the builder, twice (write-once: 2 rows, then 0): **every table equal**.
These comparisons are deleted with the doors in the removal commit (`4d59c0a826`). What stays is `test_the_builders_rows_match_their_golden`: the practice and regrade builders' grading-record rows (`agent_runs`, `practice_attempts`, `grading_evidence`, `raw_grade_events`, `attempt_feedback_metadata`, `diagnostic_augmentation_receipts`, `judgment_ledger`, `text_write_provenance`, `content_events`; tokenized as above) against `tests/goldens/joint_grading_builder.json`, recorded at the builder commit with the split off and unchanged after the removal on a split vault (the switch's absence changes nothing the builders write). Not covered by the comparison: a joint regrade reading a frozen assessment contract (`reads_contract`), and the vault door's other users (exams, teacher checks and probes; the teacher probe test asserts the joint identity the switch-off path stamped).

## 30. What went, and every assertion changed

| commit | what |
|---|---|
| `131489e468` | the builders of joint grades, joint regrades and the vault door's joint grading, with the two door comparisons and the golden (§29) |
| `a718d77679` | the hold builder with its comparison; `joint_proposal_of`, `write_joint_answer` |
| `d680c601dd` | the ports (§28), and `test_stored_misses_read_as_with_the_split_on` with its golden `tests/goldens/placement_stored_misses.json`, all passing with the switch present (1,353 tests in the 44 touched and nearby files) |
| `4d59c0a826` | the removal (§28's table), `RETIRED_FIELDS`, the kill-switch rows and kept-because lines, the effective-defaults golden, the tag's comment, the deleted tests, the builder comparisons deleted |
| `0297e17ba3` | `serve_presentation` loses its unread `vault` keyword, and the probe-validation sim stops passing it (part 3's open item) |
| `5c5df7e0db` | the structure golden lowered (comments naming a stage artifact 2,377 to 2,374) |
| `0b4ef8c198` | the vault's references regenerated |

**Fields:** `RetiredField("DiagnosisConfig", ("split_enabled",), bool, True, "D7")` and `("shadow",), bool, False`; `DiagnosisConfig` now keeps retired fields. No registry rule named either (`params/parameter_registry.py`), and the vault generator described them generically. No desktop or phone code reads either (searched `apps/`).

**Deletion proof** (strategy §2.1): `split_grading_active`, `diagnosis_can_arrive`, `diagnosis_live`, `hold_queued_live_diagnoses`, `SPLIT_OFF_RECHECK_SECONDS`, `_complete_joint_graded_attempt`, `_augmented_grading_context`, `_joint_sample_count`, `_run_augmented_diagnosis`, `_record_diagnostic_augmentation`, `joint_grading_prompt_tokens`, `augment_grading_context`, `diagnostic_history_context`, `record_phase_c_receipt`, `DEFAULT_HISTORY_LIMIT`, `_shadow_diagnosis_enabled` searched over `src/`, `scripts/`, `tests/`, `apps/` and the vault's `_scripts/` as names and strings: no function-local or `importlib` import, no registry, Typer or `MODULE_INVENTORY` entry left; the tests that named them are in §28. `run_diagnosis_samples`, `request_grading_proposal`, `grading_prompt`, `grading_context_hash`, `joint_grade_record`, the Phase-C constants and `FALLBACK_SPLIT_DISABLED` stay (the planted-eval harness, the offline review's joint baseline, the blind receipt, stored joint history, stored holds).

**Every assertion changed, and why:**

| test | before | after | why |
|---|---|---|---|
| `test_diagnosis_pipeline::test_a_joint_attempt_regraded_…` | `client.calls == ["grading", "blind_grading"]`, `isolated == [False, True]` | `["blind_grading"]`, `[True]` | the joint grade is the builder's, not the client's; the regrade's call is unchanged |
| `test_active_errors_overlay::…_on_joint_history`, `test_reader_guidance::test_joint_guide_plan_is_unchanged_…`, `test_voi_stopping::test_a_joint_attempts_lane_is_unchanged` | a shadow diagnosis drained (and, in the Guide test, asserted present) | no shadow diagnosis | `diagnosis.shadow` is gone; the overlay, plan and lane assertions stand |
| `test_diagnosis_card::test_a_jointly_graded_attempts_feedback_…` | the submit response and `get_feedback` carry no `diagnosisStatus`; the worker does not start | `get_feedback` carries none | a new joint answer and its submit response are gone; the feedback of stored joint history is the subject |
| `test_placement_diagnosis_decides::test_a_held_miss_stays_decided_at_its_hold` | the worker's release wrote `last_error = split_disabled`; the outcome read with the switch off, then on | the stamp is built; the outcome read once | the writers are gone; every read of the stamp (held, decided at the stamp, not reopened by a later release or a landed slip) stands |
| `test_placement_diagnosis_decides::test_the_state_loader_requires_the_time` | `TypeError` without `diagnosis_live`, and without `now_iso` | `TypeError` without `now_iso` | the parameter is gone |
| `test_exam_session::test_an_exam_answer_is_stamped_…` | parametrized over a joint and a blind vault | the blind case | the joint case graded a new answer jointly |
| `test_stuck_prompt::test_confusion_is_read_and_signalled` | parametrized over both modes | the blind case | twin |
| `test_stuck_prompt::test_an_ordinary_grading_context_carries_no_stuck_field` | also graded a joint answer and checked its prompt | the context, prompt and hash only | the joint answer is gone |
| `test_teach_back`, `test_teacher_te2_landing_r1` (joint cases) | the vault set `split_enabled = false`, then back on | the grading inside `joint_vault_door`; vaults at `mvp-0.10` | stored history, built; every identity, lookup and rebuild assertion stands |
| `test_regrade_contract_successor` (two tests) | the predecessor's regrade with the split off; the control vault also off | `write_joint_regrade`; the control vault at the default | stored history; the control's switch never mattered (it applies a held grade and rebuilds) |
| `test_ux_phase4_feedback::test_f9f_…[joint]` | the sidecar's regrade with the split off | `write_joint_regrade` with `_SixPointGrader`'s joint grade | stored history; the bundle assertions stand |
| `test_field_split_outcomes::test_blind_grades_…` | a second blind vault named "joint" | a jointly graded attempt, asserted to have no blind record | D7-8 |
| `test_sim_teach_back`, `test_reading_step_switch`, `test_teacher_te2_review_fixes` | `split_grading_active(...)` | removed | the predicate is gone |
| `test_km4_taxonomy`, `test_learner_text_gaps_review`, `test_diagnosis_async_router` | the split off | blind (the grader fake answers both contracts; self-grades; a right answer) | the joint rows were incidental |
| `test_diagnosis_pipeline::test_no_door_calls_the_joint_grading_operation` (was `test_only_the_joint_doors_…`) | `grading.py` "and the vault door's joint branch"; `diagnostic_augmentation.py` "joint practice grading" | the definition; `run_diagnosis_samples` (the planted-eval harness) | comments of an unchanged set |

Edits made by a script rather than the Edit tool: most source and test edits were exact-pattern replacements in Python one-offs that assert each pattern occurs exactly once (or a block cut between two unique markers); the seven call sites of the two vault-door identities and the eleven `diagnosis_live=diagnosis_can_arrive(...)` arguments by a mechanical replace (one replace clipped two function-local import lines' indentation, fixed before the commit); `ruff check --fix --select F401` removed the imports deleted tests left unused.

## 31. Proof

**The retired-config identities, with each entry removed.** `RETIRED_FIELDS` without the `split_enabled` line, then without the `shadow` line (mutations, not committed): `test_retired_config_identities.py` fails four tests each time (`test_the_config_identity_reproduces_both_recorded_digests`, `test_an_embedding_compare_report_is_named_as_before_arc_c`, both cases of `test_a_config_setting_the_removed_switches_keeps_every_identity`; the `switched` case fails too here, because `DiagnosisConfig` survives and only the retired field puts the value back). Restored: 16 passed. `SWITCHES_TOML` already set `split_enabled = false` and `shadow = true`, and `_pre_arc_c_shape` already carried both, so the test needed no line; `test_a_vault_that_still_sets_a_removed_switch_loads_and_the_switch_reads_nothing` loads a vault that sets both.

**P-shadow** (base `1d122fee33` from a `git archive` of `src/` and `migrations/` on `PYTHONPATH`, against this branch at `0297e17ba3`; fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp058`; counts only; copies deleted):

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| `learnloop upgrade`, both | `mvp-0.58 -> mvp-0.59` | same | same |
| shadow facet / mastery / schedule changed | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| `schedule_effects` due dates moved (items, cards) | 0, 0 (99 rows) | 0, 0 (77) | 0, 0 (32) |
| the two shadow reports, marker id, `as_of` and hashes aside | equal | equal | equal |
| every table of the two upgraded copies, row by row | 402 tables, 19,442 rows: none differ | 402, 10,426: none | 402, 23,877: none |
| the same after the shadow | none differ | none | none |
| the same after a real `rebuild-derived-state` on each side | 19,749 rows: none differ | 10,498: none | 23,719: none |
| feedback bundles of the first three jointly graded attempts (no regrade) | `01KY50X5FB4AP8466KH344TWKN`, `01KY513P8Q4369EQ66530N9AC9`, `01KY51X1SSHB6AN7Y8CDA452NJ`: byte-equal | `01KZ53Q6EXP6JQ8ZC7KTWEXWXD`, `01KZ54VPYRZX2Q661XAKX2Z4YN` (its only two): byte-equal | none graded jointly |
| Report 3, placement state, `m2_report` (JSON and Markdown), `doctor --json`, on the rebuilt copies | equal, but for the `m2_report` manifest line that drops `split enabled True, ` (and the manifest's `split_enabled` key and its `config_hash`, a provenance hash over the live model dump, which the two removed fields change); doctor equal with the copies' directory names aside | same | same |
| grading history (after the rebuild, both sides alike) | 70 attempts; 29 AI-graded, all jointly; 11 joint receipts; no diagnose job; no hold stamp | 3; 3 AI-graded, 2 jointly, 1 blind; 2 joint and 1 blind receipt; 1 diagnose job `live:done`; no stamp | 3; none AI-graded |

**Stored rows read as with the split on.** `test_placement_diagnosis_decides::test_stored_misses_read_as_with_the_split_on` builds a blind miss whose diagnosis landed (a slip: passed, maintenance), a blind miss whose live diagnosis is queued and not held (open, awaiting it, assumed) and a jointly graded miss with no blind record (failed, `no_diagnosis`, `not_blind_graded`, learning), and reads placement's state, Report 3 and `placement status --json` against a golden recorded at the ports commit with the switch present and on; it passes unchanged after the removal. With `split_enabled = false` appended at the ports commit it fails (the queued miss reads `split_disabled`), so it measures the switch.

**Old rows at the floor and the head** (`fixtures/mvp017_route_check_replay`, retagged to `mvp-0.58` and `mvp-0.59`, two live rebuilds per code): every table equal row by row after each rebuild at both tags except the one `attempt_debug_payloads` row of `att_02_svd_fail`, equal once replay's minted ids, stamps and digests are normalized (the diagnosis receipt's id hashed from the minted hypothesis id), as in parts 1 to 3.

**Goldens.** The effective-defaults golden lost exactly two lines (`diagnosis.shadow = false`, `diagnosis.split_enabled = true`) and gained none. The CLI snapshot did not change (no CLI parameter names either switch; `learnloop attempt --dry-run` keeps its contract and only ever plans `blind` now). The grade-application, due-queue and figure goldens ran unchanged in the sweep (§32). `tests/test_identity_pins.py`: unmoved, nothing written; no pin names a joint identity (the grading door's identities were pinned at their split-on values, which they keep).

**The owner lane** (`-m owner_vaults`, 31 files, copies made with the gate's `owner_copy_make.py` under `fixtures-local/owner-lane-d7d`, deleted after): 92 passed, 8 skipped, as at part 3. No owner-lane test was edited.

## 32. Gates run

All under the empty-home wrapper in 5 GB scopes.
- The builder commits: `tests/test_joint_grading_builder.py` (the comparisons and the golden) with `test_identity_pins` and `test_test_layout`. The ports commit: the 44 test files it and the removal touch or that name the grading doors, placement's readers, the dry run or the reports, with the identity, retired-config, architecture, layout, effective-defaults, CLI-snapshot, structure, kill-switch and successor-switch tests, at the ports commit and again on the removal: 1,353 passed, 2 xfailed. The `serve_presentation` commit: the 16 files that name it or the probe-validation sim (284 passed, 2 skipped).
- **The sweep:** `scripts/affected_tests.py --base 1d122fee33` selects 1,353 test files (with the standard files, 1,354); all ran in 14 chunks of 100 at `-n 4 -m "not arc_close"` behind `flock /tmp/learnloop-fullsuite.lock`, on `0b4ef8c198`: **29,015 passed, 101 skipped, 12 xfailed, no failure or error**, first time through. The grade-application, due-queue and figure goldens ran in it unchanged.
- `ruff check`: clean. `lint-imports --no-cache`: 42 kept, 0 broken. `scripts/check_gate_partition.py`: 30,970 collected, landing 30,905 + arc_close 65. `tests/test_structure_ratchets.py`: golden lowered (`5c5df7e0db`).
- Vault: references regenerated once after the source commits (`0b4ef8c198`; the two hand-written leaf counts 1,173 to 1,171); a second `generate_all.py` changed nothing. Validators: `db_validate_reference`, `desktop_validate`, `module_validate`, `validate_vault` all pass.
- The owner lane: §31.
- Not run (the orchestrator's): the durability lane, `--fresh-connections`, the arc-close lane, vitest, `cargo check` (no frontend file changed).

## 33. The census and the measures

**The census** (parts 1 to 3's scratch plugin around `version_floor.may_open_below_floor`), over the 31 test files this part edited, base code and tests (a `git archive` of `1d122fee33`) against this branch: **357 test cases opened a vault below the floor at the base, 347 now (-10)**, in 20 files then and 17 now. The 2 cases the branch has and the base lacks are the same tests renamed or unparametrized (§28). The cases gone are the deleted tests and the ports that no longer pin `mvp-0.9` for a joint vault (`test_active_errors_overlay`, `test_diagnosis_card`, `test_diagnosis_async_router`, `test_reader_guidance`, `test_voi_stopping`'s), and one `test_sim_teach_back` case whose module fixture the plugin attributes to whichever test first uses it. The 347 left (`test_pfc_unverified_unassessed` 189, `test_regrade_contract_successor` 36, `test_learner_text_gaps_review` 29, `test_voi_stopping` 28, `test_route_rules_in_grader` 21, `test_ux_phase4_feedback` 10, seven others 34) are tests whose vaults sit at an old tag for their own setup (the pre-D2a basic vault, `mvp-0.20`, `mvp-0.25`, the regrade-contract predecessor): they wait on the re-tagging step, not on a switch. (The base run had one unrelated failure, `test_ux_phase4_feedback::test_f1g_the_screen_and_the_ledger_share_one_exposure_contract`, because the base extract carries no `apps/`.)

**Measures** (`scripts/refactor_measures.py`, base `1d122fee33` from a `git archive` committed to a scratch repository, against this branch):

| measure | base | this part |
|---|---|---|
| ADR-019's kept-because list | 84 | 82 |
| tagged switches in `TAGGED_SWITCHES` | 86 | 84 |
| `mvp-0.N` literals: code / docstring / comment | 270 / 315 / 580 | 268 / 311 / 577 |
| `config/schema.py` lines | 4,974 | 4,970 |
| raw lines; code lines (all four packages) | 614,757; 432,362 | 614,219; 431,970 |
| functions over 100 lines; over 200 | 475; 73 | 474; 73 |
| `src/` lines (diff) | | +196, -734 |
| test lines (diff, goldens aside) | | +947, -621 (the builders and their test 470 of the added) |
| goldens (diff) | | +1,851, -5 (the builder golden and the stored-misses golden) |
| comments naming a stage artifact | 2,377 | 2,374 |
| effective config leaves | 1,181 | 1,179 (the measures count; the vault's catalog counts 1,171) |

## 34. Bug ledger

- **D7-1:** the split pair was not read by replay (§31's real rebuilds are equal); what is left is `replay.ledger_bounded` and `mastery.claim_fixes_enabled`.
- **D7-3:** the split's two predicates read a missing field as on, the schema default (not this row's kind); both went.
- **D7-5:** nothing of it belonged to the split pair.
- **D7-8 (new, fixed):** a test's "joint" vault was blind since D2a (§30).
- **D7-9 (new, open):** `diagnostic_augmentation.history_limit` is read by nothing now.

## 35. What remains, and judgment calls

**Not removed here:** `replay.ledger_bounded` and `mastery.claim_fixes_enabled` (the batch's replay-read pair, each alone, not started); `diagnostic_augmentation.history_limit` (D7-9).

**Judgment calls:**
1. **The builders call production's writers, not copies of them**, except the C4 history selection (copied, because its only production caller went with the joint arm). The regrade builder calls `regrade._publish_regrade` and `_disagreement_summary` (private names of the module that still owns every regrade write), so a joint regrade written today goes through the same publication a blind one does; the golden would move with any change to them, as a real regrade's rows would.
2. **The vault-door builder is a patch** (`joint_vault_door`): the shared door's three functions replaced by their joint bodies in the modules that took them by name, proven equal to the switch-off path on a teach-back finish and regrade; its other users (exams, teacher checks and probes) are covered by construction, not by a comparison.
3. **The hold builder exists** because placement still reads stored `split_held_at` stamps; no owner copy holds one (§31), so the reader is kept for history any vault could carry, with two tests on built stamps.
4. **The vault door's identities lose their `vault` parameter** (`vault_grading_run_identity(context)`, `vault_grading_calibration_identity()`), rather than keeping one nothing reads; seven call sites changed, none in a file a parallel step edits.
5. **`lanes.classify_item`'s recency arm stays.** The plan always passes a reading of open problems now, so production never takes it; `classify_item` and `classify_pool` keep their `None` default (a test calls `classify_item` without one, `test_daily_plan_review_regressions::test_f1_repair_needs_a_recent_error_not_any_active_one`) and the why-copy for "a recent error" stays with it. Removing it is a lanes change for a later step.
6. **Two tests went rather than moving to blind:** `test_deferred_regrade_validates_repaired_trace_…` (a blind grade carries no repair suggestion, so its subject has no blind form) and `test_q14_…` (the blind receipt is telemetry outside the grade's transaction, so the rollback it tested has no blind form). Part 3's reading had listed both as "move to blind".
7. **`test_stuck_prompt`'s context half stays** as its own test: `grading_prompt` and `grading_context_hash` stay for the offline review's joint baseline and the builder.
8. **`test_field_split_outcomes` was fixed, not left** (D7-8): its subject is the joint/blind comparison the builder can now make honestly.
9. **`m2_report`'s `config_hash` changes** (a provenance hash over the live model dump, which loses the two fields), as it did with every earlier removal; nothing compares it.
10. **The optional `serve_presentation` commit was made** (part 3's open item), as its own commit.

## 36. Docs

- ADR-019: the kept-because list went to 82 with this part, and how joint history is read and built. ADR-016: the switch was the kill switch; D7 removed it with the joint doors and `diagnosis.shadow`; a regrade of a joint attempt grades it blind.
- `Concepts/Algorithm Versions and Reproducibility` (mvp-0.10's row) and `Maps/LearnLoop Pipeline Map` (the provenance writers) follow. `Concepts/Attempt Processing` and `Concepts/Learning System` name neither switch and are unchanged.
- Ledger rows D7-1, D7-3, D7-5 updated; D7-8 and D7-9 added.
