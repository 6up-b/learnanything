---
title: "learnloop.db.stores.learner_gaps"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/learner_gaps.py"
source_paths:
  - "src/learnloop/db/stores/learner_gaps.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.learner_gaps module"
  - "src/learnloop/db/stores/learner_gaps.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.learner_gaps`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.learner_gaps` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The only SQL writer for the learner-text gap tables (migration 182).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/learner_gaps.py](../../../../../../../src/learnloop/db/stores/learner_gaps.py) |
| Source lines | 450 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `gap_tables_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 41)
- `insert_gap(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 71) — Append one read learner text (``id`` minted when absent).
- `gap(connection: sqlite3.Connection, gap_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 86)
- `gap_for_source(connection: sqlite3.Connection, source_kind: str, source_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 91)
- `gaps_for_attempt(connection: sqlite3.Connection, attempt_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 101) — The learner texts read from one attempt (its answer, a stuck answer), in written order.
- `gaps(connection: sqlite3.Connection, *, since: str | None=None, before: str | None=None, source_kind: str | None=None, learning_object_ids: Iterable[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 110) — Gaps in written order, optionally windowed and scoped to target/anchor LOs.
- `insert_reversal(connection: sqlite3.Connection, *, gap_id: str, reversal: str, actor: str, created_at: str, detail: Mapping[str, Any] | None=None) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 149) — Append one reversal; None when this gap already has it (a repeated tap).
- `reversals(connection: sqlite3.Connection, gap_ids: Iterable[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 168)
- `insert_check_advance(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 187)
- `check_advances(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 200)
- `insert_commitment(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 206)
- `commitments(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 219) — Light commitments whose creation the learner has not undone.
- `enqueue_job(connection: sqlite3.Connection, *, source_kind: str, source_id: str, now: str, payload: Mapping[str, Any] | None=None) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 235) — Queue one learner text; None when it is already queued or read.
- `requeue_skipped_job(connection: sqlite3.Connection, job_id: str, *, now: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 256) — Queue a skipped job again (curriculum C5: a note skipped while it was hidden or switched off, linked again); False when it is not skipped (read, queued, leased).
- `skip_queued_job(connection: sqlite3.Connection, *, source_kind: str, source_id: str, now: str, reason: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 276) — Set a still-queued job aside unread (its text no longer stands); False when it is not queued (leased, read, finished or absent: a reading already under way finishes, and its gap is set aside instead).
- `jobs(connection: sqlite3.Connection, *, states: Iterable[str] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 289)
- `job_for_source(connection: sqlite3.Connection, source_kind: str, source_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 301)
- `lease_next_job(connection: sqlite3.Connection, *, owner: str, now: str, lease_seconds: float, source: tuple[str, str] | None=None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 311) — Claim the oldest runnable job (or the one for ``source``), or None.
- `job(connection: sqlite3.Connection, job_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 348)
- `holds_job(connection: sqlite3.Connection, job_id: str, *, owner: str, epoch: int) -> bool` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 353)
- `save_job_payload(connection: sqlite3.Connection, job_id: str, payload: Mapping[str, Any], *, owner: str, epoch: int, now: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 360)
- `finish_job(connection: sqlite3.Connection, job_id: str, *, state: str, owner: str, epoch: int, now: str, error: str | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 371)
- `release_job(connection: sqlite3.Connection, job_id: str, *, owner: str, epoch: int, now: str, not_before: str | None, error: str | None, refund_attempt: bool=False) -> bool` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 383) — Back to ``queued``; ``refund_attempt`` when the job itself did not fail (a spend stop or the daily cap), so it never uses up its retries.
- `pipeline_calls_since(connection: sqlite3.Connection, since: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 409) — This pipeline's logical model calls on the live path (receipt roots) started at or after ``since``; a command's calls are not counted.

### Module constants

- `GAP_COLUMNS` ([src/learnloop/db/stores/learner_gaps.py](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 22)
- `_JSON_COLUMNS` ([src/learnloop/db/stores/learner_gaps.py](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 29)
- `PAD_TEXT_SNAPSHOT` ([src/learnloop/db/stores/learner_gaps.py](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 32)
- `PIPELINE_RECEIPT_OWNER` ([src/learnloop/db/stores/learner_gaps.py](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 402)
- `COMMAND_RECEIPT_OWNER` ([src/learnloop/db/stores/learner_gaps.py](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 406)

### Explicit exports

`__all__` declares:

- `COMMAND_RECEIPT_OWNER`
- `GAP_COLUMNS`
- `PAD_TEXT_SNAPSHOT`
- `PIPELINE_RECEIPT_OWNER`
- `check_advances`
- `commitments`
- `enqueue_job`
- `finish_job`
- `gap`
- `gap_for_source`
- `gap_tables_present`
- `gaps`
- `holds_job`
- `insert_check_advance`
- `insert_commitment`
- `insert_gap`
- `insert_reversal`
- `job`
- `job_for_source`
- `jobs`
- `lease_next_job`
- `pipeline_calls_since`
- `release_job`
- `reversals`
- `save_job_payload`
- `skip_queued_job`

## Internal implementation anchors

- `_table_present(connection: sqlite3.Connection, name: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 35)
- `_dumps(value: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 45)
- `_decode(row: sqlite3.Row | Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 49)
- `_rows(connection: sqlite3.Connection, sql: str, params: Iterable[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/learner_gaps.py), line 62)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]] — imports `module`; statically calls `gaps`, `reversals`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `module`; statically calls `gap`, `insert_check_advance`, `insert_reversal`, `reversals`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]] — imports `gaps`, `reversals`; statically calls `gaps`, `reversals`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `module`; statically calls `enqueue_job`, `finish_job`, `gap_for_source`, `gaps`, `holds_job`, `insert_gap`, `insert_reversal`, `job_for_source`, `jobs`, `lease_next_job`, `pipeline_calls_since`, `release_job`, `requeue_skipped_job`, `reversals`, `save_job_payload`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `COMMAND_RECEIPT_OWNER`, `PIPELINE_RECEIPT_OWNER`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `module`; statically calls `gap`, `gap_for_source`, `gaps`, `insert_commitment`, `insert_gap`, `reversals`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/report|learnloop.diagnosis.text_gaps.report]] — imports `module`; statically calls `gaps`, `jobs`, `reversals`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `module`; statically calls `job_for_source`
- [[Reference/Modules/learnloop/figures/learner_state|learnloop.figures.learner_state]] — imports `module`; statically calls `gaps`, `reversals`
- [[Reference/Modules/learnloop/pads/emission|learnloop.pads.emission]] — imports `module`; statically calls `enqueue_job`, `gap_tables_present`, `gaps`, `insert_reversal`, `job_for_source`, `reversals`, `skip_queued_job`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `check_advances`, `commitments`; statically calls `check_advances`, `commitments`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `module`; statically calls `gaps`, `reversals`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `module`; statically calls `gaps`, `reversals`
- [[Reference/Modules/learnloop/teacher/diagnosed_sources|learnloop.teacher.diagnosed_sources]] — imports `module`; statically calls `gaps_for_attempt`, `reversals`
- [[Reference/Modules/learnloop_sidecar/handlers/learner_gaps|learnloop_sidecar.handlers.learner_gaps]] — imports `module`; statically calls `gap`, `gap_for_source`, `job_for_source`, `reversals`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] — imports `module`; calls `record_job_enqueued`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/gaps|learnloop.cli.gaps]], [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]], [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]], [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]], [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] and 10 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/desk_helpers.py](../../../../../../../tests/desk_helpers.py) — direct import
- [tests/learner_text_gaps_review_helpers.py](../../../../../../../tests/learner_text_gaps_review_helpers.py) — direct import
- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
  - `test_the_diagnosis_hypotheses_come_first_my_gap_first_then_the_learners_gaps`
