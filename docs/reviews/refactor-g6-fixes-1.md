# G6 fixes, round 1: six protection defects

Ledger rows G6-P3, P2, P7, P6, P1 and P5 (`docs/reviews/refactor-bug-ledger.md`, "From G6"), steps G6.4 to G6.9 of
`docs/reviews/refactor-g6-design.md`, on `fix/g6-protection-defects` from the batch tip `cedd072ed3`, one commit
per defect in that order (G6-P6 has a follow-up commit, below). Each fix turned its strict xfail in `tests/test_protection_surface_matrix.py` green;
the pinned cells or "today" tests that held the old answer were moved to the new answer in the same commit, and
the rest of the matrix (1,502 cells, 100 fault cells, 30 reach cells) stayed as pinned after every commit, apart
from the cells named below. No migration, algorithm tag, config key or identity pin: `tests/test_identity_pins.py`
passed (342) after each of the six commits. No stored row is rewritten; every change is in what is sent to a model
or delivered from now on.

## Per defect

### G6-P3: the Reader's same-span thread (`36eb128ae8`)

- **Before.** With `reader_inquiry` off, `reader_dialogue.ask` left the thread to `tutor_qa._thread`, which sent
  every earlier answer on the same span as stored (`delivered_answer_md`). A direct `tutor_qa.ask_question`
  caller (context `reader`) did the same. An answer that quoted a passage held out since reached the model again.
  Who could have seen what: the tutor model, on the desktop (held-out text) and the phone (exam text); never the
  learner (the answer was theirs already).
