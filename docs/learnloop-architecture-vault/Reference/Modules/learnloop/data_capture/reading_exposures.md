---
title: "learnloop.data_capture.reading_exposures"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/data_capture/reading_exposures.py"
source_paths:
  - "src/learnloop/data_capture/reading_exposures.py"
source_commit: "43bcc8fac4be9bfc864222dd8821769f1ee74d88"
source_commit_timestamp: "2026-11-03T19:34:35-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.data_capture"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.data_capture.reading_exposures module"
  - "src/learnloop/data_capture/reading_exposures.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-data-capture"
---

# `learnloop.data_capture.reading_exposures`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.data_capture.reading_exposures` exists within [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] to own the behavior summarized by its module contract: Reader activity frozen for the delayed-completion definition (data capture; Codex re-review F1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/data_capture/reading_exposures.py](../../../../../../src/learnloop/data_capture/reading_exposures.py) |
| Source lines | 331 |
| Owning package | [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `43bcc8fac4be9bfc864222dd8821769f1ee74d88` |
| Commit timestamp | `2026-11-03T19:34:35-05:00` |

## Public API

- `reading_learning_objects(vault: Any, repository: Any, target: Any) -> list[str]` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 75) — What a decision's objective freezes (:mod:`learnloop.daily_plan.measurement`) and what an exposure names.
- `recent_since(connection: Any) -> str | None` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 230) — Where the foreground reads from: the newest source time on record less AD's overlap, so a source row stamped a little before it is still read.
- `not_yet_swept(connection: Any, vault: Any, repository: Any, *, since: str | None=None) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 239) — ``(LO, source time)`` of the listed activity no sweep has recorded yet.
- `read(connection: Any, vault: Any, repository: Any, *, since: str | None=None) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 254) — Every Reader exposure, ``(LO, source time)``: the stored receipts plus the source activity not yet swept.
- `read_for_answer(connection: Any, vault: Any, repository: Any, *, answered_at: str) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 265) — :func:`read` for judging one answer on the foreground: activity that could have made it warm, or newer than the sweep's window.
- `for_version(connection: Any, vault: Any, repository: Any, version: str, *, recent: bool=False) -> list[tuple[str, str]] | None` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 277) — :func:`read` for a derivation at ``version`` (``recent``: on the foreground, from :func:`recent_since`); None below ``router_outcomes_v3``, which reads no reading receipt.
- `sweep(vault: Any, repository: Any, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 286) — Freeze the listed Reader activity since the window's start (:func:`recent_since`); how many rows it wrote.
- `sweep_quietly(vault: Any, repository: Any, *, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 311) — :func:`sweep`, never raising: the record of an exposure never blocks Today; the next sweep reads it.

### Module constants

- `MAPPING_VERSION` ([src/learnloop/data_capture/reading_exposures.py](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 57)
- `NO_UPPER` ([src/learnloop/data_capture/reading_exposures.py](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 59)
- `_MAPPINGS` ([src/learnloop/data_capture/reading_exposures.py](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 115)
- `_MAPPINGS_KEPT` ([src/learnloop/data_capture/reading_exposures.py](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 116)

### Explicit exports

`__all__` declares:

- `MAPPING_VERSION`
- `for_version`
- `not_yet_swept`
- `read`
- `read_for_answer`
- `reading_learning_objects`
- `recent_since`
- `sweep`
- `sweep_quietly`

## Internal implementation anchors

- `_section_los(vault: Any, repository: Any, extraction_id: str, section_id: str) -> list[str]` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 62) — The LOs a section holds: its provenance-linked LOs and its coverage rows.
- `_content_revision(vault: Any) -> str` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 87) — What the mapping reads of the vault: active LOs' and their facets' provenance, and the notes' canonical sources.
- `_revision(connection: Any, vault: Any) -> tuple[Any, ...]` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 101) — A mapping stands while these do: the vault's content, the readings and their aliases, the sources' artifacts, the coverage rows.
- `_clear_mapping_cache() -> None` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 119) — A new process's view: what a test uses to say so.
- `class _Map` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 125) — A section's and a span's LOs as the objective's freeze reads them (provenance and coverage rows), an item's, a note's.
- `class _Rows` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 185) — What AD's collectors read through its material view, read plainly; ``lookup`` asks this record, not AD's.
- `_events(connection: Any, vault: Any, repository: Any, *, lower: str | None=None, upper: str=NO_UPPER) -> list[Any]` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 223) — The listed activity not yet on record since ``lower`` (all of it with none): what the sweep freezes and what :func:`read` adds are this one list.
- `_covered_sections(connection: Any) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/data_capture/reading_exposures.py), line 246) — A section's coverage rows, read live: a section on record for one LO doesn't hide one a row names later (the section's own rule, :func:`_section_los`, and its source time).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `module`; statically calls `for_version`
- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `module`, `reading_learning_objects`; statically calls `read_for_answer`, `reading_learning_objects`, `sweep_quietly`
- [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]] — imports `module`; statically calls `for_version`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `module`; statically calls `read`
- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `module`; statically calls `for_version`, `not_yet_swept`, `read`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `module`; statically calls `for_version`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `OUTCOME_VERSION_V3`, `receipts_on`, `serving_on`; calls `receipts_on`, `serving_on`
- [[Reference/Modules/learnloop/db/stores/data_capture|learnloop.db.stores.data_capture]] — imports `module`; calls `insert_reading_exposure`, `newest_reading_exposure`, `reading_exposure_recorded`, `reading_exposures_present`, `reading_receipts`, `sections_read_by_coverage`
- [[Reference/Modules/learnloop/db/stores/section_coverage|learnloop.db.stores.section_coverage]] — imports `module`; calls `learning_objects_named`, `table_present`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `RETENTION_MIN_DELAY_SECONDS`
- [[Reference/Modules/learnloop/reading_sources|learnloop.reading_sources]] — imports `SWEEP_OVERLAP`, `listed_events`, `source_stamp`; calls `listed_events`, `source_stamp`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `module`; calls `learning_objects_for_section`, `learning_objects_for_span`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `hashlib`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]], [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]], [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]], [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_data_capture_a2_measurement.py](../../../../../../tests/test_data_capture_a2_measurement.py) — direct import
- [tests/test_data_capture_a3_time_metric.py](../../../../../../tests/test_data_capture_a3_time_metric.py) — direct import
- [tests/test_data_capture_codex_rereview.py](../../../../../../tests/test_data_capture_codex_rereview.py) — direct import
  - `test_f1_a_completed_section_is_an_exposure_with_ad_off`
  - `test_f1_a_failed_sweep_never_stops_the_states`
  - `test_f1_a_section_read_after_the_last_sweep_is_found_by_the_next`
  - `test_f1_a_span_view_a_tutor_exchange_and_an_in_passage_question_are_exposures_too`
  - `test_f1_no_receipt_with_both_switches_off`
  - `test_f1_the_sweep_records_each_exposure_once_at_its_source_time`
