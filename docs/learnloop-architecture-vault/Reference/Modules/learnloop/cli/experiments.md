---
title: "learnloop.cli.experiments"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/experiments.py"
source_paths:
  - "src/learnloop/cli/experiments.py"
source_commit: "5bcead897e0c117ad063e707611aacf640acddad"
source_commit_timestamp: "2026-10-24T00:11:39-04:00"
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
  - "learnloop.cli.experiments module"
  - "src/learnloop/cli/experiments.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.experiments`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.cli.experiments` exists within [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] to own the behavior summarized by its module contract: `learnloop experiments`: research experiments on vault copies (never production).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/experiments.py](../../../../../../src/learnloop/cli/experiments.py) |
| Source lines | 309 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5bcead897e0c117ad063e707611aacf640acddad` |
| Commit timestamp | `2026-10-24T00:11:39-04:00` |

## Public API

- `e0_prepare(source: Annotated[list[Path], typer.Option('--from', help='A vault root to copy (repeatable; never arxiv_v2).')], label: Annotated[str, typer.Option('--label', help="Suffix of each copy's directory, such as a date.")], dest: Annotated[Path, typer.Option('--dest', help='Under a fixtures-local directory.')]=_DEFAULT_ROOT / 'vaults') -> None` ([source](../../../../../../src/learnloop/cli/experiments.py), line 40) — Copy vaults through SQLite's backup API (WAL state included) for E0.
- `e0_run(copy: Annotated[list[Path], typer.Option('--copy', help='A prepared vault copy (repeatable).')], dry_run: Annotated[bool, typer.Option('--dry-run', help='Plan only: no network, nothing written to the copies.')]=False, env_file: Annotated[list[Path] | None, typer.Option('--env-file', help='Load only the named key variables from this dotenv file (repeatable; never printed; a variable with different values in two files is refused).')]=None, preflight_only: Annotated[bool, typer.Option('--preflight-only', help="Load the env files and report the paid run's checks (keys present/absent only); no network, nothing spent.")]=False, perplexity_key_env: Annotated[str, typer.Option('--perplexity-key-env')]='PERPLEXITY_API_KEY', voyage_key_env: Annotated[str, typer.Option('--voyage-key-env')]='VOYAGE_API_KEY', openrouter_key_env: Annotated[str, typer.Option('--openrouter-key-env')]='OPENROUTER_API_KEY', anthropic_key_env: Annotated[str, typer.Option('--anthropic-key-env', help='The Messages API key variable (loaded only through --env-file).')]='ANTHROPIC_API_KEY', reserve_share: Annotated[float, typer.Option('--reserve-share', min=0.0, max=1.0, help='Source families reserved before question writing.')]=0.0, out: Annotated[Path | None, typer.Option('--out', help='Write the plan (JSON) here.')]=None, markdown: Annotated[Path | None, typer.Option('--markdown', help='Write the plan (Markdown) here.')]=None, run_dir: Annotated[Path, typer.Option('--run-dir', help="The paid run's private directory.")]=_DEFAULT_ROOT / 'runs', authorized: Annotated[bool, typer.Option('--i-am-authorized-to-spend', help="The orchestrator's explicit authorization for the paid run.")]=False, reader_latency_budget_s: Annotated[float | None, typer.Option('--reader-latency-budget-s', min=0.1, help='The pinned Reader p95 answer budget for S2/S4 (unset: those rules fail closed).')]=None, json_output: Annotated[bool, typer.Option('--json')]=False, new_authorization: Annotated[str | None, typer.Option('--new-authorization', help="The orchestrator's reason for a new plan's budget while another plan's ledger exists (that ledger is sealed and its spend carried: the cap is cumulative).")]=None, reuse_run: Annotated[str | None, typer.Option('--reuse-run', help='An earlier run id under --run-dir whose content-keyed stores this plan reuses (checkpoints, vectors, service copies, records); its ledger prices the remaining work.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/experiments.py), line 57) — Plan (--dry-run), check (--preflight-only) or run E0 on prepared copies within the $40 cap.
- `e0_report(results: Annotated[Path, typer.Option('--results', help='A results JSON written by the paid run.')], out: Annotated[Path | None, typer.Option('--out', help='Write the Markdown report here.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/experiments.py), line 149) — Render the aggregate E0 report (refuses private fields).
- `e1_import(e0_run: Annotated[Path, typer.Option('--e0-run', help='A FINISHED E0 run directory (runs/<e0 plan id>).')], e0_vaults: Annotated[Path, typer.Option('--e0-vaults', help="E0's frozen vault copies directory.")], dest: Annotated[Path | None, typer.Option('--dest', help='Under fixtures-local (default e1/imports/<run>).')]=None) -> None` ([source](../../../../../../src/learnloop/cli/experiments.py), line 177) — Copy a finished E0 run's outputs into E1's fixtures-local (backup API; read-only on E0).
- `e1_plan(e0_run: Annotated[Path | None, typer.Option('--e0-run', help="Plan from E0's frozen manifests (provisional).")]=None, import_dir: Annotated[Path | None, typer.Option('--import', help='Plan from a verified E1 import (frozen).')]=None, env_file: Annotated[list[Path] | None, typer.Option('--env-file', help='Report key presence (names only).')]=None, out: Annotated[Path | None, typer.Option('--out', help='Write the plan (JSON) here.')]=None, markdown: Annotated[Path | None, typer.Option('--markdown', help='Write the plan (Markdown) here.')]=None, json_output: Annotated[bool, typer.Option('--json')]=False) -> None` ([source](../../../../../../src/learnloop/cli/experiments.py), line 195) — The E1 dry run: the plan, GPU-hours and dollar estimates; no network, nothing written to the inputs.
- `e1_preflight(import_dir: Annotated[Path, typer.Option('--import', help='The E1 import.')], plan_path: Annotated[Path, typer.Option('--plan', help='The frozen E1 plan (JSON from `e1 plan --import`).')], model_dir: Annotated[Path, typer.Option('--model-dir', help='The downloaded model at the pinned revision.')], env_python: Annotated[Path, typer.Option('--env-python', help="The SEPARATE environment's interpreter.")], verify_weights: Annotated[bool, typer.Option('--verify-weights', help='Hash every shard (~34 GB read).')]=False) -> None` ([source](../../../../../../src/learnloop/cli/experiments.py), line 222) — Every check the GPU stage needs (resources measured now), nothing loaded.
- `e1_run(stage: Annotated[str, typer.Option('--stage', help='local (GPU), labels (paid) or score.')], import_dir: Annotated[Path, typer.Option('--import', help='The E1 import.')], plan_path: Annotated[Path, typer.Option('--plan', help='The frozen E1 plan.')], model_dir: Annotated[Path | None, typer.Option('--model-dir')]=None, env_python: Annotated[Path | None, typer.Option('--env-python')]=None, idle_gpu: Annotated[bool, typer.Option('--i-have-an-idle-gpu-slot', help="The owner's idle GPU slot (local stage).")]=False, authorized: Annotated[bool, typer.Option('--i-am-authorized-to-spend', help="The orchestrator's authorization (labels stage, <= $5).")]=False, dry_run: Annotated[bool, typer.Option('--dry-run', help='labels: exact counts and estimate, no network.')]=False, smoke_only: Annotated[bool, typer.Option('--smoke-only', help='local: load, the smoke checks, unload; no profiling or encoding (metered).')]=False, env_file: Annotated[list[Path] | None, typer.Option('--env-file', help='Load only the named keys.')]=None, new_authorization: Annotated[str | None, typer.Option('--new-authorization')]=None) -> None` ([source](../../../../../../src/learnloop/cli/experiments.py), line 245) — Run one E1 stage of a frozen plan.
- `e1_report(results: Annotated[Path, typer.Option('--results', help='results.json from `e1 run --stage score`.')], out: Annotated[Path | None, typer.Option('--out', help='Write the Markdown report here.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/experiments.py), line 295) — Render the aggregate E1 report (refuses private fields).

### Module constants

- `_DEFAULT_ROOT` ([src/learnloop/cli/experiments.py](../../../../../../src/learnloop/cli/experiments.py), line 26)
- `_E1_ROOT` ([src/learnloop/cli/experiments.py](../../../../../../src/learnloop/cli/experiments.py), line 169)

## Internal implementation anchors

- `_fail(exc: Exception) -> None` ([source](../../../../../../src/learnloop/cli/experiments.py), line 29) — Print a failure's SAFE message only (never a provider's text, which can echo a credential: fix round 4, High 8) and exit 1, unchained.
- `_e1_plan(path: Path) -> dict` ([source](../../../../../../src/learnloop/cli/experiments.py), line 172)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `experiments_app`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/cli/receipts|learnloop.cli.receipts]] — imports `bind_command_repository`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/boundary|learnloop.experiments.contextual_embeddings.boundary]] — imports `require_codex_lockdown`, `safe_message`; calls `require_codex_lockdown`, `safe_message`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `prepare_copies`; calls `prepare_copies`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]] — imports `ScopedLauncher`; calls `ScopedLauncher`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/plan|learnloop.experiments.contextual_embeddings.e1.plan]] — imports `render_markdown`; calls `render_markdown`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `ImportLayout`, `import_e0`; calls `ImportLayout`, `import_e0`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/report|learnloop.experiments.contextual_embeddings.e1.report]] — imports `render`; calls `render`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `dry_run`, `module`, `preflight`; calls `dry_run`, `preflight`, `run_labels`, `run_local`, `score`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `run_live`; calls `run_live`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/report|learnloop.experiments.contextual_embeddings.report]] — imports `render`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `dry_run`, `preflight`, `render_markdown`, `require_paid_authorization`; calls `dry_run`, `preflight`, `require_paid_authorization`

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

1. Modify [src/learnloop/cli/experiments.py](../../../../../../src/learnloop/cli/experiments.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
