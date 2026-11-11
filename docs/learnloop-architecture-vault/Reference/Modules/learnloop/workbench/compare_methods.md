---
title: "learnloop.workbench.compare_methods"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/workbench/compare_methods.py"
source_paths:
  - "src/learnloop/workbench/compare_methods.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.workbench"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.workbench.compare_methods module"
  - "src/learnloop/workbench/compare_methods.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-workbench"
---

# `learnloop.workbench.compare_methods`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.workbench.compare_methods` exists within [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] to own the behavior summarized by its module contract: Reader workbench RW2c: "Compare with the book's method" after a correct Submit (spec_reader_workbench_v1 §5.10, §5.4, G40).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py) |
| Source lines | 570 |
| Owning package | [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class MethodDifference(WireModel)` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 117)
- `class CompareMethodsOutputV1(WireModel)` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 123)
- `compare_enabled(vault: Any) -> bool` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 129)
- `book_solution(vault: Any, repository: Repository, item: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 143) — The book's solution passage for an imported exercise whose key status is ``book_solution``, by the span ids its key check recorded; None otherwise, or when any of it is exam material.
- `reference_for(vault: Any, repository: Repository, item: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 182)
- `reference_hash(reference: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 189) — The identity of a reference as shown: its kind, text and span ids (F9).
- `offer(vault: Any, repository: Repository, attempt_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 222) — Whether "Compare with the book's method" is offered for this attempt: only after a correct Submit of a workbench problem (not a held grade, not an exam item).
- `class CompareRefused(Exception)` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 270)
  - `__init__(self, reason: str) -> None` (line 271; internal)
- `open_comparison(vault: Any, repository: Repository, attempt_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 276) — Write the row and the reveal in one transaction, then return what the screen shows (the reference, the learner's steps).
- `view(row: Mapping[str, Any], *, reference: Mapping[str, Any], steps: Sequence[Mapping[str, Any]], reveal_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 337)
- `build_prompt(item: Any, reference: Mapping[str, Any], steps: Sequence[Mapping[str, Any]], *, request_id: str) -> str` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 354)
- `validate(output: CompareMethodsOutputV1, steps: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 367) — Lines that name an existing step (or none), of a known kind, one line each, bounded; the verdict line in plain words.
- `compare_lines(vault: Any, repository: Repository, assist_id: str, *, client: Any | None=None, clock: Clock | None=None, cancelled: Any | None=None, still_enabled: Any | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 441) — Ask for the lines and keep them on the row.

### Module constants

- `KIND` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 83)
- `PROMPT_VERSION` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 84)
- `BASIS_PREFIX` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 85)
- `CORRECT` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 87)
- `LINE_CHARS` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 88)
- `MAX_DIFFERENCES` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 89)
- `DIFFERENCE_KINDS` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 90)
- `REFERENCE_CHARS` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 91)
- `STEP_CHARS` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 92)
- `OFFER_LABEL` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 93)
- `LINES_LABEL` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 94)
- `LEARNER_LABEL` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 95)
- `BOOK_LABEL` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 96)
- `KEY_LABEL` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 97)
- `VALID_ROUTE_LINE` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 98)
- `SAME_ROUTE_LINE` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 99)
- `LEDGER_TASK` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 101)
- `CLAIM_SECONDS` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 104)
- `IN_PROGRESS_MESSAGE` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 105)
- `_INSTRUCTIONS` ([src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py), line 107)

### Explicit exports

`__all__` declares:

- `BASIS_PREFIX`
- `CLAIM_SECONDS`
- `LEDGER_TASK`
- `CompareMethodsOutputV1`
- `CompareRefused`
- `KIND`
- `OFFER_LABEL`
- `PROMPT_VERSION`
- `book_solution`
- `compare_enabled`
- `compare_lines`
- `offer`
- `open_comparison`
- `reference_for`
- `reference_hash`
- `validate`
- `view`

## Internal implementation anchors

- `_key_text(item: Any) -> str` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 138)
- `_exam_item(vault: Any, repository: Repository, item: Any) -> bool` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 197)
- `_attempt(repository: Repository, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 208)
- `_steps(repository: Repository, session_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 254)
- `_stamp(attempt_created_at: str, clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 263)
- `_placement_of(connection: Any, assist_id: str) -> tuple[dict[str, Any] | None, dict[str, Any]]` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 389)
- `_claim_live(claim: Any, now: Any) -> bool` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 394)
- `_claim(repository: Repository, assist_id: str, *, clock: Clock | None) -> tuple[str, Any]` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 401) — Claim the lines (F7): ``("claimed", token)``, ``("ready", lines)``, ``("in_progress", None)`` or ``("not_found", None)``, decided in one write transaction (``BEGIN IMMEDIATE``) so two workers never both claim.
- `_release(repository: Repository, assist_id: str, token: str) -> None` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 422) — Give a claim back (the call did not produce lines), only if still ours.
- `_verdict(lines: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/workbench/compare_methods.py), line 435)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `compare_enabled`; statically calls `compare_enabled`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `compare_enabled`, `module`; statically calls `compare_enabled`, `compare_lines`, `offer`, `open_comparison`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `call_labels`, `content_key`; calls `call_labels`, `content_key`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `reveal_episode_id`; calls `reveal_episode_id`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`, `item_exam_status`; calls `exam_material`, `item_exam_status`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `module`; calls `assist`, `compare_rows_for`, `insert_assist`, `settle_compare`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `blocks_by_key`; calls `blocks_by_key`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `applicable_checks`, `effective_key_status`, `has_required_method`, `reference_content_hash`; calls `applicable_checks`, `effective_key_status`, `has_required_method`, `reference_content_hash`
- [[Reference/Modules/learnloop/db/stores/workbench|learnloop.db.stores.workbench]] — imports `module`; calls `session_for_attempt`, `steps_for_session`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `module`; calls `live_steps`, `statement_cleared`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `exam_withheld`; calls `exam_withheld`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `CheckRoute`, `CheckUnavailable`, `daily_envelope`; calls `CheckRoute`, `daily_envelope`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `json`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_compare_methods.py](../../../../../../tests/test_compare_methods.py) — direct import
  - `test_an_imported_exercise_with_a_book_solution_shows_the_books_passage_as_a_source_review`
  - `test_book_solution_reads_the_checked_span_ids_and_never_exam_material`
  - `test_f2_the_comparison_verdict_is_a_judgment_with_its_lines`
  - `test_f7_only_the_claims_holder_settles_and_a_stale_claim_can_be_taken_over`
  - `test_f7_reopening_a_pending_comparison_starts_no_second_generation`
  - `test_f8_switching_compare_methods_off_while_its_lines_are_written_delivers_nothing`
  - `test_f9_a_changed_reference_opens_a_new_comparison_with_its_own_reveal`
  - `test_f9_lines_are_never_written_against_a_reference_other_than_the_rows`
  - `test_offered_only_after_a_correct_workbench_submit`
  - `test_the_lines_run_on_the_check_route_and_name_a_valid_route_valid`
- [tests/test_rw2c_fix_round3.py](../../../../../../tests/test_rw2c_fix_round3.py) — direct import
  - `test_l4_switching_compare_methods_off_after_the_open_makes_no_call`
  - `test_l6_the_compare_rpcs_refuse_a_problem_whose_exercise_is_withheld_now`

## Modification guidance

- Make changes here when the responsibility remains compare methods within learnloop.workbench; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/workbench/compare_methods.py](../../../../../../src/learnloop/workbench/compare_methods.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
