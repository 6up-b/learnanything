---
title: "learnloop.cli.facets"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/facets.py"
source_paths:
  - "src/learnloop/cli/facets.py"
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
  - "learnloop.cli.facets module"
  - "src/learnloop/cli/facets.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.facets`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.facets` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: Facet identity (handoff §4): dedupe an existing vault, list actions, undo one, decide a held reword.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/facets.py](../../../../../../src/learnloop/cli/facets.py) |
| Source lines | 187 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `facets_dedupe(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan the groups, calls and estimated cost; no client, no call, no change.')]=False, subject: Annotated[str | None, typer.Option('--subject', help='Only facets this subject uses.')]=None, max_calls: Annotated[int | None, typer.Option('--max-calls', min=0)]=None, max_facets: Annotated[int | None, typer.Option('--max-facets', min=0)]=None, max_pairs: Annotated[int | None, typer.Option('--max-pairs', min=0)]=None, max_retries: Annotated[int | None, typer.Option('--max-retries', min=0)]=None, max_tokens: Annotated[int | None, typer.Option('--max-tokens', min=0)]=None, max_cost_usd: Annotated[float | None, typer.Option('--max-cost-usd', min=0)]=None, price_input: Annotated[float | None, typer.Option('--price-per-million-input', min=0, help='Owner price (USD per million input tokens) for a metered judge model without a known price.')]=None, price_output: Annotated[float | None, typer.Option('--price-per-million-output', min=0, help='Owner price per million output tokens (default: input price).')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/facets.py), line 37) — Partition each concept neighbourhood's facets with the judge and apply merges.
- `facets_actions(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], run_id: Annotated[str | None, typer.Option('--run', help='Only one synthesis or dedupe run.')]=None, limit: Annotated[int, typer.Option('--limit', min=1, max=10000)]=50, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/facets.py), line 86) — Facet merges, absorbs and rewords (facet versions), newest first, with their undo state.
- `facets_undo(action_id: Annotated[str, typer.Argument(help='The action id from the result or `facets actions`.')], vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/facets.py), line 114) — Restore the facets one merge, absorb or reword replaced; re-fold their evidence.
- `facets_confirm(action_id: Annotated[str, typer.Argument(help='A reword waiting for your confirm (`facets actions`).')], vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/facets.py), line 163) — Confirm a reword that had no explanatory source behind it: it applies, with an undo.
- `facets_keep(action_id: Annotated[str, typer.Argument(help='A reword waiting for your confirm (`facets actions`).')], vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/facets.py), line 178) — Keep the facet's current wording: the held reword closes and nothing is written.

### Explicit exports

`__all__` declares:

- `facets_app`

## Internal implementation anchors

- `_emit(report: dict, json_output: bool, *, ok: set[str]) -> None` ([source](../../../../../../src/learnloop/cli/facets.py), line 19)
- `_root(vault: Path) -> Path` ([source](../../../../../../src/learnloop/cli/facets.py), line 27)
- `_decide_reword(action_id: str, vault: Path, json_output: bool, *, confirm: bool) -> None` ([source](../../../../../../src/learnloop/cli/facets.py), line 140)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `facets_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `_cancellation`; calls `_cancellation`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `FacetIdentityActionError`, `confirm_reword`, `describe`, `keep_current_wording`, `list_actions`, `undo_action`; calls `describe`, `list_actions`, `undo_action`
- [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]] — imports `run_dedupe`; calls `run_dedupe`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`, `refuse_vault_below_floor`; calls `load_vault`, `refuse_vault_below_floor`
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
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/facets.py](../../../../../../src/learnloop/cli/facets.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
