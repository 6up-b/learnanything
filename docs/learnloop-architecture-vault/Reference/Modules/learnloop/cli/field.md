---
title: "learnloop.cli.field"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/field.py"
source_paths:
  - "src/learnloop/cli/field.py"
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
  - "learnloop.cli.field module"
  - "src/learnloop/cli/field.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.field`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.field` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: Offline learner-field inspection and evaluation; never changes serving.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/field.py](../../../../../../src/learnloop/cli/field.py) |
| Source lines | 309 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `field_data_check(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault copy to inspect.')], legacy_fallback: Annotated[str | None, typer.Option('--legacy-fallback', help=_LEGACY_FALLBACK_HELP)]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/field.py), line 78) — Count evidence, revision exclusions and independence without model calls.
- `field_eval(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault copy; replay never calls a model.')], section: Annotated[str, typer.Option('--section', help='all (legacy calibration: predictions|coverage|gates|retention|propensity), field (reports 1-2), or a comma list such as all,field')]='all', bins: Annotated[int, typer.Option('--bins', min=1, help='Legacy decision-calibration bin count.')]=10, output_dir: Annotated[Path, typer.Option('--output-dir', '--output', help='Aggregate-only report destination.')]=Path('fixtures-local/reports'), arm: Annotated[list[str] | None, typer.Option('--arm', help='Repeat to select registered arms; default includes fixed sweeps.')]=None, legacy_fallback: Annotated[str | None, typer.Option('--legacy-fallback', help=_LEGACY_FALLBACK_HELP)]=None, bootstrap_samples: Annotated[int, typer.Option('--bootstrap-samples', min=1)]=1000, seed: Annotated[int, typer.Option('--seed')]=0, fast_track_q: Annotated[float, typer.Option('--fast-track-q', min=0.5, max=1.0, help='Frozen simulation threshold; conservative 0.9 until report 2 supports 0.8.')]=0.9, llm_cache: Annotated[Path | None, typer.Option('--llm-cache', help='The --probability-arm cache outside the vault; replay makes zero model calls.')]=None, prepare_llm: Annotated[bool, typer.Option('--prepare-llm', help='Explicit paid preparation of the --probability-arm arms before replay; requires --llm-cache and opt-in config.')]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='Estimate optional paid preparation without requests or report writes.')]=False, max_candidates: Annotated[int, typer.Option('--max-candidates', min=0)]=100, max_calls: Annotated[int, typer.Option('--max-calls', min=0)]=100, max_tokens: Annotated[int, typer.Option('--max-tokens', min=0)]=100000, max_cost_usd: Annotated[float, typer.Option('--max-cost-usd', min=0)]=1.0, price_per_million: Annotated[float | None, typer.Option('--price-per-million', min=0, help='Conservative combined input/output-token USD rate for paid preparation. Unknown prices fail closed on metered routes; a Codex route runs on the subscription and only estimates cost.')]=None, output_tokens: Annotated[int | None, typer.Option('--output-tokens', min=1, help="Output-token budget of each LLM-arm request; default: the shared policy (ai.output_tokens or the route's override).")]=None, json_output: Annotated[bool, typer.Option('--json')]=False, max_retries: Annotated[int, typer.Option('--max-retries', min=0, help='Probability arms only: counted retries per judge (a 429, 5xx or failed turn).')]=2, probability_arm: Annotated[list[str] | None, typer.Option('--probability-arm', help=_PROBABILITY_ARM_HELP)]=None) -> None` ([source](../../../../../../src/learnloop/cli/field.py), line 162) — Legacy calibration report by default; `--section field` adds reports 1-2.
- `families_eval(vault: Annotated[Path, typer.Option('--vault', help='Explicit vault copy; replay never calls a model.')], output_dir: Annotated[Path, typer.Option('--output', '--output-dir', help='Aggregate-only report destination.')]=Path('fixtures-local/reports'), legacy_fallback: Annotated[str | None, typer.Option('--legacy-fallback', help=_LEGACY_FALLBACK_HELP)]=None, arm: Annotated[list[str] | None, typer.Option('--arm', help='Repeat to select arms; default is the families arm set.')]=None, bootstrap_samples: Annotated[int, typer.Option('--bootstrap-samples', min=1)]=1000, seed: Annotated[int, typer.Option('--seed')]=0, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/field.py), line 279) — PF-a report on the shared harness: memory per item/family/LO and idea_hier.

### Module constants

- `LEGACY_SECTIONS` ([src/learnloop/cli/field.py](../../../../../../src/learnloop/cli/field.py), line 46)
- `FIELD_SECTION` ([src/learnloop/cli/field.py](../../../../../../src/learnloop/cli/field.py), line 47)
- `_LEGACY_FALLBACK_HELP` ([src/learnloop/cli/field.py](../../../../../../src/learnloop/cli/field.py), line 48)
- `_PROBABILITY_ARM_HELP` ([src/learnloop/cli/field.py](../../../../../../src/learnloop/cli/field.py), line 55)
- `_NUMERIC_ARM_RETIRED` ([src/learnloop/cli/field.py](../../../../../../src/learnloop/cli/field.py), line 63)

## Internal implementation anchors

- `_load_offline(vault: Path)` ([source](../../../../../../src/learnloop/cli/field.py), line 23)
- `_load_for_step(vault: Path, *, paid: bool)` ([source](../../../../../../src/learnloop/cli/field.py), line 29) — Replay and dry runs read only the vault TOML; a paid step loads like `learnloop embeddings backfill`, so the app reads its keys and per-machine Codex checkout itself.
- `_emit(report: dict, json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/field.py), line 42)
- `_sections(section: str) -> set[str]` ([source](../../../../../../src/learnloop/cli/field.py), line 69) — ``all`` is the legacy calibration report; ``field`` is opt-in.
- `_replay_inputs(loaded, *, legacy_fallback)` ([source](../../../../../../src/learnloop/cli/field.py), line 99) — One read-only snapshot: rows, signals, frozen priors and the FSRS fit.
- `_replay(loaded, inputs, *, arms, bootstrap_samples, seed, fast_track_q, extra_arms=(), pairwise=())` ([source](../../../../../../src/learnloop/cli/field.py), line 128)
- `_answer_signal_pairs(arms) -> tuple[tuple[str, str], ...]` ([source](../../../../../../src/learnloop/cli/field.py), line 149) — The duel's (base, base+signal) pairs whose two arms are both selected.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `field_app`
- [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]] — imports `_LEGACY_FALLBACK_HELP`, `_PROBABILITY_ARM_HELP`, `families_eval`, `field_eval`; statically calls `field_eval`
- [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]] — imports `_LEGACY_FALLBACK_HELP`, `_emit`, `_load_for_step`, `_replay_inputs`; statically calls `_emit`, `_load_for_step`, `_replay_inputs`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCaps`; calls `SpendCaps`
- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `_cancellation`; calls `_cancellation`
- [[Reference/Modules/learnloop/cli/field_classification|learnloop.cli.field_classification]] — imports `register_classification_command`; calls `register_classification_command`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `pairwise_comparisons`, `prepare_or_load_probability_arms`; calls `pairwise_comparisons`, `prepare_or_load_probability_arms`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/field/answer_signals|learnloop.field.answer_signals]] — imports `default_pairs`; calls `default_pairs`
- [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]] — imports `evaluate`, `family_arms`, `report_digest`, `write_reports`; calls `evaluate`, `family_arms`, `report_digest`, `write_reports`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `borrowed_repository`, `data_check`, `load_effective_replay_rows`; calls `borrowed_repository`, `data_check`, `load_effective_replay_rows`
- [[Reference/Modules/learnloop/field/predictors|learnloop.field.predictors]] — imports `registered_predictors`; calls `registered_predictors`
- [[Reference/Modules/learnloop/field/priors|learnloop.field.priors]] — imports `load_frozen_priors`; calls `load_frozen_priors`
- [[Reference/Modules/learnloop/field/probability_arms|learnloop.field.probability_arms]] — imports `parse_arm_selection`; calls `parse_arm_selection`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `fitted_fsrs_provenance`, `resolve_fsrs_weights`; calls `fitted_fsrs_provenance`, `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] — imports `build_eval_report`; calls `build_eval_report`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `json`, `pathlib`, `sqlite3`, `typing`
- Third party: `typer`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]], [[Reference/Modules/learnloop/cli/evaluation|learnloop.cli.evaluation]], [[Reference/Modules/learnloop/cli/success_head|learnloop.cli.success_head]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_family_memory_projection.py](../../../../../../tests/test_family_memory_projection.py) — direct import
  - `test_rebuild_and_evaluation_fold_the_same_leak_aware_rows`
- [tests/test_field_signal_production_paths.py](../../../../../../tests/test_field_signal_production_paths.py) — direct import
- [tests/test_probability_prep.py](../../../../../../tests/test_probability_prep.py) — direct import

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/field.py](../../../../../../src/learnloop/cli/field.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
