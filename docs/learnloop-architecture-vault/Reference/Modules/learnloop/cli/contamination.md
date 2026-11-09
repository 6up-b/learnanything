---
title: "learnloop.cli.contamination"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/contamination.py"
source_paths:
  - "src/learnloop/cli/contamination.py"
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
  - "learnloop.cli.contamination module"
  - "src/learnloop/cli/contamination.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.contamination`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.contamination` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: Slice 2 T4 shadow contamination flags: embed, then report.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/contamination.py](../../../../../../src/learnloop/cli/contamination.py) |
| Source lines | 146 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `contamination_embed(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root; use a fixtures-local copy.')], dry_run: Annotated[bool, typer.Option('--dry-run', help='Estimate calls, tokens and cost; no client, migration or data changes.')]=False, record_kind: Annotated[list[str] | None, typer.Option('--record-kind', help='A record kind or recipe (item/stem, item/expected_answer, question_event/answer, surface/statement, exam_span/text); repeatable. Default: all.')]=None, batch_size: Annotated[int, typer.Option('--batch-size', min=1, max=256)]=32, max_candidates: Annotated[int, typer.Option('--max-candidates', min=0, help='Records to embed.')]=2000, max_pairs: Annotated[int, typer.Option('--max-pairs', min=0, help='Embedding uses no pairs.')]=0, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=200, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=2, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=2000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='Positive USD input-token estimate for an unknown/changed model price; still subject to cost cap.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/contamination.py), line 40) — Embed the texts the contamination report compares; reruns skip saved hashes.
- `contamination_report_command(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault root; use a fixtures-local copy.')], dry_run: Annotated[bool, typer.Option('--dry-run', help='Scan and estimate the judge; no client, lock or data change.')]=False, no_judge: Annotated[bool, typer.Option('--no-judge', help='No paid calls: report the floor, the symbolic check and stored vectors.')]=False, detector: Annotated[list[str] | None, typer.Option('--detector', help='exam_leakage, tutor_answer_leak or reader_reveal; repeatable. Default: all.')]=None, top_k: Annotated[int, typer.Option('--top-k', min=1, max=50, help='Embedding shortlist rank; no score cutoff.')]=3, sample: Annotated[int, typer.Option('--sample', min=0, max=100, help='Audited samples per category.')]=5, repeat_sample: Annotated[int, typer.Option('--repeat-sample', min=0, max=50, help='Noise floor: pairs per detector judged a second time under identical settings (planned in --dry-run; 0 turns it off).')]=5, judge_revision: Annotated[str, typer.Option('--judge-revision', help='Checkpoint revision; change it to re-judge under a retargeted model alias.')]='1', max_candidates: Annotated[int, typer.Option('--max-candidates', min=0, help='Distinct subjects judged.')]=500, max_pairs: Annotated[int, typer.Option('--max-pairs', min=0)]=500, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=500, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=2, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=2000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='Positive owner price bound (USD per million tokens). Unknown prices fail closed on metered routes; a Codex route runs on the subscription and only estimates cost.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/contamination.py), line 89) — Shadow flag rates, floor agreement, proposals and audited samples (Slice 2 §13).

## Internal implementation anchors

- `_emit(report: dict, json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/contamination.py), line 22)
- `_load(vault: Path)` ([source](../../../../../../src/learnloop/cli/contamination.py), line 30)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `contamination_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `_cancellation`; calls `_cancellation`
- [[Reference/Modules/learnloop/ops/contamination/detectors|learnloop.ops.contamination.detectors]] — imports `DETECTORS`
- [[Reference/Modules/learnloop/ops/contamination/recipes|learnloop.ops.contamination.recipes]] — imports `CONTAMINATION_RECIPES`
- [[Reference/Modules/learnloop/ops/contamination/report|learnloop.ops.contamination.report]] — imports `contamination_report`; calls `contamination_report`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `backfill_embeddings`; calls `backfill_embeddings`
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

1. Modify [src/learnloop/cli/contamination.py](../../../../../../src/learnloop/cli/contamination.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
