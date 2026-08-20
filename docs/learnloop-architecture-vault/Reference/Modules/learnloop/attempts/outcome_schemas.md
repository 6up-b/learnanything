---
title: "learnloop.attempts.outcome_schemas"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/outcome_schemas.py"
source_paths:
  - "src/learnloop/attempts/outcome_schemas.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.outcome_schemas module"
  - "src/learnloop/attempts/outcome_schemas.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.outcome_schemas`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.outcome_schemas` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Coarse outcome schemas (spec_p0_measurement_correctness §3.1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/outcome_schemas.py](../../../../../../src/learnloop/attempts/outcome_schemas.py) |
| Source lines | 161 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class BuiltinSchema` ([source](../../../../../../src/learnloop/attempts/outcome_schemas.py), line 38)
  - `content_payload(self) -> dict[str, Any]` (line 48; public)
  - `content_hash(self) -> str` (line 60; public)
- `ensure_builtin_schemas(repository: Repository, *, clock: Clock | None=None) -> dict[str, str]` ([source](../../../../../../src/learnloop/attempts/outcome_schemas.py), line 125) — Idempotently seed the builtin outcome schemas (§3.1).
- `resolve_schema_id(repository: Repository, slug: str, *, clock: Clock | None=None) -> tuple[str, int]` ([source](../../../../../../src/learnloop/attempts/outcome_schemas.py), line 152) — Return ``(schema_id, version)`` for a slug, seeding builtins if absent.

### Module constants

- `COARSE_RESPONSE_SLUG` ([src/learnloop/attempts/outcome_schemas.py](../../../../../../src/learnloop/attempts/outcome_schemas.py), line 22)
- `COARSE_RESPONSE_UNANSWERED_SLUG` ([src/learnloop/attempts/outcome_schemas.py](../../../../../../src/learnloop/attempts/outcome_schemas.py), line 23)
- `SIGNATURE_ERROR_SLUG` ([src/learnloop/attempts/outcome_schemas.py](../../../../../../src/learnloop/attempts/outcome_schemas.py), line 24)
- `CRITERION_4CLASS_SLUG` ([src/learnloop/attempts/outcome_schemas.py](../../../../../../src/learnloop/attempts/outcome_schemas.py), line 25)
- `PARTIAL_SUCCESS_SCORE_FRACTION` ([src/learnloop/attempts/outcome_schemas.py](../../../../../../src/learnloop/attempts/outcome_schemas.py), line 30)
- `CRITERION_PARTIAL_SCORE_FRACTION` ([src/learnloop/attempts/outcome_schemas.py](../../../../../../src/learnloop/attempts/outcome_schemas.py), line 31)
- `UNASSESSABLE_SCORE_FRACTION` ([src/learnloop/attempts/outcome_schemas.py](../../../../../../src/learnloop/attempts/outcome_schemas.py), line 32)
- `SIGNATURE_ERROR_SCORE_FRACTION` ([src/learnloop/attempts/outcome_schemas.py](../../../../../../src/learnloop/attempts/outcome_schemas.py), line 33)
- `UNANSWERED_SCORE_FRACTION` ([src/learnloop/attempts/outcome_schemas.py](../../../../../../src/learnloop/attempts/outcome_schemas.py), line 34)
- `BUILTIN_SCHEMAS` ([src/learnloop/attempts/outcome_schemas.py](../../../../../../src/learnloop/attempts/outcome_schemas.py), line 64)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `COARSE_RESPONSE_SLUG`, `ensure_builtin_schemas`, `resolve_schema_id`; statically calls `ensure_builtin_schemas`, `resolve_schema_id`
- [[Reference/Modules/learnloop/attempts/grader_calibration|learnloop.attempts.grader_calibration]] — imports `BUILTIN_SCHEMAS`, `ensure_builtin_schemas`; statically calls `ensure_builtin_schemas`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `BUILTIN_SCHEMAS`, `COARSE_RESPONSE_SLUG`
- [[Reference/Modules/learnloop/diagnosis/probe_outcome_mapping|learnloop.diagnosis.probe_outcome_mapping]] — imports `BUILTIN_SCHEMAS`, `COARSE_RESPONSE_SLUG`, `COARSE_RESPONSE_UNANSWERED_SLUG`, `SIGNATURE_ERROR_SLUG`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `SIGNATURE_ERROR_SLUG`, `resolve_schema_id`; statically calls `resolve_schema_id`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `COARSE_RESPONSE_SLUG`, `ensure_builtin_schemas`; statically calls `ensure_builtin_schemas`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`, `canonical_json`; calls `canonical_hash`, `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]], [[Reference/Modules/learnloop/attempts/grader_calibration|learnloop.attempts.grader_calibration]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]], [[Reference/Modules/learnloop/diagnosis/probe_outcome_mapping|learnloop.diagnosis.probe_outcome_mapping]], [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_effective_observation.py](../../../../../../tests/test_effective_observation.py) — direct import
- [tests/test_event_sufficiency.py](../../../../../../tests/test_event_sufficiency.py) — direct import
  - `test_replay_prefers_active_interpretation_head`
- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_builtin_schemas_and_heuristic_priors_are_idempotent`
  - `test_insert_calibration_model_is_content_addressed_no_duplicate`
  - `test_resolution_seeds_and_missing_child_inherits_parent`
  - `test_signature_error_reachable_when_signature_matched_threaded`
- [tests/test_grader_channel_prior_knobs.py](../../../../../../tests/test_grader_channel_prior_knobs.py) — direct import
- [tests/test_observation_ledger_bulk.py](../../../../../../tests/test_observation_ledger_bulk.py) — direct import
  - `test_p0_replays_bulk_load_calibration_references_once`

## Modification guidance

- Change outcome schemas policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/outcome_schemas.py](../../../../../../src/learnloop/attempts/outcome_schemas.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
