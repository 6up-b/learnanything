---
title: "learnloop.source_retrieval.timing"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/timing.py"
source_paths:
  - "src/learnloop/source_retrieval/timing.py"
source_commit: "debd86c0d24a1e4837b20b76aad6a47a8720f8b2"
source_commit_timestamp: "2026-10-13T00:18:31-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.timing module"
  - "src/learnloop/source_retrieval/timing.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.timing`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.timing` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: How long the tutor's source retrieval takes, from the questions' receipts.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/timing.py](../../../../../../src/learnloop/source_retrieval/timing.py) |
| Source lines | 101 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `debd86c0d24a1e4837b20b76aad6a47a8720f8b2` |
| Commit timestamp | `2026-10-13T00:18:31-04:00` |

## Public API

- `step_stats(values: Sequence[float], *, soft_deadline_ms: float) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/timing.py), line 31)
- `truncated_answers(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/timing.py), line 39) — Root receipts whose answer stopped for length, by purpose and model.
- `tutor_timing_report(repository: Repository, *, soft_deadline_seconds: float, cancels_at_deadline: bool=False, since: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/timing.py), line 50) — Per-step p50/p90 over every tutor question whose receipt timed its retrieval.

### Explicit exports

`__all__` declares:

- `step_stats`
- `truncated_answers`
- `tutor_timing_report`

## Internal implementation anchors

- `_percentile(ordered: Sequence[float], q: float) -> float` ([source](../../../../../../src/learnloop/source_retrieval/timing.py), line 25) — Nearest-rank percentile of an ascending list.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `tutor_timing_report`; statically calls `tutor_timing_report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `TIMED_STEPS`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `math`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_retrieval_followup.py](../../../../../../tests/test_source_retrieval_followup.py) — direct import
  - `test_sources_report_gives_p50_and_p90_per_step_and_counts_truncations`

## Modification guidance

- Make changes here when the responsibility remains timing within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/timing.py](../../../../../../src/learnloop/source_retrieval/timing.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
