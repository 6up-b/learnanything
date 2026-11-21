# EP0: attempt facts and the readers' named predicates

Evidence packets spec (`docs/specs/spec_evidence_packets_v1.md`) §3, §8 EP0, §9, §10. A structure step: no served or
stored value, ordering, exception, cache key, seed or prompt changes; no identity pin moves; no migration, table,
config key, algorithm tag, kill switch, backfill or frontend capture; priming, FSRS, eligibility and certification are
untouched; the grader gains access to nothing.

- **Base:** `6b821315af` (branch `ep/ep0-attempt-facts`: EP0t's branch `ep/ep0t-time-policies` merged with origin/main
  `2f761915a2`). **Head:** the commit that adds this record.
- **New modules:** `src/learnloop/attempts/facts.py` (`AttemptFacts`, its coverage, `collect_facts`,
  `facts_from_draft`, `submitted_facts`) and `src/learnloop/attempts/fact_predicates.py` (the readers' predicates over
  the facts, each under its owner). `collect_facts` takes EP0t's `Cutoff` (`db/evidence_cutoff.py`); no other cutoff
  representation is introduced and EP0t's files are not edited.
- **Census:** `tests/fixtures/attempt_facts_census.toml` (73 readers: 10 adapted, 6 delegated, 16 named, 41 not adapted), held to the tree by
  `tests/test_attempt_facts_census.py`.

## 1. Judgment calls to read first

1. **Adaptive difficulty's predicates stay with adaptive difficulty.** `help_timing`, `category` and `ELIGIBLE_TYPES`
   (`adaptive_difficulty/outcomes.py`) are not moved: AD may import nothing of `learnloop.attempts`
   (`adaptive-difficulty-never-writes-evidence`), and `learnloop.attempts` importing AD would cross the same guard
   from the other side. `AttemptFacts` carries every input they read (correctness, `hints_used`,
   `first_hint_progress`, the questions with their progress markers, `primed`, the bound plan presentation, the forced-
   failure inputs); `pre_exposed` is AD's own frozen serve input and is `absent` here. A test helper maps facts onto
   AD's type and the categories agree on the full assistance x timing x category matrix (8 dimensions, 6,912 cases).
2. **Three predicates delegate instead of moving.** The canonical test (`counts_as_assisted`,
   `recorded_counts_as_assisted`) calls `diagnosis.causal_activity_policy`, intervention outcomes' test
   (`intervention_assisted`) calls `substrate.intervention_outcomes.is_assisted`, and the coldness dimension
   (`unassisted_for_coldness`) calls `attempts.coldness_receipt._unassisted`. The owners keep their kernels byte for
   byte. The coldness kernel was first moved and then put back: the receipt is a member of an existing 19-module import
   cycle that also contains the canonical policy, so the receipt importing the predicates (which import the policy)
   pulled the predicates into that cycle (`modules_in_an_import_cycle` 220 -> 221). With the kernel back in the
   receipt the ratchet is unchanged.
3. **One frozen-cycle exemption** (`pyproject.toml`, `frozen-cross-package-cycles`):
   `learnloop.attempts.fact_predicates -> learnloop.diagnosis.causal_activity_policy`, the same leaf and the same
   reason as the two scheduler readers of it already exempted (`recall_targets`, `serving`). Without it the
   predicates could not delegate to the complete policy, and the sheet forbids treating its legacy union as the
   canonical test.
4. **One new contract** (`graders-never-read-attempt-facts`): the nine grading-context and grading-prompt modules
   of `learnloop.attempts` import neither `attempts.facts` nor `attempts.fact_predicates`. `attempts.attempts` (which
   applies the FSRS cap after grading) is not one of them and does import the predicates.
5. **Adapted only where the change is small and provably equal** (ten reader sites in six modules, section 3).
   Readers in packages that may not import `learnloop.attempts` (adaptive difficulty, hints, router, the field's
   pure predictors) or whose import of it would be a new back edge of a frozen package cycle (goals, placement,
   substrate, learner, scheduling) are named, not adapted; SQL filters are named, not moved into Python.
