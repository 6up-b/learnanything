---
title: "learnloop.local_embeddings.setup"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/local_embeddings/setup.py"
source_paths:
  - "src/learnloop/local_embeddings/setup.py"
source_commit: "e1e10f69b9ad6f40b364fe4f79097caa108bcdd4"
source_commit_timestamp: "2026-10-24T20:18:30-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.local_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.local_embeddings.setup module"
  - "src/learnloop/local_embeddings/setup.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-local-embeddings"
---

# `learnloop.local_embeddings.setup`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.local_embeddings.setup` exists within [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] to own the behavior summarized by its module contract: The owner-run setup of the local space (spec §10 P1a, §11, Q11).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/local_embeddings/setup.py](../../../../../../src/learnloop/local_embeddings/setup.py) |
| Source lines | 201 |
| Owning package | [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e1e10f69b9ad6f40b364fe4f79097caa108bcdd4` |
| Commit timestamp | `2026-10-24T20:18:30-04:00` |

## Public API

- `setup_plan(root: Path | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/setup.py), line 62) — What setup would do, measured now (no process started, nothing written).
- `requirement_problems(run: Runner, env_python: Path, env: dict[str, str]) -> list[str]` ([source](../../../../../../src/learnloop/local_embeddings/setup.py), line 84) — What the environment lacks against the pins, asked of its own interpreter (a path that exists is not an installed environment: an interrupted install leaves the interpreter behind; Codex review F16).
- `run_setup(*, root: Path | None=None, run: Runner=subprocess.run, adopt_model_dir: Path | None=None, adopt_env_python: Path | None=None, verify_weights: bool=True, disk_free: Callable[[Path], int] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/setup.py), line 119) — Create (or adopt) the environment and the model, verify them, write the manifest.
- `load_manifest(root: Path | None=None) -> tuple[dict[str, Any] | None, str | None]` ([source](../../../../../../src/learnloop/local_embeddings/setup.py), line 184) — ``(manifest, None)`` when setup ran and its artefacts exist, else ``(None, why)``.

### Module constants

- `GIB` ([src/learnloop/local_embeddings/setup.py](../../../../../../src/learnloop/local_embeddings/setup.py), line 29)
- `_DOWNLOAD` ([src/learnloop/local_embeddings/setup.py](../../../../../../src/learnloop/local_embeddings/setup.py), line 32)
- `_INSTALLED` ([src/learnloop/local_embeddings/setup.py](../../../../../../src/learnloop/local_embeddings/setup.py), line 37)
- `_EPOCH` ([src/learnloop/local_embeddings/setup.py](../../../../../../src/learnloop/local_embeddings/setup.py), line 48)

### Explicit exports

`__all__` declares:

- `load_manifest`
- `requirement_problems`
- `run_setup`
- `setup_plan`

## Internal implementation anchors

- `_run(run: Runner, command: Sequence[str], *, env: dict[str, str] | None=None) -> str` ([source](../../../../../../src/learnloop/local_embeddings/setup.py), line 55)
- `_pinned_requirements() -> dict[str, str]` ([source](../../../../../../src/learnloop/local_embeddings/setup.py), line 80)
- `_owed_bytes(model: Path) -> int` ([source](../../../../../../src/learnloop/local_embeddings/setup.py), line 108) — The pinned bytes a (partial) model directory still lacks (missing or wrong-sized files).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]] — imports `run_setup`, `setup_plan`; statically calls `run_setup`, `setup_plan`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `load_manifest`; statically calls `load_manifest`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `load_manifest`; statically calls `load_manifest`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/local_embeddings/pins|learnloop.local_embeddings.pins]] — imports `module`; calls `data_root`, `env_dir`, `manifest_path`, `model_dir`
- [[Reference/Modules/learnloop/local_embeddings/worker|learnloop.local_embeddings.worker]] — imports `model_dir_problems`; calls `model_dir_problems`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `os`, `pathlib`, `shutil`, `subprocess`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/embeddings|learnloop.cli.embeddings]], [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]], [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_local_index.py](../../../../../../tests/test_local_index.py) — direct import
  - `test_an_interrupted_setup_resumes_the_install_and_the_download`
  - `test_setup_verifies_the_files_records_the_epoch_and_adopts_without_moving`

## Modification guidance

- Make changes here when the responsibility remains setup within learnloop.local_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/local_embeddings/setup.py](../../../../../../src/learnloop/local_embeddings/setup.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
