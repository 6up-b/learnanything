---
title: "learnloop.daily_plan.router_teach_back"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/router_teach_back.py"
source_paths:
  - "src/learnloop/daily_plan/router_teach_back.py"
source_commit: "024b1d9eab85a4dee0696c584e67af1e20403618"
source_commit_timestamp: "2026-10-15T06:30:02-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.daily_plan.router_teach_back module"
  - "src/learnloop/daily_plan/router_teach_back.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.router_teach_back`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.router_teach_back` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Router R2c: teach-back dialogues summarized into the card's typed evidence (spec §15.1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/router_teach_back.py](../../../../../../src/learnloop/daily_plan/router_teach_back.py) |
| Source lines | 304 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `024b1d9eab85a4dee0696c584e67af1e20403618` |
| Commit timestamp | `2026-10-15T06:30:02-04:00` |

## Public API

- `class TeachBackSummary(WireModel)` ([source](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 62)
- `summary_prompt(topic: str, result: str, transcript: str) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 69)
- `grading_revision(connection: Any, attempt_id: str) -> str | None` ([source](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 102) — A fingerprint of the attempt's grade as it stands: its score, its latest blind grade record and its live (non-superseded) grading evidence.
- `summarize(vault: Any, repository: Any, attempt_id: str, *, runtime: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 128) — Summarize one graded teach-back attempt and store it; returns the stored summary.
- `summaries_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 208)
- `schedule(vault: Any, sqlite_path: Any, attempt_id: str, *, runtime: Any=None) -> threading.Thread | None` ([source](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 214) — Summarize a just-graded teach-back off the hot path (a daemon thread; inline in an inline runtime).
- `summaries_for(connection: Any, learning_object_ids: Sequence[str], *, before: str, withheld: protection.Withheld, titles: Mapping[str, str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 243) — The card's typed evidence: summaries of teach-backs on these topics, made before ``before``.

### Module constants

- `LOG` ([src/learnloop/daily_plan/router_teach_back.py](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 48)
- `PURPOSE` ([src/learnloop/daily_plan/router_teach_back.py](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 50)
- `VERSION` ([src/learnloop/daily_plan/router_teach_back.py](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 51)
- `CACHE_PREFIX` ([src/learnloop/daily_plan/router_teach_back.py](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 52)
- `SECTION` ([src/learnloop/daily_plan/router_teach_back.py](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 53)
- `MAX_POINTS` ([src/learnloop/daily_plan/router_teach_back.py](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 55)
- `POINT_LIMIT` ([src/learnloop/daily_plan/router_teach_back.py](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 56)
- `CARD_LIMIT` ([src/learnloop/daily_plan/router_teach_back.py](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 58)
- `TIMEOUT_SECONDS` ([src/learnloop/daily_plan/router_teach_back.py](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 59)

### Explicit exports

`__all__` declares:

- `CACHE_PREFIX`
- `PURPOSE`
- `SECTION`
- `TeachBackSummary`
- `grading_revision`
- `schedule`
- `summaries_active`
- `summaries_for`
- `summarize`
- `summary_prompt`

## Internal implementation anchors

- `_clip(points: Sequence[str], limit: int) -> list[str]` ([source](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 87)
- `_result_word(correctness: Any) -> str` ([source](../../../../../../src/learnloop/daily_plan/router_teach_back.py), line 95)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `module`; statically calls `summaries_for`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `schedule`; statically calls `schedule`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `is_subscription_transport`; calls `is_subscription_transport`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `mixture_active`; calls `mixture_active`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `LLM`, `SUMMARY_RECEIPT_OWNER`, `SpendRefused`, `_supports_isolation`, `default_runtime`; calls `_supports_isolation`, `default_runtime`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `attempt_grade_held`, `held_for_review_attempts`; calls `attempt_grade_held`, `held_for_review_attempts`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `module`; calls `attempt_protection`, `withheld_items`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextvars`, `hashlib`, `json`, `logging`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mcp_c1a_landing.py](../../../../../../tests/test_mcp_c1a_landing.py) — direct import
  - `test_a_teach_back_on_an_item_a_cold_check_holds_is_never_summarized`
  - `test_no_reader_keeps_a_protection_of_its_own`
- [tests/test_router_r2b_requests.py](../../../../../../tests/test_router_r2b_requests.py) — direct import
  - `test_every_router_answer_model_has_the_strict_schema_the_transports_send`
- [tests/test_router_r2bc_landing.py](../../../../../../tests/test_router_r2bc_landing.py) — direct import
  - `test_the_teach_back_summarizer_reads_the_whole_dialogue`
- [tests/test_router_r2c_teach_back.py](../../../../../../tests/test_router_r2c_teach_back.py) — direct import
  - `test_a_graded_teach_back_is_summarized_into_the_next_card`
  - `test_a_held_teach_back_is_never_summarized`
  - `test_a_summary_leaves_the_card_once_its_grade_is_held_or_regraded`
  - `test_exam_or_reserved_work_is_never_summarized`
  - `test_summaries_run_only_where_the_mixture_serves`
  - `test_the_summarizer_never_sees_the_rubric_or_a_reference_answer`

## Modification guidance

- Make changes here when the responsibility remains router teach back within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/router_teach_back.py](../../../../../../src/learnloop/daily_plan/router_teach_back.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
