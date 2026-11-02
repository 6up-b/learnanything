---
title: "learnloop.cli.evaluation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/evaluation.py"
source_paths:
  - "src/learnloop/cli/evaluation.py"
source_commit: "debd86c0d24a1e4837b20b76aad6a47a8720f8b2"
source_commit_timestamp: "2026-10-13T00:18:31-04:00"
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
  - "learnloop.cli.evaluation module"
  - "src/learnloop/cli/evaluation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.evaluation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.evaluation` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop eval`: one read-only offline evaluation harness.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/evaluation.py](../../../../../../src/learnloop/cli/evaluation.py) |
| Source lines | 201 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `debd86c0d24a1e4837b20b76aad6a47a8720f8b2` |
| Commit timestamp | `2026-10-13T00:18:31-04:00` |

## Public API

- `evaluate_existing(ctx: typer.Context, vault: Annotated[Path | None, typer.Option('--vault', help='Vault root (use a copy); replay never calls a model.')]=None, section: Annotated[str, typer.Option('--section', help='all (legacy calibration: predictions|coverage|gates|retention|propensity), field (reports 1-2), or a comma list such as all,field')]='all', bins: Annotated[int, typer.Option('--bins', min=1, help='Legacy decision-calibration bin count.')]=10, output_dir: Annotated[Path, typer.Option('--output-dir', '--output', help='Aggregate-only report destination.')]=Path('fixtures-local/reports'), arm: Annotated[list[str] | None, typer.Option('--arm', help='Repeat to select registered arms; default includes fixed sweeps.')]=None, legacy_fallback: Annotated[str | None, typer.Option('--legacy-fallback', help=_LEGACY_FALLBACK_HELP)]=None, bootstrap_samples: Annotated[int, typer.Option('--bootstrap-samples', min=1)]=1000, seed: Annotated[int, typer.Option('--seed')]=0, fast_track_q: Annotated[float, typer.Option('--fast-track-q', min=0.5, max=1.0, help='Frozen simulation threshold; conservative 0.9 until report 2 supports 0.8.')]=0.9, llm_cache: Annotated[Path | None, typer.Option('--llm-cache', help='The --probability-arm cache outside the vault; replay makes zero model calls.')]=None, prepare_llm: Annotated[bool, typer.Option('--prepare-llm', help='Explicit paid preparation of the --probability-arm arms before replay; requires --llm-cache and opt-in config.')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Estimate optional paid preparation without requests or report writes.')]=False, max_candidates: Annotated[int, typer.Option('--max-candidates', min=0)]=100, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=100, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=100000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='Conservative combined input/output-token USD rate for paid preparation. Unknown prices fail closed on metered routes; a Codex route runs on the subscription and only estimates cost.')]=None, output_tokens: Annotated[int | None, typer.Option('--output-tokens', min=1, help="Output-token budget of each LLM-arm request; default: the shared policy (ai.output_tokens or the route's override).")]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False, max_retries: Annotated[int, typer.Option('--max-retries', min=0, help='Probability arms only: counted retries per judge (a 429, 5xx or failed turn).')]=2, probability_arm: Annotated[list[str] | None, typer.Option('--probability-arm', help=_PROBABILITY_ARM_HELP)]=None) -> None` ([source](../../../../../../src/learnloop/cli/evaluation.py), line 48) — Calibration report by default; `--section field` writes reports 1-2.
- `pf_pilot_eval(vault: Annotated[Path, typer.Option('--vault', help='Vault root (use a copy).')], round_id: Annotated[str, typer.Option('--round', help='The `learnloop pf generate --round` to report.')], output_dir: Annotated[Path, typer.Option('--output-dir', '--output', help='Aggregate-only report destination.')]=Path('fixtures-local/reports/pf'), judge: Annotated[bool, typer.Option('--judge', help='Run the paid blind pairwise LLM comparison (15 survivors vs 15 single-shot items, two passes).')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Estimate the judge; no requests or report files.')]=False, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=100, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=2, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=1000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='Owner price bound for a metered judge route; Codex estimates only.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/evaluation.py), line 122) — PF pilot: survival per filter and per generation path, panel disagreement, cost, usage signals.
- `pf_scaling_eval(vault: Annotated[Path, typer.Option('--vault', help='Vault root (use a copy).')], round_id: Annotated[str, typer.Option('--round', help='The round generated with --tier cheap and --tier frontier.')], output_dir: Annotated[Path, typer.Option('--output-dir', '--output', help='Aggregate-only report destination.')]=Path('fixtures-local/reports/pf'), judge: Annotated[bool, typer.Option('--judge', help='Run the paid blind pairwise rating (10 survivors per tier, two passes).')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Estimate the judge; no requests or report files.')]=False, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=100, max_retries: Annotated[int, typer.Option('--max-retries', min=0)]=2, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=1000000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='Owner price bound for a metered judge route; Codex estimates only.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/evaluation.py), line 141) — Scaling check: does quality rise with the model?
- `judges(vault: Annotated[Path, typer.Option('--vault', help='Vault root (use a copy for --live-decider).')], probe: Annotated[bool, typer.Option('--probe', help="Free reachability check: OpenRouter's public listing for the Decider. No key, no learner text, no cost.")]=False, live_decider: Annotated[bool, typer.Option('--live-decider', help='One paid, spend-capped Decider call (under $0.001) with no learner data, to confirm the endpoint and typed answers.')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='With --live-decider: resolve the call and print its token and cost estimate; no key is loaded, nothing is sent or written.')]=False, json_output: Annotated[bool, typer.Option('--json', help='Emit stable JSON.')]=False) -> None` ([source](../../../../../../src/learnloop/cli/evaluation.py), line 160) — The judgment routes: resolution, readiness and privacy disclosures (router spec §6.2).

## Internal implementation anchors

- `_pf_report(kind: str, vault: Path, round_id: str, output_dir: Path, judge: bool, dry_run: bool, max_calls: int, max_retries: int, max_tokens: int, max_cost_usd: float, price_per_million: float | None, json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/evaluation.py), line 92)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `eval_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`, `SpendLimitExceeded`; calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `_cancellation`; calls `_cancellation`
- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `_LEGACY_FALLBACK_HELP`, `_PROBABILITY_ARM_HELP`, `families_eval`, `field_eval`; calls `field_eval`
- [[Reference/Modules/learnloop/cli/placement|learnloop.cli.placement]] — imports `placement_eval`
- [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]] — imports `practice_index_eval`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `judge_readiness`, `live_decider_check`, `live_decider_estimate`; calls `judge_readiness`, `live_decider_check`, `live_decider_estimate`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `_root`; calls `_root`
- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `success_head_eval`
- [[Reference/Modules/learnloop/ops/pf_reports|learnloop.ops.pf_reports]] — imports `pilot_report`, `scaling_report`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `pathlib`, `sqlite3`, `typing`
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

1. Modify [src/learnloop/cli/evaluation.py](../../../../../../src/learnloop/cli/evaluation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
