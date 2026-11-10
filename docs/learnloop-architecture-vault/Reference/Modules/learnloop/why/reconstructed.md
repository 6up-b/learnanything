---
title: "learnloop.why.reconstructed"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/why/reconstructed.py"
source_paths:
  - "src/learnloop/why/reconstructed.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.why"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.why.reconstructed module"
  - "src/learnloop/why/reconstructed.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-why"
---

# `learnloop.why.reconstructed`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/why/_package|learnloop.why]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.why.reconstructed` exists within [[Reference/Modules/learnloop/why/_package|learnloop.why]] to own the behavior summarized by its module contract: Why x and not y for rows older than their decision records: what the old rows themselves can still say.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py) |
| Source lines | 699 |
| Owning package | [[Reference/Modules/learnloop/why/_package|learnloop.why]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `code(value: Any) -> Any` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 57) — ``value`` when it is a number, a bool or a code (:func:`provenance.is_code`); a free-form string as ``sha256:<16 hex>``, so an answer never carries text and never loses the id.
- `select_rows(connection: Any, sql: str, args: Sequence[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 75)
- `select_one(connection: Any, sql: str, args: Sequence[Any]=()) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 86)
- `moment(value: Any) -> datetime | None` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 101)
- `calls_for_owner(connection: Any, owner_ids: Iterable[str], *, owner_kind: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 134) — Calls whose ``owner_id`` is one of ``owner_ids`` (the old join), metadata only, with whether the output is present and, when absent, why (``failed``, ``interrupted``, ``never_finished``, ``pruned``).
- `late_calls(calls: Iterable[Mapping[str, Any]], decided_at: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 168) — Calls that started before ``decided_at`` and finished after it (``late_ms``) or never (``late_ms`` None).
- `router_decision(connection: Any, decision_id: str, *, timeout_now: float | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 260) — A ``router_decisions`` row as an answer: what won, the mix's alternatives, each model's answer, the inputs the row kept, versions and seed, its calls joined by the boundary key, the calls that answered after it, and next.
- `decisions_for_block(connection: Any, block_id: str) -> list[str]` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 324)
- `latest_decision(connection: Any) -> str | None` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 330)
- `offer_withdrawals(connection: Any, decision_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 348) — Each ``expired`` row that took ``decision_id``'s offer back, as an ``offer_withdrawn`` answer.
- `withdrawals_for_response(connection: Any, response_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 439)
- `problem_code(text: Any) -> str` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 447)
- `problem_path(text: Any) -> str | None` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 456) — A schema path at the head of a problem (``predictions.0.change.param``), when it is one; never the message.
- `figure(connection: Any, figure_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 486) — An ``interactive_figures`` row as a ``figure_author`` answer: its verification, the typed problem codes its report's text reduces to, the prompt version and model, its request, and its author calls.
- `prefetch_decision(connection: Any, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 556)
- `first_measurement(connection: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 579) — The first measured build latency: the first completed figure author call (the calls the quick tiers' wait W is measured from, ``figures.prefetch_ledger``), or the first pressed request.
- `first_build(connection: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 606) — The last skip, the first build and what changed between them, from ``figure_prefetch_decisions``: how many skips came before the first non-skip (overall and per trigger kind), and whether the first measured latency falls between the last skip and the first build.
- `resolve(connection: Any, target: str, *, timeout_now: float | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 658) — The reconstructed answers ``target`` names (empty when none): ``latest`` (the newest router decision), ``block:``, ``offer:``, ``decision:``, ``figure:``, or a bare router decision, figure, pre-build decision or offer response id.

### Module constants

- `LABEL` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 30)
- `ROUTER_OWNER` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 33)
- `FIGURE_OWNER_PREFIX` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 35)
- `FIGURE_AUTHOR_OWNER` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 36)
- `WITHDRAWN_KEY` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 38)
- `SUPERSEDED_KEY` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 39)
- `OFFER_PREFIX` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 41)
- `PREDICTION_INVALID` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 46)
- `VERIFICATION_FAILED` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 47)
- `SPEC_INVALID` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 48)
- `_PREDICTION_PROBLEM` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 49)
- `_INVARIANT_PROBLEM` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 50)
- `_PATH` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 51)
- `_CALL_COLUMNS` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 130)
- `_DECISION_COLUMNS` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 189)
- `_PREFETCH_COLUMNS` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 542)
- `_PREFETCH_MEASURES` ([src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py), line 546)

## Internal implementation anchors

- `_number(value: Any) -> float | int | None` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 69)
- `_json(text: Any, default: Any) -> Any` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 91)
- `_ms_between(start: Any, end: Any) -> int | None` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 111)
- `_error_type(text: Any) -> str | None` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 118) — The class at the head of a stored error (``TimeoutError: ...``), never the rest.
- `_decision_row(connection: Any, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 195)
- `_components(mixture: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 200)
- `_alternatives(row: Mapping[str, Any], mixture: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 216)
- `_decision_next(connection: Any, row: Mapping[str, Any], detail: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 230) — What came after a decision: its outcome row and responses (exact keys), and the plan's next decision (by time).
- `_workflow_for(connection: Any, item_id: str, before: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 338)
- `_figure_calls(connection: Any, figure: Mapping[str, Any]) -> tuple[list[dict[str, Any]], int | None]` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 463) — The author calls of a figure's build: owner ``figure:<content_key(input_hash, generation)>``, where the generation is how many builds of the same input came before it (a recount, so ``inferred``).
- `_prefetch(row: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 550)
- `_changed(before: Mapping[str, Any], after: Mapping[str, Any], names: Iterable[str]) -> dict[str, list[Any]]` ([source](../../../../../../src/learnloop/why/reconstructed.py), line 602)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/why/reader|learnloop.why.reader]] — imports `module`; statically calls `code`, `first_build`, `first_measurement`, `moment`, `resolve`, `select_one`, `select_rows`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `cap_alternatives`, `is_code`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `hashlib`, `json`, `re`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/why/reader|learnloop.why.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_why_reader.py](../../../../../../tests/test_why_reader.py) — direct import
  - `test_reconstructed_problem_codes_name_a_bad_prediction_and_its_schema_path`

## Modification guidance

- Make changes here when the responsibility remains reconstructed within learnloop.why; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/why/reconstructed.py](../../../../../../src/learnloop/why/reconstructed.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
