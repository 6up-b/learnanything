---
title: "learnloop.cli.recurrence"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/recurrence.py"
source_paths:
  - "src/learnloop/cli/recurrence.py"
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
  - "learnloop.cli.recurrence module"
  - "src/learnloop/cli/recurrence.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.recurrence`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.recurrence` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop recurrence`: Slice 2 T1 (M3) recurrence groups with authority.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/recurrence.py](../../../../../../src/learnloop/cli/recurrence.py) |
| Source lines | 239 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `recurrence_guard(vault: Annotated[Path, typer.Option('--vault', help='Vault root (a fixtures-local copy first).')], from_run: Annotated[Path | None, typer.Option('--from-run', help="Also judge an M1 review run's planted same-answer/different-cause cases.")]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Count the pairs and estimate the calls; no client, no call, no write.')]=False, rerun: Annotated[bool, typer.Option('--rerun', help='Ask the configured judge again on every pair; its new verdicts supersede its earlier ones.')]=False, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=60, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=20, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=400000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help=_PRICE_HELP)]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/recurrence.py), line 86) — Run the same-answer/different-cause regression suite through the judge.
- `recurrence_groups(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], reviews: Annotated[bool, typer.Option('--reviews/--no-reviews', help='Also list the review cases.')]=True, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/recurrence.py), line 131) — The current recurrence groups (merged classes only) and review cases.
- `recurrence_report(vault: Annotated[Path, typer.Option('--vault', help='Vault root.')], out: Annotated[Path | None, typer.Option('--out', help='Write the Markdown report here (JSON beside it).')]=None, audit_sample: Annotated[int, typer.Option('--audit-sample', min=0, max=200, help='Merged groups shown for the precision audit.')]=10, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/recurrence.py), line 164) — The M3 signals report (run after 2-4 weeks at mvp-0.12).
- `recurrence_bench(vault: Annotated[Path, typer.Option('--vault', help='Vault root (routes, receipts); use a fixtures-local copy.')], suite: Annotated[str, typer.Option('--suite', help='b1 (Eedi 2024) or b3 (vault replay).')], output_dir: Annotated[Path, typer.Option('--output', '--output-dir', help='Report and vector-cache directory (outside the vault).')]=Path('fixtures-local/reports/recurrence-bench'), benchmark: Annotated[Path | None, typer.Option('--benchmark', help='b1: directory with the Eedi train.csv, misconception_mapping.csv and a manifest.json.')]=None, model: Annotated[list[str] | None, typer.Option('--model', help='Embedding model id (OpenRouter); repeatable. b1 default: the five candidates; b3: embedding.model.')]=None, dims: Annotated[list[int] | None, typer.Option('--dims', min=1, help='Width(s) compared; repeatable. b1 default: 1024 (a width every candidate reaches); b3 default: the serving width, embedding.dimensions.')]=None, view: Annotated[list[str] | None, typer.Option('--view', help='b1 query views: raw, hypothesis; repeatable. Default: both.')]=None, target_recall: Annotated[float, typer.Option('--target-recall', min=0.5, max=1.0, help='b3: recall on confirmed matches that sets the cutoff and top_k.')]=0.95, max_cases: Annotated[int | None, typer.Option('--max-cases', min=1, help='b1: cases sampled (deterministically).')]=None, dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan calls and tokens; no client, request or write.')]=False, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=2000, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=50, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=10000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=2.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help="b1: one owner price for a metered hypothesis writer's input AND output tokens (an upper bound when it is the output price); prefer the input/output pair.")]=None, embedding_price_per_million: Annotated[float | None, typer.Option('--embedding-price-per-million', min=0, help='Embedding input price for models without a built-in estimate.')]=None, input_price_per_million: Annotated[float | None, typer.Option('--input-price-per-million', min=0, help="b1: the metered writer's input-token price (USD per million); with --output-price-per-million.")]=None, output_price_per_million: Annotated[float | None, typer.Option('--output-price-per-million', min=0, help="b1: the metered writer's output-token price (USD per million); with --input-price-per-million.")]=None, writer_output_tokens: Annotated[int | None, typer.Option('--writer-output-tokens', min=1, help="b1: the hypothesis writer's output budget per case (default: the output-budget policy's for the diagnosis route, ai.output_tokens 16384 unless overridden; reasoning tokens count against it).")]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/recurrence.py), line 185) — Run B1 or B3: an alias for `learnloop embeddings compare --suite b1|b3`.

### Module constants

- `_PRICE_HELP` ([src/learnloop/cli/recurrence.py](../../../../../../src/learnloop/cli/recurrence.py), line 82)

### Explicit exports

`__all__` declares:

- `recurrence_app`

## Internal implementation anchors

- `_cancellation() -> Iterator[threading.Event]` ([source](../../../../../../src/learnloop/cli/recurrence.py), line 39)
- `_load(vault: Path)` ([source](../../../../../../src/learnloop/cli/recurrence.py), line 52)
- `_repository(loaded, *, read_only: bool)` ([source](../../../../../../src/learnloop/cli/recurrence.py), line 60)
- `_echo(payload: object, json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/recurrence.py), line 71)
- `_caps(max_calls: int, max_retries: int, max_tokens: int, max_cost_usd: float) -> SpendCaps` ([source](../../../../../../src/learnloop/cli/recurrence.py), line 75)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `recurrence_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `embeddings_compare`; calls `embeddings_compare`
- [[Reference/Modules/learnloop/cli/receipts|learnloop.cli.receipts]] — imports `bind_command_repository`, `bind_command_vault`; calls `bind_command_repository`, `bind_command_vault`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `run_guard`; calls `run_guard`
- [[Reference/Modules/learnloop/diagnosis/recurrence/report|learnloop.diagnosis.recurrence.report]] — imports `m3_report`, `render_markdown`; calls `m3_report`, `render_markdown`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `json`, `pathlib`, `signal`, `threading`, `typing`
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

1. Modify [src/learnloop/cli/recurrence.py](../../../../../../src/learnloop/cli/recurrence.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
