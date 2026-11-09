---
title: "learnloop.cli.pf"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/pf.py"
source_paths:
  - "src/learnloop/cli/pf.py"
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
  - "learnloop.cli.pf module"
  - "src/learnloop/cli/pf.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.pf`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.pf` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop pf`: PF-b generate -> verify -> select -> publish (Slice 2 §5.3-§5.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/pf.py](../../../../../../src/learnloop/cli/pf.py) |
| Source lines | 118 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `pf_generate(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root; rehearse on a fixtures-local copy.')], dry_run: Annotated[bool, typer.Option('--dry-run', help='Estimate calls, tokens and cost; no client, migration or data change.')]=False, path: Annotated[str, typer.Option('--path', help='generator | ensemble | source_anchored | single_shot (pilot baseline, never published) | auto (family source_kind, else pf.default_path).')]='auto', relation: Annotated[str, typer.Option('--relation', help='Declared variant relation for ensemble proposals; programs draw isomorphs.')]='isomorph', family: Annotated[list[str] | None, typer.Option('--family', help='Activity family id; repeatable. Default: every family with an active member.')]=None, learning_object_id: Annotated[str | None, typer.Option('--lo')]=None, seed_item: Annotated[list[str] | None, typer.Option('--seed-item', help='Create an owner-authored single-item family for this unfamilied item; repeatable.')]=None, count: Annotated[int | None, typer.Option('--count', min=1, max=60, help='Candidates per family (default pf.candidates_per_family).')]=None, select: Annotated[int | None, typer.Option('--select', min=1, help='Survivors to select per family (default pf.select_per_family).')]=None, round_id: Annotated[str | None, typer.Option('--round', help="Job round; reruns of a round resume. Default: today's UTC date.")]=None, tier: Annotated[str | None, typer.Option('--tier', help='Scaling check: run generator and judge roles on pf.scaling.cheap or .frontier.')]=None, publish: Annotated[bool, typer.Option('--publish/--no-publish', help="Publish selected survivors under today's cap.")]=True, max_candidates: Annotated[int, typer.Option('--max-candidates', min=0)]=60, max_pairs: Annotated[int, typer.Option('--max-pairs', min=0)]=2000, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=400, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=2, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=4000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=2.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='Positive owner price bound (USD per million tokens, at least the higher input/output rate). Unknown prices fail closed on metered routes; Codex routes run on the subscription and only estimate cost.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/pf.py), line 41) — Over-generate, verify, filter, select and publish verified items per family.
- `pf_publish(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root.')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/pf.py), line 92) — Publish selected, verified candidates left over by a capped day.
- `pf_status_command(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root.')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/pf.py), line 107) — Candidate counts by path and status, and today's remaining publish slots.

## Internal implementation anchors

- `_emit(report: dict, json_output: bool, ok: set[str]=frozenset({'dry_run', 'complete'})) -> None` ([source](../../../../../../src/learnloop/cli/pf.py), line 23)
- `_loaded(vault: Path)` ([source](../../../../../../src/learnloop/cli/pf.py), line 31)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `pf_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `_cancellation`; calls `_cancellation`
- [[Reference/Modules/learnloop/ops/pf_generation|learnloop.ops.pf_generation]] — imports `GenerationOptions`, `generate_practice`, `pf_status`, `publish_backlog`; calls `GenerationOptions`, `generate_practice`, `pf_status`, `publish_backlog`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

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

1. Modify [src/learnloop/cli/pf.py](../../../../../../src/learnloop/cli/pf.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
