---
title: "learnloop.teacher.check_delivery"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/check_delivery.py"
source_paths:
  - "src/learnloop/teacher/check_delivery.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.teacher"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.teacher.check_delivery module"
  - "src/learnloop/teacher/check_delivery.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.check_delivery`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.check_delivery` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: How often a lesson's planned delayed check is actually answered cold: the receipts classified as of a decision, and the one-trial seed's Beta posterior over that completion probability (spec_teacher_v2 §7.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py) |
| Source lines | 434 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Trial` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 88) — One planned delayed-check entry, classified as of the read.
- `class DeliveryCounts` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 105) — The sufficient statistics for one purpose and regime as of ``as_of``.
  - `censored(self) -> int` (line 118; public)
- `class DeliveryPosterior` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 123) — ``Beta(alpha, beta)`` over the cold-completion probability of one committed check, or its limiting point mass at an endpoint (``alpha = 0``: exactly 0; ``beta = 0``: exactly 1).
  - `predictive_mean(self) -> float` (line 137; public)
  - `endpoint(self) -> float | None` (line 141; public) — The point mass at an endpoint, or None when both shapes are positive.
  - `as_dict(self) -> dict[str, Any]` (line 150; public)
- `posterior(counts: DeliveryCounts, *, eligible_now: bool) -> DeliveryPosterior` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 160) — The one-trial seed updated by the resolved trials: ``alpha = e + S``, ``beta = (1 − e) + F``.
- `counts(trials: Iterable[Trial], *, purpose: str, as_of: str, regime: str=LEGACY_REGIME) -> DeliveryCounts` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 168) — One purpose's and regime's statistics over classified trials (another purpose's never pooled in).
- `classify(repository: Any, *, as_of: str, config: Any=None) -> tuple[Trial, ...]` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 377) — Every planned delayed-check entry of every lesson receipt recorded by ``as_of``, classified as of then.
- `statistics(repository: Any, *, as_of: str, config: Any=None, purposes: Sequence[str]=PURPOSES) -> dict[str, DeliveryCounts]` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 421) — Each purpose's counts as of ``as_of`` (the legacy regime's).

### Module constants

- `DELIVERY_POLICY_VERSION` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 54)
- `PRIORS_VERSION` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 56)
- `SEED_BASIS` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 57)
- `SEED_TRIALS` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 60)
- `LEGACY_REGIME` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 62)
- `PURPOSES` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 63)
- `SUCCESS` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 65)
- `FAILURE` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 66)
- `CENSORED` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 67)
- `NOT_A_TRIAL` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 68)
- `MISSING` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 71)
- `ANSWERED_COLD` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 72)
- `SETTLED` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 73)
- `STOPPED` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 74)
- `REPLACED` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 75)
- `NOT_YET_DUE` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 76)
- `PAUSED` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 77)
- `NOT_PENDING` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 78)
- `UNGRADED` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 79)
- `PENDING` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 80)
- `NO_COMMITMENT` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 81)
- `UNKNOWN_COMMITMENT` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 82)
- `_SERVE` ([src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py), line 84)

### Explicit exports

`__all__` declares:

- `ANSWERED_COLD`
- `CENSORED`
- `DELIVERY_POLICY_VERSION`
- `DeliveryCounts`
- `DeliveryPosterior`
- `FAILURE`
- `LEGACY_REGIME`
- `MISSING`
- `NOT_A_TRIAL`
- `NOT_PENDING`
- `NOT_YET_DUE`
- `PAUSED`
- `PENDING`
- `PRIORS_VERSION`
- `PURPOSES`
- `REPLACED`
- `SEED_BASIS`
- `SEED_TRIALS`
- `SETTLED`
- `STOPPED`
- `SUCCESS`
- `Trial`
- `UNGRADED`
- `classify`
- `counts`
- `posterior`
- `statistics`

## Internal implementation anchors

- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 189)
- `_snapshots_as_of(connection: Any, as_of: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 194) — Every commitment as it stood at ``as_of``: created by then, its head the latest version by then, its events those recorded by then, folded by the intent resolver's own fold.
- `_satisfied_by(connection: Any, commitment_id: str, as_of: str) -> list[str]` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 225) — The administrations settlement recorded as satisfying the commitment by ``as_of`` (attempt ids; may be empty strings for a satisfaction recorded without one).
- `_settled_answer(connection: Any, commitment_id: str, as_of: str, *, derived: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 242) — A satisfaction recorded by ``as_of`` whose answer counts: the administration's attempt id when its grade is usable then, ``""`` for a satisfaction that names no attempt this store holds (the event is the evidence), or None (no satisfaction, or only ones whose answer was not grad…
- `_grade_usable(connection: Any, attempt: Mapping[str, Any], as_of: str) -> bool` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 260) — The attempt's grade could be used at ``as_of``: it has a correctness, and it was not held for review then.
- `_answer(repository: Any, connection: Any, snapshot: Any, *, item_id: str, learning_object_id: str | None, as_of: str, default_days: int, known: str) -> tuple[Mapping[str, Any] | None, Any]` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 298) — The attempt that answers the check by ``as_of`` (the intent resolver's rule over the entry's own item), and the check's effective date then.
- `_replaced(snapshots: Mapping[str, Any], snapshot: Any, item_id: str, learning_object_id: str | None) -> bool` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 329) — Another commitment decides the check's item as of the read (the intent resolver's F21 rule for an item-level check).
- `_outcome(repository: Any, connection: Any, entry: Mapping[str, Any], snapshots: Mapping[str, Any], *, as_of: str, cutoff: Any, default_days: int, known: str) -> tuple[str, str, str | None]` ([source](../../../../../../src/learnloop/teacher/check_delivery.py), line 339) — One entry's ``(outcome, reason, answering attempt)`` as of ``as_of`` (the module's table, in its order).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

### Repository tooling consumers

- [scripts/check_credit_report.py](../../../../../../scripts/check_credit_report.py); calls `_answer`, `_snapshots_as_of`, `classify`, `counts`, `posterior`, `statistics`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/attempt_availability|learnloop.db.attempt_availability]] — imports `attempt_time_sql`; calls `attempt_time_sql`
- [[Reference/Modules/learnloop/db/stores/intent_reads|learnloop.db.stores.intent_reads]] — imports `module`; calls `commitment_tables_present`, `events_for`, `head_targets_for`, `versions_for`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `grade_held_for_review`; calls `grade_held_for_review`
- [[Reference/Modules/learnloop/scheduling/intent/resolution|learnloop.scheduling.intent.resolution]] — imports `Resolution`, `snapshot_from_rows`; calls `Resolution`, `snapshot_from_rows`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `check_date`, `on_your_own`; calls `check_date`, `on_your_own`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `check_once_at_attempt`; calls `check_once_at_attempt`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_check_delivery.py](../../../../../../tests/test_check_delivery.py) — direct import
  - `test_a_later_decision_sees_the_late_grade_and_the_redated_answer`
  - `test_a_settled_answer_counts_once_before_and_after_its_settlement`
  - `test_an_empty_vault_predicts_exactly_the_availability`
  - `test_before_its_answer_is_known_nothing_counts`
  - `test_every_class_as_of_a_decision`
  - `test_resolved_checks_move_the_seed`
  - `test_retention_and_transfer_are_pooled_apart`

## Modification guidance

- Make changes here when the responsibility remains check delivery within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/check_delivery.py](../../../../../../src/learnloop/teacher/check_delivery.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
