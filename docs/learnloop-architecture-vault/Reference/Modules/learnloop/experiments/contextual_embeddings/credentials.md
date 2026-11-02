---
title: "learnloop.experiments.contextual_embeddings.credentials"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/credentials.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/credentials.py"
source_commit: "6b203def3a58cc7d7eb281f242b8c9e9110a0a51"
source_commit_timestamp: "2026-10-22T23:05:49-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.credentials module"
  - "src/learnloop/experiments/contextual_embeddings/credentials.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.credentials`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.credentials` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: Hosted API keys: the process environment only, never printed (spec D13).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/credentials.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/credentials.py) |
| Source lines | 114 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6b203def3a58cc7d7eb281f242b8c9e9110a0a51` |
| Commit timestamp | `2026-10-22T23:05:49-04:00` |

## Public API

- `class EnvFileError(ValueError)` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/credentials.py), line 22) — The env file could not be read; the message never contains file contents.
- `load_env_file(path: Path | str, names: Iterable[str], *, environ: MutableMapping[str, str] | None=None) -> dict[str, str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/credentials.py), line 34) — Load the named variables from ``path`` into ``environ`` (default ``os.environ``) without overriding values already set.
- `load_env_files(paths: Sequence[Path | str], names: Iterable[str], *, environ: MutableMapping[str, str] | None=None) -> dict[str, str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/credentials.py), line 72) — Load the named variables from every file of ``paths`` (``--env-file`` given more than once) into ``environ`` (default ``os.environ``), never overriding a value the shell already set.
- `availability(names: Iterable[str], *, environ: Mapping[str, str] | None=None) -> dict[str, str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/credentials.py), line 102) — ``{name: "present" | "absent"}``; the redacted check every report uses.
- `read_key(name: str, *, environ: Mapping[str, str] | None=None) -> str | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/credentials.py), line 109) — The key's value for an adapter's request header (never logged).

### Module constants

- `_LINE` ([src/learnloop/experiments/contextual_embeddings/credentials.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/credentials.py), line 18)
- `_NAME` ([src/learnloop/experiments/contextual_embeddings/credentials.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/credentials.py), line 19)

## Internal implementation anchors

- `_value(raw: str) -> str` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/credentials.py), line 26)
- `_parse(path: Path | str, wanted: Sequence[str]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/credentials.py), line 47) — The named, non-empty assignments of one dotenv file (no other line is read back).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/adapters|learnloop.experiments.contextual_embeddings.adapters]] — imports `module`; statically calls `read_key`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/anthropic_api|learnloop.experiments.contextual_embeddings.anthropic_api]] — imports `module`; statically calls `read_key`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `module`; statically calls `availability`, `load_env_files`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]] — imports `module`; statically calls `availability`, `load_env_files`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `os`, `pathlib`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/adapters|learnloop.experiments.contextual_embeddings.adapters]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/anthropic_api|learnloop.experiments.contextual_embeddings.anthropic_api]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/runner|learnloop.experiments.contextual_embeddings.runner]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_credentials.py](../../../../../../../tests/test_e0_credentials.py) — direct import
  - `test_an_unreadable_env_file_does_not_quote_it`
  - `test_availability_reports_names_only`
  - `test_env_file_loading_never_echoes_values`
  - `test_env_file_loads_only_named_variables_and_never_overrides_the_shell`
- [tests/test_e0_review_round5.py](../../../../../../../tests/test_e0_review_round5.py) — direct import
  - `test_several_env_files_load_by_name_and_a_conflict_is_refused_naming_the_variable_only`

## Modification guidance

- Make changes here when the responsibility remains credentials within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/credentials.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/credentials.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
