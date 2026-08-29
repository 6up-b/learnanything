---
title: "learnloop.attempts.reveal_ledger"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/reveal_ledger.py"
source_paths:
  - "src/learnloop/attempts/reveal_ledger.py"
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
  - "learnloop.attempts.reveal_ledger module"
  - "src/learnloop/attempts/reveal_ledger.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.reveal_ledger`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.reveal_ledger` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: The cross-channel answer-reveal ledger (migration 154).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/reveal_ledger.py](../../../../../../src/learnloop/attempts/reveal_ledger.py) |
| Source lines | 230 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `reveal_episode_id(repository: Repository, practice_item_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 40) — The live repair episode an exposure on this item belongs to, if any.
- `record_reveal(repository: Repository, *, practice_item_id: str, source_kind: str, amount: float, learning_object_id: str | None=None, remediation_episode_id: str | None=None, basis: str | None=None, question_event_id: str | None=None, attempt_id: str | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 57) — Append one reveal.
- `class ProductionAdmissibility` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 102) — Whether a learner production counts as INDEPENDENT evidence.
- `production_admissibility(repository: Repository, *, practice_item_id: str | None, learning_object_id: str | None=None, produced_at: str | None, since: str | None=None) -> ProductionAdmissibility` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 118) — Admit a learner production unless a reveal preceded it in its window.
- `repair_display_amounts(repair_suggestions: Sequence[Mapping[str, Any]] | None) -> list[tuple[str, float]]` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 169) — (repair id, declared reveal budget) for suggestions that reveal anything.
- `record_repair_display_reveals(repository: Repository, *, attempt_id: str, practice_item_id: str | None, learning_object_id: str | None=None, repair_suggestions: Sequence[Mapping[str, Any]] | None=None, clock: Clock | None=None) -> int` ([source](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 193) — Debit the ledger for repair suggestions shown on a feedback screen.

### Module constants

- `REVEAL_SOURCE_KINDS` ([src/learnloop/attempts/reveal_ledger.py](../../../../../../src/learnloop/attempts/reveal_ledger.py), line 37)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `production_admissibility`; statically calls `production_admissibility`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `production_admissibility`; statically calls `production_admissibility`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `record_reveal`, `reveal_episode_id`; statically calls `record_reveal`, `reveal_episode_id`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `record_repair_display_reveals`; statically calls `record_repair_display_reveals`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `open_episode_for_practice_item`; calls `open_episode_for_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]], [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]], [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_a_probe_answered_after_a_reveal_is_not_independent_evidence`
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
  - `test_a_production_after_a_reveal_is_not_independent`
  - `test_a_reveal_on_a_sibling_item_of_the_same_lo_still_contaminates`
  - `test_an_eliciting_response_after_a_reveal_is_recorded_but_not_independent`
  - `test_an_embedded_prediction_stays_admissible_after_a_reveal`

## Modification guidance

- Change reveal ledger policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/reveal_ledger.py](../../../../../../src/learnloop/attempts/reveal_ledger.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
