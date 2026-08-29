---
title: "learnloop.learner.hypothesis_claims"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/hypothesis_claims.py"
source_paths:
  - "src/learnloop/learner/hypothesis_claims.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.hypothesis_claims module"
  - "src/learnloop/learner/hypothesis_claims.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.hypothesis_claims`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.hypothesis_claims` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Typed learner-facing claim dispatch and local response telemetry.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/hypothesis_claims.py](../../../../../../src/learnloop/learner/hypothesis_claims.py) |
| Source lines | 277 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class HypothesisClaimError(ValueError)` ([source](../../../../../../src/learnloop/learner/hypothesis_claims.py), line 30)
- `canonical_claim_ref(value: Any) -> str` ([source](../../../../../../src/learnloop/learner/hypothesis_claims.py), line 34)
- `present_claims(repository: Repository, candidates: Iterable[Mapping[str, Any]], *, session_id: str | None=None, visit_id: str | None=None, session_card_budget: int=2, claim_cooldown_days: int=7, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/hypothesis_claims.py), line 67) — Dispatch claims under the attention budget and persist presentations.
- `record_response(repository: Repository, presentation_id: str, payload: Mapping[str, Any], *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/hypothesis_claims.py), line 220)
- `dismiss_claim(repository: Repository, presentation_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/hypothesis_claims.py), line 252)
- `export_claim_events(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/hypothesis_claims.py), line 272)
- `purge_claim_events(repository: Repository) -> int` ([source](../../../../../../src/learnloop/learner/hypothesis_claims.py), line 276)

### Module constants

- `CLAIM_CLASSES` ([src/learnloop/learner/hypothesis_claims.py](../../../../../../src/learnloop/learner/hypothesis_claims.py), line 18)
- `TEMPERATURES` ([src/learnloop/learner/hypothesis_claims.py](../../../../../../src/learnloop/learner/hypothesis_claims.py), line 19)
- `PRIORITY` ([src/learnloop/learner/hypothesis_claims.py](../../../../../../src/learnloop/learner/hypothesis_claims.py), line 20)

## Internal implementation anchors

- `_validate_candidate(candidate: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/learner/hypothesis_claims.py), line 40)
- `_cooldown_active(repository: Repository, *, claim_ref: str, claim_version: str, cooldown_days: int, clock: Clock) -> bool` ([source](../../../../../../src/learnloop/learner/hypothesis_claims.py), line 53)
- `_presentation_result(candidate: Mapping[str, Any], event: Mapping[str, Any], *, debounced: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/hypothesis_claims.py), line 195)
- `_presentation_or_raise(repository: Repository, presentation_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/hypothesis_claims.py), line 211)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `export_claim_events`, `purge_claim_events`
- [[Reference/Modules/learnloop_sidecar/handlers/claims|learnloop_sidecar.handlers.claims]] — imports `HypothesisClaimError`, `dismiss_claim`, `export_claim_events`, `present_claims`, `purge_claim_events`, `record_response`; statically calls `dismiss_claim`, `export_claim_events`, `present_claims`, `purge_claim_events`, `record_response`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/surfaced_beliefs|learnloop.learner.surfaced_beliefs]] — imports `resolve_belief_reference`; calls `resolve_belief_reference`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop_sidecar/handlers/claims|learnloop_sidecar.handlers.claims]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_hypothesis_claim_dispatcher.py](../../../../../../tests/test_hypothesis_claim_dispatcher.py) — direct import
  - `test_at_most_one_cold_reask_per_log_visit`
  - `test_cold_claims_never_take_the_reserved_hot_slot`
  - `test_debounce_same_version_and_re_presentation_of_changed_version`
  - `test_hot_claim_lands_after_cold_budget_is_exhausted`
  - `test_hot_claims_win_priority_within_one_dispatch`
  - `test_responded_claim_cools_down_for_seven_days`
  - `test_suppressed_presentation_rejects_responses`
- [tests/test_surfaced_belief_corrections.py](../../../../../../tests/test_surfaced_belief_corrections.py) — direct import
  - `test_non_belief_claims_never_record_a_belief_reference`
  - `test_suppressed_card_was_authored_not_shown`

## Modification guidance

- Change hypothesis claims policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/hypothesis_claims.py](../../../../../../src/learnloop/learner/hypothesis_claims.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
