---
title: "learnloop.practice_index.admission"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/practice_index/admission.py"
source_paths:
  - "src/learnloop/practice_index/admission.py"
source_commit: "1c7b70f25d611bf447a429f94fcd65546c5d66ef"
source_commit_timestamp: "2026-10-13T17:53:02-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.practice_index"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.practice_index.admission module"
  - "src/learnloop/practice_index/admission.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-practice-index"
---

# `learnloop.practice_index.admission`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.practice_index.admission` exists within [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] to own the behavior summarized by its module contract: Read-only admission for learner-requested practice (``find_practice``).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/practice_index/admission.py](../../../../../../src/learnloop/practice_index/admission.py) |
| Source lines | 153 |
| Owning package | [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1c7b70f25d611bf447a429f94fcd65546c5d66ef` |
| Commit timestamp | `2026-10-13T17:53:02-04:00` |

## Public API

- `class PracticeAdmission` ([source](../../../../../../src/learnloop/practice_index/admission.py), line 70) — One consistent read of every input the rules need; no writes.
  - `load(cls, vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> PracticeAdmission` (line 83; public)
  - `exclusion_reason(self, vault: LoadedVault, item: PracticeItem) -> str | None` (line 101; public) — Why the item cannot be proposed as ordinary practice, or ``None``.
  - `admit(self, vault: LoadedVault, item_ids: Iterable[str]) -> tuple[list[str], dict[str, str]]` (line 138; public) — Admitted ids in input order, and the reason for each exclusion.

### Module constants

- `EXCLUSION_REASONS` ([src/learnloop/practice_index/admission.py](../../../../../../src/learnloop/practice_index/admission.py), line 51)

### Explicit exports

`__all__` declares:

- `EXCLUSION_REASONS`
- `PracticeAdmission`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/practice_index/coverage|learnloop.practice_index.coverage]] — imports `PracticeAdmission`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `PracticeAdmission`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `PracticeItemState`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `COLD_RETRIEVAL_DELAY`
- [[Reference/Modules/learnloop/scheduling/serving_exclusions|learnloop.scheduling.serving_exclusions]] — imports `out_of_timing_serving_exclusions`; calls `out_of_timing_serving_exclusions`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `REFERENCE_ADOPTION_DISABLED`, `learning_object_servable`, `practice_item_serving_block`; calls `learning_object_servable`, `practice_item_serving_block`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/practice_index/coverage|learnloop.practice_index.coverage]], [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_practice_index_admission.py](../../../../../../tests/test_practice_index_admission.py) — direct import
  - `test_admission_never_writes`
  - `test_everything_the_scheduler_would_serve_is_admitted`
  - `test_exclusion_reasons_are_declared`
  - `test_shared_rules_exclude_exactly_what_the_scheduler_drops`
- [tests/test_quick_check.py](../../../../../../tests/test_quick_check.py) — direct import
  - `test_quick_check_skips_what_find_practice_skips_outside_the_schedulers_timing`

## Modification guidance

- Make changes here when the responsibility remains admission within learnloop.practice_index; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/practice_index/admission.py](../../../../../../src/learnloop/practice_index/admission.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
