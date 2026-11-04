# RO0 Codex review: findings and fixes (`router/ro0-logging`)

The review (codex job `20261104-112408-8janlG`, gpt-6.1-sol) read the stage at `d4996b8db9` and made eight findings. All eight reproduce and are fixed in one
commit. The tests are in `tests/test_ro0_codex_review.py`. Each test was run against the tree before the fix: the source and migrations of `d4996b8db9` were
exported to a scratch directory and put first on the path (`-o pythonpath=`). 27 of its 33 tests fail there and all 33 pass after the fix. The six that pass
on both trees are guards on what the fix must keep:

- a list that served no head reads no AD;
- an attempt from before an FG1 decision isn't its uptake;
- a session still open returns in the next one;
- off, the exposure paths write no initiator;
- an unchanged goal load takes no write lock;
- the AST audit of every exposure writer (it reads the current source, so it has no before).

## Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Refusing disclosure metadata rolls back the question itself | fixed | `2079aa1eb0` | `test_f1_a_refused_disclosure_write_leaves_the_question_and_warns`, `test_f1_the_refusal_is_the_receipts_alone_inside_a_callers_transaction` (a trigger refuses the `UPDATE` itself, not a preparatory read) |
| F2 | Medium | Forced items disappear from decision-state snapshots | fixed | `2079aa1eb0` | `test_f2_the_forced_shape_names_its_item` (the helper returned `([], [])`), `test_f2_a_forced_only_boundary_keeps_the_served_items_state_and_minutes` |
| F3 | Medium | Omitted AD belief cannot reliably be recovered by replay | fixed | `2079aa1eb0` | `test_f3_a_served_offer_keeps_its_candidates_ad_numbers`, `test_f3_a_staged_decision_keeps_its_ad_numbers`, `test_f3_the_staged_bridge_hands_its_decision_the_ad_reader`, `test_f3_a_lesson_suggestion_keeps_its_ad_numbers_read_before_its_transaction`; guard `test_f3_a_list_that_served_no_head_still_decides_nothing_and_reads_no_ad` |
| F4 | Medium | Trajectories miss FG1's generated-probe uptake | fixed | `2079aa1eb0` | `test_f4_a_generated_probes_attempt_is_uptake_counted_once_through_every_binding`, `test_f4_a_binding_outcome_is_read_and_only_a_skip_or_abandonment_is_a_rejection[5 outcomes]`, `test_f4_an_attempt_on_the_item_before_the_decision_is_not_its_uptake` |
| F5 | Medium | The initial session start is reported as a return | fixed | `2079aa1eb0` | `test_f5_the_session_a_pre_session_decision_opened_is_not_its_return`, `test_f5_a_decision_whose_session_is_unknown_is_censored_and_names_no_return`, `test_f5_a_session_still_open_returns_in_the_next_one_it_was_replaced_by` |
| F6 | Medium | Reading minutes are assigned entirely by receipt close time | fixed | `2079aa1eb0` | six `test_f6_*` tests: the tail of a visit a session starts in, midnight, idle spread, a late receipt, a visit after the session ended, a visit with no interval |
| F7 | Medium | Several live exposure paths never populate row 4 | fixed | `2079aa1eb0` | `test_f7_a_from_your_books_excerpt_names_its_initiator`, `test_f7_the_book_beside_a_problem_names_its_initiator` (set_book, open, resume), `test_f7_the_exercise_list_names_its_initiator`, `test_f7_off_the_new_paths_write_none_of_it`, `test_f7_every_writer_of_the_table_passes_the_initiators_fields` (AST audit) |
| F8 | Low | Concurrent goal sweeps append duplicate lifecycle events | fixed | `2079aa1eb0` | `test_f8_two_loaders_sweeping_a_new_goal_write_it_once`, `test_f8_two_loaders_sweeping_a_pause_write_it_once` (two connections, interleaved), `test_f8_an_unchanged_load_takes_no_write_lock` |

No finding was rejected. None is High.

## What changed

