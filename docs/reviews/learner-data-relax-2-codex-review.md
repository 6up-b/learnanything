# Learner data-relax 2: Codex review and fixes

Review: Codex (gpt-6.1-sol), job `20261101-175006-SUU1Dg`, on branch
`learner/data-relax-2` at 81d570b42e. Two High findings, both about
exam-material protection of the learner state the figure author is sent.
Fix step: Claude Opus 5.5, 2026-11-01. Fakes only, no live calls, no paid calls.

## Findings

| id | severity | title | verdict | commit | test or reason |
|----|----------|-------|---------|--------|----------------|
| F1 | High | Reading-derived gaps bypass source protection | fixed | 1102ce5184 | `test_a_reading_derived_gap_is_checked_against_the_passage_it_was_written_beside`, `test_protection_unreadable_withholds_reading_derived_gaps_too` |
| F2 | High | Delayed rich jobs send learner work that has become protected | fixed | 1102ce5184 | `test_a_queued_rich_job_never_sends_an_answer_whose_item_became_exam_material`, `test_a_rich_job_stops_when_an_input_becomes_protected_while_it_runs`, `test_a_queued_rich_job_with_learner_state_stops_when_the_switch_goes_off`, `test_a_saved_learner_state_with_no_record_of_its_inputs_is_never_sent`, `test_the_switch_is_in_the_build_and_rich_keys` |

All tests are in `tests/test_learner_data_relax_2.py`. I reproduced both
findings first. With the new tests in place and the four source files reverted
to 81d570b42e (plus a one-line import shim for `read_learner_state`), all 7 new
tests failed and the 9 existing ones passed. With the fix, all 16 pass.

### F1: what was wrong and what changed

`figures/learner_state._gap_statements` checked a gap only through its
`attempt_id` and `practice_item_id`. Gaps from active-reading answers and
figure predictions (`reader_formative`) have neither, so their words were sent
whatever passage they were written beside. That included an exam passage, a
passage reclassified as exam material, a gap with no record at all, and the
case where the protection could not be read. The reproduction showed all of
these: the exam gap, the unrecorded gap and the unreadable-protection case
each sent the statement.

Fix (`src/learnloop/figures/learner_state.py`):

- `_gap_inputs` combines the gap's own answer and item with what its
  write-time record says it was written from (`write_provenance.stored_record`,
  kind `learner_text_gap`): answers, items, learner questions and passages.
  A gap whose record is incomplete is left out, because its inputs cannot be
  established. So is a gap with no answer, no item and no record.
- `inputs_reason` is the single check. It uses the shared protection
  (`PastWork.evidence_reason` for answers and items, `question_reason` for each
  learner question, `source_reason` for passages). If the protection cannot be
  read, that counts as a reason to withhold (fail closed).
- `read_learner_state` returns no statement and no answer when
  `PastWork.withheld` is unavailable, whatever the statements were written
  from. Only the topic statuses remain.
- Deliberately not a reason: a writer having read a rubric or worked solution
  (`solution_items`). That is not exam, held-out, reserved or cold-in-flight
  material, and the items' own protection already covers those four. This is
  recorded in the `inputs_reason` docstring.

### F2: what was wrong and what changed

The rich job's durable payload carried the saved `learner_state` inside
`author_context`, but nothing about what that state was read from. At run or
resume time `rich.py` checked only the passage manifest and sent the saved
context unchanged. Two consequences:

- An answer whose item became exam material after the job was queued was
  still sent. The reproduction showed the job completing with the rich author
  called.
- The new switch was in neither gate key, so a queued job still sent its saved
  state after `figures.author_learner_state` went off.

Fix:

- `read_learner_state` returns `LearnerStateRead(state, inputs)`. `inputs` is
  `Inputs.as_json()` of every answer, item, question and passage behind what
  the state shows. It is never sent to a model.
  `FigureRequest.learner_state_inputs` carries it, and `_RichSpawn.payload`
  adds `learner_state_inputs` to the job payload. That payload is also the
  quick figure's durable rich intent, so the inputs persist with the job and
  with the figure that resumes it.
- `run_rich_job`, when the saved context carries learner state:
  - It stops with `figures_changed` if the switch is off now.
  - It stops with `exam_material` if anything the state was read from is
    protected now (`learner_state.inputs_withheld`, against the database and
    vault as they are now). A saved state with no inputs record is treated the
    same way (fail closed).
  - The job's gate key includes the switch.
  - The gate gets a `hold`, a new optional `FiguresGate` parameter in
    `figure_admission.py`. It re-runs the inputs check against the reloaded
    vault before every rich model request and at the `store` check, so the
    job stops with `exam_material` if an input becomes protected mid-job.