- [tests/test_data_capture_codex_review.py](../../../../../../tests/test_data_capture_codex_review.py) — direct import
- [tests/test_data_capture_landing_review.py](../../../../../../tests/test_data_capture_landing_review.py) — direct import
  - `test_f1_a_rebuild_with_no_decisions_needs_no_read`
  - `test_f1_a_section_no_lo_named_until_later_reads_the_same_swept_or_not`
  - `test_f1_activity_stamped_long_before_the_newest_receipt_is_read_though_the_sweep_leaves_it`
  - `test_f1_an_answer_waits_when_the_read_cannot_judge_it`
  - `test_f1_below_the_receipts_table_the_read_is_activity_alone`
  - `test_f1_derivation_metric_and_report_read_the_same_before_and_after_the_sweep`
  - `test_f1_for_version_reads_only_at_version_3`
  - `test_f1_settle_judges_the_answer_by_the_read_when_the_sweep_failed`
  - `test_f1_the_read_is_read_only_under_a_read_only_repository`
  - `test_finding2_coverage_named_after_the_sweep_is_an_exposure_too`
  - `test_r6_a_repeat_sweep_with_nothing_new_makes_no_mapping_call`
  - `test_r6_a_sweep_with_nothing_to_write_takes_no_write_lock`
  - `test_r6_a_transient_mapping_failure_is_not_cached_as_empty`
  - `test_r6_the_cached_mapping_follows_coverage_and_content`
  - `test_r6_the_foreground_read_does_not_list_the_whole_history`
  - `test_r6_with_receipts_on_record_the_window_leaves_old_unmapped_sections_alone_in_a_new_process`

## Modification guidance

- Make changes here when the responsibility remains reading exposures within learnloop.data_capture; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/data_capture/reading_exposures.py](../../../../../../src/learnloop/data_capture/reading_exposures.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
