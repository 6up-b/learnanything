---
title: "learnloop.content.sources.source_outcome_analytics"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/source_outcome_analytics.py"
source_paths:
  - "src/learnloop/content/sources/source_outcome_analytics.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.sources"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.sources.source_outcome_analytics module"
  - "src/learnloop/content/sources/source_outcome_analytics.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-sources"
---

# `learnloop.content.sources.source_outcome_analytics`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.source_outcome_analytics` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: ING M8 — provenance-outcome analytics (spec §11).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/source_outcome_analytics.py](../../../../../../../src/learnloop/content/sources/source_outcome_analytics.py) |
| Source lines | 279 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class Association` ([source](../../../../../../../src/learnloop/content/sources/source_outcome_analytics.py), line 43)
  - `as_dict(self) -> dict[str, Any]` (line 53; public)
- `class SourceOutcomeReport` ([source](../../../../../../../src/learnloop/content/sources/source_outcome_analytics.py), line 67)
  - `as_dict(self) -> dict[str, Any]` (line 72; public)
- `analyze_source_outcomes(vault: LoadedVault, repository: Repository, *, subject_id: str | None=None, min_attempts: int=DEFAULT_MIN_ATTEMPTS, min_failures: int=DEFAULT_MIN_FAILURES, min_exposures: int=DEFAULT_MIN_EXPOSURES, thin_practice: int=DEFAULT_THIN_PRACTICE) -> SourceOutcomeReport` ([source](../../../../../../../src/learnloop/content/sources/source_outcome_analytics.py), line 102) — Deterministic provenance-outcome associations, report-only (§11).
- `source_outcome_notices(report: SourceOutcomeReport) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/sources/source_outcome_analytics.py), line 256) — Additive maintenance-feed notices for the ACTIONABLE associations (§11).

### Module constants

- `DEFAULT_MIN_ATTEMPTS` ([src/learnloop/content/sources/source_outcome_analytics.py](../../../../../../../src/learnloop/content/sources/source_outcome_analytics.py), line 32)
- `DEFAULT_MIN_FAILURES` ([src/learnloop/content/sources/source_outcome_analytics.py](../../../../../../../src/learnloop/content/sources/source_outcome_analytics.py), line 33)
- `DEFAULT_MIN_EXPOSURES` ([src/learnloop/content/sources/source_outcome_analytics.py](../../../../../../../src/learnloop/content/sources/source_outcome_analytics.py), line 34)
- `DEFAULT_THIN_PRACTICE` ([src/learnloop/content/sources/source_outcome_analytics.py](../../../../../../../src/learnloop/content/sources/source_outcome_analytics.py), line 36)
- `_ATTEMPT_SCAN_LIMIT` ([src/learnloop/content/sources/source_outcome_analytics.py](../../../../../../../src/learnloop/content/sources/source_outcome_analytics.py), line 37)
- `_SEMANTIC_RELATIONS` ([src/learnloop/content/sources/source_outcome_analytics.py](../../../../../../../src/learnloop/content/sources/source_outcome_analytics.py), line 39)

## Internal implementation anchors

- `_attempt_failed(attempt: dict[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/content/sources/source_outcome_analytics.py), line 80)
- `_lo_facet_ids(vault: LoadedVault, learning_object) -> set[str]` ([source](../../../../../../../src/learnloop/content/sources/source_outcome_analytics.py), line 88)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `analyze_source_outcomes`; statically calls `analyze_source_outcomes`
- [[Reference/Modules/learnloop/ops/maintenance_feed|learnloop.ops.maintenance_feed]] — imports `analyze_source_outcomes`, `source_outcome_notices`; statically calls `analyze_source_outcomes`, `source_outcome_notices`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `analyze_source_outcomes`; statically calls `analyze_source_outcomes`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/ops/maintenance_feed|learnloop.ops.maintenance_feed]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_outcome_analytics.py](../../../../../../../tests/test_source_outcome_analytics.py) — direct import
  - `test_repeated_failure_despite_coverage_requires_exposure`

## Modification guidance

- Change source outcome analytics policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/source_outcome_analytics.py](../../../../../../../src/learnloop/content/sources/source_outcome_analytics.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
