---
title: "learnloop.experiments.contextual_embeddings.e1.run"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/e1/run.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/e1/run.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings.e1"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.e1.run module"
  - "src/learnloop/experiments/contextual_embeddings/e1/run.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings-e1"
---

# `learnloop.experiments.contextual_embeddings.e1.run`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.e1.run` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] to own the behavior summarized by its module contract: E1's stages: dry run, preflight, local (GPU), labels (paid), score.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/e1/run.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py) |
| Source lines | 485 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class PlanRefused(ValueError)` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 48) — The plan cannot run this stage (nothing was started or spent).
- `class LayeredVectorStore(VectorStore)` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 52) — E0's imported vectors read-only beneath E1's own (fills go on top).
  - `__init__(self, base: Path, overlay: Path) -> None` (line 55; internal)
  - `get(self, space: str, key: str) -> list[list[float]] | None` (line 59; public)
  - `get_raw(self, space: str, key: str) -> Any` (line 62; public)
  - `put(self, space: str, key: str, vectors: Sequence[Sequence[float]], *, raw: Any=None) -> None` (line 65; public)
- `run_root(layout: ImportLayout, plan_id: str) -> Path` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 70)
- `hosted_store(layout: ImportLayout, label: str, root: Path) -> LayeredVectorStore` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 80)
- `replay_all(layout: ImportLayout, *, root: Path | None=None) -> list[Replayed]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 84)
- `dry_run(*, e0_run_dir: Path | None=None, import_dir: Path | None=None, env_file: Sequence[Path]=(), environ: Mapping[str, str] | None=None) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 97) — The E1 plan with no network and no write to any input (digests checked before and after).
- `require_frozen(plan: Mapping[str, Any], layout: ImportLayout) -> None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 147) — A stage runs only the frozen plan the import rebuilds to.
- `environment_versions(env_python: Path, *, run: Callable[..., Any]=subprocess.run) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 159) — The separate environment's package versions (never the app's).
- `resources_now(*, meminfo: Callable[[], Mapping[str, int]]=worker_module.read_meminfo, gpu: Callable[[], Mapping[str, Any] | None]=worker_module.gpu_state) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 173)
- `preflight(plan: Mapping[str, Any], layout: ImportLayout, *, model_dir: Path, env_python: Path, verify_weights: bool=False, resources: Callable[[], dict[str, Any]]=resources_now, versions: Callable[[Path], dict[str, Any]]=environment_versions) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 192) — Every check the GPU stage needs, without loading anything (no network).
- `run_local(plan: Mapping[str, Any], layout: ImportLayout, *, model_dir: Path, launcher: Any, check_plan: bool=True, smoke_only: bool=False) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 229) — ONE scoped worker for every missing v2 document and query (resumable).
- `v2_rankings(replayed: Replayed, store: VectorStore) -> tuple[dict[str, dict[str, list[str]]], dict[str, Any]]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 269)
- `label_estimate(per_question: Sequence[int], replayed: Replayed) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 285) — Dollars for the supplementary labels of these real counts (the plan's token model).
- `run_labels(plan: Mapping[str, Any], layout: ImportLayout, *, authorized: bool=False, dry_run_only: bool=False, env_file: Sequence[Path]=(), key_envs: Mapping[str, str] | None=None, new_authorization: str | None=None, transport: Any=None, client_factory: Any=None, environ: Mapping[str, str] | None=None, check_plan: bool=True) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 318) — The v2 arms' new candidates labelled (and any voyage-context-4 fill) under E1's ledger.
- `save_supplement(path: Path, outcome: Mapping[str, Any]) -> None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 414)
- `load_supplement(path: Path) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 428)
- `score(plan: Mapping[str, Any], layout: ImportLayout, *, check_plan: bool=True) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 446)

### Module constants

