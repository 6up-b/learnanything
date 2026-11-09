---
title: "learnloop.cli.success_head"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/success_head.py"
source_paths:
  - "src/learnloop/cli/success_head.py"
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
  - "learnloop.cli.success_head module"
  - "src/learnloop/cli/success_head.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.success_head`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.success_head` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop eval success-head`: the T8 replay report (offline research only).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/success_head.py](../../../../../../src/learnloop/cli/success_head.py) |
| Source lines | 232 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `prepare_or_load_zero_data(loaded, inputs, *, cache_dir, prepare=False, dry_run=False, caps: SpendCaps, price_per_million=None, output_tokens=None, cancelled=lambda: False, routes=None)` ([source](../../../../../../src/learnloop/cli/success_head.py), line 55) — Return ``(aliased arms or None, aggregate report)``; cache-only reads build no client.
- `success_head_eval(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault copy; replay never calls a model.')], output_dir: Annotated[Path, typer.Option('--output', '--output-dir', help='Aggregate-only report destination.')]=Path('fixtures-local/reports'), legacy_fallback: Annotated[str | None, typer.Option('--legacy-fallback', help=_LEGACY_FALLBACK_HELP)]=None, bootstrap_samples: Annotated[int, typer.Option('--bootstrap-samples', min=1, help='Pre-registered: 1000.')]=1000, seed: Annotated[int, typer.Option('--seed', help='Pre-registered: 0.')]=0, llm_cache: Annotated[Path | None, typer.Option('--llm-cache', help="The llm_probability cache outside the vault (the field section's --llm-cache); its llm_probability/v2/llm arm is T8's zero-data arm. Replay makes zero calls.")]=None, prepare_llm: Annotated[bool, typer.Option('--prepare-llm', help="Explicit paid preparation of llm_probability/v2/llm (T8's zero-data arm); requires --llm-cache and both field switches. Verdicts already paid for are reused.")]=False, backfill_seen_stems: Annotated[bool, typer.Option('--backfill-seen-stems', help='Explicit paid step: embed (item/stem recipe, ai.routing.embedding) the exact stem each scored attempt showed, retired items and earlier wordings included. Needs both embedding switches; run alone, --dry-run first.')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan only: coverage, and the spend estimate with --prepare-llm or --backfill-seen-stems. No calls, no writes.')]=False, max_candidates: Annotated[int, typer.Option('--max-candidates', min=0)]=100, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=100, max_retries: Annotated[int, typer.Option('--max-retries', min=0, help="Embedding batch retries (--backfill-seen-stems only); T8's LLM preparation never retries.")]=2, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=100000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help="USD per million tokens for this invocation's paid step: combined input/output for --prepare-llm (the ai.routing.llm_probability_llm route), input for --backfill-seen-stems. Unknown prices fail closed on metered routes; a Codex route only estimates cost.")]=None, output_tokens: Annotated[int | None, typer.Option('--output-tokens', min=1, help="Output-token budget of each LLM-arm request; default: the shared policy (ai.output_tokens or the route's override).")]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/success_head.py), line 87) — T8 learner success head replay: emb_ridge's kill rule, gated heads, zero-data LLM.

### Module constants

- `LLM_ARM_ALIASES` ([src/learnloop/cli/success_head.py](../../../../../../src/learnloop/cli/success_head.py), line 35)
- `LLM_ALIAS_NOTE` ([src/learnloop/cli/success_head.py](../../../../../../src/learnloop/cli/success_head.py), line 38)

## Internal implementation anchors

- `_load(vault: Path, *, paid: bool)` ([source](../../../../../../src/learnloop/cli/success_head.py), line 51)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]] — imports `success_head_eval`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `_cancellation`; calls `_cancellation`
- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `_LEGACY_FALLBACK_HELP`, `_emit`, `_load_for_step`, `_replay_inputs`; calls `_emit`, `_load_for_step`, `_replay_inputs`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `prepare_or_load_probability_arms`; calls `prepare_or_load_probability_arms`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `MasteryConfig`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]] — imports `evaluate`, `report_digest`, `write_reports`; calls `evaluate`, `report_digest`, `write_reports`
- [[Reference/Modules/learnloop/field/item_content|learnloop.field.item_content]] — imports `load_content_index`, `seen_stem_records`; calls `load_content_index`, `seen_stem_records`
- [[Reference/Modules/learnloop/field/probability_arms|learnloop.field.probability_arms]] — imports `arm_name`; calls `arm_name`
- [[Reference/Modules/learnloop/field/success_head|learnloop.field.success_head]] — imports `LLM_ARMS`, `PREREGISTRATION`, `preregistration_hash`, `success_head_arms`; calls `preregistration_hash`, `success_head_arms`
- [[Reference/Modules/learnloop/field/success_head_analysis|learnloop.field.success_head_analysis]] — imports `make_t8_analysis`, `summary_lines`; calls `make_t8_analysis`, `summary_lines`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `backfill_embeddings`; calls `backfill_embeddings`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `math`, `pathlib`, `sqlite3`, `typing`
- Third party: `typer`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No direct or one-hop consumer test was found by static import analysis.

> [!caution] Test gap signal
> Treat this as a navigation signal, not proof that behavior is untested: dynamic and higher-level coverage is outside this static map. Add focused coverage when changing isolated behavior here.

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/success_head.py](../../../../../../src/learnloop/cli/success_head.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
