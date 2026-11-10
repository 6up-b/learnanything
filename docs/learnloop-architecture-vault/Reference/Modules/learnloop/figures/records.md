---
title: "learnloop.figures.records"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/records.py"
source_paths:
  - "src/learnloop/figures/records.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figures.records module"
  - "src/learnloop/figures/records.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.records`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.records` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: The figures' decision records (ADR-017, refactor B4): why a figure was built ahead of need or not, and why an author's attempt was kept or not.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py) |
| Source lines | 423 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `code(value: Any) -> str | None` ([source](../../../../../../src/learnloop/figures/records.py), line 110) — ``value`` when it is an id or a code constant (``provenance.check_no_prose``), else a short hash of it, so a ref that happens to hold text never carries the text and never drops the record.
- `number(value: Any, digits: int | None=None) -> float | None` ([source](../../../../../../src/learnloop/figures/records.py), line 122) — A finite float (rounded to ``digits`` when given), or None.
- `write_records(repository: Any, records: Iterable[provenance.DecisionRecord]) -> list[str | None]` ([source](../../../../../../src/learnloop/figures/records.py), line 136) — Write each record with its own short transaction (``write_decision``); never raises.
- `in_one_trace(records: Sequence[provenance.DecisionRecord]) -> list[provenance.DecisionRecord]` ([source](../../../../../../src/learnloop/figures/records.py), line 142) — The records under the current trace, or one trace born for all of them (outside every entry point each write would otherwise birth its own).
- `prebuild_record(row: Mapping[str, Any], decision: Any, model: Any, *, draw_index: int, seed: str | None, builds_left: int, render_left: float, on_mains: bool, plan_waiting: bool, expected_requests: float) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/figures/records.py), line 154) — The ``figure_prebuild`` record of one decided candidate (``row`` is its ledger row).
- `class FilterLog` ([source](../../../../../../src/learnloop/figures/records.py), line 206) — One filter pass's exclusions by rule (request keys), and what it kept.
  - `exclude(self, rule: str, candidate: Any) -> None` (line 214; public)
  - `record(self) -> provenance.DecisionRecord | None` (line 221; public) — The ``figure_prefetch_filter`` record, or None when nothing was excluded.
- `build_stop_record(rule: str, status: str, decision_id: str, *, waiting: Sequence[str]=(), error: BaseException | None=None, refusal: str | None=None) -> provenance.DecisionRecord` ([source](../../../../../../src/learnloop/figures/records.py), line 242) — A ``figure_prebuild_stop`` record: the build of ``decision_id`` stopped (``deferred``: it and the queue after it wait for a later pass), passed over (``excluded``), refused or failed.
- `spec_problem(problems: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/figures/records.py), line 263) — A parser's problems as a code: a prediction's own problem, or the spec's.
- `sketch_problem(problems: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/figures/records.py), line 269)
- `class AuthorAttempts` ([source](../../../../../../src/learnloop/figures/records.py), line 284) — What each author attempt came to, noted as the loop runs (list appends only: nothing here can change the loop's control flow), and written as ``figure_author`` records when the build ends.
  - `start(self, number: int) -> None` (line 291; public)
  - `current(self) -> _Attempt | None` (line 295; public)
  - `end(self, rule: str, *, status: str | None=None, error: BaseException | None=None, problems: int | None=None) -> None` (line 298; public) — The current attempt's verdict: ``rule`` its code (a retry follows, or it was the last).
  - `extra(self, problem: str) -> None` (line 309; public)
  - `fact(self, **facts: Any) -> None` (line 313; public)
  - `records(self, *, request: Any, request_id: str | None, model: Any, outcome: Any=None, error: BaseException | None=None) -> list[provenance.DecisionRecord]` (line 317; public) — One record per attempt (one for the refusal when the build stopped before any).
  - `write(self, repository: Any, **kwargs: Any) -> None` (line 370; public) — :meth:`records`, written; never raises (a record never changes the build it describes).

### Module constants

- `_LOG` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 34)
- `KIND_PREBUILD` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 36)
- `KIND_FILTER` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 37)
- `KIND_BUILD_STOP` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 38)
- `KIND_AUTHOR` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 39)
- `MAX_KEYS_PER_RULE` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 42)
- `FILTER_PROTECTION_UNAVAILABLE` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 45)
- `FILTER_DUPLICATE` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 46)
- `FILTER_OPEN_HORIZON` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 47)
- `FILTER_DECIDED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 48)
- `FILTER_NO_SPANS` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 49)
- `FILTER_SHOW_ME_OFF` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 50)
- `FILTER_WITHHELD` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 51)
- `FILTER_GROUNDING_WITHHELD` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 52)
- `FILTER_ITEM_PROTECTED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 53)
- `FILTER_ALREADY_BUILT` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 54)
- `STOP_FOREGROUND` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 57)
- `STOP_RICH_IN_FLIGHT` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 58)
- `STOP_OFF_MAINS` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 59)
- `STOP_AUTHOR_NOT_PLAN` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 60)
- `STOP_ITEM_PROTECTED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 61)
- `STOP_BUILT_ALREADY` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 62)
- `STOP_RENDER_MINUTES` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 63)
- `STOP_DAILY_BUILDS` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 64)
- `STOP_BUILD_REFUSED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 65)
- `STOP_BUILD_FAILED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 66)
- `STOP_RICH_JOB_RUNNING` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 67)
- `MODEL_FAILED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 71)
- `STATUS_INVALID` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 73)
- `TIER_REASON_MISSING` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 75)
- `LABEL_TEXT` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 77)
- `LABEL_TEXT_STRIPPED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 79)
- `PREDICTION_INVALID` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 81)
- `PREDICTION_DROPPED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 83)
- `SPEC_INVALID` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 85)
- `SKETCH_INVALID` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 87)
- `BRIEF_INVALID` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 89)
- `VERIFICATION_FAILED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 91)
- `SOURCE_DIFFERS` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 93)
- `QUICK_DROPPED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 95)
- `ACCEPTED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 97)
- `UNSUPPORTED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 98)
- `BUILD_ERROR` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 100)
- `INTERRUPTED` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 102)
- `_KEPT` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 104)
- `_AUTHOR_STATUSES` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 106)
- `_PREDICTION_PROBLEM` ([src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py), line 107)

### Explicit exports

`__all__` declares:

- `ACCEPTED`
- `AuthorAttempts`
- `BRIEF_INVALID`
- `FilterLog`
- `KIND_AUTHOR`
- `KIND_BUILD_STOP`
- `KIND_FILTER`
- `KIND_PREBUILD`
- `LABEL_TEXT`
- `MAX_KEYS_PER_RULE`
- `MODEL_FAILED`
- `PREDICTION_DROPPED`
- `PREDICTION_INVALID`
- `SOURCE_DIFFERS`
- `SPEC_INVALID`
- `STATUS_INVALID`
- `VERIFICATION_FAILED`
- `build_stop_record`
- `code`
- `in_one_trace`
- `number`
- `prebuild_record`
- `write_records`

## Internal implementation anchors

- `_measurements(waits: Any) -> int` ([source](../../../../../../src/learnloop/figures/records.py), line 189) — The measured latencies behind W: the quick tiers share one sample (the author call's duration counts for grammar and sketch alike), each rich tier's are its own requests.
- `_posterior_draws() -> int` ([source](../../../../../../src/learnloop/figures/records.py), line 199)
- `class _Attempt` ([source](../../../../../../src/learnloop/figures/records.py), line 274)
- `_outcome(outcome: Any, error: BaseException | None) -> tuple[str | None, str | None, str]` ([source](../../../../../../src/learnloop/figures/records.py), line 382) — The stored (or reused) figure's id, a rich-only build's job id, and the build's result as a code.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `FilterLog`, `build_stop_record`, `in_one_trace`, `prebuild_record`, `write_records`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `module`; statically calls `AuthorAttempts`, `code`, `sketch_problem`, `spec_problem`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/provenance|learnloop.db.stores.provenance]] — imports `write_decision`; calls `write_decision`
- [[Reference/Modules/learnloop/figures/prefetch_model|learnloop.figures.prefetch_model]] — imports `POSTERIOR_DRAWS`, `QUICK_TIERS`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `module`; calls `DecisionRecord`, `check_no_prose`, `current_trace`, `new_trace_id`, `where`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `logging`, `math`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figure_decision_records.py](../../../../../../tests/test_figure_decision_records.py) — direct import
  - `test_a_bad_prediction_drops_itself_and_says_so`
  - `test_a_failed_model_call_is_model_failed_with_its_exception_class`
  - `test_a_figure_stored_failed_keeps_both_attempts_problems`
  - `test_a_pass_that_excludes_nothing_writes_no_filter_record`
  - `test_a_queue_stopped_by_foreground_work_records_what_waits`
  - `test_a_refused_build_leaves_a_refused_record`
  - `test_a_refused_or_failed_prebuild_is_a_stop_record`
  - `test_a_rich_only_build_names_its_job_and_an_interrupted_build_its_error`
  - `test_attempt_one_problem_survives_an_accepted_second_attempt`
  - `test_deferred_and_capped_decisions_are_deferred_records`
  - `test_label_text_is_its_own_code`
  - `test_prebuilds_record_no_measured_latency_then_sampled_eu_positive_with_the_wait_and_seed`
  - `test_protection_exclusions_are_counted_by_rule_with_ten_keys`
  - `test_records_that_cannot_be_built_or_written_change_no_decision_build_or_prompt`
  - `test_the_recorded_seed_redraws_the_pass_exactly`
  - `test_unreadable_protection_cuts_the_whole_pass_and_says_so`

## Modification guidance

- Make changes here when the responsibility remains records within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/records.py](../../../../../../src/learnloop/figures/records.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