- **After.** Each earlier answer of the same-span thread is judged by the passages its question row records
  (`tutor_qa.reader_answer_places`: the anchor, every passage the tutor was given, citations, the excerpt, the
  retrieved keys) under the destination's material (`reader_held_out`: held out on the desktop, joined with exam
  material on the phone); one naming a withheld passage, or whose row records none, is sent as the branch
  ancestors' placeholder (`tutor_qa.READER_ANSWER_WITHHELD`, the same words as `reader_dialogue.
  ANCESTOR_ANSWER_WITHHELD`, which now aliases it). The learner's question stays; the manifest's
  `prior_exchanges` records the thread as the tutor read it. A failing protection read raises (refuses).
- **Files and functions.** `tutor/tutor_qa.py`: `_thread` (new `reader_withheld`), `reader_answer_places`,
  `sendable_reader_answer_md`, `READER_ANSWER_WITHHELD`; `ask_question` passes `reader_held_out`.
  `reader/reader_dialogue.py`: `build_reader_manifest` (legacy prior list), `ANCESTOR_ANSWER_WITHHELD`.
- **Why a new provenance reader.** `reader_dialogue.ask_provenance` (which judges branch ancestors) reads the
  `reader_answer_submitted` interaction event; a direct `tutor_qa.ask_question` caller writes only the question
  row, so that function cannot serve it, and `tutor_qa` sits below `reader_dialogue`. The predicate is the same
  (`Material.covers`).
- **Tests.** `test_a_reader_thread_leaves_out_an_answer_grounded_in_held_out_material[legacy-thread]` (the old
  xfail; red before at its own assertion) and `[branch]` (inquiry on: a follow-up's ancestor, already filtered,
  regression proof); `test_a_reader_thread_keeps_an_answer_whose_passages_stay_admissible`;
  `test_a_direct_reader_question_leaves_out_an_earlier_answer_grounded_in_held_out_material` (the direct caller;
  the stored row is unchanged); `test_an_earlier_reader_answer_with_no_recorded_passages_is_left_out` (fail
  closed). `test_a_legacy_reader_thread_sends_an_answer_grounded_in_a_passage_held_out_since` (today's pin) is
  removed.
- **Cells moved.** None (the defect had no matrix cell; RA and PA are unchanged).

### G6-P2: the pinned tutor's finished job (`1d640db037`)

- **Before.** `reader.library_ask_tutor` started its job with no `deliver`, so `reader.library_job` returned a
  finished answer as kept, whatever was marked since. Who: the desktop learner, on every poll of a finished job
  (the answer quoting a passage held out or made exam material since).
- **After.** The job carries `deliver_tutor`, run at every read: the result's `grounded_keys`, its citations and
  the passages its stored question row names (`reader_answer_places`) go through `library_ask.refuse_withheld`
  (exam material, fail closed: the same check and wording, `RESULT_WITHHELD`, as the kept ask and notes jobs); a
  row naming none refuses. The kept result and the stored question and `reader_answer_submitted` rows are
  unchanged. Not `deliver_passages`: its `hits`/`notes` shape names nothing of a tutor result.
- **Files and functions.** `learnloop_sidecar/handlers/library_ask.py`: `deliver_tutor`, `reader_library_ask_tutor`.
- **Tests.** `test_a_completed_pinned_answer_is_refused_once_its_passage_is_held_out` (the old xfail, now also
  asserting the code, the wording and that the kept result and rows are unchanged; two polls);
  `test_a_completed_pinned_answer_still_returns_while_its_passages_stay_readable` (replaces today's pin
  `test_a_completed_pinned_answer_is_returned_after_its_passage_is_held_out`);
  `test_a_completed_pinned_answer_is_refused_when_protection_cannot_be_read` (fail closed).
- **Cells moved.** None (TJ is not driven per row).

### G6-P7: the exercise author's neighbours (`10a5933a53`)

- **Before.** `exercise_authoring._context_blocks` added one block each side of the selection with no check, so a
  safe exercise beside a protected unit sent that unit's block to the author: the Reader's import (held-out
  neighbours) and the canonical import (exam or held-out neighbours). Who: the authoring model.
- **After.** `author_exercises` (and `import_exercises`) take `context_withheld`, the caller's set: the Reader's
  job passes `exam.held_out`, the canonical import `exam.material`; a caller naming none gets the Reader's
  (`held_out_material`). A selected block it covers refuses the request (`ExerciseAuthoringError`, "this exercise
  is exam or held-out material now, so it never becomes practice", the canonical import's words); a covered
  neighbour is left out of `context_blocks`. Both happen before the author call, and so before the method judge
  (which runs after the author). Figures come from selected blocks only (refused when covered); the canonical
  import's book solution already passes its own exam check (`find_book_solution`).
- **Files and functions.** `content/authoring/exercise_authoring.py`: `_context_blocks`, `author_exercises`,
  `import_exercises`; `content/pipeline/jobs.py`: `handle_reader_exercise_import`;
  `content/authoring/source_exercise_import.py`: `import_source_exercise`.
- **Tests.** `test_the_reader_imports_author_never_sees_a_held_out_neighbour`,
  `test_the_canonical_imports_author_never_sees_an_exam_neighbour` (the old xfails; red before);
  `test_the_reader_imports_author_keeps_a_safe_neighbour`, `test_the_canonical_imports_author_keeps_a_safe_neighbour`;
  `test_the_shared_author_refuses_a_protected_selected_segment_before_any_call`.
- **Cells moved.** RN S→W: 3.held, 3.camel, 6.3canonical, 6.3block, 9.switch-off. CN S→W: 2.exam, 2.split-exam,
  3.held, 3.camel, 6.2canonical, 6.2block, 6.3canonical, 6.3block, 9.switch-off. RN stays S for 2.exam,
  2.split-exam, 6.2* (exam-only, admissible to the Reader, D2). **RI 3.camel S→R** (outside this row): the author's
  own final check now refuses the camel-case held-out selection the job missed, so G6-P6's strict xfail passed
  here and its mark came off in this commit.
- **Left as S, against the ledger's scenario: RN and CN for 5.signal, 6.5canonical, 6.5block.** The block beside
  the selected theory exercise that carries the fixture's marker is the exam unit's heading; the held-out signal
  names one span (the exam exercise), not the heading, so no predicate covers it and it is kept. The protected
  span itself is two blocks away and never in the context. Not ledgered: a unit heading is a title, and the
  owner's rules hold out what the signal names; flagged here for the owner.

### G6-P6: one selection for the Reader's import (`6282c9f84f`, follow-up `bd38966aef`)

- **Before.** The job's held-out check read `node.get("span_id")` only; the author also reads `spanId`, a render
  view's display node and a quote it re-anchors. After G6-P7 the camel-case case was refused by the author's own
  check, but as `invalid_job` with other words; the scope check and the provenance rows parsed raw keys again.
- **After.** `handle_reader_exercise_import` asks the author's module which blocks it will read
  (`exercise_authoring.selected_span_ids`, the same `_anchored_segments` that `author_exercises` reads: the
  translation with the payload's `render_view_id`, segments with text), checks those blocks against the held-out
  partition before anything is sent, and reads the same blocks for the syllabus scope check and for
  `_record_reader_import_keys` (now given `span_ids`, no raw-key parser in the job). `span_id`, `spanId` and a
  display-node selection refuse identically (`exam_material`, the job's existing wording and details), with no
  author call. The author translates again for itself (deterministic, same inputs) and keeps G6-P7's final check.
  The first commit called `reader.annotations.translate_selection` from the job, a new function-local
  cross-domain edge that `tests/test_architecture.py` refuses; the follow-up commit routes it through the author's
  module instead (no new edge, one translation function for check and author).
- **Files and functions.** `content/pipeline/jobs.py`: `handle_reader_exercise_import`,
  `_record_reader_import_keys`; `content/authoring/exercise_authoring.py`: `_anchored_segments`,
  `selected_span_ids`, `author_exercises`; `tests/test_plan_first_transport_grant_scope.py` (the new keyword).
- **Tests.** `test_a_camel_case_selection_of_held_out_material_is_refused_before_the_author` (the old xfail; red
  before G6-P7 at its assertion, as the G6.1 record and the runs before G6-P7 show);
  `test_every_spelling_of_a_held_out_selection_is_refused_alike_before_the_author` (red on the code before this
  commit: `invalid_job` versus `exam_material`).
- **Cells moved.** None in this commit (RI 3.camel moved with G6-P7).

### G6-P1: figure prebuilds and exam reservations (`56c823ba2e`)

- **Before.** `figures.protection.item_passages` withheld the own passages of cold, assessment-reserved and
  probe items and of the plan's open items; an item a goal's exam pool reserves carries the exam reason, so it
  was not among them, and one made from a clean book passed the span filter too. Who: a prebuild's model (its
  exercise and solution as a figure's input), and the learner through the figure.
- **After.** The current reservations (`repository.reserved_exam_pool_item_ids`, unreleased rows only, not every
  exam-withheld item) join the set; a released reservation admits the passage again; a read that fails returns
  None (every prebuild withheld), as the function's other reads do.
- **Files and functions.** `figures/protection.py`: `item_passages`, the `LIVE_ADMINISTRATION_REASONS` comment.
- **Tests.** `test_an_exam_reserved_items_own_passage_is_withheld_from_figure_prebuilds` (the old xfail; red
  before); `test_releasing_an_exam_reservation_admits_its_items_passage_to_figure_prebuilds`;
  `test_figure_prebuilds_are_all_withheld_when_exam_reservations_cannot_be_read`.
- **Cells moved.** IP 6.exam-reserved S→W; no other.

### G6-P5: a key naming no passage (`d65396911c`)

- **Before.** `library_ask.withheld_now` asked only whether each key was exam material, so a well-formed key
  naming no reading, or no block of a reading, passed: the kept job was returned and the organizer judged (an
  empty pool), against its own fail-closed docstring.
- **After.** `withheld_now` also resolves every key to a stored block (`blocks_by_key`, the passages reader the
  module already uses); a key with none, or a read that fails, is withheld. Every caller refuses the whole
  result through it: the kept ask and notes jobs (`deliver_passages`), the organizer before its cached return
  and before judging (`organize`), and the pinned tutor's guard (G6-P2).
- **Files and functions.** `source_retrieval/library_ask.py`: `withheld_now`.
- **Tests.** `test_a_kept_answer_naming_a_passage_that_does_not_exist_is_refused[extraction]` (the old xfail) and
  `[span]` (a real reading, no such block), each: the kept job on two reads, the organizer fresh and with stored
  notes; `test_a_kept_answers_existing_passages_still_pass_the_check` (an existing clean key passes; a failing
  read withholds). All three red on the code before this commit. Today's pin
  `test_a_kept_answer_naming_a_passage_that_does_not_exist_is_returned` is removed.
- **Cells moved.** None (OR and LJ are S for every existing clean target, as pinned).

## Judgment calls

1. **G6-P2's set is all exam material, not the held-out partition.** The pinned tutor already drops an exam-only
   pin (PT is W where RA is S), and the kept ask and notes jobs judge by exam material; the guard reuses that
   check (`refuse_withheld`). Consequence: a pinned tutor job whose first pin (its anchor) is exam-only material
   is refused at its first read. The library never offers such a pin (its search leaves exam material out); a
   hand-made request could.
2. **G6-P3 reads provenance from the question row** (above), and a row without `source_spans` (written before the
   tutor recorded them) now reads as the placeholder: fail closed, so a very old same-span thread loses its
   earlier answers in the model's context (not on screen).
3. **G6-P7: a caller naming no set gets the Reader's** (`held_out_material`), so no direct caller of
   `author_exercises` is unprotected.
4. **G6-P7 moved RI 3.camel** before G6-P6, and the 5.signal heading is left as S (above).
5. **G6-P6 records the translated blocks as the import's provenance**: for a selection whose every node
   anchors, the same spans as before; a node that cannot be anchored (never authored) is no longer recorded.

## What was run

Every pytest under the empty-environment wrapper (`env -i`, empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`),
`-n 1`, in a 3 G scope, one command at a time, targets from a script file.

