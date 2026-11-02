---
title: "learnloop.workbench.route_example"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/workbench/route_example.py"
source_paths:
  - "src/learnloop/workbench/route_example.py"
source_commit: "5825048f775dc44bf0dc7d1a4b5bcaa1b0bf7b9f"
source_commit_timestamp: "2026-10-22T16:23:31-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.workbench"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.workbench.route_example module"
  - "src/learnloop/workbench/route_example.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-workbench"
---

# `learnloop.workbench.route_example`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.workbench.route_example` exists within [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] to own the behavior summarized by its module contract: Reader workbench RW2c: a worked example that takes your route (spec_reader_workbench_v1 §5.10, G40).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/workbench/route_example.py](../../../../../../src/learnloop/workbench/route_example.py) |
| Source lines | 342 |
| Owning package | [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5825048f775dc44bf0dc7d1a4b5bcaa1b0bf7b9f` |
| Commit timestamp | `2026-10-22T16:23:31-04:00` |

## Public API

- `s3_available(vault: Any) -> tuple[bool, str | None]` ([source](../../../../../../src/learnloop/workbench/route_example.py), line 71) — Whether the sources spec's ``worked_example`` intent can run here.
- `examples_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/workbench/route_example.py), line 87)
- `available(vault: Any) -> bool` ([source](../../../../../../src/learnloop/workbench/route_example.py), line 91) — The switch is on and the sources spec's S3 can serve the intent.
- `learner_work_md(steps: Sequence[Any]) -> str` ([source](../../../../../../src/learnloop/workbench/route_example.py), line 97) — The learner's steps as the verification reads them (numbered).
- `caller_for_session(repository: Repository, workbench_session_id: str, item: Any) -> Any` ([source](../../../../../../src/learnloop/workbench/route_example.py), line 123) — The workbench session's caller: the item's practice context (assisted practice), cold when a cold administration of the item is open.
- `keep(vault: Any, repository: Repository, item: Any, hits: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/workbench/route_example.py), line 133) — The verified passages a learner may be shown, route first (module docstring).
- `example_for(vault: Any, repository: Repository, *, workbench_session_id: str, item: Any, steps: Sequence[Any], trigger: str, about_step_id: str | None=None, hint_assist_id: str | None=None, submission_id: str | None=None, find: Callable[..., Any] | None=None, envelope: Any | None=None, max_calls: int | None=None, draw_enabled: bool=False, seed: str | None=None, cancelled: Callable[[], bool] | None=None, verdicts: Sequence[Mapping[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/route_example.py), line 158) — Look for the example; write the row prepared (``shown = 0``).
- `example_line(passage: Mapping[str, Any], step_number: int | None) -> str` ([source](../../../../../../src/learnloop/workbench/route_example.py), line 308)
- `example_view(row: Mapping[str, Any], *, passage_draw: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/route_example.py), line 323) — What the workbench shows of a shown example (no passage text: the passage opens in the book).

### Module constants

- `KIND` ([src/learnloop/workbench/route_example.py](../../../../../../src/learnloop/workbench/route_example.py), line 58)
- `TRIGGERS` ([src/learnloop/workbench/route_example.py](../../../../../../src/learnloop/workbench/route_example.py), line 59)
- `MIN_HINT_LEVEL` ([src/learnloop/workbench/route_example.py](../../../../../../src/learnloop/workbench/route_example.py), line 61)
- `LIMIT` ([src/learnloop/workbench/route_example.py](../../../../../../src/learnloop/workbench/route_example.py), line 63)
- `ROUTE_LINE` ([src/learnloop/workbench/route_example.py](../../../../../../src/learnloop/workbench/route_example.py), line 64)
- `OTHER_ROUTE_LINE` ([src/learnloop/workbench/route_example.py](../../../../../../src/learnloop/workbench/route_example.py), line 65)
- `NOTHING_LINE` ([src/learnloop/workbench/route_example.py](../../../../../../src/learnloop/workbench/route_example.py), line 66)
- `QUERY_CHARS` ([src/learnloop/workbench/route_example.py](../../../../../../src/learnloop/workbench/route_example.py), line 67)
- `WORK_CHARS` ([src/learnloop/workbench/route_example.py](../../../../../../src/learnloop/workbench/route_example.py), line 68)

### Explicit exports

`__all__` declares:

- `KIND`
- `MIN_HINT_LEVEL`
- `NOTHING_LINE`
- `OTHER_ROUTE_LINE`
- `ROUTE_LINE`
- `TRIGGERS`
- `available`
- `caller_for_session`
- `example_for`
- `example_line`
- `example_view`
- `examples_enabled`
- `keep`
- `learner_work_md`
- `s3_available`

## Internal implementation anchors

- `_label(hit: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/workbench/route_example.py), line 103)
- `_default_find(vault: Any, repository: Repository, query: str, *, caller: Any, learner_work_md: str, owner_id: str) -> Any` ([source](../../../../../../src/learnloop/workbench/route_example.py), line 112) — The sources spec's search under the caller's derived policy and the service's own daily cap (``propose_sources``).
- `_settle(repository: Repository, assist_id: str, fields: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/workbench/route_example.py), line 153)
- `_verdicts_json(hint: Mapping[str, Any] | None, verdicts: Sequence[Mapping[str, Any]] | None) -> str | None` ([source](../../../../../../src/learnloop/workbench/route_example.py), line 296) — The verdicts an example row keeps (fix round 3, M1): after a hint, a copy of the hint's record as stored (read through the one accessor); on "show me", the workbench context's; None when neither is on record.
- `_metered(vault: Any) -> bool` ([source](../../../../../../src/learnloop/workbench/route_example.py), line 314)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]] — imports `module`; statically calls `example_view`, `examples_enabled`
- [[Reference/Modules/learnloop/workbench/passage_draw|learnloop.workbench.passage_draw]] — imports `caller_for_session`; statically calls `caller_for_session`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `module`; statically calls `examples_enabled`, `s3_available`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `module`; statically calls `available`, `example_for`, `example_line`, `example_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`, `spend_envelopes`; calls `spend_envelopes`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `module`; calls `assist`, `insert_assist`, `settle_bridge`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `caller_for`; calls `caller_for`
- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `propose_sources`; calls `propose_sources`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`; calls `plan_route`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `exam_withheld`; calls `exam_withheld`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `module`
- [[Reference/Modules/learnloop/symbolic_view|learnloop.symbolic_view]] — imports `has_verdict_record`, `verdict_records`; calls `has_verdict_record`, `verdict_records`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_leaks_expected`; calls `span_leaks_expected`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `session_calls_on`; calls `session_calls_on`
- [[Reference/Modules/learnloop/workbench/passage_draw|learnloop.workbench.passage_draw]] — imports `module`; calls `alternatives_view`, `best_class`, `draw`, `new_seed`, `option_id`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/workbench/ladder|learnloop.workbench.ladder]], [[Reference/Modules/learnloop/workbench/passage_draw|learnloop.workbench.passage_draw]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_workbench_route_example.py](../../../../../../tests/test_workbench_route_example.py) — direct import
  - `test_an_unverified_search_shows_nothing`
  - `test_review_f1_an_example_in_another_book_carries_that_books_identity`
  - `test_what_comes_back_is_filtered_and_the_route_stays_first`
  - `test_without_the_sources_specs_s3_the_example_is_absent_not_approximated`

## Modification guidance

- Make changes here when the responsibility remains route example within learnloop.workbench; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/workbench/route_example.py](../../../../../../src/learnloop/workbench/route_example.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
