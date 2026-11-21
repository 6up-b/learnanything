---
title: "learnloop.attempts.fact_predicates"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/fact_predicates.py"
source_paths:
  - "src/learnloop/attempts/fact_predicates.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.fact_predicates module"
  - "src/learnloop/attempts/fact_predicates.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.fact_predicates`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.fact_predicates` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: The yes-or-no questions readers ask of an attempt's facts, each under its owner's name.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/fact_predicates.py](../../../../../../src/learnloop/attempts/fact_predicates.py) |
| Source lines | 185 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `counts_as_assisted(facts: AttemptFacts) -> bool` ([source](../../../../../../src/learnloop/attempts/fact_predicates.py), line 35) — The canonical assistance test (``attempt_counts_as_assisted``, policy ``causal_activity_v1``): a legacy assisted attempt type, any hint, or primed.
- `recorded_counts_as_assisted(facts: AttemptFacts, recorded: Mapping[str, Any] | None, reference_status: str | None=None) -> bool` ([source](../../../../../../src/learnloop/attempts/fact_predicates.py), line 44) — The canonical test unioned with the attempt's recorded causal classification (``resolve_attempt_activity_policy``): what ``facet_outcome_observations.assisted`` stores, and what the canonical projection and the facet timeline read.
- `intervention_assisted(facts: AttemptFacts) -> bool` ([source](../../../../../../src/learnloop/attempts/fact_predicates.py), line 58) — Intervention outcomes' test (``intervention_outcomes.is_assisted``): any attempt type outside the three unaided productions (so an open-text answer counts), a hint, or primed.
- `unassisted_for_coldness(facts: AttemptFacts, scan: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/fact_predicates.py), line 70) — The coldness receipt's ``unassisted`` dimension for a cold attempt (``coldness_receipt._unassisted``): its status and its evidence.
- `fsrs_cap_value(mapping: dict[int | str, object], hints_used: int) -> object | None` ([source](../../../../../../src/learnloop/attempts/fact_predicates.py), line 85) — The item's ``fsrs_rating_cap_by_hint`` entry for a hint count: the exact key, its string form, else the largest numeric key at or below the count (None when there is none).
- `fsrs_rating_cap(facts: AttemptFacts, cap_by_hint: dict[int | str, object]) -> object | None` ([source](../../../../../../src/learnloop/attempts/fact_predicates.py), line 106) — The cap the item's hint policy puts on an attempt's FSRS rating, from the submitted hint count (the grade application reads ``draft.hints_used``; replay and fitting the stored ``hints_used``).
- `diagnoser_assisted(facts: AttemptFacts) -> bool` ([source](../../../../../../src/learnloop/attempts/fact_predicates.py), line 122) — The diagnoser's ``assisted`` (``HistoryAttempt.assisted``): a hint, or an assisted attempt type; primed is its own field, so a primed attempt without a hint is not assisted here.
- `diagnoser_cold_unassisted(facts: AttemptFacts) -> bool` ([source](../../../../../../src/learnloop/attempts/fact_predicates.py), line 129) — The diagnoser's "demonstrated" test (``HistoryAttempt.cold_unassisted``): neither assisted nor primed.
- `unhelped_cold_type(facts: AttemptFacts, cold_types: Collection[str]=COLD_CHECK_TYPES) -> bool` ([source](../../../../../../src/learnloop/attempts/fact_predicates.py), line 142) — A cold-type answer, unprimed, with no hint (the teacher brief's "cold").
- `graded_cold_check(facts: AttemptFacts, cold_types: Collection[str]) -> bool` ([source](../../../../../../src/learnloop/attempts/fact_predicates.py), line 148) — The lesson suggestion's cold check: a cold-type answer, unprimed, with no hint, and graded.
- `teacher_attempt_kind(facts: AttemptFacts) -> Any` ([source](../../../../../../src/learnloop/attempts/fact_predicates.py), line 155) — The teacher brief's word for an attempt in a learner's history: ``cold``, ``assisted`` (an assisted type or a hint), ``primed``, else the attempt type itself.
- `hinted_or_primed(facts: AttemptFacts) -> bool` ([source](../../../../../../src/learnloop/attempts/fact_predicates.py), line 167) — The router card's per-LO ``assisted`` count: a hint or primed, whatever the attempt type.
- `primed_only(facts: AttemptFacts) -> bool` ([source](../../../../../../src/learnloop/attempts/fact_predicates.py), line 173) — The ``assisted`` field the router card's recent work and the chat packet's traces show: primed alone (the hint count is the field beside it).

### Module constants

- `DIAGNOSER_ASSISTED_TYPES` ([src/learnloop/attempts/fact_predicates.py](../../../../../../src/learnloop/attempts/fact_predicates.py), line 117)
- `COLD_CHECK_TYPES` ([src/learnloop/attempts/fact_predicates.py](../../../../../../src/learnloop/attempts/fact_predicates.py), line 139)

### Explicit exports

`__all__` declares:

- `COLD_CHECK_TYPES`
- `DIAGNOSER_ASSISTED_TYPES`
- `counts_as_assisted`
- `diagnoser_assisted`
- `diagnoser_cold_unassisted`
- `fsrs_cap_value`
- `fsrs_rating_cap`
- `graded_cold_check`
- `hinted_or_primed`
- `intervention_assisted`
- `primed_only`
- `recorded_counts_as_assisted`
- `teacher_attempt_kind`
- `unhelped_cold_type`
- `unassisted_for_coldness`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `fsrs_cap_value`; statically calls `fsrs_cap_value`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `graded_cold_check`; statically calls `graded_cold_check`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `hinted_or_primed`, `primed_only`; statically calls `hinted_or_primed`, `primed_only`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `DIAGNOSER_ASSISTED_TYPES`, `diagnoser_assisted`; statically calls `diagnoser_assisted`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `primed_only`; statically calls `primed_only`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `teacher_attempt_kind`, `unhelped_cold_type`; statically calls `teacher_attempt_kind`, `unhelped_cold_type`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]] — imports `_unassisted`; calls `_unassisted`
- [[Reference/Modules/learnloop/attempts/facts|learnloop.attempts.facts]] — imports `AttemptFacts`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `attempt_counts_as_assisted`, `resolve_attempt_activity_policy`; calls `attempt_counts_as_assisted`, `resolve_attempt_activity_policy`
- [[Reference/Modules/learnloop/substrate/intervention_outcomes|learnloop.substrate.intervention_outcomes]] — imports `is_assisted`; calls `is_assisted`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]], [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_attempt_fact_predicates.py](../../../../../../tests/test_attempt_fact_predicates.py) — direct import
  - `test_every_predicate_equals_its_readers_expression_on_the_matrix`
  - `test_the_fsrs_cap_lookup_keeps_key_coercion_and_fallback`
  - `test_the_recorded_classification_reaches_the_projections_assisted`
- [tests/test_attempt_facts_census.py](../../../../../../tests/test_attempt_facts_census.py) — direct import

## Modification guidance

- Change fact predicates policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/fact_predicates.py](../../../../../../src/learnloop/attempts/fact_predicates.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