- Each defect's strict xfail with `--runxfail` before its fix: failed at its own assertion (P3 `not
  model.carried("GSIXCLEANRES")`; P2 and P5 `DID NOT RAISE SidecarError`; P7 both `'S' == 'W'`; P1 `'S' == 'W'`;
  P6 was seen as a strict xfail in every run before P7, then passed through P7's final check, see above). The new
  proof tests of P6 and P5 were also run on the code before their commit (file checked out, run, patch reapplied):
  red at their assertions.
- After each commit: its own tests; the module's neighbouring files (P3: matrix plus 9 Reader, tutor and exam
  files, 331 passed, 6 xfailed; P2: 28 library and tutor files, 931 passed, 5 xfailed; P7: 25 authoring and
  import files, 1071 passed and 4 failed (the RI, RN and CN matrix rows and P6's strict xfail, which led to the
  cell corrections above), then the matrix alone 146 passed, 2 xfailed; P6: 31 files, 1172 passed, 2 xfailed; P1: 9 figure files,
  314 passed, 1 xfailed; P5: 38 library files, 1092 passed); `tests/test_identity_pins.py`: 342 passed each time;
  `ruff check` on the changed files: all checks passed; after P7 `lint-imports --no-cache`: 43 kept, 0 broken.
- Before the report, at the tip (after the G6-P6 follow-up):
  - `tests/test_protection_surface_matrix.py`: 152 passed in 47.45 s (no xfail left).
  - The G6.1 proof dependencies (`test_mobile_v4_codex_review`, `test_exam_protection`,
    `test_exam_protection_identity`, `test_k1_source_sets_gate`, `test_k1_remediation_cold_reservation`,
    `test_k1_mcp_find_sources`, `test_k1_serve_door_reservation`, `test_learner_protection_predicates`,
    `test_library_ask_review`): 169 passed in 38.17 s.
  - Edited test files besides the matrix (`test_plan_first_transport_grant_scope.py`): 10 passed.
  - `scripts/affected_tests.py --files <the 8 changed src files>`: 813 files, so the brief's name filter: 199
    files in five chunks of at most 40, each `-m "not arc_close"`: 650, 843, 515, 793 and 589 passed (3,390), no
    failure.
  - `tests/test_identity_pins.py`: 342 passed. `tests/test_structure_ratchets.py`: 3 passed.
    `tests/test_test_layout.py` alone: 3 passed. `tests/test_architecture.py` alone: 18 passed.
  - `ruff check`: all checks passed. `lint-imports --no-cache`: 43 kept, 0 broken.
- The first full pass at the tip found `tests/test_architecture.py::
  test_function_local_domain_imports_match_the_frozen_edge_inventory` failing (the job's new
  `reader.annotations` edge); the G6-P6 follow-up removed it, and the whole list above was run again on it.

## Not verified

- No frontend or phone client: the refusals' wording was not seen in a client (each reuses an existing message).
- G6-P3 on the phone: the phone's set reaches `_thread` through `reader_held_out` (K6-4's join), but no phone test
  drives a legacy thread. A selection's extra spans are judged through the row's `source_spans`; a selection span
  the context budget dropped is not named by the row (the question row stores no selection list).
- G6-P2 with source sets unreadable (only the predicate raising was driven) and with a bound workbench ask.
- G6-P7 for figure blocks or auxiliary text beside a protected neighbour beyond the selection (figures come from
  selected blocks; the book solution has its own check, not re-tested here).
- G6-P6 with a render view whose crosswalk names a different block than the node's own `spanId` (both given).
- The affected files' `arc_close` tests (excluded from the chunks), G6-P4 (not in this round), and the landing
  and arc-close gates.
