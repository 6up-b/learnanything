---
title: "learnloop.curriculum.confusable_concepts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/confusable_concepts.py"
source_paths:
  - "src/learnloop/curriculum/confusable_concepts.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Build a Study Map"
aliases:
  - "learnloop.curriculum.confusable_concepts module"
  - "src/learnloop/curriculum/confusable_concepts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.confusable_concepts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps confusable concepts behavior inside its owning package, [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]]. Its public surface centers on `ObservedConfusableConcept`, `learner_observed_confusable_concepts`.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/confusable_concepts.py](../../../../../../src/learnloop/curriculum/confusable_concepts.py) |
| Source lines | 90 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ObservedConfusableConcept` ([source](../../../../../../src/learnloop/curriculum/confusable_concepts.py), line 17)
- `learner_observed_confusable_concepts(vault: LoadedVault, repository: Repository, learning_object_id: str) -> list[ObservedConfusableConcept]` ([source](../../../../../../src/learnloop/curriculum/confusable_concepts.py), line 25) — Return stable learner-specific confusions inferred from probe episodes.

### Module constants

- `OBSERVED_CONFUSION_MIN_EVIDENCE` ([src/learnloop/curriculum/confusable_concepts.py](../../../../../../src/learnloop/curriculum/confusable_concepts.py), line 11)
- `OBSERVED_CONFUSION_MIN_PROBABILITY` ([src/learnloop/curriculum/confusable_concepts.py](../../../../../../src/learnloop/curriculum/confusable_concepts.py), line 12)
- `OBSERVED_CONFUSION_MIN_PRIOR_LIFT` ([src/learnloop/curriculum/confusable_concepts.py](../../../../../../src/learnloop/curriculum/confusable_concepts.py), line 13)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `learner_observed_confusable_concepts`; statically calls `learner_observed_confusable_concepts`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `episode_posterior`; calls `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `confused_concept`; calls `confused_concept`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_confusable_concepts.py](../../../../../../tests/test_confusable_concepts.py) — direct import
  - `test_repeated_probe_evidence_promotes_learner_observed_confusable`
  - `test_single_observation_does_not_promote_confusable`

## Modification guidance

- Change confusable concepts policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/confusable_concepts.py](../../../../../../src/learnloop/curriculum/confusable_concepts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
