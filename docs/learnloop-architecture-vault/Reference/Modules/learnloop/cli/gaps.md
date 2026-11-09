---
title: "learnloop.cli.gaps"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/gaps.py"
source_paths:
  - "src/learnloop/cli/gaps.py"
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
  - "learnloop.cli.gaps module"
  - "src/learnloop/cli/gaps.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.gaps`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.gaps` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop gaps`: learner-text gaps (implementation_handoffs §4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/gaps.py](../../../../../../src/learnloop/cli/gaps.py) |
| Source lines | 190 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `gaps_run(vault: VaultOption, backlog: Annotated[bool, typer.Option('--backlog', help='First queue unread stuck answers.')]=False, history: Annotated[bool, typer.Option('--history', help='With --backlog: also earlier tutor questions and diagnoses.')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Print the plan; send and write nothing.')]=False, max_texts: Annotated[int, typer.Option('--max-texts', min=1, help='Learner texts to read in this run.')]=20, max_calls: Annotated[int, typer.Option('--max-calls', min=1, help='Paid requests across the run.')]=120, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=20, max_tokens: Annotated[int, typer.Option('--max-tokens', min=1, help='Metered tokens across the run.')]=2000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0.0, help='Metered dollars across the run.')]=0.5, price_per_million: Annotated[float | None, typer.Option('--price-per-million', help='Owner price for a metered chat route without a published one.')]=None, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/gaps.py), line 64) — Read queued learner texts for named gaps (paid; --dry-run first).
- `gaps_list(vault: VaultOption, since: Annotated[str | None, typer.Option('--since', help='ISO time; only gaps read since then.')]=None, show_text: Annotated[bool, typer.Option('--show-text', help="Include the learner's text.")]=False, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/gaps.py), line 114) — List what each learner text was read as and what was done (no call).
- `gaps_undo(gap_id: Annotated[str, typer.Argument(help='The learner_text_gaps id.')], vault: VaultOption, reversal: Annotated[str, typer.Option('--reversal', help='undo_edge | undo_creation | not_this_belief')], json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/gaps.py), line 149) — Reverse one gap's action as the owner: an edge, a creation or a belief.
- `gaps_report(vault: VaultOption, since: Annotated[str | None, typer.Option('--since', help='ISO time; only gaps read since then.')]=None, out: Annotated[Path | None, typer.Option('--out', help='Write the Markdown report (with the batch review) here.')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Population sizes only; write nothing.')]=False, json_output: JsonOption=False) -> None` ([source](../../../../../../src/learnloop/cli/gaps.py), line 169) — Per kind and chooser: matched, created, undone, first checks, taps (no call).

### Explicit exports

`__all__` declares:

- `gaps_app`

## Internal implementation anchors

- `_load(vault: Path)` ([source](../../../../../../src/learnloop/cli/gaps.py), line 36)
- `_repository(loaded, *, read_only: bool)` ([source](../../../../../../src/learnloop/cli/gaps.py), line 44)
- `_echo(payload: object, json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/gaps.py), line 55)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `gaps_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/receipts|learnloop.cli.receipts]] — imports `bind_command_repository`, `bind_command_vault`; calls `bind_command_repository`, `bind_command_vault`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/learner_gaps|learnloop.db.stores.learner_gaps]] — imports `module`; calls `gaps`, `reversals`
- [[Reference/Modules/learnloop/diagnosis/offline_review/spend|learnloop.diagnosis.offline_review.spend]] — imports `ReviewSpend`; calls `ReviewSpend`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `UndoError`, `reverse_gap`; calls `reverse_gap`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `plan`, `run_pending`, `sweep_backlog`; calls `plan`, `run_pending`, `sweep_backlog`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/judges|learnloop.diagnosis.text_gaps.judges]] — imports `TextBudget`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/report|learnloop.diagnosis.text_gaps.report]] — imports `build_report`, `plan_report`, `write_report`; calls `build_report`, `plan_report`, `write_report`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `json`, `pathlib`, `typing`
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
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/gaps.py](../../../../../../src/learnloop/cli/gaps.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
