# Reader RW5d P4b (teacher visuals): Codex review and fixes

Branch `reader/rw5d-p4b-teacher-visuals` (worktree `learnanything-merge2`), reviewed at `8f9051f3ff` by Codex
(gpt-6.1-sol, job `20261102-053740-4wL5iD`; static tracing only). Fix step 2026-11-02. Each finding was reproduced
first by a failing regression test in `tests/test_reader_rw5d_p4b_teacher_visuals.py` (all seven new tests failed
before the fix, for the reason the finding gives), then fixed. No live calls; every model a fake.

## Review

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Recovering a visual can resend protected exam material | fixed | `75242bded0` | `test_review_f1_a_recovered_visual_is_never_built_after_protection_changed` (the saved goal carries `ext_lay/lay_char` words, the anchor is another passage; `lay_char` held out before resume: before the fix the author got the goal, now 0 author calls, 0 `figure_requests`, no teacher call, lesson ends `protection_changed`); `test_review_f1_a_visual_after_protection_changed_mid_action_is_not_built` (protection changes between the accepted turn and its build in one action) |
| F2 | Medium | Hidden predictions are recorded as learner exposure | fixed | `75242bded0` | `test_review_f2_a_suppressed_prediction_is_never_counted_as_shown` (a hidden prediction prompt reproducing `pi_eig_1`'s question is no longer in `shown_text` nor the receipt's `shown_items`, the visible words still are; a hidden prediction carrying the open check's solution no longer withholds an otherwise safe figure) |
| F3 | Medium | The new doctrine shares the old forecaster's learned calibration | fixed | `75242bded0` | `test_review_f3_a_visuals_lesson_forecasts_under_its_own_family` (a visuals-off and a visuals-on lesson on one vault: forecasts, receipts' `forecaster_version` and the checks' pool family differ; one cold outcome updates each family's posterior apart; the replay reproduces both and the written `lesson_weight_state` rows) |
| F4 | Medium | A budget refusal during visual recovery leaves the lesson stuck | fixed | `75242bded0` | `test_review_f4_a_budget_refusal_while_recovering_a_visual_closes_the_lesson[answer_prediction, stop, resume]` (before the fix the refusal escaped `take_turn` on every action; now the lesson closes `budget` with its receipt, returns its view, and a later action recovers and calls nothing) |
| (gate) | - | `teacher.visuals` reached the notes' code (found by the targeted gate, not by Codex) | fixed | `6f75f46c9a` | `tests/test_notes_never_read.py::test_no_generation_grading_evidence_or_ad_module_reaches_the_notes_modules` failed on the stage's tip: `visuals.figure_request` imported `teacher.actions.caller_for` (which reaches `teacher.notes`). The service (an allowed note reader) now passes the caller in; the module imports no read action |

### What changed

- **F1** (`teacher/service.py`, `teacher/visuals.py`). `take_turn` checks `protection_changed` *before* recovery. If
  changed, recovery runs only what makes no model call (`reads=False`, no figure builder) and the lesson ends
  `protection_changed`. Otherwise recovery runs as before and the check is repeated after it when it ran
  something. `_visual` checks protection before every build too, in recovery and in `_teach_loop`. If it has
  changed, nothing is sent: the visual is recorded `withheld` with code `protection_changed`
  (`V.not_built_for_protection`) and the action ends the lesson `protection_changed` after the turn
  (`_Outcome.protection_changed`). The figure service's anchor-only check stays as a second line.
- **F2** (`teacher/visuals.py`). `figure_text` drops the stored spec's or program's `predictions` before P3's
  `reveal_text`. The guards, the `shown_text` record, the reveal rows and the delayed checks' displayed text now
  read only what the lesson shows. The figure's own `reveal_text`, used by attempt hosts, is unchanged.
- **F3** (`teacher/service.py`). `_family_of(model, visuals=)`: a forecast made by a turn written under the
  visuals paragraph (its stored payload's `visuals`) carries family `teacher_doctrine_v1+teacher_visuals_v1:<model>`.
  With visuals off it is TE1's `teacher_doctrine_v1:<model>` exactly. `lesson_weight` keys pools by the receipt's
  `inputs.family`, so live mixing and replay both separate the two policies. This adds no new parameter: the new
  family starts from the same seeded, labelled prior as any family.
- **F4** (`teacher/service.py`). Recovery inside `take_turn`'s envelope is wrapped like `_teach`. A refusal by the
  lesson's spend envelope (`_refused_by_budget`) closes the lesson `budget` in `_close`'s single transaction and
  returns its view, before the requested action. A non-budget error still propagates.
- Spec as-built notes updated: `spec_reader_show_me_figures_v1.md` §10.4 and `spec_teacher_v1.md` §8.2.

### Open items (not fixed here)

- `V._budget_refused`, like TE1's `_refused_by_budget`, treats any `SpendLimitExceeded` in the cause chain as the
  lesson's envelope. When the figures' *own daily* envelope refuses the author, the figure service raises
  `FigureRefused("capped")` from a `SpendLimitExceeded`. That would close the lesson `budget` instead of
  recording the figure `unavailable`. Narrowing it to the lesson gate's `refusal` is a small follow-up. It was not
  a finding, so it is left for the orchestrator to rule on.
- Owner checkpoints (unchanged): a real lesson with visuals and a real figure on a `fixtures-local` copy.

## Gate (fix step; no full suite, per the owner's 2026-10-17 rule)

- `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **42 kept, 0 broken**.
- Targeted pytest, `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6 ...`:
  **569 passed, 1 skipped** (`test_hint_service.py:302`: the test vault's active provider is not Codex). Files:
  - `tests/test_reader_rw5d_p4b_teacher_visuals.py` (22 tests, 7 new)
  - `tests/test_teacher_te1_lesson.py`, `tests/test_teacher_te1_review_fixes.py`, `tests/test_teacher_te1_successor.py`,
    `tests/test_teacher_te1_weight.py`, `tests/test_teacher_te1_curriculum_c4.py`, `tests/test_teacher_te1_migration.py`
  - `tests/test_teacher_te0_confidence_events.py`, `tests/test_teacher_te0_fix_round2.py`, `tests/test_teacher_te0_review_fixes.py`
  - `tests/test_figures_switch_off.py`, `tests/test_figures_help.py`, `tests/test_hint_service.py`, `tests/test_notes_never_read.py`
  - contracts: `tests/test_architecture.py`, `tests/test_rebuild_orchestrator.py`, `tests/test_desktop_rpc_contract.py`,
    `tests/test_mobile_allowlist.py`, `tests/test_sidecar_serializer_snapshot.py`, `tests/test_cli_help_snapshot.py`,
    `tests/test_table_roles.py`
- Not applicable: no migration, schema, DB or connection change (no durability run, no DB reference scripts); no
  frontend or `src-tauri` change (no npm, vitest or cargo); no config key added (the defaults snapshot and
  parameter registry are untouched).
