---
title: "learnloop.diagnosis.causal_factor_deferral"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/causal_factor_deferral.py"
source_paths:
  - "src/learnloop/diagnosis/causal_factor_deferral.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.causal_factor_deferral module"
  - "src/learnloop/diagnosis/causal_factor_deferral.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.causal_factor_deferral`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.causal_factor_deferral` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Bounded deferral for promotion-blocking unresolved-cause factors.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/causal_factor_deferral.py](../../../../../../src/learnloop/diagnosis/causal_factor_deferral.py) |
| Source lines | 488 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `apply_cold_verification_to_factors(repository: Repository, *, receipt: Mapping[str, Any], clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_factor_deferral.py), line 171) — Route one recorded cold verification into open diagnostic factors.
- `sweep_promotion_blocking_factors(repository: Repository, *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_factor_deferral.py), line 347) — Attempt-time sweep: exits (b-ii) and (c) for every open factor.

### Module constants

- `ESCALATION_RECURRENCE_K` ([src/learnloop/diagnosis/causal_factor_deferral.py](../../../../../../src/learnloop/diagnosis/causal_factor_deferral.py), line 69)
- `FACTOR_DEFERRAL_TTL` ([src/learnloop/diagnosis/causal_factor_deferral.py](../../../../../../src/learnloop/diagnosis/causal_factor_deferral.py), line 75)
- `_HYPOTHESIS_STATUSES` ([src/learnloop/diagnosis/causal_factor_deferral.py](../../../../../../src/learnloop/diagnosis/causal_factor_deferral.py), line 77)

## Internal implementation anchors

- `_concrete_refs(factor: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_factor_deferral.py), line 80) — The factor's hydrated non-open-set candidate refs.
- `_open_factors(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_factor_deferral.py), line 96) — Every open factor, attempt-keyed AND observation-keyed (G15).
- `_withdraw_candidate_hypothesis(repository: Repository, hypothesis_id: str, *, reason: str, evidence_ref: Mapping[str, Any], clock: Clock | None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/causal_factor_deferral.py), line 110) — Withdraw one candidate belief by appending a retired hypothesis version.
- `_factor_signature(repository: Repository, factor: Mapping[str, Any]) -> tuple[set[str], str | None]` ([source](../../../../../../src/learnloop/diagnosis/causal_factor_deferral.py), line 267) — (normalized statements, learning_object_id) for a factor's concrete refs.
- `_signature_hypotheses(repository: Repository, learning_object_id: str, statements: set[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/causal_factor_deferral.py), line 285)
- `_case_engaged(repository: Repository, *, learning_object_id: str, statements: set[str], case_factor_ids: list[str], hypothesis_rows: list[dict[str, Any]], since: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/causal_factor_deferral.py), line 301) — Any learner engagement on the case since its first factor opened.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `sweep_promotion_blocking_factors`; statically calls `sweep_promotion_blocking_factors`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `apply_cold_verification_to_factors`; statically calls `apply_cold_verification_to_factors`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `sweep_promotion_blocking_factors`; statically calls `sweep_promotion_blocking_factors`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]], [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]], [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_factor_deferral.py](../../../../../../tests/test_causal_factor_deferral.py) — direct import
  - `test_cold_success_resolves_observation_keyed_factor`
  - `test_engagement_keeps_the_deferral_window_open`
  - `test_expiry_retires_unengaged_factor_and_sweep_is_idempotent`
  - `test_projection_sync_does_not_resurrect_deferral_closed_factors`
  - `test_successful_cold_verification_resolves_factor_and_withdraws_belief`
  - `test_unengaged_recurrences_escalate_and_promote`

## Modification guidance

- Change causal factor deferral policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/causal_factor_deferral.py](../../../../../../src/learnloop/diagnosis/causal_factor_deferral.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
