# Learner marks on hypotheses, FG1c (`followup/fg1c-marks`, base `90f7def5e3`)

Built from `docs/specs/spec_followup_generate_serve_v1.md` §7 and row 6 of `docs/specs/spec_router_objective_v1.md` §4, on the FG1 that
landed. Migration 242 (recheck the number at landing: RO0 runs beside this and takes the next one too). No successor, so no tag claimed.

## What exists now

| Item | Where |
|---|---|
| (1) Exposure receipt | `hypothesis_list_exposures`, `hypothesis_exposure_probe_links` (RECEIPT); RPC `record_hypothesis_exposure`; `followup_run/marks.py::record_exposure`; the link is written in `followup_serve/workflow.py::probe_answered` |
| (2) Raw marks ledger | `hypothesis_marks` (RAW_LEDGER); RPC `record_hypothesis_mark`; `followup_run/marks.py::record_mark`; store `db/stores/hypothesis_marks.py` |
| (3) Display order | `followup_serve/marks.py::display_order`, `hypothesis_order_v1`, seed on every panel exposure and every mark |
| (4) Desktop | `screens/feedback/HypothesisMarks.tsx`, mounted by `FeedbackScreen`; `DiagnosisCard`'s `hideTaps`; bundle key `hypothesisMarks`, added by `handlers/feedback.py::_with_hypothesis_marks` |
| (5) Attributed opinion | `daily_plan/router_card.py::_hypothesis_marks` and `router/card.py` (`MARKS_SECTION`, version suffix `+marks`); `diagnosis/split/history.py`, `context.py`, `live.py`, `snapshot.py` (`learner_marks`) |
| (6) Report | `ops/capture_report.py::hypothesis_marks_section`; `router/outcomes.py::next_delayed_outcomes` |
| (7) Kill switch | `followup.hypothesis_marks`, default true, at every version; `followup_serve/gates.py::hypothesis_marks_on`; a `structural` rule in the parameter registry |

**Import contract.** `graders-never-read-hypothesis-marks` (43 contracts now): `learnloop.attempts` imports neither the marks module nor their
store. `post_attempt` passes the switch's value to `probe_answered` so the link needs neither.

## The playbook: no successor

Item 1 asks whether the change alters persisted meaning. It doesn't:

- No score, schedule, projection or admissibility reads the three tables, and `test_marks_change_no_row_outside_their_own_ledger` compares every
  other table's every row through every kind of mark. `test_a_rebuild_ignores_marks_and_keeps_them` compares every DERIVED table with and without a mark.
- The card and the diagnoser's context are empty until a mark exists, so an unmarked vault's are byte-identical. TE0's confidence events are the
  precedent for context with no successor. A stored card says which model input it was through `+marks`, and the diagnoser's context hash is on its receipt.
- Hiding the card's tap on the probe lane changes what the screen asks at a tag that already has the lane. The RPC behind the tap is unchanged, and
  old records keep their meaning.

Items 5, 6 and 8 still apply and are done: roles classified, neither ledger cleared by replay, head fixture at 242. Item 4: `[followup] hypothesis_marks` is a
new default, so all 36 fingerprints in `DEFAULTS_SNAPSHOT_BY_ALGORITHM` were recomputed, as FG1 and data capture did for keys inert below their tags. A
fingerprint is checked by tests and isn't stored in a vault, so no vault notices.

## Where the build departs from the words, and why

1. **The panel isn't inside `FollowupPanel`.** The stage text says "marks in FollowupPanel and the feedback screen". `FollowupPanel` sits above the verdict, so
   the causes would come before what they're about, on every miss at the tag. The panel sits under the feedback surface, on the miss's own screen and on
   the probe answer's, and `FollowupPanel`'s held line is still what says why the causes are hidden. Smallest alternative: mount it from `FollowupPanel`,
   one line each in two files.
2. **`cleared` is a fifth ledger value.** "All optional" needs a way back from a slip, and the spec's three marks can only be swapped. Tapping a mark again appends
   `cleared`; the latest still counts, and the report skips it.
3. **On the probe lane only the card's tap goes, plus `why?`'s "this doesn't sound right" when it would write that tap.** §7 says the self-report stays, and
   it's the only place for *the item was unclear* and *the notation confused me*. It sits under *details*. If the owner reads "asked twice" more strictly, the
   unresolved-cause card's question can go on that lane too, with `replacesCardTap` as the switch.
4. **`no_intervention` counts as the probe lane for the tap.** The workflow's lane is `probe` though no question came, so the marks replace the tap there as well.
5. **Row 6's switch is `followup.hypothesis_marks`,** as this stage's text says, not RO0's `[router_objective] receipts`. Recorded in the spec's row 6.
6. **Exposure receipts cover four lists.** The marks panel, `why?`, the causal feedback and the unresolved-cause card, on the desktop only. They are sent only when the
   bundle carries `hypothesisMarks`, which is how the client knows the switch is on and nothing is held. The server recomputes factor, diagnosis and probe state itself
   and takes only the order from the client, after checking each id is a cause of that attempt. The attempt inspector's own record lists no
   receipt: it records its own exposure, as today.
