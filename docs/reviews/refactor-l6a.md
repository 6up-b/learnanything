# Refactor L6a: the cores already extracted return their decision records

Branch `refactor/l6a-cores-return-records`, based on main `cd792d4fc2` (I2c landed). Step L6a of the strategy v3
audit (`docs/reviews/refactor-strategy-v3-audit-2026-11-16.md` §2.5 and §3), approved by the owner on 2026-11-20.
Structure track: no served or persisted value changes.

**Outcome.** L6 ("every pure core the arcs extract returns its `DecisionRecord` with its result") now holds for I1's
grade-application core and I2's due-queue ranking, the two cores that landed before the rule reached the briefs.

- `attempts.grade_application` returns the live grade's records on `AttemptApplication.grade_decision`
  (a `grade_records.GradeDecision`: the grade's record, and its hold's when the core's in-flight hold applies; `None`
  on replay). The attempt step writes them last in its transaction, as before.
- `scheduler.rank_due` returns the slate's record on `RankedQueue.record` when its inputs ask for one (a serving
  build with a session, the build that writes a slate row). `_persist_due_queue` writes it after the offer, as
  before. The read path asks for none, so it builds and writes nothing.
- `tests/test_why_cases.py` stages one case per rule code each core can return (13 cases) and enumerates the codes
  from the code.
- L6 is in the strategy's per-step rules (§2.1, "Records (L6)").

Every record written is byte-identical on the due-queue, grade-application, journey and synthesis-tail goldens. The
identity pins are unchanged. The decision logic is untouched, by AST comparison (§4).

## 1. What moved

### The grade

**Before.** `attempts._record_grade_decision` ran after the whole attempt step. It read the application, the
`ApplyAttemptInput` and the vault, then called `grade_records.record_grade`, which built the grade's record
(`grade_record`, reading `provenance.current_cause()` for its parent), wrote it, then built the hold's record with
the written id as its parent and wrote that.

**After.**

- `grade_application`, the core's second stage, builds the records from the values it decided with:
  `grade_records.grade_decision(...)` over the result it just built, its `held`, its error events, its FSRS
  summary, its draft and its `GradeInputs`. The build never raises: a record that cannot be built logs the old
  warning and is left out, and the grade stands.
- `GradeInputs` gains the two values the old builder read from the shell that the core did not have:
  `grader_mode` (from `ApplyAttemptInput.grader_mode`, through `compute_attempt_application` and
  `_compute_resolved_grade_application`) and `replay`. On replay the core returns `None`, because replay re-applies a
  recorded attempt and must not claim to have decided it again. It wrote no record before either.
