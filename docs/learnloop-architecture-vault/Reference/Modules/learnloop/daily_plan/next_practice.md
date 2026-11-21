---
title: "learnloop.daily_plan.next_practice"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/next_practice.py"
source_paths:
  - "src/learnloop/daily_plan/next_practice.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.next_practice module"
  - "src/learnloop/daily_plan/next_practice.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.next_practice`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.next_practice` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: What comes next, dated: the session's finish and Today say it from this one read.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/next_practice.py](../../../../../../src/learnloop/daily_plan/next_practice.py) |
| Source lines | 241 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `next_practice(vault: Any, repository: Any, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/next_practice.py), line 61) — The dated summary at ``clock``'s now (see the module's docstring).
- `next_practice_or_none(vault: Any, repository: Any, *, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/next_practice.py), line 165) — :func:`next_practice` for a reply that must not fail on it: ``None`` (the screens then say nothing of it).

### Module constants

- `_CHECK_KINDS` ([src/learnloop/daily_plan/next_practice.py](../../../../../../src/learnloop/daily_plan/next_practice.py), line 36)
- `_WRITING_JOB_STATUSES` ([src/learnloop/daily_plan/next_practice.py](../../../../../../src/learnloop/daily_plan/next_practice.py), line 39)

### Explicit exports

`__all__` declares:

- `next_practice`
- `next_practice_or_none`

## Internal implementation anchors

- `_iso(moment: datetime) -> str` ([source](../../../../../../src/learnloop/daily_plan/next_practice.py), line 42)
- `_local_day(moment: datetime) -> date` ([source](../../../../../../src/learnloop/daily_plan/next_practice.py), line 46) — The plan's calendar day of an instant: the local zone's offset at that instant, not now's.
- `_day_start(day: date) -> datetime` ([source](../../../../../../src/learnloop/daily_plan/next_practice.py), line 52)
- `_supported(estimate: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/next_practice.py), line 57)
- `_unique(values: Iterable[Any]) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/next_practice.py), line 175)
- `_open_checks(reader: Any, now: datetime) -> list[Mapping[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/next_practice.py), line 179) — The checks on your own still to come or open now: not taken, not expired.
- `_question_work(reader: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/next_practice.py), line 195) — The question work under way, by what it waits on: ``writing`` (topics an unfinished writing job has not finished: its payload's topics less the parts it wrote or stopped on), ``waiting`` (finished sections whose writing waits for their book's topics or for the desktop) and ``hel…

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `next_practice_or_none`; statically calls `next_practice_or_none`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `next_practice_or_none`; statically calls `next_practice_or_none`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `review_population`; calls `review_population`
- [[Reference/Modules/learnloop/daily_plan/estimates|learnloop.daily_plan.estimates]] — imports `Estimator`, `load_duration_evidence`; calls `Estimator`, `load_duration_evidence`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/reader|learnloop.db.stores.reader]] — imports `SECTION_DEFERRED_TO_PRIMARY`, `SECTION_ENQUEUING`, `SECTION_WAITING_FOR_BUILD`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `intent_serving`; calls `intent_serving`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `practice_item_servable`; calls `practice_item_servable`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]], [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_next_practice.py](../../../../../../tests/test_next_practice.py) — direct import
  - `test_it_reads_nothing_through_the_callers_repository`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_the_session_finish_stands_when_what_comes_next_cannot_be_read`

## Modification guidance

- Make changes here when the responsibility remains next practice within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/next_practice.py](../../../../../../src/learnloop/daily_plan/next_practice.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
