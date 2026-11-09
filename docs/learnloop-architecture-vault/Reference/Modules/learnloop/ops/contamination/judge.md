---
title: "learnloop.ops.contamination.judge"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/contamination/judge.py"
source_paths:
  - "src/learnloop/ops/contamination/judge.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops.contamination"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.contamination.judge module"
  - "src/learnloop/ops/contamination/judge.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops-contamination"
---

# `learnloop.ops.contamination.judge`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.contamination.judge` exists within [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] to own the behavior summarized by its module contract: The ``leak`` / ``reveal`` judge: one bounded verdict per shortlisted pair.

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/contamination/judge.py](../../../../../../../src/learnloop/ops/contamination/judge.py) |
| Source lines | 415 |
| Owning package | [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ContaminationJudgment(WireModel)` ([source](../../../../../../../src/learnloop/ops/contamination/judge.py), line 104)
- `ledger_verdict(task: str, verdict: str) -> str` ([source](../../../../../../../src/learnloop/ops/contamination/judge.py), line 110)
- `class JudgeRequest` ([source](../../../../../../../src/learnloop/ops/contamination/judge.py), line 120)
  - `judgment_id(self) -> str` (line 129; public) — One verdict on one ordered pair in one pass; never shared between pairs.
  - `primary_id(self) -> str` (line 138; public)
- `judge_settings(vault: LoadedVault, provider: str, model: str | None, revision: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ops/contamination/judge.py), line 142)
- `decider_profiles(vault: LoadedVault) -> dict[str, str]` ([source](../../../../../../../src/learnloop/ops/contamination/judge.py), line 153) — ``{task: the Decider's profile}`` for each leak / reveal task the Decider judges first (Tier 1).
- `build_requests(candidates: Iterable[Candidate], settings: dict[str, Any], *, repeats: Collection[tuple[str, str, str, str, str]]=(), deciders: Mapping[str, str] | None=None) -> list[JudgeRequest]` ([source](../../../../../../../src/learnloop/ops/contamination/judge.py), line 162) — Every pass-1 request, then a pass-2 request for each pair in ``repeats``.
- `ledger_exists(sqlite_path: Path) -> bool` ([source](../../../../../../../src/learnloop/ops/contamination/judge.py), line 198)
- `rows_by_id(sqlite_path: Path, ids: Iterable[str]) -> dict[str, dict[str, Any]]` ([source](../../../../../../../src/learnloop/ops/contamination/judge.py), line 207)
- `owner_rows(sqlite_path: Path) -> dict[tuple[str, str, str, str, str], dict[str, Any]]` ([source](../../../../../../../src/learnloop/ops/contamination/judge.py), line 223) — The latest owner verdict per leak/reveal question (owner > verifier > llm).
- `estimate(requests: list[JudgeRequest], price_per_million: float | None) -> SpendEstimate` ([source](../../../../../../../src/learnloop/ops/contamination/judge.py), line 240) — UTF-8 bytes bound ordinary tokenizer input; output is bounded per request.
- `run_judgments(repository: Repository, pending: list[JudgeRequest], *, client: Any, budget: SpendBudget, settings: dict[str, Any], subscription: bool, price_per_million: float | None, run_id: str, on_saved: Callable[[JudgeRequest], None], vault: LoadedVault | None=None, client_factory: Callable[[], Any] | None=None) -> None` ([source](../../../../../../../src/learnloop/ops/contamination/judge.py), line 256) — Judge each pending pair once; raise on cancellation, caps or provider failure.

### Module constants

- `PROMPT_VERSIONS` ([src/learnloop/ops/contamination/judge.py](../../../../../../../src/learnloop/ops/contamination/judge.py), line 57)
- `OPERATIONS` ([src/learnloop/ops/contamination/judge.py](../../../../../../../src/learnloop/ops/contamination/judge.py), line 58)
- `JUDGE_ROUTE` ([src/learnloop/ops/contamination/judge.py](../../../../../../../src/learnloop/ops/contamination/judge.py), line 61)
- `METERED_JUDGE_TYPES` ([src/learnloop/ops/contamination/judge.py](../../../../../../../src/learnloop/ops/contamination/judge.py), line 62)
- `_COMMON` ([src/learnloop/ops/contamination/judge.py](../../../../../../../src/learnloop/ops/contamination/judge.py), line 64)
- `_INSTRUCTIONS` ([src/learnloop/ops/contamination/judge.py](../../../../../../../src/learnloop/ops/contamination/judge.py), line 70)
- `_TITLES` ([src/learnloop/ops/contamination/judge.py](../../../../../../../src/learnloop/ops/contamination/judge.py), line 97)
- `PRIMARY_PASS` ([src/learnloop/ops/contamination/judge.py](../../../../../../../src/learnloop/ops/contamination/judge.py), line 115)
- `REPEAT_PASS` ([src/learnloop/ops/contamination/judge.py](../../../../../../../src/learnloop/ops/contamination/judge.py), line 116)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/contamination/decider|learnloop.ops.contamination.decider]] — imports `JudgeRequest`, `OPERATIONS`, `ledger_verdict`; statically calls `ledger_verdict`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `JudgeRequest`, `METERED_JUDGE_TYPES`, `PRIMARY_PASS`, `PROMPT_VERSIONS`, `REPEAT_PASS`, `build_requests`, `decider_profiles`, `estimate`, `judge_settings`, `owner_rows`, `rows_by_id`, `run_judgments`; statically calls `build_requests`, `decider_profiles`, `estimate`, `judge_settings`, `owner_rows`, `rows_by_id`, `run_judgments`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIOutputTruncated`, `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`, `generation_limit`, `observe_model_calls`, `single_request`; calls `content_key`, `generation_limit`, `observe_model_calls`, `single_request`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `TruncationRetry`, `output_budget`, `output_ceiling`; calls `TruncationRetry`, `output_budget`, `output_ceiling`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendEstimate`, `subscription_usage_estimate`; calls `SpendEstimate`, `subscription_usage_estimate`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `DEFAULT_DECIDER_PROVIDER`, `DEFAULT_OUTPUT_TOKENS`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `enabled`; calls `enabled`
- [[Reference/Modules/learnloop/ops/contamination/decider|learnloop.ops.contamination.decider]] — imports `module`; calls `judge`
- [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]] — imports `Candidate`, `POSITIVE_VERDICT`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `pathlib`, `sqlite3`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/contamination/decider|learnloop.ops.contamination.decider]], [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_contamination_report.py](../../../../../../../tests/test_contamination_report.py) — direct import
- [tests/test_tier1_decider.py](../../../../../../../tests/test_tier1_decider.py) — direct import
  - `test_contamination`

## Modification guidance

- Make changes here when the responsibility remains judge within learnloop.ops.contamination; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/contamination/judge.py](../../../../../../../src/learnloop/ops/contamination/judge.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