- [tests/test_learner_text_gaps.py](../../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_a_missing_prerequisite_is_drafted_created_live_seeded_and_committed`
  - `test_the_cli_dry_runs_send_and_write_nothing`
  - `test_undo_creation_puts_the_lo_away_and_removes_its_edge_and_commitment`
- [tests/test_learner_text_gaps_flow.py](../../../../../../../tests/test_learner_text_gaps_flow.py) — direct import
  - `test_a_gap_brings_an_assumed_los_check_forward_and_the_switch_restores_the_predecessor`
  - `test_a_gap_on_a_maintenance_lo_brings_its_next_review_forward_until_answered`
  - `test_a_job_that_keeps_failing_is_logged_as_failed_without_a_target`
  - `test_stuck_text_is_read_through_the_source_interface`
  - `test_the_queue_runs_a_text_once_retries_failures_and_respects_the_switch`
  - `test_the_switch_off_queue_equals_the_predecessor_version`
- [tests/test_learner_text_gaps_rereview.py](../../../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
  - `test_rr_f5_a_commands_calls_do_not_count_toward_the_live_daily_cap`
  - `test_rr_f5_gaps_run_reads_on_a_command_budget`
- [tests/test_learner_text_gaps_review.py](../../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f3_a_belief_candidate_commits_with_its_ledger_row`
  - `test_f3_a_sighting_is_counted_once_across_a_retry`
  - `test_f5_several_same_verdicts_are_ambiguous_and_target_nothing`
- [tests/test_library_ask_review.py](../../../../../../../tests/test_library_ask_review.py) — direct import
  - `test_the_pinned_tutor_burns_a_reserve_it_reproduces_and_joins_history_and_gaps`
- [tests/test_reader_rd4_emission.py](../../../../../../../tests/test_reader_rd4_emission.py) — direct import
  - `test_a_committed_text_block_is_queued_once_with_its_snapshot`
  - `test_a_quote_pasted_into_the_learners_block_is_kept_but_never_read_for_a_gap`
  - `test_a_reading_that_finished_after_its_words_were_replaced_is_set_aside_by_the_reconcile`
  - `test_the_passages_a_block_is_linked_to_place_its_gap_and_live_equals_rebuild`
  - `test_the_tag_and_the_kind`
- [tests/test_reader_rd8a_transcribe.py](../../../../../../../tests/test_reader_rd8a_transcribe.py) — direct import
  - `test_a_linked_ink_lines_gap_is_placed_by_its_passage_and_live_equals_rebuild`
  - `test_a_transcription_is_learner_text_marked_transcribed_and_a_correction_supersedes_it`
- [tests/test_reader_rw1b_review.py](../../../../../../../tests/test_reader_rw1b_review.py) — direct import
  - `test_f1_a_formative_gap_brings_no_check_forward`
  - `test_f1_a_formative_gap_is_not_a_weak_prerequisite_signal`
  - `test_f7_a_failed_enqueue_leaves_the_self_check_unrecorded`
- [tests/test_reading_paths.py](../../../../../../../tests/test_reading_paths.py) — direct import
- [tests/test_sidecar_close_cancels_jobs.py](../../../../../../../tests/test_sidecar_close_cancels_jobs.py) — direct import
  - `test_shutting_down_the_gaps_slot_inside_a_request_sends_no_further_request`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/learner_gaps.py](../../../../../../../src/learnloop/db/stores/learner_gaps.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
