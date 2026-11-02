---
title: "learnloop.scheduling.review_log"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/review_log.py"
source_paths:
  - "src/learnloop/scheduling/review_log.py"
source_commit: "171ae5a5ed15b7627add8b2e512d0c0e91c5f3da"
source_commit_timestamp: "2026-10-13T09:11:59-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.review_log module"
  - "src/learnloop/scheduling/review_log.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.review_log`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.review_log` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: Review-log reconstruction for FSRS fitting.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/review_log.py](../../../../../../src/learnloop/scheduling/review_log.py) |
| Source lines | 160 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `171ae5a5ed15b7627add8b2e512d0c0e91c5f3da` |
| Commit timestamp | `2026-10-13T09:11:59-04:00` |

## Public API

- `class ReviewObservation` ([source](../../../../../../src/learnloop/scheduling/review_log.py), line 27)
- `class ReviewLog` ([source](../../../../../../src/learnloop/scheduling/review_log.py), line 43)
- `reconstruct_review_log(vault: LoadedVault, repository: Repository) -> ReviewLog` ([source](../../../../../../src/learnloop/scheduling/review_log.py), line 50) — The FSRS fitter's review log (``learnloop fit fsrs``).
- `review_log_from_attempts(vault: LoadedVault, rows: Iterable[Mapping[str, Any]], *, skip_ungraded: bool=False, held_attempt_ids: Collection[str]=frozenset()) -> ReviewLog` ([source](../../../../../../src/learnloop/scheduling/review_log.py), line 65) — The review log of ``rows`` (``practice_attempts`` rows ordered by item, then time, as ``Repository.list_all_attempts`` returns them).
- `predicted_retrievability_by_attempt(review_log: ReviewLog, weights: tuple[float, ...]) -> dict[str, float]` ([source](../../../../../../src/learnloop/scheduling/review_log.py), line 133) — FSRS-predicted retrievability at each reviewed attempt (router R1, D12).

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]] — imports `reconstruct_review_log`; statically calls `reconstruct_review_log`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `predicted_retrievability_by_attempt`, `review_log_from_attempts`; statically calls `predicted_retrievability_by_attempt`, `review_log_from_attempts`
- [[Reference/Modules/learnloop/scheduling/fsrs_fitting|learnloop.scheduling.fsrs_fitting]] — imports `ReviewLog`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `fsrs_rating_for_attempt`; calls `fsrs_rating_for_attempt`
- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `attempt_evidence_mass`; calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_attempt_ids`; calls `held_attempt_ids`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `MemoryState`, `Rating`, `apply_review`, `forgetting_curve`; calls `apply_review`, `forgetting_curve`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]], [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]], [[Reference/Modules/learnloop/scheduling/fsrs_fitting|learnloop.scheduling.fsrs_fitting]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_fsrs_fitting.py](../../../../../../tests/test_fsrs_fitting.py) — direct import
  - `test_review_log_loss_skips_short_gaps_and_zero_weight`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_f8_the_fsrs_fitter_never_fits_a_review_that_never_happened`
  - `test_review_f1_a_regrade_into_a_hold_supersedes_the_assessed_grade_it_replaces`
- [tests/test_review_log.py](../../../../../../tests/test_review_log.py) — direct import
  - `test_dont_know_rating_and_weight`
  - `test_elapsed_days_between_successive_attempts`
  - `test_hint_cap_and_score_binning_match_live_semantics`
  - `test_reconstruction_reproduces_live_practice_item_state`

## Modification guidance

- Change review log policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/review_log.py](../../../../../../src/learnloop/scheduling/review_log.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