- `service.build_key`, the quick author's live admission key, now includes
  `author_learner_state_enabled`. Toggling the switch mid-build stops the
  build, the same way the advanced-panels switch already does.

How "delivery" is read: for the rich job, delivery is its store step, and that
is gated. Stored figures are not re-gated on later reads. A figure explains
its passage, the author is told never to quote the learner's answers, and
nothing about the learner state is shown with it. That matches how quick
figures are already handled.

## Gate (fix step)

Owner rule of 2026-10-17: no full suite, whole durability lane or whole vitest
run in this step. Every test command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at
`-n 6`, with TMPDIR in the session scratchpad.

- `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **37 kept, 0 broken**.
- `uv run pytest -n 6 tests/test_learner_data_relax_2.py`: **16 passed**.
  Against the pre-fix source the same file gave 7 failed and 9 passed (the
  reproduction).
- Targeted lane, `uv run pytest -n 6 -p no:randomly <files below>`:
  **931 passed, 0 failed** (221.7 s).
  - Every `tests/test_figure*.py` and `tests/test_figures*.py`. These exercise
    `figures/service.py`, `figures/rich.py`, `figure_admission.FiguresGate` and
    the rich job and its recovery.
  - `tests/test_learner_data_relax_2.py`
  - `tests/test_sketch_service.py`
  - `tests/test_learner_text_gaps.py`, `tests/test_learner_text_gaps_flow.py`
    (FiguresGate in the gap jobs)
  - `tests/test_architecture.py`
  - `tests/test_reader_followups.py`, `tests/test_reader_followups_successor.py`
  - `tests/test_router_card.py`, `tests/test_mcp_c1a_review.py` (the shared
    protection's other readers)
  - `tests/test_diagnosis_input_provenance.py` (`write_provenance`)
- Not run, because nothing they cover changed: migrations and durability (no
  schema, migration or connection code changed), frontend and cargo (no
  `apps/` change), DB reference scripts (no schema change), config defaults
  snapshot (no config key added).

## Open items

- The router card (`daily_plan/router_card.py`, outside this stage) checks a
  learner-text gap only by its attempt and item, the same pattern F1 fixed
  here. A reading-derived gap's words can therefore reach the router model
  even when its passage is exam material. This predates this stage and is not
  changed here. It is a candidate for a follow-up that reuses
  `learner_state.inputs_reason`.

## Re-review

Re-review: Codex (gpt-6.1-sol), job `20261101-180806-ZroakT`, on c6c4c6c204.
It confirmed F1 fixed and reopened F2. It found no new defects in the fix
commits. Fix step: Claude Opus 5.5, 2026-11-01. Fakes only, no live calls,
no paid calls.

| id | severity | title | verdict | commit | test or reason |
|----|----------|-------|---------|--------|----------------|
| F1 | High | Reading-derived gaps bypass source protection | confirmed fixed by the re-review | 1102ce5184 | no change |
| F2 | High (reopened) | A recovered rich job returns its stored figure without rechecking the learner state, and the rich row does not keep that state's inputs | fixed | 6d8062f919 | `test_a_recovered_rich_job_rechecks_its_stored_figures_learner_state` (the post-commit recovery regression), `test_a_rich_figure_keeps_the_inputs_of_the_learner_state_it_was_written_from`, `test_a_rich_figure_whose_learner_inputs_became_protected_is_not_delivered`, `test_a_rich_only_figure_whose_learner_inputs_became_protected_is_never_reused`, `test_a_stored_rich_figure_without_learner_state_is_checked_as_before` |

### F2 (reopened): reproduction

I added the five tests above to `tests/test_learner_data_relax_2.py` and ran
them against `rich.py` and `service.py` as of c6c4c6c204: all 5 failed and the
16 existing tests passed. The recovery test reproduces the scenario directly.
The job's figure committed. The same payload was run again (a resume before
acknowledgement) after an answer's item became exam material, and
`run_rich_job` returned the stored figure (`DID NOT RAISE`) with no protection
check. With the fix, all 21 pass.

### F2 (reopened): what changed (`src/learnloop/figures/rich.py`, `src/learnloop/figures/service.py`)

- **Persisted with the figure.** When the job's saved context carries a
  learner state, `_store` writes the job's `learner_state_inputs` into the
  rich row's `verification_report` (`LEARNER_STATE_INPUTS_KEY`), for both
  shown and failed rows. A JSON key inside the existing report means no schema
  change and no migration. `figure_view` reads named report fields only, so
  the record is never shown, and it is never sent to a model.
- **One check.** `stored_learner_state_withheld(vault, repository, row)`
  returns None when the row's author was sent no learner state (the key is
  absent), so every other figure behaves exactly as before. Otherwise it runs
  `learner_state.inputs_withheld` against the protection as it is now. A key
  present with no usable record fails closed.
- **Recovery.** `run_rich_job`'s already-stored return, and `_store`'s
  concurrent-store (`IntegrityError`) return, go through `_recovered`. It
  checks the stored row's inputs and, when the payload carries a learner
  state, the payload's inputs too. Anything protected now stops the job with
  `exam_material` instead of returning the figure. The switch is not
  rechecked here, because a recovered figure sends nothing more to a model.
- **Delivery.** `row_withheld` is the shared delivery gate behind
  `figure_withheld`, the sidecar's `deliver_figure`, `list_figures`, the
  compiled-figure read and the revision base. It now also asks
  `stored_learner_state_withheld`, so a rich-only figure stops being listed or
  delivered. `fuller_state` drops a fuller version whose inputs are protected
  now: the quick figure stays, and its fuller version is not delivered or
  named failed.
- **Reuse.** `_reusable` (now passed the repository) reuses a rich-only figure
  only while its learner inputs are unprotected. Otherwise the build goes
  ahead with the learner state read fresh.

This replaces the earlier "how delivery is read" note: stored rich figures
whose author was sent a learner state *are* re-gated on later reads.

### Gate (re-review fix step)

Every test command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at
`-n 6`, with TMPDIR in the session scratchpad. No full suite, whole durability
lane or whole vitest run.

- `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **37 kept, 0 broken**.
- `uv run pytest -n 6 -p no:randomly tests/test_learner_data_relax_2.py`:
  **21 passed**. Against the pre-fix sources: 5 failed, 16 passed (the
  reproduction).
