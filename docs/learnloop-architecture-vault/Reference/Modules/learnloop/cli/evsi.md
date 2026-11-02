---
title: "learnloop.cli.evsi"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/evsi.py"
source_paths:
  - "src/learnloop/cli/evsi.py"
source_commit: "da5c9ecf8613df293d5f36f7d2c0b3fd93f3eafb"
source_commit_timestamp: "2026-10-13T15:35:46-04:00"
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
  - "learnloop.cli.evsi module"
  - "src/learnloop/cli/evsi.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.evsi`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.evsi` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop evsi simulate` and `learnloop evsi calibration` (EVSI calibration).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/evsi.py](../../../../../../src/learnloop/cli/evsi.py) |
| Source lines | 292 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `da5c9ecf8613df293d5f36f7d2c0b3fd93f3eafb` |
| Commit timestamp | `2026-10-13T15:35:46-04:00` |

## Public API

- `evsi_simulate_command(eedi_2024: Annotated[Path, typer.Option('--eedi-2024', help='Directory with the Eedi 2024 Kaggle train.csv and misconception_mapping.csv.')], eedi_2020: Annotated[Path | None, typer.Option('--eedi-2020', help='Directory with the extracted Eedi NeurIPS 2020 archive (data/...). Needed unless --fit is given.')]=None, fit_path: Annotated[Path | None, typer.Option('--fit', help='A response_fit.json from an earlier run (skips the fit).')]=None, output: Annotated[Path, typer.Option('--output', help='Directory for response_fit.json and simulation_report.json.')]=Path('fixtures-local/evsi-calibration'), task: Annotated[str, typer.Option('--task', help='Eedi 2020 task to fit on: 1_2 (15.9M answers) or 3_4 (1.4M).')]='1_2', learners: Annotated[int, typer.Option('--learners', min=10, help='Flagged learners per arm.')]=400, sensitivity_learners: Annotated[int, typer.Option('--sensitivity-learners', min=10, help='Learners per sensitivity arm.')]=300, workers: Annotated[int, typer.Option('--workers', min=1, help='Worker processes.')]=4, seed: Annotated[int, typer.Option('--seed')]=20261012, quick: Annotated[bool, typer.Option('--quick', help='A small smoke run (few learners, one regime row, short sweeps).')]=False, safety_bound: Annotated[int | None, typer.Option('--safety-bound', min=1, help='Stop every episode after this many checks (default: no bound; runs before 2026-10-13 used 25).')]=None, reference_bound: Annotated[int, typer.Option('--reference-bound', min=1, help="Count, in every cell, the episodes a bound of this many checks stops (default 25, the bound of runs before 2026-10-13); `evsi compare` attributes differences to a bounded run's bound only when it equals this.")]=25, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/evsi.py), line 37) — Fit the response model to Eedi, simulate, and score EIG/EVSI against baselines.
- `evsi_compare_command(old: Annotated[Path, typer.Option('--old', help='The stored simulation_report.json (the reference run).')], new: Annotated[Path, typer.Option('--new', help="The rerun's simulation_report.json.")], output: Annotated[Path | None, typer.Option('--output', help='Write the full comparison (JSON) here, atomically.')]=None, markdown: Annotated[Path | None, typer.Option('--markdown', help="Write the comparison's tables (Markdown) here, atomically.")]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/evsi.py), line 121) — Compare two `evsi simulate` reports: every recorded value, every headline claim, the count bound's stops (read-only).
- `evsi_multisim_command(eedi_2024: Annotated[Path | None, typer.Option('--eedi-2024', help='Directory with the Eedi 2024 Kaggle train.csv and misconception_mapping.csv. Needed unless --reanalyze is given.')]=None, eedi_2020: Annotated[Path | None, typer.Option('--eedi-2020', help='Directory with the extracted Eedi NeurIPS 2020 archive. Needed unless --fits is given.')]=None, fit_path: Annotated[Path | None, typer.Option('--fit', help="The single-family study's response_fit.json: reuse its misconception triples (else they are searched again).")]=None, fits_path: Annotated[Path | None, typer.Option('--fits', help='A family_fits.json from an earlier multisim run (skips every family fit).')]=None, output: Annotated[Path, typer.Option('--output', help='Directory for family_fits.json and multisim_report.json.')]=Path('fixtures-local/evsi-multisim'), task: Annotated[str, typer.Option('--task', help='Eedi 2020 task to fit on: 1_2 (15.9M answers) or 3_4 (1.4M).')]='1_2', cache_dir: Annotated[Path | None, typer.Option('--cache-dir', help='Where the parsed Eedi 2020 answers are cached (default: <output>/cache).')]=None, learners: Annotated[int, typer.Option('--learners', min=10, help='Flagged learners per arm.')]=400, sensitivity_learners: Annotated[int, typer.Option('--sensitivity-learners', min=10, help='Learners per sensitivity arm.')]=300, workers: Annotated[int, typer.Option('--workers', min=1, help='Worker processes.')]=4, seed: Annotated[int, typer.Option('--seed')]=20261012, quick: Annotated[bool, typer.Option('--quick', help='A small smoke run (few learners, two regimes, short sweeps).')]=False, reanalyze: Annotated[Path | None, typer.Option('--reanalyze', help='A multisim_report.json to re-score: recompute its analysis from the stored per-learner episodes (no fit, no simulation) and write it back.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/evsi.py), line 165) — Fit several simulator families to Eedi and rerun the EVSI study in each (RankCert).
- `evsi_calibration_command(vault: Annotated[Path, typer.Option('--vault', help='Vault root (read-only).')], since: Annotated[str | None, typer.Option('--since', help='Only forecasts at or after this ISO time (UTC).')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/evsi.py), line 275) — Live calibration of value-of-information forecasts (read-only).