**F1.** The `reveal_state_json` write moved to `db/stores/router_objective.set_question_state`. It runs inside a savepoint. If the write is refused, the
savepoint rolls back alone, a warning is logged, and the question and its answer stand. This holds inside a caller's `atomic()` too.

**F2.** `decision_state.candidate_ids` now reads a forced entry's `practice_item_id`. The plan's `block_minutes` also keys a forced entry by its item, so the
receipt keeps the item's FSRS state, its LO's belief, its estimator minutes and what the block was charged.

**F3.** A served Today offer (plan off), `staged_p2` and `lesson_suggestion` now read AD before their transactions open and keep the numbers with their
state hash:

- the offer reads it through `readiness.decision_state_fields`;
- the staged bridge gets the reader from the sidecar's `golden_path.advance` as `ad_fields`, because `scheduling` stays below `adaptive_difficulty` in the
  import contracts;
- the suggestion now prepares its receipt before the draw's `atomic()` opens, where AD's guard is not inside a write.

A Today list that served no head still keeps no belief. It decided nothing among its candidates, so there is no decision-time belief to lose. Spec §4 rows
9 and 13 and the stage record now say this.

Cost: plan-off Today goes from 281 to 496 ms median (+215 ms), and a served offer's receipt is 4,636 bytes. These numbers were measured on the 300-item
synthetic vault with `perf.py`, the stage record's method, and only a vault with `plan.enabled = false` pays the cost. The stage record's table and its
open question 2 hold them.

**F4.** `trajectory.TRAJECTORY_SQL` now joins FG1's `router_decision_bindings`: the item, the probe presentation, the plan presentation and the outcome.

- Uptake is the union of the attempts reached through the plan presentation, the bound plan presentation, the bound probe presentation, and the bound
  item's attempts after the decision. One attempt reached by several links counts once.
- Rejection adds a binding's `skipped` or `abandoned` outcome, deduplicated by item.

**F5.** A return is now read after the session the action happened in. That session is the decision's own; failing that, its block's, its presentation's
(direct, bound or through its block), or its attempt's (offer slate or bound item). The return is the first other session to start after it ends. If no
link names a session, the return is censored `session_unresolved` and is never inferred from the clock.

**F6.** A Reader visit's active seconds now count when they happened, not when its close was received.

- A visit's interval is its close stamp (`occurred_at` when the client sent one) minus its active plus idle seconds.
- A visit that crosses a session's start or end, or midnight, is split in proportion to the time elapsed on each side, because where its idle gaps fell
  isn't kept.
- A visit with no idle count has no interval. It goes into neither total, and the receipt reports its minutes as `reader_unattributed`.
- The receipt counts the split visits in `reader_split_visits`, and `basis` names the rule.

**F7.** The fields of `exposure.fields` now reach the three writers that the review named:

- the tutor's "From your books" excerpt (`tutor_citation`);
- the workbench's book beside a problem, on open, resume and `set_book` (`reader`);
- the library exercise list (`library`).

An AST audit fails if any call to an exposure writer, or any function that inserts into `source_exposure_events`, does not take the keyword.

**F8.** `goal_lifecycle.sweep` still reads first, and a load that changes nothing takes no write lock. When there is a change, it decides again inside the
`BEGIN IMMEDIATE` transaction before appending, so a second loader that read the same old state writes nothing. No uniqueness constraint was added,
because a goal can legitimately pause twice. Serialising the decision under the write lock is what makes the sweep idempotent.

