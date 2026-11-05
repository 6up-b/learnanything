---
title: "learnloop.grading_epochs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/grading_epochs.py"
source_paths:
  - "src/learnloop/grading_epochs.py"
source_commit: "a636f4f6d2acb0dd4f0d7e683bf58303d588d72f"
source_commit_timestamp: "2026-10-16T11:51:28-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.grading_epochs module"
  - "src/learnloop/grading_epochs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.grading_epochs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.grading_epochs` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: Grading epochs: one definition of which grade of an attempt is current.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/grading_epochs.py](../../../../../src/learnloop/grading_epochs.py) |
| Source lines | 205 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a636f4f6d2acb0dd4f0d7e683bf58303d588d72f` |
| Commit timestamp | `2026-10-16T11:51:28-04:00` |

## Public API

- `epoch_key(row: Any) -> str` ([source](../../../../../src/learnloop/grading_epochs.py), line 51) — ``revision:N`` for a row carrying a grading revision, else ``legacy:<created_at>``.
- `class GradingEpoch` ([source](../../../../../src/learnloop/grading_epochs.py), line 61) — The rows of one grading epoch, in the order they were given.
  - `revision(self) -> int | None` (line 68; public)
  - `live(self) -> bool` (line 74; public) — Does any of its rows still stand (not superseded)?
  - `last_written(self) -> tuple[str, str]` (line 80; public) — ``(created_at, id)`` of its last-written row.
  - `contract_version_id(self) -> str | None` (line 86; public)
  - `criterion_ids(self) -> tuple[str, ...]` (line 90; public)
  - `agent_run_ids(self) -> tuple[str, ...]` (line 94; public)
- `epoch_contract_version_id(rows: Iterable[Any]) -> str | None` ([source](../../../../../src/learnloop/grading_epochs.py), line 98) — The one contract version every row cites, else None (none on record).
- `group_epochs(rows: Iterable[Any]) -> list[GradingEpoch]` ([source](../../../../../src/learnloop/grading_epochs.py), line 108) — The epochs of ``rows``, in the order their keys first appear.
- `current_epoch(rows: Iterable[Any]) -> GradingEpoch | None` ([source](../../../../../src/learnloop/grading_epochs.py), line 128) — The attempt's current grading epoch: chosen among its live rows (see the module doc).
- `ordered_epochs(rows: Iterable[Any]) -> list[GradingEpoch]` ([source](../../../../../src/learnloop/grading_epochs.py), line 137) — Every epoch of ``rows`` (superseded ones included) in written order, the current epoch last.
- `next_grading_revision(rows: Iterable[Any]) -> int` ([source](../../../../../src/learnloop/grading_epochs.py), line 161) — The grading revision the attempt's next epoch takes: 0 for its first grade (no rows at all), else one more than the greatest revision any of its rows carries (superseded included), and never below 1.
- `only_grade(rows: Iterable[Any]) -> bool` ([source](../../../../../src/learnloop/grading_epochs.py), line 173) — Is ``rows`` (every row of the attempt, superseded included) one write: the attempt's first grade and nothing after it?

### Explicit exports

`__all__` declares:

- `GradingEpoch`
- `current_epoch`
- `epoch_contract_version_id`
- `epoch_key`
- `group_epochs`
- `next_grading_revision`
- `only_grade`
- `ordered_epochs`

## Internal implementation anchors

- `_field(row: Any, name: str) -> Any` ([source](../../../../../src/learnloop/grading_epochs.py), line 45)
- `_current_among(epochs: Sequence[GradingEpoch]) -> GradingEpoch | None` ([source](../../../../../src/learnloop/grading_epochs.py), line 117)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `current_epoch`; statically calls `current_epoch`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `current_epoch`, `only_grade`; statically calls `current_epoch`, `only_grade`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `current_epoch`, `epoch_contract_version_id`, `next_grading_revision`; statically calls `current_epoch`, `epoch_contract_version_id`, `next_grading_revision`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `next_grading_revision`; statically calls `next_grading_revision`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `current_epoch`, `only_grade`, `ordered_epochs`; statically calls `current_epoch`, `only_grade`, `ordered_epochs`
- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `current_epoch`; statically calls `current_epoch`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `current_epoch`; statically calls `current_epoch`
- [[Reference/Modules/learnloop/workbench/help_outcomes|learnloop.workbench.help_outcomes]] — imports `current_epoch`; statically calls `current_epoch`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `ordered_epochs`; statically calls `ordered_epochs`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_fix_review.py](../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_historical_regrade_reads_its_current_epoch_not_a_surviving_obsolete_criterion`
- [tests/test_reader_recap_review_r3.py](../../../../../tests/test_reader_recap_review_r3.py) — direct import
  - `test_f1_r3_a_hold_released_after_the_cutoff_still_holds_at_the_cutoff`
- [tests/test_regrade_contract_successor.py](../../../../../tests/test_regrade_contract_successor.py) — direct import
  - `test_an_adjudication_allocates_its_revision_inside_its_own_transaction`
  - `test_only_a_grade_no_later_write_replaced_is_an_attempts_only_grade`
  - `test_random_grading_histories_stay_in_range_replay_equal_to_live_and_rebuild_idempotent`
  - `test_the_current_epoch_is_chosen_among_live_rows_never_by_a_first_seen_stamp`

## Modification guidance

- Make changes here when the responsibility remains grading epochs within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/grading_epochs.py](../../../../../src/learnloop/grading_epochs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