- `grade_records.write_grade_decision(repository, decision)` is the writer. It fills only what exists at write time:
  the grade's parent (`current_cause()`, read at the same moment as before, just before the write) and the hold's
  parent (the grade's written id, or none when that write failed, as before).
- The regrade builds and writes through the same two functions, with its own values (`decided_by="regrade"`).
- **Gone:** `attempts._record_grade_decision` and `grade_records.record_grade`. `grade_record` no longer reads the
  context for a parent.
- **Stays in `grade_records.py`,** as the record's vocabulary the core calls: `grade_record`, `held_record`,
  `verdict_class`, `review_reason_class`, `error_types_of`, and the regrade's `held_now`.

**Where each value the record reads comes from now, and why it is the same value.**

| Value | Before (shell) | After (core) |
|---|---|---|
| draft fields: type, hints, don't know, stuck, primed, presentations, session | `attempt.draft` | `inputs.draft` |
| `agent_run_id` | `attempt.grading_agent_run_id or result.agent_run_id` | `result.agent_run_id` |
| `max_points` | `application.rubric.max_points` (guarded) | `rubric.max_points` |
| `unverified_criterion_ids` | `attempt.unverified_criterion_ids` | `inputs.unassessed_criterion_ids` |
| `grader_identity` | `attempt.grader_identity` | `inputs.grader_identity` |
| `algorithm_version` | `vault.config` | `inputs.config` (the same object) |
| error types, held, FSRS | `application.error_events`, `.grade_held`, `.fsrs_review` | the core's own values |

- **`inputs.draft` vs `attempt.draft`.** `inputs.draft` is the draft `_resolve_attempt_target` returns: the shell's
  `attempt.draft` after a second `auto_primed_draft`. The shell already normalised `attempt.draft` with the same call
  at the top of `_apply_attempt_in_transaction`, and the call returns a primed draft unchanged and changes nothing
  but `primed`. The two drafts can differ only if the first reveal-ledger read fails (it then degrades to "not
  primed") and the second succeeds. In that case the attempt row and the core's arithmetic already read the primed
  draft, and the record now agrees with them where before it could not. See judgment call 2.
- **`agent_run_id`.** `result.agent_run_id` is `inputs.agent_run_id`, which is
  `grading_agent_run_id or fallback_agent_run_id`. So `grading_agent_run_id or result.agent_run_id` reduces to it for
  every value, empty strings included.
- **`max_points`.** The core reads `rubric.max_points`, a plain pydantic `int`, before this point (the correctness
  in `grade_scope`, the FSRS rating). So the old guard could not fire without the attempt failing first, and it was
  dropped. `application.rubric` is the core's `rubric`.
- **Unverified criteria.** `unassessed_criterion_ids` is `tuple(attempt.unverified_criterion_ids)`, and
  `held_record` reads it through `_ids`, which sorts it.
- **The shell's later replacements.** `_validate_probe_presentation` replaces only `attempt_record`. The causal
  materialisation replaces only the debug payload, and the probe block end only the result's `probe_block_end`.
  Nothing the record reads is replaced, so it says the same whether it is built in the core or at the end. The
  golden proves it (§3).

### The slate

**Before.** `_persist_due_queue` called `slate_record.record_slate` after the offer with the stamped queue, the
ranking's lists, the shell's copy of the withheld exclusions, the cold deferrals and the slate id. `record_slate`
merged the exclusions, built the record (`slate_record`, which with a slate id also kept only the ten nearest
alternatives and set the subject and detail) and wrote it.

**After.**

- `rank_due` ends by building the record when `RankInputs.records_slate` is set. `_slate_decision` calls
  `slate_record.slate_decision` over the `RankedQueue` it just built, the admission's reads (placement's check
  exclusions, the probe block reason), the inputs (limit, session, the cold deferrals) and the config (the
  teach-back value switch, the algorithm tag). It returns `replace(ranked, record=...)`.
- `slate_decision` merges the exclusions and builds the record. It never raises: on failure it logs the old warning
  and returns `None`.
- `RankInputs` gains `cold_deferrals` and `records_slate`.
- `_persist_due_queue` writes `ranked.record` with `record_slate(repository, record, slate_id=...)`. The writer
  names the slate row (`with_slate_row`: the subject and detail ids, the ten nearest alternatives and the rest counted
  by the rule they lost by, the same arithmetic `slate_record` did when it was handed the id). It never raises.
- **Gone:** `_persist_due_queue`'s `withheld` and `placement_serving` parameters, and `_due_queue`'s exclusions
  dictionary made only for the record (the offer trace still gets its copy). `slate_record` no longer takes
  `slate_id`.
- **Stays in `slate_record.py`:** `by_rule`, `merged_exclusions` (also `exclusion_now`'s), `head_rule`, `item_outcome`
  (`why`'s reader) and the writer.

**Why each value is the same.**

- **The stamped queue.** `_persist_offer`'s stamped queue is `replace(item, scheduler_slate_id=...,
  scheduler_candidate_id=...)` over the ranked queue, in order. The record reads only `practice_item_id`, `priority`
  and three component keys. The one later write to a component (`probe_committed`) is a key the record does not read,
  and the record copies its numbers when it is built.
- **The withheld exclusions.** The shell's copy was rebuilt from `ranked.exclusions` key by key. Every caller hands a
  fresh `OfferTrace` (engine, sidecar, `exclusion_now`), so it held exactly the ranking's. The record sorts and
  de-duplicates what it reads anyway.
- **The other inputs.** `reads.placement_serving` and `reads.probe_block_reason` are the objects the shell passed:
  `_gather_admission_reads` stores them and `_after_check_split` copies them through. The teach-back value switch
  reads only config.

### Sizes

| | Base | Tip |
|---|---|---|
| `attempts.py` | 5,840 | 5,831 (ceiling lowered to match) |
| `scheduler.py` | 4,428 | 4,428 (ceiling unchanged) |
| `rank_due` | 192 | 193 (+ `_slate_decision` 14; built inline it was 204, over the 200-line ratchet) |
| `grade_records.py` | 217 | 246 |
| `slate_record.py` | 274 | 304 |

The builders stayed in `grade_records.py` and `slate_record.py` rather than moving into the core's modules (judgment
call 1).

## 2. The rule codes and their staged cases

Each case goes through the real path and is read back from `why --json`. The tests are
`test_the_grade_application_names_its_rule_code` and `test_the_slate_names_its_rule_code`, with staging in
`tests/why_cases_helpers.py` (`stage_grade_case`, `stage_slate_case`).

**The grade** (the `grade` record's `rule` is `verdict_class`; the hold's is `held_record`'s). Each case is one
answer on a split vault's `pi_svd_compute_001` (`setup` 2 + `result` 2) through `apply_attempt`:

| Code | Staged as |
|---|---|
| `full_credit` | 2 + 2 |
| `partial_credit` | 2 + 1 |
| `no_credit` | 0 + 0 |
| `dont_know` | attempt type `dont_know` |
| `stuck` | `declared_stuck`, 1 + 0 |
| `grade_held_for_review` (`grade_held`) | a model grade held for review with both criteria unverified (held only while nothing is assessed), parent = the grade's record |

**The slate** (the record's `rule` is `head_rule`). Each case is one serving build with a session:

| Code | Staged as |
|---|---|
| `empty_slate` | the basic vault with its one learning object paused |
| `presentation_pin` | the due-queue golden's vault, whose session committed a probe an hour before |
| `pending_followup` | the placement vault with a due cold retry on `pi_eig_easy` |
| `check_once` | the due-queue golden's vault, another session (its due "Check once" first) |
| `seeded_exploration` | the placement vault at exploration rate 1, reward window 10, no goal quota |
| `greedy_order` | the placement vault |
| `composition_order` | the placement vault with a tutor promotion the requested-items floor pulls to the front |

**How I know the list is complete.** `test_the_staged_cases_are_every_rule_code_the_two_cores_return` reads the
codes from the code:

- the module constants `head_rule` and `verdict_class` return, read from their source, conditional expressions
  included, and compared with the staged cases;
- the hold's code: `held_record` returns `grade_contract_unrecorded` only with `contract_unrecorded=True`, and the
  core's call (in `grade_decision`) passes no such keyword. The test asserts that, so the core reaches only
  `grade_held_for_review`.

A branch that returns a new code fails the test until a case stages it.

**Not counted as rule codes:**

- the slate's `lost_by` codes (`ranked_below`, `beyond_limit`) and its exclusion rules. These are the alternatives'
  and exclusions' reasons, not the record's `rule`. `tests/test_slate_record.py` covers them.
- the grade's `status` `fallback`. It is a status, not a rule.

`grade_contract_unrecorded` is reachable from no caller in `src`: the unrecorded-contract hold arises only on replay,
which writes no record. It is dead as a record code, not a bug, so it has no ledger row. A later step may drop the
branch.

## 3. Proof: every written record is byte-identical

- **Due queue, journey, synthesis tail.** `tests/test_due_queue_golden.py`, `tests/test_diagnosis_journey_golden.py`
  and `tests/test_synthesis_tail_golden.py` record `decision_records` rows. They pass at the tip with their goldens
  untouched.
- **Grade application.** `tests/goldens/grade_application/history.json` dumps every field of every
  `AttemptApplication`, so it gains the new `grade_decision` field. It was regenerated, and a scratch script compared
  the two:
  - with `grade_decision` dropped from each application, the new golden equals the base's exactly ("fields dropped:
    44 | rest identical to the old golden: True"). This includes every `live_rows` and `rebuild_rows` table, so
    `decision_records` too;
  - the text diff removes only the 44 `"mastery_seed_inputs": null` lines, which gain a trailing comma, and adds 846
    lines;
  - each of the 12 records the core returned (11 grades and 1 hold) equals a `grade`/`grade_held` row the history
    wrote, column for column apart from id, trace, parent and time. The 13th row is the regrade's own;
  - every replayed application carries `null`.

  `test_the_history_reaches_every_kind_of_grade` now also asserts that replays carry none and that the live history
  reaches all five verdicts and the hold.
- **Identity pins.** `tests/test_identity_pins.py` passes unchanged.

## 4. P-ast: the decision logic is untouched

A scratch script compared each changed module's top-level definitions between `cd792d4fc2` and the tip, as ASTs
with docstrings removed. What changed:

- `attempts.py`:
  - `grade_application`: only its `AttemptApplication(...)` gains the `grade_decision=` argument;
  - `GradeInputs` and `AttemptApplication`: the new fields;
  - `_compute_resolved_grade_application` and `compute_attempt_application`: the `grader_mode`/`replay` pass-through;
  - `_apply_attempt_in_transaction`: the one call line;
  - `_record_grade_decision`: removed.

  `grade_scope`, every stage-B part and every other function are AST-identical.
- `scheduler.py`:
  - `rank_due`: only its final statement changed (`ranked = RankedQueue(...)` and the `replace` return);
  - `RankInputs` and `RankedQueue`: the fields;
  - `_due_queue`: two lines removed (the record-only exclusions dictionary) and two keyword changes;
  - `_persist_due_queue`: the record call;
  - `_slate_decision`: added.

  `_score_candidates`, `admit_due`, the composition and every other function are AST-identical.
- `grade_records.py` and `slate_record.py`:
  - unchanged: `verdict_class`, `review_reason_class`, `held_record`, `head_rule`, `by_rule`, `merged_exclusions`,
    `item_outcome`;
  - `grade_record`: drops the parent read;
  - `slate_record`: drops the slate-id branch, which `with_slate_row` now holds;
  - `record_grade`: removed; `record_slate`: its build moved into `slate_decision`.
- `regrade.py`: the record call only.

## 5. Tests changed, and why

- `tests/test_attempt_chain_records.py`:
  - **Rewritten:** `test_a_live_held_attempt_writes_its_hold_record_in_the_attempt_step` became
    `test_a_live_held_attempt_writes_the_records_its_core_returned`. The old test forced `grade_held=True` onto the
    application after the core, by patching `compute_attempt_application`. The record is now built inside the core,
    so that patch can no longer reach it. The new test applies a held grade for real (`grade_held_for_review`, both
    criteria unverified). It checks the decision the step wrote (held fact, hold, no parents before the write) and
    the rows `why` reads (kinds, trace, the hold's parent = the grade's id). Nothing is weaker: the in-flight hold is
    still what the records carry.
  - **Ported:** `test_a_held_grade_gets_a_record_when_the_hold_first_applies` now uses
    `write_grade_decision(grade_decision(...))` in place of `record_grade(...)`. Its assertions are unchanged.
  - **Added:** `test_a_record_that_cannot_be_built_leaves_the_grade_and_logs`.
- `tests/test_provenance.py`: the rebuild test counts calls to `write_grade_decision`, the live writer now, where it
  counted `record_grade`.
- `tests/test_slate_record.py`:
  - **Ported:** `test_a_recorded_slate_keeps_ten_alternatives_and_counts_the_rest` builds without a row and applies
    `with_slate_row`. Its assertions are the same, plus the subject and detail ids and that the returned record is
    left as it was. `test_the_rule_that_put_the_head_first` drops `slate_id=None`.
  - **Added:** `test_a_record_that_cannot_be_built_changes_nothing_and_writes_nothing`.
- `tests/test_grade_application_golden.py`: the assertions in §3. Its golden was regenerated (§3).
- `tests/test_why_cases.py`, `tests/why_cases_helpers.py`: the 13 cases and the enumeration test.

No assertion that checks real behaviour was loosened.

## 6. Structure ratchet

| Number | Base | Tip | Why |
|---|---|---|---|
| `golden_json_lines` | 295,142 | 295,944 | the grade golden's new field (§3) |
| `attempts.py` | 5,840 | 5,831 | lowered for this step's own reduction |
| `functions_over_200_lines` | 70 | 70 | `rank_due` kept under 200 by `_slate_decision` |

Every other number is unchanged.

## 7. Judgment calls

1. **The builders stayed in their modules.** The brief says the two modules "lose what moved (or go, if nothing is
   left)". `attempts.py` and `scheduler.py` sit exactly at their file ceilings (M1). Moving `grade_record`,
   `held_record`, `head_rule`, `slate_record` and their helpers into them would add about 250 lines for no change in
   what the record says. So what moved is the build call and its inputs, from the shell after the decision into the
   core. The modules lost their build-and-write shells:
   - `record_grade` is gone;
   - `record_slate` is now only a writer;
   - `slate_record` no longer takes the row's id.

   L6's risk, a branch the builder does not know, is guarded by the enumeration test (§2) rather than by
   co-location. If the owner wants the builders inside the cores' modules, it is a later move with the ceilings
   raised.
2. **The record reads the core's draft** (`inputs.draft`), not the shell's `attempt.draft` (§1). They are equal
   except after a transient reveal-ledger read failure, where the record now agrees with the attempt row. Keeping
   the shell's draft would mean carrying a second draft into the core only for the record.
3. **No records on replay** is a core input (`GradeInputs.replay`), not a filter in the shell. Without it, the
   golden would carry 33 more record dumps (about 2,000 lines), and a replay would build records nobody writes.
4. **The slate record is built only when asked** (`records_slate`). The read path (`read_due_queue`,
   `exclusion_now`, a sessionless serve) builds and writes nothing, as I2c left it.
5. **The parent is filled at write time,** by the writer, not read from the context by the core. It is the same
   moment as before (just before the write), and the core reads no context variable.
6. **The enumeration test reads the two modules' source with `ast`** (not `inspect.getsource`, which the ratchet
   counts). It reads which constants two functions return, the only way a new code fails before anyone stages it.

## 8. Commands and results

All test runs used `-n 1` inside a `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=1G` scope, through
the scratch wrapper (empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`).

| Command | Result |
|---|---|
| base: the four golden files (`test_due_queue_golden`, `test_grade_application_golden`, `test_diagnosis_journey_golden`, `test_synthesis_tail_golden`) | 68 passed |
| tip, before regenerating: the same | 1 failed (the grade golden's new field), 67 passed |
| `GRADE_APPLICATION_GOLDEN_ACTUAL=<scratch> pytest tests/test_grade_application_golden.py::test_every_grade_application_and_row_is_unchanged`, then the scratch comparison | "fields dropped: 44 \| rest identical to the old golden: True"; "returned records matched to written rows: 12" |
| tip: the four goldens, `test_why_cases`, `test_slate_record`, `test_due_queue_stages`, `test_structure_ratchets`, `test_identity_pins` | 473 passed, 1 failed (`golden_json_lines` +802, before the golden's line was raised) |
| `test_structure_ratchets` after raising it | 3 passed |
| `scripts/affected_tests.py --files` (the five changed src files) | 1,351 files |
| those matching `grade\|slate\|regrade\|scheduler\|due_queue\|why\|provenance\|decision_record\|held\|chain_record\|attempt_step\|apply_attempt\|attempt_application` (46), plus `test_attempts\|session_ownership\|k1_remediation_cold\|synthesis_tail_golden\|diagnosis_journey_golden\|curriculum_c1_fix_round3\|rebuild_equivalence\|test_replay` (10), `-m "not arc_close"`, chunk 1 of 2 (40 files) | 648 passed, 2 xfailed |
| chunk 2 of 2 (16 files) | 571 passed, 6 skipped |
| `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies` | 398 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 52 kept, 0 broken. |
| `python scripts/check_gate_partition.py` | collected 33300: landing 33234 + arc_close 66 |

The vault's generated references were not regenerated (the landing does).

## 9. Not verified

- P-shadow and P-draw. No served value moved, and the router's draws are not reached.
- The full suite and the durability lane. They are the landing gate's.
- The identity pins at the first commit alone. Each run was on the working tree, and the slate change was already
  present for the first one. Every run passed.
- `scripts/affected_tests.py` listed 1,351 files. I ran the 56 whose names match the step's subject (filter in §8).
- The owner vaults were not used. The proof is on the synthetic goldens.