## Internal implementation anchors

- `_emit(payload: dict, json_output: bool) -> None` ([source](../../../../../../src/learnloop/cli/evsi.py), line 32)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `evsi_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/evsi_calibration/artifacts|learnloop.evsi_calibration.artifacts]] — imports `write_text_atomic`; calls `write_text_atomic`
- [[Reference/Modules/learnloop/evsi_calibration/compare|learnloop.evsi_calibration.compare]] — imports `compare_reports`, `render_markdown`; calls `compare_reports`, `render_markdown`
- [[Reference/Modules/learnloop/evsi_calibration/eedi|learnloop.evsi_calibration.eedi]] — imports `load_eedi_2024`, `load_neurips_2020`; calls `load_eedi_2024`, `load_neurips_2020`
- [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]] — imports `ExperimentSettings`, `SWEEPS`, `run_experiments`; calls `ExperimentSettings`, `run_experiments`
- [[Reference/Modules/learnloop/evsi_calibration/family_data|learnloop.evsi_calibration.family_data]] — imports `build_subject_data`, `build_triple_data`; calls `build_subject_data`, `build_triple_data`
- [[Reference/Modules/learnloop/evsi_calibration/family_fit|learnloop.evsi_calibration.family_fit]] — imports `FamilyFitSettings`, `FamilyFits`, `fit_families`; calls `FamilyFitSettings`, `fit_families`
- [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]] — imports `calibration_report`; calls `calibration_report`
- [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]] — imports `MultiFamilySettings`, `analyze`, `run_multifamily`; calls `MultiFamilySettings`, `analyze`, `run_multifamily`
- [[Reference/Modules/learnloop/evsi_calibration/response_fit|learnloop.evsi_calibration.response_fit]] — imports `FitSettings`, `ResponseFit`, `fit_response_model`; calls `FitSettings`, `fit_response_model`
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

- [tests/test_evsi_single_family_unbounded.py](../../../../../../tests/test_evsi_single_family_unbounded.py) — direct import
  - `test_cli_simulate_passes_an_explicit_bound_through`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/evsi.py](../../../../../../src/learnloop/cli/evsi.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
