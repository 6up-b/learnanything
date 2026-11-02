---
title: "learnloop.cli.field_classification"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/field_classification.py"
source_paths:
  - "src/learnloop/cli/field_classification.py"
source_commit: "86f17850ae44f63d89602534064feb6c21c5f776"
source_commit_timestamp: "2026-10-15T12:20:59-04:00"
source_worktree_state: "clean"
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
  - "learnloop.cli.field_classification module"
  - "src/learnloop/cli/field_classification.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.field_classification`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.field_classification` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: Opt-in question classification command; registration is owned by field CLI.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/field_classification.py](../../../../../../src/learnloop/cli/field_classification.py) |
| Source lines | 186 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `86f17850ae44f63d89602534064feb6c21c5f776` |
| Commit timestamp | `2026-10-15T12:20:59-04:00` |

## Public API

- `class QuestionClassification(WireModel)` ([source](../../../../../../src/learnloop/cli/field_classification.py), line 37)
- `register_classification_command(field_app: typer.Typer) -> None` ([source](../../../../../../src/learnloop/cli/field_classification.py), line 44)
- `classify_questions(vault: Annotated[Path, typer.Option('--vault')], dry_run: Annotated[bool, typer.Option('--dry-run')]=False, max_candidates: Annotated[int, typer.Option('--max-candidates', min=0)]=100, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=100, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=100000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', help='Explicit conservative USD rate for combined input/output tokens. Unknown prices fail closed on metered routes; a Codex route runs on the subscription and only estimates cost.')]=None, output_tokens: Annotated[int | None, typer.Option('--output-tokens', min=1, help="Output-token budget per question; default: the shared policy (ai.output_tokens or the route's override). One physical call per question by contract: a truncated answer is logged and stops the command; it is never accepted.")]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/field_classification.py), line 48) — Classify only missing question metadata.

### Module constants

- `METERED_ROUTE_TYPES` ([src/learnloop/cli/field_classification.py](../../../../../../src/learnloop/cli/field_classification.py), line 34)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `register_classification_command`; statically calls `register_classification_command`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `generation_limit`; calls `generation_limit`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`, `SpendEstimate`, `is_subscription_transport`; calls `SpendCaps`, `SpendEstimate`, `is_subscription_transport`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `_cancellation`; calls `_cancellation`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/decider_judgments|learnloop.decider_judgments]] — imports `VERSION`, `enabled`; calls `enabled`
- [[Reference/Modules/learnloop/field/classification|learnloop.field.classification]] — imports `PROMPT_VERSION`, `TASK`, `classify_missing_questions`; calls `classify_missing_questions`
- [[Reference/Modules/learnloop/field/decider|learnloop.field.decider]] — imports `Classifier`; calls `Classifier`
- [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]] — imports `classification_input`; calls `classification_input`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `math`, `pathlib`, `sqlite3`, `typing`
- Third party: `typer`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_interaction_signals.py](../../../../../../tests/test_interaction_signals.py) — direct import
  - `test_classification_cli_is_offline_lazy_bounded_and_resumable`
  - `test_classification_loads_settings_only_for_a_paid_run`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/field_classification.py](../../../../../../src/learnloop/cli/field_classification.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
