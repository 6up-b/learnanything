---
title: "learnloop.why.reader"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/why/reader.py"
source_paths:
  - "src/learnloop/why/reader.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.why"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.why.reader module"
  - "src/learnloop/why/reader.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-why"
---

# `learnloop.why.reader`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/why/_package|learnloop.why]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.why.reader` exists within [[Reference/Modules/learnloop/why/_package|learnloop.why]] to own the behavior summarized by its module contract: The one read behind ``learnloop why``, the sidecar's ``why.get``, ``router trace`` and ``trace-evidence`` (ADR-017).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/why/reader.py](../../../../../../src/learnloop/why/reader.py) |
| Source lines | 408 |
| Owning package | [[Reference/Modules/learnloop/why/_package|learnloop.why]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `objective_trace_pointer(connection: Any, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/why/reader.py), line 41) — The router objective trace of a router decision, as ids and versions (``learnloop router trace`` shows it).
- `found_anything(answer: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/why/reader.py), line 193)
- `answer(repository: Any, target: str | None=None, *, kind: str | None=None, first_build: bool=False, loaded: Any=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/why/reader.py), line 198) — Why the decisions ``target`` names went the way they did; None when nothing answers (``not_found``).
- `scheduler_explanation(loaded: Any, repository: Any, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/why/reader.py), line 248) — Today's scheduler explanation of one item, computed without persisting it; else its latest stored one.
- `item_exclusions(loaded: Any, repository: Any, practice_item_id: str, explanation: dict[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/why/reader.py), line 278) — ``item:<id>``: the newest slate records naming the item, and, off today's slate, the rule keeping it off.
- `attempt_evidence(connection: Any, attempt_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/why/reader.py), line 312) — The facets the grader saw an attempt exercise (A6), as ids and codes; the grader's words stay in the table.
- `evidence_report(repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/why/reader.py), line 322) — ``learnloop trace-evidence``: A6's concentration and A1 guard 1's unexercised supporting mass.
- `objective_trace(connection: Any, decision: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/why/reader.py), line 330) — ``learnloop router trace``: one decision's router objective trace and, for a drawn lesson offer, its binding.
- `call_ids(answer: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/why/reader.py), line 349) — Every model call an answer names: its traces' calls, the discarded and unclaimed ones, the reconstructed.
- `payloads(repository: Any, ids: Iterable[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/why/reader.py), line 362) — The prompt and output each call's receipt holds, under the receipts' own retention.
- `codes_only(value: Any, path: str='') -> tuple[Any, list[str]]` ([source](../../../../../../src/learnloop/why/reader.py), line 380) — ``value`` with every string that is not an id, a number or a code (:func:`provenance.is_code`) removed, and the paths removed.

### Module constants

- `VERSION` ([src/learnloop/why/reader.py](../../../../../../src/learnloop/why/reader.py), line 24)
- `FIGURE_PREBUILD` ([src/learnloop/why/reader.py](../../../../../../src/learnloop/why/reader.py), line 26)
- `RECONSTRUCTED_KINDS` ([src/learnloop/why/reader.py](../../../../../../src/learnloop/why/reader.py), line 28)
- `_CANDIDATE_FACTS` ([src/learnloop/why/reader.py](../../../../../../src/learnloop/why/reader.py), line 83)
- `_JSON_COLUMNS` ([src/learnloop/why/reader.py](../../../../../../src/learnloop/why/reader.py), line 235)

## Internal implementation anchors

- `_outcome(connection: Any, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/why/reader.py), line 35)
- `_decision(connection: Any, record: provenance.DecisionRecord, children: list[provenance.DecisionRecord], discarded: list[dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/why/reader.py), line 49)
- `_native_first_build(connection: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/why/reader.py), line 87) — The last ``excluded`` pre-build before the first ``chosen`` one, and the facts that differ between them.
- `_records_answer(repository: Any, target: str, kind: str | None, *, first_build: bool, timeout_now: float | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/why/reader.py), line 135)
- `_bad_rows(repository: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/why/reader.py), line 238)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `evidence_report`, `module`; statically calls `answer`, `call_ids`, `evidence_report`, `payloads`
- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `objective_trace`; statically calls `objective_trace`
- [[Reference/Modules/learnloop_sidecar/handlers/why|learnloop_sidecar.handlers.why]] — imports `module`; statically calls `answer`, `codes_only`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/trace_evidence|learnloop.attempts.trace_evidence]] — imports `trace_evidence_report`; calls `trace_evidence_report`
- [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] — imports `discarded_calls`, `trace_model_calls`, `unclaimed_calls`; calls `discarded_calls`, `trace_model_calls`, `unclaimed_calls`
- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `table_present`, `trace`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `is_code`, `read`, `read_children`, `read_kind`, `read_naming`, `where`
- [[Reference/Modules/learnloop/router_objective/offer_report|learnloop.router_objective.offer_report]] — imports `binding`; calls `binding`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `exclusion_now`, `explain_practice_item`; calls `exclusion_now`, `explain_practice_item`
- [[Reference/Modules/learnloop/scheduling/slate_record|learnloop.scheduling.slate_record]] — imports `KIND`, `item_outcome`; calls `item_outcome`
- [[Reference/Modules/learnloop/why/reconstructed|learnloop.why.reconstructed]] — imports `module`; calls `code`, `first_build`, `first_measurement`, `moment`, `resolve`, `select_one`, `select_rows`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop_sidecar/handlers/why|learnloop_sidecar.handlers.why]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_why_reader.py](../../../../../../tests/test_why_reader.py) — direct import
  - `test_codes_only_keeps_ids_numbers_codes_and_times_and_names_what_it_drops`
  - `test_why_get_returns_ids_numbers_and_codes_and_never_a_payload`

## Modification guidance

- Make changes here when the responsibility remains reader within learnloop.why; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/why/reader.py](../../../../../../src/learnloop/why/reader.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