7. **Only the marks panel is shuffled.** The other three keep their order, and their receipts record it. Router objective §11 is amended to say so.
8. **The free text reaches the diagnoser only as context.** §7 cites the Oct 12 rule on learner text, whose pipeline (`learner_text_gaps`) can create misconceptions and
   prerequisites. The stage text says "and nothing else", so that pipeline doesn't read it.
9. **A re-diagnosis of the same attempt reads its own marks; nothing triggers one.** A first diagnosis never has any.
10. **A bundle from a rating or a regrade carries no list,** as it carries no `followup`. The screen keeps what it was showing for that attempt rather than lose the
    panel on a rating tap. A mark made on a list a regrade has since replaced is refused quietly.

## The report

`learnloop data-capture report` gains `hypothesis_marks`:

- **Exposure coverage:** rows by surface, attempts displayed against attempts with causes written since the first display, later links, rows and bytes per active day.
- **Agreement with probe outcomes,** apart for independent answers and answers given after the causes were shown, with the full table by mark, outcome, independence and
  timing. `my_gap` and `none_of_these` agree when the probe supports them, `not_it` when it doesn't, `partly` is reported and never scored. A cause the probe didn't
  measure and a probe that didn't discriminate are counted apart.
- **Agreement with delayed performance:** the next delayed answer on the topic under `delayed_completion_v1`. A named gap agrees with a later miss, ruling the list out with a later success.
- **Mark rates by display position,** over the shuffled panel only.

Each of the three carries a label starting "conditional on being observed". No threshold reads any of it.

## Process notes

- Early in the stage, file-only patch scripts run with the system `python3` and two `lint-imports` runs were outside `env -i`. They read and wrote text files in the worktree, and imported no
  LearnLoop module that could reach a route. Later scripts, the generators and the fixture rebuild ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.
- No real model call, no vault opened, no paid command, no desktop window. Synthetic vaults only.
- `apps/learnloop-mobile`, `src/learnloop_mobile/allowlist.py`, `.gitignore` and `README.md` weren't touched; the new RPCs aren't on the phone's allowlist, so the phone can't reach them.

## Gate (implementation step; the full suite runs once at the landing)

Every pytest, vitest, npm and cargo command inside the memory-capped scope, pytest at most `-n 6`, heavy runs behind the lock.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | done |
| `lint-imports --no-cache` (under `env -i`) | 43 kept, 0 broken; the frozen-cycles contract kept |
| Targeted, 259 files (`docs/reviews/followup-fg1c.targeted-tests.txt`: every file naming a changed module or function, every changed test, the contract tests) | 5266 passed, 1 failed, 19 skipped, 5 xfailed (39:40) |
| The one failure | `test_followup_journey.py::test_with_the_switch_off_the_replies_match_the_predecessor`: the marks panel's order hangs off episode keys that differ between two vaults. The comparison leaves that key to FG1c's own on-and-off test, and the seed no longer takes the factor id. Passed 3 of 3 alone |
| Rerun after those fixes, 24 files | 873 passed, 0 failed: label audit `test_measurement_state_labels.py`, `test_cli_help_snapshot.py`, the process-launch list in `test_codex_lockdown_round3.py`, `test_architecture.py`, `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`, `test_sidecar_serializer_snapshot.py`, `test_config_refactor.py`, `test_table_roles.py`, `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`, `test_public_tip_guards.py`, `test_desktop_activation_audit.py`, `test_data_capture_report.py`, `test_followup_{journey,codex_review,successor,live_shape,rival_factor}.py`, `test_hypothesis_marks{,_context,_migration}.py`, `test_diagnosis_card.py`, `test_ux_phase4_feedback.py` |
| Durability (`-m durability`: `test_hypothesis_marks_migration.py`, `test_followup_migration.py`, `test_data_capture_migration.py`, `test_coordinated_migrations.py`, `test_migrations.py`) | 4 passed, 76 deselected |
| Desktop: `npm install`, `npm run typecheck` | exit 0 |
| `vitest --maxWorkers=4`: `HypothesisMarks.test.tsx`, `FeedbackScreen.followup.test.tsx`, `FeedbackScreen.test.tsx`, `FeedbackScreen.phase4.test.tsx`, `RepairOverFeedback.phase4.test.tsx`, `DiagnosisCard.test.tsx` | 115 passed |
| `npm run frontend:build`, `cargo check` (`commands.rs`, `main.rs` changed) | exit 0 |
| References: `db_generate_reference`, `db_validate_reference`, `module_generate`, `module_validate`, `desktop_generate`, `desktop_validate`, `validate_vault` | `errors: []`; 319 TS and 6 Rust notes; 1:1 module coverage; vault validation passes |

The 259-file run was before the seed fix and the panel's kept read in `FeedbackScreen.tsx`; the 24 files above and the vitest row are after them.

## Open items

- The panel has not been seen in a real window.
- Sibling RO0 takes the next migration too. A landing that renumbers this one renames `242_hypothesis_marks.sql`, the head fixture, `SCHEMA_HEAD` in the two reference scripts and `MARKS_ADDED_OBJECTS`' callers.
- Fingerprints and the leaf count in `Configuration.md` and `Database.md` move again if RO0 adds a config key.