6. **No purpose-specific difference was resolved.** Each adapter passes the values its reader read, verbatim, to a
   kernel that applies the reader's own coercions (`int(x or 0)`, `bool(x)`, plain truthiness). The differences are
   in the ledger (section 5).
7. **The census's `reads` check is a token check.** A reader that applies an inline expression is held to the tree by
   a name it reads (`hints_used`, a set, a function); the completeness check covers every function that names a
   predicate authority, and the inline rows are bounded by the search in section 4.

## 2. The facts and their coverage

`AttemptFacts` (frozen). Submitted values are kept verbatim; detail rows beside them, never recomputed into them.

| Field | Source | Coverage |
|---|---|---|
| `produced_as`, `hints_used`, `primed` | `practice_attempts.attempt_type`, `.hints_used`, `.primed` | `present` (the submitted count and flags; `primed` may have been forced at submit by the reveal ledger) |
| `first_hint_progress` | `practice_attempts.first_hint_progress` | `present`, or `absent` where the row has none (before migration 213, or no hint) |
| `correctness`, `received_at`, `latency_seconds`, `active_seconds` | `practice_attempts.*` | `present` or `absent` by the row's value |
| `declared_dont_know`, `declared_stuck` | `practice_attempts.*` | `present`, noted: a row written before its column existed reads the default 0 |
| `answer_empty` | `practice_attempts.learner_answer_md` (read, not kept) | the blank-answer input of AD's forced failure |
| `hints` (`HelpFact` per row: kind, hint kind, level, surface, counted by, requested, shown and when, attached, submit time, work length) | `help_assists` rows attached to the attempt or recorded under its submission key for its item | `absent` (no table); `count_only` (no row: no help, or none captured; the submitted count stands); `present` (shown, attached, counted kinds at levels 1-3 account for `hints_used`); `partial` (they do not, or a row is keyed but not attached, or the read is as of then) |
| `questions` (`QuestionFact`: context, type, hint-equivalent, progress marker, seconds in) | `question_events.attempt_id` | `present`, `absent` with no table |
| `reveals` (`RevealFact`: source kind, amount, basis, time, linked attempt, repair episode, `before_serve` / `during` / `unknown`) | `reveal_events` on the item after its previous attempt and at or before this one | `present`, `absent` with no table. The ledger's rows: not the submit path's total (no routine-display horizon, no own-disclosure exemption). A display row records coverage (on screen), not reading |
| `presented_at`, `plan_presentation_id`, `probe_presentation_id`, `bound_presentation` | `plan_presentations.served_at` by `practice_attempts.plan_presentation_id` | `present`, or `absent` (no plan presentation; a probe presentation's serve time is not read) |
| `pre_exposed` | `item_serve_inputs.pre_exposed` | `absent`: AD's frozen serve input, read only by its replay |
| `entry_surface`, `submission_id` | `practice_attempts.*` | provenance; one answer is one attempt whatever its surface |
| `detail` | | `full` when the help rows were found (`present` or `partial`), else `counts_only` |

A draft (`facts_from_draft`) and a row-only adapter (`submitted_facts`) mark every detail source `not_read`.

`collect_facts(reader, attempt_ids, cutoff)`: an attempt the reader withholds or `cutoff.admits` refuses is left out.
Under `corrections = "then"` (`Cutoff.as_known_at`) a help row requested after `known_at` is left out, one shown after
it reads not shown, and the help coverage is `partial` (an attachment and a submit time have no time of their own),
which is EP0t's settled reconstruction. Every other preset reads rows as they stand. The reader carries visibility:
`ConnectionReader` (all rows) or `FilteredReader` (a view with the material view's `filter`); every read
(the attempts, the item's earlier attempts, help rows, questions, reveals, presentations) goes through it.

### Stored assistance columns

| Column | Writer | Predicate | Role |
|---|---|---|---|
| `facet_outcome_observations.assisted` | `field/outcomes.py::_load` (`assisted=policy.counts_as_assisted`), written by `db/stores/field.py` | `recorded_counts_as_assisted`: the canonical test unioned with the recorded causal classification and the reference status | DERIVED (`db/table_roles.py`), rebuilt by `substrate/rebuild_orchestrator.py` |
| `facet_outcome_observations.primed` | the same | the submitted `primed`, verbatim | DERIVED |
| `certification_cold_probe_outcomes.assisted` | `goals/certification_cold_probe.py::_record_probe_outcome` | `counts_as_assisted` (the canonical test, type defaulted to `independent_attempt`) | RAW_LEDGER; `CHECK (verdict = 'indeterminate' OR assisted = 0)` |
| `retrieval_interventions.next_assisted` | `substrate/intervention_outcomes.py::outcome_for` | `intervention_assisted` (`int(is_assisted(next attempt))`) | RAW_LEDGER |

## 3. Before/after caller map

Statuses as in the census: **adapted** (asks through the named predicate), **delegated** (owner keeps the kernel; the
predicate calls it), **named** (calls a delegated or adapted owner's function, unchanged), **not adapted** (its own
expression; the reason is in the census).

| Reader | Before | After |
|---|---|---|
| `attempts/attempts.py::_capped_rating` | `_hint_policy_value(cap_by_hint, hints_used)` | `fact_predicates.fsrs_cap_value` (moved verbatim; binning, cap parsing and its error stay) |
| `diagnosis/split/history.py::history_attempt_from_blind_record` | `bool(hints_used) or attempt_type in ASSISTED_ATTEMPT_TYPES` | `diagnoser_assisted(submitted_facts(...))`; `ASSISTED_ATTEMPT_TYPES` is `DIAGNOSER_ASSISTED_TYPES` |
| `diagnosis/split/history.py::VaultHistoryStore._from_stored` | the same over `row.get("hints_used")` | `diagnoser_assisted` |
| `teacher/brief.py::_cold` | `type in _COLD_TYPES and not primed and not hints_used` | `unhelped_cold_type` |
| `teacher/brief.py::_history` | inline `cold / assisted / primed / type` | `teacher_attempt_kind` |
| `teacher/brief.py::_delayed_result` | `row[3] in _COLD_TYPES and not row[4] and not row[5]` | `unhelped_cold_type` |
| `daily_plan/lesson_suggestion.py::_cold` | cold type (lesson weight's list), unprimed, no hint, graded | `graded_cold_check(..., COLD_ATTEMPT_TYPES)` |
| `daily_plan/router_card.py::CardGatherer._learning_objects` | `int(hints_used or 0) > 0 or bool(primed)` | `hinted_or_primed` |
| `daily_plan/router_card.py::CardGatherer._recent_work` | `"assisted": bool(row.get("primed"))` | `primed_only` |
| `learner_context.py::_traces` | `"assisted": bool(row.get("primed"))` | `primed_only` |
| canonical policy (`attempt_counts_as_assisted`, `classify_attempt_activity`, `_resolve_...`, `gate_unverified_reference`) | | delegated: `counts_as_assisted`, `recorded_counts_as_assisted` |
| `substrate/intervention_outcomes.py::is_assisted` | | delegated: `intervention_assisted` |
| `attempts/coldness_receipt.py::_evaluate` (`_unassisted`) | | delegated: `unassisted_for_coldness` |
| 16 callers of the owners above (certification's stored flag, the scheduler's two, the scoreboard, the projection, the facet timeline, the field, FSRS's four other callers, intervention outcomes' own `outcome_for` and three other `is_assisted` callers, the attempt path's classification writer) | | named, unchanged |
| 41 readers with their own expressions | | not adapted, each with its reason in the census |

## 4. Predicate ownership

| Named predicate | Owner | Readers |
|---|---|---|
| `counts_as_assisted` | `diagnosis.causal_activity_policy` (`causal_activity_v1`) | certification's stored flag, the scheduler's "on your own", the scoreboard |
| `recorded_counts_as_assisted` | the same | the projection, the facet timeline, the field (stored `assisted`) |
| `intervention_assisted` | `substrate.intervention_outcomes` | next_assisted, the Reader's report and follow-ups, valuation |
| `unassisted_for_coldness` | `attempts.coldness_receipt` | the coldness receipt's dimension |
| `fsrs_cap_value`, `fsrs_rating_cap` | `attempts.attempts` (grade application) | the grade application, replay, fitting, evaluation, Reader follow-ups, the field |
| `diagnoser_assisted`, `diagnoser_cold_unassisted` | `diagnosis.split.history` | the diagnoser's history and its "demonstrated" |
| `unhelped_cold_type`, `teacher_attempt_kind` | `teacher.brief` | the teacher's brief |
| `graded_cold_check` | `daily_plan.lesson_suggestion` (types: `learner.lesson_weight`) | the lesson suggestion (equal, in SQL: lesson weight's qualifying outcomes, the miss cause's filter) |
| `hinted_or_primed` | `daily_plan.router_card` | the card's per-LO count |
| `primed_only` | `daily_plan.router_card`, `learner_context` | the card's recent work, the chat packet's traces |
| `help_timing`, `category` | `adaptive_difficulty.outcomes` (not here) | AD's replay, scoring and the randomized check's label |

The search behind the census's inline rows: every `src/` line where `hints_used` meets `primed`, `> 0`, `not`,
`bool(` or `or`/`and` (`grep -rn hints_used src | grep -E 'primed|> 0|not .*hints_used|bool\(.*hints_used|or |and '`),
excluding the submit path's folds and writes, renderings of stored flags and evidence weights.

## 5. Discrepancy ledger

Where two readers answer what looks like the same question differently. None is resolved here.

| Id | Readers | How they differ | Status |
|---|---|---|---|
| D-1 | the canonical test; the router card's per-LO count; the card's recent work and the chat packet's traces | "assisted" is a legacy assisted type, a hint or primed (canonical); a hint or primed, any type (card count); primed alone, with the hint count in the next field (both packets) | Deliberate until EP4: the spec (§3.1, §8 EP4) records the packets' primed-only field and moves every packet onto the facts there; the sheet says keep today's rendered values until EP4 |
| D-2 | intervention outcomes' `is_assisted`; the router's `INDEPENDENT_ATTEMPT_TYPES`; AD's `ELIGIBLE_TYPES`; the field's `GRADED_RETRIEVAL_TYPES` | `open_text` and `diagnostic_probe` answers are assisted for intervention outcomes (only `independent_attempt`, `dont_know`, `exam_attempt` are unaided, the field's graded retrieval types) but independent for the router's R_next and eligible for AD | Deliberate: documented at `intervention_outcomes.UNAIDED_TYPES`; owner decision K5-4 keeps the research rules apart |
| D-3 | the coldness receipt's `unassisted`; the teacher's and lesson suggestion's cold checks; the cold verification preconditions | the receipt fails on any recorded reveal of the cold item in its window, below the 0.35 auto-prime threshold too; the others read only the submitted flags (a reveal under the threshold leaves `primed` false) | Deliberate: documented at `coldness_receipt._unassisted` (the single-use cold measurement takes the tighter rule) |
| D-4 | the diagnoser's `assisted`; the canonical test | the diagnoser's `assisted` leaves `primed` out (its own field); its `cold_unassisted` (neither) equals canonical-unassisted on the whole matrix | Deliberate (the sheet: "its separate assisted and primed meanings remain separate"); its prompt does not define them (spec §3.1), which is EP4's |
| D-5 | `qualifies_as_cold_retrieval`; `_qualifies_for_field_memory_retrieval`; `_passes_intervention_coldness_checks`; placement's receipt veto | three cold rules: the receipt's claim (delay, unassisted, leakage, isolation), the field's (no delay requirement, every final receipt's interval and two dimensions), intervention outcomes' (unaided, one-day window, no topic delay reset) | Deliberate: owner decision K5-4 (`docs/reviews/owner-decisions-small-1.md`) |
| D-6 | certification's consumption gate and `diagnosis.remediation.assisted_attempt`; certification's stored `assisted`; the forecast ledger's cold outcomes | the gate and `assisted_attempt` count a hint, the `hinted_attempt` type or primed, not `guided_walkthrough` or `reconstruction_after_walkthrough`; the stored flag is the canonical test, which counts both; the forecast ledger drops `hinted_attempt`, `guided_walkthrough` and `self_report` but not `reconstruction_after_walkthrough`. A `reconstruction_after_walkthrough` answer to a cold probe would consume the probe and be stored `indeterminate`/`assisted_probe`, where a `hinted_attempt` answer leaves the task open | Unexplained: question 1 |
| D-7 | the teacher, lesson suggestion, miss cause and placement ("cold"/"clean" types); the field and intervention outcomes (graded retrieval/unaided); AD and the router | the cold types are `independent_attempt`, `open_text`, `diagnostic_probe`, `exam_attempt` for the teacher, the lesson suggestion, the miss cause and placement; `independent_attempt`, `dont_know`, `exam_attempt` for the field and intervention outcomes; AD and the router add `dont_know` (and AD `hinted_attempt`) to the first set | Unexplained as a whole: question 2. Each set is documented at its reader |

No row is a defect found by this step: nothing was added to `docs/reviews/refactor-bug-ledger.md`.

## 6. Evidence that old outputs and identities are unchanged

- **Characterized before any move.** `tests/test_attempt_predicate_characterization.py` was committed first
  (`5c06ec99fd`) and run against the unadapted readers (`6 passed`): each reader's own function on the matrix (14
  attempt types including missing and empty x 5 hint counts x 5 primed values x 4 grades = 1,400 rows; the coldness
  dimension also x 5 reveal scans; the FSRS cap 7 cap maps x 6 scores x 6 hint counts) equals a verbatim copy of its
  expression, and the sha256 of each reader's outputs on the whole matrix is pinned (`DIGESTS`). After the adaptation
  the same seven digests hold.
- **Moved kernels are node for node.** `tests/test_attempt_fact_predicates.py` compares each moved kernel's AST with
  the reader's expression as it stood (`tests/attempt_predicate_helpers.py::BASE_SOURCES`), the row reads mapped onto
  facts reads: `fsrs_cap_value` (the function), `diagnoser_assisted`, `unhelped_cold_type`, `graded_cold_check`,
  `teacher_attempt_kind`, `hinted_or_primed`, `primed_only`.
- **Every named predicate equals its reader** on the matrix, the recorded classification included.
- **Identities.** `tests/test_identity_pins.py` passes after every source commit; `tests/goldens/identities.toml` and
  `identity_shapes.toml` are untouched. No new type reaches a hash, seed, manifest or prompt (the adapters return the
  old scalars; no `asdict` of the facts in `src/`).
- **Goldens.** The diagnosis journey, due-queue and grade-application goldens pass unchanged (section 8).
- **Grader blindness.** The new contract and `tests/test_attempt_fact_predicates.py`: no grading module imports the
  facts or the predicates, and neither grading context has a field for them.

## 7. The collector's reads

On a synthetic vault (60 attempts on one item, each with a help row, a reveal, a question and a plan presentation),
through the scratch wrapper:

| Read | N=1 | N=10 | N=60 |
|---|---|---|---|
| `collect_facts`, connection reader | 8 SELECTs, 3.9 ms | 8, 4.1 ms | 8, 6.4 ms |
| the same facts by per-attempt reads (`help_assists.submission_assists` and one question, reveal and presentation read each) | 5, 3.6 ms | 41, 3.8 ms | 241, 5.9 ms |
| `collect_facts` through the material view | 17 SELECTs, 75.7 ms (the view's own first reads) | | 8, 19.3 ms |

The count is fixed per call (`tests/test_attempt_facts.py::test_the_collector_reads_a_fixed_handful_whatever_the_number_of_attempts`).
No production reader calls the collector yet.

## 8. Commands and results

All through the scratch wrapper; every pytest run in a 3G memory scope at `-n 1` with explicit targets from a script
file. Name filter for the affected set (`scripts/affected_tests.py` lists 1,021 files): the brief's names (`coldness`,
`cold_`, `assist`, `reveal`, `hint_fold`, `intervention`, `causal`, `fsrs`, `grade_application`, `eligib`,
`material_view`, `blind_grading`, `due_queue`, `diagnosis_journey`, `evidence_cutoff`: 49 files), the affected files
named for the adapted readers (`router_card`, `lesson_suggest`, `learner_context`, `teacher_te0`, `history_modes`,
the new files: 10), and every test file importing an adapted module (`learner_context`, `lesson_suggestion`,
`teacher.brief`, `router_card`, `split.history`, `split.context`: 65).

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile --extra tui`; `uv pip install --offline pypdfium2==5.14.0` | installed |
| `pytest tests/test_attempt_predicate_characterization.py` on the unadapted readers (before any move) | `6 passed in 1.80s` |
| `pytest tests/test_attempt_facts.py` (collector) | `20 passed in 11.51s` |
| `pytest tests/test_identity_pins.py tests/test_structure_ratchets.py` with the coldness kernel moved | `1 failed, 383 passed`: `modules_in_an_import_cycle` 221 > 220 (the kernel went back; section 1 item 2) |
| the same after the kernel went back | `383 passed in 35.86s` |
| `pytest -m "not arc_close"` brief chunk 1 (25 files) | `447 passed in 86.51s` |
| `pytest -m "not arc_close"` brief chunk 2 (24 files) | `714 passed in 36.28s` |
| `pytest -m "not arc_close"` chunk 3 (the 4 new files, `test_diagnosis_history_modes`, `test_router_card`, `test_router_card_reading_gaps`, three `test_teacher_te0_*`, and 30 importers) | `771 passed, 4 xfailed in 448.30s` |
| `pytest -m "not arc_close"` chunk 4 (35 importers) | `659 passed in 310.76s` |
| `pytest` the four new files, `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards`, `test_retired_config_identities` | `461 passed in 92.60s` |
| `pytest tests/test_test_layout.py` (alone) | `3 passed in 21.40s` |
| `pytest tests/test_architecture.py` (alone) | `18 passed in 31.53s` |
| `python scripts/check_gate_partition.py` | `collected 32243: landing 32178 + arc_close 65` |
| `ruff check` | `All checks passed!` |
| `lint-imports --no-cache` | `Contracts: 45 kept, 0 broken.` (44 + the new grader contract) |
| `git diff --check` (base..head) | clean |

The 4 xfails are existing strict xfails in the importers; none was added or changed.

## 9. Not checked

- The landing gate, the arc-close gate, the durability lane, and the P-shadow/P-draw lanes (the orchestrator's).
- The full affected set (`scripts/affected_tests.py` lists 1,021 files for the changed modules); the name filter used
  is in section 8.
- A withheld *revision* of a visible item: the withheld-material test withholds an item (its attempts, help rows,
  questions and reveals, and a question and a reveal on a visible attempt that name it); building a held-out revision
  needs held-out source material and revision snapshots, not built here.
- Owner data: no vault was opened, so how many stored attempts have `count_only` help or disagreeing counts is not
  known.
- The historical-default columns (`declared_*` before their migrations) are labelled in the coverage note, not
  detected per row.

## 10. Questions

1. **D-6.** Should a cold probe's consumption gate (and `remediation.assisted_attempt`) count the walkthrough types
   as the stored flag does, so that a `reconstruction_after_walkthrough` answer leaves the probe open like a hinted one,
   or is consuming it as `indeterminate` intended? Also the forecast ledger's type list.
2. **D-7.** Is `open_text` a cold/unaided answer (teacher, lesson suggestion, placement, AD, router) or not (field,
   intervention outcomes), and is `dont_know` one? Each reader documents its own set; nothing says the difference is
   meant.
3. **Where the canonical test lives.** Delegating to it needs a frozen-cycle exemption. Should the dependency-neutral
   part (`contamination_class_for_attempt`, `classify_attempt_activity`, `attempt_counts_as_assisted`) move to the
   top-level `learnloop.causal_activity_policy` beside `policy_for_class`, which would remove the exemption?
4. **The back-edge readers.** Adapting certification's, placement's, the forecast ledger's and the field's
   expressions needs a frozen-cycle exemption each (goals, placement, learner, substrate import `learnloop.attempts`
   only through exempted edges). Adapt them with exemptions in a later caller group, or leave them named?