- `KEY_ENVS` ([src/learnloop/experiments/contextual_embeddings/e1/run.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 36)
- `VERSION_PROBE` ([src/learnloop/experiments/contextual_embeddings/e1/run.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 37)

## Internal implementation anchors

- `_scratch(layout: ImportLayout) -> Path` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 74)
- `_prior(anchor: Path) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 140)
- `_priority(question: Any) -> tuple[int, str]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 310)
- `_fill_hosted(replayed: Replayed, arms: Sequence[str], *, ledger: Any, store: VectorStore, receipts_path: Path, transport: Any, key_envs: Mapping[str, str], environ: Mapping[str, str] | None) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py), line 391) — The voyage-context-4 vectors E0 never stored, bought under E1's ledger (the route's canary first, checked against E0's first canary).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]] — imports `dry_run`, `module`, `preflight`; statically calls `dry_run`, `preflight`, `run_labels`, `run_local`, `score`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/adapters|learnloop.experiments.contextual_embeddings.adapters]] — imports `AdapterError`, `Receipts`, `UrllibTransport`, `VectorStore`; calls `Receipts`, `UrllibTransport`, `VectorStore`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/budget|learnloop.experiments.contextual_embeddings.budget]] — imports `E0Stop`, `ledger_spend`; calls `ledger_spend`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/callers|learnloop.experiments.contextual_embeddings.callers]] — imports `Checkpoints`, `LiveRoleCaller`, `canary_models`; calls `Checkpoints`, `LiveRoleCaller`, `canary_models`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `_inside_local_root`; calls `_inside_local_root`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/credentials|learnloop.experiments.contextual_embeddings.credentials]] — imports `module`; calls `availability`, `load_env_files`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/decide|learnloop.experiments.contextual_embeddings.e1.decide]] — imports `decide_e1`; calls `decide_e1`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/gpu_meter|learnloop.experiments.contextual_embeddings.e1.gpu_meter]] — imports `GpuMeter`, `MIN_SLOT_S`; calls `GpuMeter`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/ledger|learnloop.experiments.contextual_embeddings.e1.ledger]] — imports `authorized_ledger`, `ledger_dir`, `prior_spend`; calls `authorized_ledger`, `ledger_dir`, `prior_spend`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]] — imports `build_job`, `limits`, `measurements`, `rank_v2`, `store_outputs`; calls `build_job`, `limits`, `measurements`, `rank_v2`, `store_outputs`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/pins|learnloop.experiments.contextual_embeddings.e1.pins]] — imports `module`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/plan|learnloop.experiments.contextual_embeddings.e1.plan]] — imports `build_plan`, `import_inputs`, `manifest_inputs`, `module`; calls `_call_usd`, `build_plan`, `import_inputs`, `manifest_inputs`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `ImportLayout`, `Replayed`, `question_texts`, `replay_copy`, `run_identity`, `verify_import`, `verify_replay`; calls `ImportLayout`, `question_texts`, `replay_copy`, `run_identity`, `verify_import`, `verify_replay`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/supplement|learnloop.experiments.contextual_embeddings.e1.supplement]] — imports `E1_ROLE_PINS`, `Supplement`, `merge`, `new_candidates`, `supplement_all`; calls `Supplement`, `merge`, `new_candidates`, `supplement_all`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/worker|learnloop.experiments.contextual_embeddings.e1.worker]] — imports `module`; calls `model_dir_problems`, `other_processes`, `start_problems`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/evaluate|learnloop.experiments.contextual_embeddings.evaluate]] — imports `question_rows`; calls `question_rows`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `NON_PRIMARY_STRATA`, `allowed_units`, `make_adapter`, `rank_arm`; calls `allowed_units`, `make_adapter`, `rank_arm`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`; calls `token_estimate`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/records|learnloop.experiments.contextual_embeddings.records]] — imports `ExperimentRecords`; calls `ExperimentRecords`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/report|learnloop.experiments.contextual_embeddings.report]] — imports `assert_aggregate`; calls `assert_aggregate`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `network_guard`, `tree_digest`; calls `network_guard`, `tree_digest`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `math`, `os`, `pathlib`, `shutil`, `subprocess`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/experiments|learnloop.cli.experiments]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e1_harness.py](../../../../../../../../tests/test_e1_harness.py) — direct import
  - `test_a_provisional_plan_runs_no_stage`
  - `test_a_smoke_only_local_run_loads_checks_and_stores_nothing`
  - `test_a_wrong_label_pool_misses_e0s_checkpoints_and_the_replay_is_unverified`
  - `test_an_unfinished_e0_run_is_not_imported_and_the_manifest_plan_is_provisional`
  - `test_preflight_reports_every_check_and_is_not_ready_without_the_model`
  - `test_the_replay_reproduces_e0_without_any_call_and_the_plan_is_frozen`
  - `test_the_separate_environment_must_carry_the_pinned_versions`
  - `test_the_whole_pilot_with_fakes`

## Modification guidance

- Make changes here when the responsibility remains run within learnloop.experiments.contextual_embeddings.e1; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/e1/run.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/run.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