- Targeted lane, `uv run pytest -n 6 -p no:randomly <40 files>`:
  **936 passed, 0 failed** (208.3 s). This is the first fix step's lane plus
  the 5 new tests. Files: `tests/test_architecture.py`,
  `tests/test_diagnosis_input_provenance.py`, every `tests/test_figure*.py`
  (`test_figure_grammar`, `_label_wording`, `_offers`, `_panels`,
  `_predictions`, `_property`, `_region`, `_requests_migration`,
  `_revisions`, `_rich_contract`, `_rich_failed_correction_durable`,
  `_rich_job`, `_rich_rereview_fixes`, `_rich_review_fixes`, `_rich_rpc`,
  `_verification`) and `tests/test_figures*.py` (`_codex_review`,
  `_final_round`, `_fix_round2` to `_fix_round5`, `_migration`, `_rpc`,
  `_rw5b_fix_round2`, `_rw5b_review`, `_scope_redesign`,
  `_show_me_codex_review`, `_show_me`, `_switch_off`),
  `tests/test_learner_data_relax_2.py`, `tests/test_learner_text_gaps.py`,
  `tests/test_learner_text_gaps_flow.py`, `tests/test_mcp_c1a_review.py`,
  `tests/test_reader_followups.py`,
  `tests/test_reader_followups_successor.py`, `tests/test_router_card.py`,
  `tests/test_sketch_service.py`.
- Not run, because nothing they cover changed: migrations and durability (no
  schema, migration or connection code), frontend and cargo (no `apps/`
  change), DB reference scripts (no schema change), config defaults snapshot
  (no config key).

### Open items (re-review)

- A quick (grammar or sketch) figure whose author was sent the learner state
  does not keep that state's inputs as a top-level record. The inputs exist
  only inside its rich intent, when it has one. So a quick figure is not
  re-gated on later reads for its learner inputs. It is built and delivered
  in the same request, behind `deliver_figure`'s recheck, and a later build
  rereads the state, so a changed state changes the reuse key. F2 covered the
  delayed rich job only. Recording the inputs on quick rows the same way is a
  one-line follow-up if wanted.
- The router-card item from the first fix step stands.
