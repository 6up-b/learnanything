---
title: "learnloop.ops.contamination.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/contamination/report.py"
source_paths:
  - "src/learnloop/ops/contamination/report.py"
source_commit: "86f17850ae44f63d89602534064feb6c21c5f776"
source_commit_timestamp: "2026-10-15T12:20:59-04:00"
source_worktree_state: "clean"
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
  - "learnloop.ops.contamination.report module"
  - "src/learnloop/ops/contamination/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops-contamination"
---

# `learnloop.ops.contamination.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.contamination.report` exists within [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] to own the behavior summarized by its module contract: Slice 2 T4's report: shadow contamination flags with audited samples (§13).

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/contamination/report.py](../../../../../../../src/learnloop/ops/contamination/report.py) |
| Source lines | 581 |
| Owning package | [[Reference/Modules/learnloop/ops/contamination/_package|learnloop.ops.contamination]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `86f17850ae44f63d89602534064feb6c21c5f776` |
| Commit timestamp | `2026-10-15T12:20:59-04:00` |

## Public API

- `class Decision` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 64)
  - `positive(self) -> bool` (line 72; public)
- `verifier_judgment_id(candidate: Candidate) -> str` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 76) — Content-addressed: the same texts and checker never append twice.
- `contamination_report(loaded: LoadedVault, *, caps: SpendCaps, dry_run: bool=False, judge: bool=True, detectors: Sequence[str]=DETECTORS, top_k: int=3, sample_size: int=5, repeat_sample: int=5, price_per_million: float | None=None, judge_revision: str='1', cancelled: Callable[[], bool] | None=None, client: Any | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 369) — Scan, decide what can be decided, and report; see the module docstring.

### Module constants

- `REPORT_VERSION` ([src/learnloop/ops/contamination/report.py](../../../../../../../src/learnloop/ops/contamination/report.py), line 58)
- `EXCERPT_CHARS` ([src/learnloop/ops/contamination/report.py](../../../../../../../src/learnloop/ops/contamination/report.py), line 59)
- `SAMPLE_CATEGORIES` ([src/learnloop/ops/contamination/report.py](../../../../../../../src/learnloop/ops/contamination/report.py), line 60)

## Internal implementation anchors

- `_repeats(requests: list[JudgeRequest]) -> int` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 86)
- `_report_lock(root: Path) -> Iterator[None]` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 91)
- `_excerpt(text: str) -> str` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 107)
- `_rationale(row: dict[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 112)
- `_decide(candidate: Candidate, request: JudgeRequest | None, rows: dict[str, dict[str, Any]], owners: dict[tuple[str, str, str, str, str], dict[str, Any]]) -> Decision` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 125)
- `_stats(values: Sequence[float]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 144)
- `_proposal(candidate: Candidate, decision: Decision) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 151)
- `_agreement(pairs: list[tuple[str, str]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 184)
- `_noise_floor(scan: DetectorScan, requests: dict[tuple[str, str, str, str, str], JudgeRequest], repeats: dict[tuple[str, str, str, str, str], JudgeRequest], rows: dict[str, dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 190) — Run-to-run disagreement of the judge on its repeated pairs (R6).
- `_owner_audit(scan: DetectorScan, requests: dict[tuple[str, str, str, str, str], JudgeRequest], rows: dict[str, dict[str, Any]], owners: dict[tuple[str, str, str, str, str], dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 207) — The independently audited baseline: each automatic judge against the owner.
- `_summarize(scan: DetectorScan, decisions: dict[tuple[str, str, str, str, str], Decision], requests: dict[tuple[str, str, str, str, str], JudgeRequest], repeats: dict[tuple[str, str, str, str, str], JudgeRequest], rows: dict[str, dict[str, Any]], owners: dict[tuple[str, str, str, str, str], dict[str, Any]], sample_size: int) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 229)
- `_write_verifier_verdicts(repository: Repository, candidates: list[Candidate], rows: dict[str, dict[str, Any]]) -> int` ([source](../../../../../../../src/learnloop/ops/contamination/report.py), line 342)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/contamination|learnloop.cli.contamination]] — imports `contamination_report`; statically calls `contamination_report`
- [[Reference/Modules/learnloop/ops/contamination/__init__|learnloop.ops.contamination]] — imports `REPORT_VERSION`, `contamination_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`, `ready_client_for_task`; calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `ESTIMATED_ONLY`, `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `is_subscription_transport`; calls `SpendBudget`, `is_subscription_transport`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `BOUNDED_STRUCTURED_COMPLETION`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]] — imports `Candidate`, `DETECTORS`, `DetectorScan`, `POSITIVE_VERDICT`, `SCANNERS`, `StoredVectors`; calls `StoredVectors`
- [[Reference/Modules/learnloop/ops/contamination/judge|learnloop.ops.contamination.judge]] — imports `JudgeRequest`, `METERED_JUDGE_TYPES`, `PRIMARY_PASS`, `PROMPT_VERSIONS`, `REPEAT_PASS`, `build_requests`, `decider_profiles`, `estimate`, `judge_settings`, `owner_rows`, `rows_by_id`, `run_judgments`; calls `build_requests`, `decider_profiles`, `estimate`, `judge_settings`, `owner_rows`, `rows_by_id`, `run_judgments`
- [[Reference/Modules/learnloop/ops/contamination/recipes|learnloop.ops.contamination.recipes]] — imports `CONTAMINATION_RECIPES`
- [[Reference/Modules/learnloop/ops/contamination/symbolic|learnloop.ops.contamination.symbolic]] — imports `SYMBOLIC_VERSION`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `vault_repository`; calls `vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `fcntl`, `json`, `math`, `pathlib`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/contamination|learnloop.cli.contamination]], [[Reference/Modules/learnloop/ops/contamination/__init__|learnloop.ops.contamination]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_contamination_report.py](../../../../../../../tests/test_contamination_report.py) — direct import
  - `test_dry_run_changes_nothing_and_builds_no_client`
  - `test_the_report_carries_a_repeated_judgment_noise_floor_and_owner_audits`
  - `test_the_report_never_calls_an_embedding_provider`

## Modification guidance

- Make changes here when the responsibility remains report within learnloop.ops.contamination; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/contamination/report.py](../../../../../../../src/learnloop/ops/contamination/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
