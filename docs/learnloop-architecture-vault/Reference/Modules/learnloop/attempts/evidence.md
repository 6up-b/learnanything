---
title: "learnloop.attempts.evidence"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/evidence.py"
source_paths:
  - "src/learnloop/attempts/evidence.py"
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
  - "learnloop.attempts.evidence module"
  - "src/learnloop/attempts/evidence.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.evidence`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.evidence` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Derived per-attempt-type evidence factors (Fable's-take item 3).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/evidence.py](../../../../../../src/learnloop/attempts/evidence.py) |
| Source lines | 42 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `attempt_evidence_mass(attempt_type: str, config: EvidenceConfig | None=None) -> float` ([source](../../../../../../src/learnloop/attempts/evidence.py), line 18) — Weight of this attempt type on ability-belief updates (mastery EKF).
- `attempt_surface_exposure(attempt_type: str, config: EvidenceConfig | None=None) -> float` ([source](../../../../../../src/learnloop/attempts/evidence.py), line 27) — Fraction of the item's facet surface this attempt type certifies as probed.
- `practice_mode_item_coverage(practice_mode: str, config: EvidenceConfig | None=None) -> float` ([source](../../../../../../src/learnloop/attempts/evidence.py), line 38) — Item-side coverage prior when an item has no evidence weights or rubric.

### Module constants

- `DEFAULT_EVIDENCE` ([src/learnloop/attempts/evidence.py](../../../../../../src/learnloop/attempts/evidence.py), line 15)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `attempt_evidence_mass`; statically calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `attempt_evidence_mass`; statically calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `attempt_evidence_mass`; statically calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `attempt_evidence_mass`, `attempt_surface_exposure`, `practice_mode_item_coverage`; statically calls `attempt_evidence_mass`, `attempt_surface_exposure`, `practice_mode_item_coverage`
- [[Reference/Modules/learnloop/scheduling/review_log|learnloop.scheduling.review_log]] — imports `attempt_evidence_mass`; statically calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `attempt_evidence_mass`; statically calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `attempt_evidence_mass`; statically calls `attempt_evidence_mass`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `EvidenceConfig`; calls `EvidenceConfig`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]], [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]], [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]], [[Reference/Modules/learnloop/scheduling/review_log|learnloop.scheduling.review_log]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_characterization_certification_ledger.py](../../../../../../tests/test_characterization_certification_ledger.py) — direct import
  - `test_evidence_mass_is_pure_function_of_attempt_type`
  - `test_evidence_mass_signature_has_no_confidence_channel`
- [tests/test_evidence_config.py](../../../../../../tests/test_evidence_config.py) — direct import
  - `test_default_config_text_round_trips_canonical_values`
  - `test_dont_know_two_axis_contract`
  - `test_evidence_mass_reproduces_old_mastery_table_exactly`
  - `test_non_recording_types_carry_zero_on_both_axes`
  - `test_override_flows_through_resolvers`
  - `test_partial_toml_override_keeps_other_types_at_defaults`
  - `test_practice_mode_item_coverage_matches_old_defaults`
  - `test_surface_exposure_matches_old_coverage_table_except_documented_changes`
  - `test_unknown_attempt_type_defaults_to_full_evidence`
- [tests/test_exam_session.py](../../../../../../tests/test_exam_session.py) — direct import
  - `test_finish_lands_exam_attempt_evidence_with_full_mass`

## Modification guidance

- Change evidence policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/evidence.py](../../../../../../src/learnloop/attempts/evidence.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
