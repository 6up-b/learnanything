---
title: "learnloop.cli.families"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/families.py"
source_paths:
  - "src/learnloop/cli/families.py"
generated: true
generated_at: "2026-11-02"
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
  - "learnloop.cli.families module"
  - "src/learnloop/cli/families.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.families`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.families` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: Explicit family authoring; no background review queue or live retention key.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/families.py](../../../../../../src/learnloop/cli/families.py) |
| Source lines | 107 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `families_propose(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root; use a copy.')], dry_run: Annotated[bool, typer.Option('--dry-run', help='Estimate only; no paid calls or data changes.')]=False, learning_object_id: Annotated[str | None, typer.Option('--lo')]=None, judge_revision: Annotated[str, typer.Option('--judge-revision', help='Checkpoint revision; change this when re-evaluating a retargeted model alias.')]='1', max_candidates: Annotated[int, typer.Option('--max-candidates', min=0)]=100, max_pairs: Annotated[int, typer.Option('--max-pairs', min=0)]=100, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=200, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=2, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=1000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='Positive owner price bound (USD per million tokens, at least the higher input/output rate). Unknown prices fail closed on metered routes; a Codex route runs on the subscription and only estimates cost.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/families.py), line 29) — Two independent passes must agree on every pair; ambiguous items stay unfamilied.
- `families_undo(decision: Annotated[str, typer.Argument(help='Applied family ID or proposal ID.')], vault: Annotated[Path, typer.Option('--vault')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/families.py), line 80) — Undo in one step, retaining historical verdicts and each item's card.

## Internal implementation anchors

- `_emit(report: dict, json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/families.py), line 20)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `families_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `_cancellation`; calls `_cancellation`
- [[Reference/Modules/learnloop/ops/family_proposals|learnloop.ops.family_proposals]] — imports `propose_families`; calls `propose_families`
- [[Reference/Modules/learnloop/substrate/families|learnloop.substrate.families]] — imports `undo_family`; calls `undo_family`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `pathlib`, `typing`
- Third party: `typer`

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

- [tests/test_cli_append_units.py](../../../../../../tests/test_cli_append_units.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_facet_identity_ingest.py](../../../../../../tests/test_facet_identity_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_graph_nomination_ingest.py](../../../../../../tests/test_graph_nomination_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_model_call_receipt_owners.py](../../../../../../tests/test_model_call_receipt_owners.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/families.py](../../../../../../src/learnloop/cli/families.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