Also: `test_ro0_row12_trajectory.py`'s return test now opens its session before building, since F5 censors a decision that no link places in a session.
`docs/reviews/router-ro0-logging.md` (row 12's audit, the serve-path section, open question 2) and spec §4 rows 9, 13 and 12 describe what was built.

## Gate

Setup: `uv sync --extra dev --extra mobile`, then `uv pip install --offline pypdfium2==5.14.0`. Every pytest run used the memory-capped
`systemd-run` scope with `-n 6`, one run at a time.

| What | Result |
|---|---|
| `lint-imports --no-cache` (`env -i`, empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`) | 42 kept, 0 broken; frozen cycles kept |
| `tests/test_ro0_codex_review.py` and `tests/test_ro0_row12_trajectory.py` | 38 passed |
| The same review file on `d4996b8db9`'s source and migrations | 27 failed, 6 passed (the guards listed above) |
| Targeted pytest, 153 files (`router-ro0-codex-review.targeted-tests.txt`) | 3,024 passed, 5 skipped, 0 failed |
| `--durable-sqlite` on `test_ro0_*.py` (the review file included) and `test_question_context.py` | 139 passed |
| `-m durability` on `test_ro0_*.py`, `test_question_context.py` and `test_coordinated_migrations.py` | 2 passed |
| Plan-off Today latency (`perf.py`, synthetic 300-item vault, `env -i`, 0 `model_call_receipts`), base `90f7def5e3` against the fix, alternating, twice | 289 and 276 ms against 499 and 492 ms median: about +210 ms, which matches the stage record's +215 |

The 153 files are every test file that names a module or function this fix changed, plus these contract and audit files:

- `test_architecture.py`;
- the CLI help snapshot (`test_cli_help_snapshot.py`);
- the serializer snapshot (`test_sidecar_serializer_snapshot.py`);
- the desktop RPC contract (`test_desktop_rpc_contract.py`);
- the mobile allowlist (`test_mobile_allowlist.py`);
- `test_table_roles.py`;
- `test_coordinated_migrations.py`;
- `test_tracked_fixture_databases.py`;
- the config defaults (`test_config_refactor.py`);
- the display label's blast-radius audit (`test_measurement_state_labels.py`);
- the approved process-launch list (`test_codex_lockdown_round3.py`).

Not run, because nothing they cover changed:

- the frontend, `cargo check` and the DB reference scripts: no frontend file, no `src-tauri` file and no schema changed, and the migration is untouched;
- the full suite, the whole durability lane and the whole vitest run: these belong to the landing gate.

No paid or live calls were made. Scripts outside pytest ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. Only synthetic vaults
were used, all in the scratch directory, and none of the owner's off-limit paths was touched.

## Codex verify: F1 and F7 reopened, fixed at the landing

The scoped verify (codex job `20261104-165216-3b1KmL`) read `58ec14a227`. It closed F2 to F6 and F8 and reopened two:

- **F1, sibling writes.** The disclosure state's fix held, but three other RO0 writes still rode their row's insert:
  `ask_available` in the plan presentation's insert (which a keyed pick requires, so a refusal failed the pick), the
  generating-process fields in the pending question's insert (a refusal failed the answer before its model call), and
  the initiator fields in the source exposure's insert (a refusal failed the opening and lost its coldness exposure).
  Codex reproduced the pick and the answer at mvp-0.43, 0.44 and 0.45.
- **F7, Reader attribution.** A visit's block was the newest reading block on its extraction and its session the one
  open when the batch arrived, so a visit stamped 09:01 and received at 10:01 was stored against a block created at
  10:00 and the newer session.

The orchestrator ruled R1 and R2 (verbatim in `docs/reviews/router-ro0-logging.md`, "Landing onto main"). Each fix is
its own commit, and its tests carry Codex's reproductions. The tests are in `tests/test_ro0_codex_verify.py`.

| Id | Ruling | Commit | Tests |
|---|---|---|---|
| F1 | R1 | `811e16a98f` | `test_r1_*` (31: 26 journeys, a keyed pick, an answer and a source opening at three versions, an arranged check's delay and an unserved check's type at 0.44 and 0.45, each under an insert-refusing and a fill-refusing trigger; every writer at the store; the five writers are the only inserts; the guards name every column and refuse every other update) |
| F7 | R2 | `ed0e027193` | `test_r2_*` (Codex's late visit; two sessions fitting, none fitting; two blocks in force, an ended block; the client's capture; a learner's visit names no block; an opening with two open sessions; off writes no link) |

**R1.** No RO0 field on a table that existed before it is written in its row's insert. The writers are the only five inserts into
those tables (a test pins the list): `insert_question_event`, `insert_source_exposure_event`, `insert_plan_presentation`,
`insert_objective` and `insert_measurement_event`. Each inserts the row with its predecessor's fields, then calls
`db/stores/router_objective.fill_receipt`. That writes RO0's fields in one `UPDATE` inside its own savepoint; refused, the savepoint rolls back
alone, a warning names the row, and the row stands with them null. `RECEIPT_FIELDS` lists the fields:

- `question_events`: `reveal_state_json`, and the generating process RO0 fills (`hints_used_before`, `scaffold_level`,
  `preceding_tutor_move`, `learner_mode`, `question_opportunity`);
- `plan_presentations.ask_available`;
- `source_exposure_events`: `initiator`, `initiator_block_id`, `initiator_session_id`, `initiator_visit_id`;
- `decision_objectives.delay_json`;
- `decision_measurement_events`: `non_service_type`, `delay_json`.

Callers are unchanged: the writer splits the fields off itself, so no caller can put one back in the insert. The
disclosure state's own helper (`set_question_state`) is folded into the fill. `ask_availability.serve_fields` no longer
raises, since a keyed pick's serve propagates what fails inside it.

Three of the tables are append-only. Migration 242 now replaces their update guards
(`plan_presentations_no_update`, `decision_objectives_no_update`, `decision_measurement_events_no_update`) with guards that allow exactly the fill:
RO0's columns set once from null, every other column unchanged. Each guard names every column of its table, and a test fails if a
later column is missing from it. Every other update, a second fill, and a fill that changes another column are still
refused, and so is every delete.

**R2.** A Reader visit's block and session are resolved as of its `occurred_at`, the client's stamp. Without a stamp,
they're resolved as of when the server had the visit.

- A session fits if it had started by then and hadn't ended before it.
- A plan reading block on the visit's extraction fits if it had been created by then and hadn't ended
  (`block_ended`) before it.
- Exactly one fit is the link. None, or more than one, is recorded as unknown.
- A block or session the client sends at the opening stands.

The payload says which happened: `session_link` and, for a plan-sent visit or a client's block, `block_link`, each
`client`, `as_of_event` or `unknown`. An unknown link has no id. An opening the server records as it happens
(`exposure.fields`, every source exposure) names the one open session, and none when two are open, where it used to name
the newest. The desktop sends neither id yet, so its visits are resolved by the server. One case stays open and is
named here, not guessed around: a session left open by a crash is ended later at its last attempt or checkpoint. A visit made while it was still open
was linked to it as of then (`as_of_event`), and a reader that trains on the link can check it against the
session's final `ended_at`.

R4 (verbatim in the record) sets the bar for later findings: there's no further Codex round on these two classes.

### Gate (step 0)

| What | Result |
|---|---|
| `tests/test_ro0_codex_verify.py` before R1's fix (R1 part) | 30 failed, 1 passed (the list of writers, which reads the source) |
| The same after R1 | 31 passed |
| R2's part before its fix | 7 failed, 1 passed (off writes no link, a guard) |
| R2's part after | 8 passed; with the row 3, 4 and 5 files and the review file, 96 passed |
| Targeted after R1: 294 files naming a changed table or writer, plus the contract files | 11,237 passed, 13 skipped, 2 xfailed, 21 failed: every one an earlier migration's additive diff, which saw `plan_presentations_no_update` change. `TE1_AND_TE1B_ALTERED_TABLES` now names it; the 21 rerun pass |
| Targeted after R2: every `test_ro0_*`, `test_question_context`, `test_data_capture_successor`, `test_table_roles`, `test_coordinated_migrations`, `test_architecture`, and the files naming the Reader's activity or an exposure (78 files) | 7,445 passed, 6 skipped, 0 failed |
| `--durable-sqlite` on `test_ro0_*.py` and `test_question_context.py` | 178 passed |
| `lint-imports --no-cache` | 42 kept, 0 broken |

Every pytest run was in the memory-capped scope with `-n 6`, and every script outside pytest under `env -i` with empty `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`. No model call. The head fixture still holds 242's earlier guards: the landing rebuilds it as `migration_head_243`, applying the
final file.
