---
title: "learnloop.cli.registry"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/registry.py"
source_paths:
  - "src/learnloop/cli/registry.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Inspect Persistent State"
aliases:
  - "learnloop.cli.registry module"
  - "src/learnloop/cli/registry.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.registry`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps registry behavior inside its owning package, [[Reference/Modules/learnloop/cli/_package|learnloop.cli]]. Its public surface centers on `registry_audit`, `registry_list`, `registry_show`, `registry_certify`, `registry_promote`, `registry_release_check`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/registry.py](../../../../../../src/learnloop/cli/registry.py) |
| Source lines | 290 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `registry_audit(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the JSON audit report.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/registry.py), line 10) — Decision-parameter audit (§6/§9.6): every LearnLoopConfig numeric leaf and named module constant must classify decision/structural; every decision entry needs status/provenance.
- `registry_list(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, status: Annotated[str | None, typer.Option('--status')]=None, lifecycle: Annotated[str | None, typer.Option('--lifecycle')]=None, kind: Annotated[str | None, typer.Option('--kind')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/registry.py), line 43) — List registry entries with optional status/lifecycle/kind filters.
- `registry_show(path: Annotated[str, typer.Argument(help='Registered parameter path.')], vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/registry.py), line 72) — Trace one parameter to its registry entry (§9.7 item 5): effective value, source, status, lifecycle, evidence refs, last review.
- `registry_certify(path: Annotated[str, typer.Argument(help='Config parameter path to certify (sweepable).')], low: Annotated[float, typer.Option('--low', help='Low end of the plausible range.')], high: Annotated[float, typer.Option('--high', help='High end of the plausible range.')], steps: Annotated[int, typer.Option('--steps', min=2, help='Grid points across [low, high].')]=3, profile: Annotated[str, typer.Option('--profile', help='Built-in profile name or YAML path.')]='intermediate_with_misconception', days: Annotated[int, typer.Option('--days', min=1, help='Sim days per grid point.')]=8, items_per_day: Annotated[int, typer.Option('--items-per-day', min=1)]=4, seed: Annotated[int, typer.Option('--seed')]=42, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/registry.py), line 99) — Run the real seeded decision-relevance sweep across ``[low, high]`` on the current vault, produce a COVERAGE certificate for the parameter's current effective value, and store + link it (U-022 v2).
- `registry_promote(path: Annotated[str, typer.Argument(help='Config parameter path to promote (sweepable).')], low: Annotated[float, typer.Option('--low', help='Low end of the plausible range.')], high: Annotated[float, typer.Option('--high', help='High end of the plausible range.')], steps: Annotated[int, typer.Option('--steps', min=2, help='Grid points across [low, high].')]=3, profile: Annotated[str, typer.Option('--profile', help='Built-in profile name or YAML path.')]='intermediate_with_misconception', days: Annotated[int, typer.Option('--days', min=1, help='Sim days per grid point.')]=8, items_per_day: Annotated[int, typer.Option('--items-per-day', min=1)]=4, seed: Annotated[int, typer.Option('--seed')]=42, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/registry.py), line 182) — Consume sim PROMOTION EVIDENCE to advance status ``heuristic -> simulation_validated`` (U-022 v2, the normative gate).
- `registry_release_check(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/registry.py), line 262) — Strict §9.6 release gate: fails on any audit failure AND on any outstanding coverage debt (``active_pending_certificate`` count > 0), with the pending list attached.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`; calls `_resolve_config_value`, `audit`, `refresh`
- [[Reference/Modules/learnloop/params/sensitivity_certificates|learnloop.params.sensitivity_certificates]] — imports `module`; calls `certify`, `link_coverage_certificate`, `promote`, `promotion_evidence_from_certificate`, `store_certificate`
- [[Reference/Modules/learnloop/sim/profiles|learnloop.sim.profiles]] — imports `ProfileError`, `load_profile`; calls `load_profile`

### Platform and third-party dependencies

- Standard library: `__future__`, `tempfile`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/registry.py](../../../../../../src/learnloop/cli/registry.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
