---
title: "learnloop.remote.sources"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/remote/sources.py"
source_paths:
  - "src/learnloop/remote/sources.py"
source_commit: "7a550e75a4a5ef9607d5eed7b078e70ca86b0435"
source_commit_timestamp: "2026-10-24T20:20:55-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.remote"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.remote.sources module"
  - "src/learnloop/remote/sources.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-remote"
---

# `learnloop.remote.sources`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.remote.sources` exists within [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] to own the behavior summarized by its module contract: Grounded passages for a chat host (spec_mcp_frontend_c1 §4.5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/remote/sources.py](../../../../../../src/learnloop/remote/sources.py) |
| Source lines | 425 |
| Owning package | [[Reference/Modules/learnloop/remote/_package|learnloop.remote]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7a550e75a4a5ef9607d5eed7b078e70ca86b0435` |
| Commit timestamp | `2026-10-24T20:20:55-04:00` |

## Public API

- `class SourcesUnavailable(RemoteRequestError)` ([source](../../../../../../src/learnloop/remote/sources.py), line 66) — The sources service is off or refused the request (a learner-readable reason).
  - `__init__(self, code: str, message: str) -> None` (line 69; internal)
- `class PassageResult` ([source](../../../../../../src/learnloop/remote/sources.py), line 78)
- `find_passages(vault: Any, repository: Any, query: str, *, call_id: str, intent: str='explain', learning_object_ids: Sequence[str]=(), misconception_id: str | None=None, verify: bool=False, limit: int=6, char_budget: int=DEFAULT_CHAR_BUDGET, clock: Clock | None=None, alias_key: bytes | None=None) -> PassageResult` ([source](../../../../../../src/learnloop/remote/sources.py), line 150) — Passages for ``query`` under the server-derived policy, recorded as exposure (in the same transaction as the final protection read) before they are returned.
- `plan_passages(vault: Any, repository: Any, query: str, *, intent: str='explain', learning_object_ids: Sequence[str]=(), misconception_id: str | None=None, verify: bool=False, limit: int=6, char_budget: int=DEFAULT_CHAR_BUDGET, alias_key: bytes | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/remote/sources.py), line 362) — Dry run of :func:`find_passages`: what it would pay for, at what cost.

### Module constants

- `CHAT_INTENTS` ([src/learnloop/remote/sources.py](../../../../../../src/learnloop/remote/sources.py), line 58)
- `DEFAULT_CHAR_BUDGET` ([src/learnloop/remote/sources.py](../../../../../../src/learnloop/remote/sources.py), line 59)
- `MAX_CHAR_BUDGET` ([src/learnloop/remote/sources.py](../../../../../../src/learnloop/remote/sources.py), line 60)
- `MIN_TAIL_CHARS` ([src/learnloop/remote/sources.py](../../../../../../src/learnloop/remote/sources.py), line 61)
- `_PROTECTING` ([src/learnloop/remote/sources.py](../../../../../../src/learnloop/remote/sources.py), line 63)
- `_UNREADABLE` ([src/learnloop/remote/sources.py](../../../../../../src/learnloop/remote/sources.py), line 73)

### Explicit exports

`__all__` declares:

- `CHAT_INTENTS`
- `DEFAULT_CHAR_BUDGET`
- `MAX_CHAR_BUDGET`
- `PassageResult`
- `SourcesUnavailable`
- `find_passages`
- `plan_passages`

## Internal implementation anchors

- `_item_files_unreadable(vault: Any) -> bool` ([source](../../../../../../src/learnloop/remote/sources.py), line 86) — Whether a practice item's file failed to load (its id is then unknown).
- `_protected_spans(vault: Any, repository: Any, withheld: Any) -> tuple[frozenset[tuple[str, str]], frozenset[str]]` ([source](../../../../../../src/learnloop/remote/sources.py), line 93) — The own passages of every item a check or reservation holds.
- `_named_los(vault: Any, repository: Any, learning_object_ids: Sequence[str], alias_key: bytes | None) -> tuple[list[str], list[str]]` ([source](../../../../../../src/learnloop/remote/sources.py), line 118) — The topics a request names, read as ``learning_context`` reads them (spec §4.7): an authored topic's id, or a generated topic's opaque alias.
- `_scope(vault: Any, repository: Any, intent: str, learning_object_ids: Sequence[str], misconception_id: str | None, alias_key: bytes | None=None) -> tuple[list[str], list[str], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/remote/sources.py), line 136)
- `_record(repository: Any, result: PassageResult, *, call_id: str, clock: Clock | None) -> list[str]` ([source](../../../../../../src/learnloop/remote/sources.py), line 199)
- `_shown(vault: Any, repository: Any, hits: Any, withheld: Any, *, intent: str, budget: int, los: list[str], unknown_los: list[str]) -> PassageResult` ([source](../../../../../../src/learnloop/remote/sources.py), line 206) — Filter ``hits`` by the protection just read and build the payload.
- `_plan_verification(vault: Any, repository: Any, query: str, *, intent: str, policy: str, verify: bool, limit: int, targets: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/remote/sources.py), line 295) — The listwise verification a request would make, at its worst case, or why it would not run.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`; calls `SpendBudget`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/pipeline/add_source|learnloop.content.pipeline.add_source]] — imports `learner_title`; calls `learner_title`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`; calls `exam_material`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `blocks_by_key`; calls `blocks_by_key`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `format_block_span`; calls `format_block_span`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `caller_for`; calls `caller_for`
- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `propose_sources`, `resolve_misconceptions`; calls `propose_sources`, `resolve_misconceptions`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `TextGuard`, `resolve_scope`, `withheld_items`; calls `TextGuard`, `resolve_scope`, `withheld_items`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `route_skip`, `task_output_tokens`; calls `route_skip`, `task_output_tokens`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `module`; calls `PaidCalls`, `estimated_call_tokens`, `plan_route`
- [[Reference/Modules/learnloop/remote/errors|learnloop.remote.errors]] — imports `InvalidRequest`, `NotFound`, `RemoteRequestError`; calls `InvalidRequest`, `NotFound`
- [[Reference/Modules/learnloop/remote/telemetry|learnloop.remote.telemetry]] — imports `record_shown_passages`; calls `record_shown_passages`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `MODEL_WITHHELD_ROLES`, `item_exclusions`; calls `item_exclusions`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `module`; calls `intent_task`, `verification_context`, `verification_prompt`, `verification_question`, `widest_candidates`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `plan_library_search`; calls `plan_library_search`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `PolicyRefused`, `derive_policy`; calls `derive_policy`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `PRICE_SETTING`, `verify_caps`; calls `verify_caps`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `pathlib`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No direct or one-hop consumer test was found by static import analysis.

> [!caution] Test gap signal
> Treat this as a navigation signal, not proof that behavior is untested: dynamic and higher-level coverage is outside this static map. Add focused coverage when changing isolated behavior here.

## Modification guidance

- Make changes here when the responsibility remains sources within learnloop.remote; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/remote/sources.py](../../../../../../src/learnloop/remote/sources.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
